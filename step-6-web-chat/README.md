# Step 6 — Web Chat (bonus)

The same agent from step 5, behind a tiny FastAPI web UI. The point: **the SDK doesn't change; only the I/O does.**

## What's new vs step 5

- A FastAPI app with one page and one API route
- The SDK runs in the route handler; the browser talks to it over **Server-Sent Events**
- `step_6_web_chat/agent.py` is essentially identical to step 5's `agent.py` — same MCP servers, same skill, same options

## Run it

```bash
# from the repo root (one-time setup is in the main README)
make step-6
```

Open [http://localhost:8000](http://localhost:8000) and chat.

## Architecture

```
Browser  ──fetch /api/chat──▶  FastAPI route
                                  │
                                  ├─ query({ prompt, options: { ... resume } })
                                  ├─ async for stream → SSE
                                  ▼
                              [external MCP] [in-process MCP] [Skill]
```

- **`step_6_web_chat/server.py`** — the FastAPI app. `GET /` returns the static HTML; `POST /api/chat` calls `query()` and translates the SDK message stream into SSE events for the browser.
- **`static/index.html`** — minimal vanilla-JS client that parses the SSE stream and renders the chat. No build step, no framework.
- **`step_6_web_chat/agent.py`** — the agent setup (`mcp_servers` + `allowed_tools` + `setting_sources` + `system_prompt`). **Mirrored from** step-5's `agent.py`, not imported — each step folder is deliberately self-contained. Look at them side-by-side: it's the same code.

## Token-by-token streaming

The route uses `include_partial_messages=True` to opt into **token-level** streaming. Without it, the SDK only emits whole `AssistantMessage` events — the UI would freeze for several seconds, then dump the full response. With it, the SDK emits `StreamEvent` objects whose `.event` field is the raw Anthropic stream event; we forward the `content_block_delta` text deltas to the browser:

```python
elif isinstance(msg, StreamEvent):
    ev = msg.event
    if ev.get("type") == "content_block_delta":
        delta = ev.get("delta") or {}
        if delta.get("type") == "text_delta":
            yield _sse({"type": "text", "text": delta.get("text", "")})
```

The whole-message `AssistantMessage` and `ResultMessage` events still arrive too, but with partials enabled we've already streamed the text from the deltas — so this minimal route ignores them. (A richer UI could read the `AssistantMessage` blocks' `ToolUseBlock`s to show which tools fired.)

## Session resume

Each browser tab tracks its own `sessionId`. The first SSE event of every response is `{"type":"session","sessionId":"..."}` — the client saves it and sends it on the next `POST /api/chat` as `{"sessionId": "..."}`. The route forwards that into `ClaudeAgentOptions.resume`, which makes the SDK continue the conversation instead of starting fresh.

## One Python-specific detail

The Makefile launches the app via:

```bash
uv run --env-file=.env --package step-6-web-chat \
    uvicorn step_6_web_chat.server:app --app-dir step-6-web-chat
```

- `--app-dir step-6-web-chat` puts the step folder on `sys.path` so `step_6_web_chat.server` resolves.
- `--env-file=.env` loads `ANTHROPIC_API_KEY` into the environment before Python starts — there is **no** `load_dotenv()` anywhere in the source. Env loading is structural across this whole workshop.
- The package name uses underscores (`step_6_web_chat`); the folder name uses hyphens (`step-6-web-chat`). Hyphens aren't valid in Python module names, hence the split.

## Try this

- Open two browser tabs. They get independent sessions (each tab tracks its own `sessionId`).
- Wire up a "Reset" button that clears `sessionId` and starts a fresh conversation.
- Add a tool-use indicator: read `AssistantMessage` blocks for `ToolUseBlock`s and emit `{"type":"tool","name":...}` events the client renders as chips.
- Deploy: any Python host that can run `uvicorn` (Fly.io, Railway, a small VM). Add `ANTHROPIC_API_KEY` to the environment.

## Gotchas

- The Agent SDK shells out to `claude` (and to `npx` for the filesystem MCP server) — running on a host without Node/npm available won't work.
- SSE is buffered by some reverse proxies. The route sets `Cache-Control: no-cache, no-transform` and `X-Accel-Buffering: no`; if you put it behind nginx, double-check buffering is off.
- `sandbox/` exists so the filesystem MCP server has somewhere safe to read/write. The path is anchored to the step folder via `Path(__file__).parent.parent`, so it works regardless of where you launch uvicorn from.

## That's it

You've now built six progressively-richer agents — from a raw API call to a full web chat with custom tools, external tools, and a skill. The SDK pattern is the same throughout. Everything else is just I/O.

## Next

[Step 7 — Subagents](../step-7-subagents): one coordinator agent that delegates specialist work to subagents.
