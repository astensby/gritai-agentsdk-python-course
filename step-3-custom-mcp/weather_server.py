"""
Custom in-process MCP server: two weather tools wrapped via `@tool` and
bundled via `create_sdk_mcp_server`.

PLACEHOLDER DATA. This step is about the *mechanics* of defining a tool —
`@tool`, the input schema, `create_sdk_mcp_server` — so the handlers just
return canned values and stay dead simple. (That's why "Oslo" is always
snowy here: it's a stub, not a real forecast.) In the next step,
`step-3b-real-weather`, these exact same tools call a real weather API.
"""

from claude_agent_sdk import create_sdk_mcp_server, tool

# Canned weather table. Identical to the TS reference — same cities, same vibes.
FAKE_WEATHER: dict[str, dict] = {
    "Oslo": {"description": "Light snow", "tempC": -3},
    "San Francisco": {"description": "Foggy", "tempC": 14},
    "London": {"description": "Rainy", "tempC": 9},
    "Tokyo": {"description": "Clear skies", "tempC": 18},
}


# `@tool(name, description, input_schema)`
#
# - `name`: what the model sees, and what you whitelist via `allowed_tools`.
# - `description`: the agent reads this to decide WHEN to call the tool.
#   Write it well — this is the single biggest lever on tool-use quality.
# - `input_schema`: the SHORTHAND form `{"field": type}`. The SDK turns this
#   into a real JSON Schema for the model. You can also pass a TypedDict or a
#   full JSON Schema dict if you need constraints (enums, min/max, etc.).
# - The decorated function is an async handler that returns
#   `{"content": [{"type": "text", "text": "..."}]}`.
@tool(
    "getWeather",
    "Get the current weather for a city. "
    "Returns a one-line description and temperature in Celsius.",
    {"city": str},
)
async def get_weather(args: dict) -> dict:
    city = args["city"]
    w = FAKE_WEATHER.get(city, {"description": "Sunny", "tempC": 22})
    return {"content": [{"type": "text", "text": f"{city}: {w['description']}, {w['tempC']}°C"}]}


@tool(
    "getForecast",
    "Get a multi-day weather forecast for a city.",
    {"city": str, "days": int},
)
async def get_forecast(args: dict) -> dict:
    city = args["city"]
    days = int(args["days"])
    # Clamp to the documented 1-7 day horizon. (With the shorthand schema we
    # can't express min/max declaratively — that's what a full JSON Schema or
    # TypedDict would buy you. For a teaching demo, clamp in code is fine.)
    days = max(1, min(7, days))
    lines = "\n".join(f"  Day {i + 1}: Partly cloudy, 20°C" for i in range(days))
    return {"content": [{"type": "text", "text": f"Forecast for {city}:\n{lines}"}]}


# An "SDK MCP server" is just a bundle of tools the SDK exposes IN-PROCESS
# (no subprocess, no stdio) via the MCP protocol. You consume it the same
# way as an external server.
weather_server = create_sdk_mcp_server(
    name="weather",
    version="1.0.0",
    tools=[get_weather, get_forecast],
)
