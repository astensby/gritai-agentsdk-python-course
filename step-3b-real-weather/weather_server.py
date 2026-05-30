"""
SAME tools as step 3 — but the handlers now call a REAL weather service:
the free, no-API-key Open-Meteo API, over `httpx.AsyncClient`. That's the
payoff of a custom tool: wrap *any* function, including a live HTTP API,
and the agent can call it. (Needs an internet connection; if a call fails
the handler returns a friendly message and the agent recovers.)
"""

import httpx
from claude_agent_sdk import create_sdk_mcp_server, tool

# WMO weather codes → a short human description. See https://open-meteo.com/en/docs
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


def describe(code: int) -> str:
    return WEATHER_CODES.get(code, "Unknown conditions")


async def geocode(client: httpx.AsyncClient, city: str) -> dict | None:
    """Resolve a city name to coordinates via Open-Meteo's geocoding API (no key)."""
    resp = await client.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1, "language": "en", "format": "json"},
        timeout=10.0,
    )
    data = resp.json()
    results = data.get("results") or []
    return results[0] if results else None


@tool(
    "getWeather",
    "Get the current weather for a city. "
    "Returns a one-line description and temperature in Celsius.",
    {"city": str},
)
async def get_weather(args: dict) -> dict:
    city = args["city"]
    async with httpx.AsyncClient() as client:
        place = await geocode(client, city)
        if not place:
            return {
                "content": [{"type": "text", "text": f'Couldn\'t find a place called "{city}".'}]
            }
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": place["latitude"],
            "longitude": place["longitude"],
            "current": "temperature_2m,weather_code",
        }
        resp = await client.get(url, params=params, timeout=10.0)
        wx = resp.json()
        current = wx.get("current")
        if not current:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"No current weather available for {place['name']}.",
                    }
                ]
            }
        text = (
            f"{place['name']}, {place['country']}: "
            f"{describe(current['weather_code'])}, "
            f"{round(current['temperature_2m'])}°C"
        )
        return {"content": [{"type": "text", "text": text}]}


@tool(
    "getForecast",
    "Get a multi-day weather forecast for a city.",
    {"city": str, "days": int},
)
async def get_forecast(args: dict) -> dict:
    city = args["city"]
    days = max(1, min(7, int(args["days"])))
    async with httpx.AsyncClient() as client:
        place = await geocode(client, city)
        if not place:
            return {
                "content": [{"type": "text", "text": f'Couldn\'t find a place called "{city}".'}]
            }
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": place["latitude"],
            "longitude": place["longitude"],
            "daily": "weather_code,temperature_2m_max,temperature_2m_min",
            "forecast_days": days,
            "timezone": "auto",
        }
        resp = await client.get(url, params=params, timeout=10.0)
        data = resp.json()
        d = data.get("daily")
        if not d:
            return {
                "content": [{"type": "text", "text": f"No forecast available for {place['name']}."}]
            }
        lines = "\n".join(
            f"  {date}: {describe(d['weather_code'][i])}, "
            f"{round(d['temperature_2m_min'][i])}–{round(d['temperature_2m_max'][i])}°C"
            for i, date in enumerate(d["time"])
        )
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Forecast for {place['name']}, {place['country']}:\n{lines}",
                }
            ]
        }


weather_server = create_sdk_mcp_server(
    name="weather",
    version="1.0.0",
    tools=[get_weather, get_forecast],
)
