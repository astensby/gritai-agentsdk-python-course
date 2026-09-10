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

*** TWO TRAPS THAT WILL SILENTLY BREAK THIS STEP. ***

Both fail the same way: the run exits zero, the agent reports success, and the
file is not where you expected. Neither shows up as an error — so the habit to
build is CHECK WHERE THE FILE LANDED, not whether the program crashed.

1. `allowed_tools` IS AUTO-APPROVE, NOT A SANDBOX.
   It grants tools; it never removes any. The built-in Write/Edit/Bash tools
   always exist, and current models PREFER them over an MCP filesystem tool.
   Allow only `mcp__fs__*` and the agent will still happily reach for the
   built-in `Write` — and write wherever it likes, outside your sandbox.
   `disallowed_tools` is what actually closes that door.

   Try it: comment out `disallowed_tools` below and re-run. Watch which tool
   the agent picks, and where `haiku.txt` ends up.

2. MCP ROOTS OVERRIDE THE SERVER'S OWN CLI ARGUMENT.
   The filesystem server implements the MCP `roots` protocol: on connect it
   asks the client which directories it may touch and, if it gets an answer,
   REPLACES its allowed directories with them. The Agent SDK answers with its
   `cwd`. So the path we pass on the command line below is only a FALLBACK,
   and the sandbox widens to wherever `cwd` happens to be. Setting `cwd` to
   the sandbox makes the two agree.

   This generalises: a well-behaved MCP server asks its client what it may
   touch, and the client wins. "The server's CLI argument is the sandbox" is
   not true against a roots-aware client — and not every client is one. Step
   11 mounts this same server from a client that does NOT advertise roots and
   logs exactly that. Same server, two clients, two different sandboxes.

The task: write a haiku to a file, then read it back.
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

# Sandbox lives next to this file. The filesystem MCP server is scoped to this
# directory — but read trap 2 above before you trust that sentence: the scope
# it ends up with depends on the roots handshake, not just this path.
SANDBOX_DIR = (Path(__file__).parent / "sandbox").resolve()


async def main() -> None:
    options = ClaudeAgentOptions(
        model="claude-sonnet-5",
        # The MCP roots handshake (see docstring) answers with `cwd`, so point
        # it at the sandbox. Without this the server's CLI argument is ignored
        # and the agent gets the whole project.
        cwd=str(SANDBOX_DIR),
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
                    # Pin the version. `npx -y <pkg>` with no version fetches
                    # whatever is newest AT RUN TIME, so two people running this
                    # on different days can get different servers. This server's
                    # roots behaviour (see docstring) arrived in one such
                    # release — pinning is how you keep a demo reproducible.
                    "@modelcontextprotocol/server-filesystem@2026.8.31",
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
            # Makes the roots handshake visible in the trace — the server
            # reports the directory it actually ended up sandboxed to.
            "mcp__fs__list_allowed_directories",
        ],
        # *** The line that makes this step actually about MCP. ***
        # Allowing the MCP tools does not DISALLOW the built-ins, and the model
        # prefers the built-ins for file work. Close that door explicitly or the
        # MCP server never gets used. See docstring, point 1.
        disallowed_tools=["Write", "Edit", "Bash"],
    )

    prompt = (
        "Create a file called 'haiku.txt' in your working directory. "
        "Write a short haiku about coffee inside it. "
        "Then read it back to confirm. "
        # Belt-and-braces alongside disallowed_tools: naming the toolset stops
        # the agent wasting a turn reaching for a built-in it can't have.
        # `disallowed_tools` says what it CAN'T use; this says what it SHOULD.
        "Use the mcp__fs__* tools for all file access. "
        "First call mcp__fs__list_allowed_directories so we can see which "
        "sandbox the server actually ended up with."
    )

    # `result` means "a turn ended", not "the run is over" — a stream can carry
    # several. Accumulate, print once. (Step 7 is where this really bites.)
    total_cost = 0.0

    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text, end="", flush=True)
                elif isinstance(block, ToolUseBlock):
                    # Useful while learning: see every tool the agent decides to call.
                    print(f"\n[tool call] {block.name}({block.input})")
        elif isinstance(message, ResultMessage):
            total_cost += message.total_cost_usd or 0.0

    print(f"\n\n---\nCost: ${total_cost:.6f}")
    print(f"Check {SANDBOX_DIR} — the file should be there.")


if __name__ == "__main__":
    asyncio.run(main())
