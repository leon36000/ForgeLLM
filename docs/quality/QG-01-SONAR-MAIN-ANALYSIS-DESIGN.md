# QG-01 — SonarQube Cloud Main-Branch Analysis Design

- **Status:** proposed design; no configuration change authorized
- **Date:** 2026-08-14
- **Candidate task:** P0-T09
- **Tracking issue:** #26
- **Repository evidence boundary:** quality-governance and integration diagnostics only

## Problem statement

ForgeLLM has repeatable pull-request analysis but an inconsistent automatic-analysis result on the protected `main` branch.

Observed evidence:

- P0-T08 implementation PR #24 exposed actionable Sonar findings.
- The two production-code findings were corrected in remediation PR #25.
- PR #25 Sonar check `94889986512` passed with zero new issues, zero accepted issues, and zero security hotspots.
- The remediation merge `e81c1c0ad0b161844569df46ee62246c9de56698` passed Phase 0 and CodeQL, but Sonar automatic `main` check `94890528740` was cancelled / reported as analysis failed without GitHub annotations.
- The S-0007 closeout merge `e669f5e1a6913005fbba8d34e9ba8bdfce91c460` reproduced the same discrepancy through Sonar check `94892860919` while Phase 0 succeeded.

The failure therefore cannot be declared a code defect or an integration defect without authenticated Sonar project evidence. The current conclusion is only: **PR analysis is healthy; automatic `main` analysis is not demonstrated healthy.**

## Primary documentation constraints

SonarQube Cloud documents two mutually exclusive analysis methods for a project:

1. automatic analysis, executed by SonarQube Cloud from the bound GitHub repository;
2. CI-based analysis, executed by a scanner in the build environment.

The official automatic-analysis documentation states that the methods are not intended to run concurrently and that CI-based analyses fail when automatic analysis is enabled. It also states that automatic-analysis logs are not available; projects needing logs should use CI-based analysis.

Primary references:

- <https://docs.sonarsource.com/sonarqube-cloud/advanced-setup/automatic-analysis>
- <https://docs.sonarsource.com/sonarqube-cloud/analyzing-source-code/ci-based-analysis/overview-of-integrated-cis>
- <https://docs.sonarsource.com/sonarqube-cloud/appendices/troubleshooting>
- <https://docs.sonarsource.com/sonarqube-cloud/administering-sonarcloud/about-sonarqube-cloud-solution/ressources-structure/binding-with-dop>

These constraints prohibit a trial configuration that leaves both methods active.

## Goals

- Determine the actual SonarQube Cloud project binding and selected analysis method.
- Obtain sufficient authenticated evidence to explain or classify the `main` analysis failure.
- Select exactly one analysis method through an explicit decision gate.
- Make pull-request and `main` results reproducible and truthfully reported.
- Preserve Phase 0, CodeQL, GitGuardian, dependency policy, branch protection, and the P0-T08 exactness boundary.
- Avoid accepting, suppressing, or excluding findings merely to make a quality gate green.

## Non-goals

- Modify speculative-decoding semantics.
- Change test expectations or lower a quality gate.
- Add broad exclusions for source or test files without an independently reviewed justification.
- Expose a Sonar token, project administration payload, email, or operational identifier.
- Run model inference, hardware probes, benchmarks, runtime, ABI, backend, or kernel work.
- Claim repository-wide zero Sonar issues from a clean pull-request new-code gate.

## Current repository observations

The repository has no committed Sonar scanner workflow, `sonar-project.properties`, or `.sonarcloud.properties` in the canonical tree. Sonar checks are supplied by the installed SonarQube Cloud GitHub integration. This supports, but does not prove, that automatic analysis is selected.

The evidence required to decide is outside the Git tree:

- project **Administration → Analysis Method** readback;
- project binding and key readback;
- project activity / compute-engine status for the failed `main` analysis;
- quality-gate and new-code definitions;
- organization/project permissions relevant to analysis execution.

## Candidate approaches

### Approach A — Preserve automatic analysis

Use this only when the project is confirmed bound to the correct repository, automatic analysis is the only configured method, and the failure is diagnosable or transient without scanner logs.

Possible actions after diagnosis:

- repair project binding or analysis-scope configuration in the Sonar UI;
- add a minimal `.sonarcloud.properties` file only for supported automatic-analysis settings;
- trigger a controlled pull-request and `main` analysis pair;
- preserve screenshots/API readback and check-run identifiers.

Advantages:

- no repository secret or scanner workflow;
- simple pull-request decoration;
- minimal maintenance.

Limitations:

- automatic-analysis logs are unavailable;
- no coverage import;
- less control over runtime and scanner configuration;
- diagnosis may remain insufficient if Sonar reports only a generic failure.

### Approach B — Migrate to CI-based analysis

Use this only after automatic analysis is explicitly disabled in the Sonar project and a reviewed GitHub Actions design is approved.

Required properties:

- one pinned Sonar scanner action or verified scanner invocation;
- least-privilege `SONAR_TOKEN` stored as a GitHub secret;
- pull-request and `main` triggers;
- full Git history where required for analysis attribution;
- explicit project key and organization values through non-secret configuration;
- logs retained in GitHub Actions;
- no simultaneous automatic analysis.

Advantages:

- reproducible scanner version and logs;
- potential coverage and external-report import;
- explicit branch/pull-request execution.

Costs and risks:

- new secret and third-party action surface;
- additional supply-chain and permissions review;
- workflow maintenance;
- automatic analysis must be disabled before the first scanner submission.

### Rejected approach — Run both methods

Rejected because SonarQube Cloud documents the methods as conflicting. Duplicate or competing analyses would make the control plane less trustworthy.

## Recommended decision process

### Gate 1 — Read-only diagnosis

No repository or Sonar setting is changed.

Collect:

- canonical Git commit and check-run IDs;
- Analysis Method readback;
- project/repository binding;
- failed-analysis task/status/message from authenticated UI or API;
- quality-gate and new-code definition;
- current project/organization plan limitations;
- confirmation that no CI scanner exists in any protected workflow or external CI.

Classify the failure as one of:

- configuration;
- binding/permission;
- scope/source detection;
- automatic-analysis platform limitation;
- transient service failure;
- unknown due to unavailable evidence.

### Gate 2 — Method selection

A short ADR or reviewed decision records exactly one method:

- `automatic_only`, or
- `ci_based_only`.

The decision includes rollback, secret implications, supported evidence, and why the alternative was rejected.

### Gate 3 — Bounded implementation

Implement only the selected method. Every setting change is recorded before/after. No issue suppression is permitted without a separate disposition record.

### Gate 4 — Verification

Require two independent cycles:

1. a pull request with Phase 0, CodeQL, GitGuardian, and Sonar result;
2. the resulting `main` commit with Phase 0, CodeQL, and a completed Sonar result.

The Sonar `main` result must be `success`, not merely absent, cancelled, skipped, or inferred from the pull request.

## Evidence model

A machine-readable closeout artifact should contain:

- repository and project identifiers in sanitized form;
- selected analysis method;
- exact configuration commit;
- Sonar check/task identifiers for pull request and `main`;
- quality-gate outcome and issue counts as reported;
- Phase 0, CodeQL, GitGuardian, and Dependency Review outcomes;
- any remaining baseline debt;
- explicit non-claims;
- screenshots or API payload hashes where raw administrative evidence cannot be published.

## Security and privacy controls

- Never commit `SONAR_TOKEN` or authenticated API responses containing user data.
- Prefer scoped organization tokens over broad personal credentials when CI-based analysis is selected.
- Record only sanitized project identifiers already public through GitHub checks.
- Pin every third-party action to an immutable commit SHA.
- Keep workflow permissions read-only unless a documented Sonar requirement proves otherwise.
- Treat the Sonar UI and API as evidence sources, not canonical project state; Git records the accepted decision and sanitized proof.

## Acceptance boundary

QG-01 is complete only when the selected method produces a successful Sonar pull-request result and a successful Sonar `main` result on reviewed commits, with no method conflict and no hidden issue suppression.

Until then, S-0007 must continue to say that Sonar `main` analysis is unresolved.