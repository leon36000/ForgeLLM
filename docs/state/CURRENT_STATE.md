# ForgeLLM Current State

- **State ID:** S-0005
- **Updated:** 2026-08-13
- **Phase:** P0
- **Milestone:** P0-M4 — protected GitHub control plane; first inventory gate next
- **Overall status:** P0-T03 complete; ruleset `FLLM` is active and protects `main`; P0-T04 is blocked only on designation of the first owner-authorized host
- **Authorized next task:** P0-T04
- **State anchor:** the Git commit containing this file

## Objective

Prepare the first reproducible and publication-safe hardware/software inventory on one explicitly authorized machine, without changing that machine or running inference workloads.

## Canonical remote and protection evidence

- Repository: `leon36000/ForgeLLM`.
- Visibility: public under ADR-0003.
- Default branch: `main`.
- Main commit before S-0005: `c1ec3db1613d9bc6a9a4cd0cd7a1c7e4eabaaa7f`.
- GitHub branch readback on 2026-08-13 reports `main.protected=true`.
- Active repository ruleset: `FLLM`, id `20820530`.
- Ruleset enforcement: `active`.
- Target ref: exactly `refs/heads/main`.
- Bypass actors: none.
- Current user bypass: never.

### FLLM policy verified by direct readback

- deletion protection;
- non-fast-forward update protection;
- required linear history;
- pull request required;
- zero approving reviews while ForgeLLM has one human maintainer;
- stale reviews dismissed on push;
- CODEOWNERS review not required in solo mode;
- last-push approval not required in solo mode;
- review conversations must be resolved;
- squash is the only allowed merge method;
- strict required status check `Validate and test` from GitHub Actions integration id `15368`.

Issue #10 records the owner checkpoint and is closed as completed. `docs/state/P0-T03-CLOSEOUT-NOTE.md` records the independent readback on the closeout branch.

## P0-T03 completion

P0-T03 is complete within its repository-hardening scope.

Satisfied gates:

- public repository boundary governed by ADR-0003;
- public/private data separation documented;
- hosted Phase 0 gate repeatedly successful;
- CodeQL execution/upload evidenced without unsupported clean-scan claims;
- Dependency Review remains optional pending its repository prerequisite;
- `main` is directly evidenced as protected by an active repository ruleset;
- no fabricated second human reviewer or bypass actor is used.

## Decisions preserved

- **D-0001:** Git-tracked state is canonical; conversation memory is auxiliary.
- **D-0002:** Rust owns the control plane; native target ecosystems own performance-critical kernels; a versioned C ABI connects layers.
- **D-0003:** existing engines are measured baselines/adapters and are replaced incrementally.
- **D-0004:** external performance remains unreproduced until a reviewed ForgeLLM experiment reproduces it.
- **D-0005:** significant work separates implementation, fresh-context verification and owner authorization.
- **D-0006:** privileged hardware execution requires protected control-plane gates and a separate review.
- **D-0007:** models, workloads, SLOs and objective functions precede any “best engine” claim.
- **D-0008:** the source/governance repository is public; restricted assets belong in a separate private plane.
- **D-0009:** external RAG/apps are derived services; Git remains canonical.
- **D-0010:** `FLLM` is the active solo-maintainer protection policy for `main` until superseded by a reviewed decision.

## Active task: P0-T04

Task packet: `tasks/open/P0-T04-first-hardware-inventory.yaml`.

Tracking issue: #12.

Status: `blocked` pending one owner input — designation of the first host by a project-safe label and selection of the execution mode described in issue #12.

P0-T04 is observation-only. The detailed operating and publication constraints are maintained in the task packet, issue #12 and repository policies.

## Evidence boundary

S-0005 proves repository protection and previously recorded hosted checks. It does not prove any hardware inventory, accelerator compatibility, inference correctness, performance, energy efficiency, model support, distributed behavior, or release readiness.

## Forbidden next steps

- do not change the selected host as part of inventory;
- do not register a self-hosted runner during P0-T04;
- do not run inference or performance benchmarks before the inventory is reviewed and P0-T05 defines workload profiles;
- do not begin engine implementation before the Phase 1 laboratory definition.
