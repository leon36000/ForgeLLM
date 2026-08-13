# ForgeLLM Current State

- **State ID:** S-0004
- **Updated:** 2026-08-13
- **Phase:** P0
- **Milestone:** P0-M3 — public repository boundary accepted and hardening underway
- **Overall status:** P0-T03 in progress; public visibility is owner-approved under ADR-0003, public-data controls are defined, and CodeQL is passing; `main` protection and owner-enabled Dependency Graph remain administrative blockers
- **Authorized next task:** P0-T03
- **State anchor:** the Git commit containing this file

## Objective

Complete the public GitHub control-plane hardening before any self-hosted hardware or private asset plane is connected.

## Canonical remote and direct evidence

- Repository: `leon36000/ForgeLLM`.
- Visibility: `public`, directly reported by GitHub on 2026-08-13.
- Default branch: `main`.
- Main commit before this change: `843f8127f76a0c7f2ef9863853dccaddeff90aa8`.
- Main branch direct evidence: `protected=false`; required-status-check enforcement `off`; no contexts/checks.
- Repository rulesets direct evidence: empty list.
- Branch-protection administrative endpoint: `403 Resource not accessible by integration`.
- Actions default/selected permission endpoints: `403 Resource not accessible by integration`.
- Code-scanning alert endpoint: `403 Resource not accessible by integration`.

The previous S-0003 statements that the repository was private are superseded by this state and ADR-0003. The repository was already public; this update records the owner's intentional decision rather than claiming an unverified private boundary.

## Owner decision and operating boundary

Issue #8 and ADR-0003 accept a public source/governance repository so public CI and agent-tool ecosystems remain available.

Every Git-tracked byte is treated as public. Secrets, restricted weights, private datasets/prompts, unredacted traces, private network details and stable device identifiers are forbidden. A future private asset plane will be introduced only through a bounded task and will be referenced by opaque IDs, revisions and hashes.

Git remains canonical. Neon or another RAG may later index the repository, but it is derived and cannot override ADRs, state, evidence or history. NVIDIA, AMD, Temporal, SonarQube, Consensus and other integrations require least privilege and task-specific data review.

## Verified inherited evidence

- Phase 0 final PR and post-merge gates passed with Ruff, validators, deterministic mobile hashes and 13 tests.
- CodeQL executed `security-extended`, uploaded SARIF and completed processing on prior heads; alert details remain inaccessible to this integration.
- No ForgeLLM inference runtime, GPU backend, self-hosted runner or private asset store exists.

## P0-T03 first PR-head evidence

PR #9 head `f6e3632bdbbdab74d88e296bfb3bb98555da1bc3` produced:

- CodeQL run `31681032932`, job `94386280268`: success; 62 Python modules extracted, 52 `security-extended` queries executed, SARIF uploaded and processing completed; alert details remain inaccessible.
- Phase 0 run `31681032948`, job `94386280549`: failure after Ruff and all structural validators passed; 15 tests passed and one stale syntax-coupled test failed because the Dependency Review condition changed.
- Dependency Review run `31681032967`, job `94386280488`: failure before dependency analysis because GitHub Dependency Graph is not enabled. This is a capability/configuration failure, not a vulnerability or license finding.

Root-cause corrections:

- Dependency Review returned to explicit opt-in until the owner enables Dependency Graph;
- the workflow guard test now mutates the semantic feature marker instead of one exact formatting string;
- the failed runs remain evidence and are not reclassified as passes.

## P0-T03 changes in this state

- accepted ADR-0003;
- added public repository and data-classification policies;
- added a public-facing security reporting file;
- updated contribution and licensing notices;
- updated repository policy, task packet, decisions, risks and mobile state;
- added tests for repository-audit classification and solo branch-protection payload;
- updated the read-only audit to distinguish pass, fail and unknown controls;
- probed Dependency Review and recorded its disabled Dependency Graph prerequisite.

## P0-T03 gates

### Expected to be demonstrated by this pull request

- exact-head `make ci`;
- CodeQL execution/upload;
- Dependency Review safely skipped until owner-enabled, or successful after Dependency Graph is enabled;
- fresh-context review;
- consistent public-data and no-license notices.

### Blocking manual/admin gates

Before P0-T03 can complete:

1. direct evidence must show `main` protected by branch protection or an enforced ruleset that requires pull requests, the stable `Validate and test` check, conversation resolution, administrators/owner, and no force push/deletion;
2. Dependency Graph must be enabled before Dependency Review can become active or required.

The current integration cannot perform or read those administrative writes. `scripts/github/apply_branch_protection.py` provides a reviewed dry-run/apply command for an owner-authenticated `gh` session.

## External-tool applicability

- Codex Engineering Guardrails and GitHub/CodeQL: used for current implementation and verification.
- SonarQube: useful when a callable server/project is connected; not currently treated as executed evidence.
- Fallow: not applicable to the present Python/Markdown codebase.
- Consensus: reserved for bounded scientific synthesis tasks.
- Neon Postgres: candidate derived RAG only after a dedicated ADR/task.
- Temporal: candidate for durable agent orchestration after workflow semantics are specified.
- NVIDIA/AMD skills: reserved for protected hardware and backend phases.

## Evidence boundary

This state proves only directly observed repository metadata and evidence emitted by completed CI jobs. It does not prove branch protection, Actions administrative settings, zero CodeQL alerts, Dependency Review results, or any inference/hardware performance.

## Forbidden next steps

- no self-hosted runner or P0-T04 hardware execution before protection is directly evidenced;
- no restricted/private payload in GitHub, issues, logs or artifacts;
- no engine implementation before repository hardening, hardware inventory and Phase 1 workload definition;
- no claim that public visibility grants an open-source license;
- no external RAG or plugin may become canonical project memory.
