# Step 2 — External MCP Server

Plug an existing MCP server into the agent. The agent gains real-world tools.

## What's new vs step 1

- `mcp_servers` option on `ClaudeAgentOptions` — declares MCP servers the agent can use
- `allowed_tools` option — the **mandatory whitelist** for MCP tools
- The agent now runs a tool loop autonomously (call tool → observe → decide → respond)

## Run it

```bash
# from the repo root (one-time setup is in the main README)
make step-2
```

Then look in `./sandbox/` — there should be a `haiku.txt` with a freshly-written haiku.

## How it works

```python
mcp_servers={
    "fs": {                                                       # ← key becomes tool prefix
        "type": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", str(SANDBOX_DIR)],
    },
}
```

The SDK spawns that command, speaks the **Model Context Protocol** over its stdin/stdout, and exposes its tools to the agent under the name `mcp__fs__<tool>`. The official `@modelcontextprotocol/server-filesystem` package gives you `read_text_file` (and the now-deprecated `read_file`), `write_file`, `list_directory`, etc., scoped to the directory you pass as an argument.

## The whitelist gotcha

Without `allowed_tools`, the agent sees no MCP tools — even though they're declared. The SDK denies all MCP tools by default. Pick one:

```python
allowed_tools=["mcp__fs__*"]                            # wildcard: easy, broad
# or
allowed_tools=[
    "mcp__fs__write_file",                              # explicit: principle of least privilege
    "mcp__fs__read_text_file",
]
```

The MCP server itself decides what tools it offers; `allowed_tools` is just the agent-side permission gate.

The code in this step uses the **explicit form** to model principle-of-least-privilege. For quick prototyping, the wildcard is fine.

## Try this

- Comment out the `allowed_tools` line and rerun. The agent will refuse to create the file. That's the gotcha in action.
- Add `"mcp__fs__list_directory"` to the prompt's request: *"List the files in your sandbox, then create..."*. Watch the extra tool call show up in the trace.
- Swap `@modelcontextprotocol/server-filesystem` for another stdio MCP server (e.g., `@modelcontextprotocol/server-github`). The pattern is identical.

## Next

In step 3, instead of using somebody else's MCP server, we'll **write our own tools** in plain Python and expose them via the SDK's in-process MCP helper (`create_sdk_mcp_server`).
