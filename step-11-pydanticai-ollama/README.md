# Step 11 — PydanticAI + Ollama (alternative SDK)

The same agent pattern (skills + custom tools + agent loop) — but with **PydanticAI** and a **local Ollama** model instead of the Claude Agent SDK + Claude API.

This step is the **contrast lesson**: agent concepts are portable across SDKs. Only the glue code changes.

## What's new vs the Claude SDK steps

|   | Claude Agent SDK | PydanticAI |
|---|---|---|
| Main entry | `query(prompt=..., options=...)` async iterator | `Agent(model, system_prompt=...)` + `await agent.run(...)` |
| Provider | `claude-agent-sdk` (Claude only) | `pydantic-ai-slim` (multi-provider) — here `OpenAIChatModel` + `OllamaProvider` |
| Loop control | Built-in, auto-iterates | Built-in, auto-iterates (similar shape) |
| MCP integration | Native `mcp_servers` option | `MCPToolset` + `FastMCPClient` — same filesystem server as step 2 |
| MCP **roots** | Advertises roots, so the server's CLI sandbox arg is overridden | Does **not** advertise roots by default, so the server keeps its CLI arg |
| Custom tools | `@tool(...)` + `create_sdk_mcp_server(...)` | `@agent.tool_plain` decorator on a Python function |
| Skills | Auto-discovered from `.claude/skills/` via `setting_sources` | **Not built-in** — `skills.py` loads them manually |
| Model | Claude (`claude-sonnet-5`) | Any Ollama model (`llama3.3`, `qwen2.5-coder`, ...) |

## Prerequisites

Beyond the rest of the workshop, this step needs **Ollama** running locally:

```bash
# Install (macOS)
brew install ollama

# Start the server (leave running in another terminal)
ollama serve

# Pull a tool-capable model. Larger = better at tool use.
ollama pull llama3.3                # or: qwen2.5-coder, mistral-nemo
```

You do NOT need `ANTHROPIC_API_KEY` for this step — the model is local.

## Run it

```bash
make step-11
```

By default it uses `llama3.3`. Swap models via env var:

```bash
OLLAMA_MODEL=qwen2.5-coder:14b make step-11
```

The agent will:

1. Load skills from `./.claude/skills/` (the same convention as step 4)
2. Inject them into the system prompt as "available skills" with usage guidance
3. Receive raw meeting notes and a prompt to format them
4. Loop: call model → see tool request → run tool → repeat — driven by PydanticAI's `Agent.run`

The custom `get_weather` tool is included as the "look, custom tools work the same way" beat. The filesystem MCP server is what gives the agent a way to write `sandbox/formatted.md` at all — a prompt that asks for a file is only as good as the tools the agent has to create one.

### The MCP roots counterpoint

Watch the server's startup line in this step:

```
Client does not support MCP Roots, using allowed directories set from server args
```

Step 2 mounts the **same server** and gets the opposite behaviour: the Claude Agent SDK advertises MCP roots, so the server discards its own CLI sandbox argument and uses whatever the client reports as its `cwd`. PydanticAI's client leaves `roots` unset, so the CLI argument stands.

Same server, two clients, two different sandboxes — a concrete demonstration that "supports MCP" is not a single capability but a pile of optional sub-protocols.

## How the skill system works here

PydanticAI has no skills primitive — so we built a tiny loader in `skills.py`:

```python
skills = load_skills(".claude/skills")
# → [Skill(name, description, body), ...]

block = format_skills_as_system_block(skills)
# → "# Available Skills\n## meeting-notes-formatter\n**When to use:** ..."

agent = Agent(model, system_prompt="You are a helpful agent." + block)
```

That's the entire skill mechanism. It puts every skill into the system prompt all at once. Compare to the Claude Agent SDK, which discovers skills the same way but is smarter about which one applies (and only includes the body when it matches).

This is fine for one or two skills; it scales badly past ~5 because the system prompt gets huge.

## SDK is different, model is different — but the AGENT IDEAS carry over

The big point of this step: a system prompt + tools + an agent loop + skills-as-injected-prompts is the agent recipe regardless of which SDK or model you use. PydanticAI's `Agent` looks different from `query()` and you wire tools with `@agent.tool_plain` instead of `@tool(...)` + `create_sdk_mcp_server(...)`. But the shape of the work is the same.

## Honest caveats with Ollama

The Agent SDK was tuned for Claude. Most local models, especially the small ones (<30B), are flaky at:

- **Tool calling format** — they may hallucinate JSON or skip tools entirely. Pick a model whose model card explicitly lists "tool calling" or "function calling" support.
- **Multi-step planning** — chaining 3+ tool calls compounds errors.
- **Following skill templates** — small models drift from the template format. Larger models (70B+) handle it.
- **Long system prompts** — local context windows are smaller. Don't load 10 skills into a 7B model.

What does work reliably on most tool-capable Ollama models:

- Single tool calls (the weather tool here)
- Following a skill template when the prompt is short
- Simple one-shot agent runs

What's painful:

- Subagents (step 7 patterns) — don't try
- Hooks/permissions — work fine, they're SDK-side
- Skills with complex templates — Claude follows them; small models improvise

## When to use which SDK

| Use this SDK | When... |
|---|---|
| **Claude Agent SDK** | Building production-quality agents. Best tool calling + skill discovery + sub-agents. Premium Claude-only. |
| **PydanticAI** | Multi-provider freedom, strong typed inputs/outputs, Python-native. Use with Claude, GPT, Gemini, or local models. Smaller surface area; you wire more yourself. |

For a workshop, the Claude Agent SDK is the right teaching default — it lets the agent ideas land before you worry about SDK plumbing. This step exists so you can see the same ideas in another shape and pick the right tool for your own projects.

## Try this

- Swap `qwen2.5-coder:14b` and observe whether the model uses the skill correctly. Then try a 7B model and watch it drift.
- Add a second skill (`code-explainer`?) and prompt for code review. Notice the model has to choose between two skills based only on description matching.
- Replace `OpenAIChatModel(..., provider=OllamaProvider(...))` with `AnthropicModel("claude-sonnet-5")` and rerun. Same code, much better results — that's the model quality gap.
- Advertise MCP roots: pass `roots=[str(SANDBOX_DIR)]` to `FastMCPClient(...)` and re-run. The server's startup line changes, because the client is now the one deciding what it may touch. That single argument is the whole difference between this step and step 2.
