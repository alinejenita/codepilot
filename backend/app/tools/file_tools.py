"""Workspace-confined file inspection and editing tools."""

import os
import tempfile
from pathlib import Path
from typing import Any


IGNORED_DIRECTORIES = {
    ".git",
    ".venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".cache",
    "dist",
    "build",
}
MAX_SEARCH_FILES = 1000
MAX_SEARCH_FILE_BYTES = 256_000
MAX_WRITE_BYTES = 1_000_000


def safe_resolve_path(target_path: str, base_dir: str) -> str:
    """Resolve a path and reject traversal or symlinks outside the workspace."""
    root = Path(base_dir).resolve()
    target = Path(target_path)
    resolved = (target if target.is_absolute() else root / target).resolve()

    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"Path is outside the workspace: {target_path}") from exc

    return str(resolved)


def list_files(directory: str = ".", workspace_root: str = "./workspace") -> dict[str, Any]:
    """List immediate children of a workspace directory."""
    try:
        resolved_dir = Path(safe_resolve_path(directory, workspace_root))
        if not resolved_dir.exists():
            return {"ok": False, "error": f"Directory not found: {directory}"}
        if not resolved_dir.is_dir():
            return {"ok": False, "error": f"Path is not a directory: {directory}"}

        entries = []
        for item in sorted(resolved_dir.iterdir(), key=lambda path: path.name.casefold()):
            if item.name in IGNORED_DIRECTORIES:
                continue
            try:
                resolved_item = Path(safe_resolve_path(str(item), workspace_root))
            except ValueError:
                continue
            is_dir = resolved_item.is_dir()
            entries.append({
                "name": item.name,
                "type": "directory" if is_dir else "file",
                "size": resolved_item.stat().st_size if not is_dir else None,
            })

        return {
            "ok": True,
            "directory": str(resolved_dir),
            "count": len(entries),
            "files": entries[:100],
        }
    except OSError as exc:
        return {"ok": False, "error": str(exc)}
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}


def read_file(path: str, workspace_root: str = "./workspace", max_bytes: int = 15000) -> dict[str, Any]:
    """Read a bounded UTF-8 text file inside the workspace."""
    try:
        resolved_path = Path(safe_resolve_path(path, workspace_root))
        if not resolved_path.exists():
            return {"ok": False, "error": f"File does not exist: {path}"}
        if not resolved_path.is_file():
            return {"ok": False, "error": f"Path is not a file: {path}"}

        file_size = resolved_path.stat().st_size
        with resolved_path.open("rb") as file:
            raw_content = file.read(max_bytes + 1)
        truncated = len(raw_content) > max_bytes
        content = raw_content[:max_bytes].decode("utf-8")
        return {
            "ok": True,
            "path": str(resolved_path),
            "size": file_size,
            "truncated": truncated,
            "content": content,
        }
    except UnicodeDecodeError:
        return {"ok": False, "error": f"File is not valid UTF-8 text: {path}"}
    except OSError as exc:
        return {"ok": False, "error": str(exc)}
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}


def search_files(
    query: str,
    workspace_root: str = "./workspace",
    directory: str = ".",
    max_results: int = 50,
) -> dict[str, Any]:
    """Search workspace text files for a case-insensitive substring."""
    if not query:
        return {"ok": False, "error": "Search query cannot be empty."}

    try:
        root = Path(workspace_root).resolve()
        search_root = Path(safe_resolve_path(directory, str(root)))
        if not search_root.exists() or not search_root.is_dir():
            return {"ok": False, "error": f"Directory not found: {directory}"}

        matches = []
        truncated = False
        files_scanned = 0
        for current_dir, directories, filenames in os.walk(search_root, followlinks=False):
            current_path = Path(current_dir)
            directories[:] = [
                name for name in directories
                if name not in IGNORED_DIRECTORIES
                and not (current_path / name).is_symlink()
            ]
            for filename in filenames:
                files_scanned += 1
                if files_scanned > MAX_SEARCH_FILES:
                    truncated = True
                    break
                candidate = current_path / filename
                try:
                    safe_path = Path(safe_resolve_path(str(candidate), str(root)))
                    if not safe_path.is_file() or safe_path.stat().st_size > MAX_SEARCH_FILE_BYTES:
                        continue
                    content = safe_path.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError, ValueError):
                    continue

                for line_number, line in enumerate(content.splitlines(), start=1):
                    if query.casefold() not in line.casefold():
                        continue
                    matches.append({
                        "path": safe_path.relative_to(root).as_posix(),
                        "line": line_number,
                        "snippet": line[:300],
                    })
                    if len(matches) >= max_results:
                        truncated = True
                        break
                if truncated:
                    break
            if truncated:
                break

        return {
            "ok": True,
            "query": query,
            "count": len(matches),
            "files_scanned": min(files_scanned, MAX_SEARCH_FILES),
            "truncated": truncated,
            "matches": matches,
        }
    except (OSError, ValueError) as exc:
        return {"ok": False, "error": str(exc)}


def write_file(
    path: str,
    content: str,
    workspace_root: str = "./workspace",
    allow_overwrite: bool = False,
) -> dict[str, Any]:
    """Atomically write a UTF-8 text file after the caller grants edit permission."""
    temporary_path = None
    try:
        if len(content.encode("utf-8")) > MAX_WRITE_BYTES:
            return {"ok": False, "error": f"File exceeds the {MAX_WRITE_BYTES}-byte write limit."}
        resolved_path = Path(safe_resolve_path(path, workspace_root))
        existed_before = resolved_path.exists()
        if existed_before and not allow_overwrite:
            return {
                "ok": False,
                "error": f"File already exists; enable file edits to replace it: {path}",
            }
        if resolved_path.exists() and not resolved_path.is_file():
            return {"ok": False, "error": f"Path is not a file: {path}"}

        resolved_path.parent.mkdir(parents=True, exist_ok=True)
        # Re-check after creating parents so a newly introduced symlink cannot escape the root.
        resolved_path = Path(safe_resolve_path(str(resolved_path), workspace_root))
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=resolved_path.parent,
            prefix=f".{resolved_path.name}.",
            delete=False,
        ) as temporary_file:
            temporary_path = temporary_file.name
            temporary_file.write(content)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())

        if allow_overwrite:
            os.replace(temporary_path, resolved_path)
        else:
            os.link(temporary_path, resolved_path)
            os.unlink(temporary_path)
        temporary_path = None
        return {
            "ok": True,
            "path": str(resolved_path),
            "bytes_written": len(content.encode("utf-8")),
            "overwritten": existed_before,
        }
    except (OSError, ValueError) as exc:
        return {"ok": False, "error": str(exc)}
    finally:
        if temporary_path and os.path.exists(temporary_path):
            os.unlink(temporary_path)
