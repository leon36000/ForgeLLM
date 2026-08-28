# ForgeLLM Decision Register

| ID | Date | Status | Decision | Source |
|---|---|---|---|---|
| D-0001 | 2026-08-12 | accepted | Git-tracked state is canonical; chat memory is auxiliary. | ADR-0002 |
| D-0002 | 2026-08-12 | accepted | Rust owns the control plane; native backends own target-specific kernels; C ABI connects them. | ADR-0001 |
| D-0003 | 2026-08-12 | accepted | Existing engines are baselines/adapters and are replaced incrementally, not rewritten wholesale. | ADR-0001 |
| D-0004 | 2026-08-12 | accepted | External benchmark claims remain unreproduced until ForgeLLM reproduces them. | Evidence policy |
| D-0005 | 2026-08-12 | accepted | Significant changes require independent implementer and verifier contexts. | Agent contract |
| D-0006 | 2026-08-12 | accepted | Self-hosted GPU execution is limited to trusted workflows and remains disabled until its security gates pass. | Security policy |
| D-0007 | 2026-08-12 | accepted | Phase 1 defines workload profiles before any “best engine” claim. | Charter |
| D-0008 | 2026-08-13 | accepted | Keep the source/governance repository public and place every restricted or operationally sensitive payload in a separate private asset plane. | ADR-0003 / issue #8 |
| D-0009 | 2026-08-13 | accepted | External RAG systems and agent tools are derived, least-privilege services; Git remains canonical. | ADR-0003 |
| D-0010 | 2026-08-13 | accepted | Repository ruleset `FLLM` is the active solo-maintainer protection policy for `main` until superseded by reviewed state. | P0-T03 / issue #10 |
| D-0011 | 2026-08-27 | accepted | Task lifecycle state is authoritative in Git packets; README, mobile state and `TREE.txt` are deterministic derived projections carrying explicit freshness metadata. | P0-T14 / issue #73 |

## Register protocol

- This file is an index, not a substitute for an ADR.
- Add a row in the same pull request that accepts, rejects or supersedes an ADR or durable governance decision.
- Never silently change the meaning of an existing decision; supersede it with a new identifier.
