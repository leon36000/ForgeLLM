# ForgeLLM Handoff

**From state:** S-0015
**To work:** complete the bounded P0-T16 CPU reference decoder slice; P0-T09 remains inactive and human-gated, P0-T04 still awaits host designation
**Generated:** 2026-08-27

## P0-T10 integration handoff

P0-T10's bounded implementation is present at public merge commit 87a1ddeb76d2bca45fe75853b4c3b4c9f19c78b0 from f8364f12402c3c58796dbc1b56f8c65d378e88de. Its receipt is reproducible from protected `main`, but lifecycle status is `review`: ADR-0005 remains `proposed` and the required final architecture/security acceptance record is absent. Do not treat the implementation merge or historical agent/Terra approval as ADR acceptance; do not execute upstream installers, runners, hooks, or any P0-T09, hardware, runtime, or external administrative operation.

## Canonical status

- repository: `leon36000/ForgeLLM`;
- protected default branch: `main`;
- P0-T07: complete;
- P0-T08 / CA-03: complete;
- P0-T09 / QG-01: owner-authorized and `in_progress`, scanner inactive;
- P0-T10: `review`, publicly merged at `main@87a1dde`, ADR-0005 proposed;
- P0-T13: complete and publicly merged at `main@ad079c0`;
- P0-T14: complete after protected merge `c1fd915`, with lifecycle validation and projections reconciled; its canonical source anchor is the protected merge snapshot;
- P0-T16: `in_progress`, bounded in-memory CPU dense decoder reference slice; no model, runtime, backend, ABI or GPU work;
- P0-T15: `in_progress`, design-only, publicly merged at `main@9932a5a`, ADR-0006 proposed;
- P0-T11/P0-T12: bounded Rust CPU reference line complete and merged on `main`;
- P0-T04: blocked only on owner host designation;
- P0-T05/P0-T06: blocked behind inventory and workload/SLO gates;
- no model, runtime, backend, kernel, or Transition Atlas implementation is authorized.

## P0-T14 lifecycle reconciliation

P0-T14 reconciles the task directories and state projections under issue #73. P0-T03 has one canonical closed packet; P0-T10 is open with status `review` while ADR-0005 is `proposed`; P0-T13 is closed and complete after its protected merge; P0-T15 is open with status `in_progress` while ADR-0006 is `proposed`; and P0-T14 is closed and complete only for the bounded validator/projection work. After the PR #80 squash, the canonical source anchor is the protected snapshot `c1fd915…`; the post-merge repair preserves the ancestry gate and synchronizes the projections. P0-T16 is the next bounded CPU reference slice and is currently `in_progress`; it has no model, runtime, backend, ABI or GPU scope. The validator rejects directory/status inversions, duplicate IDs, unresolved dependencies and invalid ADR successor metadata, and it verifies the canonical state ID/source commit, generated mobile manifest, README block and exact tracked-path tree. The derived projections are rebuildable and never replace Git state as authority.

## P0-T09 authorization and source

```text
Owner command           autorise P0-T09 / subagent-driven
Recorded date           2026-08-14
Initial base            1b1a3621fcdf4129268663c497cdcd53aed48c29
Verified pre-change main 26a0a66bbbc3c5e3f6e68ed379e074ca06da47f5
Tracking issue          #26
Task packet             tasks/open/P0-T09-sonarqube-main-analysis.yaml
```

## Post-merge main readback

The pre-merge canonical `main@4dec19558d076af03ee2bee45482a3f83a2b6f33` included the merged inactive preparation from PR #58 and PR #60. Its Automatic Analysis was `55533f96-c27b-480a-8e1f-f820bbced2f3` with public Quality Gate `OK`; the committed Sonar workflow was default-off with `producer=success` and `scanner=skipped`.

After PR #61, historical `main@2339a8daa1c26aa13c043ef1739fa647352b60a5` had Automatic Analysis `8b20603d-12a6-4d13-9d55-663d2c295384` with Quality Gate `OK`. Phase 0 run `32437158659` and CodeQL run `32437158653` succeeded; prepared workflow run `32437158674` completed with `producer=success` and `scanner=skipped`.

Verified pre-change evidence anchor after PR #62: protected `main@26a0a66bbbc3c5e3f6e68ed379e074ca06da47f5` had Automatic Analysis `2a0d79e4-bbb1-4536-b1e6-6351ab2ef56d` with Quality Gate `OK`. Phase 0 run `32438425091` and CodeQL run `32438425096` succeeded; prepared inactive workflow run `32438425087` completed with `producer=success` and `scanner=skipped`. These are Automatic Analysis and inactive-workflow readbacks, not a CI scanner submission; the merge SHA created by this final documentation synchronization is not claimed as verified by this snapshot.

The readback is not a repository-wide zero-issues claim; baseline debt and any remaining findings require their own versioned evidence and disposition.

## Analysis Method now confirmed

The owner supplied an authenticated screenshot of **SonarQube Cloud → ForgeLLM → Analysis method**.

Observed values:

```text
Automatic analysis      enabled
Recommendation          Recommended
CI method selected      no
```

The raw screenshot is not committed. Its sanitized transcription is stored in:

```text
artifacts/governance/P0-T09-sonar-analysis-method-readback.json
```

with SHA-256 evidence binding:

```text
bfab677e68396b0452bf6348be773e974a3f4325768b080961a0f5e936f7e5e1
```

This is the historical platform readback: Automatic Analysis was enabled and no CI method was selected at that time. The later accepted ADR-0004 selects `ci_based_only` for the durable architecture; Automatic Analysis remains active until the reviewed no-overlap migration sequence.

## Post-import probe

The owner imported the project into SonarQube Cloud and P0-T09 executed a new probe:

```text
PR #30 head             3bc75c6496953a4a13fece88d6547c2b1de520bd
PR Sonar                94945852247 / success / 0 new issues
main merge              bd03e479ff4649a254c41726b33f2b6e841a0e0c
main Sonar              94946081665 / cancelled / 0 annotations
```

Phase 0 and CodeQL succeeded on the probe path. Therefore project import alone did not repair the `main` analysis failure.

## 2026-08-17 independent read-only diagnosis

At the 2026-08-17 diagnostic snapshot, the canonical repository was verified clean at then-current `main@484fec34007fd89f554c9c03bffa9a5275676602`, matching `origin/main` and the GitHub `main` head. Isolated Codex, Claude Code, and OpenHands reviews independently converged on the same result without repository modifications.

A fifth recurrence is visible after PR #31:

```text
PR #31 head             a2d68d910e270fe15f590808de5041814a416b1f
PR Sonar                94948153214 / success
then-current main       484fec34007fd89f554c9c03bffa9a5275676602
main Sonar GitHub check 94948378776 / conclusion cancelled / 0 annotations
Phase 0                 success
CodeQL                  success
```

The reviews also established an important evidence boundary: GitHub check conclusion `cancelled` does **not** establish the internal Sonar background-task status. The internal task may be failed, cancelled, superseded, or otherwise terminated; only authenticated Sonar activity/task evidence can classify it.

Sanitized session evidence is recorded in:

```text
artifacts/governance/P0-T09-readonly-diagnosis-2026-08-17.json
```

A prior controller-browser attempt found no authenticated Sonar session, so it captured no administration values and changed no settings. The owner subsequently supplied authenticated Sonar UI screenshots directly: one exposes the subscription LOC-limit error and analysis ID, and a second Background Tasks screenshot establishes the internal branch-analysis task status as `FAILED`.

## Current classification

```text
analysis_method_setting automatic_enabled
compatibility           recommended
failure_classification  platform_limitation
failure_subtype         subscription_loc_limit_exceeded
analysis_id             472eadb9-b554-47ca-8336-2033fb3b7408
background_task_id      AaADNoZ4U0I7o8og6Mb6
internal_task_status    FAILED
method_selection        ci_based_only
configuration_changes   sonar_visibility_private_to_public_only
```

## Current block

Experiment **`E-P0-T09-01`** is now classified by owner-authenticated Sonar UI evidence: the analysis failed because total lines of code in the organization exceed the current subscription limit. The screenshot exposes analysis ID `472eadb9-b554-47ca-8336-2033fb3b7408`; the raw image is not committed and its hash-bound sanitized transcription is stored in the diagnosis artifact.

A second owner-provided Background Tasks screenshot shows a branch analysis task `AaADNoZ4U0I7o8og6Mb6` with internal status `FAILED`, submitted/started at 22:18:20 and finished at 22:18:23, immediately after pull-request task `AaADNKJHGgg5GiBgCda_` succeeded from 22:16:16 to 22:16:18. Public GitHub correlation strongly maps this pair to PR #31 and current `main`: assuming the Sonar UI timestamps are UTC−04:00, their finish times match checks `94948153214` and `94948378776` exactly to the second, and the checks point to `pullRequest=31` and `branch=main`. This remains strong correlation rather than definitive ID binding because GitHub exposes no Sonar background-task ID.

Independent remediation reviews then established:

```text
CI-based analysis bypasses LOC limit      no
justified ForgeLLM source exclusions      none identified
ForgeLLM maintained non-test Python       ~5k physical lines
```

Switching scanners is not a remedy for the diagnosed subscription limit, and adding exclusions merely to reduce billing would violate QG-01.

The owner subsequently authenticated manually in the isolated OpenClaw browser. A targeted before/after readback verified `ForgeLLM / leon36000_ForgeLLM` was Private while bound to the already-public GitHub repository and using Automatic Analysis. The then-current P0-T09 packet still contained a broad no-Sonar/GitHub-setting freeze before ADR-0004; the owner-directed visibility change is recorded as a bounded exception to that packet, not as retroactive authorization by the pre-change packet. Under a local single-use approval recorded outside Git, OpenClaw changed **only** Project visibility from `Private` to `Public - Anyone`; project key, GitHub binding and Automatic Analysis remained unchanged.

Independent anonymous Sonar Web API reads then returned HTTP 200 and confirmed:

```text
visibility                         public
binding                            https://github.com/leon36000/ForgeLLM
automatic analysis                 enabled
historical visibility revision     d5cd25bd9d6fc3f9cded27781c2051939dcdde85
historical visibility ncloc        1658
historical quality gate            OK / Sonar way
post-remediation main              86f32319847a011fb4d48c98f0c467282fcfbe49
post-remediation ncloc             6939
post-remediation quality gate      OK / Sonar way
canonical GitHub main at readback  484fec34007fd89f554c9c03bffa9a5275676602
```

Billing & usage after the change reports:

```text
plan                           Free
private LOC entitlement        50000
private LOC consumed           48248
remaining                      approximately 1.8k
```

The organization is therefore back below the private-LOC limit. The historical final readback also records binding `leon36000/ForgeLLM`, New Code `previous_version`, no custom analysis-scope or issue-ignore values, Automatic Analysis/Autoscan, no CI method selected at that time, and the default `Sonar way` Quality Gate. Post-remediation Automatic Analysis later succeeded on exact `main@86f32319847a011fb4d48c98f0c467282fcfbe49` with `ncloc=6939`; the pre-merge `main@4dec19558d076af03ee2bee45482a3f83a2b6f33`, post-merge `main@2339a8daa1c26aa13c043ef1739fa647352b60a5`, and verified pre-change `main@26a0a66bbbc3c5e3f6e68ed379e074ca06da47f5` readbacks are recorded above. The accepted ADR-0004 governs the merged repository preparation; no artificial probe commit or external activation is authorized in this increment.

## Decision gate after readback

The organization LOC blocker has been remediated by the smallest evidence-supported action: align ForgeLLM Sonar visibility with its already-public canonical repository. No source exclusion, project deletion, subscription purchase or analysis-method change was needed.

Next gate (not executed or authorized by this documentation increment): obtain explicit independent review and authorization for the no-overlap migration sequence. Automatic Analysis remains enabled and the prepared CI scanner remains inactive.

If separately authorized, complete the separate token identity/lifecycle security review without reading or rotating `SONAR_TOKEN`; then capture the sequence in order: fresh Automatic Analysis enabled readback; owner-authorized disable action; Automatic Analysis disabled readback. Require another explicit gate before CI activation or the first controlled submission.

Until those gates are satisfied: the repository secret may exist, but no token value is read or used, no Sonar or GitHub setting is changed, no scanner is activated, no scan is submitted, and no PR bridge is introduced. P0-T09 remains `in_progress`.

## P0-T09 local checkpoint: secretless artifact boundary

The prepared protected-ref path now has a concrete same-run data boundary. The producer uses the immutable checkout pin with `repository: ${{ github.repository }}` and `ref: ${{ github.sha }}`, non-persistent credentials, and the pinned Rust 1.97.1 toolchain. It copies only `src` and `crates`, generates the Clippy JSON report without `SONAR_TOKEN`, and uploads exactly `forgellm-sonar-input` with the reviewed upload-artifact pin.

The scanner downloads that fixed artifact first, validates the fixed source/report paths, rejects symlinks, and then invokes the final immutable Sonar action. The governance validator and 53 focused Sonar tests reject missing or mutable transfer pins, wrong artifact paths/names, checkout ref/repository overrides, and removal of the symlink guard. This is still default-off preparation: the repository secret name is present but its value is not read or used, no Sonar/GitHub setting is changed, no scan is submitted, and no PR bridge is designed or activated.

The official action provenance is recorded in `CURRENT_STATE.md`; no scanner archive digest is claimed.

## P0-T09 publication evidence

PR #67 exact head `a58ee2f0a705f73bcc769330547f1b6bb7de6a67` merged as protected `main@83f8ea624bc4382f22e2e168c5444df5304b189a`. PR checks passed for Phase 0 validation, CodeQL, SonarCloud Code Analysis and GitGuardian; Dependency Review was `SKIPPED`. Post-merge runs passed: Phase 0 `32532087564`, CodeQL `32532087569`, and prepared Sonar workflow `32532087558`, whose producer succeeded and scanner was skipped by the default-off/Automatic-Analysis gate.

This is exact-head repository and inactive-workflow evidence, not a Sonar CI submission. No token was provisioned, Automatic Analysis was not changed, and no PR bridge was introduced.

## P0-T09 token identity/lifecycle pre-activation checkpoint

`artifacts/governance/P0-T09-token-lifecycle-review.json` records the fresh pre-activation review as `not_ready_for_activation`. The repository-scoped `gh secret list` readback confirms the `SONAR_TOKEN` secret name and update metadata `2026-08-22T08:08:16Z`; `gh variable list` is empty, and no secret value was read. This repository-level readback does not establish token validity, issuer, scope, lifecycle controls, or organization- and environment-level secret state.

The review prefers a Scoped Organization Token when supported by the plan, but the recorded project plan is Free; the documented Free-plan candidate is therefore a Personal Access Token. Issuer, non-administrator permission, minimum scope, storage approval, expiry/rotation, revocation, audit and incident-response controls remain open. The secret’s presence alone does not authorize activation. The official SonarQube Cloud [Scoped Organization Token](https://docs.sonarsource.com/sonarqube-cloud/administering-sonarcloud/scoped-organization-tokens), [Personal Access Token](https://docs.sonarsource.com/sonarqube-cloud/managing-your-account/managing-tokens), and [GitHub Actions secret](https://docs.github.com/en/actions/concepts/security/secrets) documentation is recorded in the artifact.

No token value was read or recorded, and no Sonar setting, GitHub setting, scanner activation or scan submission was performed by this checkpoint. The next gate remains the ordered enabled-readback → owner-authorized disable action → disabled-readback sequence.

## Loop Engineering cycle 3/3: final snapshot stop

```text
GOAL:
  Record the final verified pre-change evidence anchor after PR #62 and stop
  the documentation loop without chasing the SHA created by this sync.

SCOPE:
  The same four P0-T09 state/roadmap/task files only.
  No workflow, source, test, secret, setting, token, scan, or external mutation.

VERIFY:
  Exact anchor 26a0a66…; Phase 0 32438425091; CodeQL 32438425096;
  prepared Sonar workflow 32438425087 with producer success/scanner skipped;
  Automatic Analysis 2a0d79e4… targeting the anchor with Quality Gate OK;
  packet validation, make validate, make ci, diff-check, and clean status.

BUDGET:
  Third and final documentation synchronization; no fourth SHA-chasing cycle.

STOP:
  After this candidate is reviewed and merged, do not create another
  documentation-only synchronization solely for its new merge SHA. Resume only
  after material activation/evidence/status change or substantive error.

RECEIPT:
  verified_pre_change_anchor: 26a0a66bbbc3c5e3f6e68ed379e074ca06da47f5
  pre_change_gate: GPT-5.6-Sol — GO for the final snapshot scope
  limitations: Automatic Analysis remains active; no token; no CI submission;
               P0-T09 remains open; P0-T10 remains blocked
  next_step: independent no-overlap review and authorization; no fourth sync
```

ADR-0004 is accepted and selects exactly `ci_based_only`. Task 4B.1 prepares the protected-ref scanner path only; the workflow remains default-off while Automatic Analysis is active. CI-based analysis does not bypass the subscription entitlement, and the two methods may never run concurrently. The pre-activation token identity/lifecycle review, the ordered Automatic Analysis disable/readback, first CI submission, and successful exact-head evidence remain independent follow-up gates.

As a bounded Task 4B.1 scope exception, `.gitleaksignore` contains exactly two path/rule/line fingerprints for the required public `sonar.projectKey` identifier; it suppresses no credential finding and does not alter scanner behavior.

## Loop Engineering receipt: documentation synchronization

```text
GOAL:
  Synchronize the P0-T09 state with canonical main@4dec195…, PR #58/#60,
  Automatic Analysis 55533f96…, and the inactive workflow posture without activation.

SCOPE:
  tasks/open/P0-T09-sonarqube-main-analysis.yaml
  docs/roadmap/PHASE0_TASKS.md
  docs/state/CURRENT_STATE.md
  docs/state/HANDOFF.md
  No workflow, source, test, secret, setting, token, scan, or external mutation.

VERIFY:
  make validate; task-packet validation; exact-scope diff check; diff --check;
  post-change readback of the main SHA, Automatic Analysis/QG, producer/scanner
  posture, open P0-T09 status, and blocked P0-T10 status.

BUDGET:
  At most 3 documentation correction cycles; external-mutation budget 0.

STOP:
  Stop if the diff leaves the four-file scope, a fact is unavailable, activation
  becomes necessary, the same failure repeats, or the correction budget is exhausted.

RECEIPT:
  base_sha: 4dec19558d076af03ee2bee45482a3f83a2b6f33
  reviewed_head_sha: e7f698f8149e10aeeeeb0e84dfa137b505378b05
  receipt_commit: e7f698f8149e10aeeeeb0e84dfa137b505378b05 (receipt introduced by the reviewed iteration)
  writer: Codex chief architect
  pre_change_gate: GPT-5.6-Sol, read-only scope gate — GO
  exact_head_gate: GPT-5.6-Sol / Hypatia, read-only exact-head gate — NO-GO
  findings: stale canonical anchor; unsupported unversioned issue claims; pre-signed GO
             did not represent the exact-head result
  commands/results: make validate=0; make ci=0 (378 tests, 230 focused tests);
                    direct packet validation with PYTHONPATH=src=0; diff-check=0
  evidence: PR #58/#60 merged; Automatic Analysis 55533f96…; Quality Gate OK;
            producer success; scanner skipped
  limitations: Automatic Analysis remains enabled; no token; no CI scan submission;
               P0-T09 remains open; P0-T10 remains blocked by unresolved MAJOR findings
  next_step: correct the exact-head findings, obtain a fresh Sol review, then proceed
             only to the human-only no-overlap activation sequence; no activation in this loop
```

## Rust reference closeout

The current protected `main` contains the completed P0-T11/P0-T12 reference line. PR #48 merged at `04342c859f790948fa784b72df940ac441ed5ed3` from exact head `dfd6849cfc3c48e801f1e495239f2ec1ad810569`; PR #53 merged at `7962abe6c08a79da28e083735507fbae29529d74` from exact head `0ce6bb4ed39125c39c2b149ae6bf26688ec649cb`.

The final exact-head evidence is 46 Rust tests, 371 Python tests, 230 focused Python tests, formatting, locked Clippy with warnings denied, `make validate`, `make ci`, packet validation, simulation hash verification, diff-check and cleanup. Hosted `Validate and test`, `reference-core`, SonarCloud and GitGuardian checks passed; dependency review was skipped by the existing workflow. Independent writable Codex review accepted both implementation packets after a scope finding was corrected.

This line is CPU-only reference work. The next work remains P0-T09's human-gated CI activation/evidence sequence, plus P0-T04 host designation; no production runtime, GPU/backend, ABI, performance, KV-cache, service, P1 or P2 claim follows from these merges.

## Exact oracle preserved

Future implementations must continue to use CA-03 as their correctness oracle. P0-T09 may not alter speculative-decoding semantics to satisfy a scanner.

## Evidence limits

P0-T09 now establishes Automatic Analysis enabled/recommended, the repeated PR-success/`main` failure pattern, internal branch-task status `FAILED`, direct failure classification `platform_limitation / subscription_loc_limit_exceeded`, owner-authorized visibility remediation, anonymous proof that ForgeLLM is now public, post-change private LOC below the Free entitlement, and accepted ADR-0004 selection of `ci_based_only`. It does **not** yet establish a healthy CI Sonar analysis on current GitHub `main`, token readiness, Automatic Analysis disablement, or final P0-T09 completion.
