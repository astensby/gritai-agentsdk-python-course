# Step 3b — Custom MCP Server, for real

Step 3 built a custom tool with **canned data** so the focus stayed on the *mechanics*. This step keeps everything identical except one thing: the tool handlers now call a **real weather API**. The lesson: a tool can wrap any function — including a live HTTP service — and the agent calls it exactly the same way.

## What's new vs step 3

- The `getWeather` / `getForecast` handlers call [Open-Meteo](https://open-meteo.com/) — a free, **no-API-key** weather service — over `httpx.AsyncClient`.
- A name → coordinates step (Open-Meteo's geocoding API) and a small WMO-weather-code → text map.
- Nothing else changes: same `@tool()` decorators, same `create_sdk_mcp_server`, same `allowed_tools`.

## Run it

```bash
# from the repo root (one-time setup is in the main README)
make step-3b
```

Ask it the same question as step 3 — but now the numbers are real. Run it in May and Oslo won't be snowy.

## How it works

The only change from step 3 is inside the handler. Instead of a lookup table:

```python
@tool("getWeather", "...", {"city": str})
async def get_weather(args: dict) -> dict:
    city = args["city"]
    async with httpx.AsyncClient() as client:
        # 1) city name → coordinates (geocoding API, no key)
        place = await geocode(client, city)
        # 2) coordinates → current conditions
        resp = await client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "current": "temperature_2m,weather_code",
            },
        )
        current = resp.json()["current"]
        return {"content": [{"type": "text",
            "text": f"{place['name']}: {describe(current['weather_code'])}, {round(current['temperature_2m'])}°C"}]}
```

`weather_code` is a [WMO code](https://open-meteo.com/en/docs); we map it to a short description (`0 → "Clear sky"`, `71 → "Light snow"`, …).

## Why two steps

- **step 3 (canned data)** keeps the first exposure to `@tool()` minimal — no network, no JSON parsing, nothing to distract from the API shape and the schema shorthand.
- **step 3b (real API)** shows the same tool reaching out to the world. In practice your tools will do exactly this: call an internal service, query a database, hit a third-party API.

## A note on failure

Real calls can fail (no network, the service is down, an unknown city). The handlers return a friendly message in those cases, and the agent reads it as a normal tool result — it can apologize or try something else. That graceful-degradation path is itself worth pointing out to participants; canned data never shows it.

## Gotchas

- **`httpx` is async — use `httpx.AsyncClient()` inside `async def` tools.** Don't reach for `requests`; it would block the event loop and your other tool calls would queue up behind it.
- The Open-Meteo geocoder returns an empty `results` list for unknown cities (not an HTTP error). We check that explicitly and return a friendly message.

## Try this

- Ask for a city that doesn't exist ("the weather in Atlantis"). Watch the handler return "couldn't find it" and the agent handle it.
- Add a `humidity` or `wind_speed_10m` field to the `current=` query and surface it in the output.
- Disconnect from the network and rerun — see how the agent reports the failure.

## Next

In [step 4](../step-4-skills), instead of giving the agent more tools, we'll give it a **Skill** — a markdown file that teaches the agent *how* to do something well, with no code at all.
