"""A tiny "skill loader" that mimics the Claude Agent SDK's .claude/skills/
discovery convention. PydanticAI doesn't ship a skill system, so we roll our
own in a few dozen lines (parallel to the TS step-11 `skills.ts`):

  1. Read every SKILL.md under .claude/skills/<name>/
  2. Parse YAML frontmatter (python-frontmatter — the Python analog to gray-matter)
  3. Concatenate name + description + body into one chunk of system prompt

The model sees: "you have these skills, here's when to use each."
Whether it actually USES them depends on the model. Small Ollama models often
need an explicit nudge in the prompt; Claude doesn't.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import frontmatter


@dataclass
class Skill:
    name: str
    description: str
    body: str


def load_skills(skills_dir: str | Path) -> list[Skill]:
    """Load all SKILL.md files from .claude/skills/<name>/SKILL.md."""
    skills: list[Skill] = []
    root = Path(skills_dir)
    if not root.is_dir():
        # No .claude/skills/ directory — return zero skills rather than throwing.
        return skills
    for entry in sorted(root.iterdir()):
        if not entry.is_dir():
            continue
        skill_path = entry / "SKILL.md"
        if not skill_path.is_file():
            continue
        try:
            post = frontmatter.load(skill_path)
        except Exception:
            # SKILL.md unreadable or malformed — skip this directory, keep loading the rest.
            continue
        name = str(post.metadata.get("name", entry.name))
        description = str(post.metadata.get("description", ""))
        body = post.content.strip()
        skills.append(Skill(name=name, description=description, body=body))
    return skills


def format_skills_as_system_block(skills: list[Skill]) -> str:
    """Render the loaded skills as a chunk of system prompt."""
    if not skills:
        return ""
    parts = [
        "## " + s.name + "\n\n**When to use:** " + s.description + "\n\n" + s.body for s in skills
    ]
    joined = "\n\n---\n\n".join(parts)
    return (
        "\n\n# Available Skills\n\n"
        "You have the following skills. Each one tells you WHEN to use it "
        "(description) and HOW to do the work (body). When the user's request "
        "matches a skill's description, follow that skill's instructions.\n\n" + joined + "\n"
    )
