# Phase 0 Task Index

| Task | Status | Deliverable | Gate |
|---|---|---|---|
| P0-T01 | complete and locally verified | generate Phase 0 operating system | `make verify`: 11 tests passed |
| P0-T02 | complete | public canonical remote, merged Phase 0, solo review policy, deterministic mobile hashing and post-merge CI | merge `20bc5fa…`; S-0003 merge `843f812…`; 13 tests passed |
| P0-T03 | in progress, owner-admin blocked | public-repository policy, security workflows, audit and main protection | PR CI/review plus direct protected-main evidence |
| P0-T04 | blocked on P0-T03 | collect first sanitized hardware inventory | protected `main`, approved public/private data boundary and authorized lab machine |
| P0-T05 | blocked on P0-T04 | define P1 workload profiles | reviewed hardware/topology evidence and owner metrics/models |
| P0-T06 | blocked on P0-T05 | write P1 baseline implementation plan | reviewed profile specification |

## P0-T03 direct evidence

- repository visibility: public by owner decision and direct API;
- `main.protected=false` and status-check enforcement off;
- repository rulesets: none;
- CodeQL execution/upload previously succeeded; alert details remain inaccessible;
- Dependency Review is enabled by this task for internal public pull requests;
- no self-hosted runner is authorized.
