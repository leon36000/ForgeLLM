# P0-T18 Differential Reference Oracle Design

**Status:** draft, prepared by Claude Code's independent adversarial/research supervisor lane; not yet reviewed or accepted. This is a proposal, not an authorization.

## Goal

Replace the hand-transcribed numerical constants in `crates/forgellm-reference`'s existing tests with a committed, hash-pinned, CI-regenerated fixture, computed by a stdlib-only Python oracle whose every value is independently re-derivable from source — closing the gap between `ARCHITECTURE_PRINCIPLES.md`'s claim that the CPU reference path "is the oracle for GPU and quantized paths" and the fact that the oracle's own tests currently rest on unverifiable, hand-copied literals (for example `numerical_contract.rs`'s `0.090_030_57`).

## Context and constraints

- `crates/forgellm-reference/src/lib.rs` (586 lines, zero dependencies, `#![forbid(unsafe_code)]`) implements `matmul`, `elementwise_add`, `elementwise_mul`, `embedding_gather`, `reshape`, `argmax`, `softmax`, and `rms_norm`, each accumulating in `f64` and casting to `f32` exactly once, at the end.
- `tasks/closed/P0-T12-decoder-tensor-primitives.yaml`'s `forbidden_actions` bars "transcendental operations" and "broaden[ing] the P0-T11 softmax numerical contract." This task does not touch `SOFTMAX_ABS_TOLERANCE`, does not edit `numerical_contract.rs`, and adds no new transcendental *production* operation — it adds a separate, additive test-oracle comparison with its own, independently-derived tolerance. This reading is stated explicitly here rather than assumed silently, so a reviewer can disagree with it before any code lands.
- `pyproject.toml` declares stdlib plus `jsonschema==4.26.0` plus `PyYAML==6.0.3` only. No numerical dependency (NumPy, PyTorch, mpmath, sympy) is available without triggering `AGENTS.md §3`'s anti-drift stop-and-decide gate. This design uses only `fractions.Fraction` and `decimal.Decimal` from the standard library.
- The house idiom for exact rational arithmetic already exists in this repository: `src/forgellm_governance/exact_distribution.py` uses `fractions.Fraction` throughout for the speculative-decoding oracle (P0-T08/CA-03).
- **The implementation must not** claim PyTorch/real-model numerical conformance (that is Phase 2's named, separately-gated deliverable), touch any path frozen by open PR #72 or PR #75, add a Rust or Python dependency, or add any file under `artifacts/governance/loop-engineering/` (see the Loop Engineering section below).

## The numerical methodology

### Why the existing ops split into two error regimes, not one

IEEE 754-2019 §5 *requires* correctly-rounded results for the basic operations (`+ − × ÷ sqrt`). It only *recommends* (§9.2, not required) correct rounding for `exp`. The crate's own existing tolerance, `SOFTMAX_ABS_TOLERANCE = 1.0e-6`, already implicitly acknowledges this asymmetry (its doc comment singles out `f64::exp` as having "unspecified precision") but never derives a number from it. This design treats the two regimes differently and says so:

- **Exact-`Fraction` ops** (`matmul`, `elementwise_add`, `elementwise_mul`, `embedding_gather`): budget is **zero** — bit-exact — *provided* every intermediate `f64` accumulation step in the fixture stays within 53 bits. The generator checks this mechanically for every fixture case (asserting each partial sum's numerator bit-length), rather than assuming it. Fixture magnitudes are kept small (values in roughly `[-8, 8]`, dimensions ≤ 8) specifically so this precondition is easy to satisfy and easy to verify by inspection.
- **`sqrt`-based ops** (`rms_norm`): IEEE 754 mandates correct rounding for `sqrt` and division, so the error budget is *provably* tight — approximately 0.5 ULP(f32) of the result — not a guess.
- **`exp`-based ops** (`softmax`): the budget is *derived*, not guessed, from a stated assumption about libm quality (this design proposes κ = 4 ULP as a conservative pad over glibc's typically sub-2-ULP behavior, cited as an assumption, not a proof) propagated through the shift/exp/sum/divide/cast pipeline using a standard forward-error bound. The module docstring must state this derivation and its assumption explicitly, so a future reader can revisit κ if the CI runner's libm turns out to behave differently — this project has no cross-platform libm measurement capability yet, per `ARCHITECTURE_PRINCIPLES.md`.

An empirical check (200,000 random samples, `math.exp` at f64 vs. `decimal.Decimal.exp()` at precision 50, compared at f32 bit-precision) found zero divergences in the softmax-relevant range — meaning the practical gap this design closes is about *provable re-derivability*, not about a numerical bug the existing tests are currently missing. This is stated plainly rather than oversold.

### Avoiding double-rounding

Converting a high-precision value to f32 via `Decimal → Python float (f64) → struct.pack('<f', ...)` performs *two* roundings and can disagree with a single correct rounding near a halfway point. This design instead converts the exact high-precision result to a `Fraction` (via `Decimal.as_integer_ratio()`, exact by definition for any finite `Decimal`) and rounds that `Fraction` directly to the nearest f32 bit pattern in one step, round-half-to-even, using only integer and exact-`Fraction` comparisons — no intermediate `float` rounding of a *computed* value anywhere in the path. (Literal, already-f32-exact test inputs may still use `struct.pack`, since encoding an exact value introduces no rounding.)

### Terminating the regress honestly

No oracle can achieve zero trust. This design moves the trust anchor from one unverifiable human transcription (today's hand-copied literals) to a small number of standards-documented, independently-testable primitives (`fractions`/`decimal`, exact by specification for the operations used) plus one short, exhaustively round-trip-testable rounding routine with no irrational component. That is a strictly stronger foundation than what exists today, and this document says so without implying the gap is fully closed — the residual uncertainty (whether `decimal.exp()`/`decimal.sqrt()` are unconditionally correctly rounded per the General Decimal Arithmetic Specification, versus correctly rounded except in rare documented cases) is absorbed by a wide, stated precision margin (base precision 40 digits against a ~7.3-digit requirement), with a fail-closed escalation (double precision and retry, raise rather than guess) if a result ever falls within its own error bound of an f32 rounding boundary.

## Fixture transport

- `scripts/generate_reference_oracle_fixture.py --check` regenerates the fixture in memory and diffs it byte-for-byte against the committed file — it never mutates the working tree.
- The fixture is JSON with a deliberately flat, fixed schema (fixed field names, hex-encoded f32 bit patterns as ASCII strings, no floating-point literals at all), read on the Rust side by a small, dependency-free, schema-restricted parser under `crates/forgellm-reference/tests/support/` — not `serde_json`, which would be a new dependency for no real benefit given the schema is fully controlled.
- Determinism: `json.dump(..., indent=2, sort_keys=True, ensure_ascii=True)`; cases sorted by `(op, case_id)` independent of source definition order; every float encoded as an 8-hex-digit lowercase `u32` bit-pattern string; no NaN/Infinity ever emitted.
- Hash pin follows the existing repository convention exactly (`sha256sum -c`, mirroring `artifacts/simulations/P0-T07-evidence.sha256`'s usage in the `Makefile`).
- A reviewer re-verifies from a clean clone, offline, with no new dependency: `python3 scripts/generate_reference_oracle_fixture.py --check --root .`, `sha256sum -c crates/forgellm-reference/tests/fixtures/reference_ops_oracle.sha256`, `cargo test -p forgellm-reference`.

## Loop Engineering discipline (not committed tooling)

`scripts/validate_loop_engineering.py` is hard-pinned to `task_id == "P0-T10"` (it rejects any other task ID, and its own docstring calls it "the fixed P0-T10 loop receipt catalog"), and ADR-0005, which the Loop Engineering bridge implements, remains `proposed`, not accepted (`docs/state/HANDOFF.md`). Committing a declaration or receipt under `artifacts/governance/loop-engineering/` for this task would either fail the one required CI check outright, or — if that check were bypassed — assert a "validated" status the tooling cannot actually confirm. That would be exactly the kind of unearned claim this project's own rules forbid.

This task therefore uses the GOAL/SCOPE/VERIFY/BUDGET/STOP/RECEIPT discipline as a working method for how the implementer paces and bounds the work, documented here for transparency, without committing any file the automated catalog would scan:

```yaml
GOAL: Add a stdlib-only, re-derivable differential oracle for forgellm-reference's existing ops, without adding a dependency or touching the existing softmax numerical contract.
SCOPE:
  - crates/forgellm-reference/tests/
  - src/forgellm_governance/reference_oracle.py
  - scripts/generate_reference_oracle_fixture.py
  - tests/test_reference_oracle.py
VERIFY:
  - cargo test --workspace --all-targets --locked
  - cargo fmt --all --check
  - cargo clippy --workspace --all-targets --locked -- -D warnings
  - PYTHONPATH=src python3 -m pytest -q tests/test_reference_oracle.py
  - python3 scripts/generate_reference_oracle_fixture.py --check --root .
BUDGET:
  max_iterations: 12
  max_identical_failures: 3
  max_wall_minutes: 90
STOP:
  on_verify_pass: true
  on_budget_exhausted: true
  on_identical_failure_limit: true
  privileged_operation: stop_and_escalate
```

Generalizing `scripts/validate_loop_engineering.py` to be task-keyed, so a real declaration/receipt pair could be committed and mechanically validated, is named here as a valuable, separate, small follow-up task — not performed as part of P0-T18, since it touches the same required-check-adjacent gate every other task's `make ci` depends on and deserves its own scoped decision.

## Explicitly deferred

Attention, transpose, RoPE, KV cache, and any other new tensor operation are deliberately **not** part of this design. `P0-T12`'s own `non_goals` named attention as future, not forbidden, work — but adding it now, before this oracle methodology exists, would validate brand-new, previously-unverified numerics against the same kind of hand-copied constant this task exists to stop using. A future `P0-T19` should build attention *on top of* the oracle infrastructure this task delivers.
