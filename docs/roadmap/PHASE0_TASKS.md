# Phase 0 Task Index

| Task | Status | Deliverable | Gate |
|---|---|---|---|
| P0-T01 | complete and locally verified | generate Phase 0 operating system | `make verify`: 11 tests passed |
| P0-T02 | complete | public canonical remote, merged Phase 0, solo review policy, deterministic mobile hashing and post-merge CI | merges `20bc5fa…` and `843f812…`; 13 tests passed |
| P0-T03 | in progress, owner-admin blocked | public-repository policy, security workflows, audit and `main` protection | PR #9 gates/review pass; direct protected-main evidence remains |
| P0-T04 | blocked on P0-T03 | collect first sanitized hardware inventory | protected `main`, approved public/private data boundary and authorized lab machine |
| P0-T05 | blocked on P0-T04 | define P1 workload profiles | reviewed hardware/topology evidence and owner metrics/models |
| P0-T06 | blocked on P0-T05 | write P1 baseline implementation plan | reviewed profile specification |

## P0-T03 evidence

- repository visibility: public by owner decision and direct API;
- `main.protected=false`, status-check enforcement off and no rulesets;
- reviewed head `9d3b47365aa017f37b16a6f8c7e307677a7526cf`;
- Phase 0 run `31681837631` / job `94388820133`: success, **17 tests**;
- CodeQL run `31681837665` / job `94388813356`: success, 62 modules, 52 queries, SARIF processed; alert details unknown;
- Dependency Review run `31681837651`: skipped by opt-in;
- failed capability probe `31681032967` / `94386280488`: Dependency Graph disabled;
- fresh-context verdict: `ACCEPT` for governance merge, not task completion;
- no self-hosted runner is authorized.
