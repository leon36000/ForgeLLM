# Contributing to ForgeLLM

ForgeLLM is a publicly visible research and engineering project. It is not yet distributed under an open-source license. Public visibility does not grant permission to reuse or redistribute the repository.

Issue discussion and primary-source corrections are welcome. Code pull requests require an owner-linked issue or task packet and explicit handling of inbound licensing until a project license and contributor policy are accepted.

## Public-data rule

Do not submit credentials, restricted model files, private datasets/prompts, customer data, hostnames, private IP addresses, full hardware UUIDs or unredacted traces. Assume every contribution and CI log is permanent and public.

## Workflow

1. Read `AGENTS.md`, the project charter and ADR-0003.
2. Obtain or create one bounded issue/task packet.
3. Create one branch and preferably one worktree per task.
4. Run `make validate` before editing.
5. Write an executable oracle or failing test first where feasible.
6. Keep the change within issue acceptance criteria.
7. Run `make ci` and all task-specific checks.
8. Open a pull request using the repository template.
9. Obtain fresh-context independent review before merge.

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
