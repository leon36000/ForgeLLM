# ForgeLLM Exact Speculative-Decoding Reference Semantics

**Status:** owner-authorized design for P0-T08 / CA-03  
**Date:** 2026-08-14  
**Evidence boundary:** finite exact semantics only  
**Primary sources:** `PAP-SPECDEC`, `PAP-SPECSAMPLING`  
**Related claim:** `CLM-047`

## 1. Durable decision

ForgeLLM will maintain a placement-independent speculative-decoding oracle based on exact finite probability distributions. The oracle defines stochastic modified rejection sampling, a separate deterministic greedy path, exhaustive equality-of-law verification and transactional token-prefix state semantics.

Future CPU, GPU, cache-aware, multi-token or distributed implementations must conform to this oracle before performance promotion.

## 2. Goals

- Represent finite categorical distributions exactly and canonically.
- Sample proposals from the exact proposal distribution used for verification.
- Implement left-to-right acceptance with `min(1, p(x)/q(x))`.
- Implement first-rejection correction from normalized `(p-q)_+`.
- Emit a target bonus token after a fully accepted block when legal.
- Prove finite bounded output-law equality against ordinary target decoding.
- Define deterministic greedy behavior separately.
- Define atomic commit, rollback, pending-token and cancellation boundaries.
- Handle EOS, zero probabilities and output budgets without ambiguity.
- Produce deterministic traces suitable for later differential tests.

## 3. Non-goals

- Neural-model loading or inference.
- Floating-point logits, top-k, top-p, temperature or quantization numerics.
- Performance measurement or speedup claims.
- CPU/GPU placement, cache locality or overlap.
- Rust runtime, C ABI, backend, kernel or network implementation.
- Tree speculation, multiple simultaneous branches, Medusa or EAGLE.
- Transition Atlas implementation.
- Approximate verification, verifier regret or response-quality changes.
- Same-seed sequence identity between baseline and speculative algorithms.

## 4. Core notation

- Tokens are non-negative integers. Python `bool` is rejected even though it subclasses `int`.
- A prefix is `tuple[int, ...]`.
- `eos_token_id` is one token in the finite vocabulary.
- `p_i` is the target distribution at the prefix before position `i`.
- `q_i` is the exact proposal distribution used to sample proposal token `x_i`.
- Probabilities are `fractions.Fraction` values.

## 5. Exact finite distributions

### 5.1 Construction

`ExactDistribution` is immutable and constructed from token/weight pairs.

Validation:

- at least one pair;
- token IDs are unique non-negative non-boolean integers;
- weights are `int` or `Fraction`, non-negative and non-boolean;
- total weight is positive;
- zero-weight entries are removed;
- canonical support is sorted by token ID;
- stored probabilities sum exactly to `Fraction(1, 1)`.

### 5.2 Operations

```python
@dataclass(frozen=True, slots=True)
class ExactDistribution:
    probabilities: tuple[tuple[int, Fraction], ...]

    @classmethod
    def from_pairs(
        cls,
        pairs: Iterable[tuple[int, int | Fraction]],
    ) -> ExactDistribution: ...

    def probability(self, token: int) -> Fraction: ...
    def support(self) -> tuple[int, ...]: ...
    def argmax(self) -> int: ...
    def sample(self, tape: RandomTape) -> tuple[int, RandomTape]: ...
    def positive_residual(self, proposal: ExactDistribution) -> ExactDistribution: ...
```

`argmax()` chooses the smallest token ID on an exact tie.

`positive_residual(q)` computes and normalizes `max(0, self-q)`. It raises `UnreachableResidualError` when total positive residual is zero.

### 5.3 Immutable random tape

The exact oracle uses one functional random source only:

```python
@dataclass(frozen=True, slots=True)
class RandomTape:
    draws: tuple[int, ...]
    cursor: int = 0

    def draw(self, upper_bound: int) -> tuple[int, RandomTape]: ...
```

Each call returns the selected integer and a new advanced tape. It never mutates the original tape.

Rules:

- `upper_bound` is a positive non-boolean integer;
- the tape must have an unused draw;
- the draw must satisfy `0 <= draw < upper_bound`;
- out-of-range draws fail rather than using modulo reduction;
- deterministic categorical distributions consume no draw;
- exact Bernoulli probabilities zero and one consume no draw;
- every other Bernoulli uses `draw(denominator) < numerator`.

Exact categorical sampling converts rational probabilities to a common integer denominator and uses one bounded draw.

## 6. One-token modified rejection sampling

For proposal token `x` sampled from `q`:

```text
alpha(x) = min(1, p(x) / q(x))
```

Preconditions:

- `x` belongs to positive support of `q`;
- recorded `q` is the distribution used to generate `x`;
- `p` and `q` are normalized exact distributions over finite token IDs.

Algorithm:

1. Accept `x` with exact probability `alpha(x)`.
2. On acceptance emit `x`.
3. On rejection sample and emit from normalized `(p-q)_+`.
4. The one-token branch emits exactly one token.

Attempting rejection when `p == q`, sampling a proposal with `q(x)==0`, or sampling an empty residual fails closed.

## 7. Sampled speculative round

Inputs:

```python
@dataclass(frozen=True, slots=True)
class SampledRoundRequest:
    prefix: tuple[int, ...]
    draft_length: int
    remaining_budget: int
    eos_token_id: int
```

Validation:

- `draft_length` is a positive non-boolean integer;
- `remaining_budget` is a non-negative non-boolean integer;
- prefix and EOS token IDs follow token validation rules.

A finite autoregressive model implements:

```python
class DistributionModel(Protocol):
    def distribution(self, prefix: tuple[int, ...]) -> ExactDistribution: ...
```

### 7.1 Proposal phase

- If `remaining_budget == 0`, return immediately without model or random-tape access.
- Propose at most `min(draft_length, remaining_budget)` tokens autoregressively from the draft model.
- Record `(prefix_before_token, q_i, x_i)` for every proposal.
- Stop proposing after EOS.

### 7.2 Verification phase

For each proposal from left to right:

1. Obtain `p_i` from the target model at the same prefix.
2. Compute exact acceptance probability against the recorded `q_i`.
3. If accepted, append `x_i` and continue unless it is EOS.
4. At first rejection, discard every later proposal, sample one correction from `(p_i-q_i)_+`, append it and stop.

No token after the first rejected proposal can be accepted or committed.

### 7.3 Bonus phase

If all generated proposals are accepted, the last accepted token is not EOS, and budget remains, sample one bonus token from the target distribution at the accepted prefix. Append it and stop the round.

### 7.4 Result

```python
@dataclass(frozen=True, slots=True)
class SampledRoundResult:
    prefix: tuple[int, ...]
    proposed_tokens: tuple[int, ...]
    accepted_count: int
    emitted_tokens: tuple[int, ...]
    acceptance_probabilities: tuple[Fraction, ...]
    correction_kind: Literal["none", "residual", "bonus"]
    termination: Literal["budget", "eos", "rejection", "all_accepted"]
    tape: RandomTape
```

Invariants:

- `0 <= accepted_count <= len(proposed_tokens)`;
- acceptance probabilities correspond exactly to verified proposals through the first rejection or accepted EOS;
- accepted proposals equal the leading emitted proposal prefix;
- `len(emitted_tokens) <= remaining_budget`;
- `residual` emits exactly accepted prefix plus one correction;
- `bonus` emits every proposal plus one target token;
- EOS is the final emitted token when present;
- zero budget yields empty proposal/emission and unchanged tape.

Termination precedence is explicit:

1. `eos` when the final emitted token is EOS, regardless of whether it was accepted, residual or bonus;
2. `rejection` for a non-EOS residual correction;
3. `budget` when zero budget or a fully accepted block consumes the remaining budget without bonus;
4. `all_accepted` when a fully accepted non-EOS block emits a non-EOS bonus.

`correction_kind` records how the final non-proposal token was produced and therefore remains independent of `termination`.

## 8. Exact output-law enumerator

### 8.1 Table-defined models

`FiniteTableModel` maps every reachable prefix to an `ExactDistribution`. Missing prefixes fail closed. Tables are immutable, token IDs are finite and EOS is explicit.

### 8.2 Baseline law

`enumerate_target_law(model, prefix, budget, eos_token_id)` recursively enumerates ordinary target decoding and returns an immutable `ExactSequenceLaw`.

Sequences contain only newly emitted tokens. Probabilities are exact, canonical and sum to one.

### 8.3 Speculative law

`enumerate_speculative_law(target, draft, prefix, budget, draft_length, eos_token_id)` analytically enumerates:

- every draft proposal path;
- every consecutive acceptance path;
- every first-rejection residual branch;
- every fully accepted bonus branch;
- subsequent rounds until budget or EOS.

It does not rely on Monte Carlo sampling. The result is canonical and sums exactly to one.

### 8.4 Required equality tests

For each finite adversarial model family, assert exact equality of baseline and speculative laws for:

- budgets 0 through 4;
- draft lengths 1 through 3;
- `p == q`;
- partial overlap;
- sharply perturbed draft distributions;
- target-zero proposed tokens;
- deterministic distributions;
- prefix-dependent distributions;
- EOS at proposal, rejection-correction and bonus positions.

Equality is map equality over all emitted sequences and exact rational masses.

## 9. Separate greedy oracle

`greedy_target_decode` emits target argmax tokens until EOS or budget.

`greedy_speculative_decode`:

1. obtains draft argmax proposals autoregressively;
2. compares each to target argmax at the same prefix;
3. accepts only exact token equality;
4. on first mismatch emits target argmax and stops that round;
5. after a fully matching non-EOS block emits one target argmax bonus if budget remains.

No random tape is accepted by the greedy API. For every finite table model, bounded output must equal `greedy_target_decode` exactly.

## 10. Transactional state semantics

### 10.1 State witness

```python
@dataclass(frozen=True, slots=True)
class DecoderState:
    output_tokens: tuple[int, ...]
    target_materialized: tuple[int, ...]
    draft_materialized: tuple[int, ...]
    pending_token: int | None
    sampler_tokens: tuple[int, ...]
    grammar_tokens: tuple[int, ...]
    finished: bool
```

Invariants:

- target and draft materialized prefixes are equal;
- sampler and grammar prefixes equal output;
- without pending token, materialized prefix equals output;
- with pending token, output equals materialized prefix plus that token;
- pending token is the final output token;
- a finished state cannot begin a new round;
- a new round requires `pending_token is None`.

### 10.2 Transaction

`RoundTransaction.begin(state)` captures the original state and creates tentative proposal witnesses without mutating the original.

Commit rules:

- accepted proposal tokens extend target and draft materialized witnesses;
- rejected and later proposal witnesses are discarded;
- residual correction or bonus extends output/sampler/grammar and becomes `pending_token`;
- accepted EOS is materialized, sets `finished=True` and creates no pending token;
- correction/bonus EOS may be pending and sets `finished=True`;
- `synchronize_pending()` materializes the pending token in both witnesses and clears it;
- `cancel()` returns the exact original state regardless of tentative work;
- invalid acceptance count, suffix mismatch or double commit/cancel fails closed.

## 11. Trace determinism

Reference result/state objects are frozen dataclasses. Canonical serialization sorts map-like structures and stores rational numbers as numerator/denominator pairs. Traces contain no timestamps, hostnames, absolute paths or random IDs.

## 12. Error taxonomy

Stable exception classes:

- `DistributionValidationError`;
- `RandomSourceError`;
- `ProposalValidationError`;
- `UnreachableResidualError`;
- `ModelTableError`;
- `LawNormalizationError`;
- `StateInvariantError`;
- `TransactionStateError`.

Expected validation failures produce concise diagnostics rather than partial outputs or silent fallback.

## 13. Testing and promotion gates

Required tests:

- exact distribution construction/sampling;
- one-token law proof by enumeration;
- sampled round branch behavior;
- exhaustive bounded autoregressive law equality;
- draft perturbation invariance;
- greedy identity;
- EOS/budget/zero-probability cases;
- transaction commit, rejection, bonus, synchronization and cancellation;
- adversarial invalid inputs and states;
- deterministic canonical serialization.

Promotion requires focused tests, complete repository CI, CodeQL, fresh specification review, fresh code-quality review and post-merge verification.

## 14. Evidence boundary

Passing CA-03 proves only the finite exact reference semantics implemented by the oracle. It does not prove floating-point, model, tokenizer, KV-tensor, hardware, performance, distributed or production behavior.
