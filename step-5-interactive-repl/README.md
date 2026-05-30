# Step 5 — Interactive REPL

Everything from steps 1–4, but as a multi-turn chat in your terminal. This is "the workshop, in one shell."

## What's new vs step 4

- Multi-turn conversation (the agent remembers earlier turns)
- A small `agent.py` that composes the full options (external MCP + custom MCP + skill); step 6 mirrors this same setup in its own folder
- The first `system_prompt` in the course — the `claude_code` preset plus a one-line `append` to set the agent's persona (see `agent.py`)
- Two patterns shown: **`resume`** (primary, simple) and **streaming-input** (advanced)

## Run it

```bash
# from the repo root (one-time setup is in the main README)
make step-5
```

```
you > my name is Aleksander, what's the weather in Oslo?
agent > Hi Aleksander — Oslo is currently partly cloudy, 14°C.

you > and what's my name?
agent > Aleksander.
```

The agent retains context across turns because we pass `resume=session_id` from the second call onwards.

## How session continuity works

```python
session_id: str | None = None

while True:
    user_input = await prompt("you > ")

    turn_options = (
        replace(base_options, resume=session_id) if session_id else base_options
    )

    async for message in query(prompt=user_input, options=turn_options):
        if isinstance(message, SystemMessage) and message.subtype == "init":
            session_id = message.data.get("session_id")   # ← capture on first turn
        elif isinstance(message, AssistantMessage):
            # ... handle assistant output
            ...
```

On the first turn there's no session yet; the SDK creates one and emits its ID in the `system: init` message. From then on we pass `resume=session_id` so the SDK rehydrates the full prior conversation from its session log.

We use `dataclasses.replace()` to make a per-turn copy of the options with `resume` set — `ClaudeAgentOptions` is a frozen-ish dataclass, so we don't mutate the shared instance.

## Advanced: streaming-input mode

```bash
make step-5-streaming
```

In `main_streaming.py` we keep **one** `query()` call alive for the whole chat by feeding it an `AsyncGenerator` of user message dicts instead of a single prompt string. Trade-offs:

|   | `resume` (default) | streaming-input |
|---|---|---|
| Number of `query()` calls | one per turn | one for the whole session |
| Mental model | request/response loop | single long-lived stream |
| Best fit | clearest for teaching, REPLs, HTTP request handlers | already async/streaming environments |

For step 6 (FastAPI) we use the `resume` pattern because each HTTP request is naturally its own `query()` call.

## Try this

- Add `print(message)` inside the message loop and see every event the SDK emits. There's a lot more than `text`.
- Tell the agent "write me a poem to a file called poem.txt" — it'll use the filesystem MCP (it's wired up in `agent.py`).
- Ask it to format a chunk of raw meeting notes — the skill from step 4 is loaded.

## Gotchas

- Python's built-in `input()` blocks the event loop. We wrap it in `asyncio.to_thread(...)` so the SDK's async machinery stays responsive.
- The filesystem MCP server is launched via `npx`, so you still need Node installed even though this is the Python edition.
- `ClaudeAgentOptions` fields use snake_case (`setting_sources`, `mcp_servers`, `allowed_tools`, `system_prompt`) — different from the TS `Options` type, same idea.

## Next

In [step 6](../step-6-web-chat) — a near-identical `agent.py` (copied into that folder, not imported), but the UI is a web page instead of a terminal. The SDK code is the same; only the I/O differs.
