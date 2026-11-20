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


---

## 2026-11-18 — Coding Agent MVP: Workspace Safety, Editing, and Test Runner

### Prompt given
"i need this to be a good coding agent now so let's do whatever this tasks need okay??"

### Work completed
- Replaced the previous path resolver with a canonical workspace guard that rejects traversal and symlinks resolving outside the configured root.
- Added bounded text search, live file previews, and atomic UTF-8 file writes. File-writing tools are only supplied when the user explicitly enables edits for a request.
- Added an opt-in pytest-only tool. It uses an argument list (never a shell), restricts targets to workspace-relative paths, applies the configured timeout, and caps returned output. There is no arbitrary command tool.
- Loaded the canonical system prompt from `prompts/SYSTEM_PROMPT.md`, wired the configured maximum agent iteration count and Ollama keep-alive setting, and made tool result/error reporting explicit.
- Updated the web UI and CLI with edit/test permission toggles. The workspace drawer now reads actual workspace files, and backend failures no longer create fake successful tool traces.
- Added automated file-tool, agent-loop, permission, and API boundary tests. Updated README setup, API, capabilities, and limitations.

### Files created or changed
- `backend/app/tools/file_tools.py` — path safety, list/read/search, atomic writes
- `backend/app/agent/loop.py` — bounded agent orchestration, guarded tools, pytest runner
- `backend/app/api/routes_chat.py` — chat permission flags and workspace preview endpoints
- `backend/tests/` — offline unit and API tests
- `frontend/src/App.jsx`, `frontend/src/services/api.js`, `frontend/src/components/WorkspacePanel.jsx` — permission controls and real workspace views
- `frontend/src/components/ChatMessage.jsx`, `frontend/src/components/Sidebar.jsx`, `frontend/src/components/ToolActivityPanel.jsx` — accurate tool and capability display
- `cli/main.py` — edit/test permission toggles and updated agent return handling
- `prompts/SYSTEM_PROMPT.md` — current tool and safety instructions
- `README.md` — current behavior, configuration, and limitations

### Commands and tests
- `.venv/bin/python -m pytest backend/tests` — PASS (17 tests)
- `cd frontend && npm run build` — PASS
- `.venv/bin/python -m backend.app.smoke_test qwen2.5-coder:7b` — PASS (local Ollama tool call)
- Local agent turn asking it to list workspace files — PASS (`list_files` executed and result synthesized)
- `git diff --check` — PASS
- `cd frontend && npm run lint` — FAIL (37 ESLint errors remain, all missing React prop validation; production build succeeds)

### Current status
CodePilot can inspect, search, and explain files; create or replace files when explicitly enabled; and run pytest on a workspace-relative target when explicitly enabled. File and test tool permissions default to off. General shell execution, streaming, and per-file diff approval are not implemented.

### Issues and decisions
- Pytest runs project code and configuration, so it remains opt-in and should only be used with a trusted workspace.
- The test tool is deliberately limited to pytest rather than accepting arbitrary shell commands.
- Frontend lint cleanup was not mixed into this feature work; the current lint failure is recorded for a separate cleanup task.

### Next steps
- Add a reviewable diff/approval flow for edits rather than relying only on request-level permission.
- Decide whether to support a carefully allowlisted set of additional commands.
- Resolve frontend ESLint issues and add interaction tests for permission toggles and workspace previews.


---

## 2026-11-18 — CLI Workspace Selection and Clear Write Failures

### Prompt given
"i need the cli to create and save files too in the mentioned directory"

### Work completed
- Added the CLI `--workspace` option so a user can intentionally select an existing directory, such as `~/Desktop`, as the active workspace boundary.
- Kept file writes opt-in through `/allow-edits`; the configured CLI workspace remains the only root accessible to the agent, and parent directories for requested new files are created automatically.
- Updated the CLI banner and `/workspace` command to show the active directory.
- Fixed tool trace status output to show a failure marker for failed tool calls instead of always printing a green success.
- Documented the Desktop example and added tests for explicit workspace selection and invalid workspace paths.

### Files created or changed
- `cli/main.py` — `--workspace` option, active workspace display, accurate tool status
- `backend/tests/test_cli.py` — CLI workspace selection tests
- `README.md` — CLI usage for selecting Desktop or another workspace
- `prompts/PROMPT_LOG.md` — this entry

### Commands and tests
- `.venv/bin/python -m pytest backend/tests` — PASS (19 tests)
- `cd frontend && npm run build` — PASS (from the previous implementation validation)
- `python -m cli.main --help` — PASS (`--workspace` option shown)
- Piped `/workspace`, `/allow-edits`, `/exit` to CLI with `--workspace "$HOME/Desktop"` — PASS (selected root displayed and edit toggle enabled)
- `git diff --check` — PASS

### Current status
The CLI can target a user-selected existing directory while preserving workspace containment. File creation and replacement still require `/allow-edits`.

### Issues and decisions
- Desktop access is not granted by default. The user must explicitly pass the directory as `--workspace`; all tool paths remain restricted to that selected root.

### Next steps
- Restart the CLI with `--workspace "$HOME/Desktop"`, enable `/allow-edits`, and test a small file creation.

### Follow-up correction — prompt-directed destinations
- The user clarified they do not want to choose a workspace when starting the CLI. The CLI now detects an explicitly requested Desktop or existing absolute home-directory save destination in the current prompt, uses it as the workspace boundary, and retains that boundary for follow-up turns.
- `/workspace` reports the active boundary; `/workspace default` returns to the configured default.
- External workspace selection is restricted to a directory under the current user's home folder and is only enabled by the CLI after parsing a save/create request. The API continues to enforce its configured workspace.
- The CLI also grants file-write permission for one task when the prompt clearly requests an implementation change, so the user does not need a separate `/allow-edits` command for ordinary create/fix/update requests. Explanatory "how-to" questions do not auto-enable writes; `/allow-edits` remains available for follow-up tasks.
- Verified with tests for Desktop/absolute-path prompt parsing and home-directory boundary enforcement.

### Follow-up correction — use the current prompt destination
- User testing showed an existing CLI process still using its previous code, so it remained scoped to the default workspace. Prompt-directed workspaces are resolved when the CLI receives each task; restart an already running CLI after updating the code.
- The destination parser now uses the nearest existing parent for a new absolute file/folder destination. An absolute model-generated path is allowed only if it resolves within that selected workspace.
- Failed write traces now report the real boundary error in the summary instead of saying "Wrote".
- Removed workspace selection from CLI startup. No startup directory choice is required; the prompt determines it for the task.
- Added regression tests for the exact Desktop calculator flow and absolute in-workspace tool paths.

---

## 2026-11-18 — Bundled Agent Skills

### Work completed
- Added bundled skills using the Agent Skills `SKILL.md` directory format with validated `name` and `description` metadata.
- Added progressive discovery: skill summaries are included in the system context, while full instructions are loaded on demand through a read-only `load_skill` tool.
- Added built-in workflows for workspace exploration, feature implementation, debugging, and testing/verification.
- Added `/skills` to the CLI and documented skill authoring, activation, and security boundaries.

### Files created or changed
- `backend/app/agent/skills.py` — validate, discover, and load bundled skills by registered name
- `backend/app/agent/loop.py` — advertise skill metadata and expose the constrained loader tool
- `skills/` — four built-in coding workflow skills
- `cli/main.py` — `/skills` command
- `prompts/SYSTEM_PROMPT.md` and `README.md` — skill behavior and usage
- `backend/tests/test_skills.py` — discovery, metadata validation, loading, and agent activation tests

### Commands and tests
- `.venv/bin/python -m pytest backend/tests -q` — PASS (31 tests)
- `git diff --check` — PASS

### Security and design decisions
- Skills are guidance, not executable plugins. They cannot grant tool availability, edit/test permissions, shell access, or a wider workspace.
- The model can load only a skill by a validated registered name; it cannot provide an arbitrary path.
- Followed the Agent Skills progressive-disclosure approach: short descriptions first, full instructions only when relevant.

---

## 2026-11-18 — Explicit CLI Workspace Selection in Prompts

### Work completed
- Fixed CLI routing for requests such as “use `<absolute path>` as the workspace and explore it.”
- Workspace-selection prompts now select only the explicitly named existing directory; they do not silently fall back to a parent when that workspace is missing.
- Kept the existing home-directory authorization boundary for CLI-selected workspaces and documented the prompt pattern.

### Verification
- `.venv/bin/python -m pytest backend/tests/test_cli.py -q` — PASS (7 tests)
- Runtime check against `/Users/jenny/Development/projects/final_archon_ai` — PASS; path exists and is selected as requested
- `git diff --check` — PASS

---

## 2026-11-19 — CLI Conversation Context and Automatic Skill Activation

### Work completed
- The CLI now passes up to the last 12 user/assistant messages into each agent turn, preserving context for follow-up prompts.
- Added automatic activation of matching skill instructions for common task signals, including project/workspace exploration and technology-stack questions.
- Clarified that project-specific questions should be answered by inspecting the active workspace with the available file tools, not by asking users to list files.
- Expanded the workspace exploration skill with direct inspection guidance for dependency manifests and technology identification.

### Verification
- `.venv/bin/python -m pytest backend/tests/test_cli.py backend/tests/test_skills.py backend/tests/test_agent_loop.py -q` — PASS (25 tests)
- `git diff --check` — PASS

---

## 2026-11-19 — Stronger Workspace Exploration Evidence

### Work completed
- Tightened the workspace-exploration skill for backend/frontend and technology-stack questions: do not answer from `README.md` alone; inspect dependency manifests for each relevant app or service.
- Added a fallback to inspect entry points, imports, and framework configuration when a dependency manifest is missing.
- Required answers to distinguish declared dependencies from technologies verified in source/configuration and identify the files supporting conclusions.
- Updated the canonical system prompt to reinforce direct workspace inspection for stack questions.
- Updated this README to explain the skill behavior and note that skill guidance is model-driven, not a guarantee of tool use.

### Verification
- `.venv/bin/python -m pytest backend/tests/test_skills.py -q` — PASS (8 tests)
- `git diff --check` — PASS

---

## 2026-11-19 — Evidence-Guided Agent Loop and Skill Workflows

### Work completed
- Agent skill selection now considers recent user conversation context, so follow-up prompts can retain the relevant exploration workflow.
- Added a server-side evidence gate for backend/frontend and project stack questions: the agent must successfully read at least two distinct non-README files before returning a stack answer. If the iteration budget ends without that evidence, it returns an explicit unverified response instead of a generated stack claim.
- Reinforced the system prompt to tie project-specific statements to inspected files, distinguish evidence from inference, and report successful changes/checks only when tool results confirm them.
- Reworked all four bundled skills into ordered workflows with explicit completion checks, scope limits, and truthful verification/reporting guidance.
- Updated the README with the evidence gate and its limitation: this reduces unsupported stack answers but cannot guarantee zero hallucinations or independently verify every model claim.

### Verification
- `.venv/bin/python -m pytest backend/tests -q` — PASS (38 tests)
- `.venv/bin/python -m compileall -q backend/app/agent backend/tests` — PASS
- `git diff --check` — PASS

### Focused regression coverage
- A follow-up stack question uses earlier user context, rejects a premature answer, reads two non-README files, and then returns the answer.
- A stack answer based on only `README.md` is withheld when the iteration budget expires.

---

## 2026-11-19 — Recovery from Unsupported Model Tool Calls

### Work completed
- Agent instructions now explicitly prohibit inventing tool names.
- When a model requests an unregistered tool, CodePilot records the failure, tells the model not to retry tools, and makes a tool-free recovery request to answer the original user task or ask a focused clarification.
- If the model requests another tool during recovery, CodePilot stops without executing it and returns an explicit error.
- Added regression tests for direct-answer recovery and stopping repeated tool requests; documented the behavior in the README.

### Verification
- `.venv/bin/python -m pytest backend/tests -q` — PASS (40 tests)
- `git diff --check` — PASS

### Correction — Fail closed instead of retrying the model
- The tool-free retry still relied on a second unverified model answer, so it did not satisfy the goal of avoiding unsupported claims.
- Replaced that retry with a deterministic failure response when any unsupported tool is requested. No requested tools in that response are executed, including otherwise valid calls bundled with the unsupported one.
- Regression tests assert that no second model response is used and that valid calls in a mixed response are not run.

---

## 2026-11-20 — Capstone Technical Project Report

### Work completed
- Embedded the existing architecture diagram and documented the project’s actual validation results and known frontend lint issues.
- Added README links to the technical report and explainer video script so the submission documents are easy to find.

### Verification
- Backend tests — PASS (45 tests)
- `cd frontend && npm run build` — PASS
- Frontend lint — reports 40 existing `react/prop-types` errors across six files; recorded in the report.
- Reopened and checked the DOCX with `python-docx`; confirmed the report content, 12 tables, and one embedded architecture image.
- `git diff --check` — PASS
