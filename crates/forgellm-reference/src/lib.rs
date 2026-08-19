#![forbid(unsafe_code)]

//! Deterministic CPU reference semantics for the first ForgeLLM engine-code slice.
//!
//! The crate intentionally implements a narrow correctness surface: checked contiguous
//! row-major `f32` tensors plus a small set of decoder-relevant operations. It is not a
//! general tensor framework and it makes no performance claim.

use std::error::Error;
use std::fmt::{self, Display, Formatter};

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
}

impl Display for ReferenceError {
    fn fmt(&self, formatter: &mut Formatter<'_>) -> fmt::Result {
        match self {
            Self::EmptyShape => write!(formatter, "tensor shape must contain at least one dimension"),
            Self::ZeroDimension { axis } => write!(formatter, "tensor dimension {axis} must be non-zero"),
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
            Self::EmptyInput { operation } => write!(formatter, "{operation} input must not be empty"),
            Self::LengthMismatch {
                operation,
                left,
                right,
            } => write!(formatter, "{operation} length mismatch: left={left}, right={right}"),
            Self::NonFiniteInput { operation, index } => {
                write!(formatter, "{operation} input at index {index} is not finite")
            }
            Self::NonFiniteWeight { operation, index } => {
                write!(formatter, "{operation} weight at index {index} is not finite")
            }
            Self::InvalidEpsilon => write!(formatter, "rms_norm epsilon must be finite and strictly positive"),
            Self::NonFiniteResult { operation, index } => {
                write!(formatter, "{operation} result at index {index} is not finite")
            }
        }
    }
}

impl Error for ReferenceError {}

/// A checked contiguous row-major `f32` tensor.
#[derive(Debug, Clone, PartialEq)]
pub struct Tensor {
    shape: Box<[usize]>,
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

        Ok(Self {
            shape: shape.into_boxed_slice(),
            data,
        })
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

fn first_non_finite(values: &[f32]) -> Option<usize> {
    values.iter().position(|value| !value.is_finite())
}

fn require_finite(values: &[f32], operation: &'static str) -> Result<(), ReferenceError> {
    if let Some(index) = first_non_finite(values) {
        return Err(ReferenceError::NonFiniteInput { operation, index });
    }
    Ok(())
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
    let mut output = Vec::with_capacity(output_len);

    for row in lhs.data.chunks_exact(shared) {
        for column in 0..columns {
            let accumulator = row
                .iter()
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

    Tensor::new(vec![rows, columns], output)
}

/// Computes a numerically stable softmax over one non-empty finite vector.
pub fn softmax(values: &[f32]) -> Result<Vec<f32>, ReferenceError> {
    const OPERATION: &str = "softmax";

    if values.is_empty() {
        return Err(ReferenceError::EmptyInput {
            operation: OPERATION,
        });
    }
    require_finite(values, OPERATION)?;

    let maximum = values
        .iter()
        .copied()
        .fold(f32::NEG_INFINITY, f32::max);
    let exponentials: Vec<f64> = values
        .iter()
        .map(|value| f64::from(*value - maximum).exp())
        .collect();
    let denominator: f64 = exponentials.iter().sum();

    let mut probabilities = Vec::with_capacity(values.len());
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

    let mut output = Vec::with_capacity(values.len());
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
