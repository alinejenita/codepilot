"""Bounded multi-turn agent execution loop for CodePilot."""

import json
import os
import re
import time
from typing import List, Dict, Any, Tuple, Optional
import ollama
from backend.app.config import settings
from backend.app.tools.file_tools import list_files, read_file
from backend.app.smoke_test import extract_tool_calls

AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files and directories in a directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "Path or directory to list. Defaults to the active target workspace.",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read text content of a file (e.g. package.json, README.md, code files).",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to read (relative or absolute).",
                    }
                },
                "required": ["path"],
            },
        },
    },
]


def extract_path_from_text(text: str) -> Optional[str]:
    """Search text for an absolute filesystem path that exists."""
    matches = re.findall(r"(/[\w\-\./]+)", text)
    for m in matches:
        clean = m.rstrip(".,;:'\"")
        if os.path.exists(clean) and os.path.isdir(clean):
            return clean
    return None


def resolve_active_workspace(
    user_prompt: str,
    history: List[Dict[str, str]] = None,
    explicit_workspace: str = None,
) -> str:
    """Determine the active workspace from explicit parameter, current prompt, or prior history."""
    if explicit_workspace and os.path.exists(explicit_workspace):
        return explicit_workspace

    # Check current prompt
    path_in_prompt = extract_path_from_text(user_prompt)
    if path_in_prompt:
        return path_in_prompt

    # Check conversation history backwards
    if history:
        for msg in reversed(history):
            content = msg.get("content", "")
            found = extract_path_from_text(content)
            if found:
                return found

    return settings.workspace_root



# Patterns that indicate the model leaked a raw tool call JSON into its reply
_TOOL_CALL_PATTERNS = [
    # Full inline JSON: {"name": "list_files", ...}
    re.compile(
        r'\{["\']?name["\']?\s*:\s*["\'](?:list_files|read_file|search_files|run_command|write_file)["\'].*?\}',
        re.DOTALL,
    ),
    # XML-style: <tool_call>...</tool_call>
    re.compile(r'<tool_call>.*?</tool_call>', re.DOTALL | re.IGNORECASE),
    # Function-call text pattern: <function=list_files> ... </function>
    re.compile(r'<function=\w+>.*?</function>', re.DOTALL | re.IGNORECASE),
]


def _clean_final_answer(text: str) -> str:
    """Remove any leaked raw tool-call JSON or XML from the model's final reply."""
    if not text:
        return text
    cleaned = text
    for pattern in _TOOL_CALL_PATTERNS:
        cleaned = pattern.sub('', cleaned)
    # Collapse runs of blank lines left behind
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned).strip()
    return cleaned


def run_agent_turn(
    user_prompt: str,
    model_name: str = None,
    history: List[Dict[str, str]] = None,
    workspace: str = None,
    max_iterations: int = 5,
) -> Tuple[str, List[Dict[str, Any]], str]:
    """Execute a bounded agent loop and return (final_answer, steps, active_workspace)."""
    model = model_name or settings.ollama_model
    client = ollama.Client(host=settings.ollama_base_url)

    active_workspace = resolve_active_workspace(user_prompt, history, workspace)

    system_instruction = (
        "You are CodePilot, a software engineering assistant running locally.\n"
        "Your task is to inspect codebases, read files, and answer the user's questions clearly.\n"
        f"Active target directory: {active_workspace}\n"
        "RULES:\n"
        "1. When you need to inspect files, emit a TOOL CALL (function call) — never write JSON tool calls as plain text.\n"
        "2. Your final answer must be clean prose or markdown. NEVER include raw JSON like {\"name\": \"...\", \"arguments\": {...}} in your reply.\n"
        "3. Keep file operations within the active target directory.\n"
        "4. Be concise and direct. After getting tool results, synthesize a human-readable answer."
    )

    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": system_instruction},
    ]

    # Append recent conversation history (up to last 6 turns)
    if history:
        for msg in history[-6:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})

    # Append current user prompt
    messages.append({"role": "user", "content": user_prompt})

    steps: List[Dict[str, Any]] = []

    for iteration in range(max_iterations):
        try:
            res = client.chat(
                model=model,
                messages=messages,
                tools=AGENT_TOOLS,
                options={
                    "num_ctx": settings.ollama_context_length,
                    "temperature": settings.ollama_temperature,
                },
            )
        except Exception as e:
            return f"Agent error during model chat: {str(e)}", steps, active_workspace

        tool_calls = extract_tool_calls(res.message)

        # If no tool calls were emitted, we have the final answer
        if not tool_calls:
            final_answer = _clean_final_answer(res.message.content or "Task completed.")
            return final_answer, steps, active_workspace

        # Execute requested tools
        for tc in tool_calls:
            fn_name = tc.get("name")
            fn_args = tc.get("arguments", {})

            start_t = time.time()
            if fn_name == "list_files":
                raw_dir = fn_args.get("directory", active_workspace)
                actual_dir = active_workspace if raw_dir in (".", "./workspace", "") else raw_dir
                if not os.path.isabs(actual_dir):
                    actual_dir = os.path.join(active_workspace, actual_dir)
                output = list_files(actual_dir, active_workspace)
                summary = f"Listed {output.get('count', 0)} files in {actual_dir}"

            elif fn_name == "read_file":
                raw_path = fn_args.get("path", "")
                if not os.path.isabs(raw_path):
                    actual_path = os.path.join(active_workspace, raw_path)
                else:
                    actual_path = raw_path
                output = read_file(actual_path, active_workspace)
                summary = f"Read {os.path.basename(actual_path)} ({output.get('size', 0)} bytes)"

            else:
                output = {"ok": False, "error": f"Tool '{fn_name}' not available."}
                summary = f"Unknown tool: {fn_name}"

            latency_ms = round((time.time() - start_t) * 1000, 1)

            step_record = {
                "tool": fn_name,
                "args": fn_args,
                "status": "completed" if output.get("ok") else "failed",
                "summary": summary,
                "result": output,
                "latency_ms": latency_ms,
            }
            steps.append(step_record)

            # Properly format response for next turn
            if getattr(res.message, "tool_calls", None):
                messages.append(res.message)
                messages.append({
                    "role": "tool",
                    "content": json.dumps(output),
                })
            else:
                messages.append({
                    "role": "assistant",
                    "content": res.message.content or json.dumps(tc),
                })
                # Send result as user prompt to avoid Ollama protocol hangs
                messages.append({
                    "role": "user",
                    "content": f"[Tool Result for {fn_name}]: {json.dumps(output)}\nNow continue with the task or provide your final answer.",
                })

    # If reached max iterations, ask for final synthesis
    try:
        messages.append({"role": "user", "content": "Please synthesize your final answer now."})
        final_res = client.chat(model=model, messages=messages)
        return _clean_final_answer(final_res.message.content or "Completed."), steps, active_workspace
    except Exception:
        return "Stopped: maximum iterations reached.", steps, active_workspace
