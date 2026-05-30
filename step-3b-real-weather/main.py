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
        model="claude-sonnet-4-6",
        # Mount our in-process MCP server. The key ("weather") becomes the tool prefix.
        mcp_servers={"weather": weather_server},
        # Whitelist — same rules as step 2.
        allowed_tools=[
            "mcp__weather__getWeather",
            "mcp__weather__getForecast",
        ],
    )

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
            print(f"\n\n---\nCost: ${message.total_cost_usd:.6f}")


if __name__ == "__main__":
    asyncio.run(main())
