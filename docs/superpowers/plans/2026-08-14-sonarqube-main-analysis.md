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

### Task 4B: Migrate to CI-based analysis — conditional path

Execute only when ADR-0004 selects `ci_based_only`.

**Possible files:**
- Create: `.github/workflows/sonar.yml`
- Create: `sonar-project.properties`
- Modify: `.github/workflows/phase0.yml` only when required by an explicit gate decision
- Modify: `docs/quality/P0-T09-SONAR-BASELINE.md`
- Modify: `artifacts/governance/P0-T09-sonar-baseline.json`

- [ ] Disable automatic analysis in the Sonar project before the first CI scanner submission.
- [ ] Create a least-privilege scoped Sonar token and store it only as `SONAR_TOKEN` in GitHub Actions secrets.
- [ ] Pin scanner/action and checkout dependencies to immutable commit SHAs.
- [ ] Use read-only workflow permissions unless the official scanner requirement proves otherwise.
- [ ] Configure pull-request and protected `main` triggers.
- [ ] Fetch sufficient Git history for Sonar attribution.
- [ ] Expose project key/organization only through public configuration; never print the token.
- [ ] Add secret-absence behavior that fails clearly without leaking values.
- [ ] Validate workflow syntax and repository automation policy.
- [ ] Run a controlled PR and then `main` analysis.
- [ ] Roll back and re-enable the previous method only through a reviewed decision if CI analysis fails.

### Task 5: Add governance regression checks

**Files:**
- Modify: `src/forgellm_governance/validation.py`
- Modify/Create: `tests/test_validation.py`
- Modify: `Makefile`

- [ ] Add a failing test that detects simultaneous automatic-analysis configuration assumptions and a committed CI scanner configuration when mechanically observable.
- [ ] Add a test requiring pinned third-party actions in a Sonar workflow.
- [ ] Add a test preventing committed token values or suspicious Sonar credential names outside GitHub secret references.
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
- [ ] Require Sonar PR check `success`, with issue/hotspot counts recorded.
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