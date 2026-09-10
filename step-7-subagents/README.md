# Step 7 — Subagents

A main agent that delegates specialist work to **subagents**. This is the single most-asked-about Agent SDK pattern and the canonical "putting it all together in Agents" idea from Day 2.

> **Subagents run in the background by default.** The delegation tool takes a `run_in_background`
> parameter that defaults to **true**. Leave it alone and the coordinator dispatches both
> specialists, announces they're running in the background, and *ends its turn* — so the stream
> emits a `result` (with a cost) before either subagent has reported. That run produces 116 lines
> of output and **three** cost lines, with both subagent transcripts interleaved over the summary.
>
> `main.py` handles it three ways, and all three are worth understanding:
>
> 1. The prompt asks for `run_in_background: false`.
> 2. The message loop skips anything carrying `parent_tool_use_id` — that's how you tell a
>    subagent's chatter from the coordinator's.
> 3. Cost is accumulated and printed **after** the stream, because `result` means "a turn ended",
>    not "the run is over".
>
> **Try it:** delete the `run_in_background: false` sentence from the prompt and re-run. Comparing
> the two traces teaches background delegation and stream handling at the same time.

## What's new

- The `agents` option in `ClaudeAgentOptions`
- The built-in delegation tool (`Agent`; older CLIs called it `Task`, still accepted as an alias) — how the main agent dispatches to subagents
- A "coordinator + specialists" pattern: one main agent, two subagents (`code-reviewer`, `test-planner`)

## Run it

```bash
# from the repo root (one-time setup is in the main README)
make step-7
```

Watch the trace — you'll see the main agent dispatch two `Agent` calls (one per subagent; the tool is `Agent` on current CLIs, `Task` on older ones), each subagent reports back, and the main agent synthesizes a final summary.

## How it works

```python
from claude_agent_sdk import AgentDefinition

options = ClaudeAgentOptions(
    allowed_tools=[
        "Read",
        "Agent",
        "Task",
    ],  # ← main agent needs the delegation tool (Agent/Task) to dispatch
    add_dirs=[str(sample_dir)],
    agents={
        "code-reviewer": AgentDefinition(
            description="...",  # ← main agent uses this to decide WHEN to dispatch
            prompt="...",  # ← the subagent's system prompt
            tools=["Read", "Grep"],  # ← the subagent's own allowed tools
        ),
        "test-planner": AgentDefinition(...),
    },
)
```

The main agent's system prompt is automatically augmented with a list of available subagents (taken from each `description`). When the main agent decides to delegate, it emits an `Agent` tool call (named `Task` on older CLIs) with `subagent_type: "code-reviewer"` and a prompt for the subagent. The SDK spins up a fresh agent loop for that subagent with its own context and tools, and returns the final result to the main agent.

## Why subagents

- **Context isolation** — a subagent's intermediate reasoning doesn't pollute the main agent's context window
- **Specialization** — each subagent has its own focused system prompt and tool whitelist
- **Parallelism** — the main agent can dispatch multiple subagents (in some patterns concurrently)
- **Composition** — subagents can themselves dispatch sub-subagents (use with care)

## AgentDefinition fields worth knowing

`AgentDefinition` is a **dataclass** — construct it with `AgentDefinition(...)`, not a plain dict (the SDK serializes it with `dataclasses.asdict`, which only works on instances). Its field names are **the one place in the Python SDK that keeps camelCase** (everything else on `ClaudeAgentOptions` is snake_case). Watch for `disallowedTools`, `permissionMode`, `mcpServers`, `maxTurns`.

| Field | What it does |
|---|---|
| `description` | Drives the main agent's decision to dispatch — be specific |
| `prompt` | System prompt for the subagent |
| `tools` | Allowed tools (defaults to inheriting parent's tools) |
| `model` | Pin a different model (e.g. `"haiku"` for cheap parallel work) |
| `maxTurns` | Cap on agentic round-trips before the subagent gives up |
| `disallowedTools` | Explicit deny list |

## Gotchas

- The sample file is `sample/auth.ts` — TypeScript, on purpose. The lesson is reviewing existing code; TS is what most participants encounter in the wild. The host program is still Python.
- `add_dirs` is required to let `Read` reach files outside the script's CWD. Without it the subagents will refuse to read `auth.ts`.
- `AgentDefinition` field names are camelCase (`disallowedTools`, `permissionMode`, ...). The rest of `ClaudeAgentOptions` is snake_case. It's a dataclass, so a wrong field name is a `TypeError` at construction — read the dataclass definition if you're adding a new one.

## Try this

- Add a third subagent `security-auditor` that focuses only on security. Watch the main agent route differently.
- Pin `"model": "haiku"` on `test-planner` (cheaper). The other can stay on Sonnet.
- Drop **both** `Agent` and `Task` from the main agent's `allowed_tools` (they're the same tool — `Task` is just the legacy alias, so removing only one still lets it dispatch). With both gone, the agents are configured but the main agent can no longer reach them — useful test.

## Next

[Step 8 — Hooks](../step-8-hooks): intercept the tool loop with logging, auditing, or blocking.
