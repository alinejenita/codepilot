---
name: debugging
description: Diagnose a software bug or unexpected behavior using reproducible evidence, code tracing, and focused tests. Use when the user reports a failure, incorrect output, crash, or regression.
---

# Debugging

1. Capture the exact observed behavior, expected behavior, and a minimal failing input or reproduction.
2. Inspect the error output and trace the relevant code path from input to failure.
3. Distinguish observed facts from hypotheses. Check likely branches and state changes rather than assuming a familiar cause.
4. Identify the earliest point where actual behavior diverges from expected behavior; fix that root cause.
5. Add a regression test that fails before the fix and passes after it when practical.
6. Run the focused verification available for the workspace and report its real result.
7. If evidence is insufficient, explain the uncertainty and request the smallest missing diagnostic rather than making speculative changes.

Do not hide errors or convert a failure into a success-shaped response.
