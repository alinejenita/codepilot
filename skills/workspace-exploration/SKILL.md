---
name: workspace-exploration
description: Inspect and understand an unfamiliar codebase before answering or changing it. Use for repository orientation, locating relevant files, tracing behavior, and finding existing conventions.
---

# Workspace exploration

Use this workflow when a task depends on understanding an existing project.

1. Use the active workspace provided by CodePilot; do not ask the user to list or paste files that the tools can inspect.
2. Start with `list_files` to understand the workspace layout. For large workspaces, narrow to likely directories.
3. Use `search_files` for relevant symbols, behavior, tests, and existing patterns. Read the actual source and nearby tests with `read_file` before drawing conclusions.
4. For questions about frameworks, technologies, or the backend/frontend stack, do not answer from `README.md` alone. After locating the project structure, inspect dependency manifests for each relevant app or service: for example `package.json`, `pyproject.toml`, `requirements.txt`, `Pipfile`, `Cargo.toml`, `go.mod`, or their equivalents. Check backend and frontend separately when both are asked about.
5. If a side has no dependency manifest, inspect its entry point, imports, and framework configuration to identify technologies from implementation evidence. Do not invent a stack or treat a technology mentioned only in documentation as confirmed usage.
6. In the answer, identify which files support each conclusion and distinguish declared dependencies from technologies verified in source/configuration. If the relevant files cannot be found or read, state that limitation instead of asking the user to enumerate files.
7. Trace the relevant call path and identify how inputs, permissions, and errors flow through the code.
8. Prefer existing helpers and conventions over introducing a parallel implementation.
9. Report only findings supported by tool results. If the available tools cannot inspect something, say so.

Do not modify files as part of exploration unless the user also asked for an implementation.
