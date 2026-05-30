# Multi-turn chat in the terminal.
#
# Approach: call query() once per user message, passing `resume=session_id`
# from the second turn onwards. The SDK rehydrates the prior conversation
# from its session log so the agent has full context.
#
# This is the clearest pattern for teaching. For a more advanced pattern
# that keeps a single query() alive across turns (better for some streaming
# scenarios), see ./main_streaming.py.

import asyncio
from dataclasses import replace

from agent import build_agent_options
from claude_agent_sdk import AssistantMessage, SystemMessage, TextBlock, query


async def prompt(label: str) -> str:
    # Built-in input() blocks the event loop; run it in a worker thread so
    # the SDK's async machinery stays responsive.
    return (await asyncio.to_thread(input, label)).strip()


async def main() -> None:
    base_options = build_agent_options()
    session_id: str | None = None

    print("Workshop agent. Type /exit (or an empty line) to quit.\n")

    while True:
        user_input = await prompt("you > ")
        if user_input == "/exit" or user_input == "":
            break

        print("agent > ", end="", flush=True)

        # On the first turn there's no session yet — the SDK creates one and
        # emits its ID in the `system: init` message. From then on we pass
        # `resume=session_id` so the SDK rehydrates the full prior conversation.
        turn_options = replace(base_options, resume=session_id) if session_id else base_options

        async for message in query(prompt=user_input, options=turn_options):
            if isinstance(message, SystemMessage):
                if message.subtype == "init":
                    session_id = message.data.get("session_id")
            elif isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(block.text, end="", flush=True)

        print("\n")


if __name__ == "__main__":
    asyncio.run(main())
