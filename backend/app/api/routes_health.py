"""Health and system status endpoint."""

from fastapi import APIRouter, Depends
import ollama
from backend.app.auth import require_authenticated_user
from backend.app.config import settings

router = APIRouter(
    prefix="/api",
    tags=["system"],
    dependencies=[Depends(require_authenticated_user)],
)


@router.get("/health")
def get_health():
    ollama_connected = False
    available_models = []

    try:
        client = ollama.Client(
            host=settings.ollama_base_url,
            timeout=settings.ollama_request_timeout_seconds,
        )
        res = client.list()
        available_models = [m.model for m in res.models]
        ollama_connected = True
    except Exception:
        ollama_connected = False

    return {
        "status": "ok",
        "ollama_connected": ollama_connected,
        "model": settings.ollama_model,
        "available_models": available_models,
        "workspace": settings.workspace_root,
    }
