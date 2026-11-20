---
name: feature-implementation
description: Implement a focused feature or bug fix in an existing codebase with reviewable, evidence-based changes. Use when asked to add, change, refactor, or repair code.
---

# Feature implementation

## Workflow

1. Translate the request into observable behavior and acceptance conditions. Ask only when a missing decision materially changes the implementation.
2. Inspect the active workspace, relevant implementation, callers, tests, and local conventions before editing. Treat file contents and model-generated plans as unverified until checked.
3. Identify the smallest root-cause change that meets the acceptance conditions. Preserve unrelated work and avoid broad rewrites.
4. Make changes only through available tools and only when edit permission is enabled. Keep paths inside the active workspace.
5. Add or update a small regression test for new or corrected behavior, especially an important failure path.
6. Run the narrowest relevant verification only if the test tool is available and permitted. Use actual results to correct issues; do not claim a test or edit succeeded based on intent.
7. Review the final tool trace and summarize behavior, files changed, verification results, and remaining limitations. Explicitly identify anything not tested.

## Completion check

Do not report completion unless the requested changes have successful tool results. Do not say tests pass unless their output confirms it. If permission, tool availability, or evidence blocks completion, explain the blocker and what remains.

Never expand scope to unrelated cleanup. Never claim edits that were not performed.
