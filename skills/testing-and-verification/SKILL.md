---
name: testing-and-verification
description: Select and run focused tests, inspect failures, and report verification accurately. Use when the user requests tests or when changes need validation.
---

# Testing and verification

1. Find the project's existing test and build conventions before choosing a command.
2. Select the smallest test target that covers the changed behavior; broaden only if targeted results reveal a need.
3. Run tests only through an available, explicitly permitted test tool. Do not imply that tests ran if they did not.
4. Read the complete relevant failure details and distinguish test failures from setup or environment failures.
5. When tests fail, connect the failure to the changed behavior before editing; do not make unrelated fixes.
6. Report the exact command or target, pass/fail outcome, and any unverified areas.

Remember that tests may execute workspace code and configuration. Respect the user's test-execution permission.
