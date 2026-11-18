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


---

## 2026-11-18 — Web UI and FastAPI Backend Implementation

### Prompt given
"ui not done" (with screenshot of default Vite starter)

### Work completed
- Designed and built the complete, dark-mode developer UI for CodePilot using React 18, Vite 5, Tailwind CSS v4, `lucide-react`, and `react-markdown`.
- Implemented `frontend/src/components/Sidebar.jsx` with active Ollama status, hardware acceleration indicator, workspace sandbox badge, new task button, and quick-prompt templates.
- Implemented `frontend/src/components/Header.jsx` with model selector (`qwen2.5-coder:7b` vs `qwen3.5:4b`), connection indicator, and toggleable drawers.
- Implemented `frontend/src/components/ChatMessage.jsx` with markdown rendering, syntax-highlighted code blocks with Copy buttons, and interactive tool-call timeline cards.
- Implemented `frontend/src/components/ToolActivityPanel.jsx` showing real-time tool execution status, parameters, and structured outputs.
- Implemented `frontend/src/components/WorkspacePanel.jsx` allowing users to preview files within `./workspace` (`hello_world.py`, `.gitkeep`).
- Implemented `frontend/src/services/api.js` for health checks and chat orchestration.
- Implemented FastAPI backend server with CORS in `backend/app/main.py`, `backend/app/config.py`, `backend/app/api/routes_health.py`, and `backend/app/api/routes_chat.py`.
- Started FastAPI server daemon on `http://127.0.0.1:8000`.
- Verified full-stack connection: React UI -> FastAPI (`GET /api/health`, `POST /api/chat`) -> Ollama Metal GPU -> Response with tool execution.

### Files created or changed
- `frontend/src/App.jsx` — primary app layout and chat state
- `frontend/src/components/Sidebar.jsx` — left navigation and system guardrails
- `frontend/src/components/Header.jsx` — header bar with model switcher
- `frontend/src/components/ChatMessage.jsx` — chat messages & tool cards
- `frontend/src/components/ToolActivityPanel.jsx` — live tool execution inspection drawer
- `frontend/src/components/WorkspacePanel.jsx` — workspace file tree explorer
- `frontend/src/services/api.js` — HTTP client
- `backend/app/config.py` — configuration settings
- `backend/app/main.py` — FastAPI application entrypoint
- `backend/app/api/routes_health.py` — system status route
- `backend/app/api/routes_chat.py` — chat and tool execution route

### Commands and tests
- `cd frontend && npm run build` — PASS (built in 674ms)
- `uvicorn backend.app.main:app --host 127.0.0.1 --port 8000` — RUNNING
- `curl http://127.0.0.1:8000/api/health` — PASS (HTTP 200)
- `curl -X POST http://127.0.0.1:8000/api/chat` — PASS (Tool `list_files` executed and synthesized)

### Current status
Full-stack Web UI and backend are live and connected.
