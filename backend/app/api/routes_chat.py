"""Chat and agent orchestration API routes."""

import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from backend.app.auth import require_authenticated_user
from backend.app.agent.loop import run_agent_turn
from backend.app.config import settings
from backend.app.tools.file_tools import list_files, read_file, safe_resolve_path

router = APIRouter(
    prefix="/api",
    tags=["chat"],
    dependencies=[Depends(require_authenticated_user)],
)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=12000, description="The user's coding prompt or question")
    model: Optional[str] = Field(default=None, description="Optional model override")
    history: List[Dict[str, str]] = Field(default_factory=list, description="Prior conversation messages")
    workspace: Optional[str] = Field(default=None, description="Workspace root or subdirectory")
    allow_edits: bool = Field(default=False, description="Allow file creation and replacement for this request")
    allow_test_execution: bool = Field(default=False, description="Allow pytest execution for this request")


class ToolStep(BaseModel):
    tool: str
    args: Any = None
    status: str
    summary: str
    result: Any = None
    latency_ms: Optional[float] = None


class ChatResponse(BaseModel):
    run_id: str
    status: str
    response: str
    steps: List[ToolStep] = Field(default_factory=list)
    workspace: Optional[str] = None


@router.get("/workspace")
def get_workspace():
    result = list_files(".", str(settings.resolved_workspace_root))
    if not result.get("ok"):
        raise HTTPException(status_code=500, detail=result["error"])
    return {
        "workspace": str(settings.resolved_workspace_root),
        "files": [
            item["name"] for item in result["files"]
            if item["type"] == "file"
        ],
    }


@router.get("/workspace/file")
def get_workspace_file(path: str):
    try:
        safe_resolve_path(path, str(settings.resolved_workspace_root))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    result = read_file(path, str(settings.resolved_workspace_root))
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/chat", response_model=ChatResponse)
def handle_chat(payload: ChatRequest):
    run_id = str(uuid.uuid4())

    try:
        response_text, steps_data, active_ws = run_agent_turn(
            user_prompt=payload.message,
            model_name=payload.model,
            history=payload.history,
            workspace=payload.workspace,
            allow_edits=payload.allow_edits,
            allow_test_execution=payload.allow_test_execution,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Local agent request failed: {exc}") from exc

    steps = [
        ToolStep(
            tool=s.get("tool", "unknown"),
            args=s.get("args"),
            status=s.get("status", "completed"),
            summary=s.get("summary", ""),
            result=s.get("result"),
            latency_ms=s.get("latency_ms"),
        )
        for s in steps_data
    ]

    return ChatResponse(
        run_id=run_id,
        status="completed",
        response=response_text,
        steps=steps,
        workspace=active_ws,
    )
