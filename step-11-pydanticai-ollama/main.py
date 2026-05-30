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
  - The model provider is `OpenAIModel` pointed at Ollama's OpenAI-compatible
    endpoint (http://localhost:11434/v1) — no Anthropic API key needed.
  - Skills are NOT a first-class feature in PydanticAI — we load + inject manually
    via `skills.py` (parallel to TS `skills.ts`).
  - Tool quality is bounded by the local model (see README).
  - We skip MCP here to keep the demo focused. PydanticAI does have MCP
    support — see the README "Try this" section for how to add it.

Requires Ollama running locally:
    ollama serve
    ollama pull llama3.3   # or qwen2.5-coder, mistral-nemo — must support tool calling
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

import httpx
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
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

    # 2) Build the model. OpenAIModel + Ollama's OpenAI-compatible endpoint is
    #    the canonical PydanticAI recipe for local models.
    model = OpenAIModel(
        model_name=MODEL,
        provider=OpenAIProvider(base_url="http://localhost:11434/v1"),
    )

    # 3) Build the agent. System prompt = base + injected skills block.
    system_prompt = (
        "You are a helpful agent. Use the available tools and skills as needed."
        + format_skills_as_system_block(skills)
    )
    agent = Agent(model, system_prompt=system_prompt)

    # 4) Register a custom tool (same idea as step-3's weather tool) — it calls
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

    # 5) Run the agent loop. PydanticAI's Agent.run drives the loop internally
    #    (call model → execute tool → feed result back → repeat) until the model
    #    stops requesting tools.
    prompt = (
        "Format these raw meeting notes into a structured summary using the "
        "meeting-notes-formatter skill, then save the result to formatted.md "
        f"in {SANDBOX_DIR}.\n\n"
        f"RAW NOTES:\n{RAW_NOTES}"
    )

    result = await agent.run(prompt)

    # PydanticAI returns the final assistant text in `result.output`.
    print("\n" + (result.output or ""))

    print("\n---")
    print(f"Model:  {MODEL}")
    print(f"Output: {SANDBOX_DIR}/formatted.md (if the model used the tool)")


if __name__ == "__main__":
    asyncio.run(main())
