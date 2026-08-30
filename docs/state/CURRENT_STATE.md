# ForgeLLM Current State

- **State ID:** S-0017
- **Updated:** 2026-08-29
- **Canonical source commit:** `cc5a90d0190bf84e3124a7e81bbe52bc7d0820bc`
- **Phase:** P0
- **Milestone:** P0-M8 — bounded reference attention coverage
- **Overall status:** P0-T07, P0-T08/CA-03, P0-T11/P0-T12, P0-T13, P0-T14, P0-T16, P0-T17, P0-T18, P0-T19 and the bounded P0-T20 implementation are complete in this candidate; P0-T10 remains in `review` because ADR-0005 is still `proposed`; P0-T15 remains `in_progress` as a design-only task with ADR-0006 `proposed`; P0-T09/QG-01 remains active and its scanner is inactive. P0-T04 remains blocked on designation of one owner-authorized host.
- **Authorized next work:** Reconcile the exact candidate with independent review, hosted required checks and protected merge, then capture post-merge evidence. Do not accept ADR-0005 or ADR-0006 from merged design/integration evidence alone. P0-T09 remains under its independent no-overlap/token lifecycle gates; do not read `SONAR_TOKEN`, change Sonar/GitHub settings, activate CI, submit a scan, or run hardware/model/runtime work.
- **State anchor:** the Git commit containing this file

- **Latest protected-main baseline for P0-T20:** `main@cc5a90d0190bf84e3124a7e81bbe52bc7d0820bc` (PR #89 P0-T19 closeout); P0-T17/P0-T18/P0-T19 are protected and complete, while the P0-T20 candidate remains isolated pending review.

`Canonical source commit` identifies the protected-main snapshot read when this state projection was reconciled. The validator requires that snapshot to be present and ancestral, so a squash merge cannot leave a branch-only source commit in the projection. The derived mobile manifest below hashes the exact canonical source files used for the projection and is non-authoritative.

## P0-T14 lifecycle reconciliation

- P0-T03 has one canonical `complete` packet under `tasks/closed`; its stale open duplicate was removed.
- P0-T10 remains under `tasks/open` with status `review`. ADR-0005 remains `proposed`; the final Sol gate found that explicit architectural acceptance evidence is still missing. The implementation merge at `main@87a1dde` is not treated as ADR acceptance.
- P0-T13 is under `tasks/closed` with status `complete`, backed by protected merge `ad079c0bf6f86b044f1d1d819cb105e3afe5a65f` and its post-merge validation.
- P0-T14 is under `tasks/closed` with status `complete` at the reconciled protected snapshot `c1fd91536031fd9b2fbc24b71095bd4a0c8d0e66`; the post-merge source-anchor repair is recorded in its review.
- P0-T16 is under `tasks/closed` with status `complete`; it delivers one in-memory CPU dense decoder token composed from the existing checked reference operations, with no model, runtime, ABI, backend or GPU scope.
- P0-T15 remains under `tasks/open` with status `in_progress`; ADR-0006 remains `proposed` and the merged increment contains no ABI header, symbol, FFI, backend or runtime implementation.
- The validator rejects directory/status inversions, duplicate IDs, unresolved dependencies and unresolved ADR successors; it also validates the README block, mobile manifest and exact tracked-path tree.

## P0-T10 integration status

The P0-T10 implementation is present at public merge commit 87a1ddeb76d2bca45fe75853b4c3b4c9f19c78b0 from canonical base f8364f12402c3c58796dbc1b56f8c65d378e88de. Its receipt and review input bind to that public commit. The ADR-0005 integration adds only an inert pinned vendor subset, a ForgeLLM-owned bounded bridge, and repository-native receipts/validation; P0-T09 and hardware/runtime boundaries remain unchanged. Lifecycle status is now `review`, not `complete`, because ADR-0005 remains `proposed` and the required final architecture/security acceptance record is absent. The Sol gate explicitly rejected treating the implementation merge as architectural acceptance.

## P0-T13 privacy closeout

P0-T13 is complete under protected merge `ad079c0bf6f86b044f1d1d819cb105e3afe5a65f` (PR #78). The fail-closed public-artifact sanitizer and snapshot privacy boundary passed the post-merge focused suite (`34` tests), full suite (`487` tests), speculative suite (`230` tests), packet validation, Ruff, diff-check and cleanup. No real host probe or inventory publication occurred.

## P0-T15 design-only checkpoint

P0-T15 is an `in_progress` design task under `tasks/open/P0-T15-versioned-c-abi-design.yaml`. Its protected merge `9932a5a496df53e812d9f47c6bb95ae94b3a4a2f` contains only the proposed ADR-0006, source review, bounded implementation plan, task packet and review record. ADR-0006 remains `proposed`; no ABI header, symbol, binding, runtime, backend or C/C++ implementation is authorized by this state.

## P0-T16 bounded CPU dense decoder slice

P0-T16 is complete in the closed packet `tasks/closed/P0-T16-dense-decoder-reference.yaml`. The public `dense_decode_single_token` composition consumes a checked embedding table and projection plus RMSNorm parameters, then returns the first-index greedy argmax after softmax. Its independent synthetic oracle and typed failure tests establish only a small CPU reference slice; real-model conformance, tokenization, model formats, attention, KV cache, scheduling, runtime, ABI, backend, GPU and performance remain future gates.

## P0-T17 / P0-T18 / P0-T19 protected reference increments

- P0-T17 is complete: the Rust reference workspace is part of the repository CI gate and its protected closeout is recorded in `tasks/closed/P0-T17-rust-reference-ci-gate.yaml` and `docs/quality/P0-T17-RUST-CI-GATE.md`.
- P0-T18 is complete at its protected implementation/closeout sequence (`03c4bee` then `d50cd7e`): the stdlib-only Fraction/Decimal oracle, deterministic fixture, restricted reader and differential contract cover the existing reference operations without a production dependency.
- P0-T19 is complete at protected implementation/closeout `e26072f`/`cc5a90d`: rank-two transpose and single-query scaled dot-product attention are CPU-only reference operations. Multi-query row-wise attention was explicitly deferred to P0-T20.

## P0-T20 bounded multi-query attention

P0-T20 adds `attention_decode_multi_query` for caller-supplied finite tensors with shapes `[query_count, head_dim]`, `[context_len, head_dim]`, and `[context_len, head_dim]`. It gives every query row an independent scaled score row and flat-softmax call, then performs the checked weighted-sum matmul. The candidate has no causal-mask policy, multi-head layout, RoPE, KV-cache management, runtime/backend/ABI integration, model, hardware or performance scope. Its local candidate evidence records 12 focused Rust tests, 60 focused oracle tests, 563 full Python tests, 230 speculative tests and 101 Rust tests in `make ci`; the closed packet and state projections are synchronized, while independent review, exact PR-head checks and protected merge remain pending.

## Objective

Preserve the exact speculative-decoding oracle as the correctness reference for later cache-aware, accelerator and runtime implementations while restoring a reproducible and truthful SonarQube Cloud quality signal for protected `main`.

## Canonical repository

- Repository: `leon36000/ForgeLLM`.
- Default branch: protected `main`.
- Initial P0-T09 base: `1b1a3621fcdf4129268663c497cdcd53aed48c29`.
- Verified pre-change evidence anchor: protected `main@26a0a66bbbc3c5e3f6e68ed379e074ca06da47f5`.
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

Post-remediation Automatic Analysis then succeeded on `main@86f32319847a011fb4d48c98f0c467282fcfbe49`; the anonymous readback matched that exact revision, reported Quality Gate `OK`, public visibility, and `ncloc=6939`. Historical readbacks after PR #61 and PR #62 recorded `main@2339a8daa1c26aa13c043ef1739fa647352b60a5` / Automatic Analysis `8b20603d-12a6-4d13-9d55-663d2c295384` and verified pre-change `main@26a0a66bbbc3c5e3f6e68ed379e074ca06da47f5` / Automatic Analysis `2a0d79e4-bbb1-4536-b1e6-6351ab2ef56d`, each with Quality Gate `OK`, Phase 0 and CodeQL success, and prepared workflow `producer=success`, `scanner=skipped`. These are Automatic Analysis readbacks, not CI activation. The merge SHA created by this final documentation synchronization is not claimed as verified by this snapshot.

### Task 4B.1 preparation boundary

The historical evidence, owner-authorized visibility remediation, administrative readback, accepted ADR-0004, and merged inactive preparation now establish the current repository state. ADR-0004 selects exactly `ci_based_only`; it does not authorize external activation in this increment.

The prepared `.github/workflows/sonar.yml` and `sonar-project.properties` are intentionally default-off: the scanner requires explicit repository variables, the disabled-Automatic-Analysis gate, and protected `main`. The repository secret name is present, but the scanner remains inactive because the lifecycle and no-overlap gates are unresolved; no token value was read, no external analysis setting was changed, and no scan was submitted.

The verified-anchor readback is bounded: Automatic Analysis completed with Quality Gate `OK`; `producer=success` and `scanner=skipped` describe the inactive workflow posture and must not be interpreted as a CI scan result. This readback does not establish repository-wide zero Sonar issues.

As a bounded Task 4B.1 scope exception, `.gitleaksignore` contains exactly two path/rule/line fingerprints for the required public `sonar.projectKey` identifier; it suppresses no credential finding and does not alter scanner behavior.

Independent follow-up remains: complete the pre-activation identity/lifecycle review without reading or rotating the secret; read back Automatic Analysis enabled; perform the owner-authorized disable action; read back disabled; then authorize the first controlled CI submission. A PR trusted-data bridge remains a separate blocked design task. The already-completed `private -> public` visibility change remains a bounded, owner-authorized remediation, not an analysis-method change.

Automatic and CI-based analysis must never run concurrently for the same Sonar project.

### P0-T09 secretless artifact-boundary checkpoint

This checkpoint makes the protected-ref preparation internally coherent without activating it. The producer checks out `${{ github.repository }}` at `${{ github.sha }}` with the pinned checkout action, shallow history and non-persistent credentials; installs the repository-pinned Rust toolchain; copies only `src` and `crates` into `.sonar-input/source`; generates `.sonar-input/reports/clippy.json` with Cargo/Clippy without `SONAR_TOKEN`; and publishes exactly the fixed `forgellm-sonar-input` artifact with pinned `actions/upload-artifact`.

The scanner consumes only that same-run artifact through pinned `actions/download-artifact` as its first step. Its secretless validation requires the fixed source/report paths and rejects symlinks before the final immutable Sonar action, which alone receives `SONAR_TOKEN`. `SONAR_ARTIFACT_BOUNDARY` rejects missing, mutable, mismatched or reordered transfer steps, missing symlink rejection, and checkout ref/repository overrides. No token, external setting change, CI activation, scan submission or PR bridge was introduced; P0-T09 remains `in_progress`.

Action provenance reviewed 2026-08-21 from the [official upload-artifact v7.0.1 release](https://github.com/actions/upload-artifact/releases/tag/v7.0.1) and [official download-artifact v8.0.1 release](https://github.com/actions/download-artifact/releases/tag/v8.0.1): commits `043fb46d1a93c77aae656e7c1c64a875d1fc6a0a` and `3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c`, respectively. The scanner archive digest remains an explicit open limitation.

Publication evidence for this checkpoint: PR #67 exact head passed Validate and test (`32531975996`), SonarCloud Code Analysis, CodeQL (`96925821594`), and GitGuardian; Dependency Review was terminal `SKIPPED`. The resulting protected `main@83f8ea624bc4382f22e2e168c5444df5304b189a` passed Phase 0 run `32532087564`, CodeQL run `32532087569`, and the prepared inactive Sonar run `32532087558` with `producer=success` and `scanner=skipped`. These checks prove workflow preparation and repository gates only; they do not prove token readiness, Automatic Analysis disablement, CI scanner activation, or a Sonar CI submission.

### P0-T09 token identity/lifecycle pre-activation checkpoint

The historical pre-provisioning review is superseded by a fresh repository-scoped readback at protected `main@901667fe0dc5b20e5b97ef883c6659198202a2ae`: the `SONAR_TOKEN` secret name is present with update metadata `2026-08-22T08:08:16Z`, while repository variables remain empty. The secret value was not read. This does not establish token validity, issuer, scope, expiry, rotation, revocation, organization- or environment-level secret state.

The review prefers a Scoped Organization Token when the plan supports it because SonarQube Cloud documents it as non-user-specific, project-scoped and limited to Execute Analysis. The recorded project plan is Free, for which the official setup documentation identifies a Personal Access Token as the candidate; the issuing identity, non-administrator permission, minimum scope, storage approval, expiry, rotation, revocation, audit trail and incident-response controls remain open. The repository secret was added before those controls were independently recorded, so it is not an activation approval. The [official Scoped Organization Token documentation](https://docs.sonarsource.com/sonarqube-cloud/administering-sonarcloud/scoped-organization-tokens), [Personal Access Token documentation](https://docs.sonarsource.com/sonarqube-cloud/managing-your-account/managing-tokens), and [GitHub Actions secret guidance](https://docs.github.com/en/actions/concepts/security/secrets) are recorded as the review sources.

This documentation checkpoint changes no Sonar or GitHub setting, does not read or record `SONAR_TOKEN`, and does not activate or submit a scanner. The ordered no-overlap readbacks remain the next external gate; P0-T09 stays `in_progress`.

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

P0-T09 evidence is `quality_governance_read_only + ci_preparation`. It establishes the configured Automatic Analysis method, the historical PR-success/`main` GitHub-check-cancelled pattern, verified pre-change `main@26a0a66bbbc3c5e3f6e68ed379e074ca06da47f5` Automatic Analysis `2a0d79e4-bbb1-4536-b1e6-6351ab2ef56d` with Quality Gate `OK`, Phase 0 and CodeQL success, the inactive workflow posture (`producer=success`, `scanner=skipped`), the immediate historical failure class `platform_limitation` with subtype `subscription_loc_limit_exceeded`, and the internal branch-analysis task status `FAILED`. ADR-0004 now selects `ci_based_only`; the evidence does not establish a CI scanner submission, token readiness, Automatic Analysis disablement, or final P0-T09 completion. The merge SHA created by this final documentation synchronization is outside this snapshot’s verification anchor.

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
