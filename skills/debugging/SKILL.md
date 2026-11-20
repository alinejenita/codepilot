---
name: debugging
description: Diagnose crashes, regressions, incorrect output, and other unexpected software behavior from a concrete reproduction and code evidence. Use when the user reports a bug or failure.
---

# Debugging

## Workflow

1. Establish the exact observed result, expected result, affected scope, and available error output. Use the user's reproduction when possible; do not invent missing logs or conditions.
2. Inspect the failing area, its callers, relevant state transitions, and nearby tests. Trace the real execution path rather than stopping at the first plausible file.
3. State possible causes as hypotheses. Check them against code, tool output, and a minimal reproduction before changing anything.
4. Find the earliest point where actual behavior diverges from expected behavior and fix that cause, not just a downstream symptom.
5. Add a focused regression test that fails for the reported behavior and passes with the fix, when the available project setup permits.
6. Run the smallest relevant permitted verification. Preserve and report failures, timeouts, and environment/setup issues accurately.
7. If evidence does not isolate a cause, stop short of speculative edits. State what is known, what remains uncertain, and request the smallest missing diagnostic.

## Completion check

Report the reproduction or evidence inspected, root cause only when established, changes made, and exact verification outcome. Never turn an error into a success-shaped answer or claim a fix is verified when it is not.
