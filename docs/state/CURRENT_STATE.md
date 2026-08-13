# ForgeLLM Current State

- **State ID:** S-0003
- **Updated:** 2026-08-13
- **Phase:** P0
- **Milestone:** P0-M2 — canonical GitHub foundation merged and verified
- **Overall status:** P0-T02 complete; Phase 0 foundation is merged into private `main` and passed post-merge CI; P0-T03 repository hardening is in progress with successful CodeQL execution but branch-protection and alert visibility still unresolved
- **Authorized next task:** P0-T03
- **State anchor:** the Git commit containing this file; the state does not embed its own self-referential commit SHA

## Objective

Harden the canonical repository control plane before connecting privileged or self-hosted hardware, while preserving the verified Phase 0 foundation and keeping inference-engine implementation blocked until the laboratory and workload profiles are defined.

## Canonical remote

- Platform: GitHub
- Repository: `leon36000/ForgeLLM`
- Visibility: private, verified through the connected GitHub API on 2026-08-13
- Default branch: `main`
- Phase 0 bootstrap PR: `#1 — chore: import ForgeLLM phase 0 foundation`
- PR #1 final reviewed head: `aa978989a5f6ad3524618eda5cd8b650288c7a67`
- PR #1 squash merge commit: `20bc5fa061aa039d32c2702d47eeba07dd353363`
- PR #1 merge tree: `c75bc10c17744cba0bf0c5a284cd40f4285a2e10`
- S-0003 closeout PR: `#4 — docs(state): close P0-T02 and activate P0-T03`

## P0-T02 completion evidence

P0-T02 is complete within its declared private-bootstrap scope.

Verified evidence:

- private canonical remote exists;
- exactly five canonical mobile Markdown files are enforced by `scripts/hash_mobile_context.py`;
- fresh-context review report exists at `docs/reviews/P0-T02-INDEPENDENT-AGENT-REVIEW.md` with verdict `ACCEPT`;
- owner authorized continuation and PR #1 was merged by squash;
- final pull-request CI run `31676559801`, job `94372299029`, succeeded on head `aa978989a5f6ad3524618eda5cd8b650288c7a67`;
- post-merge `main` CI run `31676680397`, job `94372665642`, succeeded on merge commit `20bc5fa061aa039d32c2702d47eeba07dd353363`.

The decoded post-merge job log showed:

- Ruff 0.16.2: passed;
- project-state validation: passed;
- research-catalog validation: passed;
- benchmark example validation: passed;
- P0-T02 task-packet validation: passed;
- exact five-file mobile context check and SHA-256 emission: passed;
- Python tests: **13 passed**;
- Ubuntu bootstrap dry-run: passed;
- GitHub token permissions limited to metadata/content read.

## S-0003 closeout evidence before the final state amendment

On PR #4 head `113b0e8cf86fa40c2f05e2742a635de17cef5afd`:

### Phase 0 verification

- run: `31677360240`;
- job: `94374759191`;
- conclusion: `success`;
- Ruff passed;
- project, research, benchmark, P0-T02 and P0-T03 task validation passed;
- exactly five mobile hashes were emitted;
- **13 tests passed**;
- Ubuntu bootstrap dry-run passed;
- token permissions were metadata/content read only.

### CodeQL

- run: `31677360037`;
- job: `94374758365`;
- conclusion: `success`;
- CodeQL Action 4.37.6 and CLI 2.26.2 initialized successfully;
- Python extraction completed over 61 modules;
- the `security-extended` suite executed 52 queries;
- SARIF upload succeeded and GitHub reported processing complete;
- workflow permissions were contents/read, metadata/read and security-events/write.

The connected integration returned `403 Resource not accessible by integration` for the code-scanning alerts endpoint. Therefore the analysis execution and upload are proven, while alert count, severities and triage state remain **unknown**. A successful workflow conclusion must not be restated as “zero alerts.”

### Dependency Review

- run: `31677360127`;
- conclusion: `skipped` by the private-repository feature guard.

Dependency Review is not active evidence and must not become a required check while it remains skipped.

## Mobile hash observed on the reviewed S-0003 proposal

```text
506b740aeff18d6e96a3db2550caa710995a9e93059b7ab5513b8f20020592f0  chatgpt/mobile-core/03_FORGELLM_STATE_AND_DECISIONS.md
```

The current state amendment changes that file; PR #4 must emit a replacement hash on its final exact head before merge.

## Accepted decisions preserved

- **D-0001:** Git-tracked state is canonical; conversation memory is auxiliary.
- **D-0002:** Rust owns the control plane; native accelerator stacks own target-specific kernels; a versioned C ABI connects them.
- **D-0003:** existing engines are measured baselines/adapters and are replaced incrementally, not rewritten wholesale.
- **D-0004:** external performance remains unreproduced until a reviewed ForgeLLM experiment reproduces it.
- **D-0005:** significant work separates implementation, fresh-context verification and owner authorization; a second account controlled by the same person is not independent.
- **D-0006:** no self-hosted GPU runner is registered before private-repository, protected-branch and untrusted-code controls are directly evidenced.
- **D-0007:** Phase 1 defines models, workloads, SLOs and objective functions before any “best engine” claim.

## Evidence boundary

The verified Phase 0 foundation proves repository structure, governance tooling, deterministic mobile context, validation logic and hosted CI execution. It does not prove:

- any ForgeLLM inference implementation;
- numerical compatibility with PyTorch or another engine;
- NVIDIA, AMD, CPU or distributed performance;
- branch-protection activation;
- absence or count of CodeQL alerts;
- Dependency Review success;
- any externally reported performance result;
- public-release or production readiness.

The root `MANIFEST.sha256` remains historical evidence for the initial Phase 0 delivery. Live repository identity is the Git commit/tree; experiment and mobile packages use scoped manifests.

## Active task: P0-T03

Task packet: `tasks/open/P0-T03-repository-hardening.yaml`.

Status: `in_progress`.

Goal: directly inspect and configure the strongest available GitHub protections and optional security checks without registering a self-hosted runner or weakening existing CI.

Progress already evidenced:

- private repository and default branch identity verified;
- Phase 0 check name and successful execution verified;
- CodeQL execution, SARIF upload and processing verified;
- CodeQL alert visibility remains inaccessible;
- Dependency Review remains skipped.

Remaining primary gates:

1. capture direct branch-protection/ruleset evidence or an explicit API/plan/access blocker;
2. capture GitHub Actions default and selected-action permissions directly;
3. retrieve or otherwise review CodeQL alert output before treating the scan as clean or required;
4. determine whether Dependency Review is supported and run it successfully before making it required;
5. preserve all repository-admin writes and rollback commands;
6. run exact-head CI and fresh-context review for P0-T03.

## Current blockers and owner-controlled choices

- The connected GitHub integration returned `403 Resource not accessible by integration` for the branch-protection endpoint; protection is therefore unknown, not assumed.
- The same integration returned `403` for the CodeQL alerts endpoint; scan result details are unknown despite successful execution.
- No self-hosted runner may be registered while branch protection remains unknown.
- Project license and contributor policy remain undecided.
- No second real human maintainer or active CODEOWNERS exists.
- Exact hardware, topology, OS, drivers and network remain unrecorded.
- Phase 1 models, workloads and objective priorities remain undefined.

## Forbidden next steps

- Do not register a self-hosted CPU or GPU runner before `main` protection is directly verified.
- Do not begin inference-engine implementation before repository hardening, hardware inventory and Phase 1 workload definition.
- Do not label external benchmark results as reproduced.
- Do not install or replace GPU drivers through an unattended agent.
- Do not make the repository public or select a license without an owner-approved decision.
- Do not claim CodeQL found no alerts, Dependency Review passed, or branch protection/rulesets are active without direct evidence.
