# P0-T20 evidence: bounded multi-query attention

## Status and boundary

This is an in-progress evidence record for task `P0-T20`. The candidate is
based on protected `main@cc5a90d0190bf84e3124a7e81bbe52bc7d0820bc` and remains
isolated until independent review, exact-head hosted checks and merge are
complete. It is a CPU-only reference increment. It does not claim causal
masking, full self-attention policy, multi-head layout, RoPE/ALiBi, KV-cache
management, model loading, PyTorch/JAX conformance, hardware behavior,
CUDA/ROCm, runtime/backend/ABI integration, serving, performance or production
readiness.

## TDD receipt

The failing tests were added before the implementation:

- `cargo test --test multi_query_attention --locked` failed with Rust error
  `unresolved import forgellm_reference::attention_decode_multi_query`;
- `PYTHONPATH=src python3 -m pytest -q tests/test_reference_oracle.py` failed
  during collection because `multi_query_attention_oracle` was not yet
  importable.

The packet was then validated, the smallest Rust implementation and independent
oracle were added, and the focused tests were rerun.

## Implemented contract

`attention_decode_multi_query` accepts finite rank-two tensors with shapes
`[query_count, head_dim]`, `[context_len, head_dim]`, and
`[context_len, head_dim]`. It transposes keys, computes the existing checked
matmul, performs the P0-T19 f64 scale followed by one f32 cast, invokes the
existing flat softmax once for each contiguous query row, and performs the
final checked matmul. A two-dimensional values tensor with a width other than
`head_dim` is rejected with a typed `DimensionMismatch`; no existing primitive
was changed.

`multi_query_attention_oracle` repeats the reviewed P0-T19 oracle independently
for every query row and returns a matching context/tolerance matrix. Raw and
scaled intermediate values are rounded to f32 before each row's softmax. The
per-element bound is the existing softmax budget propagated through that row's
value-column absolute sum plus two half-ULP terms for the independent final
narrowing casts. Fixture generation mechanically checks the exact-Fraction
accumulation precondition for its committed cases; randomized tests use small
dimensions and bounded inputs rather than pretending the precondition holds for
arbitrary large full-mantissa inputs.

## Local evidence

At the current candidate checkpoint:

- focused Rust multi-query integration: **12 passed**;
- focused oracle module: **60 passed**;
- full `make ci` run before the final state/review closeout: **563 Python tests
  passed**, **230 speculative tests passed**, and **101 Rust tests passed**;
- fixture generator `--check`: passed;
- fixture SHA-256: `238bc4a1b8650cc995d952155c2b2c4df6e87864da54724ac2df0ecc13775dfb`;
- `cargo fmt --all --check`, Clippy, packet validation and project validation:
  passed at the corresponding checkpoints;
- no changes to `Cargo.toml`, `Cargo.lock`, `pyproject.toml`, or
  `artifacts/governance/loop-engineering/`.

The fixture contains `multi_query_context_len_one` and
`multi_query_context_len_three`, and the restricted Rust contract dispatch
executes both. The Python suite includes bounded randomized comparisons,
context-length-one exactness, row independence, malformed-shape checks, and a
raw-score f32 tie case built from representable inputs.

## Review and publication gates

The first read-only Luna audit occurred before fixture/state finalization and
returned `NO-GO` for the then-missing fixture/state/review artifacts and the
then-unrounded independent scale result. Those concrete findings were resolved
before this record was written; that early verdict is not being counted as
final acceptance. A fresh independent Luna review and one GPT-5.6-Sol critical
gate on the exact final candidate are required before push. The exact PR head,
hosted required checks and merge SHA are intentionally blank until observed.

## Residual limitations

The oracle inherits P0-T19's documented exact-accumulation precondition for
arbitrary large/full-mantissa inputs and does not turn that inherited function
into a general numerical proof. No real model, PyTorch, hardware, accelerator,
runtime, backend or performance evidence is present. P0-T09's Sonar secret and
platform lifecycle remain untouched; no secret value or external setting was
read or changed, and no LiteLLM or external model trio was used as evidence.
