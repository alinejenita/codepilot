# CodePilot Architecture

```mermaid
flowchart LR
    user[User]

    subgraph clients["Client interfaces"]
        web["Web UI<br/>React + Vite"]
        browserStorage[("Browser localStorage<br/>chat sessions")]
        cli["Terminal CLI<br/>Rich"]
        viteProxy["Vite dev proxy<br/>/api"]
        web <--> browserStorage
    end

    subgraph backend["Local Python backend"]
        api["FastAPI<br/>/api/chat<br/>/api/health<br/>/api/workspace"]
        auth["Shared login<br/>signed 8-hour session cookie"]
        agent["Bounded agent loop<br/>run_agent_turn"]
        prompt["System prompt<br/>prompts/SYSTEM_PROMPT.md"]
        config["Settings<br/>login, model, Ollama URL,<br/>workspace, limits"]
        dispatcher["Allowlisted tool dispatcher"]
        fileTools["Workspace file tools<br/>list / read / search"]
        writeTool["write_file<br/>per-request opt-in"]
        testTool["run_tests<br/>per-request opt-in"]
        skillLoader["Skill loader"]
    end

    workspace[("Active workspace files")]
    skills[("Bundled skills/")]
    pytest["Pytest subprocess"]
    ollama["Local Ollama runtime<br/>selected model"]

    user --> web
    user --> cli
    web -->|"same-origin /api requests"| viteProxy
    viteProxy -->|"login / status"| auth
    auth -->|"HTTP-only session cookie"| web
    api -->|"validates session cookie"| auth
    viteProxy -->|"proxy to 127.0.0.1:8000"| api
    api -->|"POST /api/chat"| agent
    cli -->|"direct Python call"| agent
    prompt --> agent
    config --> agent

    agent <-->|"chat, tool calls,<br/>tool results, final answer"| ollama
    agent --> dispatcher
    dispatcher --> fileTools
    fileTools <-->|"workspace-confined reads"| workspace
    dispatcher --> writeTool
    writeTool -->|"only when edits enabled"| workspace
    dispatcher --> testTool
    testTool -->|"only when tests enabled"| pytest
    pytest -->|"runs in workspace"| workspace
    dispatcher --> skillLoader
    skillLoader --> skills

    agent -->|"response + execution trace"| api
    api -->|"JSON response"| web
    agent -->|"response + execution trace"| cli
```

## Request flow

- The web UI sends chat requests to FastAPI. The API calls the shared agent loop and returns its response, workspace, and tool trace.
- Browser login uses a shared server-configured username and password. Protected API routes require a signed, HTTP-only session cookie with an eight-hour lifetime.
- The terminal CLI calls the same agent loop directly; it does not send chat requests through FastAPI.
- The agent loop sends the conversation and currently enabled tool definitions to the configured local Ollama model. It dispatches allowlisted tool calls and returns a final response with the execution trace.
- File access is scoped to the active workspace. File edits and pytest execution are exposed only when enabled for the request. There is no general shell tool.
- The agent loads skill instructions from the bundled `skills/` directory when appropriate. The browser stores chat sessions in localStorage.
