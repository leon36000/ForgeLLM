# P0-T18 — Stdlib-Only Differential Reference Oracle Evidence

- Task: P0-T18 — replace hand-copied golden constants in `crates/forgellm-reference`'s existing
  tests with a committed, hash-pinned, CI-regenerated fixture, computed by a stdlib-only Python
  oracle (renamed from P0-T17, which PR #82 and #79 claimed for other tasks during this task's
  own development — see below).
- Canonical base: `55d08c76b7fcdc3b6c256d35a4d74b275652964c` (protected `main`, includes the
  merged P0-T17 CI-gate fix this task depends on).
- Evidence boundary: `crates/forgellm-reference` gains an additive test-only differential oracle.
  `src/lib.rs` is unchanged. No dependency added. No PyTorch/real-model conformance claim.

## What was built

- `src/forgellm_governance/reference_oracle.py`: exact `fractions.Fraction` arithmetic for
  `matmul`/`elementwise_add`/`elementwise_mul`/`embedding_gather`; `decimal.Decimal`-based
  `softmax`/`rms_norm` with a Ziv-style precision-escalation escape (`decimal_transcendental_with_escape`)
  that raises (`ReferenceOracleAmbiguousRounding`) rather than silently guessing if correct
  rounding cannot be proven; a from-scratch, exhaustively-tested `fraction_to_f32_bits`
  round-half-to-even rounding routine that never passes a *computed* value through an
  intermediate Python `float` (avoiding double rounding both on the way in, via
  `fraction_to_decimal`'s exact-integer-division conversion, and on the way out).
- `scripts/generate_reference_oracle_fixture.py`: deterministic generator with a non-mutating
  `--check` mode (regenerates in memory, diffs byte-for-byte, never writes).
- `crates/forgellm-reference/tests/fixtures/reference_ops_oracle.json` (8 cases across all 6
  covered ops) and its `.sha256` pin.
- `crates/forgellm-reference/tests/support/mod.rs`: a ~280-line dependency-free JSON reader
  restricted to the fixture's exact flat grammar (no `serde_json` dependency), with 14 of its
  own malformed-input tests (duplicate keys, escapes, floats, trailing commas, unterminated
  strings, non-hex, wrong-length hex, etc.) plus 2 recursion-depth-limit tests added after an
  adversarial-input audit (see below).
- `crates/forgellm-reference/tests/reference_ops_oracle_contract.rs`: fixture-driven differential
  tests, plus a dependency-free from-scratch SHA-256 implementation used only to verify the
  fixture's own committed hash pin at test time (not exposed as a library API), itself checked
  against 4 real `hashlib`-derived test vectors including the one-block/two-block padding
  boundary (55 vs. 64 input bytes).
- `tests/test_reference_oracle.py`: 41 pytest cases for the oracle itself.

## Verification (this exact head)

- Toolchain: `rustc 1.97.1 (8bab26f4f 2026-07-14)`.
- `PYTHONPATH=src python3 -m pytest -q tests/test_reference_oracle.py`: **41/41 passed**.
- `python3 scripts/generate_reference_oracle_fixture.py --check --root .`: OK, byte-identical.
- `sha256sum -c crates/forgellm-reference/tests/fixtures/reference_ops_oracle.sha256`: passed.
- `cargo test --workspace --all-targets --locked`: **72/72 passed** (2 `allocation_tests`, 17
  `decoder_primitives`, 7 `dense_decoder`, 3 `numerical_contract`, 24 `reference_ops`, 19 new
  `reference_ops_oracle_contract` — the last including the fixture-driven differential tests for
  all 6 ops, the SHA-256 pin check and its 4 published-vector checks, the 14 parser
  malformed-input tests, and the 2 recursion-depth tests).
- `cargo fmt --all --check`: clean. `cargo clippy --workspace --all-targets --locked -- -D warnings`: 0 warnings.
- Full `make ci`: **exit 0** — 544 pytest (up from 503 at this task's base, +41 from
  `test_reference_oracle.py`), 230 focused speculative tests, cache-placement simulation hashes,
  the new fixture `--check` + `sha256sum -c` steps, and all 69 Rust tests.
- `crates/forgellm-reference/src/lib.rs` and every pre-existing test file: byte-identical to
  base (no production or existing-test change).
- No dependency added to `Cargo.toml`, `Cargo.lock`, or `pyproject.toml` (checked by direct diff).
- No file added under `artifacts/governance/loop-engineering/`.

## Bugs found and fixed during this task's own development (recorded per project rule: negative results are evidence)

Writing and actually running the test suite — rather than trusting the design on paper — caught
three real defects before any Rust code was written against the oracle:

1. **`rms_norm_oracle` originally returned one fixed global tolerance** (`4 * F64_EPSILON +
   F32_CAST_HALF_ULP`, i.e. correct only near output magnitude 1). A randomized test comparing
   against a real f64 reference pipeline failed: `delta=6.2e-8 > budget=5.96e-8` for
   larger-magnitude outputs. Root cause: `rms_norm`'s output is not bounded to `[0, 1]` the way
   `softmax`'s is, so a magnitude-1-only tolerance is wrong wherever the real output is larger.
   Fixed by adding `half_ulp_at(value)` and returning a **per-element** tolerance
   (`(n/2 + 4) * F64_EPSILON * |result| + half_ulp_at(result)`), matching the per-case-tolerance
   design principle already used for the fixture format. Regression test:
   `test_rms_norm_oracle_tolerance_scales_with_output_magnitude`.
2. **The exponent-boundary exhaustive round-trip test failed once**, on negative zero
   (`0x80000000`): `Fraction` has no signed zero, so `f32_bits_to_fraction` collapses `-0.0` to
   `Fraction(0)`, and round-tripping that back gives positive zero's bit pattern, not `-0.0`'s.
   This is a real, documented limitation of representing f32 values as `Fraction` (not a bug in
   the rounding arithmetic itself) — excluded explicitly in the exhaustive test with a named
   constant and a comment, rather than silently passed over.
3. **The hand-rolled JSON reader (`tests/support/mod.rs`) stack-overflowed and aborted the whole
   test process (SIGABRT) on a deeply-nested adversarial input** (confirmed at 5,000 levels of
   `[` nesting; the real fixture never nests more than 5 levels). This is a genuine robustness
   gap in unbounded recursive descent, found by actually constructing and running the adversarial
   input, not by reasoning about the parser on paper. Fixed by adding `MAX_NESTING_DEPTH = 64`
   (generous relative to the fixture's real depth of 5) checked once, centrally, in
   `parse_value`, converting unbounded recursion into a clean `ParseError`. Verified the fix
   holds even at 1,000,000 levels of adversarial nesting (`nesting_beyond_the_limit_is_a_clean_error_not_a_crash`).
   The fixture is generator-controlled, not untrusted external input, so this is robustness
   hardening rather than a claimed security fix for an actual attack surface.
4. **The initial `decimal_transcendental_with_escape`/`softmax_oracle`/`rms_norm_oracle` design
   converted its Fraction input to a Python `float` before building the `Decimal`**
   (`Decimal(str(float(value))).exp()`), which is exactly the double-rounding failure mode this
   module's own docstring says it avoids. Caught during implementation, before any test ran
   against it: fixed by adding `fraction_to_decimal(value, prec)` (exact-integer `Decimal`
   division, redone at each escalating precision level) so no float ever appears anywhere in the
   transcendental path. Regression test: `test_fraction_to_decimal_never_touches_float`, using a
   Fraction whose naive `float()` conversion would already be lossy.

## Mid-review task-ID churn (this task was P0-T17, then P0-T18)

Two task packets were originally drafted together: a small CI-gate fix (originally P0-T16) and
this oracle task (originally P0-T17). Before either merged, PR #82 ("dense decoder composition")
claimed the real P0-T16 for an unrelated feature, so the CI-gate fix was renamed P0-T17 and
merged as such (PR #79). That left P0-T17 taken, so this task was finalized as **P0-T18** and
declares `dependencies: [P0-T17]` (satisfied: P0-T17 is merged). All internal cross-references
(spec/plan filenames, the task packet's own `non_goals` mention of the *next* deferred task) were
swept and corrected accordingly — including one self-referential bug this exact renaming
introduced (the spec's "Explicitly deferred" section originally deferred attention to "a future
P0-T18," which after the rename would have pointed at itself; corrected to P0-T19).

## Non-claims

This task does not implement attention, transpose, or any new tensor operation (deferred to a
future P0-T19). It does not claim PyTorch, JAX, or real-model numerical conformance — that
remains Phase 2's separately-gated deliverable. It does not touch
`crates/forgellm-reference/src/lib.rs`, `numerical_contract.rs`, `reference_ops.rs`, or
`decoder_primitives.rs` — the pre-existing hand-authored golden-constant tests are deliberately
left unconverted; retrofitting them to draw from the same fixture is valuable, real follow-up
work, not bundled here to keep this increment reviewable as one coherent change. It does not
generalize `scripts/validate_loop_engineering.py` beyond its current `P0-T10` scope, and adds no
file under `artifacts/governance/loop-engineering/`.
