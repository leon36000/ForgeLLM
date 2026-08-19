# P0-T10 — Bounded Loop Engineering Evidence

- **Task:** P0-T10 — Adopt bounded Loop Engineering orchestration
- **Tracking:** issue #36, pull request #37
- **Canonical base:** `8594ef5abb19ca7a870fe6d71ae7aad8e15f4602`
- **Owner decision:** design B approved on 2026-08-19 — vendored static upstream methodology plus a ForgeLLM-specific bounded bridge
- **ADR:** `ADR-0005-bounded-loop-engineering.md`, status `proposed` until final independent architecture/security review
- **Evidence boundary:** `orchestration_governance`; this work does not prove runtime, inference, hardware, performance, CUDA, ROCm, distributed, or Sonar-CI activation behavior

## Selected boundary

Loop Engineering is installed only as a project-local ForgeLLM bridge. Existing ForgeLLM authority is unchanged: accepted charter/ADRs and the active task packet outrank loop declarations, plans, receipts, skills, and vendored upstream text.

Every runnable ForgeLLM loop binds exactly the six semantic fields `GOAL`, `SCOPE`, `VERIFY`, `BUDGET`, `STOP`, and `RECEIPT` to one task packet and one Git base revision. The P0-T10 active loop is bounded by:

- `max_iterations: 10`;
- `max_identical_failures: 3`;
- `max_wall_minutes: 60`;
- `privileged_operation: stop_and_escalate`.

The bridge does not execute upstream orchestration. It contains no upstream installer, shell runner, eval-based loop runner, Stop hook, or shadow `docs/GOALS.md` / `docs/STATUS.md` / project-brief state.

## Upstream provenance

Reviewed upstream: `https://github.com/lcajigasm/loop-engineering` at exact commit `ae2d610985064bb30c5013261988c813013c09e3`.

Vendored inert files and exact upstream Git blob SHAs:

| Path | Upstream blob SHA |
|---|---|
| `LICENSE` | `84524f23b209fccb02a8f239165f0444bfd70f3f` |
| `core/METHODOLOGY.md` | `c7094ca40c2257d653c4d48f6b87c40cb82b209b` |
| `core/COMMANDS.md` | `4de9e981ad89c04f28d94ea4ad5b97e1b513b578` |
| `core/templates/PLAN.template.md` | `3477e664b738a46b36e4b015b1b2ef502b5c6dd4` |
| `core/templates/RECEIPT.template.md` | `2f5da7d5736067c965b4fed2604982e00a79b024` |
| `core/templates/INTEGRATION.template.md` | `2f740b4dbc1f7ee63688abe570c179bd28fc4508` |
| `core/templates/CAPABILITIES.template.md` | `da89bdb92b2f61558babc7c699cd2c350904f07a` |

License is MIT. `PROVENANCE.yaml` records the exact upstream commit, license blob, file blobs, and excluded executable/shadow-state surfaces. Repository validation recomputes the Git-compatible blob SHA for every vendored file and fails on byte drift or any extra file in the vendored tree.

Explicitly excluded upstream surfaces:

- `install.sh`;
- `core/scripts/`;
- `claude-code/`;
- `codex/`;
- GOALS/STATUS/PROJECT_BRIEF/ADR templates that could create a competing state hierarchy.

## TDD and negative-result ledger

### 1. Core contract RED → GREEN

- RED commit `5840448bd545eb269e139498a80a56da58e825e8`.
- Phase 0 run `32225843931` / job `95985262800`: failure after existing Ruff/structural gates passed; pytest `334 passed / 43 failed`, with every new failure caused by the intentionally absent `forgellm_governance.loop_engineering` module.
- GREEN commit `3205bacbec3fd6e3dc4bc51e107f577322cb498b`.
- Phase 0 run `32226029581` / job `95985793320`: success; `377 passed` complete suite plus `230 passed` focused speculative tests.

The GREEN validator rejects scope widening, verifier widening, unbounded budget, privileged operation, shadow-state authority, provenance drift, and incomplete receipts.

### 2. Repository gate RED → GREEN

- RED commit `b7e3ae36ffc3d78cda381f0faaece7d13c34ee94`.
- Phase 0 run `32226151353` / job `95986140019`: failure with `377 passed / 1 failed`; only failure was the intentionally absent `scripts/validate_loop_engineering.py`.
- First GREEN candidate `783b3ced605a2306c697c0162c67742635526ed7` exposed a real YAML typing defect: unquoted all-zero `final_commit` was parsed as integer `0`, and the fail-closed receipt validator correctly rejected it.
- Minimal correction `8649d22185fdfda736351b02b6b09b0eb90e7662` quoted the placeholder SHA.
- Phase 0 run `32226526309` / job `95987208211`: success; `378 passed` plus `230 passed` focused speculative tests.

### 3. Claude/Codex bridge RED → GREEN

- RED commit `52e6f8ce4e13a486999cebbbc48f57385d4d6ed7`.
- Phase 0 run `32226680215` / job `95987652406`: failure with `378 passed / 4 failed`; failures were only the intentionally missing project-local skills and Working Agreement markers.
- GREEN commit `b7da84ec0334ba3e83cb1c93916c031521cb5d51`.
- Phase 0 run `32226917734` / job `95988351864`: success; `382 passed` plus `230 passed` focused speculative tests.

The Claude and Codex skills are byte-identical project-local documentation. They require Git/task/ADR precedence, one isolated writer branch/worktree, the six loop fields, finite budgets, raw verifier feedback, a fresh independent verifier before a passing receipt, and `stop_and_escalate` at privilege boundaries. They contain no hook installation instructions.

### 4. Repository-wide Make gate RED → GREEN

- RED commit `b534ccbc352a7aca0783da29148342cd5fece63e`.
- Phase 0 run `32227052977` / job `95988763478`: failure with `382 passed / 2 failed`; only failures were missing `validate-loop`/P0-T10 wiring and missing Loop Python format coverage.
- First Makefile candidate `7a3878f93fa832fdd51478f39ed580d5b7201d14` exposed a real formatting gap when the new Python surfaces were finally placed under Ruff format check; Phase 0 run `32227205948` / job `95989244810` failed rather than weakening the format gate.
- Formatting correction head `80ed7b478532979da0e0209a077d7e412ddd65b3`.
- Phase 0 run `32227445846` / job `95989981494`: success; `validate-loop` ran before historical validation, P0-T09 validation remained present, Ruff covered 20 files, `384 passed` complete suite, `230 passed` focused speculative suite.

### 5. Sonar findings resolved without suppression

On the Makefile-green implementation Sonar reported 10 maintainability findings: one cognitive-complexity issue in receipt validation, one unnecessary test exception wrapper, and eight composite pytest assertions. The Quality Gate was green, but the findings were not accepted or hidden.

They were fixed through behavior-preserving decomposition and assertion clarification:

- implementation head `5c5a7e54149c8d824d411283f44a99e9bd0f08a0`;
- Phase 0 run `32227746741` / job `95990883246`: success;
- complete suite: `384 passed`;
- focused speculative suite: `230 passed`;
- CodeQL check `95991070923`: success, no new alerts in changed code;
- GitGuardian check `95990891924`: success, 14 PR commits scanned with no secrets;
- Sonar Automatic check `95990997714`: success, Quality Gate passed, 0 new issues, 0 accepted issues, 0 security hotspots;
- fresh cache-busted Sonar issue readback: `total=0`;
- Dependency Review check `95990884483`: terminal `skipped`, not success.

### 6. Final-receipt promotion boundary RED → GREEN

Adversarial review found a semantic gap: the inert repository `TEMPLATE.yaml` was validated by the same generic function used for a final receipt. Documentation said the template was non-probative, but code did not make that distinction fail-closed.

- RED commit `54d3c3b4de95f261d7c51e48cb7400814e8849fd` added four tests only: a template cannot pass final-receipt validation; all-zero final SHA is rejected; `stop_reason: template` is rejected by final validation; a dedicated template validator is required.
- Phase 0 run `32228926686` / job `95994408597`: failure with `384 passed / 4 failed`; Ruff, provenance, Loop gate and P0-T09 validation remained green.
- First GREEN candidate `6f9dcad1ebe3707a932d00832c0cd56d63441f15` separated final/template semantics but concentrated template validation enough for Sonar `python:S3776` (cognitive complexity 19 > 15); no threshold or suppression was changed.
- Refactor `accdb6f4eb1ebcf3ebae7202d54286538891877e` decomposed template validation. Sonar returned 0 new issues, but Phase 0 produced `387 passed / 1 failed`.
- That single failure was classified **bad gate**: the test compared the real P0-T10 template with a synthetic P0-T99 declaration, so the validator correctly reported task/base/VERIFY binding mismatches. Validator policy was not weakened.
- Bad-gate fix `6a7bf616b972bab00649962fe4eaed84a5020dbf` changed only the test to load the active P0-T10 declaration for template-structure validation.
- Phase 0 run `32230113979` / job `95997918154`: terminal `success`; repository Loop validation, Ruff, all historical validation and the complete/focused test gates succeeded. The connector did not expose a stable raw pytest-count line on re-read, so no exact new test count is asserted here.
- CodeQL check `95998373942`: `success`, no new alerts in changed code.
- GitGuardian check `95997918026`: `success`, 20 PR commits scanned with no secrets.
- Sonar Automatic check `95998242109`: `success`, Quality Gate passed, 0 new issues, 0 accepted issues, 0 security hotspots.
- Fresh cache-busted Sonar issue readback on PR #37: `total=0`.
- Dependency Review check `95997918947`: terminal `skipped`, not success.

Final semantics are now mechanically distinct:

- `validate_loop_receipt()` accepts only final evidence: non-zero full Git SHA, approved final stop reason, non-template reviewer, declared VERIFY evidence, scope pass and task/base binding.
- `validate_loop_receipt_template()` accepts only the inert sentinel form: `final_commit: REPLACE_WITH_FINAL_COMMIT`, `stop_reason: template`, zero iterations/failures, no changed paths, `TEMPLATE:` evidence/reviewer markers, and exact P0-T10 task/base/VERIFY binding.
- `scripts/validate_loop_engineering.py` validates repository `TEMPLATE.yaml` only through the template validator. A template therefore cannot be promoted into final evidence by passing the repository gate.

## Installed ForgeLLM surfaces

- `src/forgellm_governance/loop_engineering.py` — fail-closed declaration, final receipt, template receipt, and vendor-provenance validation.
- `scripts/validate_loop_engineering.py` — read-only repository validator; no loop execution.
- `artifacts/governance/loop-engineering/P0-T10-loop.yaml` — bounded P0-T10 declaration.
- `artifacts/governance/loop-engineering/receipts/TEMPLATE.yaml` — inert receipt template with a non-SHA sentinel and explicit TEMPLATE markers.
- `.agents/skills/forgellm-loop-engineering/SKILL.md` and `.claude/skills/forgellm-loop-engineering/SKILL.md` — identical project-local adapters.
- `AGENTS.md` / `CLAUDE.md` — bounded bridge precedence markers appended without replacing existing instructions.
- `Makefile` — `validate-loop` is part of ordinary `validate`/`make ci`; P0-T09 validation remains intact.

## Privilege and source-of-truth firewall

A loop may narrow but never widen its task packet's `allowed_paths` or `verification_commands`. It cannot grant itself authority over secrets, credentials, accounts, billing, GitHub or Sonar administration, Tailscale, privileged hosts/runners, production machines, or destructive external operations. Those require separate explicit authorization and before/after verification outside the loop.

Receipts are evidence only. A green receipt cannot override an accepted ADR, task non-goal, failed correctness oracle, or security gate.

## Explicit non-claims

P0-T10 does **not**:

- activate P0-T09 Sonar CI or provision `SONAR_TOKEN`;
- change Sonar, GitHub, Tailscale, billing, or account settings;
- authorize hardware inventory, CUDA, HIP/ROCm, kernels, runtime, C ABI, distributed execution, model inference, or benchmarks;
- establish performance claims;
- close P0-T09 or P0-T04/P0-T05;
- prove that the upstream Loop Engineering runner is safe to execute;
- make the receipt template a passing receipt.

## Remaining acceptance gate

ADR-0005 remains `proposed`. Before merge, PR #37 requires an independent architecture/security review of the exact final diff with no unresolved BLOCKER or MAJOR finding. The reviewer must challenge source-of-truth duplication, command injection/eval surfaces, scope-prefix escape, verifier self-certification, unbounded retry/watch behavior, privilege escalation from loop text, vendor provenance drift, agent-instruction conflicts, worktree/writer assumptions, and receipt promotion semantics.

Only after independent ACCEPT may ADR-0005 become `accepted`; that status change must then receive a fresh exact-head Phase 0, CodeQL, GitGuardian, Sonar and Dependency Review readback before merge.
