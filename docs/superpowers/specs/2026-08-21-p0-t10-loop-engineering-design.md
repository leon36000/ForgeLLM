# P0-T10 Bounded Loop Engineering Design

**Status:** approved in chat on 2026-08-21; implementation target for the fresh P0-T10 branch

## Goal

Adopt Loop Engineering as a bounded, reproducible orchestration layer for ForgeLLM while keeping Git-tracked task packets, accepted ADRs, and repository gates as the only project authority.

## Context and constraints

P0-T10 issue #36 is open. PR #37 was closed after adversarial review identified command-composition bypasses, wrapper bypasses, incomplete Git/GitHub mutation controls, privileged secret reads, and receipt artifacts that were not validated as committed run outputs. The implementation must start from the current protected `main`, not from the closed PR head.

The implementation must not:

- change Sonar or GitHub settings, provision tokens, activate a scanner, or alter P0-T09;
- run model inference, hardware probes, benchmarks, runtime, ABI, backend, kernel, or Transition Atlas work;
- install or execute upstream shell installers, `eval`-based runners, Stop hooks, or agent adapters;
- replace ForgeLLM task packets, ADRs, `CURRENT_STATE`, or `HANDOFF` with upstream GOALS/STATUS/project-brief files;
- grant loops authority over credentials, accounts, billing, privileged hosts/runners, or external mutations.

## Chosen architecture

Use the owner-approved vendored-and-bridged design with the upstream Loop Engineering source pinned to an immutable commit and provenance/license records preserved. Vendored content is inert reference material; ForgeLLM owns the adapter, authority checks, task binding, and repository-native validation. There is no automatic loop runner in this increment.

Every run is bound to one ForgeLLM task packet and one Git base revision through the explicit fields `GOAL`, `SCOPE`, `VERIFY`, `BUDGET`, `STOP`, and `RECEIPT`. Scope and verification may narrow the task packet but may not widen its allowed paths, forbidden actions, or evidence requirements.

## Security boundary

The verifier accepts only an explicit read-only command allowlist for repository inspection. It rejects shell composition and redirection operators (`;`, `&`, `|`, `<`, `>`), command wrappers (`env`, `command`, `exec`, `xargs`, `parallel`, `timeout`, `nice`, `setsid`), Git/GitHub mutation forms, compact mutation flags, subcommand-confusion/global-option forms, secret or infrastructure clients, and privileged reads. No verifier result can authorize a subsequent mutation.

The firewall must classify the complete tokenized command, not only the first executable. `make` remains an allowed repository gate only when the complete command is a single permitted invocation. `gh` is limited to the read operations explicitly needed by the repository oracle. A command that cannot be classified safely fails closed.

## Receipt integrity

The repository validator validates every committed final receipt and its index, not just a template. Each receipt binds to an immutable, committed run declaration containing the task packet identity, exact base commit, and declaration digest. Historical schema versions remain preserved and are validated under their declared compatibility rules; they are not silently rewritten.

Receipt validation rejects missing or mismatched declaration bindings, mutable active declarations that do not match the recorded run, unknown receipt/index entries, duplicate run identities, invalid `stop_reason`/`verification.disposition` combinations, and self-asserted verification presented as independent evidence. Failed or incomplete runs remain valid historical evidence only when their disposition and stop reason agree.

## Implementation surfaces

- `src/forgellm_governance/loop_engineering.py`: pure task/run models, command firewall, authority and receipt-binding logic.
- `scripts/validate_loop_engineering.py`: repository-level validation of the task packet, declarations, receipts, index, upstream provenance, and fixed integration surface.
- `tests/test_loop_engineering.py`: deterministic unit and negative tests for firewall and receipt invariants.
- `tasks/open/P0-T10-bounded-loop-engineering.yaml`: task authority and acceptance criteria.
- `artifacts/governance/loop-engineering/`: pinned declarations, receipts, index, and rejected-command fixtures.
- `third_party/loop-engineering/`: pinned inert upstream reference and provenance/license metadata only.
- `docs/architecture/ADR-0005-bounded-loop-engineering.md`, `docs/quality/P0-T10-LOOP-ENGINEERING.md`, and state/handoff updates: durable decision and evidence boundaries.
- `Makefile`: invoke the repository validator without weakening existing Phase 0 gates.

## Test and gate strategy

1. Write deterministic RED tests for each known bypass and receipt-drift finding.
2. Implement the smallest parser/allowlist and receipt-binding behavior that makes those tests GREEN.
3. Run focused tests after each slice, then `make validate` and `make ci`.
4. Inspect the exact diff for scope, provenance, secret hygiene, and authority drift.
5. Run fresh Phase 0, CodeQL, GitGuardian, and Sonar checks on the exact PR head; Dependency Review is reported according to its actual conclusion.
6. Obtain an independent architecture/security ACCEPT with no unresolved BLOCKER or MAJOR finding, then obtain the GPT-5.6-Sol exact-head merge gate.
7. Merge only after the exact-head gates pass. No direct push to `main`.

## Acceptance boundary

This design establishes a safe, repository-native loop contract and validation surface. It does not claim that ForgeLLM has an autonomous production agent, privileged-operation automation, model execution, hardware support, or a production inference runtime. Those require separate task packets and gates.
