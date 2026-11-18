"""Smoke test and tool-calling extraction utilities."""

import json
import os
import re
import sys
from typing import Any, Dict, List
from pydantic import BaseModel, Field
import ollama
from dotenv import load_dotenv

load_dotenv()

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
WORKSPACE_ROOT = os.path.abspath(os.getenv("WORKSPACE_ROOT", "./workspace"))


class ListFilesArgs(BaseModel):
    directory: str = Field(default=".", description="Relative directory path to list")


list_files_tool = {
    "type": "function",
    "function": {
        "name": "list_files",
        "description": "List files and subdirectories in the specified workspace directory.",
        "parameters": {
            "type": "object",
            "properties": {
                "directory": {
                    "type": "string",
                    "description": "Relative directory path inside the workspace to list. Defaults to '.'",
                }
            },
            "required": [],
        },
    },
}


def find_json_tool_objects(s: str) -> List[Dict[str, Any]]:
    """Scan string for any valid JSON object that contains a 'name' field for tool calling."""
    results = []
    i = 0
    while i < len(s):
        if s[i] == "{":
            depth = 0
            start = i
            for j in range(i, len(s)):
                if s[j] == "{":
                    depth += 1
                elif s[j] == "}":
                    depth -= 1
                    if depth == 0:
                        candidate = s[start:j+1]
                        try:
                            obj = json.loads(candidate)
                            if isinstance(obj, dict) and "name" in obj:
                                results.append(obj)
                        except Exception:
                            pass
                        i = j
                        break
        i += 1
    return results


def extract_tool_calls(message) -> List[Dict[str, Any]]:
    """Extract tool calls from native Ollama tool_calls, XML tags, or embedded JSON in content."""
    tool_calls = []

    # 1. Native tool calls
    if getattr(message, "tool_calls", None):
        for tc in message.tool_calls:
            tool_calls.append({
                "name": tc.function.name,
                "arguments": tc.function.arguments or {},
            })
        return tool_calls

    content = getattr(message, "content", "") or ""

    # 2. Check XML tags <tool_call>...</tool_call>
    xml_matches = re.findall(r"<tool_call>(.*?)</tool_call>", content, re.DOTALL)
    for raw in xml_matches:
        try:
            data = json.loads(raw.strip())
            if isinstance(data, dict) and "name" in data:
                tool_calls.append({
                    "name": data["name"],
                    "arguments": data.get("arguments", {}),
                })
        except Exception:
            pass

    if tool_calls:
        return tool_calls

    # 3. Robust bracket-depth scanner for any embedded JSON tool call in conversational text
    embedded = find_json_tool_objects(content)
    for obj in embedded:
        tool_calls.append({
            "name": obj["name"],
            "arguments": obj.get("arguments", {}),
        })

    return tool_calls


def run_smoke_test(model_name: str = OLLAMA_MODEL) -> bool:
    print(f"=== CodePilot Tool-Calling Smoke Test ===")
    print(f"Ollama URL : {OLLAMA_BASE_URL}")
    print(f"Model      : {model_name}")
    print(f"Workspace  : {WORKSPACE_ROOT}")
    print("------------------------------------------")

    client = ollama.Client(host=OLLAMA_BASE_URL)

    try:
        models_response = client.list()
        available_models = [m.model for m in models_response.models]
        print(f"[OK] Connected to Ollama. Models present: {available_models}")
    except Exception as e:
        print(f"[FAIL] Could not connect to Ollama: {e}")
        return False

    os.makedirs(WORKSPACE_ROOT, exist_ok=True)

    messages = [
        {
            "role": "system",
            "content": "You are a coding assistant with access to tools. Always call list_files when asked to inspect files.",
        },
        {
            "role": "user",
            "content": "Please inspect the workspace directory and list the files in it.",
        },
    ]

    try:
        response = client.chat(
            model=model_name,
            messages=messages,
            tools=[list_files_tool],
        )
    except Exception as e:
        print(f"[FAIL] Ollama chat call failed: {e}")
        return False

    tool_calls = extract_tool_calls(response.message)
    if not tool_calls:
        print(f"[FAIL] Model did not return any tool call. Message content: {response.message.content}")
        return False

    print(f"[OK] Model returned {len(tool_calls)} tool call(s): {tool_calls}")
    return True


if __name__ == "__main__":
    model = sys.argv[1] if len(sys.argv) > 1 else OLLAMA_MODEL
    success = run_smoke_test(model)
    sys.exit(0 if success else 1)
