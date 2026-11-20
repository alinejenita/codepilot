from contextlib import nullcontext

from cli import main as cli_main
from cli.main import prompt_requests_file_edits, workspace_requested_by_prompt


def test_cli_picks_desktop_from_the_current_prompt(tmp_path):
    desktop = tmp_path / "Desktop"
    desktop.mkdir()

    assert workspace_requested_by_prompt(
        "Save the calculator in a folder on my Desktop.",
        home_directory=tmp_path,
    ) == desktop


def test_cli_accepts_a_directory_path_entered_as_a_follow_up(tmp_path):
    desktop = tmp_path / "Desktop"
    desktop.mkdir()

    assert workspace_requested_by_prompt(str(desktop), home_directory=tmp_path) == desktop


def test_cli_picks_an_explicit_prompt_directory_and_ignores_non_destinations(tmp_path):
    destination = tmp_path / "Documents"
    destination.mkdir()

    assert workspace_requested_by_prompt(
        f"Save the generated file in this directory {destination}",
        home_directory=tmp_path,
    ) == destination
    assert workspace_requested_by_prompt(
        "Explain how the Desktop application works.",
        home_directory=tmp_path,
    ) is None


def test_cli_selects_explicitly_named_workspace_to_explore(tmp_path):
    workspace = tmp_path / "Development" / "projects" / "final_archon_ai"
    workspace.mkdir(parents=True)

    assert workspace_requested_by_prompt(
        f"I want you to use {workspace} as the workspace and explore contents from it",
        home_directory=tmp_path,
    ) == workspace


def test_cli_does_not_select_a_parent_for_a_missing_workspace(tmp_path):
    missing_workspace = tmp_path / "Development" / "missing-project"

    assert workspace_requested_by_prompt(
        f"Use {missing_workspace} as the workspace and explore it",
        home_directory=tmp_path,
    ) is None


def test_cli_picks_existing_parent_for_a_new_absolute_destination(tmp_path):
    desktop = tmp_path / "Desktop"
    desktop.mkdir()
    destination_file = desktop / "test_calc" / "calculator.py"

    assert workspace_requested_by_prompt(
        f"Create a calculator and save it as {destination_file}",
        home_directory=tmp_path,
    ) == desktop


def test_cli_enables_edits_for_explicit_file_change_requests_only():
    assert prompt_requests_file_edits(
        "Create a Python calculator file and save it on my Desktop."
    )
    assert prompt_requests_file_edits("Fix the bug in this function.")
    assert not prompt_requests_file_edits("How would I create a Python file?")
    assert not prompt_requests_file_edits("Explain this file.")


def test_cli_sends_previous_turns_as_agent_history(monkeypatch):
    class FakeConsole:
        def __init__(self):
            self.inputs = iter([
                "What technologies are used for backend and frontend?",
                "You can go through yourself.",
                "/exit",
            ])

        def clear(self):
            pass

        def input(self, _prompt):
            return next(self.inputs)

        def print(self, *_args, **_kwargs):
            pass

        def status(self, *_args, **_kwargs):
            return nullcontext()

    class FakeOllamaClient:
        def __init__(self, **_kwargs):
            pass

        def list(self):
            return object()

    calls = []

    def fake_agent_turn(**kwargs):
        calls.append({**kwargs, "history": list(kwargs["history"])})
        return "I will inspect the project files.", [], kwargs["workspace"]

    monkeypatch.setattr(cli_main, "console", FakeConsole())
    monkeypatch.setattr(cli_main.ollama, "Client", FakeOllamaClient)
    monkeypatch.setattr(cli_main, "run_agent_turn", fake_agent_turn)

    cli_main.run_cli()

    assert calls[0]["history"] == []
    assert calls[1]["history"] == [
        {"role": "user", "content": "What technologies are used for backend and frontend?"},
        {"role": "assistant", "content": "I will inspect the project files."},
    ]


def test_cli_handles_interrupt_during_agent_turn(monkeypatch):
    class FakeConsole:
        def __init__(self):
            self.inputs = iter(["Create a file", "/exit"])
            self.messages = []

        def clear(self):
            pass

        def input(self, _prompt):
            return next(self.inputs)

        def print(self, message="", **_kwargs):
            self.messages.append(str(message))

        def status(self, *_args, **_kwargs):
            return nullcontext()

    class FakeOllamaClient:
        def __init__(self, **_kwargs):
            pass

        def list(self):
            return object()

    fake_console = FakeConsole()

    def interrupt_turn(**_kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(cli_main, "console", fake_console)
    monkeypatch.setattr(cli_main.ollama, "Client", FakeOllamaClient)
    monkeypatch.setattr(cli_main, "run_agent_turn", interrupt_turn)

    cli_main.run_cli()

    assert any("Turn interrupted" in message for message in fake_console.messages)
