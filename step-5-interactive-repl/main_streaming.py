# ADVANCED VARIANT — Streaming-input mode.
#
# Instead of calling query() per user turn with `resume`, we hand the SDK
# an async generator of user messages as the prompt. The SDK keeps a single
# session open and pulls messages from the iterable as they arrive.
#
# Trade-offs vs ./main.py:
#   + Single connection, no per-turn session rehydration
#   + Natural fit if you're already plumbing async streams (web servers, etc.)
#   - Slightly more conceptual overhead — you're juggling two async generators
#
# Run with: make step-5-streaming

import asyncio
from collections.abc import AsyncGenerator

from agent import build_agent_options
from claude_agent_sdk import AssistantMessage, ResultMessage, TextBlock, query


async def prompt(label: str) -> str:
    return (await asyncio.to_thread(input, label)).strip()


async def user_inputs() -> AsyncGenerator[dict, None]:
    print("Workshop agent (streaming mode). Type /exit to quit.\n")
    while True:
        user_input = await prompt("you > ")
        if user_input == "/exit" or user_input == "":
            return
        print("agent > ", end="", flush=True)
        yield {
            "type": "user",
            "message": {"role": "user", "content": user_input},
            "parent_tool_use_id": None,
        }


async def main() -> None:
    async for message in query(prompt=user_inputs(), options=build_agent_options()):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text, end="", flush=True)
        elif isinstance(message, ResultMessage):
            # Each turn still produces its own `result` event — same event shape
            # as the resume-based variant. The only structural difference between
            # the two is that we keep ONE query() alive across all turns here,
            # whereas the resume variant calls query() once per turn.
            print("\n")


if __name__ == "__main__":
    asyncio.run(main())
