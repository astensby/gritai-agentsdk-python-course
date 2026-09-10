"""Step 11 — ALTERNATIVE-SDK DEMO (PydanticAI + Ollama)

The Python contrast lesson. Same agent ideas as the rest of the workshop, but
the SDK is different (PydanticAI instead of the Claude Agent SDK) AND the
model is different (a local Ollama model instead of Claude).

What stays the same — the AGENT IDEAS carry over:
  - There's a system prompt
  - There are tools (here: a custom weather tool)
  - There's a loop (tool call → tool result → next step), built into the agent
  - Skills are still just markdown files that get injected as system-prompt text

What's different:
  - `Agent(model, system_prompt=...)` + `agent.run(...)` instead of `query(...)`
  - The model provider is `OpenAIChatModel` + `OllamaProvider`, pointed at the
    local Ollama server — no Anthropic API key needed.
  - Skills are NOT a first-class feature in PydanticAI — we load + inject manually
    via `skills.py` (parallel to TS `skills.ts`).
  - Tool quality is bounded by the local model (see README).

*** THE MCP ROOTS COUNTERPOINT ***

We mount the SAME filesystem MCP server that step 2 uses. Watch its log line:

    Client does not support MCP Roots, using allowed directories set from
    server args

Step 2's client (the Claude Agent SDK) DOES advertise roots, so the server
throws away its own `--sandbox` argument and uses what the client tells it.
PydanticAI's client doesn't advertise roots by default (`FastMCPClient` takes
a `roots=` argument that defaults to None), so the server keeps its CLI
argument instead.

Same server. Two clients. Two different sandboxes. That is a concrete
demonstration that "supports MCP" is not one capability — it's a pile of
optional sub-protocols, and which ones your client implements changes where
your files actually land.

Requires Ollama running locally:
    ollama serve
    ollama pull llama3.3   # or gemma4, qwen3.5 — must support tool calling
    # override with OLLAMA_MODEL in the root .env
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

import httpx
from pydantic_ai import Agent
from pydantic_ai.mcp import FastMCPClient, MCPToolset, StdioTransport

# Note for anyone following older PydanticAI tutorials: the OpenAI-compatible
# chat class is `OpenAIChatModel`. You'll see `OpenAIModel` in examples written
# against 1.x, where it was a deprecated alias — it no longer exists. There's
# also a dedicated `OllamaProvider` now, rather than pointing the generic
# `OpenAIProvider` at a base_url by hand.
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.ollama import OllamaProvider
from skills import format_skills_as_system_block, load_skills

PROJECT_DIR = Path(__file__).resolve().parent
SANDBOX_DIR = PROJECT_DIR / "sandbox"
SKILLS_DIR = PROJECT_DIR / ".claude" / "skills"

MODEL = os.environ.get("OLLAMA_MODEL", "llama3.3")

RAW_NOTES = """
Q3 LAUNCH SYNC — 12 May 2026
Attendees: Anna (eng), Bob (marketing), Chen (security), Dani (PM)

Decided to push the launch from June 15 to June 30 to make room for security review.
Anna will lead the security review and coordinate with Chen's team.
Bob to draft revised launch comms by next Friday.
Anna to share security-review checklist on Monday.

Open: do we owe customers a heads-up before June 15? Bob to consult legal.
Open: budget for a second push if the date slips? Dani to ask the CFO.
"""

# WMO weather codes → short description (https://open-meteo.com/en/docs).
WEATHER_CODES: dict[int, str] = {
    0: "clear sky",
    1: "mainly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "fog",
    48: "rime fog",
    51: "light drizzle",
    53: "drizzle",
    55: "heavy drizzle",
    61: "light rain",
    63: "rain",
    65: "heavy rain",
    66: "freezing rain",
    67: "heavy freezing rain",
    71: "light snow",
    73: "snow",
    75: "heavy snow",
    77: "snow grains",
    80: "light showers",
    81: "showers",
    82: "violent showers",
    85: "snow showers",
    86: "heavy snow showers",
    95: "thunderstorm",
    96: "thunderstorm with hail",
    99: "severe thunderstorm",
}


async def main() -> None:
    SANDBOX_DIR.mkdir(parents=True, exist_ok=True)

    # 1) Load skills the same way the Claude Agent SDK does — from .claude/skills/.
    skills = load_skills(SKILLS_DIR)
    print(f"Loaded {len(skills)} skill(s) from .claude/skills/")

    # 2) Build the model. OpenAIChatModel talks the OpenAI wire format;
    #    OllamaProvider points it at the local Ollama server.
    model = OpenAIChatModel(
        MODEL,
        provider=OllamaProvider(base_url="http://localhost:11434/v1"),
    )

    # 3) Mount the SAME filesystem MCP server step 2 uses — this is what gives
    #    the agent a way to actually write the file the prompt asks for, and
    #    what produces the "Client does not support MCP Roots" line (docstring).
    fs_toolset = MCPToolset(
        FastMCPClient(
            StdioTransport(
                command="npx",
                args=[
                    "-y",
                    # Pinned, same as every other step — see step 2.
                    "@modelcontextprotocol/server-filesystem@2026.8.31",
                    str(SANDBOX_DIR),
                ],
            )
            # `FastMCPClient(..., roots=...)` is where you'd advertise roots.
            # Leaving it unset is what makes this client behave differently from
            # the Agent SDK's — try setting it and watch the log line change.
        )
    )

    # 4) Build the agent. System prompt = base + injected skills block.
    system_prompt = (
        "You are a helpful agent. Use the available tools and skills as needed. "
        "Use the filesystem tools to read and write files." + format_skills_as_system_block(skills)
    )
    agent = Agent(model, system_prompt=system_prompt, toolsets=[fs_toolset])

    # 5) Register a custom tool (same idea as step-3's weather tool) — it calls
    #    the free, no-API-key Open-Meteo service, just like the Claude steps do.
    #    `@agent.tool_plain` = a tool that doesn't need the run context.
    @agent.tool_plain
    async def get_weather(city: str) -> str:
        """Get the current weather for a city."""
        print(f"\n[tool] get_weather({city!r})")
        async with httpx.AsyncClient(timeout=10.0) as client:
            geo = (
                await client.get(
                    "https://geocoding-api.open-meteo.com/v1/search",
                    params={"name": city, "count": 1, "language": "en", "format": "json"},
                )
            ).json()
            results = geo.get("results") or []
            if not results:
                return f"Couldn't find {city!r}."
            place = results[0]
            wx = (
                await client.get(
                    "https://api.open-meteo.com/v1/forecast",
                    params={
                        "latitude": place["latitude"],
                        "longitude": place["longitude"],
                        "current": "temperature_2m,weather_code",
                    },
                )
            ).json()
        current = wx.get("current")
        if not current:
            return f"No weather available for {place['name']}."
        desc = WEATHER_CODES.get(int(current["weather_code"]), "unknown")
        return f"{place['name']}: {desc}, {round(current['temperature_2m'])}°C"

    # 6) Run the agent loop. PydanticAI's Agent.run drives the loop internally
    #    (call model → execute tool → feed result back → repeat) until the model
    #    stops requesting tools.
    #
    #    `async with agent:` starts the MCP toolset's subprocess and shuts it
    #    down afterwards. Without it the filesystem tools are never connected.
    prompt = (
        "Format these raw meeting notes into a structured summary using the "
        "meeting-notes-formatter skill, then save the result to formatted.md "
        f"in {SANDBOX_DIR}.\n\n"
        f"RAW NOTES:\n{RAW_NOTES}"
    )

    async with agent:
        result = await agent.run(prompt)

    # PydanticAI returns the final assistant text in `result.output`.
    print("\n" + (result.output or ""))

    written = SANDBOX_DIR / "formatted.md"
    print("\n---")
    print(f"Model:  {MODEL}")
    print(
        f"Output: {written}"
        if written.exists()
        else f"Output: {written} — NOT written. Small local models often skip the\n"
        f"        tool call even when the prompt asks for it; that gap between\n"
        f"        'has tools' and 'uses them well' is the point of this step."
    )


if __name__ == "__main__":
    asyncio.run(main())
