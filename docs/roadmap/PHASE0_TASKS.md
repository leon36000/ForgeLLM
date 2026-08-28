# Phase 0 Task Index

| Task | Status | Deliverable | Gate |
|---|---|---|---|
| P0-T01 | complete and locally verified | generate Phase 0 operating system | `make verify`: 11 tests passed |
| P0-T02 | complete | canonical remote, review policy, deterministic mobile hashing and post-merge CI | merges `20bc5fa…` and `843f812…` |
| P0-T03 | complete | public-repository policy, hosted security gates and protected `main` | active ruleset `FLLM` |
| P0-T04 | blocked on owner host designation | collect first sanitized hardware/software inventory | one approved host label and execution mode |
| P0-T05 | blocked on P0-T04 | define P1 workload profiles | reviewed hardware/topology evidence and owner metrics/models |
| P0-T06 | blocked on P0-T05 | write P1 baseline implementation plan | reviewed profile specification |
| P0-T07 | complete | synthetic cache-aware topology and placement simulator | PR #20; 102 tests; PR/post-merge gates |
| P0-T08 / CA-03 | complete | finite exact speculative-decoding reference semantics | PR #24 + remediation PR #25; 332 complete and 230 focused tests; dual review; PR/post-merge gates |
| P0-T09 / QG-01 | in progress — Task 4B.1 artifact boundary merged (inactive) | maintain and independently review the accepted `ci_based_only` scanner path without activation or submission | LOC-limit cause classified; PR #67 merged at `main@83f8ea6`; producer success/scanner skipped; current Sonar project remains Automatic Analysis |
| P0-T11 | complete | bounded Rust CPU reference core: checked tensors, matmul, softmax, RMSNorm, argmax and recoverable allocations | PR #48; 28 Rust tests; independent review; hosted exact-head gates; merge `04342c8` |
| P0-T12 | complete | bounded decoder tensor primitives: reshape, exact-shape add/multiply and embedding gather | PR #53; 46 Rust tests on the stacked line; independent review; hosted exact-head gates; merge `7962abe6` |
| P0-T13 | complete | public-artifact privacy hardening with fail-closed sanitization and snapshot boundary | PR #78; protected merge `ad079c0`; 34 focused, 487 full and 230 speculative tests |
| P0-T14 | complete | task lifecycle and derived-state validation with deterministic projections | issue #73; 13 lifecycle tests; `make validate`/`make ci`; ADR-0005 and ADR-0006 remain proposed |
| P0-T15 | in progress — design-only checkpoint merged | versioned C ABI and runtime lifecycle design, without implementation | PR #75; protected merge `9932a5a`; ADR-0006 proposed; no ABI/runtime/backend code |
| P0-T10 | review — implementation merged, acceptance pending | bounded, inert Loop Engineering bridge with provenance, task binding, receipts, and fail-closed repository validation | `main@87a1dde`; make validate-loop; ADR-0005 remains proposed; final architecture/security acceptance record absent |

## P0-T10 integration checkpoint

The P0-T10 static integration is published at merge commit 87a1ddeb76d2bca45fe75853b4c3b4c9f19c78b0 from canonical base f8364f12402c3c58796dbc1b56f8c65d378e88de. Its receipt binds to that public merge commit, so a fresh clone containing only protected `main` can reproduce the catalog validation. The lifecycle record remains `review` because ADR-0005 is still `proposed` and the required final architecture/security acceptance record is absent. The increment remains limited to governance/reference artifacts and does not modify P0-T09, hardware, runtime, backend, or Sonar settings.

## P0-T14 lifecycle checkpoint

P0-T14 reconciles the open/closed task directories and the derived state projections required by issue #73. The implementation enforces non-terminal open packets, terminal closed packets, unique IDs, exact filename prefixes, dependency resolution, ADR status/successor rules, canonical state metadata, a hashed non-authoritative mobile manifest, the README current-state block and an exact `git ls-files` tree. P0-T10 stays in `review` because ADR-0005 is `proposed`; this checkpoint does not accept an ADR or alter any external setting.

## P0-T09 current gate

- owner command: `autorise P0-T09 / subagent-driven`;
- canonical base: `1b1a3621fcdf4129268663c497cdcd53aed48c29`;
- evidence branch: `forgeai/manual-p0-t09-evidence-update-20260817102053`;
- verified pre-change evidence anchor: protected `main@26a0a66bbbc3c5e3f6e68ed379e074ca06da47f5`;
- task packet: `tasks/open/P0-T09-sonarqube-main-analysis.yaml`;
- selected analysis method: `ci_based_only` (ADR-0004), with explicit preparation-only posture;
- current Sonar analysis method in platform: Automatic Analysis remains active;
- explicit guard: no SONAR_TOKEN provisioning, no scanner submission, no activation, no PR secret delivery.
- baseline JSON: `artifacts/governance/P0-T09-sonar-baseline.json`;
- baseline report: `docs/quality/P0-T09-SONAR-BASELINE.md`;
- configuration changes: `ForgeLLM Sonar visibility private -> public` only, under explicit owner authorization;
- failure classification: `platform_limitation / subscription_loc_limit_exceeded`;
- internal failed branch-task status: `FAILED`;
- post-remediation Billing & usage: Free plan, 50,000 private-LOC entitlement, 48,248 consumed, approximately 1.8k remaining;
- method selection: `ci_based_only` (ADR-0004 accepted); Task 4B.1 remains preparation-only.
- merged preparation: PR #58 and PR #60; post-merge state synchronizations: PR #61 and PR #62; workflow remains default-off and inactive;
- verified pre-change Automatic Analysis: `2a0d79e4-bbb1-4536-b1e6-6351ab2ef56d` on `main@26a0a66bbbc3c5e3f6e68ed379e074ca06da47f5`, Quality Gate `OK`;
- workflow posture on the verified anchor: `producer=success`, `scanner=skipped`; this is not a CI scanner submission.

Public and owner-authenticated evidence now shows five historical PR-success/`main`-failure recurrences, with Phase 0 and CodeQL succeeding on the corresponding commits. Sonar Background Tasks establishes the internal branch-analysis status as `FAILED`, and the owner-authenticated error identifies the organization private-LOC subscription limit as the immediate cause. The verified pre-change anchor contains `.github/workflows/sonar.yml` and `sonar-project.properties` as an inactive, default-off CI path; the producer succeeded, the scanner was skipped, and no CI scan was submitted.

The historical administrative readback records binding `leon36000/ForgeLLM`, Automatic Analysis/Autoscan, no CI method selected at that time, New Code `previous_version`, default/no custom scope or issue-ignore settings, and default `Sonar way`. ADR-0004 subsequently accepted `ci_based_only`. After ForgeLLM was aligned from private to public in Sonar, anonymous Sonar API access independently confirmed the public project while Billing & usage returned below the private-LOC limit.

Verified pre-change evidence anchor: protected `main@26a0a66bbbc3c5e3f6e68ed379e074ca06da47f5`. Phase 0 run `32438425091` and CodeQL run `32438425096` succeeded; prepared inactive Sonar workflow run `32438425087` completed with `producer=success` and `scanner=skipped`; Automatic Analysis `2a0d79e4-bbb1-4536-b1e6-6351ab2ef56d` targets that exact revision with Quality Gate `OK`. This is Automatic Analysis evidence, not a CI scanner submission.
Merging this four-file documentation synchronization will create a different protected-main SHA. That merge SHA is not claimed as verified by this snapshot. No fourth documentation-only synchronization may chase it.

Next gate (not executed or authorized by this documentation increment): obtain explicit independent review and authorization for the no-overlap migration sequence. Automatic Analysis remains enabled and the prepared CI scanner remains inactive.
If separately authorized, complete a separate token identity/lifecycle security review without provisioning `SONAR_TOKEN`; then capture the sequence in order: fresh Automatic Analysis enabled readback; owner-authorized disable action; Automatic Analysis disabled readback. Require another explicit gate before CI activation or the first controlled submission.
Until those gates are satisfied: no `SONAR_TOKEN`, no Sonar or GitHub setting change, no scanner activation, no scan submission, and no PR bridge. P0-T09 remains `in_progress`. After this final snapshot cycle, stop the documentation loop; resume only after a material activation, evidence, status, or substantive-error change.
Automatic and CI-based methods may not run concurrently for the same project; this increment is preparation-only.

Merged checkpoint: the protected-ref producer prepares source and Clippy data without credentials and transfers one immutable fixed artifact to the scanner; the validator mechanically requires the event-SHA checkout, fixed upload/download pins and fail-closed symlink rejection. Focused governance evidence is 53 tests passing; protected `main@83f8ea6` has Phase 0 and CodeQL success plus producer success/scanner skipped. P0-T09 remains `in_progress` because token lifecycle, no-overlap activation and successful Sonar CI evidence are still open.

## P0-T11 / P0-T12 final evidence

- P0-T11 base: `main@aff9897e1c9e3aaebd67889eb9ff6d65a1710694`; published head:
  `dfd6849cfc3c48e801f1e495239f2ec1ad810569`; PR #48 merge:
  `04342c859f790948fa784b72df940ac441ed5ed3`.
- P0-T12 stacked implementation head: `0e14b9471cc68227b589fa274fbb6cf65bc6802e`; corrected
  validation head: `95139f8aea2aa1b4adedb66c22ecf698b127f8ab`; final publication head:
  `0ce6bb4ed39125c39c2b149ae6bf26688ec649cb`; PR #53 merge:
  `7962abe6c08a79da28e083735507fbae29529d74`.
- The final source tree contains a CPU reference increment only: 46 Rust tests pass (2 unit,
  17 decoder, 3 numerical, 24 reference), with rustfmt, Clippy, `make ci`, direct packet
  validation and the required hosted checks green.
- Hosted `dependency-review` was `SKIPPED` on both PRs by the existing workflow configuration;
  Validate and test, reference-core, SonarCloud and GitGuardian passed on each exact head.
- The independent local verdicts are recorded in `docs/reviews/P0-T11-CODEX-REVIEW-2026-08-20.md`
  and `docs/reviews/P0-T12-CODEX-REVIEW-2026-08-20.md`.
- This line does not establish real-model conformance, PyTorch numerical agreement, hardware or
  accelerator behavior, performance, ABI, scheduling, KV cache, service runtime, P1/P2 promotion,
  or production readiness.

## P0-T08 final evidence

- base: `1cd502609c7b05ac628057f79a9135b07c08e821`;
- final implementation head: `16d65288b34a9f2f91a4c67182aab13ddfb5e17d`;
- implementation merge: `e6c9d1ae30f1b5e161a56bf8c9b4fa25c823fe24`;
- Phase 0 implementation `31831781322` / `94868927648`: success;
- complete suite: 332 passed;
- focused exact-reference suite: 230 passed;
- CodeQL implementation `31831781266` / `94868926709`: success;
- specification-compliance review `4940413742`: `ACCEPT`;
- code-quality review `4940415259`: `ACCEPT`;
- remediation head: `a7f508fe1fa4787b889445c5e5986339b508217a`;
- remediation merge: `e81c1c0ad0b161844569df46ee62246c9de56698`;
- Phase 0 remediation `31838436974` / `94889874946`: success;
- CodeQL remediation `31838436902` / `94889874310`: success;
- SonarQube Cloud PR check `94889986512`: Quality Gate passed, 0 new issues, 0 security hotspots;
- evidence boundary: `finite_exact_reference`.

## P0-T04 entry condition

Issue #12 and `tasks/open/P0-T04-first-hardware-inventory.yaml` remain authoritative. Execution begins only after the owner designates one project-safe host label and an execution mode.

## Future research entry condition

Transition Atlas, real-model conformance and runtime integration remain proposals only. Each requires its own primary-source-backed specification, reviewed plan, schema-valid task packet and owner authorization. CA-03 provides a correctness oracle but does not authorize implementation of those paths.
