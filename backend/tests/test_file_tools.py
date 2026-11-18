import os

import pytest

from backend.app.tools.file_tools import list_files, read_file, safe_resolve_path, search_files, write_file


def test_safe_resolve_rejects_traversal_and_external_symlinks(tmp_path):
    workspace = tmp_path / "workspace"
    outside = tmp_path / "outside"
    workspace.mkdir()
    outside.mkdir()
    (outside / "secret.txt").write_text("private", encoding="utf-8")
    (workspace / "escape").symlink_to(outside, target_is_directory=True)

    with pytest.raises(ValueError, match="outside the workspace"):
        safe_resolve_path("../outside/secret.txt", str(workspace))
    with pytest.raises(ValueError, match="outside the workspace"):
        safe_resolve_path("escape/secret.txt", str(workspace))

    assert read_file("escape/secret.txt", str(workspace))["ok"] is False
    assert list_files(".", str(workspace))["files"] == []


def test_read_search_and_list_workspace_content(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "main.py").write_text("def greet():\n    return 'hello'\n", encoding="utf-8")
    (workspace / ".venv").mkdir()

    listing = list_files(".", str(workspace))
    assert listing["ok"]
    assert [entry["name"] for entry in listing["files"]] == ["main.py"]

    read_result = read_file("main.py", str(workspace))
    assert read_result["ok"]
    assert "return 'hello'" in read_result["content"]

    search_result = search_files("HELLO", str(workspace))
    assert search_result["ok"]
    assert search_result["matches"] == [
        {"path": "main.py", "line": 2, "snippet": "    return 'hello'"},
    ]


def test_read_file_rejects_binary_and_reports_truncation(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "binary.dat").write_bytes(b"\xff\xfe")
    (workspace / "large.txt").write_text("0123456789", encoding="utf-8")

    assert "not valid UTF-8" in read_file("binary.dat", str(workspace))["error"]
    truncated = read_file("large.txt", str(workspace), max_bytes=4)
    assert truncated["ok"]
    assert truncated["truncated"]
    assert truncated["content"] == "0123"


def test_write_file_creates_atomically_and_requires_overwrite_permission(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    created = write_file("nested/new.py", "print('first')\n", str(workspace))
    assert created["ok"]
    assert created["overwritten"] is False
    assert (workspace / "nested/new.py").read_text(encoding="utf-8") == "print('first')\n"

    rejected = write_file("nested/new.py", "print('second')\n", str(workspace))
    assert rejected["ok"] is False
    assert (workspace / "nested/new.py").read_text(encoding="utf-8") == "print('first')\n"

    overwritten = write_file("nested/new.py", "print('second')\n", str(workspace), allow_overwrite=True)
    assert overwritten["ok"]
    assert overwritten["overwritten"] is True
    assert (workspace / "nested/new.py").read_text(encoding="utf-8") == "print('second')\n"


def test_write_file_cannot_escape_workspace(tmp_path):
    workspace = tmp_path / "workspace"
    outside_file = tmp_path / "outside.txt"
    workspace.mkdir()
    outside_file.write_text("unchanged", encoding="utf-8")

    result = write_file("../outside.txt", "modified", str(workspace), allow_overwrite=True)
    assert result["ok"] is False
    assert outside_file.read_text(encoding="utf-8") == "unchanged"


def test_search_bounds_number_of_scanned_files(monkeypatch, tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "a.txt").write_text("needle\n", encoding="utf-8")
    (workspace / "b.txt").write_text("needle\n", encoding="utf-8")
    monkeypatch.setattr("backend.app.tools.file_tools.MAX_SEARCH_FILES", 1)

    result = search_files("needle", str(workspace))

    assert result["ok"]
    assert result["files_scanned"] == 1
    assert result["truncated"] is True


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
def test_list_skips_symlink_escape(tmp_path):
    workspace = tmp_path / "workspace"
    outside = tmp_path / "outside"
    workspace.mkdir()
    outside.mkdir()
    (workspace / "escape").symlink_to(outside, target_is_directory=True)

    assert list_files(".", str(workspace))["files"] == []
