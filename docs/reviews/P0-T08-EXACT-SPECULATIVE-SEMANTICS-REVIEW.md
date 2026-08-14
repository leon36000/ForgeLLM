# P0-T08 / CA-03 — Exact Speculative-Decoding Semantics Review

- **Task:** P0-T08 / CA-03
- **Owner authorization:** `subagent-driven`, recorded 2026-08-14
- **Implementation pull request:** #24
- **Remediation pull request:** #25
- **Base:** `1cd502609c7b05ac628057f79a9135b07c08e821`
- **Final implementation head:** `16d65288b34a9f2f91a4c67182aab13ddfb5e17d`
- **Implementation merge:** `e6c9d1ae30f1b5e161a56bf8c9b4fa25c823fe24`
- **Final remediation head:** `a7f508fe1fa4787b889445c5e5986339b508217a`
- **Remediation merge:** `e81c1c0ad0b161844569df46ee62246c9de56698`
- **Review date:** 2026-08-14
- **Evidence boundary:** `finite_exact_reference`
- **Final verdict:** `ACCEPT`

## Review separation

Two explicit implementation passes were performed and anchored in PR #24:

1. specification-compliance review `4940413742` — `ACCEPT`;
2. code-quality review `4940415259` — `ACCEPT`.

A third targeted remediation review was recorded on PR #25 after SonarQube Cloud exposed two production-code maintainability findings.

## Specification-compliance assessment

The implementation conforms to the canonical CA-03 specification:

- exact finite distributions use `fractions.Fraction`;
- `p` denotes target and `q` the recorded proposal distribution actually used;
- acceptance is `min(1, p(x)/q(x))`;
- first rejection samples normalized `(p-q)_+` and discards the proposal suffix;
- a target bonus is emitted only after a fully accepted non-EOS block with budget remaining;
- EOS, rejection, budget and all-accepted termination are explicit;
- exact target/speculative laws are compared as canonical rational maps;
- coverage includes budgets 0–4, draft lengths 1–3, equal/partial/disjoint support, target-zero proposals, sharply perturbed drafts, prefix-dependent tables, non-empty prefixes, EOS and multi-round composition;
- stochastic exactness means equality of output law, not same-seed identity;
- greedy decoding has a separate deterministic oracle;
- accepted state commits, rejected suffix state is discarded, pending correction/bonus state is explicit and cancellation is atomic;
- traces contain exact rational values and no environment-dependent metadata.

No model, tokenizer, hardware, benchmark, runtime, C ABI, backend, kernel, Transition Atlas or approximate verifier is introduced.

## Code-quality assessment

The reviewed implementation fails closed on malformed distributions, invalid random sources, empty tables, proposal/support mismatches, mutable or impossible probability witnesses, budget overrun, hidden suffix acceptance, invalid EOS/branch traces and invalid transaction states.

Public errors are stable, exact arithmetic has no tolerance path, and deterministic ordering and trace serialization are preserved.

## Findings resolved in PR #24

- Ruff import/format failures;
- an invalid random-tape negative test;
- incorrect bonus termination precedence;
- module/test paths and signatures outside the approved packet;
- missing explicit prefix-dependent law family;
- invalid direct dataclass construction bypassing factory guards;
- impossible probability witnesses;
- missing canonical `canonical_trace_document` API;
- overlapping negative tests that obscured the intended invariant.

Every valid finding received a regression test before or with the minimal fix.

## SonarQube Cloud remediation

The PR #24 Sonar analysis failed and reported two production-code maintainability findings: a repeated RandomTape validation literal and a helper returning variable tuple shapes. PR #25 changed only those two surfaces:

- the literal is centralized in `RANDOM_TAPE_REQUIRED`;
- `_completion_outcomes` consistently returns a list.

The exact-head PR #25 diff contained no semantic change to the finite oracle.

## Exact-head implementation evidence

On `16d65288b34a9f2f91a4c67182aab13ddfb5e17d`:

- Phase 0 run `31831781322`, job `94868927648`: success;
- complete suite: **332 passed**;
- focused `verify-speculative`: **230 passed**;
- CodeQL run `31831781266`, job `94868926709`: success;
- Dependency Review run `31831781321`: skipped by policy.

## Exact-head remediation evidence

On `a7f508fe1fa4787b889445c5e5986339b508217a`:

- Phase 0 run `31838436974`, job `94889874946`: success;
- CodeQL run `31838436902`, job `94889874310`: success;
- CodeQL check `94890057549`: no new alerts in changed code;
- SonarQube Cloud check `94889986512`: Quality Gate passed, 0 new issues, 0 accepted issues, 0 security hotspots;
- GitGuardian check `94889866775`: success;
- Dependency Review run `31838436968`: skipped by policy.

## Final post-merge evidence

On `main` commit `e81c1c0ad0b161844569df46ee62246c9de56698`:

- Phase 0 run `31838603770`, job `94890388826`: success;
- CodeQL run `31838603775`, job `94890388594`: success.

## Sonar branch-analysis caveat

Automatic SonarQube Cloud analysis of `main` at the remediation merge was reported as cancelled / failed by check `94890528740`, with no GitHub annotations. The clean PR quality gate demonstrates that the remediation introduces no new Sonar issues; it does not prove that automatic branch analysis is operational. QG-01 / issue #26 tracks the integration discrepancy. This caveat does not weaken or suppress any finding.

## Residual limitations

The oracle does not establish floating-point or quantized equivalence, neural-model or tokenizer support, real KV tensors, concurrent memory safety, batching, hardware placement, cache residency, distributed execution, performance, energy, acceptance rate, quality or production readiness.

## Final decision

`ACCEPT` and archive P0-T08 as complete. Preserve P0-T04/P0-T05 as hardware and workload gates. Any future Transition Atlas, real-model conformance or runtime task must use this oracle but requires a new authorization packet. QG-01 requires its own task packet before Sonar configuration changes.
