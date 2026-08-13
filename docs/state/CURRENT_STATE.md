# ForgeLLM Current State

- **State ID:** S-0003
- **Updated:** 2026-08-13
- **Phase:** P0
- **Milestone:** P0-M2 — canonical GitHub foundation merged and verified
- **Overall status:** P0-T02 complete; Phase 0 foundation is merged into private `main` and passed post-merge CI; P0-T03 repository hardening is ready and active
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

## Mobile hashes verified on merged `main`

```text
8a189b9dab3f60fe370099504c39d2196872ebc1977a5c91e34423a124766fbe  chatgpt/mobile-core/00_FORGELLM_CORE_CONTEXT.md
e76b7813eae0d8003bd5941d9dc07c28894c8acd0d835545a1b7b12bf865b26b  chatgpt/mobile-core/01_FORGELLM_AGENT_OPERATING_SYSTEM.md
10830969febb4234a61b0c36857be561d5185a0b64b7b9015fe055b6a0790801  chatgpt/mobile-core/02_FORGELLM_RESEARCH_AND_EVIDENCE.md
9315d61b2a8c4b4f8ab19e2fb23fbe2367a1089f293c41c7882b94f4cdab853c  chatgpt/mobile-core/03_FORGELLM_STATE_AND_DECISIONS.md
9697f7b35aa1924bdd9c07cf259fad41209d6e174cd7b2ecec3f65ab71932ff9  chatgpt/mobile-core/04_FORGELLM_PROMPTS_AND_WORKFLOWS.md
```

The S-0003 mobile projection changes the fourth hash; the closeout PR must emit and record the replacement hash before merge.

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
- CodeQL or Dependency Review success;
- any externally reported performance result;
- public-release or production readiness.

The root `MANIFEST.sha256` remains historical evidence for the initial Phase 0 delivery. Live repository identity is the Git commit/tree; experiment and mobile packages use scoped manifests.

## Active task: P0-T03

Task packet: `tasks/open/P0-T03-repository-hardening.yaml`.

Goal: directly inspect and configure the strongest available GitHub protections and optional security checks without registering a self-hosted runner or weakening existing CI.

Primary gates:

1. capture direct branch-protection/ruleset evidence or an explicit API/plan/access blocker;
2. verify Actions default permissions;
3. determine whether CodeQL and Dependency Review are supported, enable them only after successful runs, and never make a skipped check required;
4. preserve all repository-admin writes and rollback commands;
5. run exact-head CI and fresh-context review.

## Current blockers and owner-controlled choices

- The connected GitHub integration returned `403 Resource not accessible by integration` for the branch-protection endpoint; protection is therefore unknown, not assumed.
- No self-hosted runner may be registered while that state remains unknown.
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
- Do not claim CodeQL, Dependency Review, secret scanning, push protection or rulesets are active without direct evidence.
