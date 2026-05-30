---
name: meeting-notes-formatter
description: Use this skill when the user provides raw meeting notes, transcript snippets, or stream-of-consciousness notes from a discussion and wants them organized. Transforms messy notes into a structured summary with Decisions, Action Items, and Open Questions sections.
---

# Meeting Notes Formatter

When invoked, transform the user's raw meeting notes into output that follows EXACTLY this template:

## Summary
A 1–2 sentence overview of what the meeting was about.

## Decisions
- One bullet per decision made.
- Be concrete: who, what, by when (if mentioned).

## Action Items
- [ ] **@owner** — Action description (due: date if mentioned)
- Use GitHub checkbox syntax `- [ ]` so the list can be ticked off later.
- One action per bullet.

## Open Questions
- Each unresolved question on its own line.
- Note who needs to answer it if known.

## Rules

- **Do not invent** decisions, owners, deadlines, or action items that aren't in the source.
- If a section has no content, write `_None._` — do not omit the heading.
- Keep bullets short. Detail belongs in the original notes, not the summary.
- Preserve names verbatim; do not anonymize.
