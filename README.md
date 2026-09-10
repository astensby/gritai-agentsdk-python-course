# GritAI · Claude Agent SDK Workshop — Python edition

A hands-on, progressive workshop for the [Claude Agent SDK](https://docs.claude.com/en/api/agent-sdk/overview) in Python, by [GritAI](https://gritai.no). Fourteen runnable step folders, one root install, one `.env` file. Drop in at any step.

> **Interactive companion:** open [`guide.html`](./guide.html) in a browser for a visual walk-through of the whole arc, with expandable step cards and copyable run commands.

## What you'll build

You start with a **single API call** and finish with a **useful agent** that turns raw meeting transcripts into structured summaries — composing MCP servers, Skills, hooks, and built-in tools along the way.

| Step | What it adds | Key SDK concept |
|---|---|---|
| [`step-0-raw-api`](./step-0-raw-api) | The Anthropic SDK with no Agent SDK | `messages.create()` — the primitive everything else wraps |
| [`step-1-hello-loop`](./step-1-hello-loop) | A single `query()` call | Async-iterable message stream |
| [`step-2-external-mcp`](./step-2-external-mcp) | An external MCP server (filesystem) | `mcp_servers` + `allowed_tools` |
| [`step-2b-builtin-tools`](./step-2b-builtin-tools) | The SDK's built-in `Read`/`Write`/`Bash`/... | MCP isn't needed for everything |
| [`step-3-custom-mcp`](./step-3-custom-mcp) | Your own Python functions as MCP tools (canned data) | `create_sdk_mcp_server` + `@tool` |
| [`step-3b-real-weather`](./step-3b-real-weather) | The same tool, now calling a real API | `httpx` → Open-Meteo (no key) |
| [`step-4-skills`](./step-4-skills) | A Skill the agent invokes autonomously | `.claude/skills/` + `setting_sources` (and the `skills` option) |
| [`step-5-interactive-repl`](./step-5-interactive-repl) | Multi-turn terminal chat | Session continuity via `resume` |
| [`step-6-web-chat`](./step-6-web-chat) | The same agent behind a FastAPI UI | Token streaming via `include_partial_messages` over SSE |
| [`step-7-subagents`](./step-7-subagents) | Delegate to specialist subagents | `agents` option + `Agent` tool (alias `Task`) |
| [`step-8-hooks`](./step-8-hooks) | Observe / audit / block tool calls | `PreToolUse` hooks |
| [`step-9-permissions`](./step-9-permissions) | Interactive "allow this?" prompts | `can_use_tool` callback + `permission_mode` |
| [`step-10-capstone-meeting-notes`](./step-10-capstone-meeting-notes) | **Capstone** — meeting-notes agent | Composes built-ins + skill + hook into one useful agent |
| [`step-11-pydanticai-ollama`](./step-11-pydanticai-ollama) | Same patterns, **different SDK + local model** | PydanticAI + Ollama + MCP roots counterpoint |

## Setup (once)

```bash
git clone <this repo>
cd gritai-agentsdk-python-course
cp .env.example .env             # paste your ANTHROPIC_API_KEY
uv sync --all-packages           # installs deps for all 14 steps (workspace)
```

That's it. No per-folder `cd`, no per-folder `uv sync`, no per-folder `.env`.

> **Why `--all-packages`?** The root `pyproject.toml` has empty `dependencies = []` (it's just a workspace aggregator). Plain `uv sync` will succeed but **won't** install the step packages, so `import claude_agent_sdk` will fail. `uv sync --all-packages` installs every workspace member into the shared `.venv`.

## Run any step

```bash
make step-1                  # smallest possible agent
make step-3                  # custom MCP server with weather tool
make step-6                  # spins up the FastAPI web chat at localhost:8000
make step-7                  # subagents (code reviewer + test planner)
make step-10                 # the capstone meeting-notes agent
```

All targets live in the root `Makefile`. One has a variant:

```bash
make step-5-streaming        # step 5's advanced streaming-input variant
```

## Prerequisites

- **Python 3.11+** (the workspace pins `requires-python = ">=3.11"`)
- **[uv](https://docs.astral.sh/uv/)** — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **An Anthropic API key** — get one at [console.anthropic.com](https://console.anthropic.com/)
- **Node.js 20+** — *only* for the steps that spawn `npx @modelcontextprotocol/server-filesystem@2026.8.31` as an external MCP server (steps 2, 5, 6 and 11). The Agent SDK itself does **not** need it. The server version is **pinned in the `npx` args**: `npx -y <pkg>` with no version fetches whatever is newest at run time, so without a pin two people running the same step on different days can get different servers.
- *(For step 11)* — a running [Ollama](https://ollama.ai) server with a tool-capable model pulled

> **No separate Claude Code CLI install needed.** The Agent SDK is a [standalone package](https://docs.claude.com/en/api/agent-sdk/overview) — `claude-agent-sdk` ships the Claude Code CLI it runs under the hood (a native binary, bundled in the wheel), so you do **not** need to `npm install -g @anthropic-ai/claude-code`. The SDK finds and uses the bundled binary automatically. If it can't be located on your platform, see gotcha 9.

## How the env works

Every `make step-N` target runs `uv run --env-file=.env ...`. uv's `--env-file` flag loads the root `.env` into `os.environ` **before** Python starts — so `ANTHROPIC_API_KEY` is available structurally, with no `dotenv` package and no `load_dotenv()` line in source. One source of truth, the root `.env`.

Step 6 (FastAPI) uses the same trick: `uv run --env-file=.env uvicorn ...` puts the key into the uvicorn worker's environment before your route handlers ever import the SDK.

## Workshop plan

A suggested order through the steps, grouped by what each phase builds. Skip around if you're self-paced — every step is standalone — but the phases land cleanly back-to-back in a live workshop.

- **Phase 1 — Build the loop.** The agent loop and its tools, from the raw API to a tool that calls the real world: `step-0` → `step-1` → `step-2` + `step-2b` (external MCP vs built-ins) → `step-3` → `step-3b` (same tool, real API).
- **Phase 2 — Teach it well.** Skills change behaviour without changing code; subagents split a big job into specialists: `step-4` → `step-7`.
- **Phase 3 — Put it to work.** Real I/O, observability, permissions, and composition: `step-5` → `step-6` (web) → `step-8` (hooks) → `step-9` (permissions) → `step-10` (**capstone**) → `step-11` (alt SDK + local model, bonus).

## Common gotchas

1. **`ANTHROPIC_API_KEY` not set** — make sure you copied `.env.example` to `.env` (at the **root**, not inside a step folder) and pasted your key. Confirm with `uv run --env-file=.env python -c "import os; print(bool(os.getenv('ANTHROPIC_API_KEY')))"`.
2. **A Skill isn't loading** — Skills are discovered from your setting sources. The SDK default loads all of them (`user` + `project` + `local`), so a project's `.claude/skills/` is picked up automatically. If you've passed `setting_sources=[]` (isolation mode) you've turned discovery off — include `"project"`. Or skip discovery entirely and name them: `skills=["meeting-notes-formatter"]`. See [step-4](./step-4-skills).
3. **An MCP tool doesn't fire** — list it (or a wildcard) in `allowed_tools`. Tools are named `mcp__<server-name>__<tool-name>`. Built-in tools use bare names (`Read`, `Write`, ...). You may also see an extra `ToolSearch` call before it: MCP tool schemas are deferred rather than all pasted into the prompt, so the model looks them up by name first.
4. **The agent used a built-in tool instead of your MCP server** — `allowed_tools` is **auto-approve, not a sandbox**. It grants tools; it never removes any. The built-in `Write`/`Edit`/`Bash` always exist, and current models prefer them for file work. Add `disallowed_tools=["Write", "Edit", "Bash"]` to force the MCP route. See [step-2](./step-2-external-mcp).
5. **A file landed somewhere unexpected** — the filesystem MCP server implements the MCP **roots** protocol: it asks the client which directories it may touch and replaces its own CLI argument with the answer. The Agent SDK answers with `cwd`, so set `cwd` to your sandbox or the sandbox silently widens to the whole project. See [step-2](./step-2-external-mcp); [step-11](./step-11-pydanticai-ollama) mounts the same server with a client that *doesn't* advertise roots.
6. **Cost printed two or three times, or output cut short** — a stream can contain **several** `result` messages. `result` means "a turn ended", not "the run is over": background subagents and multi-turn work each produce one. Accumulate and print after the loop instead of `if result: print(cost); break`. See [step-7](./step-7-subagents).
7. **Python too old / `uv` missing** — the workspace requires Python 3.11+ and uv 0.5+. Check with `python3 --version` and `uv --version`.
8. **`ModuleNotFoundError: No module named 'claude_agent_sdk'`** — you ran `uv sync` instead of `uv sync --all-packages`. The root project has no deps of its own; you need the `--all-packages` flag to install the workspace members.
9. **`Error: command not found: claude` (or `CLINotFoundError`)** — `claude-agent-sdk` ships a bundled Claude Code CLI and uses it automatically, so this should be rare. If the bundled binary can't be found on your platform, install the CLI globally with `npm install -g @anthropic-ai/claude-code`, or point the SDK at one with `ClaudeAgentOptions(cli_path=...)`.

## "Can I just run one step in isolation?"

Yes. Each step folder is a complete project — its own `pyproject.toml` declares all its deps. After the root `uv sync --all-packages`, you can also `cd` into a step and run it with its own venv:

```bash
cd step-3-custom-mcp
uv sync
uv run --env-file=../.env python main.py
```

That'll work because the step's `pyproject.toml` is self-contained. The shared workspace just hoists the deps into the root `.venv` so you don't pay 14× the install cost during the workshop.

## Further reading

- [Agent SDK Overview](https://docs.claude.com/en/api/agent-sdk/overview)
- [Python SDK Reference](https://docs.claude.com/en/api/agent-sdk/python)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Skills documentation](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview)
- [PydanticAI](https://ai.pydantic.dev/) — used as the alternative SDK in step 11
- For **MCP Apps / UI resources**, see our separate MCP course material — the rendering story is host-side, not SDK-side, so it lives there.


# Quickstart

| Command | What it runs |
|---|---|
| `make step-0` | Raw Anthropic SDK (no Agent SDK) |
| `make step-1` | Minimum viable Agent SDK loop |
| `make step-2` | External MCP (filesystem) |
| `make step-2b` | Built-in tools, no MCP |
| `make step-3` | Custom MCP (weather tool, canned) |
| `make step-3b` | Custom MCP (weather tool, real Open-Meteo API) |
| `make step-4` | Skills |
| `make step-5` | Interactive REPL (resume pattern) |
| `make step-5-streaming` | REPL via streaming-input mode |
| `make step-6` | FastAPI web chat (opens at localhost:8000) |
| `make step-7` | Subagents |
| `make step-8` | Hooks (logging + Bash-deny) |
| `make step-9` | Interactive permissions |
| `make step-10` | Capstone — meeting-notes agent |
| `make step-11` | PydanticAI + Ollama (alternative SDK, local model) |
| `make typecheck` | Type-check every step with mypy |
| `make lint` | Ruff lint across the workspace |
| `make format` | Ruff format across the workspace |
