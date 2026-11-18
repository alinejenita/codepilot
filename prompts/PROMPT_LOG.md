# CodePilot Prompt & Development Log

This file is an append-only diary tracking development tasks, Antigravity prompts, code changes, and test outcomes.

---

## 2026-11-18 — Milestone 1: Environment and Model Verification

### Prompt given
"let's set it up by installing ollama, use terminal commands"

### Work completed
- Initialized git repository (`main` branch) and defined comprehensive `.gitignore`.
- Created CodePilot folder structure (`backend/app/{api,agent,llm,tools}`, `frontend`, `cli`, `prompts`, `workspace`, `docs`).
- Configured `.env.example` and `.env` with initial runtime parameters.
- Created Python virtual environment (`.venv`) and installed dependencies: `fastapi`, `uvicorn`, `ollama`, `pydantic`, `pydantic-settings`, `python-dotenv`, `pytest`, `httpx`.
- Froze backend dependencies to `backend/requirements.txt`.
- Scaffolded React frontend using Vite and installed Tailwind CSS v4 (`@tailwindcss/vite`, `tailwindcss`). Verified frontend production build.
- Installed Ollama via Homebrew (`/opt/homebrew/bin/ollama`) and launched the service daemon (`brew services start ollama`).
- Verified Ollama endpoint responding at `http://127.0.0.1:11434`.
- Initiated pull of initial model (`qwen3.5:4b`).
- Created canonical `prompts/SYSTEM_PROMPT.md`.
- Implemented `backend/app/smoke_test.py` to validate structured tool calling (`list_files`) with Pydantic validation.

### Files created or changed
- `.gitignore` — repository exclusions
- `.env.example` / `.env` — configuration defaults
- `workspace/.gitkeep` — workspace root marker
- `backend/requirements.txt` — Python dependencies
- `frontend/` — React + Vite + Tailwind setup
- `prompts/SYSTEM_PROMPT.md` — canonical system instructions
- `backend/app/smoke_test.py` — tool calling verification script
- `prompts/PROMPT_LOG.md` — initialized project log

### Commands and tests
- `git init && git branch -M main` — PASS
- `python3 -m venv .venv && pip install ...` — PASS
- `cd frontend && npm install && npm run build` — PASS (built in 244ms)
- `brew install ollama && brew services start ollama` — PASS
- `curl http://127.0.0.1:11434/` — PASS ("Ollama is running")
- `ollama pull qwen3.5:4b` — PASS (4.0 GB model downloaded)
- `ollama pull qwen2.5-coder:7b` — PASS (4.7 GB model downloaded)
- `.venv/bin/python backend/app/smoke_test.py qwen2.5-coder:7b` — PASS (clean tool call extraction, Pydantic validation, and response synthesis)
- `.venv/bin/python backend/app/smoke_test.py qwen3.5:4b` — PASS
- `ollama ps` — 100% GPU offload on Apple Silicon Metal / MLX runner

### Current status
Milestone 1 is complete. Environment and dual-model verification fully passed. Both `qwen2.5-coder:7b` and `qwen3.5:4b` are downloaded and verified to successfully call tools with Pydantic validation. Default set to `qwen2.5-coder:7b`.

### Issues and decisions
- Used `create-vite@5` for non-interactive scaffolding.
- Configured Tailwind CSS v4 via `@tailwindcss/vite` plugin.
- Added robust dual-mode tool call parsing in `smoke_test.py` supporting both native Ollama `tool_calls` and embedded JSON / XML tags to prevent formatting mismatches across model architectures.
- Verified 100% GPU offload on Apple Silicon Metal.

### Next steps
- Proceed to Milestone 2: implement configuration module (`config.py`), base LLM adapter (`ollama_adapter.py`), tool schemas, tool registry, and safe workspace tools (`list_files`, `read_file`, `search_files`, `write_file`, `run_command`).
- Add unit tests for workspace boundary containment and command execution safety.
