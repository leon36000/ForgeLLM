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
| P0-T09 / QG-01 | in progress — Task 4B.1 preparation merged (inactive) | maintain and independently review the accepted `ci_based_only` scanner path without activation or submission | LOC-limit cause classified; inactive preparation merged; current Sonar project remains Automatic Analysis |
| P0-T11 | complete | bounded Rust CPU reference core: checked tensors, matmul, softmax, RMSNorm, argmax and recoverable allocations | PR #48; 28 Rust tests; independent review; hosted exact-head gates; merge `04342c8` |
| P0-T12 | complete | bounded decoder tensor primitives: reshape, exact-shape add/multiply and embedding gather | PR #53; 46 Rust tests on the stacked line; independent review; hosted exact-head gates; merge `7962abe6` |

## P0-T09 current gate

- owner command: `autorise P0-T09 / subagent-driven`;
- canonical base: `1b1a3621fcdf4129268663c497cdcd53aed48c29`;
- evidence branch: `forgeai/manual-p0-t09-evidence-update-20260817102053`;
- current canonical `main`: `2339a8daa1c26aa13c043ef1739fa647352b60a5`;
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
- merged preparation: PR #58 and PR #60; post-merge state synchronization: PR #61; workflow remains default-off and inactive;
- current main Automatic Analysis: `8b20603d-12a6-4d13-9d55-663d2c295384` on `main@2339a8daa1c26aa13c043ef1739fa647352b60a5`, Quality Gate `OK`;
- workflow posture on current main: `producer=success`, `scanner=skipped`; this is not a CI scanner submission.

Public and owner-authenticated evidence now shows five historical PR-success/`main`-failure recurrences, with Phase 0 and CodeQL succeeding on the corresponding commits. Sonar Background Tasks establishes the internal branch-analysis status as `FAILED`, and the owner-authenticated error identifies the organization private-LOC subscription limit as the immediate cause. The current `main` now contains `.github/workflows/sonar.yml` and `sonar-project.properties` as an inactive, default-off CI path; the producer succeeded, the scanner was skipped, and no CI scan was submitted.

The historical administrative readback records binding `leon36000/ForgeLLM`, Automatic Analysis/Autoscan, no CI method selected at that time, New Code `previous_version`, default/no custom scope or issue-ignore settings, and default `Sonar way`. ADR-0004 subsequently accepted `ci_based_only`. After ForgeLLM was aligned from private to public in Sonar, anonymous Sonar API access independently confirmed the public project while Billing & usage returned below the private-LOC limit.

Next gate (not executed or authorized by this documentation increment): obtain explicit human review and authorization for the no-overlap migration sequence. Automatic Analysis remains enabled and the prepared CI scanner remains inactive.
If separately authorized, capture the sequence in order: fresh Automatic Analysis enabled readback; human disable action; Automatic Analysis disabled readback. Complete a separate token identity/lifecycle security review before provisioning `SONAR_TOKEN`, and require another explicit gate before CI activation or the first controlled submission.
Until those gates are satisfied: no `SONAR_TOKEN`, no Sonar or GitHub setting change, no scanner activation, no scan submission, and no PR bridge. P0-T09 remains `in_progress`.
Automatic and CI-based methods may not run concurrently for the same project; this increment is preparation-only.

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
