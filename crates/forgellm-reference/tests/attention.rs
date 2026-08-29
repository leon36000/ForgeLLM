use forgellm_reference::{ReferenceError, Tensor, attention_decode_single_query};

fn assert_close(actual: f32, expected: f32, tolerance: f32) {
    let delta = (actual - expected).abs();
    assert!(
        delta <= tolerance,
        "actual={actual:?} expected={expected:?} delta={delta:?} tolerance={tolerance:?}"
    );
}

/// Independently re-derives single-query scaled dot-product attention from raw `f64` loops
/// (no call into the crate's own `matmul`/`transpose`/`softmax`), mirroring the same
/// operation order the real implementation performs: `f64`-accumulated dot products cast once
/// to `f32`, one `f32` scale multiply, a max-shifted softmax, then an `f64`-accumulated
/// weighted sum cast once to `f32`. This is the same "hand-written independent pipeline,
/// compared against the crate's composed function" pattern `dense_decoder.rs` already uses.
fn oracle_attention(
    query: &[f32],
    keys: &[f32],
    values: &[f32],
    context_len: usize,
    head_dim: usize,
) -> Vec<f32> {
    let mut raw_scores = vec![0.0f32; context_len];
    for (row, score) in raw_scores.iter_mut().enumerate() {
        let accumulator = (0..head_dim).fold(0.0f64, |sum, column| {
            sum + f64::from(query[column]) * f64::from(keys[row * head_dim + column])
        });
        *score = accumulator as f32;
    }

    let scale = 1.0f32 / (head_dim as f32).sqrt();
    let scaled: Vec<f32> = raw_scores.iter().map(|score| *score * scale).collect();

    let maximum = f64::from(scaled.iter().copied().fold(f32::NEG_INFINITY, f32::max));
    let exponentials: Vec<f64> = scaled
        .iter()
        .map(|value| (f64::from(*value) - maximum).exp())
        .collect();
    let denominator: f64 = exponentials.iter().sum();
    let probabilities: Vec<f32> = exponentials
        .iter()
        .map(|exponential| (exponential / denominator) as f32)
        .collect();

    let mut context = vec![0.0f32; head_dim];
    for (column, output) in context.iter_mut().enumerate() {
        let accumulator = (0..context_len).fold(0.0f64, |sum, row| {
            sum + f64::from(probabilities[row]) * f64::from(values[row * head_dim + column])
        });
        *output = accumulator as f32;
    }
    context
}

/// `(query, keys, values, context_len, head_dim)` for one golden-oracle comparison case.
type AttentionCase<'a> = (&'a [f32], &'a [f32], &'a [f32], usize, usize);

#[test]
fn attention_matches_independent_golden_oracle() {
    let cases: &[AttentionCase] = &[
        (
            &[1.0, 0.0],
            &[1.0, 0.0, 0.0, 1.0],
            &[1.0, 2.0, 3.0, 4.0],
            2,
            2,
        ),
        (
            &[0.5, -1.5, 2.0],
            &[1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0],
            &[2.0, -1.0, 0.5, 1.0, 0.0, 3.0, -2.0, 4.0, 1.0, 1.0, 1.0, 1.0],
            4,
            3,
        ),
        (&[3.0], &[1.0, -1.0, 2.0], &[5.0, -5.0, 10.0], 3, 1),
    ];

    for (case_index, (query, keys, values, context_len, head_dim)) in cases.iter().enumerate() {
        let query_tensor = Tensor::new(vec![1, *head_dim], query.to_vec()).unwrap();
        let keys_tensor = Tensor::new(vec![*context_len, *head_dim], keys.to_vec()).unwrap();
        let values_tensor = Tensor::new(vec![*context_len, *head_dim], values.to_vec()).unwrap();

        let expected = oracle_attention(query, keys, values, *context_len, *head_dim);
        let actual =
            attention_decode_single_query(&query_tensor, &keys_tensor, &values_tensor).unwrap();

        assert_eq!(actual.shape(), &[1, *head_dim], "case={case_index}");
        for (left, right) in actual.data().iter().zip(&expected) {
            assert_close(*left, *right, 1.0e-5);
        }
    }
}

#[test]
fn attention_averages_values_when_scores_are_equal() {
    // query is orthogonal-equal to both one-hot key rows (dot product 1 against each), so
    // every context position scores identically regardless of the 1/sqrt(head_dim) scale --
    // softmax must then be exactly uniform, and the context vector must be the exact
    // (rational, hand-verifiable) elementwise mean of `values`, with no transcendental
    // approximation involved anywhere in this expected value.
    let query = Tensor::new(vec![1, 2], vec![1.0, 1.0]).unwrap();
    let keys = Tensor::new(vec![2, 2], vec![1.0, 0.0, 0.0, 1.0]).unwrap();
    let values = Tensor::new(vec![2, 2], vec![2.0, 4.0, 6.0, 8.0]).unwrap();

    let context = attention_decode_single_query(&query, &keys, &values).unwrap();

    assert_eq!(context.shape(), &[1, 2]);
    assert_close(context.data()[0], 4.0, 1.0e-6);
    assert_close(context.data()[1], 6.0, 1.0e-6);
}

#[test]
fn attention_rejects_multi_row_query() {
    let query = Tensor::new(vec![2, 2], vec![1.0, 0.0, 0.0, 1.0]).unwrap();
    let keys = Tensor::new(vec![2, 2], vec![1.0, 0.0, 0.0, 1.0]).unwrap();
    let values = Tensor::new(vec![2, 2], vec![1.0, 0.0, 0.0, 1.0]).unwrap();

    let error = attention_decode_single_query(&query, &keys, &values).unwrap_err();

    assert_eq!(
        error,
        ReferenceError::UnsupportedQueryCount {
            operation: "attention_decode_single_query",
            actual: 2,
        }
    );
}

#[test]
fn attention_rejects_non_rank_two_query() {
    let query = Tensor::new(vec![1, 1, 2], vec![1.0, 0.0]).unwrap();
    let keys = Tensor::new(vec![2, 2], vec![1.0, 0.0, 0.0, 1.0]).unwrap();
    let values = Tensor::new(vec![2, 2], vec![1.0, 0.0, 0.0, 1.0]).unwrap();

    let error = attention_decode_single_query(&query, &keys, &values).unwrap_err();

    assert_eq!(
        error,
        ReferenceError::RankMismatch {
            operation: "attention_decode_single_query",
            expected: 2,
            actual: 3,
        }
    );
}

#[test]
fn attention_rejects_key_value_context_length_mismatch() {
    let query = Tensor::new(vec![1, 2], vec![1.0, 0.0]).unwrap();
    let keys = Tensor::new(vec![2, 2], vec![1.0, 0.0, 0.0, 1.0]).unwrap();
    let values = Tensor::new(vec![3, 2], vec![1.0; 6]).unwrap();

    let error = attention_decode_single_query(&query, &keys, &values).unwrap_err();

    assert_eq!(
        error,
        ReferenceError::DimensionMismatch {
            operation: "matmul",
            left: 2,
            right: 3,
        }
    );
}

#[test]
fn attention_rejects_head_dim_mismatch_between_query_and_keys() {
    let query = Tensor::new(vec![1, 3], vec![1.0, 0.0, 0.0]).unwrap();
    let keys = Tensor::new(vec![2, 2], vec![1.0, 0.0, 0.0, 1.0]).unwrap();
    let values = Tensor::new(vec![2, 2], vec![1.0, 0.0, 0.0, 1.0]).unwrap();

    let error = attention_decode_single_query(&query, &keys, &values).unwrap_err();

    assert_eq!(
        error,
        ReferenceError::DimensionMismatch {
            operation: "matmul",
            left: 3,
            right: 2,
        }
    );
}

#[test]
fn attention_rejects_non_rank_two_keys() {
    // keys' own rank is validated by the nested `transpose` call, before matmul ever runs.
    let query = Tensor::new(vec![1, 2], vec![1.0, 0.0]).unwrap();
    let keys = Tensor::new(vec![4], vec![1.0, 0.0, 0.0, 1.0]).unwrap();
    let values = Tensor::new(vec![2, 2], vec![1.0, 0.0, 0.0, 1.0]).unwrap();

    let error = attention_decode_single_query(&query, &keys, &values).unwrap_err();

    assert_eq!(
        error,
        ReferenceError::RankMismatch {
            operation: "transpose",
            expected: 2,
            actual: 1,
        }
    );
}

#[test]
fn attention_rejects_non_rank_two_values() {
    // values' own rank is validated by the final `matmul` call, as its right-hand operand.
    let query = Tensor::new(vec![1, 2], vec![1.0, 0.0]).unwrap();
    let keys = Tensor::new(vec![2, 2], vec![1.0, 0.0, 0.0, 1.0]).unwrap();
    let values = Tensor::new(vec![2, 1, 2], vec![1.0, 0.0, 0.0, 1.0]).unwrap();

    let error = attention_decode_single_query(&query, &keys, &values).unwrap_err();

    assert_eq!(
        error,
        ReferenceError::RankMismatch {
            operation: "matmul",
            expected: 2,
            actual: 3,
        }
    );
}

#[test]
fn attention_context_len_one_returns_values_row_exactly() {
    // A single-position context makes softmax exactly 1.0 regardless of the score or scale --
    // context must equal `values[0]` exactly, independent of query/keys. Mirrors
    // tests/test_reference_oracle.py's test_attention_oracle_context_len_one_returns_values_row_exactly.
    let query = Tensor::new(vec![1, 2], vec![3.0, -1.0]).unwrap();
    let keys = Tensor::new(vec![1, 2], vec![5.0, 2.0]).unwrap();
    let values = Tensor::new(vec![1, 2], vec![7.0, -4.0]).unwrap();

    let context = attention_decode_single_query(&query, &keys, &values).unwrap();

    assert_eq!(context.shape(), &[1, 2]);
    assert_eq!(context.data(), &[7.0, -4.0]);
}

#[test]
fn attention_propagates_non_finite_query() {
    let query = Tensor::new(vec![1, 2], vec![1.0, f32::NAN]).unwrap();
    let keys = Tensor::new(vec![2, 2], vec![1.0, 0.0, 0.0, 1.0]).unwrap();
    let values = Tensor::new(vec![2, 2], vec![1.0, 0.0, 0.0, 1.0]).unwrap();

    let error = attention_decode_single_query(&query, &keys, &values).unwrap_err();

    assert_eq!(
        error,
        ReferenceError::NonFiniteInput {
            operation: "matmul",
            index: 1,
        }
    );
}

#[test]
fn attention_propagates_non_finite_keys() {
    let query = Tensor::new(vec![1, 2], vec![1.0, 0.0]).unwrap();
    let keys = Tensor::new(vec![2, 2], vec![1.0, 0.0, f32::NAN, 1.0]).unwrap();
    let values = Tensor::new(vec![2, 2], vec![1.0, 0.0, 0.0, 1.0]).unwrap();

    let error = attention_decode_single_query(&query, &keys, &values).unwrap_err();

    assert_eq!(
        error,
        ReferenceError::NonFiniteInput {
            operation: "transpose",
            index: 2,
        }
    );
}

#[test]
fn attention_propagates_non_finite_values() {
    let query = Tensor::new(vec![1, 2], vec![1.0, 0.0]).unwrap();
    let keys = Tensor::new(vec![2, 2], vec![1.0, 0.0, 0.0, 1.0]).unwrap();
    let values = Tensor::new(vec![2, 2], vec![1.0, f32::NAN, 0.0, 1.0]).unwrap();

    let error = attention_decode_single_query(&query, &keys, &values).unwrap_err();

    assert_eq!(
        error,
        ReferenceError::NonFiniteInput {
            operation: "matmul",
            index: 1,
        }
    );
}
