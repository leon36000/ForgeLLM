# SonarQube Cloud Main-Analysis Recovery Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` or `superpowers:executing-plans` after owner authorization. Do not change Sonar or GitHub configuration during the read-only diagnosis tasks. This plan preserves historical checkpoints, but accepted ADR-0004 supersedes the earlier proposed state for operative planning and selects `ci_based_only`.

**Goal:** Establish one reproducible SonarQube Cloud analysis method for ForgeLLM that reports a successful pull-request quality gate and a completed successful `main` analysis without suppressing findings.

**Architecture:** Separate completed evidence collection and method selection from implementation and closeout. Accepted ADR-0004 selects `ci_based_only`; Task 4A is rejected and inactive unless a later accepted ADR supersedes it. Task 4B first prepares a default-off protected-ref scanner path, then optionally adds a separately reviewed pull-request trusted-data bridge. Git stores the accepted method and sanitized proof, while Sonar remains an external evidence system.

**Tech stack:** GitHub REST/check APIs, SonarQube Cloud project UI/API, optional GitHub Actions and Sonar scanner only if CI-based analysis is selected, existing ForgeLLM Python validation tooling. No inference or hardware tooling.

## Global constraints

- No configuration change before owner authorization and a validated P0-T09 packet.
- Never enable automatic and CI-based analysis concurrently.
- Never commit a token or unsanitized administrative payload.
- Never suppress, accept, or exclude a finding merely to make a quality gate pass.
- Preserve protected `main`, Phase 0, CodeQL, GitGuardian, Dependency Review policy, and P0-T08 semantics.
- Pin any new third-party action to an immutable commit SHA.
- Treat absent, skipped, cancelled, or annotation-free checks as inconclusive rather than success.
- Record exact check, workflow, analysis-task, project-binding, and configuration identifiers.
- A token-bearing process never executes contributor-controlled commands, code, dependencies, build scripts, package-manager hooks, proc macros, tests, or binaries.
- Never use `pull_request_target`; disable automatic Clippy in the token-bearing scanner and import only bounded, validated reports produced without privileged credentials through trusted fixed paths.
- Inject `SONAR_TOKEN` only into the final approved scanner step. Workflow/job/container/service environments, same-repository or fork `pull_request` secret delivery, reusable-workflow forwarding, `secrets: inherit`, token propagation through outputs/state, and every earlier/later step are forbidden. Checkout, source/report acquisition, extraction, normalization and validation remain secretless, and no token-bearing post-processing is permitted.
- The eventual scanner job never checks out contributor-originated source and never executes repository-local actions/scripts or contributor-controlled action metadata. Source/reports enter only as validated data through a separately reviewed secretless transfer boundary. The final scanner step uses only an immutable reviewed external scanner action/invocation whose complete pre/main/post behavior is reviewed.
- `workflow_run` is forbidden for the current Sonar implementation. Any future PR trusted-data bridge that needs a privileged follow-up trigger requires a separate reviewed design update before that trigger may be introduced.
- Record immutable action SHA separately from scanner binary version and GPG/signature verification. The exact scanner archive digest remains an open limitation unless independently proven.

---

### Task 1: Freeze the observed failure matrix

**Files:**
- Create: `artifacts/governance/P0-T09-sonar-baseline.json`
- Create: `docs/quality/P0-T09-SONAR-BASELINE.md`

- [ ] Record PR #24 Sonar failure check `94869018087` and classify every published annotation by production/test code.
- [ ] Record remediation PR #25 check `94889986512` and its passed new-code measures.
- [ ] Record `main` failures `94890528740` and `94892860919`, including zero GitHub annotations.
- [ ] Record corresponding Phase 0 and CodeQL outcomes for each commit.
- [ ] Hash any screenshots or downloaded administrative payloads; do not commit raw private data.
- [ ] Validate the JSON artifact deterministically.
- [ ] Commit: `docs(quality): freeze Sonar failure matrix`.

### Task 2: Perform authenticated read-only Sonar diagnosis

**Files:**
- Modify: `artifacts/governance/P0-T09-sonar-baseline.json`
- Modify: `docs/quality/P0-T09-SONAR-BASELINE.md`

**Required readback:**

- project key and bound GitHub repository;
- organization/project binding status;
- Administration → Analysis Method state;
- last analysis method;
- automatic-analysis compatibility result;
- compute-engine/activity record for the failed `main` analysis where available;
- quality-gate definition and status;
- new-code definition;
- analysis-scope settings;
- project plan/tier limitations relevant to pull requests and branches;
- current permissions and token requirements without exposing credentials.

- [ ] Capture each field through authenticated UI or API with timestamp and sanitized evidence hash.
- [ ] Confirm repository search contains no scanner workflow or properties file outside the canonical tree.
- [ ] Confirm no external CI is submitting analyses to the same project.
- [ ] Classify the failure: configuration, binding/permission, source detection, platform limitation, transient service, or unknown.
- [ ] Stop and report `blocked` when evidence remains unavailable; do not guess.
- [ ] Commit: `docs(quality): classify Sonar main-analysis failure`.

### Task 3: Write the mutually exclusive analysis-method decision

**Status:** historical chronology completed. The earlier `proposed` checkpoint is retained; accepted ADR-0004 dated 2026-08-18 supersedes it for operative planning and selects `ci_based_only`.

**Files:**
- Create: `docs/adr/ADR-0004-sonarqube-analysis-method.md`
- Modify: `tasks/open/P0-T09-sonarqube-main-analysis.yaml`

- [ ] Compare `automatic_only` and `ci_based_only` against logs, coverage, secret surface, reproducibility, plan limits, and maintenance.
- [ ] Select exactly one method based on Task 2 evidence.
- [ ] Define rollback and failure conditions.
- [ ] Record whether a secret or third-party action is introduced.
- [ ] Record owner approval of the selected method.
- [ ] Run task-packet and ADR validation if available.
- [ ] Commit: `docs(adr): select Sonar analysis method`.

### Task 4A: Repair automatic analysis — conditional path

**Status:** rejected and inactive. Do not execute while accepted ADR-0004 selects `ci_based_only`. Retain this section as historical alternative analysis; it becomes operative only if a later accepted ADR explicitly supersedes ADR-0004.

**Possible files:**
- Create/Modify: `.sonarcloud.properties`
- Modify: `docs/quality/P0-T09-SONAR-BASELINE.md`
- Modify: `artifacts/governance/P0-T09-sonar-baseline.json`

- [ ] Verify no CI scanner workflow and no `sonar-project.properties` exists.
- [ ] Apply only the minimal supported automatic-analysis setting needed by the diagnosed cause.
- [ ] Record every Sonar UI setting before and after.
- [ ] Do not add unsupported wildcard/property behavior.
- [ ] Trigger a controlled pull-request analysis.
- [ ] Merge only after Phase 0, CodeQL, GitGuardian, and Sonar PR quality gate succeed.
- [ ] Verify the resulting `main` Sonar check completes with `success`.
- [ ] Roll back when `main` is cancelled/failed or binding changes unexpectedly.

### Task 4B: Migrate to CI-based analysis — conditional path

**Status:** operative under accepted ADR-0004. Preparation does not authorize token provisioning, Automatic Analysis mutation, scanner submission, or activation.

**Possible files:**
- Create: `.github/workflows/sonar.yml`
- Create: `sonar-project.properties`
- Modify: `.github/workflows/phase0.yml` only when required by an explicit gate decision
- Modify: `docs/quality/P0-T09-SONAR-BASELINE.md`
- Modify: `artifacts/governance/P0-T09-sonar-baseline.json`

#### Task 4B.0: Prove the semantic guard before scanner configuration

- [ ] Write unsafe fixtures and demonstrate RED for overlap, activation without disabled readback, direct same-repository/fork `pull_request` secret delivery, `pull_request_target`, `workflow_run`, workflow/job/container/service secret scope, reusable workflows with explicit secret forwarding or `secrets: inherit`, token propagation through outputs/state, reusable/composite/local actions receiving the token, repository-local scripts/actions in the scanner step, contributor-source checkout in the eventual scanner job, scanner/action pre/post hooks or any token-bearing post execution, token-bearing contributor-code execution, automatic Clippy, untrusted configuration/report paths, unbounded bridge inputs, and mutable/unverified scanner provenance.
- [ ] Implement the smallest semantic governance validator and demonstrate GREEN on safe fixtures while every unsafe fixture remains rejected.
- [ ] Complete this RED-to-GREEN proof before adding scanner workflow or properties configuration; syntax and grep checks alone do not satisfy the gate.

#### Task 4B.1: Prepare the protected-ref scanner path, inactive by default

- [ ] Prepare a protected trusted-ref token-bearing scanner path that is default-off and mechanically incapable of submission until activation.
- [ ] Source workflow, connection/project configuration, scanner source/version, token handling, and report paths only from trusted configuration that contributor content cannot override.
- [ ] Use least-privilege permissions. Any contributor-source checkout and source/report preparation occur only in a separate secretless producer boundary; the eventual scanner job never checks out contributor-originated source. Where checkout is used in a producer, use immutable action pins, non-persistent credentials and only sufficient attribution history.
- [ ] In the eventual scanner job, prohibit repository-local actions/scripts, reusable workflows, `secrets: inherit`, containers/services that receive the token, and any other contributor-controlled action metadata or executable path. The final scanner step must use only the reviewed immutable external scanner action/invocation, with its complete pre/main/post behavior reviewed.
- [ ] Disable automatic Clippy and duplicate ingestion. The token-bearing process executes no contributor-controlled commands, code, dependencies, build scripts, package-manager hooks, proc macros, tests, or binaries.
- [ ] Pin actions to immutable full commit SHAs. Separately pin the scanner binary version and verify its published GPG/signature chain. Do not claim an exact archive digest unless independently proven; carry it as an explicit open limitation.
- [ ] Bind `SONAR_TOKEN` only on the final approved scanner step. Prohibit workflow/job/container/service secret environments, direct PR secret delivery, reusable-workflow forwarding, `secrets: inherit`, outputs/state propagation, and all other step scopes; ensure source/report acquisition/extraction/normalization/validation complete before token injection; prohibit token-bearing post-processing and unreviewed action pre/post hooks.
- [ ] Fail clearly on secret absence without printing or probing the value.

Current implementation checkpoint: the protected-ref producer now transfers one fixed, immutable source/report artifact to the scanner. The governance validator requires the event-SHA checkout, exact artifact action pins and inputs, and a secretless scanner validation step that fails closed on symlinks; the final scanner remains default-off and no activation or submission has occurred.

Publication checkpoint: PR #67 merged this inactive preparation at protected `main@83f8ea624bc4382f22e2e168c5444df5304b189a`; post-merge Phase 0 and CodeQL passed, and the prepared Sonar workflow recorded `producer=success`, `scanner=skipped`. This does not close P0-T09.

#### Task 4B.2: Review token identity and lifecycle before provisioning

- [ ] Review identity, issuer/owner, minimum scope, storage boundary, rotation, expiry, revocation, audit trail, and incident response.
- [ ] Reject an owner/admin personal token chosen merely for convenience; prefer a dedicated least-privilege identity where supported.
- [ ] Only after review, store the value as `SONAR_TOKEN`; never record the value or private payload.

Pre-activation checkpoint 2026-08-22: [`artifacts/governance/P0-T09-token-lifecycle-review.json`](../../artifacts/governance/P0-T09-token-lifecycle-review.json) records `not_ready_for_activation`. The repository-scoped readback at protected `main@901667fe0dc5b20e5b97ef883c6659198202a2ae` confirms the `SONAR_TOKEN` secret name with update metadata `2026-08-22T08:08:16Z`; repository variables remain empty and no secret value was read. The recorded Free plan makes a Personal Access Token the documented candidate, but issuer, non-administrator permission, minimum scope, storage approval, expiry/rotation, revocation, audit and incident-response controls remain open. Secret presence alone is not activation approval; no Sonar setting, scanner activation or scan submission was performed by this checkpoint.

#### Task 4B.3: Separately design and review any PR trusted-data bridge

**Status:** blocked for the current implementation increment. `workflow_run` and `pull_request_target` are forbidden for Sonar. Task 4B.0/4B.1 may proceed for a protected trusted ref, but P0-T09 pull-request Sonar completion remains blocked until a separate reviewed bridge design is accepted.

- [ ] Treat the bridge as a separate implementation/review unit. Ordinary fork `pull_request` execution remains secretless and no privileged follow-up trigger is authorized by this plan revision.
- [ ] Run contributor code and Cargo/Clippy/coverage production only without privileged credentials.
- [ ] Before any privileged artifact consumer is authorized, specify and test an immutable binding over repository identity, trusted producer workflow identity and immutable workflow SHA, event type, run ID and attempt, PR number, PR head SHA, artifact ID/name, and expected producer commit.
- [ ] Require an independently recorded artifact digest before consumption; validate the binding and digest without `SONAR_TOKEN` before any extraction or scanner step.
- [ ] Define extraction into a new empty isolated directory and reject before extraction: duplicate/colliding names, absolute or escaping paths, symlinks, hardlinks, device/special files, excessive entry count, compression bombs, and per-file/aggregate compressed or expanded sizes above explicit limits.
- [ ] Allowlist exact artifact file names, media/types, encodings and schemas; reject unexpected files, executable or active content, configuration overrides, and any source capable of altering host, organization, project key, token handling, scanner binary/version, or trusted report paths.
- [ ] Any future consumer must acquire, validate, extract and normalize artifacts entirely without `SONAR_TOKEN`; the token is injected only into the final approved scanner step after all validation succeeds, with no token-bearing post-processing.
- [ ] If the complete bridge protocol is not independently accepted, defer Sonar proof to a protected trusted ref. An absent/skipped fork Sonar check is not success, and P0-T09 must remain open rather than weakening the trust boundary.

#### Task 4B.4: Activate with direct no-overlap evidence

- [ ] Independently accept the validator, prepared-inactive path, trusted configuration, token lifecycle, provenance, and any bridge.
- [ ] Complete token identity/lifecycle review without provisioning; then record Automatic Analysis enabled readback, the owner-authorized disable action, and disabled readback, in that order.
- [ ] Only after disabled readback, enable CI and permit the first submission; never infer state from the mutation request.
- [ ] Validate exact-head PR/trusted-ref and protected-`main` analyses while preserving other gates.
- [ ] On initial failure before material Rust analysis, stop submissions, prove CI inactive, and use only reviewed ADR-0004 rollback. After material Rust analysis, repair CI or adopt a later ADR.

### Task 5: Add governance regression checks

**Files:**
- Modify: `src/forgellm_governance/validation.py`
- Create: `tests/test_sonar_validation.py`
- Modify: `tests/test_validation.py` only if an existing general-validator regression requires it
- Modify: `Makefile` only if the dedicated Sonar test module is not already included by the existing test gate

- [ ] Add a failing test that detects simultaneous automatic-analysis configuration assumptions and a committed CI scanner configuration when mechanically observable.
- [ ] Add a test requiring pinned third-party actions in a Sonar workflow.
- [ ] Add a test preventing committed token values or suspicious Sonar credential names outside GitHub secret references.
- [ ] Add semantic tests for the Task 4B trust split, default-off state, ordered activation evidence, automatic-Clippy disablement, trusted fixed paths, bounded bridge data, and distinct action-SHA/scanner-binary provenance.
- [ ] Add task-packet validation to `make validate`.
- [ ] Preserve every existing repository gate.
- [ ] Commit: `test(quality): guard Sonar analysis method`.

### Task 6: Verify pull-request evidence

**Files:**
- Modify: `artifacts/governance/P0-T09-sonar-baseline.json`
- Create: `docs/reviews/P0-T09-SONAR-MAIN-ANALYSIS-REVIEW.md`

- [ ] Run complete `make ci` on the exact final implementation head.
- [ ] Require CodeQL success.
- [ ] Require GitGuardian success.
- [ ] Characterize Dependency Review honestly.
- [ ] Require Sonar PR check `success`, with issue/hotspot counts recorded, only after the separate trusted-data bridge design and implementation are independently accepted. Until then this step is blocked and must not be satisfied by `workflow_run`, `pull_request_target`, a direct secret-bearing contributor workflow, or an absent/skipped check.
- [ ] Request a fresh configuration/security review.
- [ ] Reject any hidden issue suppression, unpinned action, excessive permission, or mixed analysis method.
- [ ] Commit review evidence only after exact-head checks.

### Task 7: Verify `main` analysis and close out

**Files:**
- Modify: `artifacts/governance/P0-T09-sonar-baseline.json`
- Modify: `docs/reviews/P0-T09-SONAR-MAIN-ANALYSIS-REVIEW.md`
- Modify after evidence: `tasks/open/P0-T09-sonarqube-main-analysis.yaml`
- Modify after evidence: state, handoff, roadmap, and mobile projection allowed by the packet

- [ ] Merge the implementation PR only after Task 6 acceptance.
- [ ] Require post-merge Phase 0 and CodeQL success.
- [ ] Require Sonar `main` check `success`; `cancelled`, `skipped`, absent, or generic failure is not acceptable.
- [ ] Record Sonar analysis task ID and quality-gate status when available.
- [ ] Repeat one additional controlled PR/main cycle if the original failure was classified transient.
- [ ] Close issue #26 only after reproducibility is demonstrated.
- [ ] Archive P0-T09 and advance state in a separate reviewed closeout PR.

## Verification commands

```bash
python scripts/validate_task_packet.py tasks/open/P0-T09-sonarqube-main-analysis.yaml --root .
python -c "import yaml; yaml.safe_load(open('tasks/open/P0-T09-sonarqube-main-analysis.yaml', encoding='utf-8'))"
# Before scanner configuration: prove the semantic validator RED on unsafe fixtures, then GREEN on safe fixtures.
make ci
git grep -n -E 'pull_request_target|SONAR_TOKEN|sonar\.projectKey|sonar\.scm\.revision|sonarcloud|sonarqube|sonar\.rust\.clippy' -- . ':!docs/quality/*' ':!tasks/*'
git diff -- tasks/open/P0-T09-sonarqube-main-analysis.yaml docs/superpowers/plans/2026-08-14-sonarqube-main-analysis.md
git diff --check
git status --short
```

Authenticated evidence commands are selected after method diagnosis and must avoid printing credentials. Typical read-only endpoints may include project status, compute-engine activity, project branches, and project binding metadata. Store sanitized output or hashes, not raw private payloads.

## Completion report

The final report records:

1. owner authorization and selected method;
2. diagnosis evidence and failure classification;
3. exact settings before/after;
4. secret/action/permission changes;
5. complete and focused validation outputs;
6. PR and `main` Sonar check/task IDs;
7. Phase 0, CodeQL, GitGuardian, and Dependency Review outcomes;
8. quality-gate counts and remaining baseline debt;
9. rollback evidence;
10. explicit non-claims and next task.

Until implementation evidence exists, state explicitly whether scanner configuration, token provisioning, Automatic Analysis disablement, trusted-data bridge, CI activation, or scanner submission exists. If a secret is added before the lifecycle gate is complete, record only sanitized presence metadata and keep activation blocked. List the exact scanner archive digest as unresolved unless independently proven; do not conflate it with the action SHA or scanner version/GPG verification.
