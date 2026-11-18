---
name: feature-implementation
description: Plan and implement a focused software feature or bug fix in an existing codebase. Use when the user asks to add, change, refactor, or repair code.
---

# Feature implementation

1. Restate the observable behavior the user wants and note any essential ambiguity.
2. Inspect relevant implementation, callers, tests, and project conventions before editing.
3. Make the smallest complete change at the source of the behavior. Preserve unrelated work and existing behavior.
4. Add or update focused tests for the requested behavior, including important failure cases.
5. Use `write_file` only when it is available and the user has authorized edits. Do not claim to have edited files when permission is absent or a tool fails.
6. If test execution is available, run the narrowest relevant tests. Otherwise state what still needs verification.
7. Summarize changed files, behavior, verification results, and remaining limitations.

Never infer success from a model-generated plan; rely on the actual tool results.
