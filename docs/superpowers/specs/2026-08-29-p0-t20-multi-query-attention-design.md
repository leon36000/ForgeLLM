# P0-T20 design: bounded multi-query attention

Date: 2026-08-29
Status: approved for bounded implementation by the active ForgeLLM continuation
Task: `P0-T20`

## Decision

Add one CPU reference function:

```text
attention_decode_multi_query(
    queries: &Tensor,
    keys: &Tensor,
    values: &Tensor,
) -> Result<Tensor, ReferenceError>
```

The accepted shapes are `queries=[query_count, head_dim]`,
`keys=[context_len, head_dim]`, and `values=[context_len, head_dim]`. All
dimensions are already non-zero under `Tensor::new`. The result is
`[query_count, head_dim]`.

This is a context-supplied reference primitive, not a policy layer. The caller
chooses the key/value context. No causal mask is inferred or applied; masked or
full self-attention policy remains a later task.

## Exact composition

For each query row, the implementation performs the following fixed sequence:

1. Transpose `keys` with the existing checked `transpose` primitive.
2. Compute `queries @ keysᵀ` with the existing checked `matmul`, accumulating in
   `f64` and narrowing each score to `f32` exactly as that primitive does.
3. Multiply each score in `f64` by `1 / sqrt(head_dim)` and cast once to `f32`,
   matching P0-T19's single-query scale step.
4. Pass exactly one contiguous score row at a time to the existing flat
   `softmax`. Concatenate the returned probability rows in query order.
5. Materialize the probability matrix and compute `probabilities @ values`
   with the existing checked `matmul`.

The row boundary is semantic: no maximum, exponential denominator, or
probability from one query row may be reused by another. Existing primitive
signatures and numerical behavior are unchanged.

## Failure behavior

The function first requires rank-two queries; `transpose` validates key rank
and finiteness, and the existing `matmul` calls validate dimensions, values
rank, finiteness, result finiteness, and recoverable output allocation. Thus a
bad query, key, or value fails closed through the existing typed
`ReferenceError` variants; a two-dimensional value tensor with the wrong
output width is rejected before the final multiplication. The function adds no
new error enum variant.

## Oracle and numerical boundary

`multi_query_attention_oracle` repeats the reviewed P0-T19
`attention_oracle` composition independently for every exact-Fraction query
row and returns a matrix of contexts plus a matching matrix of per-element
tolerances. It explicitly rounds the raw score and scale result to the f32 bit
pattern before invoking the Decimal softmax oracle. The existing P0-T19
softmax error budget is propagated through the final weighted sum separately
for each query row; the value-column absolute sum and two f32 half-ULP terms
remain per output element.

The oracle's exact-Fraction accumulation precondition is documented and
mechanically checked when fixture inputs are generated: the generator rebuilds
each f64 matmul fold from exact f32 operands, checks every sequential partial
sum for finite binary64 representability, and uses the f32 probabilities from
the same f64 exp/divide/cast sequence for the final fold. Random tests use
small dimensions or low-bit-count, shared-power-of-two inputs so this
precondition is true rather than assumed. The oracle is a reference artifact,
not a claim of cross-platform libm identity or real-model conformance.

## Verification design

The Rust integration test contains a from-scratch row-wise implementation and
tests different query rows, context length one, malformed ranks/dimensions,
non-finite inputs, and typed failures. Python tests independently simulate the
compiled Rust operation order, exercise bounded randomized inputs, and check
the returned per-row tolerances plus a near-f32-rounding-boundary case.

The pinned fixture receives at least one context-length-one case and one
multi-position case. Its existing restricted parser and SHA-256 pin remain the
only fixture trust surface; no `serde_json` or other dependency is added.

## Explicit exclusions

This checkpoint does not implement causal masking, full self-attention policy,
multi-head layout, RoPE/ALiBi, KV-cache management, batching/scheduling,
`dense_decode_single_token` integration, runtime/backend/ABI code, model
loading, PyTorch/JAX comparison, hardware probes, CUDA/ROCm, benchmarks, or
performance claims.
