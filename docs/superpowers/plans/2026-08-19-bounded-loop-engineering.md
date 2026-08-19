# Bounded Loop Engineering Execution Plan

> **Task:** P0-T10 / issue #36 / PR #37  
> **Canonical base:** `8594ef5abb19ca7a870fe6d71ae7aad8e15f4602`  
> **Decision:** owner-approved design B — pinned vendored methodology plus ForgeLLM-specific bounded bridge  
> **ADR:** `ADR-0005-bounded-loop-engineering.md`, still `proposed` until independent exact-head review

## Goal

Operationalize Loop Engineering for ForgeLLM as a bounded orchestration discipline without creating a second source of truth, expanding task authority, or granting loops privilege over secrets/external administration.

## Non-negotiable architecture

ForgeLLM task packets and accepted ADRs remain authoritative. Vendored upstream material is reference/evidence only. A runnable loop must bind `GOAL`, `SCOPE`, `VERIFY`, `BUDGET`, `STOP`, and `RECEIPT` to one task packet and Git base revision. `SCOPE` and `VERIFY` may narrow but never widen task-packet authority.

The active P0-T10 budget is:

```yaml
BUDGET:
  max_iterations: 10
  max_identical_failures: 3
  max_wall_minutes: 60
STOP:
  on_verify_pass: true
  on_budget_exhausted: true
  on_identical_failure_limit: true
  privileged_operation: stop_and_escalate
```

No upstream `install.sh`, `start`, `auto`, eval-based runner, shell runner, Stop hook, `docs/GOALS.md`, `docs/STATUS.md`, project brief, or alternate ADR hierarchy may be introduced by P0-T10.

## Implemented stages

### Stage 1 — Governance foundation: complete

Delivered on `f6bf714df6090f4a7cc41818930dcc4d26b22b1a`:

- `tasks/open/P0-T10-bounded-loop-engineering.yaml`;
- proposed `docs/architecture/ADR-0005-bounded-loop-engineering.md`;
- this implementation plan.

The packet explicitly isolates P0-T10 from P0-T09 and forbids privilege widening, unbounded loops, floating upstream fetches, shadow project state, upstream executable integration, and direct `main` writes.

### Stage 2 — Static upstream snapshot: complete

Delivered on `7bdf3889e5730fc604eedb9ee5c08671a3832e6e` from exact upstream `lcajigasm/loop-engineering@ae2d610985064bb30c5013261988c813013c09e3`.

Vendored only:

- MIT `LICENSE`;
- `core/METHODOLOGY.md`;
- `core/COMMANDS.md`;
- PLAN, RECEIPT, INTEGRATION and CAPABILITIES templates.

`third_party/loop-engineering/PROVENANCE.yaml` binds every file to an upstream Git blob SHA. No `.sh`, installer, upstream agent adapter, GOALS/STATUS/project-brief/ADR template is present.

### Stage 3 — Core fail-closed contract: complete via TDD

RED `5840448bd545eb269e139498a80a56da58e825e8` proved the contract did not exist: existing gates passed, then `334 passed / 43 failed` exclusively for the missing module.

GREEN `3205bacbec3fd6e3dc4bc51e107f577322cb498b` introduced `src/forgellm_governance/loop_engineering.py`; Phase 0 passed with `377` complete tests and `230` focused speculative tests.

Validator invariants include:

- exact six semantic fields;
- ForgeLLM/task/Git-base binding;
- path-safe SCOPE subset checks including prefix-confusion rejection;
- exact VERIFY subset of task-packet commands;
- positive iteration, repeated-failure and wall-time ceilings;
- fail-closed STOP fields and `stop_and_escalate` privilege policy;
- receipt location/binding/scope/evidence validation;
- byte-for-byte vendor provenance validation;
- hard rejection of GOALS/STATUS/project-brief shadow state.

### Stage 4 — Repository Loop gate: complete via TDD

RED `b7e3ae36ffc3d78cda381f0faaece7d13c34ee94` produced `377 passed / 1 failed` solely because the repository CLI was absent.

The first GREEN candidate `783b3ced605a2306c697c0162c67742635526ed7` exposed a YAML type defect: unquoted all-zero SHA parsed as integer. The validator correctly failed. `8649d22185fdfda736351b02b6b09b0eb90e7662` fixed only the template representation and passed with `378` tests + `230` focused.

Delivered:

- read-only `scripts/validate_loop_engineering.py`;
- active `P0-T10-loop.yaml` declaration;
- explicit non-passing receipt template.

The repository CLI validates policy; it does not execute loop iterations.

### Stage 5 — Project-local Claude/Codex bridge: complete via TDD

RED `52e6f8ce4e13a486999cebbbc48f57385d4d6ed7`: `378 passed / 4 failed`, exclusively missing skills/Working Agreement markers.

GREEN `b7da84ec0334ba3e83cb1c93916c031521cb5d51`: `382` tests + `230` focused passed.

The Claude and Codex `SKILL.md` files are byte-identical. They require authoritative Git startup, one isolated writer branch/worktree, the six fields, finite budgets, raw verifier feedback, a fresh independent verifier before a passing receipt, and `stop_and_escalate` for privilege boundaries. Vendored upstream documents are marked reference-only. No hook/runner/install command is exposed.

### Stage 6 — Normal `make ci` integration: complete via TDD

RED `b534ccbc352a7aca0783da29148342cd5fece63e`: `382 passed / 2 failed`, proving P0-T10 was not yet wired into normal validation/formatting.

Candidate `7a3878f93fa832fdd51478f39ed580d5b7201d14` then exposed one real Ruff-format gap when the new Python surfaces entered the format gate. The format gate was preserved and the code corrected.

`80ed7b478532979da0e0209a077d7e412ddd65b3` passed normal Phase 0 with `384` complete tests + `230` focused speculative tests. `validate-loop` runs before historical validation, and the pre-existing P0-T09 packet validation remains intact.

### Stage 7 — Static-analysis remediation: complete, no suppression

Sonar found 10 maintainability issues on the initial Makefile-green implementation: receipt-validator cognitive complexity, one unnecessary test exception wrapper, and eight composite assertions.

They were fixed structurally. Current implementation head before this plan/evidence update:

`5c5a7e54149c8d824d411283f44a99e9bd0f08a0`

Exact evidence:

- Phase 0 run `32227746741` / job `95990883246`: success;
- Ruff: all checks passed, 20 files already formatted;
- Loop contract: `OK: bounded Loop Engineering contract is valid`;
- complete suite: `384 passed`;
- focused speculative suite: `230 passed`;
- CodeQL check `95991070923`: success / no new alerts;
- GitGuardian check `95990891924`: success / 14 commits scanned / no secrets;
- Sonar check `95990997714`: success / Quality Gate passed / 0 new issues / 0 accepted issues / 0 hotspots;
- fresh cache-busted Sonar issue readback: total `0`;
- Dependency Review `95990884483`: terminal `skipped`, not success.

## Current stage — documentation/evidence synchronization

This plan and `docs/quality/P0-T10-LOOP-ENGINEERING.md` must reflect the tested implementation and negative results. Their commit moves the PR head, so all exact-head gates must rerun afterward. No ADR status change is permitted in this stage.

Verification after this update:

```bash
python scripts/validate_task_packet.py tasks/open/P0-T10-bounded-loop-engineering.yaml --root .
python scripts/validate_loop_engineering.py --root .
python -m pytest -q tests/test_loop_engineering.py
make ci
git diff --check
git status --short
```

GitHub-hosted evidence must also include Phase 0, CodeQL, GitGuardian, Sonar and the actual Dependency Review conclusion on the exact documentation head.

## Remaining stage A — Independent architecture/security review

Freeze one exact review head only after all machine gates are green. Request an independent reviewer/model that did not author the implementation.

The review must challenge at minimum:

1. source-of-truth duplication or shadow state;
2. command-injection/eval or indirect executable vendoring;
3. path normalization and prefix-escape mistakes;
4. verifier widening or writer self-certification;
5. unbounded retry/watch/daemon behavior;
6. privilege escalation through loop/task/skill text;
7. third-party provenance drift or incomplete license binding;
8. Claude/Codex instruction conflicts;
9. one-writer/worktree assumptions and parallel overlap;
10. receipt semantics that could falsely promote an unauthorized result.

Any BLOCKER or MAJOR finding requires code/test remediation and a fresh exact-head review. Green CI alone is not review acceptance.

## Remaining stage B — Accept ADR-0005 only after independent ACCEPT

After independent ACCEPT on the exact implementation/evidence head:

- record reviewer/model, reviewed SHA, disposition, and any remediations in the quality evidence;
- change ADR-0005 from `proposed` to `accepted`;
- do not alter the decision content unless review requires a new change;
- rerun every exact-head gate after the status commit.

The ADR status commit itself invalidates earlier exact-head evidence for merge purposes.

## Remaining stage C — Merge through protected PR

Immediately before merge:

- re-read `main` and PR #37 head;
- require `main` compatibility;
- require exact-head Phase 0, CodeQL, GitGuardian and Sonar success;
- report Dependency Review by its actual conclusion;
- require the independent ACCEPT to bind the exact accepted-ADR implementation lineage;
- squash-merge using `expected_head_sha`;
- never push directly to `main`.

## Remaining stage D — Protected-main proof and separate closeout

After merge:

1. require resulting `main` Phase 0/Loop gate success and applicable CodeQL/GitGuardian/Sonar evidence;
2. confirm no P0-T09 external configuration changed;
3. create a separate reviewed closeout branch/PR;
4. write the real P0-T10 receipt with final merge SHA and independent verifier evidence;
5. move the task packet from `tasks/open/` to `tasks/closed/`;
6. update CURRENT_STATE, HANDOFF and PHASE0_TASKS from exact merged-main evidence;
7. retain all negative results and explicit non-claims.

## Stop conditions

Stop implementation and diagnose rather than raising budgets when any of these occurs:

- 10 implementation iterations are exhausted;
- 3 consecutive identical verifier failures occur;
- 60 minutes of declared loop wall time is exhausted for one bounded execution;
- a privileged operation is required;
- scope/verification authority needs widening;
- provenance cannot be bound byte-for-byte;
- independent review returns an unresolved BLOCKER/MAJOR;
- P0-T09 or another task would need to be modified implicitly.

The loop never authorizes a privileged workaround to a STOP condition.
