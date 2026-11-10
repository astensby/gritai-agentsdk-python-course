# Step 8 — Hooks

Intercept the agent loop with pure Python async functions. Two flavours: **observability** (log every tool call) and **safety** (block dangerous ones).

## What's new

- The `hooks` option in `ClaudeAgentOptions`
- `HookMatcher(matcher=..., hooks=[...])` — group of hooks bound to a tool-name matcher
- Returning `permissionDecision: "deny"` from a PreToolUse hook to block a tool call
- `on_failure="block"` on a matcher, so a hook that crashes stops the tool call instead of letting it through

## Run it

```bash
# from the repo root (one-time setup is in the main README)
make step-8
```

You'll see lines like:

```
  [hook] Write → {"file_path": "…/notes.txt", "content": "Use 'enumerate' instead of..."}
  [hook] Bash → {"command": "rm …/notes.txt"}
  ↑ blocked by hook
  [hook] Bash → {"command": "ls …"}
```

The agent tried to `rm`, got blocked, recovered, and continued.

## How it works

```python
from claude_agent_sdk import ClaudeAgentOptions, HookMatcher

options = ClaudeAgentOptions(
    hooks={
        "PreToolUse": [
            HookMatcher(hooks=[log_tool_calls]),                  # matcher omitted = all tools
            HookMatcher(matcher="Bash", hooks=[block_dangerous_bash], on_failure="block"),  # matcher = tool name pattern
        ],
    },
)
```

Each hook event (`PreToolUse`, `PostToolUse`, `Stop`, ...) takes a list of `HookMatcher` groups. Each group runs its hooks against tool calls that match the `matcher`.

> **On ordering:** the SDK dispatches multiple matcher groups on the *same* event **concurrently**, so don't build a chain where one hook depends on another having already run. The output here happens to arrive tidily — the log line, then the block — but that's incidental rather than guaranteed.

The hook callback signature is:

```python
async def my_hook(input_data, tool_use_id, context):
    # input_data["tool_name"], input_data["tool_input"], etc.
    return {}
    # or to block:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",  # or "allow" / "ask"
            "permissionDecisionReason": "...",
            # "updatedInput": {...},  # optionally rewrite the tool input
        },
    }
```

> Note the camelCase keys in the return payload. This is the SDK's wire format to the agent process — it mirrors the JS SDK on purpose. The Python option fields (`allowed_tools`, `add_dirs`, ...) are snake_case, but the hook-response dict is not.

## Available hook events

These ten are the **complete** list — the `HookEvent` union in the SDK types. Worth knowing it's closed, because the Claude Code **CLI** has its own hook events that are *not* available here: register a `SessionStart` or `SessionEnd` hook through the SDK and it silently does nothing.

| Event | When it fires |
|---|---|
| `PreToolUse` | Before a tool runs (most common) |
| `PostToolUse` | After a tool returns |
| `PostToolUseFailure` | After a tool throws |
| `UserPromptSubmit` | When a new user message arrives |
| `Stop` | The agent thinks it's done (turn end) |
| `SubagentStart` | A subagent was spawned (pairs with step 7) |
| `SubagentStop` | A subagent finished (pairs with step 7) |
| `PreCompact` | Before context compaction |
| `Notification` | The agent wants to notify the host |
| `PermissionRequest` | Around a permission check (pairs with step 9) |

## Hooks vs `can_use_tool` vs `allowed_tools`

|   | `allowed_tools` | `can_use_tool` | Hooks |
|---|---|---|---|
| **Where it lives** | Static config | Single callback | Per-event matcher groups |
| **What it can do** | Auto-approve list | Allow / deny (and rewrite the input) | Allow / deny / ask / rewrite / observe |
| **Granularity** | Per tool name | Per tool call | Per event |
| **When to reach for it** | Coarse access control | Interactive permission UX (step 9) | Logging, auditing, safety rails, side-effects |

## Gotchas

- The hook RETURN dict uses camelCase (`hookSpecificOutput`, `hookEventName`, `permissionDecision`, `permissionDecisionReason`). The `ClaudeAgentOptions` fields around it are snake_case. Easy to mix up.
- The regex `\brm\b` is intentionally crude — it blocks plain `rm notes.txt`. A real deny rule needs more care than a substring match.
- **Hooks fail open by default.** A callback that raises or returns `None` does not stop the agent: Claude Code logs the error (a long stack trace on stderr) and the tool **runs anyway**. So a safety hook needs `on_failure="block"` on its matcher, as the Bash matcher here has (SDK 0.2.177+). A failing callback then blocks the call, whatever the command was, so a broken check stops harmless commands too.
- **`updatedInput` is validated.** Rewrites must be valid input for that tool; unknown keys are dropped.

## Try this

- Add a `PostToolUse` hook that records latency per tool call to a CSV.
- Use `updatedInput` to redact a secret from any `Bash` command before it runs.
- Add `raise RuntimeError("down")` as the first line of `block_dangerous_bash` and run it. You get a stack trace, every Bash call is blocked, and the agent tells you nothing ran. Then remove `on_failure="block"` and run it again: same stack trace, but the commands run, `rm` included. The sandbox can look empty both times, so read what the agent reports.
- Add a `Stop` hook that prints a "done" banner when the agent finishes.

## Next

[Step 9 — Permissions](../step-9-permissions): the *interactive* approval pattern (`can_use_tool`), which is the higher-level cousin of PreToolUse hooks.
