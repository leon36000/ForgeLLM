# Codex and Claude Code Setup for ForgeLLM

## One canonical contract

`AGENTS.md` is the cross-agent root contract. Keep it compact and stable. More specific nested `AGENTS.md` files may be added later for runtime, CUDA, HIP, CPU, benchmarks or infrastructure and take precedence only in their subtree.

`CLAUDE.md` imports `@AGENTS.md`, so Claude Code receives the same root rules rather than a divergent duplicate. `.claude/rules/` adds path- or concern-specific research, testing and security constraints. GitHub Copilot receives the repository summary from `.github/copilot-instructions.md`.

## Codex startup

Provide Codex the repository and one validated task packet, then use `docs/agents/MASTER_AGENT_PROMPT.md`. Require it to:

1. identify the effective `AGENTS.md` scope;
2. run `make validate` before changes;
3. work in one branch/worktree;
4. show test failures before implementation where feasible;
5. update state and handoff records;
6. report only commands it actually executed.

Do not give Codex broad repository-admin credentials for an implementation task. Repository settings, secrets, runners and releases are separate owner-authorized tasks.

## Claude Code startup

Launch Claude Code at the repository root, verify that `CLAUDE.md` and imported `AGENTS.md` are visible, and assign one task packet. Use the same master prompt. Claude-specific durable notes belong in repository files, not in an untracked local memory file that other agents cannot inspect.

## Context budget rule

Agents should load the smallest sufficient context:

- root contract and project state always;
- active task packet always;
- relevant ADRs and claims;
- only the source files needed for the task;
- raw benchmark artifacts only when verifying that experiment.

Long transcripts are not project memory. Summarize verified outcomes into state, ADR, claim, experiment and handoff files.

## Role separation

For material changes, use distinct contexts or agents:

- implementer;
- correctness reviewer;
- performance/reproducibility reviewer;
- security/license reviewer when applicable.

The verifier starts from the task packet and diff, not from the implementer’s reasoning. It reruns commands independently and may reject completion.

## GitHub connector and CLI boundaries

Use structured GitHub tools for issue, pull-request and repository metadata. Use local `git` for worktrees, diffs and commits. Use `gh` for Actions logs and repository settings only when the task authorizes those actions. Read-only audit commands should precede writes.

## Required closeout

Every agent writes a completion report using `docs/agents/REVIEWER_PROMPT.md` and updates `docs/state/HANDOFF.md`. A future clean agent must be able to continue without access to the previous conversation.
