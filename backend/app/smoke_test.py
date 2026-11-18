"""Smoke test for verifying Ollama connectivity and structured tool calling.

Validates that:
1. Ollama is running and accessible.
2. The configured model can produce structured tool calls (e.g. list_files).
3. The response can be validated with Pydantic.
4. Tool outputs can be returned to the model for a final synthesis.
"""

import json
import os
import re
import sys
from typing import Any, Dict, List
from pydantic import BaseModel, Field
import ollama
from dotenv import load_dotenv

load_dotenv()

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3.5:4b")
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


def extract_tool_calls(message) -> List[Dict[str, Any]]:
    """Extract tool calls either from native Ollama tool_calls or parsed from message content."""
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

    # 2. Check message content for XML tags <tool_call>...</tool_call>
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

    # 3. Check if whole content is a JSON tool call
    try:
        data = json.loads(content.strip())
        if isinstance(data, dict) and "name" in data:
            tool_calls.append({
                "name": data["name"],
                "arguments": data.get("arguments", {}),
            })
            return tool_calls
    except Exception:
        pass

    return tool_calls


def run_smoke_test(model_name: str = OLLAMA_MODEL) -> bool:
    print(f"=== CodePilot Tool-Calling Smoke Test ===")
    print(f"Ollama URL : {OLLAMA_BASE_URL}")
    print(f"Model      : {model_name}")
    print(f"Workspace  : {WORKSPACE_ROOT}")
    print("------------------------------------------")

    client = ollama.Client(host=OLLAMA_BASE_URL)

    # 1. Check connection
    try:
        models_response = client.list()
        available_models = [m.model for m in models_response.models]
        print(f"[OK] Connected to Ollama. Models present: {available_models}")

        model_found = any(model_name in m or m.startswith(model_name.split(":")[0]) for m in available_models)
        if not model_found:
            print(f"[WARN] Requested model '{model_name}' not yet listed in Ollama. Available: {available_models}")
    except Exception as e:
        print(f"[FAIL] Could not connect to Ollama: {e}")
        return False

    # Ensure workspace exists with a sample file
    os.makedirs(WORKSPACE_ROOT, exist_ok=True)
    sample_file = os.path.join(WORKSPACE_ROOT, "hello_world.py")
    if not os.path.exists(sample_file):
        with open(sample_file, "w") as f:
            f.write("# Hello from CodePilot workspace\nprint('Hello, world!')\n")

    # 2. Send prompt with tool
    messages = [
        {
            "role": "system",
            "content": "You are a coding assistant with access to tools. Always call list_files when asked to inspect files in the workspace.",
        },
        {
            "role": "user",
            "content": "Please inspect the workspace directory and list the files in it.",
        },
    ]

    print("\nSending user request with tool definitions...")
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

    print(f"[OK] Model returned {len(tool_calls)} tool call(s):")
    for tc in tool_calls:
        fn_name = tc["name"]
        fn_args = tc["arguments"]
        print(f"     Tool: {fn_name}, Arguments: {fn_args}")

        # 3. Validate with Pydantic
        if fn_name != "list_files":
            print(f"[FAIL] Unexpected tool name: {fn_name}")
            return False

        try:
            validated_args = ListFilesArgs(**(fn_args or {}))
            print(f"[OK] Pydantic validation passed: {validated_args}")
        except Exception as e:
            print(f"[FAIL] Pydantic validation failed: {e}")
            return False

    # 4. Execute tool
    items = os.listdir(WORKSPACE_ROOT)
    tool_result = {"ok": True, "files": items}
    print(f"[OK] Executed list_files tool -> result: {tool_result}")

    # 5. Append assistant tool call and tool result to messages
    if getattr(response.message, "tool_calls", None):
        messages.append(response.message)
        messages.append({
            "role": "tool",
            "content": json.dumps(tool_result),
        })
    else:
        # If model emitted tool call as text content, normalize for follow-up
        messages.append({
            "role": "assistant",
            "content": response.message.content,
        })
        messages.append({
            "role": "user",
            "content": f"Tool 'list_files' returned: {json.dumps(tool_result)}. Now answer the user's initial request.",
        })

    # 6. Ask model for final response
    print("\nSending tool result back to model for final synthesis...")
    try:
        final_response = client.chat(
            model=model_name,
            messages=messages,
        )
        print("\n[OK] Final response received from model:")
        print(f"     {final_response.message.content}")
    except Exception as e:
        print(f"[FAIL] Final chat completion failed: {e}")
        return False

    print(f"\n=== Smoke Test Passed Successfully for {model_name}! ===")
    return True


if __name__ == "__main__":
    model = sys.argv[1] if len(sys.argv) > 1 else OLLAMA_MODEL
    success = run_smoke_test(model)
    sys.exit(0 if success else 1)
