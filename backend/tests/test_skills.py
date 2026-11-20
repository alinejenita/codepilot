import json
from types import SimpleNamespace

import pytest

from backend.app.agent import loop, skills
from backend.app.config import settings


def skill_file(root, name, description, instructions):
    directory = root / name
    directory.mkdir()
    path = directory / "SKILL.md"
    path.write_text(
        f"---\nname: {name}\ndescription: {description}\n---\n\n{instructions}\n",
        encoding="utf-8",
    )
    return path


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


def test_discovers_bundled_skills_in_name_order(monkeypatch, tmp_path):
    skill_file(tmp_path, "z-skill", "Last skill.", "Last instructions.")
    skill_file(tmp_path, "a-skill", "First skill.", "First instructions.")
    monkeypatch.setattr(skills, "SKILLS_ROOT", tmp_path)

    discovered = skills.discover_skills()

    assert [item.name for item in discovered] == ["a-skill", "z-skill"]
    assert discovered[0].description == "First skill."


def test_loader_returns_instructions_only_for_registered_skill(monkeypatch, tmp_path):
    skill_file(tmp_path, "debugging", "Debug code.", "Reproduce before fixing.")
    monkeypatch.setattr(skills, "SKILLS_ROOT", tmp_path)

    assert skills.load_skill("debugging") == {
        "ok": True,
        "name": "debugging",
        "instructions": "Reproduce before fixing.",
    }
    assert skills.load_skill("../outside") == {"ok": False, "error": "Unknown skill: ../outside"}


@pytest.mark.parametrize(
    ("directory", "metadata", "error"),
    [
        ("bad_name", "name: Bad_Name\ndescription: Description.", "lowercase kebab-case"),
        ("folder-name", "name: another-name\ndescription: Description.", "match its directory"),
        ("empty-description", "name: empty-description\ndescription:", "description must contain"),
    ],
)
def test_rejects_invalid_skill_metadata(monkeypatch, tmp_path, directory, metadata, error):
    skill_dir = tmp_path / directory
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(f"---\n{metadata}\n---\nInstructions.\n", encoding="utf-8")
    monkeypatch.setattr(skills, "SKILLS_ROOT", tmp_path)

    with pytest.raises(ValueError, match=error):
        skills.discover_skills()


def test_agent_loads_relevant_skill_before_answering(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "workspace_root", str(tmp_path))
    client = FakeClient([
        native_call("load_skill", {"name": "feature-implementation"}),
        final_answer("I will inspect the code, make a focused change, and verify it."),
    ])
    monkeypatch.setattr(loop.ollama, "Client", lambda **_: client)

    answer, steps, _ = loop.run_agent_turn("Implement a focused code feature")

    offered_tools = {tool["function"]["name"] for tool in client.calls[0]["tools"]}
    system_prompt = client.calls[0]["messages"][0]["content"]
    skill_result = json.loads(client.calls[1]["messages"][-1]["content"])

    assert "load_skill" in offered_tools
    assert "feature-implementation" in system_prompt
    assert steps[0]["tool"] == "load_skill"
    assert steps[0]["status"] == "completed"
    assert "relevant implementation, callers, tests" in skill_result["instructions"]
    assert answer.startswith("I will inspect")


def test_agent_auto_activates_exploration_skill_for_stack_questions(monkeypatch, tmp_path):
    skill_file(
        tmp_path,
        "workspace-exploration",
        "Inspect projects.",
        "Inspect manifests directly and do not ask users to enumerate files.",
    )
    monkeypatch.setattr(skills, "SKILLS_ROOT", tmp_path)

    instruction = loop._build_system_instruction(
        "/workspace/project",
        allow_edits=False,
        allow_test_execution=False,
        user_prompt="What technologies are used for backend and frontend?",
    )

    assert "Relevant skill instructions for this task" in instruction
    assert "Inspect manifests directly" in instruction
    assert "Do not ask the user to list files" in instruction


def test_exploration_skill_requires_backend_and_frontend_evidence():
    result = skills.load_skill("workspace-exploration")

    assert result["ok"] is True
    instructions = result["instructions"]
    assert "Do not answer a backend/frontend technology question from `README.md` alone." in instructions
    assert "Read relevant dependency manifests and configuration" in instructions
    assert "investigate each side independently" in instructions
    assert "inspect that component's entry points, imports, and framework configuration" in instructions
