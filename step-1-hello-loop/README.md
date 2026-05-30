# Step 1 — Hello Loop

The smallest possible Claude Agent SDK program. One prompt, one response.

## What you'll learn

- The Agent SDK's core API: `query(prompt=..., options=ClaudeAgentOptions(...))`
- That `query()` returns an **async iterator of messages** — there is no separate "agent loop" to write
- The shape of the message stream: `SystemMessage`, `AssistantMessage`, `ResultMessage`

## Run it

```bash
# from the repo root (one-time setup is in the main README)
make step-1
```

You should see Claude's answer stream to stdout, followed by cost + duration:

```
An AI agent is software that ...
---
Cost:     $0.001234
Duration: 1842ms
```

## Try this

- Swap the model to `claude-haiku-4-5` (faster, cheaper) or `claude-opus-4-7` (smarter, costlier) and observe the cost change.
- Change the prompt to something requiring tools — like `"Read pyproject.toml and tell me the dependencies."` — and watch it fail. Why? You haven't given it any tools yet. That's [step 2](../step-2-external-mcp).

## Key concepts

| Concept | Where in code |
|---|---|
| Async iterator | `async for message in query(...)` |
| Message types | `isinstance(message, AssistantMessage \| ResultMessage \| ...)` |
| Content blocks | `message.content` is a list of typed blocks — here always `TextBlock`; `ToolUseBlock` appears once you add tools (step 2) |
| Cost telemetry | `message.total_cost_usd` on `ResultMessage` |

## Gotchas

- **No `load_dotenv()` here.** The `Makefile` runs `uv run --env-file=.env ...`, which loads `ANTHROPIC_API_KEY` into the environment before Python starts. Don't add `python-dotenv` to any step — env loading is structural.
- **Content blocks live on the message directly.** In Python it's `message.content`; in the TS SDK it's `message.message.content`. Don't get tripped up if you're cross-referencing the TS course.
- **Pin the model.** `claude-sonnet-4-6` is the default model for every step in this workshop. Change it intentionally, not by accident.
