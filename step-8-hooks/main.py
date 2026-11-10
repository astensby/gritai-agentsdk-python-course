"""
Step 8 — Hooks

HOOKS let you intercept the agent loop. The SDK's hook events are exactly
these ten — no more, and it's worth knowing the list, because the CLI has
its OWN hook events (SessionStart, SessionEnd, ...) that are NOT available
here. Registering one of those silently does nothing:

    PreToolUse          before a tool runs      (both demos below)
    PostToolUse         after a tool returns
    PostToolUseFailure  after a tool throws
    UserPromptSubmit    a prompt was submitted
    Stop                the turn ended
    SubagentStop        a subagent finished     (pairs with step 7)
    SubagentStart       a subagent was spawned  (pairs with step 7)
    PreCompact          before context compaction
    Notification        the agent wants to notify the host
    PermissionRequest   around a permission check (pairs with step 9)

Two patterns we'll demo:

 1. PreToolUse for OBSERVABILITY — print every tool call as it happens.
 2. PreToolUse for SAFETY — block any Bash command that contains `rm` or `sudo`.

Hooks are pure async functions (not config) and run in your process — so they
can do anything: write logs, send metrics, decide allow/deny, even rewrite
the tool input.

Two registration shapes:
  - HookMatcher(hooks=[fn])              — no matcher: fires on every tool
  - HookMatcher(matcher="Bash", hooks=[fn]) — fires only when the tool name matches

Both fire for a Bash call: the unmatched logger AND the Bash-matched blocker.
One caveat — the SDK dispatches multiple matchers on the SAME event
CONCURRENTLY, so don't build a chain where one hook depends on another having
already run. The output below happens to arrive in a tidy order (the log line,
then the block), but that's incidental rather than guaranteed.

*** HOOKS FAIL OPEN BY DEFAULT. *** If a hook callback raises, or returns
None, Claude Code logs the failure and the tool RUNS ANYWAY. A broken safety
check is the same as no safety check, so the Bash matcher below sets
`on_failure="block"`: if the callback fails, the tool call is blocked instead.
Set it on every hook whose job is safety. (Needs SDK 0.2.177 or later.)

Note: the hook RETURN VALUE uses camelCase keys (`hookSpecificOutput`,
`hookEventName`, `permissionDecision`, `permissionDecisionReason`). The SDK
forwards this payload to the agent process verbatim — same wire format as
the TS SDK — so the schema mirrors the JS side, not the Python option fields.
"""

import asyncio
import json
import re
from pathlib import Path

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    HookMatcher,
    ResultMessage,
    TextBlock,
    query,
)

SANDBOX_DIR = (Path(__file__).parent / "sandbox").resolve()


# --- Hook 1: log every tool call --------------------------------------------
async def log_tool_calls(input_data, tool_use_id, context):
    tool_name = input_data.get("tool_name", "?")
    full = json.dumps(input_data.get("tool_input", {}))
    summary = full[:80]
    suffix = "…" if len(full) > 80 else ""
    print(f"  [hook] {tool_name} → {summary}{suffix}")
    # Empty return = continue normally. The agent doesn't know we ran.
    return {}


# --- Hook 2: block dangerous shell commands ---------------------------------
# Registered with matcher="Bash", so it only ever receives Bash calls.
async def block_dangerous_bash(input_data, tool_use_id, context):
    cmd = input_data.get("tool_input", {}).get("command", "") or ""
    # Match any `rm` (with or without flags) and any `sudo`. Keeping it to a
    # bare `\brm\b` means the block fires even on a plain `rm notes.txt` —
    # a real deny rule would need more care than a substring match.
    if re.search(r"\brm\b", cmd, re.IGNORECASE) or re.search(r"\bsudo\b", cmd, re.IGNORECASE):
        print("  ↑ blocked by hook")
        return {
            # `deny` short-circuits before the tool runs. The agent gets a
            # tool_result it can read, recover from, or apologize for.
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    "Hook blocked: rm/sudo commands are not allowed in this demo."
                ),
            }
        }
    return {}


async def main():
    options = ClaudeAgentOptions(
        model="claude-sonnet-5-5",
        # Ignore ~/.claude so this run depends only on this file. See step 1.
        setting_sources=[],
        allowed_tools=["Read", "Write", "Bash"],
        add_dirs=[str(SANDBOX_DIR)],
        # Hooks are grouped by event, then by matcher. The matcher is a
        # tool-name pattern; omitted means "all tools".
        hooks={
            "PreToolUse": [
                HookMatcher(hooks=[log_tool_calls]),  # fires for every tool
                # Only for Bash. If this safety check crashes, block the call.
                HookMatcher(matcher="Bash", hooks=[block_dangerous_bash], on_failure="block"),
            ],
        },
    )

    prompt = (
        f"Write a file called notes.txt in {SANDBOX_DIR} with one Python tip, "
        f"then try to delete it with rm. After that, list the files in {SANDBOX_DIR}."
    )

    # `result` means "a turn ended", not "the run is over" — a stream can
    # carry several, and `total_cost_usd` on each one is the running total for
    # the whole call. Keep the latest, print once. (Step 7 shows why.)
    total_cost = 0.0

    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text, end="", flush=True)
        elif isinstance(message, ResultMessage):
            total_cost = message.total_cost_usd or total_cost

    print(f"\n\n---\nCost: ${total_cost:.6f}")


if __name__ == "__main__":
    asyncio.run(main())
