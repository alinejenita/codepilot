"""Login and session status routes."""

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field

from backend.app.auth import (
    clear_session_cookie,
    is_authenticated,
    set_session_cookie,
    verify_credentials,
)
from backend.app.config import settings

router = APIRouter(prefix="/api/auth", tags=["authentication"])


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=128)
    password: str = Field(..., min_length=1, max_length=256)


@router.get("/status")
def get_auth_status(request: Request, response: Response):
    response.headers["Cache-Control"] = "no-store"
    configured = settings.login_configured
    return {
        "configured": configured,
        "authenticated": configured and is_authenticated(request),
    }


@router.post("/login")
def login(payload: LoginRequest, response: Response):
    response.headers["Cache-Control"] = "no-store"
    if not settings.login_configured:
        raise HTTPException(
            status_code=503,
            detail="CodePilot login is not configured on the server.",
        )
    if not verify_credentials(payload.username, payload.password):
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    set_session_cookie(response, payload.username)
    return {"authenticated": True}


@router.post("/logout")
def logout(response: Response):
    response.headers["Cache-Control"] = "no-store"
    clear_session_cookie(response)
    return {"authenticated": False}
