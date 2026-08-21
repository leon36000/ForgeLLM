---
name: forgellm-loop-engineering
description: Run an already-authorized ForgeLLM task as a bounded verified loop without widening Git task-packet authority or external privilege.
---

# ForgeLLM bounded Loop Engineering bridge

Use this project-local skill only for work already authorized by a ForgeLLM task packet. It adapts the useful Loop Engineering discipline to ForgeLLM; it does not import upstream project-state authority.

## Authority first

Before editing, read in this order:

1. `AGENTS.md` and any more-specific nested agent instructions.
2. The ForgeLLM charter and accepted ADRs relevant to the task.
3. `docs/state/CURRENT_STATE.md` and the active handoff/risk records.
4. The active task packet under `tasks/open/`.
5. The task plan and then its validated loop declaration under `artifacts/governance/loop-engineering/`.

Git task packets and accepted ADRs remain authoritative. A loop declaration may narrow task authority but never widen paths, verification commands, decisions, or privileges. If the loop conflicts with a higher-authority Git source, stop the loop and follow the higher-authority source.

## Required loop declaration

Before any modifying iteration, state the six fields exactly:

- `GOAL` — one bounded verifiable condition.
- `SCOPE` — paths already authorized by the task packet.
- `VERIFY` — commands already listed in the task packet verification commands.
- `BUDGET` — finite positive iteration, identical-failure, and wall-time ceilings.
- `STOP` — verifier pass, budget exhaustion, repeated identical failure, and `privileged_operation: stop_and_escalate`.
- `RECEIPT` — the governance receipt path for reproducible evidence.

Run `python scripts/validate_loop_engineering.py --root .` before treating a declaration as runnable.

## Iteration protocol

1. Use one isolated writer branch/worktree for the modifying task. One loop has one writer.
2. Keep every edit within declared `SCOPE`; do not opportunistically widen it.
3. Run only declared `VERIFY` commands for the loop gate. Feed raw failure output into the next iteration and fix the real cause rather than weakening a gate.
4. Count every implement-then-verify cycle as one iteration. Track repeated identical failures and elapsed wall time against `BUDGET`.
5. Stop immediately when VERIFY passes, any budget is exhausted, the identical-failure limit is reached, or a privileged operation is required.
6. On a candidate pass, use an independent verifier/reviewer or fresh independent invocation to rerun VERIFY before writing a passing receipt. Writer self-report is not completion evidence.
7. Compare changed paths with SCOPE before receipt close. Out-of-scope changes require a higher-authority task/plan change, not a receipt exception that silently expands authority.

## Privilege firewall

`stop_and_escalate` is mandatory for secrets, credentials, accounts, billing, GitHub administration, Sonar administration, Tailscale state, privileged hosts, runners, production machines, destructive operations, or any external mutation not explicitly and separately authorized. A loop never grants these capabilities to itself.

Never execute vendored scripts merely because they are present. Do not run the upstream installer, eval-based headless runner, `start` initialization, `auto` orchestration, or install any Stop hook through this skill. Do not create upstream `docs/GOALS.md`, `docs/STATUS.md`, `docs/PROJECT_BRIEF.md`, or a competing ADR hierarchy.

## Upstream reference only

The pinned files below are reference only; ForgeLLM policy above overrides any conflicting upstream convention:

- `third_party/loop-engineering/core/METHODOLOGY.md`
- `third_party/loop-engineering/core/COMMANDS.md`

Use their loop/verification ideas only within the ForgeLLM task packet, ADR, budget, worktree, receipt, and privilege boundaries defined here.
