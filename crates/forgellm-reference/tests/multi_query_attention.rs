use forgellm_reference::{ReferenceError, Tensor, attention_decode_multi_query};

fn assert_close(actual: f32, expected: f32, tolerance: f32) {
    let delta = (actual - expected).abs();
    assert!(
        delta <= tolerance,
        "actual={actual:?} expected={expected:?} delta={delta:?} tolerance={tolerance:?}"
    );
}

/// Re-derives the row-wise operation order without calling the crate's attention, matmul,
/// transpose, or softmax implementation. The f64 scale and explicit f32 casts mirror the
/// production contract rather than relying on an expected literal.
fn oracle_multi_query(
    queries: &[f32],
    keys: &[f32],
    values: &[f32],
    query_count: usize,
    context_len: usize,
    head_dim: usize,
) -> Vec<f32> {
    let scale = 1.0f64 / (head_dim as f64).sqrt();
    let mut output = Vec::with_capacity(query_count * head_dim);

    for query_row in 0..query_count {
        let mut scaled_scores = Vec::with_capacity(context_len);
        for key_row in 0..context_len {
            let score = (0..head_dim).fold(0.0f64, |sum, column| {
                sum + f64::from(queries[query_row * head_dim + column])
                    * f64::from(keys[key_row * head_dim + column])
            });
            let scaled = ((score as f32) as f64 * scale) as f32;
            scaled_scores.push(f64::from(scaled));
        }

        let maximum = scaled_scores
            .iter()
            .copied()
            .fold(f64::NEG_INFINITY, f64::max);
        let exponentials: Vec<f64> = scaled_scores
            .iter()
            .map(|score| (*score - maximum).exp())
            .collect();
        let denominator: f64 = exponentials.iter().sum();
        let probabilities: Vec<f32> = exponentials
            .iter()
            .map(|exponential| (exponential / denominator) as f32)
            .collect();

        for column in 0..head_dim {
            let context = (0..context_len).fold(0.0f64, |sum, key_row| {
                sum + f64::from(probabilities[key_row])
                    * f64::from(values[key_row * head_dim + column])
            });
            output.push(context as f32);
        }
    }

    output
}

#[test]
fn multi_query_attention_matches_independent_rowwise_oracle() {
    let query_values = vec![1.0, 0.0, 0.0, 1.0];
    let key_values = vec![1.0, 0.0, 0.0, 1.0, 1.0, 1.0];
    let value_values = vec![2.0, 0.0, 0.0, 2.0, 1.0, 3.0];
    let queries = Tensor::new(vec![2, 2], query_values.clone()).unwrap();
    let keys = Tensor::new(vec![3, 2], key_values.clone()).unwrap();
    let values = Tensor::new(vec![3, 2], value_values.clone()).unwrap();

    let actual = attention_decode_multi_query(&queries, &keys, &values).unwrap();
    let expected = oracle_multi_query(&query_values, &key_values, &value_values, 2, 3, 2);

    assert_eq!(actual.shape(), &[2, 2]);
    for (got, want) in actual.data().iter().zip(expected) {
        assert_close(*got, want, 1.0e-5);
    }
}

#[test]
fn multi_query_attention_normalizes_each_query_row_independently() {
    let queries = Tensor::new(vec![2, 2], vec![1.0, 0.0, 0.0, 1.0]).unwrap();
    let keys = Tensor::new(vec![2, 2], vec![1.0, 0.0, 0.0, 1.0]).unwrap();
    let values = Tensor::new(vec![2, 2], vec![10.0, 0.0, 0.0, 20.0]).unwrap();

    let actual = attention_decode_multi_query(&queries, &keys, &values).unwrap();

    assert_eq!(actual.shape(), &[2, 2]);
    assert!(actual.data()[0] > actual.data()[1]);
    assert!(actual.data()[3] > actual.data()[2]);
    assert!(actual.data()[0] > actual.data()[2]);
}

#[test]
fn multi_query_attention_context_len_one_returns_each_value_row_exactly() {
    let queries = Tensor::new(vec![2, 3], vec![3.0, -1.0, 2.0, 0.0, 4.0, 1.0]).unwrap();
    let keys = Tensor::new(vec![1, 3], vec![5.0, 2.0, -4.0]).unwrap();
    let values = Tensor::new(vec![1, 3], vec![7.0, -4.0, 2.5]).unwrap();

    let actual = attention_decode_multi_query(&queries, &keys, &values).unwrap();

    assert_eq!(actual.shape(), &[2, 3]);
    assert_eq!(actual.data(), &[7.0, -4.0, 2.5, 7.0, -4.0, 2.5]);
}

#[test]
fn multi_query_attention_rejects_non_rank_two_queries() {
    let queries = Tensor::new(vec![1, 1, 2], vec![1.0, 0.0]).unwrap();
    let keys = Tensor::new(vec![1, 2], vec![1.0, 0.0]).unwrap();
    let values = Tensor::new(vec![1, 2], vec![1.0, 0.0]).unwrap();

    let error = attention_decode_multi_query(&queries, &keys, &values).unwrap_err();

    assert_eq!(
        error,
        ReferenceError::RankMismatch {
            operation: "attention_decode_multi_query",
            expected: 2,
            actual: 3,
        }
    );
}

#[test]
fn multi_query_attention_propagates_dimension_mismatch() {
    let queries = Tensor::new(vec![2, 3], vec![1.0; 6]).unwrap();
    let keys = Tensor::new(vec![2, 2], vec![1.0; 4]).unwrap();
    let values = Tensor::new(vec![2, 2], vec![1.0; 4]).unwrap();

    let error = attention_decode_multi_query(&queries, &keys, &values).unwrap_err();

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
fn multi_query_attention_rejects_value_width_mismatch() {
    let queries = Tensor::new(vec![2, 2], vec![1.0; 4]).unwrap();
    let keys = Tensor::new(vec![2, 2], vec![1.0; 4]).unwrap();
    let values = Tensor::new(vec![2, 3], vec![1.0; 6]).unwrap();

    let error = attention_decode_multi_query(&queries, &keys, &values).unwrap_err();

    assert_eq!(
        error,
        ReferenceError::DimensionMismatch {
            operation: "attention_decode_multi_query",
            left: 2,
            right: 3,
        }
    );
}

#[test]
fn multi_query_attention_propagates_key_value_context_mismatch() {
    let queries = Tensor::new(vec![2, 2], vec![1.0; 4]).unwrap();
    let keys = Tensor::new(vec![2, 2], vec![1.0; 4]).unwrap();
    let values = Tensor::new(vec![3, 2], vec![1.0; 6]).unwrap();

    let error = attention_decode_multi_query(&queries, &keys, &values).unwrap_err();

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
fn multi_query_attention_propagates_non_finite_values() {
    let queries = Tensor::new(vec![2, 2], vec![1.0; 4]).unwrap();
    let keys = Tensor::new(vec![2, 2], vec![1.0; 4]).unwrap();
    let values = Tensor::new(vec![2, 2], vec![1.0, f32::NAN, 1.0, 1.0]).unwrap();

    let error = attention_decode_multi_query(&queries, &keys, &values).unwrap_err();

    assert_eq!(
        error,
        ReferenceError::NonFiniteInput {
            operation: "matmul",
            index: 1,
        }
    );
}

#[test]
fn multi_query_attention_propagates_non_finite_query() {
    let queries = Tensor::new(vec![2, 2], vec![1.0, f32::NAN, 1.0, 1.0]).unwrap();
    let keys = Tensor::new(vec![2, 2], vec![1.0; 4]).unwrap();
    let values = Tensor::new(vec![2, 2], vec![1.0; 4]).unwrap();

    let error = attention_decode_multi_query(&queries, &keys, &values).unwrap_err();

    assert_eq!(
        error,
        ReferenceError::NonFiniteInput {
            operation: "matmul",
            index: 1,
        }
    );
}

#[test]
fn multi_query_attention_propagates_non_finite_keys() {
    let queries = Tensor::new(vec![2, 2], vec![1.0; 4]).unwrap();
    let keys = Tensor::new(vec![2, 2], vec![1.0, f32::NAN, 1.0, 1.0]).unwrap();
    let values = Tensor::new(vec![2, 2], vec![1.0; 4]).unwrap();

    let error = attention_decode_multi_query(&queries, &keys, &values).unwrap_err();

    assert_eq!(
        error,
        ReferenceError::NonFiniteInput {
            operation: "transpose",
            index: 1,
        }
    );
}

#[test]
fn multi_query_attention_rejects_non_rank_two_keys() {
    let queries = Tensor::new(vec![2, 2], vec![1.0; 4]).unwrap();
    let keys = Tensor::new(vec![4], vec![1.0; 4]).unwrap();
    let values = Tensor::new(vec![2, 2], vec![1.0; 4]).unwrap();

    let error = attention_decode_multi_query(&queries, &keys, &values).unwrap_err();

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
fn multi_query_attention_rejects_non_rank_two_values() {
    let queries = Tensor::new(vec![2, 2], vec![1.0; 4]).unwrap();
    let keys = Tensor::new(vec![2, 2], vec![1.0; 4]).unwrap();
    let values = Tensor::new(vec![2, 1, 2], vec![1.0; 4]).unwrap();

    let error = attention_decode_multi_query(&queries, &keys, &values).unwrap_err();

    assert_eq!(
        error,
        ReferenceError::RankMismatch {
            operation: "matmul",
            expected: 2,
            actual: 3,
        }
    );
}
