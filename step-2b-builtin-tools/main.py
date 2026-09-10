"""
Step 2b — Built-in tools (no MCP needed)

Plot twist: step 2 used an EXTERNAL MCP server to read and write files.
You don't need MCP for that. The Agent SDK ships with built-in file and
shell tools: Read, Write, Edit, Bash, Glob, Grep — the same toolset
Claude Code uses.

Reach for MCP when you want to integrate with EXTERNAL services
(GitHub, Slack, Postgres) or wrap YOUR OWN business logic.
For local files? Just use the built-ins.
"""

import asyncio
from pathlib import Path

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    query,
)

SANDBOX_DIR = (Path(__file__).resolve().parent / "sandbox").resolve()


async def main() -> None:
    prompt = (
        f"Create a file called 'limerick.txt' in {SANDBOX_DIR} with a short "
        f"limerick about Python. Then read it back to confirm."
    )

    options = ClaudeAgentOptions(
        model="claude-sonnet-5",
        # Just whitelist the built-in tools by their bare names. No MCP at all.
        # (Tools without `mcp__` prefix are built-ins.)
        allowed_tools=["Read", "Write", "Bash"],
        # Built-in file tools are scoped to add_dirs.
        # Without this, the agent can only touch CWD and below.
        add_dirs=[SANDBOX_DIR],
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
                    summary = str(block.input)[:100]
                    print(f"\n[tool call] {block.name}({summary})")
        elif isinstance(message, ResultMessage):
            total_cost += message.total_cost_usd or 0.0

    print(f"\n\n---\nCost: ${total_cost:.6f}")
    print(f"Check {SANDBOX_DIR}/limerick.txt")


if __name__ == "__main__":
    asyncio.run(main())
