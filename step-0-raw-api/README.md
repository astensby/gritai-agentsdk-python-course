# Step 0 — Raw API (before the Agent SDK)

What's below the Agent SDK? This.

## What you'll learn

- The raw [`anthropic`](https://pypi.org/project/anthropic/) Python SDK — a thin HTTP client for Claude's REST API
- A single `messages.create()` call: prompt in, response out, done
- Why the Agent SDK exists: it wraps a *loop* of these calls and threads tool results back in

## Run it

```bash
# from the repo root (one-time setup is in the main README)
make step-0
```

You'll see the response, then token counts and a stop reason.

## The core call

(The full file also has the loop that prints the response and token counts — this is the part that matters.)

```python
client = AsyncAnthropic()

response = await client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Explain what an AI agent is in three sentences."},
    ],
)
```

That's it. One HTTP call. One response.

## How the Agent SDK relates

The Agent SDK is **not a different API**. It's a runtime that:

1. Calls `messages.create()` like above
2. Looks at the response — did the model ask to use a tool?
3. If yes: runs the tool, appends the result to the conversation, and calls `messages.create()` again
4. Repeats until the model says "I'm done" (`stop_reason: "end_turn"`)
5. Plus: MCP plumbing, skill discovery, hooks, permissions, sessions, ...

You could write the loop yourself with raw `messages.create()` calls — and people do, when they need full control. The Agent SDK is the well-tested, conventions-baked-in version.

## Gotchas

- No `load_dotenv()` here — `ANTHROPIC_API_KEY` is loaded by the Makefile via `uv run --env-file=.env`. The `AsyncAnthropic()` constructor picks it up from `os.environ` automatically.
- This step uses the standalone `anthropic` SDK, **not** `claude-agent-sdk`. From step 1 onwards we switch to the Agent SDK and never look back.

## Next

[Step 1](../step-1-hello-loop) — the same idea, but via the Agent SDK. You'll see the *exact same model + prompt* return through a different API, with the loop already built for you.
