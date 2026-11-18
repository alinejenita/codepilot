from fastapi.testclient import TestClient

from backend.app.config import settings
from backend.app.main import app
from backend.app.api import routes_chat


def test_workspace_api_lists_and_previews_real_files(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "workspace_root", str(tmp_path))
    (tmp_path / "hello.py").write_text("print('hello')\n", encoding="utf-8")
    client = TestClient(app)

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
    client = TestClient(app)

    response = client.post("/api/chat", json={
        "message": "Read private files",
        "workspace": str(outside),
    })

    assert response.status_code == 400
    assert "outside the workspace" in response.json()["detail"]


def test_chat_passes_explicit_permissions_to_agent(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "workspace_root", str(tmp_path))
    received = {}

    def fake_agent_turn(**kwargs):
        received.update(kwargs)
        return "Done.", [], str(tmp_path)

    monkeypatch.setattr(routes_chat, "run_agent_turn", fake_agent_turn)
    client = TestClient(app)
    response = client.post("/api/chat", json={
        "message": "Make and test a change",
        "allow_edits": True,
        "allow_test_execution": True,
    })

    assert response.status_code == 200
    assert received["allow_edits"] is True
    assert received["allow_test_execution"] is True
