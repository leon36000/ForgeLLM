# ForgeLLM Current State

- **State ID:** S-0004
- **Updated:** 2026-08-13
- **Phase:** P0
- **Milestone:** P0-M3 — public repository boundary accepted and hardening underway
- **Overall status:** P0-T03 in progress; public visibility is owner-approved under ADR-0003, public-data controls and review evidence are complete, hosted gates pass, and `main` protection remains the blocking owner-admin control
- **Authorized next task:** P0-T03
- **State anchor:** the Git commit containing this file

## Objective

Complete the public GitHub control-plane hardening before any self-hosted hardware or private asset plane is connected.

## Canonical remote and direct evidence

- Repository: `leon36000/ForgeLLM`.
- Visibility: `public`, directly reported by GitHub on 2026-08-13.
- Default branch: `main`.
- Main commit before P0-T03: `843f8127f76a0c7f2ef9863853dccaddeff90aa8`.
- Main direct evidence: `protected=false`; required-status-check enforcement `off`; no contexts/checks.
- Repository rulesets direct evidence: empty list.
- Branch-protection administrative endpoint: `403 Resource not accessible by integration`.
- Actions default/selected permission endpoints: `403 Resource not accessible by integration`.
- Code-scanning alert endpoint: `403 Resource not accessible by integration`.

The previous private-visibility statements are superseded by ADR-0003 and this state. The repository was already public; the owner intentionally retains that boundary for public tooling.

## Owner decision and operating boundary

Issue #8 and ADR-0003 accept a public source/governance repository. Every Git-tracked byte, issue, PR, workflow log and artifact is treated as public and permanently copyable.

Secrets, restricted weights, private datasets/prompts, unredacted traces, private network details and stable device identifiers are forbidden. A future private asset plane requires its own bounded task and is referenced publicly only through opaque IDs, revisions and hashes.

Git remains canonical. Neon or another RAG may index the repository later, but it is derived and cannot override ADRs, state, evidence or history. NVIDIA, AMD, Temporal, SonarQube, Consensus and other integrations require least privilege and task-specific data review.

## P0-T03 verified implementation evidence

Reviewed implementation head: `9d3b47365aa017f37b16a6f8c7e307677a7526cf`.

### Phase 0 verification

- run: `31681837631`;
- job: `94388820133`;
- conclusion: success;
- Ruff passed;
- project, research, benchmark, P0-T02 and P0-T03 task validation passed;
- exact five-file mobile hashing passed;
- **17 tests passed**;
- Ubuntu bootstrap dry-run passed;
- workflow token permissions were contents/read and metadata/read.

### CodeQL

- run: `31681837665`;
- job: `94388813356`;
- conclusion: success;
- CodeQL Action 4.37.6 / CLI 2.26.2;
- 62 Python modules extracted;
- 52 `security-extended` queries executed;
- SARIF uploaded and processing completed;
- alert details remain inaccessible and therefore unknown.

### Dependency Review

- capability probe run `31681032967`, job `94386280488`: failed because Dependency Graph is disabled; no dependency finding was produced;
- reviewed-head run `31681837651`: skipped by the explicit opt-in guard.

Dependency Review remains non-required until the owner enables Dependency Graph and obtains one successful internal PR run.

### Fresh-context review

`docs/reviews/P0-T03-PUBLIC-REPOSITORY-REVIEW.md` records verdict `ACCEPT` for the governance PR while preserving P0-T03 as `in_progress`.

The review found and resolved an audit false positive: a nonempty but unrelated/disabled ruleset can no longer be treated as protection for `main`. Direct `branches/main.protected=true` is required for the audit pass.

## P0-T03 implemented changes

- ADR-0003 and decisions D-0008/D-0009;
- public repository/data-classification policy and public security reporting entry point;
- contribution and no-license notices;
- expanded secret/restricted-asset ignore rules;
- typed read-only repository audit and reviewed branch-protection payload;
- tests for public visibility, inaccessible admin controls, unrelated rulesets and solo-owner protection semantics;
- honest recording of Dependency Graph and CodeQL-alert visibility limitations;
- S-0004 decisions, risks, roadmap, handoff and mobile projection.

## P0-T03 remaining blocking gates

Before P0-T03 can complete, direct evidence must show `main` protected by classic protection or an enforced equivalent ruleset that:

- requires pull requests;
- requires the stable `Validate and test` check;
- requires conversation resolution;
- enforces the owner/admin path;
- rejects force pushes and branch deletion;
- uses zero fabricated human approvals while the project is solo.

The current integration cannot perform or read that administrative write. `scripts/github/apply_branch_protection.py` provides a reviewed dry-run/apply command for an owner-authenticated `gh` session.

Optional security follow-ups:

- enable Dependency Graph before opt-in Dependency Review;
- inspect CodeQL alerts through an owner-authorized UI or CLI;
- capture Actions administrative permissions directly.

## External-tool applicability

- GitHub, CodeQL and Codex Engineering Guardrails: used for P0-T03.
- SonarQube: relevant only when a callable server/project is configured; no Sonar result is claimed.
- Fallow: not applicable to the current Python/Markdown surface.
- Consensus: reserved for bounded scientific synthesis tasks.
- Neon Postgres: candidate derived RAG only after a dedicated ADR/task.
- Temporal: candidate for durable agent orchestration after workflow semantics are specified.
- NVIDIA/AMD skills: reserved for protected hardware/backend phases.

## Evidence boundary

This state proves directly observed repository metadata and completed hosted jobs only. It does not prove protected `main`, readable Actions settings, zero CodeQL alerts, Dependency Review success, runner safety, an open-source license or any inference/hardware performance.

## Forbidden next steps

- no self-hosted runner or P0-T04 hardware execution before protection is directly evidenced;
- no restricted/private payload in GitHub, issues, logs or artifacts;
- no engine implementation before repository hardening, hardware inventory and Phase 1 workload definition;
- no claim that public visibility grants an open-source license;
- no external RAG or plugin may become canonical project memory.
