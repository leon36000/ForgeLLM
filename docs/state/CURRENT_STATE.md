# ForgeLLM Current State

- **State ID:** S-0007
- **Updated:** 2026-08-14
- **Phase:** P0
- **Milestone:** P0-M6 — exact speculative-decoding reference verified
- **Overall status:** P0-T08 / CA-03 is complete with finite exact-reference evidence; P0-T04 remains blocked on designation of one owner-authorized host; SonarQube Cloud pull-request analysis is clean while automatic `main` analysis remains an open tooling discrepancy tracked by QG-01 / issue #26
- **Authorized next work:** P0-T04 after owner host designation; QG-01 requires a separate schema-valid task packet before configuration changes; no model, runtime, backend, kernel or Transition Atlas implementation is authorized
- **State anchor:** the Git commit containing this file

## Objective

Preserve the exact speculative-decoding oracle as the correctness reference for later cache-aware, accelerator and runtime implementations while keeping observed-hardware and workload claims behind P0-T04 and P0-T05.

## Canonical repository

- Repository: `leon36000/ForgeLLM`.
- Default branch: protected `main`.
- P0-T08 implementation pull request: #24.
- Final implementation head: `16d65288b34a9f2f91a4c67182aab13ddfb5e17d`.
- Implementation merge: `e6c9d1ae30f1b5e161a56bf8c9b4fa25c823fe24`.
- Sonar remediation pull request: #25.
- Final remediation head: `a7f508fe1fa4787b889445c5e5986339b508217a`.
- Remediation merge: `e81c1c0ad0b161844569df46ee62246c9de56698`.

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

### Implementation pull-request evidence

On `16d65288b34a9f2f91a4c67182aab13ddfb5e17d`:

- Phase 0 run `31831781322`, job `94868927648`: success;
- complete suite: **332 passed**;
- focused `verify-speculative`: **230 passed**;
- CodeQL run `31831781266`, job `94868926709`: success;
- specification-compliance review `4940413742`: `ACCEPT`;
- code-quality review `4940415259`: `ACCEPT`.

The SonarQube Cloud analysis on PR #24 failed and exposed two production-code maintainability findings plus test-code smells. The two production findings were fixed in the separate remediation PR #25 before task closeout.

### Sonar remediation evidence

On `a7f508fe1fa4787b889445c5e5986339b508217a`:

- Phase 0 run `31838436974`, job `94889874946`: success;
- CodeQL run `31838436902`, job `94889874310`: success;
- CodeQL check `94890057549`: no new alerts in code changed by the pull request;
- SonarQube Cloud check `94889986512`: Quality Gate passed, 0 new issues, 0 accepted issues and 0 security hotspots;
- GitGuardian check `94889866775`: success;
- Dependency Review run `31838436968`: skipped by policy.

### Final post-merge evidence

On `main` commit `e81c1c0ad0b161844569df46ee62246c9de56698`:

- Phase 0 run `31838603770`, job `94890388826`: success;
- CodeQL run `31838603775`, job `94890388594`: success.

CodeQL workflow success proves execution and SARIF processing; zero repository-wide alerts are not asserted.

## SonarQube Cloud discrepancy

The automatic SonarQube Cloud analysis of `main` at `e81c1c0ad0b161844569df46ee62246c9de56698` was reported as cancelled / analysis failed by check `94890528740`, with no GitHub annotations. This does not overturn the clean exact-head PR quality gate, but it prevents a claim that Sonar branch analysis is healthy. QG-01 / issue #26 tracks the integration investigation. No Sonar issue is suppressed or accepted merely to make a gate green.

## Established claims

Within the finite exact oracle and committed test families:

- modified rejection sampling recovers the target output law exactly;
- changing a valid draft distribution changes branch behavior but not the final target law;
- the greedy speculative oracle equals ordinary target greedy decoding;
- rejected speculative suffix state is not committed;
- cancellation restores the original token-prefix witness exactly;
- same-seed token identity is not the stochastic correctness criterion.

## Evidence boundary

P0-T08 evidence is `finite_exact_reference`. It does not establish:

- floating-point or quantized numerical equivalence;
- correctness of any neural model or tokenizer;
- real KV tensors, concurrent memory safety or batching;
- CPU/GPU placement, cache residency or overlap;
- distributed execution or networking;
- latency, throughput, energy, acceptance-rate or quality improvement;
- production runtime, ABI, backend or kernel readiness.

## Active and blocked work

### P0-T04

`tasks/open/P0-T04-first-hardware-inventory.yaml` remains observation-only and blocked on one owner input: a project-safe host label and execution mode.

### P0-T05 and P0-T06

They remain blocked behind the reviewed inventory and workload/SLO definitions.

### QG-01

Issue #26 tracks SonarQube Cloud `main`-branch analysis reliability. It is a proposed quality-governance package only; configuration changes require a reviewed task packet.

### Future research

Transition Atlas and runtime conformance may use CA-03 as an oracle, but neither is authorized by S-0007. Each requires a separate primary-source-backed specification, plan and task packet.

## Forbidden next steps

- no hardware benchmark before P0-T04 and P0-T05;
- no model download or production inference under the completed CA-03 task;
- no claim that finite exact semantics proves real-model or hardware behavior;
- no claim that PR-level Sonar success establishes a healthy `main` analysis;
- no Transition Atlas, runtime, C ABI, backend or kernel implementation without a new authorization packet;
- no approximate quality-changing policy presented as exact speculative decoding.
