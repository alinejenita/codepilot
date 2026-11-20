from fastapi.testclient import TestClient
from pydantic import SecretStr

from backend.app.config import Settings, settings
from backend.app.main import app
from backend.app.api import routes_chat


def authenticated_client(monkeypatch):
    monkeypatch.setattr(settings, "login_username", "demo-user")
    monkeypatch.setattr(settings, "login_password", SecretStr("demo-password"))
    monkeypatch.setattr(settings, "session_secret", SecretStr("s" * 32))
    monkeypatch.setattr(settings, "cookie_secure", False)
    client = TestClient(app)
    response = client.post("/api/auth/login", json={
        "username": "demo-user",
        "password": "demo-password",
    })
    assert response.status_code == 200
    return client


def test_api_requires_login_and_rejects_invalid_credentials(monkeypatch):
    monkeypatch.setattr(settings, "login_username", "demo-user")
    monkeypatch.setattr(settings, "login_password", SecretStr("demo-password"))
    monkeypatch.setattr(settings, "session_secret", SecretStr("s" * 32))
    client = TestClient(app)

    assert client.get("/api/workspace").status_code == 401
    assert client.post("/api/auth/login", json={
        "username": "demo-user",
        "password": "wrong-password",
    }).status_code == 401

    login = client.post("/api/auth/login", json={
        "username": "demo-user",
        "password": "demo-password",
    })
    assert login.status_code == 200
    assert "httponly" in login.headers["set-cookie"].lower()
    assert client.get("/api/auth/status").json() == {
        "configured": True,
        "authenticated": True,
    }


def test_api_fails_closed_when_login_is_not_configured(monkeypatch):
    monkeypatch.setattr(settings, "login_username", "")
    monkeypatch.setattr(settings, "login_password", SecretStr(""))
    monkeypatch.setattr(settings, "session_secret", SecretStr(""))
    client = TestClient(app)

    assert client.get("/api/auth/status").json() == {
        "configured": False,
        "authenticated": False,
    }
    assert client.get("/api/workspace").status_code == 503


def test_login_can_be_configured_with_documented_environment_variables(monkeypatch):
    monkeypatch.setenv("CODEPILOT_LOGIN_USERNAME", "demo-user")
    monkeypatch.setenv("CODEPILOT_LOGIN_PASSWORD", "demo-password")
    monkeypatch.setenv("CODEPILOT_SESSION_SECRET", "s" * 32)
    monkeypatch.setenv("CODEPILOT_COOKIE_SECURE", "true")

    configured = Settings(_env_file=None)

    assert configured.login_configured is True
    assert configured.cookie_secure is True


def test_logout_invalidates_browser_session(monkeypatch):
    client = authenticated_client(monkeypatch)

    assert client.get("/api/auth/status").json()["authenticated"] is True
    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/api/auth/status").json()["authenticated"] is False
    assert client.get("/api/workspace").status_code == 401


def test_workspace_api_lists_and_previews_real_files(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "workspace_root", str(tmp_path))
    (tmp_path / "hello.py").write_text("print('hello')\n", encoding="utf-8")
    client = authenticated_client(monkeypatch)

    listing = client.get("/api/workspace")
    preview = client.get("/api/workspace/file", params={"path": "hello.py"})

    assert listing.status_code == 200
    assert listing.json()["files"] == ["hello.py"]
    assert preview.status_code == 200
    assert preview.json()["content"] == "print('hello')\n"


def test_chat_rejects_workspace_outside_configured_root(monkeypatch, tmp_path):
    workspace = tmp_path / "workspace"
    outside = tmp_path / "outside"
    workspace.mkdir()
    outside.mkdir()
    monkeypatch.setattr(settings, "workspace_root", str(workspace))
    client = authenticated_client(monkeypatch)

    response = client.post("/api/chat", json={
        "message": "Read private files",
        "workspace": str(outside),
    })

    assert response.status_code == 400
    assert "outside the workspace" in response.json()["detail"]


def test_chat_passes_explicit_permissions_to_agent(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "workspace_root", str(tmp_path))
    received = {}
    client = authenticated_client(monkeypatch)

    def fake_agent_turn(**kwargs):
        received.update(kwargs)
        return "Done.", [], str(tmp_path)

    monkeypatch.setattr(routes_chat, "run_agent_turn", fake_agent_turn)
    response = client.post("/api/chat", json={
        "message": "Make and test a change",
        "allow_edits": True,
        "allow_test_execution": True,
    })

    assert response.status_code == 200
    assert received["allow_edits"] is True
    assert received["allow_test_execution"] is True
