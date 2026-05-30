# Step 10 — Capstone: Meeting Notes Agent

The whole workshop in one small, **actually useful** agent: convert raw meeting transcripts into structured Markdown summaries.

## What this composes

| From step | What it contributes |
|---|---|
| [2b](../step-2b-builtin-tools) | Built-in `Glob`, `Read`, `Write` — no MCP needed |
| [4](../step-4-skills) | The `meeting-notes-formatter` skill drives the output shape |
| [8](../step-8-hooks) | A `PreToolUse` hook logs every step so you can watch it work |

No MCP servers. No web UI. No subagents. Just the pieces this job actually needs.

> **About `setting_sources`:** the `setting_sources=["project"]` line in `main.py` scopes skill discovery to this folder. The SDK default already includes `project`, so deleting the line still loads the skill — but setting it to `[]` (isolation mode) disables discovery, and the agent then emits unstructured prose with no error message. Keep it as `["project"]` for reproducible runs. See [step 4](../step-4-skills).

## Run it

```bash
# from the repo root (one-time setup is in the main README)
make step-10
```

The agent will:

1. `Glob` the `transcripts/` folder for `*.txt`
2. For each file: `Read` it → invoke the skill → `Write` `output/<same-name>.md`
3. Print a one-line summary

Two sample transcripts ship in the box: a Q3 launch sync and an incident review. Drop in your own to test.

## Output shape

Each transcript becomes a Markdown file like:

```md
## Summary
The team pushed the Q3 launch from June 15 to June 30 to make room for a security review.

## Decisions
- Launch date moved from 2026-06-15 → 2026-06-30
- Anna owns the security review, coordinating with Chen's team

## Action Items
- [ ] **@Bob** — Draft revised launch comms (due: next Friday)
- [ ] **@Anna** — Share security-review checklist on Monday
- [ ] **@Dani** — Update the launch tracker today

## Open Questions
- Do we owe customers a heads-up before June 15? (Bob to consult legal)
- Is there budget for a second push if the new date slips? (Dani to ask the CFO)
```

The format comes from `.claude/skills/meeting-notes-formatter/SKILL.md` — change the skill and the output shape changes, no code edit needed.

## SDK concepts in play

- `allowed_tools=["Glob", "Read", "Write"]` — auto-approves those three so the agent doesn't prompt
- `disallowed_tools=["Bash"]` — actually removes the shell so the agent can't go off-script
- `add_dirs=[transcripts_dir, output_dir]` — built-in file tools refuse paths outside CWD unless added
- `setting_sources=["project"]` — narrows skill discovery to this folder
- `hooks={"PreToolUse": [HookMatcher(hooks=[log_tool_calls])]}` — observability with one async function

## Gotchas

- **`allowed_tools` is not a whitelist.** It auto-approves; it doesn't remove. Without `disallowed_tools=["Bash"]` the agent would happily `ls` and `mkdir` instead of using `Glob` and `Write`.
- **`add_dirs` is mandatory** when the agent needs to touch files outside the project's working directory. Built-in `Read`/`Write` refuse otherwise.
- **Skills are loaded from `.claude/skills/`** in the project (because `setting_sources=["project"]`). Move the SKILL.md and the output format changes — no code edit.
- **`AgentDefinition` (step 7) is the one place with camelCase field names** in the SDK. Everywhere else, including this step, fields are snake_case.

## What this proves

A useful agent is small. The Agent SDK gave us:

- **Tool selection** (`Glob` → `Read` → `Write`) — we didn't write that logic
- **Loop management** — we didn't write retry/iteration code
- **Skill discovery** — we put a markdown file in a folder
- **Observability** — we added one async function

Total app code: under 100 lines, most of it comments and the prompt.

## Try this

- Add a third transcript with a deliberately ambiguous note. See what the skill does — does it invent or leave it as an open question?
- Add a `PostToolUse` hook that records word counts to a CSV per file.
- Wrap this in a cron job so it runs against an inbox folder every morning.
- Replace the prompt with `sys.argv[1]` to make it a CLI: `uv run python main.py path/to/transcript.txt`.

## Next steps for your own agents

You now have all the pieces:

- **MCP** (steps 2, 3) — talk to external services or wrap business logic
- **Skills** (step 4) — teach the agent how to do something well, in plain Markdown
- **Multi-turn** (step 5) — keep context across user inputs
- **Web** (step 6) — same SDK, different I/O
- **Subagents** (step 7) — decompose into specialists
- **Hooks** (step 8) — observe, audit, rewrite
- **Permissions** (step 9) — keep the human in the loop
- **Compose** (this step) — pick the few you need

Go build.
