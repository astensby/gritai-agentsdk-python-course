# Same shape as step-5's agent.py. The SDK call is identical — only the I/O
# changes between a terminal REPL (step 5) and an HTTP+SSE route (this step).
#
# This module exports `build_agent_options()`, which returns a fully-configured
# `ClaudeAgentOptions` with:
#   - the in-process `weather` MCP server (custom tool — Open-Meteo, no API key)
#   - the external `fs` MCP server (npx @modelcontextprotocol/server-filesystem)
#   - skill discovery scoped to this project via `setting_sources=["project"]`
#   - the same short, conversational system-prompt append from step 5

from pathlib import Path
from typing import Any

import httpx
from claude_agent_sdk import (
    ClaudeAgentOptions,
    create_sdk_mcp_server,
    tool,
)

# WMO weather codes → short description (https://open-meteo.com/en/docs).
WEATHER_CODES: dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Rime fog",
    51: "Light drizzle",
    53: "Drizzle",
    55: "Heavy drizzle",
    61: "Light rain",
    63: "Rain",
    65: "Heavy rain",
    66: "Freezing rain",
    67: "Heavy freezing rain",
    71: "Light snow",
    73: "Snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Light showers",
    81: "Showers",
    82: "Violent showers",
    85: "Snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with hail",
    99: "Severe thunderstorm",
}


@tool(
    "getWeather",
    "Get the current weather for a city. Returns description + temp in °C.",
    {"city": str},
)
async def get_weather(args: dict[str, Any]) -> dict[str, Any]:
    city = args["city"]
    async with httpx.AsyncClient(timeout=10.0) as client:
        geo = (
            await client.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": city, "count": 1, "language": "en", "format": "json"},
            )
        ).json()
        results = geo.get("results") or []
        if not results:
            return {"content": [{"type": "text", "text": f'Couldn\'t find "{city}".'}]}
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
            return {
                "content": [{"type": "text", "text": f"No weather available for {place['name']}."}]
            }
        desc = WEATHER_CODES.get(current["weather_code"], "Unknown conditions")
        return {
            "content": [
                {
                    "type": "text",
                    "text": (
                        f"{place['name']}, {place['country']}: "
                        f"{desc}, {round(current['temperature_2m'])}°C"
                    ),
                }
            ]
        }


weather_server = create_sdk_mcp_server(
    name="weather",
    version="1.0.0",
    tools=[get_weather],
)


def build_agent_options() -> ClaudeAgentOptions:
    # Anchor the sandbox + skill discovery to this step's project root (the
    # `step-6-web-chat/` folder). `Path(__file__).parent.parent` walks up from
    # `step_6_web_chat/agent.py` → `step_6_web_chat/` → `step-6-web-chat/`.
    project_root = Path(__file__).parent.parent
    sandbox_dir = project_root / "sandbox"

    return ClaudeAgentOptions(
        model="claude-sonnet-4-6",
        cwd=str(project_root),
        # Scope skill discovery to this project (see step 4).
        setting_sources=["project"],
        mcp_servers={
            "fs": {
                "type": "stdio",
                "command": "npx",
                "args": [
                    "-y",
                    "@modelcontextprotocol/server-filesystem",
                    str(sandbox_dir),
                ],
            },
            "weather": weather_server,
        },
        allowed_tools=[
            "mcp__fs__read_text_file",
            "mcp__fs__read_file",
            "mcp__fs__write_file",
            "mcp__fs__list_directory",
            "mcp__weather__getWeather",
        ],
        system_prompt={
            "type": "preset",
            "preset": "claude_code",
            "append": (
                "You are the workshop web-chat agent. Keep replies short and conversational."
            ),
        },
    )
