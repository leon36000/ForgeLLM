# ForgeLLM Current State

- **State ID:** S-0008
- **Updated:** 2026-08-20
- **Phase:** P0
- **Milestone:** P0-M6 — exact speculative-decoding reference verified
- **Overall status:** P0-T08 / CA-03 is complete; the bounded Rust CPU reference line P0-T11/P0-T12 is complete and merged; P0-T09 / QG-01 remains active after the default-off Task 4B.1 preparation was merged for the accepted ADR-0004 method `ci_based_only`. Automatic Analysis remains enabled in SonarQube Cloud, while the committed CI workflow is inactive: current `main@2339a8daa1c26aa13c043ef1739fa647352b60a5` has Automatic Analysis `8b20603d-12a6-4d13-9d55-663d2c295384` with public Quality Gate `OK`, and the workflow posture is `producer=success`, `scanner=skipped`. This is not a CI scanner submission. The diagnosed historical failure remains classified `platform_limitation / subscription_loc_limit_exceeded` with internal task status `FAILED`; the owner-authorized minimal remediation changed only Sonar project visibility for `leon36000_ForgeLLM` from private to public, matching the already-public canonical GitHub repository. Billing & usage after the change shows Free plan, 50,000 private-LOC entitlement, 48,248 private LOC consumed and approximately 1.8k remaining. P0-T04 remains blocked on designation of one owner-authorized host.
- **Authorized next work:** ADR-0004 is accepted and selects `ci_based_only`. Obtain explicit human review and authorization for the no-overlap migration sequence; do not provision `SONAR_TOKEN`, disable Automatic Analysis, activate CI submission, submit a scan, or design the blocked PR bridge from this documentation increment. If separately authorized, record enabled readback → human disable action → disabled readback, then complete token identity/lifecycle review before any first controlled CI submission. P0-T04 may proceed independently after host designation.
- **State anchor:** the Git commit containing this file

## Objective

Preserve the exact speculative-decoding oracle as the correctness reference for later cache-aware, accelerator and runtime implementations while restoring a reproducible and truthful SonarQube Cloud quality signal for protected `main`.

## Canonical repository

- Repository: `leon36000/ForgeLLM`.
- Default branch: protected `main`.
- Initial P0-T09 base: `1b1a3621fcdf4129268663c497cdcd53aed48c29`.
- Latest canonical `main`: `2339a8daa1c26aa13c043ef1739fa647352b60a5`.
- Active task packet: `tasks/open/P0-T09-sonarqube-main-analysis.yaml`.
- Tracking issue: #26.
- Owner authorization: `P0-T09 / subagent-driven`, recorded 2026-08-14.

## P0-T08 / CA-03 completion

CA-03 delivered a placement-independent finite exact oracle for stochastic and greedy speculative decoding.

### Delivered capabilities

- canonical finite distributions using `fractions.Fraction`;
- immutable deterministic `RandomTape` with no modulo reduction;
- exact Bernoulli and one-token modified rejection sampling;
- recorded proposal distributions and prefixes;
- first-rejection correction from normalized `(p-q)_+`;
- legal target bonus, EOS and output-budget semantics;
- exact ordinary-target and speculative output-law enumeration;
- exact-law grids for budgets 0–4 and draft lengths 1–3, including prefix-dependent and adversarial models;
- separate deterministic greedy oracle;
- transactional materialized/pending target, draft, sampler and grammar witnesses;
- cancellation rollback and pending-token synchronization;
- deterministic environment-free traces;
- fail-closed guards for invalid direct constructions and impossible probability witnesses;
- explicit `verify-speculative` repository gate.

### Final evidence

- implementation head `16d65288b34a9f2f91a4c67182aab13ddfb5e17d`;
- implementation merge `e6c9d1ae30f1b5e161a56bf8c9b4fa25c823fe24`;
- complete suite: **332 passed**;
- focused `verify-speculative`: **230 passed**;
- specification-compliance review `4940413742`: `ACCEPT`;
- code-quality review `4940415259`: `ACCEPT`;
- remediation head `a7f508fe1fa4787b889445c5e5986339b508217a`;
- remediation merge `e81c1c0ad0b161844569df46ee62246c9de56698`;
- evidence boundary: `finite_exact_reference`.

## P0-T09 / QG-01 active diagnosis

### Public and owner-authenticated evidence

The evidence is recorded in:

- `artifacts/governance/P0-T09-sonar-baseline.json`;
- `artifacts/governance/P0-T09-sonar-analysis-method-readback.json`;
- `docs/quality/P0-T09-SONAR-BASELINE.md`;
- `artifacts/governance/P0-T09-readonly-diagnosis-2026-08-17.json`.

The GitHub evidence now includes a post-import probe:

1. PR #30 Sonar check `94945852247` succeeded with 0 new issues and 0 security hotspots;
2. Phase 0 and CodeQL succeeded on the PR head;
3. the merged `main` commit `bd03e479ff4649a254c41726b33f2b6e841a0e0c` received Sonar check `94946081665`, completed `cancelled` with `SonarQube Cloud analysis failed` and zero GitHub annotations.

Therefore importing the project was not sufficient to repair the `main` analysis path.

A fifth recurrence was observed on the then-current head: PR #31 Sonar check `94948153214` succeeded, while `main@484fec34007fd89f554c9c03bffa9a5275676602` received Sonar GitHub check `94948378776` with conclusion `cancelled` and zero annotations; Phase 0 and CodeQL succeeded on the same `main` commit. The GitHub check conclusion is evidence about the check-run object, not proof that the internal Sonar background task itself had status `CANCELED`.

### Analysis Method readback

An owner-authenticated screenshot of **SonarQube Cloud → ForgeLLM → Analysis method** confirms:

```text
Automatic analysis: enabled
Recommendation: Recommended
CI method selected: no
```

The raw screenshot is not committed. A sanitized transcription and its SHA-256 evidence binding are stored in `artifacts/governance/P0-T09-sonar-analysis-method-readback.json`.

This promotes the earlier repository-based inference to an observed project setting: ForgeLLM is currently configured for automatic analysis.

### Current classification

```text
analysis_method_setting = automatic_enabled
compatibility           = recommended
failure_classification  = platform_limitation
failure_subtype         = subscription_loc_limit_exceeded
internal_task_status    = FAILED
background_task_id      = AaADNoZ4U0I7o8og6Mb6
analysis_id             = 472eadb9-b554-47ca-8336-2033fb3b7408
method_selection        = ci_based_only
configuration_changes   = sonar_visibility_private_to_public_only
```

Owner-authenticated Sonar UI evidence gives a direct sanitized error: the analysis failed because the organization's total lines of code exceed the current subscription limit. A second owner-provided Background Tasks screenshot establishes the internal branch-analysis task status `FAILED` for task `AaADNoZ4U0I7o8og6Mb6`, submitted/started at 22:18:20 and finished at 22:18:23, immediately after a pull-request task `AaADNKJHGgg5GiBgCda_` succeeded from 22:16:16 to 22:16:18. The screenshots expose analysis ID `472eadb9-b554-47ca-8336-2033fb3b7408`; raw images are not committed and their SHA-256 evidence bindings are recorded in the sanitized diagnosis artifact. Public GitHub correlation now strongly associates the Background Tasks pair with PR #31 and the then-current `main@484fec34007fd89f554c9c03bffa9a5275676602`: under a UTC−04:00 UI offset, the Sonar PR and branch task finish times match GitHub checks `94948153214` and `94948378776` exactly to the second, and the public check scopes are respectively `pullRequest=31` and `branch=main`. This is strong correlation but not a definitive shared-identifier binding because the GitHub check payload exposes no Sonar task ID. Authenticated Sonar task detail with revision/SHA would be required only to promote that historical correlation to a shared-identifier proof; it is not required to classify the directly observed failure. The administrative decision readback is now materially complete. ADR-0004 is accepted and selects `ci_based_only`; the remaining repository work is strictly inactive Task 4B.1 preparation, while Automatic Analysis remains active and scanner submission/`SONAR_TOKEN` activation are explicitly forbidden until the human-reviewed no-overlap sequence is completed.

Independent Codex and Claude Code remediation reviews add two negative results that constrain the fix: moving scanner execution from Automatic Analysis to CI-based analysis does not remove SonarQube Cloud's organization LOC entitlement, and the canonical ForgeLLM tree contains no generated, vendored, build-output, fixture, or third-party production source that is justified for exclusion. The maintained non-test Python footprint is approximately 5k physical lines, so subscription remediation must be based on authenticated organization-level Billing & usage rather than speculative repository exclusions.

### Owner-authorized visibility remediation

On 2026-08-17 local time, after the failure class was established, the owner explicitly directed aligning the Sonar project visibility with the already-public canonical GitHub repository. The then-current P0-T09 packet still contained a broad no-Sonar/GitHub-setting freeze before ADR-0004; this action is therefore recorded as a bounded owner-directed exception to that packet, not as an action retroactively authorized by the pre-change packet. A local single-use controller approval was recorded outside Git, and OpenClaw changed only `leon36000_ForgeLLM` from `Private` to `Public - Anyone`. Project key, GitHub binding and Automatic Analysis remained unchanged. Independent anonymous Sonar Web API reads then returned HTTP 200 and confirmed `visibility=public`, binding `https://github.com/leon36000/ForgeLLM`, `autoscanEnabled=true`, the historical visibility-readback revision `d5cd25bd9d6fc3f9cded27781c2051939dcdde85` with `ncloc=1658`, and Quality Gate `OK` for that readback. No GitHub setting, subscription, quality gate, scope, exclusion or analysis method was changed.

Billing & usage after the visibility change reports Free plan, 50,000 private-LOC entitlement, 48,248 private LOC consumed and approximately 1.8k remaining. The diagnosed organization LOC blocker is therefore no longer active at readback time, although the organization is close to the limit.

Post-remediation Automatic Analysis then succeeded on `main@86f32319847a011fb4d48c98f0c467282fcfbe49`; the anonymous readback matched that exact revision, reported Quality Gate `OK`, public visibility, and `ncloc=6939`. The pre-merge current-main readback on `main@4dec19558d076af03ee2bee45482a3f83a2b6f33` completed Automatic Analysis `55533f96-c27b-480a-8e1f-f820bbced2f3` with Quality Gate `OK`; its workflow producer succeeded and scanner was skipped. After PR #61, current `main@2339a8daa1c26aa13c043ef1739fa647352b60a5` completed Automatic Analysis `8b20603d-12a6-4d13-9d55-663d2c295384` with Quality Gate `OK`; Phase 0 and CodeQL also succeeded, and the prepared workflow remained `producer=success`, `scanner=skipped`. This confirms current-main Automatic Analysis health, not CI activation.

### Task 4B.1 preparation boundary

The historical evidence, owner-authorized visibility remediation, administrative readback, accepted ADR-0004, and merged inactive preparation now establish the current repository state. ADR-0004 selects exactly `ci_based_only`; it does not authorize external activation in this increment.

The prepared `.github/workflows/sonar.yml` and `sonar-project.properties` are intentionally default-off: the scanner requires explicit repository variables, the disabled-Automatic-Analysis gate, and protected `main`. No token is provisioned, no external analysis setting is changed, and no scan is submitted.

The current-main readback is bounded: Automatic Analysis completed with Quality Gate `OK`; `producer=success` and `scanner=skipped` describe the inactive workflow posture and must not be interpreted as a CI scan result. This readback does not establish repository-wide zero Sonar issues.

As a bounded Task 4B.1 scope exception, `.gitleaksignore` contains exactly two path/rule/line fingerprints for the required public `sonar.projectKey` identifier; it suppresses no credential finding and does not alter scanner behavior.

Human-only follow-up remains: review token identity/lifecycle; read back Automatic Analysis enabled; disable it; read back disabled; then authorize the first controlled CI submission. A PR trusted-data bridge remains a separate blocked design task. The already-completed `private -> public` visibility change remains a bounded, owner-authorized remediation, not an analysis-method change.

Automatic and CI-based analysis must never run concurrently for the same Sonar project.

## P0-T11 / P0-T12 completed Rust reference line

The bounded CPU-only Rust reference work is complete and published on protected `main`:

- P0-T11 decoder-free reference core: PR #48 exact head `dfd6849cfc3c48e801f1e495239f2ec1ad810569`, hosted exact-head checks passed, squash merge `04342c859f790948fa784b72df940ac441ed5ed3`;
- P0-T12 decoder tensor primitives: PR #53 exact head `0ce6bb4ed39125c39c2b149ae6bf26688ec649cb`, hosted exact-head checks passed, squash merge `7962abe6c08a79da28e083735507fbae29529d74`;
- final local evidence at the P0-T12 publication head: 46 Rust tests, 371 Python tests, 230 focused Python tests, `cargo fmt --all --check`, locked Clippy with warnings denied, `make validate`, `make ci`, task-packet validation, simulation hash verification, diff-check and cleanup;
- hosted exact-head checks passed: `Validate and test`, `reference-core`, SonarCloud Code Analysis and GitGuardian Security Checks. `dependency-review` was skipped by the existing workflow configuration;
- independent final writable Codex review: `ACCEPT`, with no concrete findings. The review record is in `docs/reviews/P0-T11-CODEX-REVIEW-2026-08-20.md` and `docs/reviews/P0-T12-CODEX-REVIEW-2026-08-20.md`.

This evidence establishes only a bounded CPU reference implementation. It does not claim a production decoder, GPU/backend support, ABI stability, performance, scheduler, KV-cache, service, P1 or P2 completion.

## Established claims

Within the finite exact oracle and committed test families:

- modified rejection sampling recovers the target output law exactly;
- changing a valid draft distribution changes branch behavior but not the final target law;
- the greedy speculative oracle equals ordinary target greedy decoding;
- rejected speculative suffix state is not committed;
- cancellation restores the original token-prefix witness exactly;
- same-seed token identity is not the stochastic correctness criterion.

## Evidence boundaries

P0-T08 evidence is `finite_exact_reference`. It does not establish real-model, floating-point, KV-tensor, hardware, performance, distributed, or production behavior.

P0-T09 evidence is `quality_governance_read_only + ci_preparation`. It establishes the configured Automatic Analysis method, the historical PR-success/`main` GitHub-check-cancelled pattern, current `main@2339a8daa1c26aa13c043ef1739fa647352b60a5` Automatic Analysis `8b20603d-12a6-4d13-9d55-663d2c295384` with Quality Gate `OK`, Phase 0 and CodeQL success, the inactive workflow posture (`producer=success`, `scanner=skipped`), the immediate historical failure class `platform_limitation` with subtype `subscription_loc_limit_exceeded`, and the internal branch-analysis task status `FAILED`. ADR-0004 now selects `ci_based_only`; the evidence does not establish a CI scanner submission, token readiness, Automatic Analysis disablement, or final P0-T09 completion.

## Active and blocked work

### P0-T09

Status: `in_progress`. `E-P0-T09-01` classified the immediate failure as `platform_limitation / subscription_loc_limit_exceeded`; authenticated Background Tasks establishes internal status `FAILED`; owner-authorized visibility remediation is applied and independently verified public; Billing/admin evidence is materially complete. ADR-0004 is accepted as `ci_based_only`; `E-P0-T09-04B.1` is the merged default-off, inactive protected-ref preparation. P0-T09 remains open until the human-reviewed activation sequence and successful exact-head CI evidence are complete.

### P0-T04

`tasks/open/P0-T04-first-hardware-inventory.yaml` remains observation-only and blocked on a project-safe host label and execution mode.

### P0-T05 and P0-T06

They remain blocked behind the reviewed inventory and workload/SLO definitions.

### Future research

Transition Atlas and runtime conformance may use CA-03 as an oracle, but neither is authorized by S-0007.

## Forbidden next steps

- no external Sonar/GitHub analysis-setting mutation, Automatic Analysis disable, token provisioning, scanner activation, or scan submission from this preparation increment; these require the ordered human review and no-overlap evidence;
- no automatic and CI-based analysis concurrently;
- no token, private administrative payload, or hidden issue suppression in Git;
- no hardware benchmark before P0-T04 and P0-T05;
- no model download or production inference under P0-T09;
- no claim that finite exact semantics proves real-model or hardware behavior;
- no Transition Atlas, runtime, C ABI, backend, or kernel implementation without a new authorization packet.
