# CodePilot 🚀

> **Capstone Project 1** — A locally-running AI coding agent with a Claude-style Web UI and an OpenCode-style terminal CLI, powered entirely by Ollama on Apple Silicon.

---

## Overview

CodePilot is a full-stack AI coding assistant designed to run locally through Ollama. It can inspect and search a configured workspace, answer engineering questions with tool evidence, and create or replace files when the user explicitly enables file edits for a request. It does not use cloud model APIs.

| Layer | Stack |
|---|---|
| **LLM Runtime** | Ollama (`qwen2.5-coder:7b` default, `qwen3.5:4b` fallback) |
| **Backend** | FastAPI + Python 3.13 |
| **Agent Loop** | Custom bounded multi-turn loop with tool call extraction |
| **Web UI** | React 18 + Vite 5 + Tailwind CSS v4 |
| **Terminal CLI** | Python `rich` (OpenCode-style) |
| **Hardware** | MacBook Air M4 — 100% Apple Silicon Metal GPU offload |

---

## Features

- 🧠 **Multi-step agent loop** — model plans, calls tools, reads results, synthesizes answers
- 🔎 **Workspace search** — bounded, case-insensitive search with file and line references
- ✍️ **Opt-in file edits** — file writes are not available unless enabled for the request
- 🧪 **Opt-in pytest runner** — runs only `python -m pytest` against a workspace-relative target; no general shell tool
- 💬 **Claude-style Web UI** — persistent chat history, collapsible execution trace pills, terracotta accent palette
- 🖥️ **OpenCode-style CLI** — rich terminal panels, `CodePilot ❯` prompt, slash commands
- 📂 **Live workspace preview** — reads the actual files from the configured workspace
- 🔒 **Workspace containment** — traversal and symlink escapes are rejected
- 🛠️ **Tool execution traces** — every tool call logged with args, result, and latency

---

## Project Structure

```
codepilot/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── config.py            # pydantic-settings config from .env
│   │   ├── agent/
│   │   │   └── loop.py          # Bounded multi-turn agent loop
│   │   │   └── skills.py        # Bundled Agent Skills discovery and loading
│   │   ├── api/
│   │   │   ├── routes_health.py # GET /api/health
│   │   │   └── routes_chat.py   # POST /api/chat
│   │   ├── tools/
│   │   │   └── file_tools.py    # list, read, search, and opt-in write tools
│   │   ├── tests/               # Offline unit and API tests
│   │   └── smoke_test.py        # Tool-calling verification script
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Main layout + session manager
│   │   ├── components/
│   │   │   ├── Sidebar.jsx      # Session history list
│   │   │   ├── Header.jsx       # Model switcher + workspace toggle
│   │   │   ├── ChatMessage.jsx  # Markdown + collapsible trace pills
│   │   │   ├── WorkspacePanel.jsx
│   │   │   └── ToolActivityPanel.jsx
│   │   └── services/
│   │       └── api.js           # fetchHealth + sendChatMessage
│   ├── vite.config.js
│   └── package.json
├── cli/
│   └── main.py                  # OpenCode-style Rich terminal CLI
├── prompts/
│   ├── SYSTEM_PROMPT.md         # Canonical agent system instructions
│   └── PROMPT_LOG.md            # Append-only development diary
├── skills/                      # Bundled, on-demand Agent Skills
├── workspace/                   # Default sandboxed workspace
├── .env.example
└── README.md
```

---

## Prerequisites

- **macOS** (Apple Silicon recommended)
- **Python 3.11+**
- **Node.js 18+**
- **Ollama** — [https://ollama.com](https://ollama.com)

---

## Setup & Installation

### 1. Clone the repo

```bash
git clone <your-repo-url>
cd codepilot
```

### 2. Install Ollama and pull models

```bash
brew install ollama
brew services start ollama
ollama pull qwen2.5-coder:7b
ollama pull qwen3.5:4b
```

### 3. Set up Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env
# Edit .env if needed — defaults work out of the box
```

### 5. Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

---

## Running the App

### Backend (FastAPI)

```bash
cd /Users/jenny/Development/projects/codepilot
source .venv/bin/activate
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

### Web UI (Vite dev server)

```bash
cd frontend
npm run dev
# Open http://localhost:5173
```

### Terminal CLI

```bash
source .venv/bin/activate
python cli/main.py
```

The CLI starts in the configured default workspace. You can name a different save destination or explicitly select an existing workspace directly in a task prompt; for example:

> Create a basic OOP calculator and save it in a new `test_calc` folder on my Desktop as `calculator.py`.
>
> Use `/Users/jenny/Development/projects/final_archon_ai` as the workspace and explore its contents.

When the prompt explicitly names Desktop or an absolute directory under your home folder as the save destination, the CLI selects that location for the task (using the nearest existing parent if the requested folder does not exist). For workspace-selection requests, the CLI switches only to the named existing directory. The agent can create missing folders beneath a selected workspace; paths outside it remain blocked. Use `/workspace` to see the active directory or `/workspace default` to return to the configured default.

The CLI carries up to the last 12 user/assistant messages into each agent request, so follow-up prompts can refer to earlier questions and answers. For project-specific questions, CodePilot inspects the active workspace with its file tools instead of asking the user to enumerate files. Relevant bundled skill instructions are automatically included for common task types.

For a direct request to create or change a file (for example, “create a calculator file”), the CLI enables file edits for that task only. For broader follow-up editing, enter `/allow-edits` to toggle persistent edit permission. Restart an already-open CLI process after updating CodePilot so it loads these prompt-routing changes.

---

## CLI Slash Commands

| Command | Description |
|---|---|
| `/help` | Show available commands |
| `/model <name>` | Switch active model |
| `/workspace` | Show active workspace path and list its files |
| `/trace` | Show the detailed tool execution trace of the last turn |
| `/skills` | List bundled agent skills and when they apply |
| `/allow-edits` | Toggle file creation and replacement |
| `/allow-tests` | Toggle pytest execution for subsequent tasks |
| `/clear` | Clear the terminal |
| `/exit` | Quit CodePilot |

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Ollama status + available models |
| `GET` | `/api/workspace` | List files at the configured workspace root |
| `GET` | `/api/workspace/file?path=...` | Preview a UTF-8 text file inside the workspace |
| `POST` | `/api/chat` | Send a message; returns answer + tool steps |

### `/api/chat` request body

```json
{
  "message": "Explain the backend structure",
  "model": "qwen2.5-coder:7b",
  "history": [...],
  "workspace": "./subdirectory",
  "allow_edits": false,
  "allow_test_execution": false
}
```

`WORKSPACE_ROOT` in `.env` defines the maximum accessible directory. A request may select that root or a subdirectory, never a path outside it. Set `allow_edits` to `true` only when the user has approved file changes for that request. Pytest can execute code and project configuration; enable `allow_test_execution` only for a workspace you trust.

## Agent Skills

CodePilot supports bundled skills in the open Agent Skills directory format: each `skills/<name>/SKILL.md` contains YAML frontmatter with a matching lowercase kebab-case `name` and a `description`, followed by Markdown instructions. CodePilot includes only each skill's name and description in the model's system context. For common task signals, matching skill instructions are included automatically; otherwise, the model can call the read-only `load_skill` tool to load relevant guidance. The loader only accepts registered bundled skill names; it does not read arbitrary paths or execute skill files.

Built-in skills cover [workspace exploration](./skills/workspace-exploration/SKILL.md), [feature implementation](./skills/feature-implementation/SKILL.md), [debugging](./skills/debugging/SKILL.md), and [testing and verification](./skills/testing-and-verification/SKILL.md). For questions about the backend/frontend stack, workspace exploration directs CodePilot to inspect manifests for each relevant app or service (such as `requirements.txt` and `package.json`) rather than relying on `README.md` alone. If a manifest is absent, it should inspect entry points, imports, and framework configuration, and identify the files supporting its conclusions.

Skills provide workflow guidance only: they cannot enable file edits or tests, grant shell access, or change workspace restrictions. Skill activation and tool use are model-guided rather than a guarantee that every suggested inspection will occur, so verify tool traces for important answers. Use `/skills` in the CLI to list available skills.

---

## Smoke Test

Verify the full tool-calling pipeline without the UI:

```bash
source .venv/bin/activate
python -m backend.app.smoke_test
```

Run the automated tests without requiring Ollama:

```bash
source .venv/bin/activate
pytest backend/tests
```

---

## Models

| Model | Size | Use |
|---|---|---|
| `qwen2.5-coder:7b` | 4.7 GB | Default — best tool-calling reliability |
| `qwen3.5:4b` | 4.0 GB | Fallback — faster, lighter |

Both run with 100% GPU offload via Apple Silicon Metal on the M4.

---

## Architecture

```
User (Browser / Terminal)
        │
        ▼
  FastAPI Backend (:8000)
        │
        ▼
  Agent Loop (loop.py)
   ├─ System prompt + history + user message
   ├─ Ollama chat() with tool definitions
   ├─ Extract tool calls (native → XML → bracket-depth JSON)
   ├─ Execute tools (list, read, search, opt-in write, opt-in pytest)
   └─ Feed results back → next iteration
        │
        ▼
  Final answer (cleaned, markdown)
        │
        ▼
  React UI / Rich CLI
```

---

## Known Limitations

- No general shell command tool is available. Pytest runs only after explicit user opt-in.
- File edits replace a whole file when explicitly enabled. Review changes in version control before accepting them.
- Pytest executes the target project's code; treat the test opt-in as running untrusted code.
- No streaming / SSE yet — responses arrive all at once
- Context window capped at 8192 tokens (configurable via `.env`)
- Workspace root is configured by the operator in `.env`; there is no per-request arbitrary-root access.

---

## Development Log

See [`prompts/PROMPT_LOG.md`](prompts/PROMPT_LOG.md) for a full append-only diary of all development tasks, prompts, and test outcomes.

---

## License

MIT
