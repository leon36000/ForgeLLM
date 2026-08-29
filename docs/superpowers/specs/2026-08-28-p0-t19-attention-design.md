# P0-T19 design: single-query scaled dot-product attention + transpose

## Context

P0-T18 (merged as `03c4bee`, PR #85) deferred "attention, transpose, or any new tensor
operation" to a future P0-T19 (see its non-goals and
`docs/quality/P0-T18-REFERENCE-ORACLE.md`'s "Non-claims" section). This is that increment.

**Collision check performed before starting** (2026-08-28, live): no open PR, issue, task
packet, or code on `main` (`d50cd7e` at time of writing) mentions `P0-T19`, attention,
transpose, RoPE, or KV-cache. `docs/roadmap/PHASE0_TASKS.md` does not list a P0-T19 row.
`docs/reviews/P0-T16-DENSE-DECODER-REVIEW.md` explicitly disclaims attention as out of scope
for the dense decoder ("This is not ... attention, KV-cache ..."). `docs/agents/AGENT_ROLES.md`
defines functional roles (Implementer, Correctness reviewer, ...), not a fixed per-tool lane,
so implementing this task packet is within scope for this session. This is a point-in-time
check, not a lease: re-verified again immediately before opening a PR and again immediately
before merge, matching this session's established practice.

## Scope decision: single query, not full self-attention

The smallest complete next vertical slice is **one query vector attending over a fixed
key/value context**, producing one context vector — the exact shape needed for a real
autoregressive decode step (attend the current token's query to all prior tokens' cached
keys/values), and a direct sibling of `dense_decode_single_token`'s "one token" bound.

This is deliberately **not** full self-attention over a batch of queries with a causal mask,
for one concrete, load-bearing reason: `crates/forgellm-reference::softmax` operates on a
single flat `&[f32]` vector — one probability distribution. A multi-query attention
(`[num_queries, head_dim]`) needs **per-row** softmax (each query's score row normalized
independently), which today's `softmax` does not do and which this task does not modify
(modifying an existing, already-reviewed primitive is out of scope) or duplicate (writing a
second, parallel per-row-softmax would be new numerically-sensitive surface with no numerical
benefit over just waiting for a real multi-query task to justify it). Constraining `query` to
exactly one row (`shape == [1, head_dim]`) means the existing `softmax` is called on the full,
single-row score tensor's data — correct by construction, zero new softmax logic, and the
already-derived `softmax_oracle` tolerance applies unchanged. Multi-query/full self-attention
with a causal mask is deliberately deferred to a future P0-T20.

No causal masking logic is implemented or needed: the caller supplies exactly the key/value
context the query may attend to (this mirrors how a real incremental-decode attention step
already only has access to past and current positions by construction of what's in the KV
cache — masking future positions is enforced by what the caller passes in, not by logic inside
this primitive). KV-cache *management* (append, eviction, capacity) remains explicitly out of
scope — this task takes `keys`/`values` as given, already-assembled rank-two tensors.

## New Rust surface (`crates/forgellm-reference/src/lib.rs`)

1. **`transpose(tensor: &Tensor) -> Result<Tensor, ReferenceError>`** — swaps the two axes of
   a rank-two tensor. Pure data movement (no arithmetic, so no rounding to reason about), but
   validates input finiteness for consistency with every other op in this crate (matching
   `embedding_gather`'s precedent of checking finiteness even for a pure-copy operation — a
   deliberate repo-wide fail-closed convention, not an oversight to skip here).

2. **`attention_decode_single_query(query: &Tensor, keys: &Tensor, values: &Tensor) -> Result<Tensor, ReferenceError>`**
   — `query` is `[1, head_dim]`; `keys`/`values` are `[context_len, head_dim]` with equal
   `context_len`. Implementation composes existing, already-reviewed primitives exactly like
   `dense_decode_single_token` does:
   - `raw_scores = matmul(query, transpose(keys)?)?` → `[1, context_len]`.
   - Scale every element of `raw_scores.data()` by `1.0f64 / (head_dim as f64).sqrt()`,
     computed in `f64` and cast to `f32` once per element — one new, tiny, private (non-`pub`)
     loop, matching this crate's dominant "compute in the widest natural precision, cast once"
     pattern (`matmul`, `rms_norm`) rather than chaining several separately-rounded native-`f32`
     operations. (An `f32`-native version — `f32::sqrt` then `f32` division then `f32`
     multiply — was the first draft; switched to this `f64`-then-cast-once form before writing
     the oracle, since it is both more precise *and* simpler to derive a tolerance for: it
     reduces to exactly the same "one final cast" shape already used everywhere else in this
     file, rather than needing a new three-term chained-relative-error argument.)
   - `probabilities = softmax(&scaled)?` — the existing, unmodified primitive.
   - `context = matmul(&Tensor::new([1, context_len], probabilities)?, values)?` → `[1, head_dim]`.

   A new `ReferenceError::UnsupportedQueryCount { operation, actual }` variant covers the
   `query.shape[0] != 1` case precisely (checked: no exhaustive `match` on `ReferenceError`
   exists anywhere in the repo — `grep` confirms every use site is an `assert_eq!`/construction,
   so this additive variant cannot break an existing exhaustive match).

   **Why fold the scale in as a separate step instead of fusing it into `matmul`'s own
   accumulator before its single cast** (the alternative considered): it keeps 100% reuse of
   the existing, already-hardened `matmul`/`softmax`/`transpose` primitives and adds only a few
   lines of genuinely new numerical logic (the scale loop) — directly following
   `dense_decode_single_token`'s own stated design principle ("intentionally a composition of
   the existing checked primitives"). The cost is one extra derived (not guessed) half-ULP term
   in the oracle tolerance for the one new `f64`→`f32` cast; see below. Given this session's own
   experience finding a real bug in new numerically-sensitive code
   (`docs/quality/P0-T18-REFERENCE-ORACLE.md`'s BLOCKER), minimizing new arithmetic surface is
   the higher-priority trade-off.

## Python oracle extension (`src/forgellm_governance/reference_oracle.py`)

1. **`transpose_exact(matrix: list[list[Fraction]]) -> list[list[Fraction]]`** — exact
   (zero-tolerance), since it is pure rearrangement of already-exact `Fraction` values, exactly
   like `embedding_gather_exact`.

2. **`attention_oracle(query, keys, values) -> tuple[list[Fraction], Fraction]`** — mirrors the
   Rust composition exactly, in the same order, so the derived tolerance matches what Rust's
   actual operation sequence can introduce:
   - `raw_scores = matmul_exact([query], transpose_exact(keys))[0]` — exact (`Fraction`), zero
     rounding, since matmul over already-exact f32-derived `Fraction`s of these small fixture
     magnitudes stays within `assert_f64_exact_accumulation`'s checked 53-bit range (checked
     mechanically, not assumed, exactly as the existing exact ops already do).
   - Scale factor: `1 / sqrt(head_dim)` computed via `decimal_transcendental_with_escape("sqrt", Fraction(head_dim))`
     then inverted with exact `Fraction` division (`head_dim` is a small exact integer, so this
     reuses the already-independently-reviewed-and-fixed Ziv-escape sqrt path unchanged — no
     new escalation logic to get wrong a second time — and the reciprocal itself is exact, not
     an approximation, since `Fraction` division never rounds).
   - `scaled = [score * scale for score in raw_scores]` — exact `Fraction` multiply against a
     provably-correctly-rounded-to-high-precision scale value.
   - `probabilities, softmax_epsilon = softmax_oracle(scaled)` — reuses the existing, unchanged
     softmax oracle and its already-derived tolerance term.
   - `context = matmul_exact([probabilities], values)[0]` — exact.
   - **Derived combined tolerance, applied to the actual returned value.** `attention_decode_single_query`
     returns only the context vector — a Rust-side fixture test cannot observe or compare the
     intermediate scores/probabilities, so the tolerance must describe the context vector
     itself, not an intermediate quantity (an earlier draft of this derivation made exactly
     that mistake — see the module docstring's own note). Chain: (a) `raw_scores` matches
     zero-tolerance under the same mechanically-checked exact-accumulation precondition every
     other exact op already relies on; (b) the scale step's own f64-rounding gap versus this
     oracle's near-exact reciprocal is ~2 `F64_EPSILON`-relative terms, many orders of magnitude
     below any f32-scale term here, so it is dropped as provably negligible (the same
     dominated-term argument `rms_norm_oracle` already makes for its own reciprocal-vs-divide
     gap) rather than silently ignored; (c) `softmax_oracle`'s already-derived `epsilon` is
     therefore, to excellent approximation, the real per-element error on the probabilities;
     (d) that per-probability error is propagated worst-case-linearly (triangle inequality, no
     assumed cancellation) through the final `matmul(probabilities, values)`:
     `context[k]`'s tolerance is `epsilon * sum_j abs(values[j][k]) + half_ulp_at(context[k])`,
     where the last term is that matmul's own final cast — *not* covered by the
     exact-accumulation zero-tolerance treatment here, since `probabilities` are no longer exact
     inputs by that point. This keeps the derivation honest and additive rather than inventing a
     single fudged constant, and it is the tolerance the fixture-driven Rust contract test can
     actually apply to what `attention_decode_single_query` returns.
   - **Fail-closed precondition, mechanically checked, not assumed**: the generator calls
     `assert_f64_exact_accumulation` on every raw-score and context-vector partial sum, exactly
     like every existing exact-Fraction fixture case, and keeps fixture magnitudes small enough
     that this passes by construction rather than by luck.

## Adversarial self-audit plan (mandatory before requesting review, per this session's own
established practice — see the P0-T18 BLOCKER lesson)

The P0-T18 BLOCKER was a rounding-tie *safety-margin* bug that only adversarial,
near-tie-constructed inputs could expose — realistic fixture values never came close to
triggering it. Applying that lesson directly here:

1. Construct `head_dim`/query/key/value values that place at least one scaled score's `f32`
   cast within a handful of ULPs of a real f32 rounding tie, and confirm the derived
   `attention_tolerance` still holds against 300+ digit ground truth at that boundary — not
   just for "nice" fixture numbers.
2. Randomized stress test (thousands of trials) comparing `attention_oracle` against a
   from-scratch Python re-implementation of the exact Rust `f64`-accumulate-then-cast pipeline
   (not the oracle's own code) across a spread of `context_len` (1, 2, 8, 64) and magnitudes
   (1e-3 to 1e3), to catch an operation-order mismatch the way the `rms_norm` reciprocal-vs-
   divide gap was caught previously.
3. Re-run this session's exact `_margin_to_nearest_rounding_boundary`/Ziv-escape adversarial
   battery (4000 near-tie constructions) unchanged, as a regression guard — this task reuses
   that code path unmodified via `decimal_transcendental_with_escape`, so it must still show
   `0/4000` confidently wrong, not because this task re-proves it but because reuse of a fixed
   function must not silently regress.

## Non-goals (explicit)

- Multi-query / full self-attention with a causal mask over `[num_queries, context_len]`
  scores (needs per-row softmax; deferred to a future P0-T20).
- Multi-head reshape/split, RoPE, or any positional-encoding scheme.
- KV-cache append/eviction/capacity management — `keys`/`values` are caller-supplied, already
  final tensors.
- Any change to `matmul`, `softmax`, `transpose` (new, but frozen once merged), or any existing
  public function's signature or numerical behavior.
- Any PyTorch/NumPy dependency, or a real-model/attention-conformance claim.
- Wiring this into `dense_decode_single_token` or any new composed "attention decoder" — this
  task ships the primitive and its oracle only, exactly as P0-T11/T12 shipped primitives ahead
  of P0-T16's composition.

## Addendum: the self-audit plan above caught a real bug

Step 2 of the adversarial self-audit plan (randomized cross-check against a from-scratch
simulated-Rust pipeline) found a real bug in the first `attention_oracle` draft before any
review was requested: it fed `softmax_oracle` the *unrounded* exact `raw_scores`/`scaled`
values instead of first rounding each to the actual `f32` value real Rust's `matmul`/scale steps
produce, which silently made `softmax_oracle`'s own derived epsilon stop bounding anything about
the real gap to Rust. Full reproduction, fix, and re-verified numbers are in
`docs/quality/P0-T19-ATTENTION.md`'s "A second real bug found by this session's own adversarial
self-audit" section — recorded there rather than duplicated here since it is evidence about what
actually happened during implementation, not a forward-looking design decision.

## Addendum 2: the self-audit plan's stated scale (context_len 64, magnitude up to 1e3) was
revised after hitting a real, measured performance cliff, not silently dropped

The original plan (and the task packet's first-drafted acceptance criterion) called for >= 2,000
trials spanning `context_len` up to 64 and magnitude up to `1e3`/`2**10`. Attempting this
directly revealed a genuine, fully-diagnosed cost cliff: that magnitude combined with
`head_dim=16` produces post-shift softmax logits around `-7e5`, whose `Decimal.exp()` result
underflows to a value exactly representable only as a `Fraction` with a ~1,000,000-bit
denominator — and exact-`Fraction` arithmetic at that scale is genuinely (not pathologically)
slow, confirmed exponential in magnitude by direct measurement. This is not a correctness
concern and not representative of real, well-scaled attention inputs. The acceptance criterion
was revised down to magnitude `2**-6..2**6` with this measurement as the stated justification;
full investigation, numbers, and the resulting permanent test are in
`docs/quality/P0-T19-ATTENTION.md`'s "Adversarial stress test" section.
