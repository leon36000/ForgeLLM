# P0-T08 / CA-03 — Exact Speculative-Decoding Semantics Review

- **Task:** P0-T08 / CA-03
- **Owner authorization:** `subagent-driven`, recorded 2026-08-14
- **Pull request:** #24
- **Base commit:** `1cd502609c7b05ac628057f79a9135b07c08e821`
- **Implementation-reviewed head:** `16efc462270a45f386a339aaeccef9d4d773b4a4`
- **Canonical specification:** `docs/superpowers/specs/2026-08-14-exact-speculative-decoding-semantics.md`
- **Canonical plan:** `docs/superpowers/plans/2026-08-14-exact-speculative-decoding-reference.md`
- **Review date:** 2026-08-14
- **Evidence boundary:** `finite_exact_reference`

## Review separation

Two explicit review passes were performed against the same implementation-reviewed head.

1. **Specification-compliance review:** checks mathematical semantics, state boundaries, EOS/budget behavior, public API correspondence and task-packet scope.
2. **Code-quality review:** checks exact arithmetic, immutable witnesses, invalid direct construction, deterministic diagnostics, adversarial coverage and absence of hidden environment or hardware dependencies.

The implementation may be merged only after both passes accept it and the final documentation head repeats the hosted Phase 0 and CodeQL gates.

## Specification-compliance review — ACCEPT

### Exact finite probabilities

- `ExactDistribution` uses `fractions.Fraction` exclusively for governed probability mass.
- Invalid, duplicate, negative, boolean and zero-total inputs fail closed.
- Support order and argmax tie-breaking are deterministic.
- `RandomTape` is immutable, rejects exhaustion/out-of-range draws and never applies modulo reduction.
- Deterministic categorical and Bernoulli decisions consume no draw.

### Modified rejection sampling

ForgeLLM notation remains consistent:

- `p` is the target distribution;
- `q` is the recorded proposal distribution actually used to sample the proposal.

The one-token oracle implements:

```text
alpha(x) = min(1, p(x) / q(x))
```

At first rejection it samples from normalized `(p-q)_+`. A proposal with `q(x) == 0`, a zero-mass residual or an impossible manually constructed acceptance/rejection witness is rejected.

### Sampled block semantics

- Proposals are generated autoregressively and retain their exact prefix and `q_i`.
- Verification is consecutive and left-to-right.
- No token after the first rejected proposal is accepted or committed.
- A rejection emits exactly one residual correction.
- A fully accepted non-EOS block emits a target bonus only when budget remains.
- EOS has precedence over rejection and bonus classification.
- A round cannot propose or emit more tokens than its remaining budget.
- Acceptance-probability witnesses are immutable tuples and have exact branch-consistent lengths and values.

### Exact equality of law

The exhaustive oracle compares canonical maps from emitted token sequences to exact rational mass. The committed tests cover:

- budgets `0..4`;
- draft lengths `1..3`;
- `p == q`;
- partial overlap;
- disjoint support;
- target-zero proposed tokens;
- sharply perturbed drafts;
- deterministic and stochastic distributions;
- prefix-dependent target and draft tables;
- non-empty initial prefixes;
- EOS in proposal, correction and bonus paths;
- composition across multiple speculative rounds.

The speculative and ordinary target laws are asserted equal exactly, without Monte Carlo sampling or floating-point tolerance. The documentation explicitly rejects same-seed token identity as the stochastic exactness criterion.

### Greedy oracle

The greedy path is separate from stochastic sampling, accepts no random tape and uses the smallest token ID on an exact argmax tie. Matching, mismatch, bonus, EOS, budget and non-empty-prefix cases equal ordinary target greedy decoding.

### Transactional state

- Target and draft materialized prefixes remain identical.
- Sampler and grammar witnesses equal visible output.
- Accepted proposal state is materialized.
- Rejected proposal suffix state is discarded.
- One residual or bonus token may remain pending.
- Pending synchronization materializes the token in both witnesses.
- Cancellation restores the exact original state.
- Finished, pending, empty-proposal and closed transactions fail closed, including direct dataclass construction.

### Trace and public API

`canonical_trace_document` and `canonical_trace_bytes` serialize exact rational values and immutable state without timestamps, hostnames, absolute paths or random IDs. `build_trace_document` remains a compatibility wrapper. Public exports match the planned stable oracle surface.

### Scope

All changed files are included in the P0-T08 allowed paths. No neural model, tokenizer, hardware probe, benchmark, Rust runtime, C ABI, accelerator backend, kernel, tree speculation, Transition Atlas implementation or approximate verifier is introduced.

## Code-quality review — ACCEPT

### Public-construction invariants

The review added regression tests and fail-closed guards for:

- empty direct `FiniteTableModel` construction;
- non-`RandomTape` deterministic Bernoulli calls;
- mutable/non-tuple acceptance-probability witnesses;
- proposal count greater than budget;
- open `RoundTransaction` construction from finished/pending/empty states;
- transaction commit with a non-result object;
- accepted decisions with zero acceptance probability;
- rejected decisions with probability one;
- a residual correction equal to the rejected proposal token;
- accepted round positions with zero probability;
- rejected round positions with probability one.

### Determinism and exact arithmetic

- Governed probabilities remain `Fraction` values.
- Enumeration aggregates exact branch mass and requires total mass exactly one.
- Canonical ordering is deterministic.
- Traces contain no environment-dependent field.
- Error classes are stable and distinguish distribution, proposal, model, law, state and transaction failures.

### Maintainability

The original large verification functions were decomposed into focused helpers while preserving the mathematical behavior. Module and test names were aligned with the task packet. The Makefile contains an explicit `verify-speculative` gate and task-owned Ruff-format scope; pre-existing repository formatting debt outside the packet was not modified.

## Findings resolved before acceptance

### MAJOR — branch initially failed Ruff and format gates

Imports, line wrapping and formatting were normalized. Ruff check and task-owned format verification now pass.

### MAJOR — invalid random-tape test vector

A test expected an out-of-range error from a draw that was actually valid. The vector was corrected so the asserted branch is genuinely exercised.

### MAJOR — bonus termination precedence

The initial result validator classified a fully accepted bonus that consumed the remaining budget as `budget`. The canonical precedence was restored: a non-EOS bonus is `all_accepted`; EOS remains `eos`.

### MAJOR — implementation paths and APIs diverged from the packet

Module/test names, public signatures, error names and exports were aligned with the approved specification and task packet. Out-of-scope duplicate files were removed.

### MAJOR — prefix-dependent equality was not explicit

An exact-law regression family with genuinely different distributions by prefix was added.

### MAJOR — invalid public dataclass construction could bypass factories

Direct empty table construction, invalid round witnesses and non-executable transactions now fail in `__post_init__`.

### MAJOR — impossible probability witnesses were constructible

The oracle now rejects acceptance with probability zero, rejection with probability one and residual emission of the proposed token, both at one-token and round-witness levels.

### MINOR — canonical trace API name absent

`canonical_trace_document` was added and exported. The earlier name remains a compatibility wrapper.

### MINOR — overlapping negative tests obscured the intended invariant

A test that violated budget and suffix invariants simultaneously was made discriminating by using a legal budget.

## Hosted evidence on the implementation-reviewed head

On `16efc462270a45f386a339aaeccef9d4d773b4a4`:

- Phase 0 run `31831427741`, job `94867790897`: `success`;
- Ruff check and task-owned Ruff format verification: pass;
- project, research, benchmark and task validators: pass;
- complete suite: **332 passed**;
- focused `verify-speculative`: **230 passed**;
- existing canonical P0-T07 simulation/evidence gate: pass;
- CodeQL run `31831427752`, job `94867791028`: `success`;
- Dependency Review run `31831427740`: skipped by policy and not counted as executed evidence.

CodeQL workflow success proves execution and SARIF processing; this report does not assert zero alerts.

## Residual evidence limits

Acceptance proves only the finite exact Python reference semantics. It does not establish:

- floating-point, quantized or neural-model equivalence;
- tokenizer or model-family support;
- real KV tensors or concurrent memory safety;
- CPU/GPU placement or cache residency;
- batching, disaggregation, distributed execution or networking;
- latency, throughput, energy, acceptance-rate or response-quality improvement;
- production runtime readiness.

## Verdict

**Specification compliance: ACCEPT.**  
**Code quality: ACCEPT.**

P0-T08 remains in `review` until the final PR documentation head passes hosted Phase 0 and CodeQL, the PR is merged, and the merge commit passes the same post-merge gates. Only then may a separate state PR archive the task as complete and advance the canonical state.
