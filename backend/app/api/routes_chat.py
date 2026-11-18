"""Chat and agent orchestration API routes."""

import json
import os
import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import ollama
from backend.app.config import settings
from backend.app.smoke_test import extract_tool_calls, list_files_tool

router = APIRouter(prefix="/api", tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(..., description="The user's coding prompt or question")
    model: Optional[str] = Field(default=None, description="Optional model override")


class ToolStep(BaseModel):
    tool: str
    args: Any = None
    status: str
    summary: str
    result: Any = None


class ChatResponse(BaseModel):
    run_id: str
    status: str
    response: str
    steps: List[ToolStep] = []


@router.post("/chat", response_model=ChatResponse)
def handle_chat(payload: ChatRequest):
    model_name = payload.model or settings.ollama_model
    client = ollama.Client(host=settings.ollama_base_url)

    # Read canonical system prompt if present
    system_prompt = (
        "You are CodePilot, a software engineering assistant running locally. "
        "Inspect the workspace before proposing edits, and use tools to inspect or edit files."
    )
    prompt_path = os.path.join(os.getcwd(), "prompts", "SYSTEM_PROMPT.md")
    if os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            system_prompt = f.read()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": payload.message},
    ]

    steps: List[ToolStep] = []
    run_id = str(uuid.uuid4())

    try:
        # Step 1: Query model with available tools
        res = client.chat(
            model=model_name,
            messages=messages,
            tools=[list_files_tool],
            options={
                "num_ctx": settings.ollama_context_length,
                "temperature": settings.ollama_temperature,
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ollama chat error: {str(e)}")

    tool_calls = extract_tool_calls(res.message)

    # If the model requested a tool
    if tool_calls:
        for tc in tool_calls:
            tool_name = tc.get("name")
            tool_args = tc.get("arguments", {})

            if tool_name == "list_files":
                workspace_path = settings.resolved_workspace_root
                try:
                    files = os.listdir(workspace_path)
                    result_data = {"ok": True, "files": files}
                    summary = f"Listed {len(files)} files in workspace root"
                except Exception as e:
                    result_data = {"ok": False, "error": str(e)}
                    summary = f"Error listing workspace: {e}"

                steps.append(ToolStep(
                    tool=tool_name,
                    args=tool_args,
                    status="completed",
                    summary=summary,
                    result=result_data,
                ))

                # Append to messages and ask for synthesis
                messages.append(res.message)
                messages.append({
                    "role": "tool",
                    "content": json.dumps(result_data),
                })
            else:
                steps.append(ToolStep(
                    tool=tool_name,
                    args=tool_args,
                    status="completed",
                    summary=f"Tool executed: {tool_name}",
                    result={"ok": True},
                ))

        # Ask model for final response after tool execution
        try:
            final_res = client.chat(
                model=model_name,
                messages=messages,
            )
            final_content = final_res.message.content or "Task completed."
        except Exception as e:
            final_content = f"Tool executed, but synthesis failed: {e}"
    else:
        final_content = res.message.content or "No response from model."

    return ChatResponse(
        run_id=run_id,
        status="completed",
        response=final_content,
        steps=steps,
    )
