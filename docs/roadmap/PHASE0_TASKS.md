# Phase 0 Task Index

| Task | Status | Deliverable | Gate |
|---|---|---|---|
| P0-T01 | complete and locally verified | generate Phase 0 operating system | `make verify`: 11 tests passed |
| P0-T02 | complete | public canonical remote, merged Phase 0, solo review policy, deterministic mobile hashing and post-merge CI | merges `20bc5fa…` and `843f812…`; 13 tests passed |
| P0-T03 | complete | public-repository policy, hosted security gates and protected `main` | active ruleset `FLLM` id `20820530`; `main.protected=true` |
| P0-T04 | blocked on owner host designation | collect first sanitized hardware/software inventory | one approved host label and execution mode |
| P0-T05 | blocked on P0-T04 | define P1 workload profiles | reviewed hardware/topology evidence and owner metrics/models |
| P0-T06 | blocked on P0-T05 | write P1 baseline implementation plan | reviewed profile specification |
| P0-T07 | complete | synthetic cache-aware topology and placement simulator | PR #20; 102 tests; canonical simulation; PR and post-merge CodeQL/Phase 0 success |
| P0-T08 / CA-03 | owner-authorized, packet next | exact speculative-decoding reference semantics | reviewed specification/plan, finite exact-law oracle and transactional state tests |

## P0-T07 final evidence

- implementation merge: `b0f3f241537b50de0dd3c0cb7bc2e6bf274a7034`;
- final PR head: `99c1c1488f622a6d4290e21a17ff313a1c3568c6`;
- Phase 0 run `31784275654`, job `94716606110`: success, 102 tests;
- CodeQL run `31784275655`, job `94716597658`: success;
- post-merge Phase 0 `31784610893` / `94717633943`: success;
- post-merge CodeQL `31784610881` / `94717633957`: success;
- evidence boundary: `synthetic_only`;
- no hardware, model, runtime, ABI or kernel work occurred.

## P0-T04 entry condition

Issue #12 and `tasks/open/P0-T04-first-hardware-inventory.yaml` remain authoritative. Execution begins only after the owner designates one project-safe host label and an execution mode.

## CA-03 entry condition

The owner authorized CA-03 on 2026-08-14. Work begins with a primary-source-backed written specification, TDD plan and schema-valid bounded task packet. CA-03 uses finite synthetic probability tables only and cannot bypass P0-T04/P0-T05.
