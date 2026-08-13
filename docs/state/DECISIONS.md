# ForgeLLM Decision Register

| ID | Date | Status | Decision | Source |
|---|---|---|---|---|
| D-0001 | 2026-08-12 | accepted | Git-tracked state is canonical; chat memory is auxiliary. | ADR-0002 |
| D-0002 | 2026-08-12 | accepted | Rust owns the control plane; native backends own target-specific kernels; C ABI connects them. | ADR-0001 |
| D-0003 | 2026-08-12 | accepted | Existing engines are baselines/adapters and are replaced incrementally, not rewritten wholesale. | ADR-0001 |
| D-0004 | 2026-08-12 | accepted | External benchmark claims remain unreproduced until ForgeLLM reproduces them. | Evidence policy |
| D-0005 | 2026-08-12 | accepted | Significant changes require independent implementer and verifier contexts. | Agent contract |
| D-0006 | 2026-08-12 | accepted | GPU self-hosted runners are restricted to trusted private workflows. | Security policy |
| D-0007 | 2026-08-12 | accepted | Phase 1 defines workload profiles before any “best engine” claim. | Charter |

## Register protocol

- This file is an index, not a substitute for an ADR.
- Add a row in the same pull request that accepts, rejects or supersedes an ADR.
- Never silently change the meaning of an existing decision; supersede it with a new identifier.
