# Phase 0 Task Index

| Task | Status | Deliverable | Gate |
|---|---|---|---|
| P0-T01 | complete and locally verified | generate Phase 0 operating system | `make verify`: 11 tests passed |
| P0-T02 | complete | public canonical remote, merged Phase 0, solo review policy, deterministic mobile hashing and post-merge CI | merges `20bc5fa…` and `843f812…`; 13 tests passed |
| P0-T03 | complete | public-repository policy, hosted security gates and protected `main` | active ruleset `FLLM` id `20820530`; `main.protected=true` |
| P0-T04 | blocked on owner host designation | collect first sanitized hardware/software inventory | one approved host label and execution mode |
| P0-T05 | blocked on P0-T04 | define P1 workload profiles | reviewed hardware/topology evidence and owner metrics/models |
| P0-T06 | blocked on P0-T05 | write P1 baseline implementation plan | reviewed profile specification |

## P0-T03 final evidence

- GitHub reports `main.protected=true`;
- repository ruleset `FLLM` is active and targets exactly `refs/heads/main`;
- no bypass actors are configured;
- pull requests, linear history, resolved conversations and squash-only merge are required;
- strict required check is `Validate and test` from GitHub Actions integration id `15368`;
- issue #10 is closed as completed.

## P0-T04 entry condition

Issue #12 and `tasks/open/P0-T04-first-hardware-inventory.yaml` define the next task. Execution begins only after the owner designates one project-safe host label and an execution mode.
