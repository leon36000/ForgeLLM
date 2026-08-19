# SonarQube Cloud Main-Analysis Recovery Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` or `superpowers:executing-plans` after owner authorization. Do not change Sonar or GitHub configuration during the read-only diagnosis tasks.

**Goal:** Establish one reproducible SonarQube Cloud analysis method for ForgeLLM that reports a successful pull-request quality gate and a completed successful `main` analysis without suppressing findings.

**Architecture:** Separate evidence collection, method selection, implementation, and closeout. The first stage is read-only and must classify the failure using authenticated Sonar project evidence. A decision gate then selects `automatic_only` or `ci_based_only`; the two implementations are mutually exclusive. Git stores the accepted method and sanitized proof, while Sonar remains an external evidence system.

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

Execute only when ADR-0004 selects `automatic_only`.

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

### Task 4B: Migrate to CI-based analysis — selected path

ADR-0004 is accepted and selects `ci_based_only`. The canonical Task 4B base is the Task 3 merge `8594ef5abb19ca7a870fe6d71ae7aad8e15f4602`. Current Automatic Analysis is a proven pre-migration fallback only; it must remain the only submitting Sonar method until the controlled activation boundary below.

**Files:**
- Create/Modify: `.github/workflows/sonar.yml`
- Create `sonar-project.properties` only if a parameter cannot be kept in trusted workflow arguments without losing reproducibility; do not place authentication or critical connection controls there.
- Modify: `docs/quality/P0-T09-SONAR-BASELINE.md`
- Modify: `artifacts/governance/P0-T09-sonar-baseline.json`
- Modify: `tasks/open/P0-T09-sonarqube-main-analysis.yaml`
- Modify this plan when execution evidence invalidates an assumption.

**Interfaces:**
- Consumes: accepted ADR-0004, `SONAR_TOKEN`, repository variable `FORGELLM_SONAR_CI_ENABLED`, exact GitHub pull-request metadata resolved immediately before dispatch, and the public Sonar project identity `leon36000_ForgeLLM` / organization `leon36000`.
- Produces: one guarded CI scanner workflow whose disabled state cannot submit analysis, whose protected-`main` job runs only on a `main` push, and whose PR job can run only through `workflow_dispatch` from the workflow already stored on default `main`, with repository-owner actor and exact PR metadata guards.

#### Stage 4B.1: Commit an inert, reviewable scanner scaffold

- [ ] Reconfirm `main == 8594ef5abb19ca7a870fe6d71ae7aad8e15f4602` or rebase the execution plan before writing.
- [ ] Record the Task 3 post-merge evidence before changing analysis method: Sonar main check `95933687884` success, exact Sonar revision `8594ef5abb19ca7a870fe6d71ae7aad8e15f4602`, Quality Gate `OK`, `ncloc=6939`, Phase 0 run `32207542577` success, CodeQL run `32207542554` success, and 67 open new-code issues that remain debt rather than a zero-issue claim.
- [ ] Preserve the rejected preparation experiment: the first inert scaffold used ordinary same-repository `pull_request`. It was safe while `FORGELLM_SONAR_CI_ENABLED` was absent/false, but is rejected for activation because a same-repository PR can modify the workflow definition that would receive repository secrets. Ref ownership does not make the workflow or checked-out source trusted.
- [ ] Create `.github/workflows/sonar.yml` with no `pull_request`, `pull_request_target`, or `workflow_run` trigger. Use `push` limited to `main` plus `workflow_dispatch` with required inputs `pr_number:number`, `head_sha:string`, and `head_ref:string`.
- [ ] Split the workflow into exactly two token-bearing scanner jobs. The `main` job requires the enable variable, `github.event_name == 'push'`, and `github.ref == 'refs/heads/main'`. The PR job requires the enable variable, `github.event_name == 'workflow_dispatch'`, `github.ref == 'refs/heads/main'`, and `github.actor == github.repository_owner`.
- [ ] Treat `github.actor == github.repository_owner` as a fail-closed project-specific gate. If ForgeLLM later moves to an organization-owned repository, this expression must be replaced through reviewed governance before PR dispatch can run; do not weaken it implicitly.
- [ ] For a dispatched PR, resolve `pr_number`, exact `head_sha`, `head_ref`, and target branch from canonical GitHub immediately before dispatch. Verify the PR is still open, targets `main`, and the supplied head SHA/ref still equal GitHub readback; stale or mismatched metadata blocks dispatch.
- [ ] Checkout PR source by exact `${{ inputs.head_sha }}` only. Pass Sonar PR identity explicitly as trusted workflow arguments: `sonar.pullrequest.key=${{ inputs.pr_number }}`, `sonar.pullrequest.branch=${{ inputs.head_ref }}`, and `sonar.pullrequest.base=main`. Never accept an arbitrary base branch input.
- [ ] Set workflow permissions to exactly `contents: read`. Do not add write permissions unless a later primary-source requirement and independent security review prove one necessary.
- [ ] Before checkout, add a trusted static preflight step that receives `secrets.SONAR_TOKEN` only in that step and fails with `SONAR_TOKEN is not configured` when empty without printing the value.
- [ ] Pin checkout to `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1`, set `persist-credentials: false`, and set `fetch-depth: 0`.
- [ ] Pin the scanner action to `SonarSource/sonarqube-scan-action@22918119ff8e1ca75a623e15c8296b6ea4fbe28f` and pin its scanner input to `8.1.0.6389` unless fresh primary-source verification shows that exact immutable pair is no longer acceptable.
- [ ] Pass critical controls as trusted scanner arguments, not repository-controlled project configuration: `sonar.host.url=https://sonarcloud.io`, `sonar.organization=leon36000`, `sonar.projectKey=leon36000_ForgeLLM`, `sonar.sca.enabled=false`, `sonar.rust.clippy.enable=false`, `sonar.qualitygate.wait=true`, and `sonar.qualitygate.timeout=300`.
- [ ] Keep `SONAR_TOKEN` step-scoped to the fixed preflight/scanner steps. No build, package-manager, test, Cargo, Clippy, proc-macro, dependency, or contributor-provided command may execute in a token-bearing scanner job.
- [ ] Treat checked-out source as untrusted scanner input even when the dispatch itself is trusted. The scanner may parse source but must not invoke project code, dependencies, package hooks, or build tooling in the token-bearing context.
- [ ] Do not generate Rust Clippy or coverage reports in the scanner job. When Rust enters the analyzed tree, generate required reports in a separate secretless job and import only bounded validated report paths; avoid duplicate Clippy ingestion.
- [ ] Explicitly keep initial SCA disabled. Current ForgeLLM Free-plan evidence has no SCA surface, while Sonar documents `sonar.sca.enabled=true` as the scanner default when Advanced Security is active and may invoke build tools. Enabling SCA later requires a separate reviewed threat model; `false` here preserves rather than weakens the current surface.
- [ ] Complete Task 5 regression guards and independent security review before merging the scaffold. During preparation, the absence of a `Sonar CI` PR run is expected because the secret-bearing workflow has no `pull_request` trigger; that absence is not classified as success. Current Automatic Analysis remains the sole submitting method.
- [ ] Commit scaffold preparation separately from activation so rollback never depends on editing an unreviewed workflow under time pressure.

#### Stage 4B.2: Prove the credential and transition controls before activation

- [ ] Read back the actual Sonar organization/project permission model with owner-authenticated evidence. The candidate credential is a dedicated analysis identity whose PAT has only the effective project permission required for `Execute Analysis`; reject an owner/admin PAT used merely for convenience.
- [ ] If Free-plan permissions cannot isolate a usable analysis identity without unnecessary administrative privilege, stop activation and record the blocker. Do not buy/upgrade a plan or broaden confidentiality/administration without separate explicit owner approval.
- [ ] Store the approved value only as the GitHub Actions secret `SONAR_TOKEN`; record secret name, identity class, permission evidence, creation/rotation policy, and hashes/sanitized screenshots without recording the value.
- [ ] Keep `FORGELLM_SONAR_CI_ENABLED` absent/false after secret provisioning. Verify no dispatch or push scanner can submit and Automatic Analysis is still enabled.
- [ ] Obtain an exact before-state readback for Automatic Analysis, project binding, visibility, Quality Gate, current main revision and the enable-variable state.

#### Stage 4B.3: Cross the mutually-exclusive activation boundary

- [ ] Disable Automatic Analysis first. Read it back as disabled before permitting any CI scanner submission.
- [ ] Set repository variable `FORGELLM_SONAR_CI_ENABLED=true` only after Automatic is confirmed disabled and `SONAR_TOKEN` is proven present/sanitized.
- [ ] Open a controlled same-repository PR targeting `main` whose changes do not modify the already-merged Sonar workflow. Resolve the PR number, exact current head SHA/ref and base from GitHub immediately before each dispatch.
- [ ] Invoke `workflow_dispatch` on the workflow stored on protected `main`, as the repository owner/trusted controller, passing only the verified PR number, head SHA and head ref. Re-read the PR after dispatch and reject evidence if the head changed during the run.
- [ ] Require the dispatched PR scanner job to complete and fail the workflow on a red Quality Gate via `sonar.qualitygate.wait=true`. Also require Phase 0, CodeQL and GitGuardian success; characterize Dependency Review by its actual terminal result.
- [ ] Record the workflow run, Sonar task/analysis identifier, exact PR head, Quality Gate, issue/hotspot counts, action/scanner SHAs and the absence of secret leakage. Do not call a skipped/absent check success.
- [ ] Merge only after fresh configuration/security review accepts the exact implementation and dispatched-evidence boundary.
- [ ] Require the resulting protected `main` push to trigger the `main` scanner job automatically, and require both its GitHub check and Sonar revision to equal the merge commit with Quality Gate success.

#### Stage 4B.4: Kill-switch rollback

- [ ] On activation failure, set `FORGELLM_SONAR_CI_ENABLED=false` first and verify no CI scanner submission is active or can start.
- [ ] Only after the CI path is inert may Automatic Analysis be re-enabled, and only before Rust requires CI-only coverage under ADR-0004. Record before/after state and the failure cause.
- [ ] If Rust is already materially analyzed, do not use Automatic as steady-state rollback while Rust remains ineligible; repair CI or supersede ADR-0004 through review.
- [ ] Do not delete evidence or remove failing findings to make rollback green.

### Task 5: Add governance regression checks before Task 4B activation

Task 5 moves ahead of Stage 4B.3 as a security prerequisite. Use strict TDD: each new policy must first fail on a minimal fixture, then pass after the smallest validator change.

**Files:**
- Modify: `src/forgellm_governance/validation.py`
- Modify: `tests/test_validation.py`
- Do not modify `Makefile`: canonical `make validate` already runs `scripts/validate_project_state.py` (which calls `validate_project()`) and validates the active P0-T09 task packet.

**Interfaces:**
- Consumes: repository workflow text under `.github/workflows/*.yml` and the selected Sonar CI markers above.
- Produces: `validate_project()` errors that make `make validate`/`make ci` reject unsafe Sonar workflow states before activation.

- [ ] Require no secret-bearing Sonar `pull_request`, `pull_request_target`, or `workflow_run` trigger.
- [ ] Require `push` targeting `main` and `workflow_dispatch` with required typed inputs `pr_number`, `head_sha`, and `head_ref`.
- [ ] Require exactly the `main` and `pull_request` scanner jobs with the enable guard. Require the main job's push/main guards and the dispatch job's workflow-dispatch/main-ref/repository-owner guards.
- [ ] Require the dispatched PR checkout to use exactly `${{ inputs.head_sha }}` and require the three explicit Sonar PR parameters with hardcoded `base=main`.
- [ ] Require exactly `contents: read`, immutable full-SHA action references, `persist-credentials: false`, and `fetch-depth: 0` in both scanner jobs.
- [ ] Require trusted markers `sonar.sca.enabled=false`, `sonar.rust.clippy.enable=false`, `sonar.qualitygate.wait=true`, exact public project key/organization/host, and a non-empty pinned scanner version.
- [ ] Require scanner auth to use exactly `secrets.SONAR_TOKEN` and reject every non-preflight `run:` command in a token-bearing scanner job.
- [ ] Preserve regression tests for forbidden `pull_request_target`, unsafe self-hosted PR workflows, action pinning, and existing guarded workflows.
- [ ] Add a positive fixture for the reviewed trusted-dispatch workflow and prove `validate_project()` returns no Sonar-policy issue.
- [ ] Run strict RED/GREEN through the exact PR CI, then run the complete test suite, `make validate`, `make ci`, `git diff --check`, and secret-pattern grep.
- [ ] Preserve every existing repository gate and keep P0-T04/P0-T05 untouched.
- [ ] Commit: `test(quality): guard trusted Sonar dispatch`.

### Task 6: Verify pull-request evidence

**Files:**
- Modify: `artifacts/governance/P0-T09-sonar-baseline.json`
- Create: `docs/reviews/P0-T09-SONAR-MAIN-ANALYSIS-REVIEW.md`

- [ ] Run complete `make ci` on the exact final implementation head.
- [ ] Require CodeQL success.
- [ ] Require GitGuardian success.
- [ ] Characterize Dependency Review honestly.
- [ ] Require the controlled trusted-dispatch Sonar PR run to complete successfully on the exact verified PR head, with issue/hotspot counts recorded.
- [ ] Request a fresh configuration/security review.
- [ ] Reject any hidden issue suppression, unpinned action, excessive permission, mixed analysis method, stale dispatch metadata, or secret-bearing workflow definition taken from untrusted PR content.
- [ ] Commit review evidence only after exact-head checks.

### Task 7: Verify `main` analysis and close out

**Files:**
- Modify: `artifacts/governance/P0-T09-sonar-baseline.json`
- Modify: `docs/reviews/P0-T09-SONAR-MAIN-ANALYSIS-REVIEW.md`
- Modify after evidence: `tasks/open/P0-T09-sonarqube-main-analysis.yaml`
- Modify after evidence: state, handoff, roadmap, and mobile projection allowed by the packet

- [ ] Merge the implementation PR only after Task 6 acceptance.
- [ ] Require post-merge Phase 0 and CodeQL success.
- [ ] Require the protected-main CI Sonar check `success`; `cancelled`, `skipped`, absent, or generic failure is not acceptable.
- [ ] Record Sonar analysis task ID and quality-gate status when available.
- [ ] Repeat one additional controlled PR/main cycle if the original failure is classified transient.
- [ ] Close issue #26 only after reproducibility is demonstrated.
- [ ] Archive P0-T09 and advance state in a separate reviewed closeout PR.

## Verification commands

```bash
python scripts/validate_task_packet.py tasks/open/P0-T09-sonarqube-main-analysis.yaml --root .
make ci
git grep -n -E 'SONAR_TOKEN|sonar\.projectKey|sonarcloud|sonarqube' -- . ':!docs/quality/*' ':!tasks/*'
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