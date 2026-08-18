# Phase 0 Task Index

| Task | Status | Deliverable | Gate |
|---|---|---|---|
| P0-T01 | complete and locally verified | generate Phase 0 operating system | `make verify`: 11 tests passed |
| P0-T02 | complete | canonical remote, review policy, deterministic mobile hashing and post-merge CI | merges `20bc5fa…` and `843f812…` |
| P0-T03 | complete | public-repository policy, hosted security gates and protected `main` | active ruleset `FLLM` |
| P0-T04 | blocked on owner host designation | collect first sanitized hardware/software inventory | one approved host label and execution mode |
| P0-T05 | blocked on P0-T04 | define P1 workload profiles | reviewed hardware/topology evidence and owner metrics/models |
| P0-T06 | blocked on P0-T05 | write P1 baseline implementation plan | reviewed profile specification |
| P0-T07 | complete | synthetic cache-aware topology and placement simulator | PR #20; 102 tests; PR/post-merge gates |
| P0-T08 / CA-03 | complete | finite exact speculative-decoding reference semantics | PR #24 + remediation PR #25; 332 complete and 230 focused tests; dual review; PR/post-merge gates |
| P0-T09 / QG-01 | in progress — remediation verification | stabilize SonarQube Cloud analysis on protected `main` | LOC-limit cause classified; ForgeLLM visibility remediation applied; evidence PR → protected `main` verification required |

## P0-T09 current gate

- owner command: `autorise P0-T09 / subagent-driven`;
- canonical base: `1b1a3621fcdf4129268663c497cdcd53aed48c29`;
- evidence branch: `forgeai/manual-p0-t09-evidence-update-20260817102053`;
- current canonical `main`: `484fec34007fd89f554c9c03bffa9a5275676602`;
- task packet: `tasks/open/P0-T09-sonarqube-main-analysis.yaml`;
- baseline JSON: `artifacts/governance/P0-T09-sonar-baseline.json`;
- baseline report: `docs/quality/P0-T09-SONAR-BASELINE.md`;
- configuration changes: `ForgeLLM Sonar visibility private -> public` only, under explicit owner authorization;
- failure classification: `platform_limitation / subscription_loc_limit_exceeded`;
- internal failed branch-task status: `FAILED`;
- post-remediation Billing & usage: Free plan, 50,000 private-LOC entitlement, 48,248 consumed, approximately 1.8k remaining;
- method selection: `not_selected`.

Public and owner-authenticated evidence now shows five PR-success/`main`-failure recurrences, with Phase 0 and CodeQL succeeding on the corresponding commits. Sonar Background Tasks establishes the internal branch-analysis status as `FAILED`, and the owner-authenticated error identifies the organization private-LOC subscription limit as the immediate cause. The canonical tree contains no Sonar scanner workflow or properties file.

The administrative readback records binding `leon36000/ForgeLLM`, Automatic Analysis/Autoscan, no CI method selected, New Code `previous_version`, default/no custom scope or issue-ignore settings, and default `Sonar way`. After ForgeLLM was aligned from private to public in Sonar, anonymous Sonar API access independently confirmed the public project while Billing & usage returned below the private-LOC limit.

The next gate is the reviewed evidence-update PR itself: its exact head must pass Sonar, Phase 0, CodeQL and GitGuardian; after merge, the resulting protected `main` Sonar check must complete successfully. No artificial probe is required. ADR-0004 may select exactly one analysis method only after this post-remediation cycle; Automatic and CI-based methods may not run concurrently.

## P0-T08 final evidence

- base: `1cd502609c7b05ac628057f79a9135b07c08e821`;
- final implementation head: `16d65288b34a9f2f91a4c67182aab13ddfb5e17d`;
- implementation merge: `e6c9d1ae30f1b5e161a56bf8c9b4fa25c823fe24`;
- Phase 0 implementation `31831781322` / `94868927648`: success;
- complete suite: 332 passed;
- focused exact-reference suite: 230 passed;
- CodeQL implementation `31831781266` / `94868926709`: success;
- specification-compliance review `4940413742`: `ACCEPT`;
- code-quality review `4940415259`: `ACCEPT`;
- remediation head: `a7f508fe1fa4787b889445c5e5986339b508217a`;
- remediation merge: `e81c1c0ad0b161844569df46ee62246c9de56698`;
- Phase 0 remediation `31838436974` / `94889874946`: success;
- CodeQL remediation `31838436902` / `94889874310`: success;
- SonarQube Cloud PR check `94889986512`: Quality Gate passed, 0 new issues, 0 security hotspots;
- evidence boundary: `finite_exact_reference`.

## P0-T04 entry condition

Issue #12 and `tasks/open/P0-T04-first-hardware-inventory.yaml` remain authoritative. Execution begins only after the owner designates one project-safe host label and an execution mode.

## Future research entry condition

Transition Atlas, real-model conformance and runtime integration remain proposals only. Each requires its own primary-source-backed specification, reviewed plan, schema-valid task packet and owner authorization. CA-03 provides a correctness oracle but does not authorize implementation of those paths.
