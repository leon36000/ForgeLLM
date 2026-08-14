# ForgeLLM Handoff

**From state:** S-0006  
**To work:** CA-03 — exact speculative-decoding reference semantics  
**Generated:** 2026-08-14

## Canonical status

- repository: `leon36000/ForgeLLM`;
- protected default branch: `main`;
- P0-T07 merge: `b0f3f241537b50de0dd3c0cb7bc2e6bf274a7034`;
- P0-T07: complete;
- P0-T04: blocked only on owner host designation;
- CA-03: owner-authorized for subagent-driven execution;
- hardware/model/runtime work under CA-03: forbidden.

## P0-T07 evidence

Final pull-request head `99c1c1488f622a6d4290e21a17ff313a1c3568c6`:

- Phase 0 `31784275654` / `94716606110`: success;
- 102 tests passed;
- canonical synthetic scenario executed;
- CodeQL `31784275655` / `94716597658`: success;
- Dependency Review `31784275656`: skipped;
- fresh-context verdict: `ACCEPT`.

Post-merge on `b0f3f241537b50de0dd3c0cb7bc2e6bf274a7034`:

- Phase 0 `31784610893` / `94717633943`: success;
- CodeQL `31784610881` / `94717633957`: success.

Synthetic hashes:

```text
6738d9596a2a9b9224a68e071a94463cdcbe7cff10a7cd30c4de29cd3381aa2f  topology
3aa6dcb2504aebee7c3db236abdd59867efe25296420bdc7e9ba1883061f4cb5  component profile
e5eb661bb48eca62b778714670000f963922ca459cb8590b3717150993a921ae  generated result
```

The machine-readable closeout is `artifacts/simulations/P0-T07-closeout-evidence.json`.

## CA-03 required scope

CA-03 must produce a placement-independent exact reference for speculative decoding.

### Required semantics

1. An exact finite distribution representation with explicit normalization.
2. Proposal sampling from `q`.
3. Per-token acceptance probability `min(1, p(x)/q(x))`.
4. On rejection, sampling from normalized positive residual `(p-q)_+`.
5. A target bonus token when all proposals are accepted and budget/EOS permit.
6. A separate greedy oracle with deterministic tie-breaking.
7. Transactional target/draft KV and auxiliary state:
   - retain only accepted proposal state;
   - discard rejected proposal suffix state;
   - treat replacement/bonus token state according to the next target evaluation boundary;
   - roll back atomically on cancellation.
8. Exhaustive finite probability-law tests against ordinary target decoding.
9. Explicit handling of zero-probability proposal entries, EOS and output budget.
10. No same-seed sequence-identity claim; exactness means equality of output law, not identical random-number consumption.

## Required process

1. Review primary sources and register scoped claims.
2. Commit a written CA-03 specification.
3. Write a detailed TDD implementation plan.
4. Create a schema-valid P0 task packet with explicit allowed paths.
5. Implement by isolated tasks.
6. Review specification compliance and code quality separately.
7. Run exact-head hosted Phase 0 and CodeQL gates.
8. Update state only after merge and post-merge verification.

## Evidence boundary

CA-03 may use finite table-defined synthetic target/draft models. It may not download a model, run a GPU, benchmark performance or implement the production runtime.

## Parallel hardware task

P0-T04 may start later when the owner designates one host and mode. CA-03 does not satisfy, replace or weaken the hardware and workload gates.
