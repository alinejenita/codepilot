# CodePilot 🚀

> **Capstone Project 1** — A locally-running AI coding agent with a Claude-style Web UI and an OpenCode-style terminal CLI, powered entirely by Ollama on Apple Silicon.

---

## Overview

CodePilot is a full-stack AI coding assistant that runs **100% offline** on your machine. It uses a local LLM (via Ollama) to inspect codebases, read files, and answer engineering questions through a multi-step tool-calling agent loop — no cloud APIs required.

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
- 💬 **Claude-style Web UI** — persistent chat history, collapsible execution trace pills, terracotta accent palette
- 🖥️ **OpenCode-style CLI** — rich terminal panels, `CodePilot ❯` prompt, slash commands
- 📂 **Multi-turn context** — remembers active codebase path across conversation turns
- 🔒 **Workspace containment** — file tools are sandboxed to the target directory
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
│   │   ├── api/
│   │   │   ├── routes_health.py # GET /api/health
│   │   │   └── routes_chat.py   # POST /api/chat
│   │   ├── tools/
│   │   │   └── file_tools.py    # list_files + read_file (sandboxed)
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

---

## CLI Slash Commands

| Command | Description |
|---|---|
| `/help` | Show available commands |
| `/model <name>` | Switch active model |
| `/workspace` | Show active workspace path |
| `/trace` | Toggle tool execution trace display |
| `/clear` | Clear the terminal |
| `/exit` | Quit CodePilot |

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Ollama status + available models |
| `POST` | `/api/chat` | Send a message; returns answer + tool steps |

### `/api/chat` request body

```json
{
  "message": "Explain the backend structure",
  "model": "qwen2.5-coder:7b",
  "history": [...],
  "workspace": "/path/to/project"
}
```

---

## Smoke Test

Verify the full tool-calling pipeline without the UI:

```bash
source .venv/bin/activate
python backend/app/smoke_test.py
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
   ├─ Execute tools (list_files, read_file)
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

- File tools are currently read-only (`list_files`, `read_file`)
- No streaming / SSE yet — responses arrive all at once
- Workspace write and shell execution tools are planned but not yet wired
- Context window capped at 8192 tokens (configurable via `.env`)

---

## Development Log

See [`prompts/PROMPT_LOG.md`](prompts/PROMPT_LOG.md) for a full append-only diary of all development tasks, prompts, and test outcomes.

---

## License

MIT
