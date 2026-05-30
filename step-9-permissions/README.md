# Step 9 — Interactive Permissions

The "Claude wants to run X — allow?" pattern you've seen in Claude Code itself. Step 8's hooks are programmatic; this is the *interactive* cousin.

## What's new

- The `can_use_tool` callback in `ClaudeAgentOptions`
- The `PermissionResultAllow` / `PermissionResultDeny` shape
- The `permission_mode` option (`default` / `acceptEdits` / `plan` / `bypassPermissions`)

## Run it

```bash
# from the repo root (one-time setup is in the main README)
make step-9
```

For every tool the agent wants to use, you'll see:

```
┌─ Permission request ──────────────────────
│ Claude wants to write …/pizza.txt
│ Input: {'file_path': '…/pizza.txt', 'content': '…'}
└────────────────────────────────────────────
[y]es / [n]o / [a]lways allow >
```

Hit `y`, `n`, or `a`. `a` remembers your decision for that tool for the rest of the session.

## How it works

```python
from claude_agent_sdk import PermissionResultAllow, PermissionResultDeny

async def can_use_tool(tool_name, tool_input, context):
    # ask the user...
    return PermissionResultAllow(
        updated_input=tool_input,        # optional: rewrite before running
    )
    # or:
    return PermissionResultDeny(
        message="User declined.",         # ← the agent sees this as tool_result
    )

options = ClaudeAgentOptions(
    allowed_tools=[],     # ← empty: nothing is auto-allowed
    can_use_tool=can_use_tool,
)
```

A tool call goes through this order:

1. **Is it in `allowed_tools`?** → run immediately
2. **Else, do PreToolUse hooks say deny?** → block (step 8 pattern)
3. **Else, is there a `can_use_tool` callback?** → call it, use its decision
4. **Else** → default to deny

## `permission_mode` cheat sheet

| Mode | Behaviour |
|---|---|
| `default` | Route uncertain tools through `can_use_tool` |
| `acceptEdits` | Auto-allow file edits, still ask for Bash/network |
| `plan` | Research-only mode — agent produces a plan, doesn't act |
| `bypassPermissions` | Auto-allow everything. **Dangerous.** Requires `allow_dangerously_skip_permissions=True` |
| `dontAsk` | Auto-deny anything not in `allowed_tools` (good for headless agents) |
| `auto` | A model classifier approves/denies each prompt for you |

## `PermissionResultAllow` returning `updated_input`

The callback can **rewrite** the input before the tool runs:

```python
return PermissionResultAllow(
    updated_input={**tool_input, "command": tool_input["command"].replace("--force", "")},
)
```

Useful for stripping risky flags, redacting secrets, or pinning paths.

## Gotchas

- We use `asyncio.to_thread(input, ...)` to read stdin without blocking the SDK's event loop — no extra deps like `aioconsole` required.
- `ALWAYS_ALLOW` is a per-process set keyed by tool name. Persist it to disk if you want decisions to survive restarts.
- `PermissionResult` only has `"allow"` and `"deny"`. The third value `"ask"` that appears elsewhere in the SDK types is for **hook** outputs (`PreToolUseHookSpecificOutput.permissionDecision`), NOT for `can_use_tool`.

## Try this

- Switch to `permission_mode="plan"` and rerun. The agent produces a plan without touching the filesystem.
- Put `Read` and `Glob` into `allowed_tools` so only the risky ones (Write, Bash) prompt.
- Wire `can_use_tool` into a Slack DM bot — same callback shape, different transport.

## Next

[Step 10 — Capstone: meeting-notes agent](../step-10-capstone-meeting-notes): compose built-ins, a skill, and a hook into one useful agent.
