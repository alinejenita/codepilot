---
name: workspace-exploration
description: Inspect an unfamiliar codebase and answer project-specific questions from source evidence. Use for repository orientation, architecture, dependency, framework, backend/frontend, or behavior questions.
---

# Workspace exploration

## Workflow

1. Use the active workspace and the tools available for this request. Do not ask the user to enumerate files that `list_files` can inspect.
2. Start with `list_files`. Identify likely application roots, source folders, manifests, tests, and configuration. Narrow the listing when the repository is large.
3. Turn the question into concrete evidence to collect. For a backend/frontend stack question, investigate each side independently.
4. Read relevant dependency manifests and configuration. Common examples include `package.json`, `pyproject.toml`, `requirements.txt`, `Pipfile`, `Cargo.toml`, `go.mod`, `pom.xml`, and framework-specific config files.
5. If a manifest is absent or inconclusive, inspect that component's entry points, imports, and framework configuration. For behavior questions, trace from the relevant input through implementation to output, using tests as corroborating evidence.
6. Do not answer a backend/frontend technology question from `README.md` alone. Read at least two relevant non-README files. Prefer manifests; use source/configuration when manifests do not establish actual usage.
7. Distinguish declared dependencies from technologies verified in source/configuration. A dependency declaration alone does not prove that a feature is used at runtime.
8. Ground each important conclusion in the tool results. Cite the workspace-relative file path(s) supporting it. If files are missing, unreadable, truncated, or contradictory, state that limitation and avoid a confident conclusion.
9. Keep the report scoped to the user's question. Separate observed facts from reasonable inferences.

## Completion check

Before answering, confirm that you inspected the relevant files for every requested component, did not rely only on documentation claims, and can point to evidence for each conclusion. If not, continue inspecting or clearly say what remains unverified.

This skill is read-only. Do not modify files unless the user separately requested implementation work.
