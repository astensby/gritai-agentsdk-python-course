# Step 2b — Built-in Tools (no MCP needed)

A correction to a common misconception you might have picked up after step 2: **you don't need MCP for everything.** The Agent SDK ships with the same file and shell tools that Claude Code uses, built in.

## What's new vs step 2

- No MCP server at all
- `allowed_tools=["Read", "Write", "Bash"]` — bare names, not `mcp__*`
- `add_dirs` to scope file access

## Run it

```bash
# from the repo root (one-time setup is in the main README)
make step-2b
```

Same outcome as step 2 (a file gets created in `./sandbox/`), but with zero MCP plumbing.

## When to use which

| Use built-in tools | Use MCP |
|---|---|
| Local file I/O (`Read`, `Write`, `Edit`) | Calling external services (GitHub, Slack, Postgres, ...) |
| Running shell commands (`Bash`) | Wrapping your own business logic as a tool (step 3) |
| Searching the codebase (`Grep`, `Glob`) | Tools that need to live in their own process |
| Delegating to subagents (`Agent`, see step 7) | Reusing the same tool across multiple agents/languages |

The built-in toolset is essentially the same toolbox you use when you talk to Claude Code on the command line. Same `Read`, same `Write`, same `Bash`.

## The built-in tools

| Tool | What it does |
|---|---|
| `Read` | Read a file. Supports images and PDFs too. |
| `Write` | Write a file (overwrites existing). |
| `Edit` | Find-and-replace within a file. |
| `Bash` | Run a shell command. |
| `Glob` | Find files by pattern. |
| `Grep` | Search file contents with regex. |
| `Agent` | Delegate to a subagent (see [step 7](../step-7-subagents)). Older CLIs called it `Task`, still accepted as an alias. |
| `WebFetch`, `WebSearch` | Fetch a URL or search the web. |

The to-do tools (`TodoWrite`, `TaskCreate`) aren't in the default set on Sonnet 5 and later, so don't plan around them.

See [the Agent SDK docs](https://code.claude.com/docs/en/agent-sdk/python) for the full list and their input shapes.

## The `add_dirs` gotcha

Built-in file tools can only operate inside the current working directory **plus** any paths you list in `add_dirs`. In this demo the sandbox lives *inside* the project folder (the cwd when you run the step), so the agent could reach it either way — here `add_dirs` is belt-and-suspenders. You need it the moment the agent must touch a path **outside** the project (a shared data dir, `/tmp`, a sibling repo). It's the same principle-of-least-privilege idea as `allowed_tools`.

## `allowed_tools` is an auto-approve list, not a sandbox

A subtle but important point: `allowed_tools` lists the tools that run **without an approval prompt**. It does **not** restrict which tools exist. Leave `Bash` out and the model can still call it: a read-only command like `ls` is approved by itself, and anything else falls through to the permission mode, which in a headless run usually means denied. To actually *remove* a tool, use `disallowed_tools`.

## Try this

- **Actually block the shell:** add `disallowed_tools=["Bash"]` to the options, change the prompt to "run `ls` in the sandbox," and re-run. Now it can't. (Just *omitting* `Bash` from `allowed_tools` is **not** enough: `ls` is approved on its own. See the note above.)
- Change the prompt to also ask the agent to `Read` the file back, then re-run and watch the `[tool call]` trace.
- Combine built-ins and MCP in the same `allowed_tools` list — both worlds can coexist.

## Next

Back to MCP in [step 3](../step-3-custom-mcp), but now you know: MCP is for the cases the built-ins don't already cover.
