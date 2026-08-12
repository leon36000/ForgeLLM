# ForgeLLM Risk Register

Scoring uses probability and impact from 1 to 5; exposure is their product.

| ID | Risk | P | I | Exposure | Owner role | Mitigation | Trigger |
|---|---|---:|---:|---:|---|---|---|
| R-001 | Scope expands into a full engine before baselines exist. | 4 | 5 | 20 | architect | phase gates, task packets, non-goals | code added outside authorized phase |
| R-002 | Benchmarks compare different models, loads or environments. | 4 | 5 | 20 | performance reviewer | schema, raw samples, baseline manifest | missing immutable model/workload field |
| R-003 | Rust/native boundary causes lifecycle or synchronization defects. | 3 | 5 | 15 | runtime reviewer | opaque handles, safety invariants, contract tests, sanitizers | use-after-free, hang, stream race |
| R-004 | Portable DSL or dependency changes break the build. | 4 | 3 | 12 | build owner | pinned versions, adapters, fallback backend | upstream incompatible release |
| R-005 | Self-hosted GPU runner executes malicious/untrusted code. | 3 | 5 | 15 | security owner | private repo, restricted groups/tags, manual approval, ephemeral workers | fork job reaches GPU runner |
| R-006 | Agent reports work or tests that were not executed. | 3 | 5 | 15 | verifier | command logs, CI, artifacts, independent replay | report lacks machine output |
| R-007 | Chat context diverges from repository state. | 4 | 4 | 16 | governance owner | session bootstrap/closeout and mobile-state regeneration | conflicting decisions/state IDs |
| R-008 | “Most powerful” remains undefined and unfalsifiable. | 5 | 4 | 20 | product owner | workload profiles and objective functions in P1 | optimization proposal lacks target metric |
| R-009 | Vendor-specific optimization creates irreversible lock-in. | 3 | 4 | 12 | architect | shared semantics, ABI, conformance suite, multiple baselines | public API exposes vendor internals |
| R-010 | Model or dataset licensing blocks publication. | 3 | 4 | 12 | legal/governance owner | license inventory and private artifacts | unknown or incompatible terms |
| R-011 | Thermal/power behavior invalidates performance results. | 3 | 3 | 9 | lab owner | warm-up, clocks, temperature and power notes | run-to-run drift exceeds threshold |
| R-012 | Heterogeneous network transfers erase compute gains. | 4 | 4 | 16 | distributed reviewer | topology probe and transfer microbenchmarks before placement | KV transfer dominates TTFT/TPOT |

## Review cadence

Review on every phase transition, architecture ADR, new backend, new runner, or benchmark-method change. Close a risk only with evidence, not optimism.
