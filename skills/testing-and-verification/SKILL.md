---
name: testing-and-verification
description: Choose and run focused project tests, interpret the actual output, and report verified behavior and gaps accurately. Use when asked to test or when code changes need validation.
---

# Testing and verification

## Workflow

1. Inspect project manifests, test configuration, and nearby tests to find the repository's existing test commands and conventions. Do not guess the runner from a filename alone.
2. Map each changed behavior to the smallest relevant test target. Broaden the run only when focused results indicate a wider regression risk.
3. Check that the test tool is available and that the user enabled execution. Tests can execute project code and configuration; never bypass the permission gate.
4. Run the selected target and inspect its actual output, including setup errors, skipped tests, timeouts, and failures.
5. If a failure occurs, classify it from evidence before proposing a code fix. Do not hide, rewrite, or infer a passing result.
6. Report what ran, the real outcome, and what was not covered or could not run. Distinguish a build, lint, or syntax check from a test suite.

## Completion check

Only claim that a check passed when its output confirms success. If no execution tool or permission is available, provide the suggested command as unrun and label verification as pending.
