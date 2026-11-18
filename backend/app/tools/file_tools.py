"""Safe file inspection and editing tools for CodePilot."""

import os
from typing import Dict, Any, List


def safe_resolve_path(target_path: str, base_dir: str) -> str:
    """Resolve target path. If target_path is absolute and exists, allow it, else resolve relative to base_dir."""
    if os.path.isabs(target_path):
        resolved = os.path.abspath(target_path)
    else:
        resolved = os.path.abspath(os.path.join(base_dir, target_path))
    return resolved


def list_files(directory: str = ".", workspace_root: str = "./workspace") -> Dict[str, Any]:
    """List files in the directory, filtering out git and cache directories."""
    resolved_dir = safe_resolve_path(directory, workspace_root)

    if not os.path.exists(resolved_dir):
        return {"ok": False, "error": f"Directory not found: {directory}"}

    if not os.path.isdir(resolved_dir):
        return {"ok": False, "error": f"Path is not a directory: {directory}"}

    entries = []
    ignored = {".git", ".venv", "node_modules", "__pycache__", ".pytest_cache", ".cache", "dist"}

    try:
        for item in sorted(os.listdir(resolved_dir)):
            if item in ignored:
                continue
            item_path = os.path.join(resolved_dir, item)
            is_dir = os.path.isdir(item_path)
            entries.append({
                "name": item,
                "type": "directory" if is_dir else "file",
                "size": os.path.getsize(item_path) if not is_dir else None,
            })
        return {
            "ok": True,
            "directory": resolved_dir,
            "count": len(entries),
            "files": entries[:40],  # Bound to 40 items to avoid context overflow
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def read_file(path: str, workspace_root: str = "./workspace", max_bytes: int = 15000) -> Dict[str, Any]:
    """Read a text file with a safety size limit."""
    resolved_path = safe_resolve_path(path, workspace_root)

    if not os.path.exists(resolved_path):
        return {"ok": False, "error": f"File does not exist: {path}"}

    if not os.path.isfile(resolved_path):
        return {"ok": False, "error": f"Path is not a file: {path}"}

    try:
        file_size = os.path.getsize(resolved_path)
        with open(resolved_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read(max_bytes)

        is_truncated = file_size > max_bytes
        return {
            "ok": True,
            "path": resolved_path,
            "size": file_size,
            "truncated": is_truncated,
            "content": content,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}
