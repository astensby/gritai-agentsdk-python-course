# GritAI · Agent SDK Workshop — Python edition
#
# One `make install` at the root sets up every step.
# Then `make step-N` runs step N. All steps share a single `.venv` and
# load `ANTHROPIC_API_KEY` from the root `.env`.

UV       := uv
RUN      := $(UV) run --env-file=.env

.PHONY: install
install:
	# --all-packages: workspace members declare their deps independently; without
	# this flag uv only installs the (empty) root project's deps and you'd hit
	# `ModuleNotFoundError: No module named 'claude_agent_sdk'` on the first run.
	$(UV) sync --all-packages

.PHONY: typecheck
typecheck:
	# Every step has its own `main.py`, so a single `mypy step-*/` invocation
	# trips over duplicate module names. Check each step folder on its own.
	@for d in step-*/; do echo "mypy $$d"; $(UV) run mypy "$$d" || exit 1; done

.PHONY: lint
lint:
	$(UV) run ruff check .

.PHONY: format
format:
	$(UV) run ruff format .

# -- Step runners -------------------------------------------------------------

.PHONY: step-0
step-0:
	$(RUN) --package step-0-raw-api python step-0-raw-api/main.py

.PHONY: step-1
step-1:
	$(RUN) --package step-1-hello-loop python step-1-hello-loop/main.py

.PHONY: step-2
step-2:
	$(RUN) --package step-2-external-mcp python step-2-external-mcp/main.py

.PHONY: step-2b
step-2b:
	$(RUN) --package step-2b-builtin-tools python step-2b-builtin-tools/main.py

.PHONY: step-3
step-3:
	$(RUN) --package step-3-custom-mcp python step-3-custom-mcp/main.py

.PHONY: step-3b
step-3b:
	$(RUN) --package step-3b-real-weather python step-3b-real-weather/main.py

.PHONY: step-4
step-4:
	$(RUN) --package step-4-skills python step-4-skills/main.py

.PHONY: step-5
step-5:
	$(RUN) --package step-5-interactive-repl python step-5-interactive-repl/main.py

.PHONY: step-5-streaming
step-5-streaming:
	$(RUN) --package step-5-interactive-repl python step-5-interactive-repl/main_streaming.py

.PHONY: step-6
step-6:
	$(RUN) --package step-6-web-chat uvicorn step_6_web_chat.server:app --reload --host 127.0.0.1 --port 8000 --app-dir step-6-web-chat

.PHONY: step-7
step-7:
	$(RUN) --package step-7-subagents python step-7-subagents/main.py

.PHONY: step-8
step-8:
	$(RUN) --package step-8-hooks python step-8-hooks/main.py

.PHONY: step-9
step-9:
	$(RUN) --package step-9-permissions python step-9-permissions/main.py

.PHONY: step-10
step-10:
	$(RUN) --package step-10-capstone-meeting-notes python step-10-capstone-meeting-notes/main.py

.PHONY: step-11
step-11:
	$(RUN) --package step-11-pydanticai-ollama python step-11-pydanticai-ollama/main.py
