"""
Step 4 — Skills

A *skill* is a markdown file that teaches the agent how to do one task well.
No code, no tools — just instructions Claude reads and follows when the user's
prompt looks like the kind of work the skill is for.

The skill for this step lives at:

    step-4-skills/.claude/skills/meeting-notes-formatter/SKILL.md

The SDK auto-discovers any `.claude/skills/*/SKILL.md` file in the project. At
decision time Claude reads each skill's YAML frontmatter `description` and
invokes the skill autonomously when the prompt matches.

The one thing that's new vs step 3 is this option:

    setting_sources=["project"]

Skills are discovered from your on-disk "setting sources." In SDK 0.2.87 the
default is to load *all* sources (user / project / local), so the project skill
loads even if you omit this line. We pass ["project"] on purpose: it SCOPES
discovery to this folder, so workshop runs depend only on the skill shipped
here — not on whatever you happen to have in your personal `~/.claude`.
Pass `[]` to turn skill discovery off entirely (the SDK's "isolation mode").
"""

import asyncio

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    query,
)

RAW_NOTES = """
Quick sync about the Q3 launch.
We decided to push the launch from June 15 to June 30 to give us time for a security review.
Anna will lead the security review and coordinate with the platform team.
We still need to figure out what to do about the marketing campaign that's already booked
for June 15 — open question for the marketing team.
Action: Bob to draft revised comms by next Friday.
Action: Anna to share the security review checklist on Monday.
We also touched on the Q4 roadmap but parked it for next time.
"""


async def main() -> None:
    options = ClaudeAgentOptions(
        model="claude-sonnet-4-6",
        # Scope skill discovery to this project's .claude/ folder. See top-of-file
        # comment for the full reasoning — default is "load all sources", we
        # narrow it to "project" for reproducibility.
        setting_sources=["project"],
    )

    async for message in query(
        prompt=f"Here are my raw meeting notes — please format them:\n\n{RAW_NOTES}",
        options=options,
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text, end="", flush=True)
        elif isinstance(message, ResultMessage):
            print(f"\n\n---\nCost: ${message.total_cost_usd:.6f}")


if __name__ == "__main__":
    asyncio.run(main())
