# ForgeLLM Current State

- **State ID:** S-0007
- **Updated:** 2026-08-14
- **Phase:** P0
- **Milestone:** P0-M6 — exact speculative-decoding reference verified
- **Overall status:** P0-T08 / CA-03 is complete; P0-T09 / QG-01 is owner-authorized and active in read-only diagnosis; Sonar Automatic analysis is now owner-confirmed enabled and Recommended, while the `main` failure cause remains unknown; P0-T04 remains blocked on designation of one owner-authorized host
- **Authorized next work:** capture the failed `main` Sonar activity/task message and remaining read-only project settings without changing Sonar/GitHub configuration; P0-T04 may proceed independently after host designation
- **State anchor:** the Git commit containing this file

## Objective

Preserve the exact speculative-decoding oracle as the correctness reference for later cache-aware, accelerator and runtime implementations while restoring a reproducible and truthful SonarQube Cloud quality signal for protected `main`.

## Canonical repository

- Repository: `leon36000/ForgeLLM`.
- Default branch: protected `main`.
- Initial P0-T09 base: `1b1a3621fcdf4129268663c497cdcd53aed48c29`.
- Latest diagnostic `main` probe: `bd03e479ff4649a254c41726b33f2b6e841a0e0c`.
- Active task packet: `tasks/open/P0-T09-sonarqube-main-analysis.yaml`.
- Tracking issue: #26.
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

### Public and owner-authenticated evidence

The evidence is recorded in:

- `artifacts/governance/P0-T09-sonar-baseline.json`;
- `artifacts/governance/P0-T09-sonar-analysis-method-readback.json`;
- `docs/quality/P0-T09-SONAR-BASELINE.md`.

The GitHub evidence now includes a post-import probe:

1. PR #30 Sonar check `94945852247` succeeded with 0 new issues and 0 security hotspots;
2. Phase 0 and CodeQL succeeded on the PR head;
3. the merged `main` commit `bd03e479ff4649a254c41726b33f2b6e841a0e0c` received Sonar check `94946081665`, completed `cancelled` with `SonarQube Cloud analysis failed` and zero GitHub annotations.

Therefore importing the project was not sufficient to repair the `main` analysis path.

### Analysis Method readback

An owner-authenticated screenshot of **SonarQube Cloud → ForgeLLM → Analysis method** confirms:

```text
Automatic analysis: enabled
Recommendation: Recommended
CI method selected: no
```

The raw screenshot is not committed. A sanitized transcription and its SHA-256 evidence binding are stored in `artifacts/governance/P0-T09-sonar-analysis-method-readback.json`.

This promotes the earlier repository-based inference to an observed project setting: ForgeLLM is currently configured for automatic analysis.

### Current classification

```text
analysis_method_setting = automatic_enabled
compatibility           = recommended
failure_classification  = automatic_analysis_enabled_root_cause_unknown
method_selection        = not_selected
configuration_changes   = none
```

The most important missing evidence is now the detailed failed `main` **Project Activity / analysis task** message. Binding, quality gate, new-code definition, scope/issue-ignore settings, plan/tier, and external-scanner confirmation are also still required before ADR-0004 may select a final method.

### Hard gate

No Sonar or GitHub analysis configuration may change until:

1. the remaining read-only evidence is captured in sanitized form;
2. the failed `main` task message allows the cause to be classified without guessing;
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

P0-T09 evidence is currently `quality_governance_read_only`. It now establishes the configured automatic-analysis method plus the repeated PR-success/`main`-failure pattern, but not the internal failure cause or the final remediation method.

## Active and blocked work

### P0-T09

Status: `in_progress`, blocked on the failed-main Sonar activity/task message and remaining read-only project administration evidence.

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
