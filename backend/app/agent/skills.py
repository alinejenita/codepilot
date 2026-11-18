"""Discovery and loading for CodePilot's bundled Agent Skills."""

import re
from dataclasses import dataclass
from pathlib import Path


SKILLS_ROOT = Path(__file__).resolve().parents[3] / "skills"
_SKILL_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass(frozen=True)
class AgentSkill:
    name: str
    description: str
    path: Path


def _read_skill(path: Path) -> tuple[str, str, str]:
    try:
        contents = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"Could not read skill file {path}: {exc}") from exc

    if not contents.startswith("---\n"):
        raise ValueError(f"Skill file must start with YAML frontmatter: {path}")
    _, frontmatter, body = contents.split("---", 2)
    metadata: dict[str, str] = {}
    for line in frontmatter.splitlines():
        if not line.strip():
            continue
        key, separator, value = line.partition(":")
        if not separator:
            raise ValueError(f"Invalid skill metadata in {path}: {line}")
        metadata[key.strip()] = value.strip().strip("\"'")

    name = metadata.get("name", "")
    description = metadata.get("description", "")
    if not _SKILL_NAME.fullmatch(name) or len(name) > 64:
        raise ValueError(f"Skill name must be lowercase kebab-case: {path}")
    if len(description) > 1024 or not description:
        raise ValueError(f"Skill description must contain 1-1024 characters: {path}")
    if name != path.parent.name:
        raise ValueError(f"Skill name must match its directory name: {path}")
    return name, description, body.strip()


def discover_skills() -> list[AgentSkill]:
    """Return the validated bundled skills in stable name order."""
    if not SKILLS_ROOT.is_dir():
        return []

    skills = []
    for directory in sorted(SKILLS_ROOT.iterdir()):
        skill_path = directory / "SKILL.md"
        if not directory.is_dir() or directory.is_symlink() or not skill_path.is_file():
            continue
        resolved_path = skill_path.resolve()
        try:
            resolved_path.relative_to(SKILLS_ROOT.resolve())
        except ValueError as exc:
            raise ValueError(f"Skill file resolves outside the bundled skills directory: {skill_path}") from exc
        name, description, _ = _read_skill(resolved_path)
        skills.append(AgentSkill(name=name, description=description, path=resolved_path))
    return skills


def load_skill(name: str) -> dict[str, str | bool]:
    """Load one bundled skill by its registered name, never by a model-supplied path."""
    skill = next((item for item in discover_skills() if item.name == name), None)
    if skill is None:
        return {"ok": False, "error": f"Unknown skill: {name}"}
    loaded_name, _, instructions = _read_skill(skill.path)
    return {"ok": True, "name": loaded_name, "instructions": instructions}


def relevant_skills(prompt: str) -> list[dict[str, str]]:
    """Return full instructions for skills that match common task signals."""
    normalized = prompt.casefold()
    skill_signals = {
        "workspace-exploration": (
            "workspace", "explore", "contents", "codebase", "repository", "project structure",
            "backend", "frontend", "technology", "technologies", "tech stack", "framework",
            "what software", "what kind of software",
        ),
        "feature-implementation": (
            "implement", "create", "add ", "change", "modify", "refactor", "fix",
        ),
        "debugging": ("bug", "error", "fails", "failing", "crash", "unexpected"),
        "testing-and-verification": ("test", "verify", "verification"),
    }
    matches = [
        skill_name
        for skill_name, signals in skill_signals.items()
        if any(signal in normalized for signal in signals)
    ]
    results = []
    for skill_name in matches:
        result = load_skill(skill_name)
        if result.get("ok"):
            results.append({
                "name": skill_name,
                "instructions": str(result["instructions"]),
            })
    return results
