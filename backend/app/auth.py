"""Shared web-login authentication helpers."""

import base64
import binascii
import hashlib
import hmac
import json
import time

from fastapi import HTTPException, Request, Response

from backend.app.config import settings

SESSION_COOKIE = "codepilot_session"
SESSION_DURATION_SECONDS = 8 * 60 * 60


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def verify_credentials(username: str, password: str) -> bool:
    if not settings.login_configured:
        return False

    username_matches = hmac.compare_digest(
        username.encode("utf-8"),
        settings.login_username.encode("utf-8"),
    )
    password_matches = hmac.compare_digest(
        password.encode("utf-8"),
        settings.login_password.get_secret_value().encode("utf-8"),
    )
    return username_matches & password_matches


def set_session_cookie(response: Response, username: str) -> None:
    expires_at = int(time.time()) + SESSION_DURATION_SECONDS
    payload = _encode(json.dumps(
        {"username": username, "expires_at": expires_at},
        separators=(",", ":"),
    ).encode("utf-8"))
    signature = hmac.new(
        settings.session_secret.get_secret_value().encode("utf-8"),
        payload.encode("ascii"),
        hashlib.sha256,
    ).digest()
    response.set_cookie(
        key=SESSION_COOKIE,
        value=f"{payload}.{_encode(signature)}",
        max_age=SESSION_DURATION_SECONDS,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=SESSION_COOKIE,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
        path="/",
    )


def is_authenticated(request: Request) -> bool:
    if not settings.login_configured:
        return False

    token = request.cookies.get(SESSION_COOKIE, "")
    if not token or len(token) > 2048:
        return False

    try:
        payload_part, signature_part = token.split(".", 1)
        provided_signature = _decode(signature_part)
        expected_signature = hmac.new(
            settings.session_secret.get_secret_value().encode("utf-8"),
            payload_part.encode("ascii"),
            hashlib.sha256,
        ).digest()
        if not hmac.compare_digest(provided_signature, expected_signature):
            return False

        payload = json.loads(_decode(payload_part))
        return (
            payload.get("username") == settings.login_username
            and isinstance(payload.get("expires_at"), int)
            and payload["expires_at"] > int(time.time())
        )
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError, binascii.Error):
        return False


def require_authenticated_user(request: Request) -> None:
    if not settings.login_configured:
        raise HTTPException(
            status_code=503,
            detail="CodePilot login is not configured on the server.",
        )
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Authentication required.")
