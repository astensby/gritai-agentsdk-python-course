"""
The simplest possible Claude Agent SDK program.

`query()` returns an async iterator of messages. The SDK runs the full
agent loop internally (model call -> tool use -> model call -> ...) and emits
a stream of typed messages: SystemMessage, AssistantMessage, UserMessage,
ResultMessage.

For a one-shot prompt with no tools, we'll typically see:
  1. one SystemMessage (init)
  2. one or more AssistantMessage with the response
  3. one ResultMessage with cost + duration

Note for folks coming from the TS SDK: the Python message objects expose
content blocks directly on the message (e.g. `message.content`), not
nested under `message.message.content` as in JS.
"""

import asyncio

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    query,
)


async def main() -> None:
    options = ClaudeAgentOptions(
        model="claude-sonnet-4-6",
    )

    async for message in query(
        prompt="Explain what an AI agent is in three sentences.",
        options=options,
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text, end="", flush=True)
        elif isinstance(message, ResultMessage):
            print("\n\n---")
            print(f"Cost:     ${message.total_cost_usd:.6f}")
            print(f"Duration: {message.duration_ms}ms")


if __name__ == "__main__":
    asyncio.run(main())
