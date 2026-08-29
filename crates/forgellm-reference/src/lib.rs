#![forbid(unsafe_code)]

//! CPU reference semantics for the first ForgeLLM engine-code slice.
//!
//! The crate intentionally implements a narrow correctness surface: checked contiguous
//! row-major `f32` tensors plus a small set of decoder-relevant operations. Fixed-order
//! arithmetic such as matmul and argmax is deterministic. Softmax uses the Rust `f64::exp`
//! transcendental and therefore has an explicit tolerance-based numerical contract rather
//! than a bitwise cross-platform reproducibility claim. This is not a general tensor
//! framework and it makes no performance claim.

use std::error::Error;
use std::fmt::{self, Display, Formatter};

/// Absolute comparison tolerance used by the pinned softmax reference vectors.
///
/// Rust specifies `f64::exp` with unspecified precision. ForgeLLM therefore validates
/// softmax against this tolerance on its pinned reference evidence environment instead of
/// claiming bitwise equality across Rust versions, targets, or platforms.
pub const SOFTMAX_ABS_TOLERANCE: f32 = 1.0e-6;

/// Typed failures produced by the reference semantics.
#[derive(Debug, Clone, PartialEq)]
pub enum ReferenceError {
    /// Tensor rank must be at least one.
    EmptyShape,
    /// Zero-length dimensions are outside the initial reference-core contract.
    ZeroDimension { axis: usize },
    /// The product of tensor dimensions overflowed `usize`.
    ElementCountOverflow,
    /// The provided buffer length does not match the checked shape product.
    DataLengthMismatch { expected: usize, actual: usize },
    /// An operation received a tensor with an unsupported rank.
    RankMismatch {
        operation: &'static str,
        expected: usize,
        actual: usize,
    },
    /// Two operation dimensions that must agree are different.
    DimensionMismatch {
        operation: &'static str,
        left: usize,
        right: usize,
    },
    /// Two tensors that must have identical shapes are different.
    ShapeMismatch { operation: &'static str },
    /// A requested index is outside the operation's valid half-open range.
    IndexOutOfBounds {
        operation: &'static str,
        index: usize,
        upper_bound: usize,
    },
    /// A vector operation requires at least one value.
    EmptyInput { operation: &'static str },
    /// Two vectors that must have the same length are different.
    LengthMismatch {
        operation: &'static str,
        left: usize,
        right: usize,
    },
    /// An operation input contains a NaN or infinity.
    NonFiniteInput {
        operation: &'static str,
        index: usize,
    },
    /// A normalization weight contains a NaN or infinity.
    NonFiniteWeight {
        operation: &'static str,
        index: usize,
    },
    /// RMSNorm epsilon must be finite and strictly positive.
    InvalidEpsilon,
    /// A finite-input reference operation produced a non-finite `f32` result.
    NonFiniteResult {
        operation: &'static str,
        index: usize,
    },
    /// A recoverable vector reservation failed before an operation produced its result.
    AllocationFailed {
        operation: &'static str,
        requested_elements: usize,
    },
    /// An operation that requires exactly one query row received a different row count.
    UnsupportedQueryCount {
        operation: &'static str,
        actual: usize,
    },
}

impl Display for ReferenceError {
    fn fmt(&self, formatter: &mut Formatter<'_>) -> fmt::Result {
        match self {
            Self::EmptyShape => write!(
                formatter,
                "tensor shape must contain at least one dimension"
            ),
            Self::ZeroDimension { axis } => {
                write!(formatter, "tensor dimension {axis} must be non-zero")
            }
            Self::ElementCountOverflow => write!(formatter, "tensor element count overflows usize"),
            Self::DataLengthMismatch { expected, actual } => write!(
                formatter,
                "tensor data length mismatch: expected {expected} values, received {actual}"
            ),
            Self::RankMismatch {
                operation,
                expected,
                actual,
            } => write!(
                formatter,
                "{operation} rank mismatch: expected rank {expected}, received rank {actual}"
            ),
            Self::DimensionMismatch {
                operation,
                left,
                right,
            } => write!(
                formatter,
                "{operation} dimension mismatch: left={left}, right={right}"
            ),
            Self::ShapeMismatch { operation } => {
                write!(
                    formatter,
                    "{operation} requires tensors with identical shapes"
                )
            }
            Self::IndexOutOfBounds {
                operation,
                index,
                upper_bound,
            } => write!(
                formatter,
                "{operation} index {index} is outside the valid range 0..{upper_bound}"
            ),
            Self::EmptyInput { operation } => {
                write!(formatter, "{operation} input must not be empty")
            }
            Self::LengthMismatch {
                operation,
                left,
                right,
            } => write!(
                formatter,
                "{operation} length mismatch: left={left}, right={right}"
            ),
            Self::NonFiniteInput { operation, index } => {
                write!(
                    formatter,
                    "{operation} input at index {index} is not finite"
                )
            }
            Self::NonFiniteWeight { operation, index } => {
                write!(
                    formatter,
                    "{operation} weight at index {index} is not finite"
                )
            }
            Self::InvalidEpsilon => write!(
                formatter,
                "rms_norm epsilon must be finite and strictly positive"
            ),
            Self::NonFiniteResult { operation, index } => {
                write!(
                    formatter,
                    "{operation} result at index {index} is not finite"
                )
            }
            Self::AllocationFailed {
                operation,
                requested_elements,
            } => write!(
                formatter,
                "{operation} could not reserve {requested_elements} output elements"
            ),
            Self::UnsupportedQueryCount { operation, actual } => write!(
                formatter,
                "{operation} requires exactly one query row, received {actual}"
            ),
        }
    }
}

impl Error for ReferenceError {}

/// A checked contiguous row-major `f32` tensor.
#[derive(Debug, Clone, PartialEq)]
pub struct Tensor {
    shape: Vec<usize>,
    data: Vec<f32>,
}

impl Tensor {
    /// Creates a tensor after validating the shape product and buffer length.
    pub fn new(shape: Vec<usize>, data: Vec<f32>) -> Result<Self, ReferenceError> {
        if shape.is_empty() {
            return Err(ReferenceError::EmptyShape);
        }

        let mut expected = 1usize;
        for (axis, dimension) in shape.iter().copied().enumerate() {
            if dimension == 0 {
                return Err(ReferenceError::ZeroDimension { axis });
            }
            expected = expected
                .checked_mul(dimension)
                .ok_or(ReferenceError::ElementCountOverflow)?;
        }

        if data.len() != expected {
            return Err(ReferenceError::DataLengthMismatch {
                expected,
                actual: data.len(),
            });
        }

        Ok(Self { shape, data })
    }

    /// Returns the immutable tensor shape.
    #[must_use]
    pub fn shape(&self) -> &[usize] {
        &self.shape
    }

    /// Returns the immutable contiguous row-major storage.
    #[must_use]
    pub fn data(&self) -> &[f32] {
        &self.data
    }
}

fn try_vec_with_capacity<T>(
    requested_elements: usize,
    operation: &'static str,
) -> Result<Vec<T>, ReferenceError> {
    let mut values = Vec::new();
    values
        .try_reserve_exact(requested_elements)
        .map_err(|_| ReferenceError::AllocationFailed {
            operation,
            requested_elements,
        })?;
    Ok(values)
}

fn try_clone_shape(shape: &[usize], operation: &'static str) -> Result<Vec<usize>, ReferenceError> {
    let mut cloned = try_vec_with_capacity(shape.len(), operation)?;
    cloned.extend_from_slice(shape);
    Ok(cloned)
}

fn first_non_finite(values: &[f32]) -> Option<usize> {
    values.iter().position(|value| !value.is_finite())
}

fn require_finite(values: &[f32], operation: &'static str) -> Result<(), ReferenceError> {
    if let Some(index) = first_non_finite(values) {
        return Err(ReferenceError::NonFiniteInput { operation, index });
    }
    Ok(())
}

fn require_same_shape(
    lhs: &Tensor,
    rhs: &Tensor,
    operation: &'static str,
) -> Result<(), ReferenceError> {
    if lhs.shape != rhs.shape {
        return Err(ReferenceError::ShapeMismatch { operation });
    }
    Ok(())
}

/// Changes tensor metadata without reordering the contiguous data buffer.
///
/// The tensor is consumed so the existing data allocation is reused. The new shape is checked
/// by [`Tensor::new`] using the same non-empty, non-zero and overflow-safe constructor contract.
pub fn reshape(tensor: Tensor, new_shape: Vec<usize>) -> Result<Tensor, ReferenceError> {
    Tensor::new(new_shape, tensor.data)
}

/// Adds two tensors element by element using exact-shape, fixed-order `f32` semantics.
pub fn elementwise_add(lhs: &Tensor, rhs: &Tensor) -> Result<Tensor, ReferenceError> {
    const OPERATION: &str = "elementwise_add";

    require_same_shape(lhs, rhs, OPERATION)?;
    require_finite(&lhs.data, OPERATION)?;
    require_finite(&rhs.data, OPERATION)?;

    let mut output = try_vec_with_capacity(lhs.data.len(), OPERATION)?;
    for (index, (left, right)) in lhs.data.iter().zip(&rhs.data).enumerate() {
        let value = *left + *right;
        if !value.is_finite() {
            return Err(ReferenceError::NonFiniteResult {
                operation: OPERATION,
                index,
            });
        }
        output.push(value);
    }

    Tensor::new(try_clone_shape(&lhs.shape, OPERATION)?, output)
}

/// Multiplies two tensors element by element using exact-shape, fixed-order `f32` semantics.
pub fn elementwise_mul(lhs: &Tensor, rhs: &Tensor) -> Result<Tensor, ReferenceError> {
    const OPERATION: &str = "elementwise_mul";

    require_same_shape(lhs, rhs, OPERATION)?;
    require_finite(&lhs.data, OPERATION)?;
    require_finite(&rhs.data, OPERATION)?;

    let mut output = try_vec_with_capacity(lhs.data.len(), OPERATION)?;
    for (index, (left, right)) in lhs.data.iter().zip(&rhs.data).enumerate() {
        let value = *left * *right;
        if !value.is_finite() {
            return Err(ReferenceError::NonFiniteResult {
                operation: OPERATION,
                index,
            });
        }
        output.push(value);
    }

    Tensor::new(try_clone_shape(&lhs.shape, OPERATION)?, output)
}

/// Gathers embedding rows from a finite rank-two table in token-ID order.
///
/// Repeated token IDs repeat rows in the output. Empty token-ID sequences are rejected because
/// the initial reference tensor contract does not admit zero-length dimensions.
pub fn embedding_gather(table: &Tensor, token_ids: &[usize]) -> Result<Tensor, ReferenceError> {
    const OPERATION: &str = "embedding_gather";

    if table.shape.len() != 2 {
        return Err(ReferenceError::RankMismatch {
            operation: OPERATION,
            expected: 2,
            actual: table.shape.len(),
        });
    }
    if token_ids.is_empty() {
        return Err(ReferenceError::EmptyInput {
            operation: OPERATION,
        });
    }
    require_finite(&table.data, OPERATION)?;

    let vocabulary = table.shape[0];
    let width = table.shape[1];

    for token_id in token_ids.iter().copied() {
        if token_id >= vocabulary {
            return Err(ReferenceError::IndexOutOfBounds {
                operation: OPERATION,
                index: token_id,
                upper_bound: vocabulary,
            });
        }
    }

    let output_len = token_ids
        .len()
        .checked_mul(width)
        .ok_or(ReferenceError::ElementCountOverflow)?;
    let mut output = try_vec_with_capacity(output_len, OPERATION)?;

    for token_id in token_ids.iter().copied() {
        let row_start = token_id
            .checked_mul(width)
            .ok_or(ReferenceError::ElementCountOverflow)?;
        let row_end = row_start
            .checked_add(width)
            .ok_or(ReferenceError::ElementCountOverflow)?;
        for value in &table.data[row_start..row_end] {
            output.push(*value);
        }
    }

    let mut output_shape = try_vec_with_capacity(2, OPERATION)?;
    output_shape.push(token_ids.len());
    output_shape.push(width);
    Tensor::new(output_shape, output)
}

/// Transposes a rank-two row-major tensor, swapping its two axes.
///
/// Pure data movement: no arithmetic occurs, so there is no rounding to reason about. Input
/// finiteness is still checked for consistency with every other operation in this crate (the
/// same fail-closed convention `embedding_gather` already applies to its own pure-copy path).
pub fn transpose(tensor: &Tensor) -> Result<Tensor, ReferenceError> {
    const OPERATION: &str = "transpose";

    if tensor.shape.len() != 2 {
        return Err(ReferenceError::RankMismatch {
            operation: OPERATION,
            expected: 2,
            actual: tensor.shape.len(),
        });
    }
    require_finite(&tensor.data, OPERATION)?;

    let rows = tensor.shape[0];
    let columns = tensor.shape[1];
    let mut output = try_vec_with_capacity(tensor.data.len(), OPERATION)?;
    for column in 0..columns {
        for row in 0..rows {
            output.push(tensor.data[row * columns + column]);
        }
    }

    let mut output_shape = try_vec_with_capacity(2, OPERATION)?;
    output_shape.push(columns);
    output_shape.push(rows);
    Tensor::new(output_shape, output)
}

/// Computes single-query scaled dot-product attention over a fixed key/value context.
///
/// `query` must have shape `[1, head_dim]`; `keys` and `values` must have shape
/// `[context_len, head_dim]` with equal `context_len` (checked implicitly by the final
/// `matmul`'s dimension check). This is the bounded decode-time attention step: the caller
/// supplies exactly the key/value context the query may attend to. There is no internal causal
/// mask, KV-cache management, or multi-head reshape -- those remain out of scope for this
/// reference increment (see `docs/superpowers/specs/2026-08-28-p0-t19-attention-design.md`).
///
/// The implementation is intentionally a composition of the existing checked primitives, in
/// the same spirit as [`dense_decode_single_token`]: `matmul`/`transpose` for the raw scores,
/// one new `f64`-domain multiply cast once per element for the `1/sqrt(head_dim)` scale, the
/// existing `softmax` for the attention weights, and `matmul` again for the weighted sum over
/// `values`.
pub fn attention_decode_single_query(
    query: &Tensor,
    keys: &Tensor,
    values: &Tensor,
) -> Result<Tensor, ReferenceError> {
    const OPERATION: &str = "attention_decode_single_query";

    if query.shape.len() != 2 {
        return Err(ReferenceError::RankMismatch {
            operation: OPERATION,
            expected: 2,
            actual: query.shape.len(),
        });
    }
    if query.shape[0] != 1 {
        return Err(ReferenceError::UnsupportedQueryCount {
            operation: OPERATION,
            actual: query.shape[0],
        });
    }
    let head_dim = query.shape[1];

    let keys_transposed = transpose(keys)?;
    let raw_scores = matmul(query, &keys_transposed)?;

    // Computed in `f64` and cast once per element, matching this crate's dominant pattern
    // (`matmul`, `rms_norm`): a single correctly-rounded `f64`-domain multiply per score,
    // narrowed to `f32` once, rather than chaining several separately-rounded native-`f32`
    // operations (`f32::sqrt` then `f32` division then `f32` multiply), which would introduce
    // three separate rounding steps instead of one.
    let scale = 1.0f64 / (head_dim as f64).sqrt();
    let mut scaled = try_vec_with_capacity(raw_scores.data.len(), OPERATION)?;
    for (index, score) in raw_scores.data.iter().enumerate() {
        let value = (f64::from(*score) * scale) as f32;
        if !value.is_finite() {
            return Err(ReferenceError::NonFiniteResult {
                operation: OPERATION,
                index,
            });
        }
        scaled.push(value);
    }

    let probabilities = softmax(&scaled)?;
    let context_len = probabilities.len();
    let probabilities_tensor = Tensor::new(vec![1, context_len], probabilities)?;

    matmul(&probabilities_tensor, values)
}

/// Decodes one token through the bounded dense CPU reference pipeline.
///
/// The operation is intentionally a composition of the existing checked primitives:
/// embedding gather, RMS normalization, rank-two projection, softmax and first-index argmax.
/// It accepts only in-memory tensors and makes no model-format, runtime, backend or performance
/// claim.
pub fn dense_decode_single_token(
    embedding_table: &Tensor,
    token_id: usize,
    rms_weights: &[f32],
    rms_epsilon: f32,
    projection: &Tensor,
) -> Result<usize, ReferenceError> {
    let gathered = embedding_gather(embedding_table, &[token_id])?;
    let normalized = rms_norm(gathered.data(), rms_weights, rms_epsilon)?;
    let hidden = Tensor::new(vec![1, normalized.len()], normalized)?;
    let logits = matmul(&hidden, projection)?;
    let probabilities = softmax(logits.data())?;
    argmax(&probabilities)
}

/// Multiplies two rank-two row-major tensors using a fixed accumulation order.
///
/// Products are accumulated in `f64` and converted once per output element to provide a
/// simple, deterministic correctness reference. This is deliberately not a performance path.
pub fn matmul(lhs: &Tensor, rhs: &Tensor) -> Result<Tensor, ReferenceError> {
    const OPERATION: &str = "matmul";

    if lhs.shape.len() != 2 {
        return Err(ReferenceError::RankMismatch {
            operation: OPERATION,
            expected: 2,
            actual: lhs.shape.len(),
        });
    }
    if rhs.shape.len() != 2 {
        return Err(ReferenceError::RankMismatch {
            operation: OPERATION,
            expected: 2,
            actual: rhs.shape.len(),
        });
    }

    let rows = lhs.shape[0];
    let shared = lhs.shape[1];
    let rhs_shared = rhs.shape[0];
    let columns = rhs.shape[1];
    if shared != rhs_shared {
        return Err(ReferenceError::DimensionMismatch {
            operation: OPERATION,
            left: shared,
            right: rhs_shared,
        });
    }

    require_finite(&lhs.data, OPERATION)?;
    require_finite(&rhs.data, OPERATION)?;

    let output_len = rows
        .checked_mul(columns)
        .ok_or(ReferenceError::ElementCountOverflow)?;
    let mut output = try_vec_with_capacity(output_len, OPERATION)?;

    for row in lhs.data.chunks_exact(shared) {
        for column in 0..columns {
            let accumulator =
                row.iter()
                    .copied()
                    .enumerate()
                    .fold(0.0f64, |sum, (inner, lhs_value)| {
                        let rhs_value = rhs.data[inner * columns + column];
                        sum + f64::from(lhs_value) * f64::from(rhs_value)
                    });
            let value = accumulator as f32;
            if !value.is_finite() {
                return Err(ReferenceError::NonFiniteResult {
                    operation: OPERATION,
                    index: output.len(),
                });
            }
            output.push(value);
        }
    }

    let mut output_shape = try_vec_with_capacity(2, OPERATION)?;
    output_shape.push(rows);
    output_shape.push(columns);
    Tensor::new(output_shape, output)
}

/// Computes a max-shifted softmax over one non-empty finite vector.
///
/// The operation has a fixed iteration order but calls `f64::exp`, whose precision is
/// unspecified by Rust. Callers comparing reference values should use
/// [`SOFTMAX_ABS_TOLERANCE`] rather than assume bitwise cross-platform equality.
pub fn softmax(values: &[f32]) -> Result<Vec<f32>, ReferenceError> {
    const OPERATION: &str = "softmax";

    if values.is_empty() {
        return Err(ReferenceError::EmptyInput {
            operation: OPERATION,
        });
    }
    require_finite(values, OPERATION)?;

    let maximum = f64::from(values.iter().copied().fold(f32::NEG_INFINITY, f32::max));
    let mut exponentials = try_vec_with_capacity(values.len(), OPERATION)?;
    for value in values {
        exponentials.push((f64::from(*value) - maximum).exp());
    }
    let denominator: f64 = exponentials.iter().sum();

    let mut probabilities = try_vec_with_capacity(values.len(), OPERATION)?;
    for (index, exponential) in exponentials.into_iter().enumerate() {
        let probability = (exponential / denominator) as f32;
        if !probability.is_finite() {
            return Err(ReferenceError::NonFiniteResult {
                operation: OPERATION,
                index,
            });
        }
        probabilities.push(probability);
    }

    Ok(probabilities)
}

/// Applies RMS normalization to one finite vector using elementwise finite weights.
pub fn rms_norm(values: &[f32], weights: &[f32], epsilon: f32) -> Result<Vec<f32>, ReferenceError> {
    const OPERATION: &str = "rms_norm";

    if values.is_empty() {
        return Err(ReferenceError::EmptyInput {
            operation: OPERATION,
        });
    }
    if values.len() != weights.len() {
        return Err(ReferenceError::LengthMismatch {
            operation: OPERATION,
            left: values.len(),
            right: weights.len(),
        });
    }
    if !epsilon.is_finite() || epsilon <= 0.0 {
        return Err(ReferenceError::InvalidEpsilon);
    }
    require_finite(values, OPERATION)?;
    if let Some(index) = first_non_finite(weights) {
        return Err(ReferenceError::NonFiniteWeight {
            operation: OPERATION,
            index,
        });
    }

    let sum_of_squares = values.iter().copied().fold(0.0f64, |sum, value| {
        let value = f64::from(value);
        sum + value * value
    });
    let mean_square = sum_of_squares / values.len() as f64;
    let inverse_rms = 1.0f64 / (mean_square + f64::from(epsilon)).sqrt();

    let mut output = try_vec_with_capacity(values.len(), OPERATION)?;
    for (index, (value, weight)) in values.iter().zip(weights).enumerate() {
        let normalized = (f64::from(*value) * inverse_rms * f64::from(*weight)) as f32;
        if !normalized.is_finite() {
            return Err(ReferenceError::NonFiniteResult {
                operation: OPERATION,
                index,
            });
        }
        output.push(normalized);
    }

    Ok(output)
}

/// Returns the first index of the maximum finite value.
///
/// First-index tie behavior is part of the reference contract.
pub fn argmax(values: &[f32]) -> Result<usize, ReferenceError> {
    const OPERATION: &str = "argmax";

    if values.is_empty() {
        return Err(ReferenceError::EmptyInput {
            operation: OPERATION,
        });
    }
    require_finite(values, OPERATION)?;

    let mut best_index = 0usize;
    let mut best_value = values[0];
    for (index, value) in values.iter().copied().enumerate().skip(1) {
        if value > best_value {
            best_value = value;
            best_index = index;
        }
    }

    Ok(best_index)
}

#[cfg(test)]
mod allocation_tests;

#[cfg(test)]
mod decoder_validation_tests {
    use super::{ReferenceError, Tensor, embedding_gather};

    #[test]
    fn embedding_gather_checks_invalid_id_before_output_capacity() {
        // This deliberately bypasses Tensor::new's storage invariant to exercise the
        // operation-order seam without allocating a huge embedding table. With the
        // old ordering, three rows of this width overflowed before the invalid ID was
        // reported; the public constructor cannot represent that table in memory.
        let table = Tensor {
            shape: vec![3, usize::MAX / 2 + 1],
            data: Vec::new(),
        };

        let error = embedding_gather(&table, &[3, 3, 3]).unwrap_err();

        assert_eq!(
            error,
            ReferenceError::IndexOutOfBounds {
                operation: "embedding_gather",
                index: 3,
                upper_bound: 3,
            }
        );
    }
}
