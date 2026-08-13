# P0-T03 Public Repository Hardening — Fresh-Context Review

- **Task:** P0-T03 — Harden and directly verify the public ForgeLLM GitHub control plane
- **Issue:** #8
- **Pull request:** #9 — `docs(governance): accept public repository boundary`
- **Base commit:** `843f8127f76a0c7f2ef9863853dccaddeff90aa8`
- **Reviewed implementation head:** `9d3b47365aa017f37b16a6f8c7e307677a7526cf`
- **Review date:** 2026-08-13
- **Review role:** fresh agent context, separate from the implementation sequence
- **Verdict:** `ACCEPT` for merging the public-repository governance change; P0-T03 remains `in_progress` and blocked on owner-admin controls

## Scope reviewed

The review evaluated the complete PR diff against the charter, ADRs, S-0003, the rewritten P0-T03 task packet, the public-data boundary, CI/security workflows, repository-audit logic, tests and mobile projection.

Representative files inspected:

- `docs/architecture/ADR-0003-public-repository-and-private-assets.md`;
- `docs/governance/PUBLIC_REPOSITORY_POLICY.md`, `SECURITY_POLICY.md`, `CONTRIBUTING.md` and `LICENSING_DECISION.md`;
- `.github/SECURITY.md`, CodeQL and Dependency Review workflows;
- `scripts/github/audit_repository.py` and `apply_branch_protection.py`;
- `tests/test_github_audit.py` and `tests/test_validation.py`;
- `tools/repository-policy.yaml`;
- S-0004 state, handoff, risks, decisions, roadmap and mobile projection.

## Direct repository evidence

Before this PR, GitHub directly reported:

- repository visibility `public`;
- default branch `main`;
- `main.protected=false`;
- required-status-check enforcement `off` with no contexts/checks;
- repository rulesets `[]`;
- branch-protection, Actions-permission and CodeQL-alert administrative endpoints inaccessible to the connected integration (`403`).

The PR correctly supersedes stale private-repository assumptions instead of treating public visibility as an incident or silently changing the owner decision.

## Exact-head verification evidence

### Phase 0 gate

On head `9d3b47365aa017f37b16a6f8c7e307677a7526cf`:

- run: `31681837631`;
- job: `94388820133`;
- conclusion: `success`;
- token permissions: contents/read and metadata/read;
- checkout: `persist-credentials=false`;
- Ruff 0.16.2: passed;
- project, research, benchmark, P0-T02 and P0-T03 task validation: passed;
- exact five-file mobile validation and SHA-256 emission: passed;
- Python tests: **17 passed**;
- Ubuntu bootstrap dry-run: passed;
- no GPU drivers, CUDA, ROCm, container runtime or privileged service installed.

Observed S-0004 mobile-state hash on that head:

```text
a8385ab40c1df9d5d140263d8f054b9fa02f689833543b3f02253b6d7e2339ad  chatgpt/mobile-core/03_FORGELLM_STATE_AND_DECISIONS.md
```

### CodeQL gate

On the same head:

- run: `31681837665`;
- job: `94388813356`;
- conclusion: `success`;
- CodeQL Action 4.37.6 / CLI 2.26.2;
- Python extraction: 62 modules;
- `security-extended`: 52 queries;
- SARIF upload: success;
- GitHub processing: complete;
- permissions: contents/read, metadata/read and security-events/write.

The alerts endpoint remains inaccessible to this integration. The review accepts execution/upload/processing evidence but does **not** assert zero alerts, severity distribution or triage state.

### Dependency Review

- initial capability probe: run `31681032967`, job `94386280488`, failed because GitHub Dependency Graph is disabled;
- current head: run `31681837651`, conclusion `skipped` by the explicit opt-in guard.

The failed probe is a configuration/capability result, not a dependency vulnerability or license finding. Dependency Review must remain non-required until the owner enables Dependency Graph, enables the repository variable and observes a successful internal PR run.

## Findings

### BLOCKER — intentionally remains after merge: `main` is unprotected

No classic protection or applicable ruleset is directly evidenced. This blocks P0-T03 completion, P0-T04 and every self-hosted runner. The governance PR may merge because it documents and enforces the blocker rather than bypassing it.

### MAJOR — resolved: stale private-repository model

ADR-0003, the public repository policy and S-0004 consistently establish a public source/governance plane and a future separate private asset plane. Secrets, restricted weights/data/prompts, unredacted traces, private network data and stable device identifiers are prohibited.

### MAJOR — resolved: Dependency Review caused a false blocking failure

The first public-PR run failed before dependency analysis because Dependency Graph was disabled. The workflow returned to explicit opt-in, and the regression test now checks the semantic feature marker instead of one formatting string. The failed evidence remains recorded.

### MAJOR — resolved during review: unrelated ruleset could fake protection

The first audit implementation treated any nonempty repository ruleset list as proof that `main` was protected. A disabled ruleset or a tag-only ruleset would therefore create a false security pass.

Resolution:

- `branches/main.protected` is now the authoritative aggregate for this exact branch;
- ruleset count is diagnostic only;
- a regression test proves that an unrelated tag ruleset cannot pass `main-protection`.

### MINOR — accepted: public repository without project license

README, contribution and licensing policy state that public visibility is not a license. External code contributions remain gated until an inbound and outbound license policy is accepted.

### MINOR — accepted: external tools are not canonical memory

Git remains authoritative. Neon/RAG, SonarQube, Consensus, Temporal, NVIDIA/AMD skills and other integrations are task-bound derived services with least-privilege and data-classification requirements.

## Security assessment

- no self-hosted runner exists or is authorized;
- public-data restrictions are explicit in repository-facing documentation;
- CI Actions are pinned to full SHAs and the functional gate uses read-only token permissions;
- CodeQL security-events write is limited to the scan workflow;
- Dependency Review is not falsely advertised as active;
- the audit distinguishes `pass`, `fail` and `unknown` rather than translating access denial into success;
- branch protection application remains dry-run plus an explicit owner confirmation environment variable.

## Evidence boundary

This review does not establish:

- protected `main`;
- readable Actions administrative settings;
- zero CodeQL alerts;
- successful Dependency Review;
- safety of any self-hosted runner;
- any inference implementation, hardware support or performance result;
- an open-source license grant.

## Verdict

`ACCEPT` for merge of PR #9 after the evidence-closeout head passes:

1. `Validate and test`;
2. CodeQL execution/upload;
3. fresh mobile hash generation.

Dependency Review may remain skipped because the disabled Dependency Graph prerequisite is explicitly preserved and the check is non-required.

After merge, P0-T03 remains `in_progress`. The owner-admin completion sequence is:

1. review and apply `scripts/github/apply_branch_protection.py` through an authenticated `gh` session or an equivalent GitHub ruleset;
2. capture direct `main.protected=true` or enforced ruleset evidence;
3. enable Dependency Graph, then opt in Dependency Review and obtain a successful run if that control is desired;
4. inspect CodeQL alerts through an owner-authorized interface;
5. update state and close P0-T03 through a separate reviewed PR.

No self-hosted runner or P0-T04 work may begin before step 2 is proven.
