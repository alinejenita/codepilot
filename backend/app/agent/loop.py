"""Bounded agent execution loop for CodePilot."""

import json
import os
import re
import time
from typing import List, Dict, Any, Tuple
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
                        "description": "Path or directory to list. Can be relative or absolute.",
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
            "description": "Read text content of a file (e.g. README.md, code file).",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to read.",
                    }
                },
                "required": ["path"],
            },
        },
    },
]


def extract_path_from_prompt(prompt: str) -> str:
    """Check if the user explicitly provided a path in their prompt."""
    match = re.search(r"(?:path(?:\s+is)?[:=]?\s*|in\s+)(/[\w\-\./]+)", prompt)
    if match:
        extracted = match.group(1).rstrip(".")
        if os.path.exists(extracted):
            return extracted
    return settings.workspace_root


def run_agent_turn(
    user_prompt: str,
    model_name: str = None,
    max_iterations: int = 5,
) -> Tuple[str, List[Dict[str, Any]]]:
    """Execute a bounded agent loop and return the final answer + tool step traces."""
    model = model_name or settings.ollama_model
    client = ollama.Client(host=settings.ollama_base_url)

    target_workspace = extract_path_from_prompt(user_prompt)

    system_instruction = (
        "You are CodePilot, a software engineering assistant running locally.\n"
        "Your task is to inspect codebases, read files, and answer the user's questions clearly.\n"
        f"Active target directory: {target_workspace}\n"
        "When asked to explain a codebase, first list files, then read the README.md or primary entry points, "
        "and finally synthesize a concise answer matching the user's constraints."
    )

    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": user_prompt},
    ]

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
            return f"Agent error during model chat: {str(e)}", steps

        tool_calls = extract_tool_calls(res.message)

        # If no tool calls, model provided the final answer
        if not tool_calls:
            final_answer = res.message.content or "Task completed."
            return final_answer, steps

        # Execute requested tools
        for tc in tool_calls:
            fn_name = tc.get("name")
            fn_args = tc.get("arguments", {})

            start_t = time.time()
            if fn_name == "list_files":
                raw_dir = fn_args.get("directory", target_workspace)
                # If model requested '.' or empty, resolve to target_workspace
                actual_dir = target_workspace if raw_dir in (".", "") else raw_dir
                output = list_files(actual_dir, target_workspace)
                summary = f"Listed {output.get('count', 0)} files in {actual_dir}"

            elif fn_name == "read_file":
                raw_path = fn_args.get("path", "")
                if not os.path.isabs(raw_path):
                    actual_path = os.path.join(target_workspace, raw_path)
                else:
                    actual_path = raw_path
                output = read_file(actual_path, target_workspace)
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
                # Send result as user prompt to prevent Ollama protocol hangs
                messages.append({
                    "role": "user",
                    "content": f"[Tool Result for {fn_name}]: {json.dumps(output)}\nNow continue with the task or provide your final answer.",
                })

    # If reached max iterations, ask for final synthesis
    try:
        messages.append({"role": "user", "content": "Please synthesize your final answer now."})
        final_res = client.chat(model=model, messages=messages)
        return final_res.message.content or "Completed.", steps
    except Exception:
        return "Stopped: maximum iterations reached.", steps
