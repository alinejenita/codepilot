"""Chat and agent orchestration API routes."""

import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from backend.app.agent.loop import run_agent_turn

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
    latency_ms: Optional[float] = None


class ChatResponse(BaseModel):
    run_id: str
    status: str
    response: str
    steps: List[ToolStep] = []


@router.post("/chat", response_model=ChatResponse)
def handle_chat(payload: ChatRequest):
    run_id = str(uuid.uuid4())

    try:
        response_text, steps_data = run_agent_turn(
            user_prompt=payload.message,
            model_name=payload.model,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent loop error: {str(e)}")

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
    )
