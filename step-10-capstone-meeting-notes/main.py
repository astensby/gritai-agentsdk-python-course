"""
CAPSTONE — the workshop in one agent.

One job: turn every raw transcript in ./transcripts/ into a formatted
summary in ./output/. To do it, the agent uses:

  - The Glob built-in tool          (find transcripts)
  - The Read built-in tool          (read each one)
  - The meeting-notes-formatter SKILL (decides the output format)
  - The Write built-in tool         (save the result)
  - A PreToolUse HOOK               (log every step so you can watch it work)

That's: built-in tools (step 2b) + skills (step 4) + hooks (step 8),
composed into a small useful agent. No MCP needed — this could be a CLI
tool you ship.
"""

import asyncio
import json
from pathlib import Path

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    HookMatcher,
    ResultMessage,
    TextBlock,
    query,
)

PROJECT_DIR = Path(__file__).resolve().parent
TRANSCRIPTS_DIR = PROJECT_DIR / "transcripts"
OUTPUT_DIR = PROJECT_DIR / "output"


async def log_tool_calls(input_data, tool_use_id, context):
    """PreToolUse hook — log every tool call so the audience can watch the agent work."""
    tool_name = input_data.get("tool_name", "?")
    summary = json.dumps(input_data.get("tool_input", {}))[:100]
    suffix = "…" if len(summary) >= 100 else ""
    print(f"  · {tool_name}({summary}{suffix})")
    return {}


async def main() -> None:
    prompt = f"""Process every .txt file in {TRANSCRIPTS_DIR}:

1. Read each transcript.
2. Use the meeting-notes-formatter skill to convert it into a structured summary.
3. Save the summary to {OUTPUT_DIR}, using the same basename but with a .md extension
   (e.g., 2026-05-12-q3-launch.txt → 2026-05-12-q3-launch.md).
4. When you're done, print a one-line summary: "Processed N transcripts → output/."

Don't skip any files. Don't add anything that isn't in the source transcripts."""

    options = ClaudeAgentOptions(
        model="claude-sonnet-4-6",
        # This job only needs Glob/Read/Write. Note `allowed_tools` AUTO-APPROVES
        # those (so they run without a prompt) — it does NOT remove the others.
        # To actually keep the agent off the shell we add `disallowed_tools`;
        # without it, the agent would happily reach for Bash (e.g. `ls`, `mkdir`).
        allowed_tools=["Glob", "Read", "Write"],
        disallowed_tools=["Bash"],
        add_dirs=[str(TRANSCRIPTS_DIR), str(OUTPUT_DIR)],
        # Scope skill discovery to this project's .claude/ folder so the run is
        # reproducible — independent of whatever you have in ~/.claude. (The SDK
        # default already loads project skills; setting it explicitly just
        # narrows the search.) See step 4 for the full story.
        setting_sources=["project"],
        # Observe every tool call so the workshop audience can see what's happening.
        hooks={
            "PreToolUse": [
                HookMatcher(hooks=[log_tool_calls]),
            ],
        },
    )

    print("Running capstone agent...\n")

    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text, end="", flush=True)
        elif isinstance(message, ResultMessage):
            print("\n\n---")
            print(f"Cost:     ${message.total_cost_usd:.6f}")
            print(f"Duration: {message.duration_ms}ms")
            print(f"Output:   {OUTPUT_DIR}")


if __name__ == "__main__":
    asyncio.run(main())
