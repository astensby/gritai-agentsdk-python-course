# Step 9 — Interactive Permissions

The "Claude wants to run X — allow?" pattern you've seen in Claude Code itself. Step 8's hooks are programmatic; this is the *interactive* cousin.

> **A plain string prompt is enough.** If you come across older examples that wrap a single prompt
> in an async generator before calling `query()`, that was a workaround for a time when the SDK
> only opened the control channel it uses to call `can_use_tool` in streaming-input mode. It keeps
> stdin open for a string prompt now, so the callback fires either way.

## What's new

- The `can_use_tool` callback in `ClaudeAgentOptions`
- The `PermissionResultAllow` / `PermissionResultDeny` shape
- The `permission_mode` option (`default` / `acceptEdits` / `plan` / `bypassPermissions` / `dontAsk` / `auto`)

## Run it

```bash
# from the repo root (one-time setup is in the main README)
make step-9
```

For each call that needs approval you'll see the prompt below. Expect one for the write (usually `Write`, sometimes a shell command that writes), and **none** for the read-back or `ls`: read-only work inside your project is approved on its own.

```
┌─ Permission request ──────────────────────
│ Allow tool: Write?
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
    allowed_tools=[],     # ← empty: nothing is pre-approved by an allow rule
    can_use_tool=can_use_tool,
)
```

A tool call goes through this order, and the first step that decides ends it:

1. **Hooks** — a `PreToolUse` hook can deny outright (step 8)
2. **Deny rules** — `disallowed_tools` and settings files; holds even in `bypassPermissions`
3. **Ask rules** — from settings files; these send the call to your callback
4. **Permission mode** — `acceptEdits`, `bypassPermissions`, `plan` and `auto` may decide here
5. **Allow rules** — `allowed_tools` and settings files; read-only work inside your project is also approved here
6. **`can_use_tool`** — only if nothing above decided. With no callback, the call is denied

So `allowed_tools` does not run first, and a hook that returns `allow` doesn't get past a deny rule.

## `permission_mode` cheat sheet

| Mode | Behaviour |
|---|---|
| `default` | No auto-approvals from the mode; calls that need approval and match no allow rule go to `can_use_tool` |
| `acceptEdits` | Auto-allow file edits, still ask for Bash/network |
| `plan` | Research-only mode — agent produces a plan, doesn't act |
| `bypassPermissions` | Auto-allow everything. **Dangerous.** Requires `allow_dangerously_skip_permissions=True` |
| `dontAsk` | Deny instead of prompting, without calling `can_use_tool` (good for headless agents) |
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
- Add a prompt that needs a non-read-only `Bash` command, and watch it reach the callback where `ls` didn't.
- Wire `can_use_tool` into a Slack DM bot — same callback shape, different transport.

## Next

[Step 10 — Capstone: meeting-notes agent](../step-10-capstone-meeting-notes): compose built-ins, a skill, and a hook into one useful agent.
