"""
Same setup as step 3 — same `tool()` definitions, same mounting, same
allowlist. The ONLY difference is that the tool handlers in
`weather_server.py` now call a real weather API instead of returning canned
data. The agent doesn't know or care: a tool is a tool.
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
        # Mount our in-process MCP server. The key ("weather") becomes the tool prefix.
        mcp_servers={"weather": weather_server},
        # Whitelist — same rules as step 2.
        allowed_tools=[
            "mcp__weather__getWeather",
            "mcp__weather__getForecast",
        ],
    )

    # `result` means "a turn ended", not "the run is over" — a stream can
    # carry several. Accumulate, print once. (Step 7 shows why.)
    total_cost = 0.0

    async for message in query(
        prompt=(
            "What's the weather in Oslo right now? Also give me a 3-day forecast for San Francisco."
        ),
        options=options,
    ):
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
