# Step 3 — Custom MCP Server (in-process)

Wrap your own Python functions as MCP tools using the SDK's `create_sdk_mcp_server` helper. No subprocess, no JSON-RPC plumbing — just async functions.

## What's new vs step 2

- `create_sdk_mcp_server` + `@tool` from the SDK
- Input schemas for tool arguments (the SDK converts them to JSON Schema for the model)
- An MCP server that lives **in the same process** as your agent

## Run it

```bash
# from the repo root (one-time setup is in the main README)
make step-3
```

The agent will call `getWeather` then `getForecast`. You'll see each tool invocation in the trace.

## How it works

`weather_server.py` defines two tools:

```python
@tool(
    "getWeather",                                          # ← name (shows up as mcp__weather__getWeather)
    "Get the current weather for a city. ...",             # ← description (the agent's decision lever)
    {"city": str},                                         # ← input_schema: shorthand {field: type}
)
async def get_weather(args: dict) -> dict:                 # ← handler
    return {"content": [{"type": "text", "text": "..."}]}


weather_server = create_sdk_mcp_server(
    name="weather",
    version="1.0.0",
    tools=[get_weather, get_forecast],
)
```

Then in `main.py` you mount it the same way as an external server:

```python
mcp_servers={"weather": weather_server}
```

## The schema shorthand

The third arg to `@tool` accepts a **shorthand mapping** of `{field_name: type}` — Python types like `str`, `int`, `bool`. The SDK turns that into a real JSON Schema for the model. If you need constraints (enums, min/max, descriptions per field) you can pass a `TypedDict` or a full JSON Schema dict instead.

The handler always receives a single `args: dict` — not unpacked kwargs. Pull fields out yourself: `city = args["city"]`.

## In-process vs subprocess MCP — when to use which

| In-process (`create_sdk_mcp_server`) | Subprocess (stdio MCP) |
|---|---|
| Same Python codebase | Reusable across projects/languages |
| Share state with your app | Process isolation |
| No marshaling overhead | Sandboxable |
| Can't reuse from non-SDK clients | Speaks plain MCP |

If you'd rather **build the MCP server itself** as a standalone, distributable artifact, see day 1's morning track on building MCP servers.

## Try this

- Improve the tool descriptions so the agent always passes a valid city. (Hint: switch from the shorthand to a full JSON Schema with an `enum` or per-field `description`.)
- Add a third tool `getAirQuality(city)` and call it from the prompt.
- Make `get_weather` deliberately raise on `"Atlantis"`. Watch how the agent recovers.

## Next

The tools here return **canned data** to keep the mechanics clear. In [step 3b](../step-3b-real-weather) the same tools call a **real weather API** — one small change to the handler. Then [step 4](../step-4-skills) gives the agent a **Skill** instead of a tool: a markdown file that teaches it *how* to do something well, with no code at all.
