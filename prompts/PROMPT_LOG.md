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


---

## 2026-11-18 — Claude-Style Web UI & OpenCode-Style Terminal CLI

### Prompt given
"the ui has to be like claude chat style with the history of chats are keeping traces, the terminal version should look like open code"

### Work completed
- Redesigned the entire Web UI to faithfully match **Claude Chat**:
  - Warm charcoal aesthetic (`#181816`), warm terracotta accents (`#d97757`), elegant typography, and subtle rounded corners.
  - Collapsible **Execution Trace Pills** on every assistant message (e.g. `⚡ Tool Execution Trace (2 steps) — list_files, read_file`) with full step breakdown and outputs.
  - Persistent Chat History in `localStorage` preserving past sessions, prompts, responses, and tool execution traces across browser refreshes.
  - Claude-style floating rounded card composer at the bottom with quick suggestion pills.
  - Minimalist top header with model selector and workspace drawer toggle.
- Built the **OpenCode-style Terminal CLI** in `cli/main.py` using `rich`:
  - Distinctive colored header banner showing active model, Apple Silicon Metal acceleration, sandboxed workspace, and slash commands.
  - Custom `CodePilot ❯` prompt with colored status.
  - Slash command suite: `/help`, `/model <name>`, `/workspace`, `/trace`, `/clear`, `/exit`.
  - Tool execution cards displayed in bordered magenta panels with millisecond latency and execution status.
  - Full syntax-highlighted Markdown rendering of agent responses.

### Files created or changed
- `frontend/src/index.css` — Claude color system & warm typography
- `frontend/src/App.jsx` — persistent `localStorage` session manager and Claude layout
- `frontend/src/components/Sidebar.jsx` — Claude sidebar with session list & trace counters
- `frontend/src/components/ChatMessage.jsx` — collapsible execution trace pill & markdown
- `frontend/src/components/Header.jsx` — minimalist Claude header
- `cli/main.py` — OpenCode-style interactive terminal CLI
- `backend/requirements.txt` — added `rich`

### Commands and tests
- `cd frontend && npm run build` — PASS (built in 727ms)
- `printf "/help\n/workspace\n/exit\n" | .venv/bin/python cli/main.py` — PASS
- `printf "List the files in the workspace\n/exit\n" | .venv/bin/python cli/main.py` — PASS (Tool call executed, markdown response rendered)

### Current status
Both the Claude-style Web UI and OpenCode-style CLI are fully implemented and verified.


---

## 2026-11-18 — Multi-Turn History Persistence & Bracket-Depth Tool Parsing Fix

### Issues diagnosed
1. **Raw JSON Leak:** When the local LLM generated conversational text before its JSON tool call (e.g. `To determine what is used to build the frontend... {"name": "list_files", ...}`), simple `json.loads` threw an error and treated the raw text + JSON as the final assistant response rather than executing the tool.
2. **Context Amnesia Across Turns:** The frontend was only transmitting `message: prompt` without prior chat history or active workspace path, causing turn 2 (`what is used to build the frontend?`) to lose the context that turn 1 was inspecting `/Users/jenny/Development/projects/papersynth`.

### Work completed
- Implemented bracket-depth JSON scanner (`find_json_tool_objects`) in `backend/app/smoke_test.py` and `backend/app/agent/loop.py` that reliably detects and extracts tool calls regardless of leading or trailing conversational chatter.
- Added multi-turn conversation memory: `frontend/src/services/api.js` and `frontend/src/App.jsx` now pass `history` and `workspace` with each request.
- Configured dynamic workspace resolution in `backend/app/agent/loop.py` to maintain active repository paths across multiple turns.
- Started Uvicorn with `--reload` to ensure real-time module updates.
- Verified test sequence: Turn 1 (explain codebase with path) -> Turn 2 ("what is used to build the frontend?") -> accurately answers **React** (and correctly inspects `frontend/package.json` with tools).

### Commands and tests
- `uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000` — RUNNING
- `curl -X POST http://127.0.0.1:8000/api/chat` (Multi-turn) — PASS (Response: "The frontend of the PaperSynth application is built using React.")
- `curl -X POST http://127.0.0.1:8000/api/chat` (Read `package.json`) — PASS (Tools executed: `read_file`, correctly listed dependencies: `axios`, `lucide-react`, `react`, `react-dom`)


---

## 2026-11-18 — Fix: Leaked Tool-Call JSON in UI Responses

### Prompt given
"unnecessary codes given here" (screenshot showing raw `{"name": "list_files", ...}` JSON rendering in the chat UI)

### Problem diagnosed
`qwen2.5-coder:7b` sometimes emits tool calls as plain-text JSON in its `content` field instead of structured native `tool_calls`. Because `loop.py` was forwarding raw `content` directly as the final answer, the JSON bled into the UI chat bubble as visible text — breaking the user experience.

### Work completed
- Added `_clean_final_answer()` to `backend/app/agent/loop.py` using three regex patterns to strip:
  - Inline JSON tool calls: `{"name": "list_files", ...}`
  - XML-style tags: `<tool_call>...</tool_call>`
  - Function-call format: `<function=list_files>...</function>`
- Applied `_clean_final_answer()` at both final-answer return points (normal exit and max-iterations fallback).
- Strengthened the agent system prompt with explicit rules: "NEVER include raw JSON in your reply — emit function calls via the tool-calling interface."
- Added `cleanContent()` in `frontend/src/components/ChatMessage.jsx` as a second safety net that strips the same patterns before rendering markdown.

### Files changed
- `backend/app/agent/loop.py` — `_clean_final_answer()` + stronger system prompt
- `frontend/src/components/ChatMessage.jsx` — `cleanContent()` applied before `ReactMarkdown`

### Commands and tests
- Backend restarted: `source .venv/bin/activate && uvicorn backend.app.main:app --reload` — RUNNING
- Verified in UI: tool execution trace pill shows correctly; response content is clean prose/markdown only

### Current status
UI responses are now clean. Tool calls are hidden in the collapsible Execution Trace Pill only.

---

## 2026-11-18 — Docs: README and PROMPT_LOG Update + GitHub Push Prep

### Prompt given
"let's push to github now, let's update the prompt log and update the readme files"

### Work completed
- Created `README.md` from scratch with full project documentation:
  - Overview, feature list, project structure tree
  - Prerequisites, step-by-step setup and installation
  - Run commands for backend, Web UI, and CLI
  - CLI slash command reference table
  - API endpoint documentation with example request body
  - Architecture diagram (ASCII)
  - Model comparison table
  - Known limitations section
- Appended all 2026-11-18 session entries to `prompts/PROMPT_LOG.md`

### Files created or changed
- `README.md` — created (full project documentation)
- `prompts/PROMPT_LOG.md` — updated with all session entries

### Current status
Repository is clean and documented. Ready for first GitHub push.
