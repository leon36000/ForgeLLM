# Contributing to ForgeLLM

ForgeLLM currently operates as a private research and engineering project. Contributions must be traceable to an issue or task packet.

## Workflow

1. Read `AGENTS.md` and the project charter.
2. Create one branch and preferably one worktree per task.
3. Run `make validate` before editing.
4. Write an executable oracle or failing test first where feasible.
5. Keep the change within the issue acceptance criteria.
6. Run `make ci` and all task-specific checks.
7. Open a pull request using the repository template.
8. Obtain independent review before merge.

## Commit policy

Use focused commits with imperative messages, for example:

- `feat(runtime): add versioned backend descriptor`
- `test(kv): add copy-on-write property cases`
- `docs(research): record FlashAttention-3 review`

Do not combine formatting, dependency updates and behavioral changes in one commit.

## Research and benchmark contributions

Research records require immutable source identifiers and scoped claims. Benchmark changes require raw data, environment manifests, correctness results and the machine-readable schema. External performance numbers remain unreproduced until a reviewed ForgeLLM experiment validates them.

## Generated or AI-assisted work

AI assistance does not remove contributor responsibility. The pull-request author must review every change, identify material generated code where required by policy, verify licenses and provide test evidence. Do not merge code that no reviewer can explain.
