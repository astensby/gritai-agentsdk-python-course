# Step 4 — Skills

Give the agent a **Skill**: a markdown file that teaches it how to do a task well. No code, no tools — just instructions Claude reads and follows when relevant.

## What's new vs step 3

- A skill file at `.claude/skills/meeting-notes-formatter/SKILL.md`
- One critical option: `setting_sources=["project"]`
- Zero application code change beyond that line

## Run it

```bash
# from the repo root (one-time setup is in the main README)
make step-4
```

The agent should autonomously invoke the `meeting-notes-formatter` skill (because the prompt matches its `description:` frontmatter) and produce output structured exactly per the skill template.

## How it works

```
step-4-skills/
├── .claude/
│   └── skills/
│       └── meeting-notes-formatter/
│           └── SKILL.md       ← the entire skill is this file
└── main.py
```

The SDK auto-discovers any `.claude/skills/*/SKILL.md` files in the project. Claude reads each skill's frontmatter `description` at decision time and invokes the skill autonomously when a user prompt matches.

## What `setting_sources` does

`setting_sources` controls which on-disk setting layers the SDK loads — `user` (`~/.claude`), `project` (`./.claude`), and `local` (`./.claude/settings.local.json`). Skills are discovered from these layers.

```python
options = ClaudeAgentOptions(
    setting_sources=["project"],   # scope skill discovery to THIS project
)
```

The SDK default is to load **all** sources (`user`, `project`, `local`), so `.claude/skills/` already loads even if you omit the option. We pass `["project"]` on purpose: workshop runs then depend only on the skill shipped in this folder, not on whatever you happen to have in your personal `~/.claude`. To turn filesystem settings (and skill discovery) **off**, pass `[]` — that's the SDK's isolation mode.

## Skill anatomy

A SKILL.md is just markdown with YAML frontmatter:

```md
---
name: meeting-notes-formatter
description: Use this skill when... (triggers autonomous invocation)
---

# Instructions to Claude

When invoked, do this and this and this.
- Output format
- Edge cases
- Rules
```

Two things matter most:

1. **`description`** — Claude scans this to decide whether to fire the skill. Be specific about *when* to use it. "Use this when..." is a strong pattern.
2. **The body** — straightforward instructions to Claude. No need to be clever. Treat it like a tight brief to a smart contractor.

## Try this

- Set `setting_sources=[]` (isolation mode). The skill no longer loads and the agent improvises its own format. Switch back to `["project"]` (or remove the line) and the skill returns. (Omitting the option and `["project"]` both load the skill; only `[]` disables it.)
- Edit `SKILL.md` to add a `## Risks` section to the template. Rerun. The skill output changes.
- Add a second skill (e.g., `code-review-formatter`) and prompt for code review. The agent picks the right one based on `description`.

## Next

In [step 5](../step-5-interactive-repl), we'll let participants **chat** with the agent instead of running a one-shot prompt — turning everything we've built so far into an interactive shell.
