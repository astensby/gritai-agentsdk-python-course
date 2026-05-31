"""
Step 7 — Subagents (coordinator + specialists)

One MAIN agent (the "coordinator") delegates work to two SUBAGENTS:
  - code-reviewer: spots bugs, security issues, code smells
  - test-planner:  proposes a test plan for the same code

The main agent uses the built-in delegation tool to spin up each subagent.
Recent CLI versions renamed that tool from `Task` to `Agent` (with `Task`
kept as an alias), so we allow-list both names and match both when we watch
the coordinator dispatch. Each subagent runs in its own context with its own
system prompt and tool whitelist — keeps the main agent's context lean and
gives each subagent a tight, single-responsibility role.

Note on the SDK surface: `ClaudeAgentOptions` uses snake_case
(allowed_tools, add_dirs, ...), but `AgentDefinition` is the ONE place
that keeps camelCase field names (disallowedTools, permissionMode,
mcpServers, maxTurns). It's a dataclass — construct it with
`AgentDefinition(...)`, not a plain dict, or the SDK can't serialize it.

The sample file is `sample/auth.ts` — a deliberately mediocre TypeScript
file. The lesson is "review existing code", and TypeScript is what most
participants will encounter day-to-day, so we keep the sample in TS even
though the host program is Python.
"""

import asyncio
from pathlib import Path

from claude_agent_sdk import (
    AgentDefinition,
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    query,
)


async def main() -> None:
    sample_dir = (Path(__file__).parent / "sample").resolve()
    auth_path = sample_dir / "auth.ts"

    prompt = (
        f"Use the code-reviewer and test-planner subagents to analyze {auth_path}. "
        "Then give me a final summary in 5 bullet points."
    )

    options = ClaudeAgentOptions(
        model="claude-sonnet-4-6",
        # The main agent gets Read + the delegation tool. `Agent` is the current
        # name; `Task` is the legacy alias — list both so this works regardless
        # of the CLI version bundled with the installed SDK.
        allowed_tools=["Read", "Agent", "Task"],
        add_dirs=[str(sample_dir)],
        # Each entry under `agents` defines a subagent. The key is the name
        # the main agent passes as `subagent_type` when it delegates.
        # `AgentDefinition` is a
        # dataclass whose field names are camelCase (`disallowedTools`,
        # `permissionMode`, ...) — the one place the SDK breaks snake_case.
        agents={
            "code-reviewer": AgentDefinition(
                description=(
                    "Reviews TypeScript code for bugs, security issues, and code smells. "
                    "Returns a concise list of findings ranked by severity."
                ),
                prompt=(
                    "You are a senior code reviewer. Read the file you're given "
                    "and produce a bullet list:\n"
                    "- Critical: bugs that break correctness or security\n"
                    "- Major: design problems that will bite later\n"
                    "- Minor: style/clarity nits\n\n"
                    "Be specific: cite line numbers and quote the offending code. "
                    "Don't speculate beyond what's in the file."
                ),
                tools=["Read", "Grep"],
            ),
            "test-planner": AgentDefinition(
                description=(
                    "Proposes a test plan for a TypeScript file. Returns a checklist of test cases "
                    "without writing actual test code."
                ),
                prompt=(
                    "You are a test engineer. For the file you're given, "
                    "produce a Markdown checklist of test cases that should exist:\n"
                    "- Happy paths\n"
                    "- Edge cases\n"
                    "- Failure / error modes\n"
                    "- Security-relevant invariants\n\n"
                    "Group by function. Don't write the actual tests — "
                    "just the list of what should be tested."
                ),
                tools=["Read"],
            ),
        },
    )

    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text, end="", flush=True)
                elif isinstance(block, ToolUseBlock):
                    # Watch the coordinator delegate — each call spawns a subagent.
                    # Match both the current name (`Agent`) and the legacy alias (`Task`).
                    if block.name in ("Agent", "Task"):
                        subagent_type = block.input.get("subagent_type")
                        print(f"\n\n[dispatch] subagent: {subagent_type}")
        elif isinstance(message, ResultMessage):
            print(f"\n\n---\nCost: ${message.total_cost_usd:.6f}")


if __name__ == "__main__":
    asyncio.run(main())
