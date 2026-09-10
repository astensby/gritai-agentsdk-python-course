"""
Step 3 — Custom MCP Server (in-process)

Wrap your own Python functions as MCP tools using the SDK's `create_sdk_mcp_server`
helper. No subprocess, no JSON-RPC plumbing — just async functions.

The tools live in a sibling file `weather_server.py` (mirroring the TS
`weather-server.ts`). Here in main.py we just import the bundled server,
mount it under `mcp_servers`, and whitelist the two tool names.

Tool names that come from an SDK MCP server show up as
`mcp__<server-key>__<tool-name>` — here, `mcp__weather__getWeather` and
`mcp__weather__getForecast`.
"""

import asyncio

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    query,
)
from weather_server import weather_server


async def main() -> None:
    options = ClaudeAgentOptions(
        model="claude-sonnet-5",
        # Mount our in-process MCP server. The key ("weather") becomes the
        # tool-name prefix the model sees.
        mcp_servers={"weather": weather_server},
        # Whitelist — same rules as step 2.
        allowed_tools=[
            "mcp__weather__getWeather",
            "mcp__weather__getForecast",
        ],
    )

    prompt = (
        "What's the weather in Oslo right now? Also give me a 3-day forecast for San Francisco."
    )

    # `result` means "a turn ended", not "the run is over" — a stream can
    # carry several. Accumulate, print once. (Step 7 shows why.)
    total_cost = 0.0

    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text, end="", flush=True)
                elif isinstance(block, ToolUseBlock):
                    print(f"\n[tool call] {block.name}({block.input})")
        elif isinstance(message, ResultMessage):
            total_cost += message.total_cost_usd or 0.0

    print(f"\n\n---\nCost: ${total_cost:.6f}")


if __name__ == "__main__":
    asyncio.run(main())
