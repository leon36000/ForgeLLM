# ForgeLLM Exact Speculative-Decoding Reference

## Purpose

This package is the placement-independent correctness oracle for future ForgeLLM speculative-decoding implementations. It uses finite token sets and exact rational probabilities so that target and speculative output laws can be compared without floating-point tolerance or Monte Carlo error.

The evidence boundary is **finite exact reference semantics**. Passing these tests does not prove real-model numerics, tokenizer behavior, KV-tensor correctness, hardware performance, batching, distributed execution or production readiness.

## Notation

ForgeLLM uses:

- `p`: target distribution;
- `q`: proposal or draft distribution actually used to sample a proposal;
- `x`: proposed token;
- `eos_token_id`: explicit end-of-sequence token;
- `budget`: maximum number of newly emitted tokens.

For a proposal `x ~ q`, the acceptance probability is:

```text
min(1, p(x) / q(x))
```

At the first rejection, the correction distribution is:

```text
max(0, p - q) / sum(max(0, p - q))
```

No proposal after the first rejected position can be accepted or committed.

## Exact distributions and random tapes

`ExactDistribution` stores normalized `fractions.Fraction` values in canonical token-ID order. It rejects duplicate or invalid token IDs, negative weights, floating-point weights and zero total mass.

`RandomTape` is immutable. Each non-deterministic choice consumes one predeclared integer draw and returns an advanced tape. Deterministic categorical and Bernoulli choices consume no draw. Out-of-range draws fail; modulo reduction is forbidden.

```python
from fractions import Fraction

from forgellm_governance import ExactDistribution, RandomTape

p = ExactDistribution.from_pairs(
    [(0, Fraction(1, 4)), (1, Fraction(3, 4))]
)
token, advanced = p.sample(RandomTape((2,)))
```

## Sampled round

A sampled round:

1. generates at most `min(draft_length, remaining_budget)` proposal tokens;
2. records the exact `q_i` and prefix used at every proposal position;
3. verifies proposals from left to right against target `p_i`;
4. stops at the first rejection and emits one residual correction;
5. emits one target bonus token only after a fully accepted non-EOS block with budget remaining.

```python
from forgellm_governance import (
    FiniteTableModel,
    RandomTape,
    SampledRoundRequest,
    sample_speculative_round,
)

request = SampledRoundRequest(
    prefix=(),
    draft_length=2,
    remaining_budget=3,
    eos_token_id=9,
)
result = sample_speculative_round(target, draft, request, RandomTape((0, 0)))
```

Termination precedence is:

1. `eos` when the final emitted token is EOS;
2. `rejection` for a non-EOS residual correction;
3. `budget` for zero budget or a fully accepted block that consumes the budget without a bonus;
4. `all_accepted` for a non-EOS target bonus.

`correction_kind` is independent from termination and records `none`, `residual` or `bonus`.

## Equality of law

`enumerate_target_law` recursively enumerates ordinary autoregressive target decoding. `enumerate_speculative_law` analytically enumerates every proposal path, acceptance/rejection branch, correction, bonus and subsequent round.

```python
from forgellm_governance import (
    enumerate_speculative_law,
    enumerate_target_law,
)

baseline = enumerate_target_law(target, (), budget=4, eos_token_id=9)
speculative = enumerate_speculative_law(
    target,
    draft,
    (),
    budget=4,
    draft_length=3,
    eos_token_id=9,
)
assert speculative == baseline
```

Exactness means equality of the complete output law. It does **not** mean that ordinary and speculative algorithms consume random draws identically or emit identical sequences under an uncoupled same-seed test.

## Greedy oracle

Greedy decoding is separate from stochastic rejection sampling. `greedy_target_decode` and `greedy_speculative_decode` use the smallest token ID to break exact probability ties.

```python
from forgellm_governance import (
    greedy_speculative_decode,
    greedy_target_decode,
)

baseline = greedy_target_decode(target, (), budget=4, eos_token_id=9)
speculative = greedy_speculative_decode(
    target,
    draft,
    (),
    budget=4,
    draft_length=3,
    eos_token_id=9,
)
assert speculative == baseline
```

At the first draft/target argmax mismatch, the target token is emitted and the proposal suffix is discarded. A fully matching non-EOS block may receive one target argmax bonus.

## Transactional state

`DecoderState` models ownership boundaries with token-prefix witnesses rather than real KV tensors:

- target and draft materialized prefixes are equal;
- sampler and grammar prefixes equal visible output;
- a residual correction or bonus may be the single pending token;
- accepted proposal tokens are materialized immediately;
- rejected proposal suffixes are never committed;
- cancellation returns the exact original state;
- `synchronize_pending` materializes a pending correction or bonus in both witnesses.

```python
from forgellm_governance import DecoderState, RoundTransaction

state = DecoderState(
    output_tokens=(),
    target_materialized=(),
    draft_materialized=(),
    pending_token=None,
    sampler_tokens=(),
    grammar_tokens=(),
    finished=False,
)
transaction = RoundTransaction.begin(state, result.proposed_tokens)
committed, closed = transaction.commit(result, eos_token_id=9)
```

A finished state or a state with a pending token cannot begin a new round. Closed transactions cannot be committed or cancelled again.

## Stable errors

The public exact-reference error taxonomy includes:

- `DistributionValidationError`;
- `RandomSourceError`;
- `ProposalValidationError`;
- `UnreachableResidualError`;
- `ModelTableError`;
- `LawNormalizationError`;
- `StateInvariantError`;
- `TransactionStateError`.

Expected invalid input fails closed rather than silently renormalizing, reusing stale proposal probabilities, inventing a route or committing partial state.

## Deterministic traces

`canonical_trace_bytes` serializes round requests, results, rational probabilities, random-tape position and optional decoder state. Rational values use numerator/denominator objects. Traces contain no timestamp, hostname, absolute path or random identifier.

## Verification

Run the focused correctness gate:

```bash
make verify-speculative
```

Run every ForgeLLM Phase 0 gate:

```bash
make ci
```

The focused suite covers exact one-token branch mass, bounded target/speculative law equality, sharply perturbed draft distributions, greedy identity, EOS/budget cases, transaction commit/rollback and adversarial invalid inputs.

## Explicit non-claims

This reference does not establish:

- floating-point or quantized equivalence;
- correctness of a neural target or draft model;
- tokenizer or model-family support;
- real KV-cache ownership or memory safety;
- CPU/GPU placement, cache residency or overlap;
- latency, throughput, energy or acceptance-rate improvement;
- multi-branch/tree speculation;
- approximate verification or response-quality changes.
