# P0-T18 Differential Reference Oracle Implementation Plan

> **Note on tooling:** the historical convention in this repository's `docs/superpowers/plans/` files references `superpowers:subagent-driven-development`/`superpowers:executing-plans` as the expected execution skill. The Superpowers plugin is not installed in the session that drafted this plan. This plan follows the same spec-plus-plan-plus-task-packet structure without claiming to invoke a skill that was not actually available.

**Goal:** Deliver a stdlib-only, re-derivable differential oracle for `crates/forgellm-reference`'s existing operations, replacing hand-copied test constants with a committed, hash-pinned, CI-regenerated fixture.

**Architecture:** Pure-Python oracle (`fractions.Fraction` for exact ops, `decimal.Decimal` with a derived precision and fail-closed escalation for transcendental ops) generates a flat JSON fixture; a small, dependency-free Rust reader consumes it in new, additive test files. No production source in `crates/forgellm-reference/src/lib.rs` changes.

**Tech stack:** Python 3 stdlib only (`fractions`, `decimal`, `struct`, `json`), pytest, Rust 1.97.1 (pinned), cargo test/fmt/clippy, Make.

**Spec:** `docs/superpowers/specs/2026-08-27-p0-t18-reference-oracle-design.md`

## Global constraints

- ForgeLLM task packets and accepted ADRs remain the source of truth; this plan may narrow but never widen `tasks/open/P0-T18-differential-reference-oracle.yaml`.
- No new Rust or Python dependency, anywhere.
- `crates/forgellm-reference/src/lib.rs`, `numerical_contract.rs`, `reference_ops.rs`, and `decoder_primitives.rs` are not modified — new tests are additive.
- No file under `artifacts/governance/loop-engineering/` is created (see spec; that validator is hard-pinned to `P0-T10`).
- No path frozen by open PR #72 or PR #75 is touched.
- Final integration requires exact-head CI and independent correctness/numerical-methods review; no direct push to `main`.

---

### Task 1: Establish the RED suite for the rounding routine
- [ ] Write `tests/test_reference_oracle.py` with the f32-bit-pattern round-trip property test (`f32_bits_to_fraction` then round-to-f32-bits returns the identical bit pattern) covering: all-zero, negative zero, smallest/largest normal, smallest/largest subnormal, both exact-tie mantissa parities, and a random sample across exponent ranges.
- [ ] Confirm these tests fail (module does not exist yet).

### Task 2: Implement exact f32↔Fraction conversion and round-half-to-even rounding
- [ ] Implement `src/forgellm_governance/reference_oracle.py`: `f32_bits_to_fraction`, `round_fraction_to_f32_bits` (round-half-to-even, integer/exact-Fraction comparisons only, explicit subnormal/overflow handling).
- [ ] Task 1's tests pass.

### Task 3: Implement the exact-Fraction ops (matmul, elementwise_add/mul, embedding_gather)
- [ ] Implement each as a pure-Python function operating on `Fraction`-valued tensors, mirroring `lib.rs`'s exact accumulation order.
- [ ] Implement the mechanical f64-exactness precondition check (assert every intermediate partial sum's bit length stays within 53 bits for the fixture's chosen magnitudes) as part of the generator, not as a silent assumption.
- [ ] Unit tests confirming zero-tolerance agreement against hand-computed small examples.

### Task 4: Implement the Decimal-based ops (softmax, rms_norm) with a derived, escalating precision
- [ ] Implement `decimal_transcendental_with_escape`: compute at a base precision, check whether the result is provably farther from the nearest f32 rounding boundary than the error bound at that precision; if not, double precision and retry; raise (fail closed) past a maximum.
- [ ] Document, in the module docstring, the derivation of the softmax error budget (shift/exp/sum/divide/cast forward-error propagation, stated libm-quality assumption) and the rms_norm error budget (IEEE-754 correct-rounding guarantee for sqrt/division).
- [ ] Unit tests for both ops against known values, plus the extreme-shift/subnormal-tail cases already covered by the existing `numerical_contract.rs` (to confirm the oracle agrees with, not merely duplicates, the crate's current behavior).

### Task 5: Build the fixture generator and its `--check` mode
- [ ] Implement `scripts/generate_reference_oracle_fixture.py`: deterministic case list (sorted by `(op, case_id)`), hex-encoded f32 bit patterns, `sort_keys=True` JSON output, per-case embedded comparison tolerance and its derivation string.
- [ ] Implement `--check`: regenerate in memory, diff byte-for-byte against the committed file, exit non-zero with a diff summary on mismatch, never mutate the working tree.
- [ ] Generate and commit `crates/forgellm-reference/tests/fixtures/reference_ops_oracle.json` and its `.sha256` pin.

### Task 6: Build the Rust fixture reader and contract tests
- [ ] Implement `crates/forgellm-reference/tests/support/mod.rs`: a schema-restricted reader for exactly the fixture's flat grammar (fixed field names, hex bit-pattern strings), with its own malformed-input tests. Add `#![forbid(unsafe_code)]` explicitly at the top of new test files (the crate-level attribute does not propagate to separate `tests/*.rs` binaries).
- [ ] Implement `crates/forgellm-reference/tests/reference_ops_oracle_contract.rs`: for each fixture case, call the corresponding `lib.rs` function and compare against the fixture's expected value at its embedded tolerance (zero for exact-Fraction ops, the derived budget for Decimal-based ops).
- [ ] `cargo test --workspace --all-targets --locked` passes, including both the existing hand-authored tests (unmodified) and the new contract tests.

### Task 7: CI and documentation closeout
- [ ] Confirm `cargo fmt --all --check` and `cargo clippy --workspace --all-targets --locked -- -D warnings` pass.
- [ ] Confirm `python3 scripts/generate_reference_oracle_fixture.py --check --root .` and `sha256sum -c crates/forgellm-reference/tests/fixtures/reference_ops_oracle.sha256` pass.
- [ ] Write `docs/quality/P0-T18-REFERENCE-ORACLE.md` recording exact test counts before/after, the per-op budget derivations, the fixture's committed hash, and confirmation that no dependency or `artifacts/governance/loop-engineering/` file was added.
- [ ] Update `docs/state/CURRENT_STATE.md` / `HANDOFF.md` only within this task's `allowed_paths`, stating this is a bounded CPU-only reference increment with no PyTorch/real-model conformance claim.
- [ ] Request independent correctness and numerical-methods review against the exact final head before any merge.
