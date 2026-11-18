from types import SimpleNamespace

import pytest

from backend.app.agent import loop
from backend.app.config import settings


def native_call(name, arguments):
    return SimpleNamespace(
        message=SimpleNamespace(
            content="",
            tool_calls=[
                SimpleNamespace(
                    function=SimpleNamespace(name=name, arguments=arguments),
                ),
            ],
        ),
    )


def final_answer(content):
    return SimpleNamespace(message=SimpleNamespace(content=content, tool_calls=[]))


class FakeClient:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []

    def chat(self, **kwargs):
        self.calls.append(kwargs)
        return next(self.responses)


def test_agent_searches_then_answers_with_real_tool_result(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "workspace_root", str(tmp_path))
    (tmp_path / "module.py").write_text("answer = 42\n", encoding="utf-8")
    client = FakeClient([
        native_call("search_files", {"query": "answer"}),
        final_answer("The workspace defines `answer = 42`."),
    ])
    monkeypatch.setattr(loop.ollama, "Client", lambda **_: client)

    answer, steps, active_workspace = loop.run_agent_turn("Find the answer")

    assert answer == "The workspace defines `answer = 42`."
    assert active_workspace == str(tmp_path)
    assert steps[0]["tool"] == "search_files"
    assert steps[0]["result"]["matches"][0]["path"] == "module.py"
    assert client.calls[0]["keep_alive"] == settings.ollama_keep_alive
    assert "write_file" not in {tool["function"]["name"] for tool in client.calls[0]["tools"]}


def test_agent_only_writes_when_user_enables_edits(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "workspace_root", str(tmp_path))
    client = FakeClient([
        native_call("write_file", {"path": "new.py", "content": "print('ok')\n"}),
        final_answer("I could not edit the file because edits were disabled."),
    ])
    monkeypatch.setattr(loop.ollama, "Client", lambda **_: client)

    _, steps, _ = loop.run_agent_turn("Create new.py", allow_edits=False)

    assert steps[0]["status"] == "failed"
    assert "disabled" in steps[0]["result"]["error"]
    assert not (tmp_path / "new.py").exists()
    assert "write_file" not in {tool["function"]["name"] for tool in client.calls[0]["tools"]}


def test_agent_writes_only_inside_workspace_when_enabled(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "workspace_root", str(tmp_path))
    client = FakeClient([
        native_call("write_file", {"path": "src/new.py", "content": "print('ok')\n"}),
        final_answer("Created `src/new.py`."),
    ])
    monkeypatch.setattr(loop.ollama, "Client", lambda **_: client)

    answer, steps, _ = loop.run_agent_turn("Create src/new.py", allow_edits=True)

    assert answer == "Created `src/new.py`."
    assert steps[0]["status"] == "completed"
    assert (tmp_path / "src/new.py").read_text(encoding="utf-8") == "print('ok')\n"
    assert "write_file" in {tool["function"]["name"] for tool in client.calls[0]["tools"]}


def test_agent_accepts_model_absolute_path_inside_selected_workspace(tmp_path):
    desktop = tmp_path / "Desktop"
    target = desktop / "test_calc" / "calculator.py"
    desktop.mkdir()

    result, summary = loop._execute_tool(
        "write_file",
        {"path": str(target), "content": "class Calculator:\n    pass\n"},
        str(desktop),
        allow_edits=True,
        allow_test_execution=False,
    )

    assert result["ok"] is True
    assert target.read_text(encoding="utf-8") == "class Calculator:\n    pass\n"
    assert summary == "Wrote calculator.py"


def test_failed_write_trace_does_not_claim_success(tmp_path):
    result, summary = loop._execute_tool(
        "write_file",
        {"path": "../outside.py", "content": "print('no')"},
        str(tmp_path / "workspace"),
        allow_edits=True,
        allow_test_execution=False,
    )

    assert result["ok"] is False
    assert "outside the workspace" in summary


def test_agent_rejects_workspace_outside_configured_root(monkeypatch, tmp_path):
    workspace = tmp_path / "workspace"
    outside = tmp_path / "outside"
    workspace.mkdir()
    outside.mkdir()
    monkeypatch.setattr(settings, "workspace_root", str(workspace))

    with pytest.raises(ValueError, match="outside the workspace"):
        loop.run_agent_turn("Inspect files", workspace=str(outside))


def test_agent_accepts_explicit_home_directory_only_when_cli_authorizes_it(monkeypatch, tmp_path):
    home = tmp_path / "home"
    desktop = home / "Desktop"
    outside = tmp_path / "outside"
    desktop.mkdir(parents=True)
    outside.mkdir()
    monkeypatch.setattr(settings, "workspace_root", str(tmp_path / "default"))
    monkeypatch.setattr(loop.Path, "home", lambda: home)

    assert loop._resolve_active_workspace(str(desktop), allow_external_workspace=True) == str(desktop)
    with pytest.raises(ValueError, match="inside your home directory"):
        loop._resolve_active_workspace(str(outside), allow_external_workspace=True)


def test_test_runner_is_explicit_and_never_uses_a_shell(monkeypatch, tmp_path):
    (tmp_path / "tests").mkdir()
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return SimpleNamespace(returncode=0, stdout="2 passed\n", stderr="")

    monkeypatch.setattr(loop.subprocess, "run", fake_run)

    denied, _ = loop._execute_tool(
        "run_tests",
        {"target": "tests"},
        str(tmp_path),
        allow_edits=False,
        allow_test_execution=False,
    )
    assert denied["ok"] is False
    assert not calls

    result, summary = loop._execute_tool(
        "run_tests",
        {"target": "tests"},
        str(tmp_path),
        allow_edits=False,
        allow_test_execution=True,
    )

    command, options = calls[0]
    assert command[1:] == ["-m", "pytest", "tests", "-q"]
    assert options["cwd"] == str(tmp_path)
    assert options["capture_output"] is True
    assert "shell" not in options
    assert result["ok"] is True
    assert "2 passed" in result["output"]
    assert summary == "Pytest passed"


def test_test_runner_rejects_path_escape(monkeypatch, tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()

    result, _ = loop._execute_tool(
        "run_tests",
        {"target": "../outside"},
        str(workspace),
        allow_edits=False,
        allow_test_execution=True,
    )

    assert result["ok"] is False
    assert "outside the workspace" in result["error"]


def test_test_runner_executes_pytest_in_the_workspace(tmp_path):
    (tmp_path / "test_example.py").write_text(
        "def test_example():\n    assert 2 + 2 == 4\n",
        encoding="utf-8",
    )

    result, summary = loop._execute_tool(
        "run_tests",
        {"target": "test_example.py"},
        str(tmp_path),
        allow_edits=False,
        allow_test_execution=True,
    )

    assert result["ok"] is True
    assert "1 passed" in result["output"]
    assert summary == "Pytest passed"
