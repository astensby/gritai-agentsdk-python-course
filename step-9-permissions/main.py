"""
Step 9 — Interactive Permissions

`can_use_tool` is the INTERACTIVE permission pattern — the "Claude wants to
run X — allow?" prompt you've seen in Claude Code itself.

Whereas:
  - `allowed_tools` is a static whitelist
  - PreToolUse hooks are programmatic (deny on a regex, etc.)
can_use_tool is a single async callback the SDK calls before EVERY tool
use that isn't already covered by allowed_tools — and you can ask the
human whatever you want before deciding.

Other relevant permission_mode values:
  "default"            — ask via can_use_tool (what we use)
  "acceptEdits"        — auto-allow file edits (still ask for Bash etc.)
  "bypassPermissions"  — YOLO, no prompts (also requires
                         allow_dangerously_skip_permissions: True)
  "plan"               — research-only mode; agent produces a plan instead of acting
  "dontAsk"            — never prompt; deny anything not pre-approved (headless)
  "auto"               — a model classifier approves/denies each prompt

Note: PermissionResult only has behavior "allow" | "deny". The third value
"ask" you may see in the SDK types is for hook outputs
(PreToolUseHookSpecificOutput.permissionDecision), NOT for can_use_tool.
"""

import asyncio
from pathlib import Path

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    PermissionResultAllow,
    PermissionResultDeny,
    ResultMessage,
    TextBlock,
    query,
)

SANDBOX_DIR = (Path(__file__).parent / "sandbox").resolve()

# Remember decisions per tool so we don't ask the same question twice.
ALWAYS_ALLOW: set[str] = set()


async def can_use_tool(tool_name, tool_input, context):
    if tool_name in ALWAYS_ALLOW:
        return PermissionResultAllow(updated_input=tool_input)

    # The SDK gives us a pre-rendered prompt sentence when available.
    prompt = context.title or f"Allow tool: {tool_name}?"
    summary = str(tool_input)[:120]

    print("\n┌─ Permission request ──────────────────────")
    print(f"│ {prompt}")
    print(f"│ Input: {summary}")
    print("└────────────────────────────────────────────")

    # asyncio.to_thread keeps the SDK event loop responsive while blocking
    # input() runs on a worker thread (no extra deps required).
    answer = (await asyncio.to_thread(input, "[y]es / [n]o / [a]lways allow > ")).strip().lower()

    if answer == "a":
        ALWAYS_ALLOW.add(tool_name)
        return PermissionResultAllow(updated_input=tool_input)
    if answer == "y" or answer == "":
        return PermissionResultAllow(updated_input=tool_input)
    return PermissionResultDeny(
        message=(
            f"User declined {tool_name}. Don't retry — explain what you would have done instead."
        ),
    )


async def main():
    options = ClaudeAgentOptions(
        model="claude-sonnet-5",
        # NOTE: we deliberately leave allowed_tools empty so EVERY tool call
        # routes through can_use_tool. In a real app you'd allowed_tools the
        # cheap/safe tools (Read, Glob, Grep) and only prompt for the risky
        # ones (Write, Edit, Bash).
        allowed_tools=[],
        add_dirs=[str(SANDBOX_DIR)],
        can_use_tool=can_use_tool,
        permission_mode="default",
    )

    prompt_text = (
        f"Create a file called pizza.txt in {SANDBOX_DIR} with a short pizza "
        f"recipe. Then read it back, then run 'ls' on the sandbox folder."
    )

    # A plain string prompt is all you need. If you find older examples that
    # wrap a single prompt in an async generator, that was a workaround for a
    # time when the SDK only opened the control channel it uses to call
    # `can_use_tool` in streaming-input mode. It keeps stdin open for a string
    # prompt now, so the callback fires either way.
    total_cost = 0.0

    async for message in query(prompt=prompt_text, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text, end="", flush=True)
        elif isinstance(message, ResultMessage):
            total_cost += message.total_cost_usd or 0.0

    print(f"\n\n---\nCost: ${total_cost:.6f}")


if __name__ == "__main__":
    asyncio.run(main())
