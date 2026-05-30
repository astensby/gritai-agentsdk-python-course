"""
Step 2 — External MCP Server

We give the agent access to a sandbox folder via an EXTERNAL MCP server —
in this case, the official filesystem server from the Anthropic / MCP team.
The SDK launches it as a subprocess over stdio and bridges its tools into
the agent's tool catalogue.

Two new ClaudeAgentOptions fields earn their keep here:

  * mcp_servers — a dict of MCP server configs. The KEY ("fs" below) becomes
    part of the tool name the model sees: tools are auto-namespaced as
    `mcp__fs__<tool>`.
  * allowed_tools — the mandatory whitelist for MCP tools. The SDK denies
    all MCP tools by default; you MUST opt them in. Wildcards work
    (`mcp__fs__*`); explicit names give you tighter principle-of-least-
    privilege. We list the ones this step needs.

Same prompt as the TS version: write a haiku to a file, then read it back.
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

# Sandbox lives next to this file. The filesystem MCP server is sandboxed to
# this directory — it cannot read or write anything outside it.
SANDBOX_DIR = Path(__file__).parent / "sandbox"


async def main() -> None:
    options = ClaudeAgentOptions(
        model="claude-sonnet-4-6",
        # Configure MCP servers. The KEY here ("fs") becomes part of the tool
        # name the model sees: tools are auto-namespaced as `mcp__fs__<tool>`.
        mcp_servers={
            "fs": {
                # stdio transport: the SDK runs this command and talks MCP
                # over its stdin/stdout.
                "type": "stdio",
                "command": "npx",
                "args": [
                    "-y",
                    "@modelcontextprotocol/server-filesystem",
                    str(SANDBOX_DIR),
                ],
            },
        },
        # *** This is the line participants most commonly forget. ***
        # MCP tools are denied by default. You MUST whitelist them.
        # Wildcards work (`mcp__fs__*`). Explicit names give you tighter
        # principle-of-least-privilege. We list the ones this step needs.
        # Note: this server now prefers `read_text_file` and marks `read_file`
        # deprecated, so we allow both — otherwise the "read it back" step can
        # be silently denied when the model picks the newer name.
        allowed_tools=[
            "mcp__fs__write_file",
            "mcp__fs__read_text_file",
            "mcp__fs__read_file",
            "mcp__fs__list_directory",
        ],
    )

    prompt = (
        "Create a file called 'haiku.txt' in your working directory. "
        "Write a short haiku about coffee inside it. "
        "Then read it back to confirm."
    )

    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text, end="", flush=True)
                elif isinstance(block, ToolUseBlock):
                    # Useful while learning: see every tool the agent decides to call.
                    print(f"\n[tool call] {block.name}({block.input})")
        elif isinstance(message, ResultMessage):
            print(f"\n\n---\nCost: ${message.total_cost_usd:.6f}")
            print("Check ./sandbox/ — the file should be there.")


if __name__ == "__main__":
    asyncio.run(main())
