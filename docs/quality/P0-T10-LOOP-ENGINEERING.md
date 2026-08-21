# P0-T10 — Bounded Loop Engineering Evidence

- Task: P0-T10 — bounded Loop Engineering static integration
- Canonical base: f8364f12402c3c58796dbc1b56f8c65d378e88de
- ADR: ADR-0005-bounded-loop-engineering.md, proposed and not yet accepted
- Evidence boundary: governance/reference validation only; no runtime, inference, hardware, backend, benchmark, or Sonar activation claim

## Selected boundary

ForgeLLM uses a project-local bridge around an inert, pinned upstream reference. Git task packets and accepted ADRs remain authoritative. A loop declaration may narrow task-packet authority but cannot widen paths, verification commands, decisions, or privilege.

The bridge validates the six semantic fields GOAL, SCOPE, VERIFY, BUDGET, STOP, and RECEIPT. It has no autonomous runner, shell evaluator, Stop hook, installer, adapter, credential capability, or external mutation path.

## Upstream provenance

The reviewed source is https://github.com/lcajigasm/loop-engineering at commit ae2d610985064bb30c5013261988c813013c09e3, licensed under MIT. The license Git blob is 84524f23b209fccb02a8f239165f0444bfd70f3f.

The exact selected upstream blob bindings are recorded in third_party/loop-engineering/PROVENANCE.yaml and checked by validate_vendor_provenance. The local tree is required to contain only LICENSE, PROVENANCE.yaml, core/METHODOLOGY.md, core/COMMANDS.md, and the four selected core templates. install.sh, scripts, hooks, adapters, and shadow-state templates are excluded.

## Verification evidence

- Controller RED tests initially failed at collection because validate_vendor_provenance was absent.
- The focused controller suite is the required regression gate for the firewall, authority, receipt, provenance, skill, marker, and Makefile contracts.
- make validate-loop validates the P0-T10 packet and the repository catalog/provenance gate.
- make validate retains all existing project and P0-T09 validation commands through a dependency on validate-loop.
- ADR-0005 remains proposed pending independent architecture/security review.

## Limitations and non-goals

This increment does not authorize or validate P0-T09 implementation/settings/tokens, GitHub or Sonar administration, hardware probing, model execution, runtime/backend/kernel work, Cargo/Rust changes, chatgpt/mobile-core changes, or closed task packets.
