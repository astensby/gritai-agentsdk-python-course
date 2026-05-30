# Step 6 — Web Chat (FastAPI + SSE)
#
# The same agent from step 5, behind a tiny FastAPI app. The point:
# **the SDK doesn't change; only the I/O does.**
#
# Architecture:
#
#   Browser  ──fetch /api/chat──▶  FastAPI route
#                                     │
#                                     ├─ query({ prompt, options: { ... resume } })
#                                     ├─ async for stream → SSE
#                                     ▼
#                                 [external MCP] [in-process MCP] [Skill]
#
# - GET /            serves the single-page chat UI (static/index.html)
# - POST /api/chat   accepts {"message": str, "sessionId"?: str}, calls query()
#                    with include_partial_messages=True (token-by-token streaming),
#                    and translates the SDK message stream into SSE events.
#
# Three event types are forwarded to the client:
#   {"type":"session","sessionId":"..."}   on SystemMessage subtype="init"
#   {"type":"text","text":"..."}            on StreamEvent text_delta events
#   {"type":"error","message":"..."}        on exceptions

import json
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from claude_agent_sdk import (
    StreamEvent,
    SystemMessage,
    query,
)
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, StreamingResponse

from .agent import build_agent_options

app = FastAPI(title="Workshop Agent — Step 6")

STATIC_DIR = Path(__file__).parent.parent / "static"


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


def _sse(payload: dict[str, Any]) -> str:
    """Format a single SSE event line."""
    return f"data: {json.dumps(payload)}\n\n"


async def _chat_stream(message: str, session_id: str | None) -> AsyncIterator[str]:
    base_options = build_agent_options()
    # Stream tokens (not just whole messages). With include_partial_messages
    # the SDK emits StreamEvent objects whose `.event` is the raw Anthropic
    # content_block_delta union — we forward text deltas to the browser.
    base_options.include_partial_messages = True
    if session_id:
        base_options.resume = session_id

    # The agent can emit several text blocks per reply (e.g. a line before a
    # tool call, then the answer after). They arrive as separate blocks, so
    # we insert a paragraph break between them — otherwise the client, which
    # just concatenates deltas, would run them together ("…weather.It's…").
    has_streamed_text = False

    try:
        async for msg in query(prompt=message, options=base_options):
            if isinstance(msg, SystemMessage) and msg.subtype == "init":
                yield _sse({"type": "session", "sessionId": msg.data["session_id"]})
            elif isinstance(msg, StreamEvent):
                ev = msg.event
                ev_type = ev.get("type")
                if ev_type == "content_block_start":
                    block = ev.get("content_block") or {}
                    if block.get("type") == "text" and has_streamed_text:
                        yield _sse({"type": "text", "text": "\n\n"})
                elif ev_type == "content_block_delta":
                    delta = ev.get("delta") or {}
                    if delta.get("type") == "text_delta":
                        has_streamed_text = True
                        yield _sse({"type": "text", "text": delta.get("text", "")})
            # Whole-message AssistantMessage and ResultMessage events still
            # arrive, but with partials enabled we've already streamed the text
            # from the deltas — and this minimal client only renders text — so
            # we ignore them. (A richer UI could read AssistantMessage tool_use
            # blocks here to show "used tool: X" chips.)
    except Exception as err:  # noqa: BLE001 — surface any failure to the client
        yield _sse({"type": "error", "message": str(err)})


@app.post("/api/chat")
async def chat(req: Request) -> StreamingResponse:
    body = await req.json()
    message: str = body.get("message", "")
    session_id: str | None = body.get("sessionId")

    return StreamingResponse(
        _chat_stream(message, session_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
