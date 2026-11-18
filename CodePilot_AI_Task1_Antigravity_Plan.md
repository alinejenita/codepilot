# CodePilot — AI Coding Agent
## Capstone Project 1: Master Implementation Plan

**Target deadline:** 20 November 2026  
**Development machine:** MacBook Air M4, 16 GB unified memory  
**Primary objective:** Build a locally running AI coding agent with both a command-line interface (CLI) and a browser-based interface.

---

## 1. Project overview

Build **CodePilot**, a small but capable AI coding agent that can understand a user's programming task, inspect a local project, propose and make code changes, run approved commands and tests, and explain the result.

The project must run locally. It must not require paid API keys or silently fall back to cloud models.

### Required interfaces

1. **CLI** — interactive terminal experience for asking questions and running coding tasks.
2. **Web UI** — React application for chatting with the agent, viewing tool activity, and reviewing code changes.

### Core capabilities

- Understand a coding request and plan a sequence of actions.
- Read and search files inside a configured workspace.
- Create and edit files inside that workspace.
- Run explicitly permitted terminal commands.
- Use test and command output to diagnose and fix errors.
- Show the user what tools were called and what happened.
- Ask for approval before potentially destructive or risky actions.
- Keep a record of agent activity for debugging and evaluation.

### Non-goals for the first version

- Autonomous access to the entire computer.
- Unrestricted shell access.
- Cloud model providers or paid API integrations.
- Multi-agent orchestration.
- IDE plugins, deployment automation, or production-grade sandboxing.

Keep the first version small, safe, demonstrable, and testable.

---

## 2. Recommended local model and Ollama setup

### Recommended starting model

Use **Qwen 3.5 4B through Ollama** as the initial model:

```bash
ollama pull qwen3.5:4b
```

Why start here:
- A 4B model is a more conservative fit for a 16 GB unified-memory machine.
- It leaves more memory available for macOS, the IDE, browser, FastAPI, and the React development server.
- It is suitable for building and testing the agent architecture before spending time tuning a larger model.

### Larger-model comparison

After the first end-to-end agent loop works, download and benchmark:

```bash
ollama pull qwen3.5:9b
```

The 9B Q4 model is approximately 6.6 GB on the Ollama model listing. It may produce better reasoning and code, but memory pressure is more likely when several development tools are open. Treat it as an optional upgrade, not the initial dependency.

### Coding-specialist comparison

Optionally compare:

```bash
ollama pull qwen2.5-coder:7b
```

Use the same benchmark tasks for all models. Do not assume a model is better based only on its parameter count or marketing description.

### Model selection rule

Start with `qwen3.5:4b`. Keep the model name configurable so you can switch to `qwen3.5:9b` or `qwen2.5-coder:7b` without changing agent code.

Before committing to a model, run a tool-calling smoke test. Model-family support does not guarantee that every quantized tag will reliably emit the exact tool calls your agent expects.

### Install and verify Ollama

1. Install Ollama for macOS from the official Ollama website.
2. Start the Ollama application/service.
3. Pull the starting model:

```bash
ollama pull qwen3.5:4b
```

4. Confirm that it responds:

```bash
ollama run qwen3.5:4b
```

5. In another terminal, inspect loaded model memory:

```bash
ollama ps
```

### Application configuration

Keep project configuration in a root `.env` file:

```dotenv
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen3.5:4b
OLLAMA_CONTEXT_LENGTH=8192
OLLAMA_TEMPERATURE=0.2
OLLAMA_KEEP_ALIVE=10m

WORKSPACE_ROOT=./workspace
MAX_AGENT_ITERATIONS=8
COMMAND_TIMEOUT_SECONDS=30
```

These are **CodePilot application settings**. Load them in the Python backend with a settings library such as `pydantic-settings`.

For each Ollama chat request, pass model options explicitly:

```python
options = {
    "num_ctx": settings.ollama_context_length,
    "temperature": settings.ollama_temperature,
    "num_predict": 4096,
}
```

Also pass `keep_alive=settings.ollama_keep_alive` to the Ollama chat call. Start with an 8K context. If the machine experiences memory pressure, reduce it to 4K. Avoid multiple simultaneous generations initially; serialize agent runs in the backend.

The application should connect only to `http://127.0.0.1:11434` by default. Do not implement a cloud fallback.

### Tool-calling smoke test

Before building the full agent, create a small script that:
1. Sends a user message asking the model to inspect a file.
2. Supplies one harmless tool definition, such as `list_files`.
3. Checks whether the response contains a valid tool call.
4. Validates the tool name and arguments in Python.
5. Executes the tool only after validation.
6. Sends the tool result back to the model.

If the model does not produce reliable structured tool calls, test the alternative model tags and document the result. Never execute arbitrary text as a tool call.

---

## 3. Technology stack

| Layer | Technology | Responsibility |
|---|---|---|
| Language | Python 3.11+ | Agent logic and backend |
| Local model runtime | Ollama | Runs the local LLM |
| Model integration | Ollama Python SDK or HTTP API | Chat and tool-call requests |
| Backend API | FastAPI | HTTP endpoints and orchestration |
| Validation | Pydantic | Request, response, and tool schemas |
| Python dependencies | `venv` + `pip` | Isolated backend environment |
| Frontend | React + Vite | Browser interface |
| Styling | Tailwind CSS | UI styling |
| Frontend dependencies | npm | JavaScript package management |
| Tests | pytest | Backend and agent tests |
| Version control | Git | Change tracking |

Do not use Streamlit. The web interface must be React + Vite + Tailwind CSS.

---

## 4. High-level architecture

```text
                         USER
                    /            \
                  CLI            WEB UI
                   |          React + Vite
                   |               |
                   |           HTTP / JSON
                   |               |
                   +---------- FastAPI
                                  |
                             Agent Core
                                  |
                    +-------------+-------------+
                    |             |             |
                Prompt        Tool Registry   Run Manager
                Builder          |             |
                    |       +----+----+        |
                    |       |    |    |        |
                    |     Files Search Shell   |
                    |       Tools  Tool Tool    |
                    |             |             |
                    +-------------+-------------+
                                  |
                           Ollama Adapter
                                  |
                         Local Ollama Runtime
                                  |
                         Local coding model

                 All file operations are restricted
                    to the configured workspace.
```

### Architectural rules

- The agent core must not depend directly on FastAPI or React.
- The CLI and web UI must call the same agent service.
- The model adapter must hide Ollama-specific request details.
- Tools must be registered in one central tool registry.
- Tool arguments must be validated before execution.
- File tools must enforce workspace boundaries.
- Shell commands must use an allowlist and timeout.
- The model must never receive unrestricted access to the host machine.

---

## 5. Suggested repository structure

```text
codepilot/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── routes_chat.py
│   │   │   └── routes_health.py
│   │   ├── agent/
│   │   │   ├── core.py
│   │   │   ├── loop.py
│   │   │   ├── planner.py
│   │   │   ├── state.py
│   │   │   └── message_types.py
│   │   ├── llm/
│   │   │   ├── base.py
│   │   │   └── ollama_adapter.py
│   │   ├── tools/
│   │   │   ├── registry.py
│   │   │   ├── schemas.py
│   │   │   ├── file_tools.py
│   │   │   ├── search_tool.py
│   │   │   └── shell_tool.py
│   │   ├── config.py
│   │   └── logging_config.py
│   ├── tests/
│   │   ├── test_file_tools.py
│   │   ├── test_tool_registry.py
│   │   ├── test_agent_loop.py
│   │   └── test_api.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── types/
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── cli/
│   └── main.py
├── prompts/
│   ├── SYSTEM_PROMPT.md
│   └── PROMPT_LOG.md
├── workspace/
│   └── .gitkeep
├── docs/
│   ├── architecture.md
│   ├── setup.md
│   └── evaluation.md
├── .env.example
├── .gitignore
├── README.md
└── LICENSE
```

The exact filenames may change as implementation evolves, but preserve the separation of concerns.

---

## 6. Environment setup

### Create the project and Python environment

```bash
mkdir codepilot
cd codepilot

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
pip install fastapi uvicorn ollama pydantic pydantic-settings python-dotenv pytest httpx
```

Save the backend dependencies:

```bash
pip freeze > backend/requirements.txt
```

Use the virtual environment for all Python commands. Do not install project Python dependencies globally.

### Create the React application

From the project root:

```bash
npm create vite@latest frontend -- --template react
cd frontend
npm install
npm install -D tailwindcss @tailwindcss/vite
```

Configure Tailwind according to the installed version's Vite setup instructions. Keep all frontend dependencies managed by npm.

### Git setup

```bash
git init
```

Add `.venv/`, `node_modules/`, `.env`, Python cache files, build output, and local model data to `.gitignore`. Do not commit secrets or large model files.

---

## 7. Agent design

### 7.1 Agent loop

Implement a bounded tool-use loop:

1. Receive the user's task.
2. Build the conversation using the system prompt and task.
3. Ask the local model for its next response.
4. If the response is a normal final answer, return it.
5. If the response requests a tool, validate the tool name and arguments.
6. Check permissions and workspace restrictions.
7. Execute the tool.
8. Append the tool result to the conversation.
9. Ask the model to continue.
10. Stop when the model finishes or the iteration limit is reached.

Pseudocode:

```python
for step in range(max_iterations):
    response = llm.chat(messages=messages, tools=tool_definitions)

    if response.is_final:
        return response.text

    tool_call = validate_tool_call(response.tool_call)
    result = tool_registry.execute(tool_call)
    messages.append(tool_result_message(result))

return "Stopped: maximum agent iterations reached."
```

The actual implementation must handle multiple tool calls, malformed arguments, model errors, tool errors, cancellation, and timeouts.

### 7.2 Model adapter

Create a small interface so the agent does not depend on one model vendor:

```python
class LLMAdapter:
    def chat(self, messages, tools=None):
        raise NotImplementedError
```

Implement `OllamaAdapter` with:
- Configurable model name.
- Configurable context length.
- Configurable temperature and output token limit.
- Tool definitions and tool-call response parsing.
- Clear handling of connection errors and model-not-found errors.
- No remote provider fallback.

### 7.3 Tool registry

Every tool should have:
- A stable name.
- A short description.
- A Pydantic argument schema.
- A handler function.
- A permission/risk classification.
- A predictable result structure.

Suggested result shape:

```json
{
  "ok": true,
  "tool": "read_file",
  "data": {
    "content": "..."
  },
  "error": null
}
```

Do not let the model call arbitrary Python functions by name. Only registered tools may run.

---

## 8. Initial tool set

Implement these tools in order.

### Tool 1 — `list_files`

- List files and directories under the workspace.
- Support a relative subdirectory.
- Ignore `.git`, `.venv`, `node_modules`, and other configured exclusions.
- Do not follow symlinks outside the workspace.

### Tool 2 — `read_file`

- Read a text file using a workspace-relative path.
- Enforce a maximum file size.
- Return a clear error for missing files, binary files, and invalid paths.

### Tool 3 — `search_files`

- Search text files for a query.
- Return file paths, line numbers, and short matching snippets.
- Apply ignore rules and result limits.

### Tool 4 — `write_file`

- Create or replace a text file inside the workspace.
- Reject absolute paths and path traversal.
- For an existing file, preserve a backup or show a diff before replacement.
- Require user approval for overwriting important existing files.

### Tool 5 — `run_command`

- Execute only approved commands.
- Use a fixed working directory inside the workspace.
- Never use `shell=True`.
- Apply a strict timeout and output-size limit.
- Capture stdout, stderr, and exit code.
- Require approval for commands that modify files or have elevated risk.

Start with a narrow allowlist such as Python test and inspection commands. Expand it only when required and documented.

---

## 9. Security and reliability requirements

These are core requirements, not optional polish.

### Workspace containment

- Resolve every requested path against the configured workspace root.
- Reject paths that resolve outside that root.
- Reject or safely handle symlinks that escape the workspace.
- Never accept arbitrary absolute paths from the model.

### Terminal safety

- Use `subprocess.run()` with an argument list, not a shell command string.
- Do not use `shell=True`.
- Use an allowlist of executable commands and permitted argument patterns.
- Apply timeouts and output limits.
- Ask for approval before destructive or potentially risky commands.
- Do not run commands requiring administrator privileges.

### Model-output validation

- Treat model output as untrusted input.
- Validate tool names, argument types, path values, and command arguments.
- Handle malformed JSON and unknown tools safely.
- Never execute code just because the model produced it.

### API safety

- Bind the development server to localhost by default.
- Validate request sizes.
- Return structured errors without exposing stack traces to the browser.
- Do not expose the Ollama service or local workspace to a public network.

### Logging

Record:
- Timestamp and run ID.
- User task.
- Model name and settings.
- Agent iteration count.
- Tool name and validated arguments.
- Tool result summary and exit status.
- Errors and final response.

Avoid logging unnecessary sensitive file contents.

---

## 10. System prompt

Create `prompts/SYSTEM_PROMPT.md` as the canonical system prompt. Load it from disk rather than duplicating the prompt in several Python files.

It should instruct the agent to:

1. Act as a careful software engineering assistant.
2. Inspect the workspace before proposing edits.
3. Make a short plan for multi-step tasks.
4. Use only tools that are explicitly available.
5. Never invent tool results.
6. Keep all file operations inside the workspace.
7. Validate tool arguments and respect approval requirements.
8. Make focused changes rather than rewriting unrelated files.
9. Run relevant tests after code changes when permitted.
10. Report files changed, commands run, test results, and remaining limitations.
11. Ask a concise clarification when essential requirements are missing.
12. Stop when the task is complete or the iteration budget is exhausted.

The prompt is guidance, not a security boundary. Enforce all restrictions in Python code.

---

## 11. Antigravity workflow and prompt logging

Use Antigravity as the coding assistant that helps implement the project, while keeping the repository understandable and under version control.

### `prompts/PROMPT_LOG.md`

Maintain this as an append-only project diary. Add an entry after every substantial Antigravity task.

Each entry should include:

```markdown
## YYYY-MM-DD — Short task title

### Prompt given
[Paste the exact prompt given to Antigravity.]

### Work completed
- [What was implemented.]

### Files created or changed
- `path/to/file.py` — [reason]

### Commands and tests
- Command: `...`
- Result: PASS / FAIL / NOT RUN
- Notes: ...

### Current status
[What works now.]

### Issues and decisions
[Errors, trade-offs, and decisions.]

### Next steps
- [Next small task.]
```

Do not rewrite old entries to make the history look cleaner. Add corrections or follow-up entries instead.

### Antigravity task discipline

- Give Antigravity one milestone or small feature at a time.
- Ask it to inspect existing files before editing.
- Ask it to explain the intended changes before broad refactors.
- Require it to run relevant tests and report exact results.
- Review diffs before accepting changes.
- Do not ask it to implement the entire project in one prompt.

---

## 12. Frontend requirements

Build a clean, responsive React interface.

### Main layout

- Left sidebar: new chat and recent sessions (if session persistence is implemented).
- Main panel: conversation history.
- Message composer: multiline input and send button.
- Activity area: visible tool calls and their status.
- Workspace status: configured workspace and backend connection state.

### Message display

Support:
- User messages.
- Agent responses.
- Code blocks with syntax highlighting if practical.
- Tool activity entries.
- Error messages.
- Loading/generating state.

### Tool activity display

For each tool call, show:
- Tool name.
- Short arguments summary.
- Running, completed, or failed status.
- A concise result summary.

Do not expose secrets or dump entire file contents into the activity panel unnecessarily.

### API integration

At minimum implement:
- `GET /api/health`
- `POST /api/chat`

The chat endpoint should accept a task and return the agent response plus structured run metadata. If streaming is added, use Server-Sent Events or another clearly documented streaming approach; do not let streaming delay the first working version.

---

## 13. CLI requirements

The CLI must use the same agent service as the web API.

Minimum features:
- Start an interactive session.
- Accept a task.
- Display the agent response.
- Display tool activity and errors.
- Support an exit command such as `/exit`.
- Show the active model and workspace.
- Provide a clear message when Ollama is unavailable.

Example usage:

```bash
python -m cli.main
```

Example session:

```text
CodePilot — local coding agent
Model: qwen3.5:4b
Workspace: ./workspace

You> Explain the structure of this project.

CodePilot> I will inspect the workspace first.
[tool] list_files — completed
[tool] read_file — completed

CodePilot> The project contains ...
```

---

## 14. API contract

### Health endpoint

`GET /api/health`

Example response:

```json
{
  "status": "ok",
  "ollama_connected": true,
  "model": "qwen3.5:4b",
  "workspace": "./workspace"
}
```

### Chat endpoint

`POST /api/chat`

Example request:

```json
{
  "message": "Inspect this project and explain its structure."
}
```

Example response:

```json
{
  "run_id": "example-run-id",
  "status": "completed",
  "response": "This project contains ...",
  "steps": [
    {
      "tool": "list_files",
      "status": "completed",
      "summary": "Listed workspace files"
    }
  ]
}
```

Use Pydantic request and response models. The example run ID is illustrative; generate real unique IDs in the application.

---

## 15. Testing and evaluation

### Unit tests

Test:
- Path traversal rejection.
- Absolute path rejection.
- Symlink escape rejection.
- File read and write behavior.
- Search result limits.
- Unknown tool rejection.
- Invalid tool arguments.
- Command allowlist enforcement.
- Command timeout behavior.
- Agent iteration limit.
- Ollama unavailable behavior.

### Integration tests

Test:
- FastAPI health endpoint.
- Chat endpoint with a mocked model adapter.
- Tool call → tool result → final response flow.
- CLI using the shared agent service.

Use mocked model responses for deterministic automated tests. Keep a separate small set of manual tests against the real local model.

### Model benchmark tasks

Run the same tasks with each candidate model:

1. Explain a small Python project.
2. Find a named function in a multi-file workspace.
3. Create a small Python module from a specification.
4. Diagnose a deliberately failing unit test.
5. Make a focused change and run the test suite.
6. Use two tools in sequence and summarize the result.

Score each from 0–2:

| Criterion | 0 | 1 | 2 |
|---|---|---|---|
| Tool selection | Incorrect | Partly correct | Correct |
| Tool arguments | Invalid | Needs correction | Valid |
| Code quality | Fails | Partly works | Works |
| Test behavior | Does not run | Runs incorrectly | Correctly runs and interprets |
| Final explanation | Misleading | Incomplete | Accurate |

Record latency, failures, and memory observations using `ollama ps` and macOS Activity Monitor. Select the model based on overall agent performance, not just response speed.

---

## 16. Milestones and schedule

The deadline is 20 November 2026. Prioritize a reliable end-to-end demonstration over optional features.

### Milestone 1 — Environment and model verification
**Target: 18 November**

- [ ] Create repository and folder structure.
- [ ] Create and activate `.venv`.
- [ ] Create React/Vite frontend and install Tailwind.
- [ ] Install Ollama and pull `qwen3.5:4b`.
- [ ] Verify a normal chat response.
- [ ] Run the tool-calling smoke test.
- [ ] Record model, context, and memory observations.

**Exit condition:** Backend environment, frontend environment, and local model all run.

### Milestone 2 — Backend and safe tools
**Target: 18–19 November**

- [ ] Implement settings and `.env.example`.
- [ ] Implement Ollama adapter.
- [ ] Implement tool schemas and registry.
- [ ] Implement `list_files`, `read_file`, and `search_files`.
- [ ] Implement safe `write_file`.
- [ ] Implement restricted `run_command`.
- [ ] Add unit tests for workspace containment and command safety.

**Exit condition:** Tools work independently and security tests pass.

### Milestone 3 — Agent loop and CLI
**Target: 19 November**

- [ ] Implement canonical system prompt.
- [ ] Implement bounded agent loop.
- [ ] Handle tool calls and tool results.
- [ ] Add error handling and run logging.
- [ ] Build interactive CLI.
- [ ] Complete one end-to-end coding task in the workspace.

**Exit condition:** CLI can inspect a project, make a controlled change, and run a test.

### Milestone 4 — FastAPI and React UI
**Target: 19–20 November**

- [ ] Implement health endpoint.
- [ ] Implement chat endpoint.
- [ ] Connect React chat UI to FastAPI.
- [ ] Display tool activity and errors.
- [ ] Add loading and backend-connection states.
- [ ] Test the same task through the web interface.

**Exit condition:** CLI and web UI both use the same working agent core.

### Milestone 5 — Evaluation and submission
**Target: 20 November**

- [ ] Run automated tests.
- [ ] Run model comparison tasks.
- [ ] Fix critical bugs only; avoid late feature expansion.
- [ ] Complete README and setup instructions.
- [ ] Complete architecture and evaluation notes.
- [ ] Capture screenshots and a short demo recording.
- [ ] Prepare final project report and known-limitations section.
- [ ] Verify a clean setup procedure from the README.

**Exit condition:** A reproducible local demo works and submission materials are complete.

---

## 17. Definition of done

The project is ready when all of the following are true:

- [ ] Ollama runs the configured model locally.
- [ ] No cloud API key is required.
- [ ] CLI accepts a coding task and returns a useful response.
- [ ] React web UI accepts a coding task and displays the response.
- [ ] Both interfaces use the same agent core.
- [ ] The agent can list, read, search, and write workspace files.
- [ ] The agent can run approved commands with timeout and output limits.
- [ ] Tool calls are validated before execution.
- [ ] Workspace path traversal is blocked.
- [ ] Risky actions require approval.
- [ ] Agent iterations are bounded.
- [ ] Automated tests pass.
- [ ] README explains installation, setup, run commands, architecture, and limitations.
- [ ] Demo evidence and final report are ready.

---

## 18. Run commands (intended development workflow)

Start Ollama using the macOS app or service. In terminal one:

```bash
source .venv/bin/activate
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

In terminal two, run the frontend:

```bash
cd frontend
npm run dev
```

In terminal three, run the CLI:

```bash
source .venv/bin/activate
python -m cli.main
```

Adjust module paths if the final package layout differs. Document the final commands in `README.md`.

---

## 19. Submission deliverables

1. **Source repository** — backend, frontend, CLI, tests, prompts, and configuration example.
2. **README** — project overview, prerequisites, installation, configuration, run instructions, and troubleshooting.
3. **Architecture document** — components, agent loop, model adapter, and tool flow.
4. **Evaluation document** — model comparison, test results, limitations, and design decisions.
5. **Screenshots** — CLI and web UI.
6. **Short demo video** — show a task from prompt through tool use to verified result.
7. **Final report** — problem statement, objectives, methodology, implementation, evaluation, limitations, and future work.

---

## 20. Important implementation principles

1. Build a narrow working vertical slice before adding features.
2. Use one model and one tool first; expand only after the loop works.
3. Keep model choice configurable.
4. Keep all model execution local through Ollama.
5. Treat model outputs as untrusted.
6. Enforce security in code, not only in the system prompt.
7. Keep the CLI and web UI thin; the agent core owns the logic.
8. Use automated tests for safety-critical behavior.
9. Record Antigravity prompts and implementation outcomes in `prompts/PROMPT_LOG.md`.
10. Reserve time for testing and submission. A reliable, explainable agent is better than a large collection of unfinished features.
