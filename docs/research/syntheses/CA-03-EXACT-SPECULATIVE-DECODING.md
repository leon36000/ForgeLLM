# CA-03 — Exact Speculative-Decoding Research Synthesis

- **Date:** 2026-08-14
- **Status:** primary-source synthesis for P0-T08 / CA-03
- **Evidence boundary:** finite exact semantics only
- **Primary sources:** `PAP-SPECDEC`, `PAP-SPECSAMPLING`
- **Existing scoped claim:** `CLM-047`

## Question

What is the smallest placement-independent reference semantics that can prove a speculative decoder preserves the target autoregressive output law, while also defining unambiguous EOS, budget, cancellation and transactional-state behavior for later ForgeLLM runtime implementations?

## Source-derived findings

### Target-law preservation

Both primary papers define speculative decoding/sampling as a modified rejection-sampling procedure that can accelerate decoding without changing the target distribution, subject to implementation numerics. The draft model proposes a short autoregressive continuation; the target model scores the proposal positions in parallel; proposals are then processed from left to right.

ForgeLLM uses the following notation consistently even where a paper uses the opposite letters:

- `p_i`: target distribution at proposal position `i`;
- `q_i`: proposal/draft distribution actually used to sample proposal token `x_i`.

For a proposed token `x_i ~ q_i`, the exact acceptance probability is:

```text
alpha_i(x_i) = min(1, p_i(x_i) / q_i(x_i))
```

A proposal sampled from `q_i` necessarily has `q_i(x_i) > 0`. An implementation must fail closed if the recorded proposal distribution disagrees with the one used to generate the token.

### First rejection and correction distribution

Proposals are accepted only as one consecutive prefix. At the first rejection, all later speculative work is discarded. The emitted correction token is sampled from the normalized positive residual:

```text
r_i(x) = max(0, p_i(x) - q_i(x))
         / sum_y max(0, p_i(y) - q_i(y))
```

The papers prove that the combination of accepted draft mass and residual correction mass recovers `p_i` exactly. If `p_i == q_i`, rejection probability is zero and the residual has zero total mass; therefore attempting to sample that residual indicates an unreachable or inconsistent branch.

### Fully accepted block and target bonus

If every proposal in a block is accepted, the target evaluation already provides the distribution for the next position. One additional target token may therefore be sampled. This bonus is permitted only when the output budget still has capacity and the accepted proposal block did not terminate with EOS.

### Conditional distributions matter

For multi-token blocks, `p_i` and `q_i` are conditional distributions at the exact prefix preceding position `i`. Reusing a stale distribution or validating a proposal against a distribution from a different prefix breaks the proof. The exact reference must preserve the proposal distribution used at each position.

### Proposal quality and performance are separate

The correction rule permits any proposal model that exposes the probabilities used for its proposals. Proposal quality changes acceptance and performance, not the target output law. Hardware cost, draft latency, target verification cost and acceptance rate are separate performance questions and remain outside CA-03.

## ForgeLLM design requirements derived from the sources

The papers establish the sampling law but do not fully specify production KV-cache ownership, cancellation, grammar state or output-budget edge cases. CA-03 adds explicit reference semantics for those concerns; these are ForgeLLM design decisions, not claims copied from the papers.

### Exact arithmetic oracle

The reference uses finite token sets and rational arithmetic (`fractions.Fraction`). It does not use floating-point logits. Exact arithmetic provides a proof oracle for small synthetic models; it does not claim bitwise equivalence with future floating-point kernels.

### Equality of law, not equality of random streams

Baseline decoding and speculative decoding consume random choices differently. Exactness means that every finite output sequence has the same probability under both decoders. A same-seed token-by-token identity test is not a valid exactness oracle unless both algorithms are coupled deliberately for that test.

### EOS and budget

- A remaining output budget of zero performs no model lookup and consumes no random draw.
- A round proposes at most `min(draft_length, remaining_budget)` tokens.
- Proposal generation stops after proposal EOS.
- Accepted EOS terminates the round and sequence; no bonus token follows it.
- A rejection emits at most one residual correction and stops the round.
- A fully accepted non-EOS block emits a target bonus only when budget remains.
- No round emits more tokens than its remaining budget.

### Separate greedy oracle

Greedy decoding is deterministic and does not need stochastic rejection sampling. CA-03 defines a separate oracle:

- choose the smallest token ID among equal maximum probabilities;
- accept a draft token only when it equals the target argmax at that prefix;
- at the first mismatch emit the target argmax and stop the round;
- after a fully matching block, emit the next target argmax when budget and EOS permit.

The bounded greedy result must equal ordinary target greedy decoding exactly.

### Transactional state boundary

The reference models target KV state, draft KV state and auxiliary sampling/grammar state as token-prefix witnesses rather than real tensors.

At round start, target and draft materialized prefixes must agree. During a round, speculative suffix state is tentative. Commit behavior is:

- accepted proposal tokens become materialized for both target and draft witnesses;
- rejected proposal and later suffix state is discarded;
- a correction or bonus token becomes emitted auxiliary state and one pending token to be materialized at the next target/draft evaluation boundary;
- accepted EOS is already materialized and creates no bonus;
- cancellation restores the complete pre-round state atomically;
- starting a new speculative round with an unsynchronized pending token fails closed.

This state model is an ownership oracle for later Rust/C-ABI design, not a production cache implementation.

## Falsifiable CA-03 claims

### C1 — one-token exactness

For every finite normalized `p` and `q`, the modified rejection procedure emits each token `x` with probability exactly `p(x)`.

**Test:** exhaustively enumerate proposal, acceptance and correction branches with rational mass.

### C2 — autoregressive block exactness

For every complete finite table-defined target/draft model, every bounded speculative output law equals ordinary target decoding for the same budget and EOS token.

**Test:** compare exact maps `sequence -> Fraction` for budgets 1–4 and draft lengths 1–3 across adversarial models.

### C3 — draft perturbation independence

Changing `q` while preserving valid support/probabilities changes branch structure and acceptance but not the final target law.

**Test:** compare multiple sharply different draft tables to one target table.

### C4 — greedy identity

The separate greedy speculative oracle emits exactly the same bounded sequence as ordinary target greedy decoding.

**Test:** exhaustive prefixes with ties, mismatches, EOS and budgets.

### C5 — transactional rollback

Cancellation and rejection never commit speculative suffix state; successful commit preserves the declared materialized/pending invariants.

**Test:** state-machine transition tests and adversarial invalid-state construction.

## Required adversarial models

- `p == q`;
- disjoint or nearly disjoint support;
- partial overlap;
- target probability zero for a proposed token;
- proposal zero entries;
- prefix-dependent distributions;
- EOS proposed at each possible position;
- bonus-token EOS;
- deterministic target or draft distributions;
- equal-probability argmax ties;
- missing table prefix;
- zero budget;
- cancellation before and after tentative verification.

## Evidence limits

CA-03 will not establish:

- performance, speedup or acceptance on a real model;
- floating-point numerical equivalence;
- tokenizer or model-family support;
- tree speculation, Medusa/EAGLE semantics or multiple proposal branches;
- hardware placement, cache residency or CPU/GPU overlap;
- production KV allocation or synchronization;
- approximate verification or response-quality changes.

## Decision

Proceed with a finite exact Python oracle, exhaustive probability-law enumeration, a separate greedy oracle and transactional prefix-state witnesses. These artifacts become the correctness reference for later ForgeCacheDraft, Transition Atlas and runtime tasks; no performance path may replace or weaken this oracle.
