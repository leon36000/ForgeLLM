# P0-T20 evidence: bounded multi-query attention

## Status and boundary

This is the local closeout evidence record for task `P0-T20`. The initial
implementation head was `c3d01dc47e36005b4b229527a7a019558c91bfb4`; the
first remediation head was `b814770e63147b9dff650744fd5861377d9990a2`, and
the final remediation code head is `0554747b036faba0f4185dd08ccc080fe3a1b76b`.
The integrated candidate exact head reviewed below is
`99aea33bb5159f9888d7641c47012c71a417a1b9`, based on protected
`main@cc5a90d0190bf84e3124a7e81bbe52bc7d0820bc`; it remains isolated
until independent review, exact-head hosted checks and merge are complete. It is
a CPU-only reference increment. It does not claim causal
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

The first remediation was rejected by the independent Luna audit at
`ecf8ee98936d79838153f47d444c9f63f6f5bed1`: the trace helper had rounded each
partial before the proof guard inspected it. A new regression was added first;
the focused run was **1 failed, 65 deselected**, because the unrepresentable
exact partial `1 + 2^-53` had been returned as `1`. The helper was then changed
to retain exact Fraction partials before any binary64 rounding, and the final
candidate below passed the regression.

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
narrowing casts. Fixture generation reconstructs every f64 matmul fold from
the actual rounded f32 operands, checks every sequential partial sum for exact
finite binary64 representability, and uses the f32 probabilities from the same
f64 exp/divide/cast sequence for the final fold. The guard rejects non-dyadic
intermediates such as `1/3` even when a later partial sum is zero. Randomized
tests use small dimensions and bounded inputs rather than pretending the
precondition holds for arbitrary large full-mantissa inputs.

## Local evidence

At the final remediation implementation checkpoint
`0554747b036faba0f4185dd08ccc080fe3a1b76b`, integrated at candidate
`99aea33bb5159f9888d7641c47012c71a417a1b9`:

- focused Rust multi-query integration: **12 passed**;
- focused oracle module: **66 passed**;
- full `make ci` run on the remediation candidate: **569 Python tests
  passed**, **230 speculative tests passed**, and **101 Rust tests passed**;
- fixture generator `--check`: passed;
- fixture SHA-256: `7fd3b5824945b868025ddb7272c87e5daa8ffd843536cedc313569bfb999e1bc`;
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

The first two read-only Luna audits found process/receipt gaps; the earlier
critical Sol gate additionally found an unsound exact-accumulation proof. A
fresh Luna audit then found that the first remediation still recorded rounded
partial states. That finding is addressed in the final candidate above: the
trace now preserves exact mathematical partials before the binary64
representability check. None of the prior `NO-GO` verdicts is relabeled as
acceptance. The fresh final Luna review accepted exact head
`99aea33bb5159f9888d7641c47012c71a417a1b9` with no findings, and the fresh
GPT-5.6-Sol critical gate accepted the same exact head with no findings. Their
conditions are limited to this receipt reconciliation, hosted exact-head
checks, protected merge and post-merge evidence. The exact PR head, hosted
required checks and merge SHA remain blank until observed.

## Residual limitations

The oracle inherits P0-T19's documented exact-accumulation precondition for
arbitrary large/full-mantissa inputs and does not turn that inherited function
into a general numerical proof. No real model, PyTorch, hardware, accelerator,
runtime, backend or performance evidence is present. P0-T09's Sonar secret and
platform lifecycle remain untouched; no secret value or external setting was
read or changed, and no LiteLLM or external model trio was used as evidence.
