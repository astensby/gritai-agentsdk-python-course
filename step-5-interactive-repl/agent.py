# The agent setup for step 5 (terminal REPL). Step 6 (web chat) carries a
# near-identical copy in its own package — same SDK call, only the I/O surface
# differs (stdin/stdout here vs HTTP/SSE there). Each step folder is
# deliberately self-contained, so the file is copied, not imported.

from pathlib import Path

import httpx
from claude_agent_sdk import ClaudeAgentOptions, create_sdk_mcp_server, tool

# --- A small custom MCP server (carried from step 3b) ----------------------
# It calls the free, no-API-key Open-Meteo service — a custom tool can wrap a
# real HTTP API just as easily as canned data.

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
async def get_weather(args: dict) -> dict:
    city = args["city"]
    async with httpx.AsyncClient(timeout=10.0) as client:
        geo_resp = await client.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1, "language": "en", "format": "json"},
        )
        geo = geo_resp.json()
        results = geo.get("results") or []
        if not results:
            return {"content": [{"type": "text", "text": f'Couldn\'t find "{city}".'}]}
        place = results[0]
        wx_resp = await client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "current": "temperature_2m,weather_code",
            },
        )
        wx = wx_resp.json()
        current = wx.get("current")
        if not current:
            return {
                "content": [{"type": "text", "text": f"No weather available for {place['name']}."}]
            }
        desc = WEATHER_CODES.get(current["weather_code"], "Unknown conditions")
        temp = round(current["temperature_2m"])
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"{place['name']}, {place['country']}: {desc}, {temp}°C",
                }
            ]
        }


weather_server = create_sdk_mcp_server(
    name="weather",
    version="1.0.0",
    tools=[get_weather],
)


# --- Compose the full options object ---------------------------------------


def build_agent_options() -> ClaudeAgentOptions:
    # sandbox dir sits next to this file, just like the TS version.
    sandbox_dir = (Path(__file__).parent / "sandbox").resolve()

    return ClaudeAgentOptions(
        model="claude-sonnet-5",
        # The MCP roots handshake answers with `cwd`, so point it at the sandbox
        # or the filesystem server's own CLI argument gets overridden and the
        # agent gets the whole project. Full explanation in step 2's docstring.
        #
        # This does NOT break skill discovery: `setting_sources=["project"]`
        # resolves by walking UP from cwd, so `.claude/skills/` one level above
        # is still found.
        cwd=str(sandbox_dir),
        # Scope skill discovery to this project (see step 4).
        setting_sources=["project"],
        # External MCP (from step 2) + in-process MCP (from step 3).
        mcp_servers={
            "fs": {
                "type": "stdio",
                "command": "npx",
                "args": [
                    "-y",
                    # Pinned: `npx -y` with no version fetches latest at run
                    # time. See step 2.
                    "@modelcontextprotocol/server-filesystem@2026.8.31",
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
        # Without this the model reaches for the built-in Write/Edit for file
        # work and never touches the MCP server. In a chat this surfaces on turn
        # two as "I need permission to write that file" — or worse, a successful
        # write somewhere you didn't intend. See step 2, point 1.
        disallowed_tools=["Write", "Edit", "NotebookEdit"],
        system_prompt={
            "type": "preset",
            "preset": "claude_code",
            "append": (
                "You are the workshop demo agent. Keep replies short and "
                "conversational unless asked otherwise. "
                "Use the mcp__fs__* tools for any file reading or writing."
            ),
        },
    )
