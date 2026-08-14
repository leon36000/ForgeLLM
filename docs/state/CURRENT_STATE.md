# ForgeLLM Current State

- **State ID:** S-0007
- **Updated:** 2026-08-14
- **Phase:** P0
- **Milestone:** P0-M6 — exact speculative-decoding reference verified
- **Overall status:** P0-T08 / CA-03 is complete; P0-T09 / QG-01 is owner-authorized and active in read-only diagnosis; P0-T04 remains blocked on designation of one owner-authorized host
- **Authorized next work:** freeze and classify P0-T09 evidence without changing Sonar/GitHub configuration; P0-T04 may proceed independently after host designation
- **State anchor:** the Git commit containing this file

## Objective

Preserve the exact speculative-decoding oracle as the correctness reference for later cache-aware, accelerator and runtime implementations while restoring a reproducible and truthful SonarQube Cloud quality signal for protected `main`.

## Canonical repository

- Repository: `leon36000/ForgeLLM`.
- Default branch: protected `main`.
- Canonical P0-T09 base: `1b1a3621fcdf4129268663c497cdcd53aed48c29`.
- Active task packet: `tasks/open/P0-T09-sonarqube-main-analysis.yaml`.
- Tracking issue: #26.
- Execution branch: `feat/p0-t09-sonar-diagnosis`.
- Owner authorization: `P0-T09 / subagent-driven`, recorded 2026-08-14.

## P0-T08 / CA-03 completion

CA-03 delivered a placement-independent finite exact oracle for stochastic and greedy speculative decoding.

### Delivered capabilities

- canonical finite distributions using `fractions.Fraction`;
- immutable deterministic `RandomTape` with no modulo reduction;
- exact Bernoulli and one-token modified rejection sampling;
- recorded proposal distributions and prefixes;
- first-rejection correction from normalized `(p-q)_+`;
- legal target bonus, EOS and output-budget semantics;
- exact ordinary-target and speculative output-law enumeration;
- exact-law grids for budgets 0–4 and draft lengths 1–3, including prefix-dependent and adversarial models;
- separate deterministic greedy oracle;
- transactional materialized/pending target, draft, sampler and grammar witnesses;
- cancellation rollback and pending-token synchronization;
- deterministic environment-free traces;
- fail-closed guards for invalid direct constructions and impossible probability witnesses;
- explicit `verify-speculative` repository gate.

### Final evidence

- implementation head `16d65288b34a9f2f91a4c67182aab13ddfb5e17d`;
- implementation merge `e6c9d1ae30f1b5e161a56bf8c9b4fa25c823fe24`;
- complete suite: **332 passed**;
- focused `verify-speculative`: **230 passed**;
- specification-compliance review `4940413742`: `ACCEPT`;
- code-quality review `4940415259`: `ACCEPT`;
- remediation head `a7f508fe1fa4787b889445c5e5986339b508217a`;
- remediation merge `e81c1c0ad0b161844569df46ee62246c9de56698`;
- evidence boundary: `finite_exact_reference`.

## P0-T09 / QG-01 active diagnosis

### Public evidence frozen

The baseline is recorded in:

- `artifacts/governance/P0-T09-sonar-baseline.json`;
- `docs/quality/P0-T09-SONAR-BASELINE.md`.

The public GitHub evidence reproduces this pattern three times:

1. a pull-request Sonar quality gate succeeds with zero new issues;
2. Phase 0 and CodeQL succeed;
3. the resulting `main` Sonar check is completed as `cancelled` with `SonarQube Cloud analysis failed` and zero GitHub annotations.

Relevant `main` checks are `94890528740`, `94892860919`, and `94894966719`.

### Repository readback

At the canonical base tree:

- no `.github/workflows/sonar.yml` exists;
- no `sonar-project.properties` exists;
- no `.sonarcloud.properties` exists.

The GitHub SonarQube Cloud App produces the checks. This is consistent with automatic analysis but is not an authenticated readback of the Sonar **Analysis Method** setting.

### Current classification

```text
failure_classification = unknown_due_to_missing_authenticated_evidence
method_selection       = not_selected
configuration_changes  = none
```

Authenticated read-only evidence is still required for project binding, analysis method, failed task message, quality gate, new-code definition, scope settings, plan/tier, and confirmation that no external CI scanner submits to the same project.

### Hard gate

No Sonar or GitHub analysis configuration may change until:

1. the missing read-only evidence is captured in sanitized form;
2. the failure is classified without guessing;
3. ADR-0004 selects exactly one method: `automatic_only` or `ci_based_only`;
4. the selected method and rollback are reviewed.

Automatic and CI-based analysis must never run concurrently for the same Sonar project.

## Established claims

Within the finite exact oracle and committed test families:

- modified rejection sampling recovers the target output law exactly;
- changing a valid draft distribution changes branch behavior but not the final target law;
- the greedy speculative oracle equals ordinary target greedy decoding;
- rejected speculative suffix state is not committed;
- cancellation restores the original token-prefix witness exactly;
- same-seed token identity is not the stochastic correctness criterion.

## Evidence boundaries

P0-T08 evidence is `finite_exact_reference`. It does not establish real-model, floating-point, KV-tensor, hardware, performance, distributed, or production behavior.

P0-T09 evidence is currently `quality_governance_read_only`. It establishes a repeated GitHub check pattern, not the internal Sonar failure cause or the selected remediation method.

## Active and blocked work

### P0-T09

Status: `in_progress`, blocked after the public read-only baseline on owner-authenticated Sonar project administration/activity readback.

### P0-T04

`tasks/open/P0-T04-first-hardware-inventory.yaml` remains observation-only and blocked on a project-safe host label and execution mode.

### P0-T05 and P0-T06

They remain blocked behind the reviewed inventory and workload/SLO definitions.

### Future research

Transition Atlas and runtime conformance may use CA-03 as an oracle, but neither is authorized by S-0007.

## Forbidden next steps

- no Sonar/GitHub configuration change before authenticated diagnosis and ADR-0004;
- no automatic and CI-based analysis concurrently;
- no token, private administrative payload, or hidden issue suppression in Git;
- no hardware benchmark before P0-T04 and P0-T05;
- no model download or production inference under P0-T09;
- no claim that finite exact semantics proves real-model or hardware behavior;
- no Transition Atlas, runtime, C ABI, backend, or kernel implementation without a new authorization packet.
