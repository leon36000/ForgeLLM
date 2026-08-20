use forgellm_reference::{
    ReferenceError, Tensor, elementwise_add, elementwise_mul, embedding_gather, reshape,
};

#[test]
fn reshape_preserves_contiguous_data_order() {
    let tensor = Tensor::new(vec![2, 3], vec![1.0, 2.0, 3.0, 4.0, 5.0, 6.0]).unwrap();

    let reshaped = reshape(tensor, vec![3, 2]).unwrap();

    assert_eq!(reshaped.shape(), &[3, 2]);
    assert_eq!(reshaped.data(), &[1.0, 2.0, 3.0, 4.0, 5.0, 6.0]);
}

#[test]
fn reshape_rejects_element_count_mismatch() {
    let tensor = Tensor::new(vec![2, 3], vec![1.0; 6]).unwrap();

    let error = reshape(tensor, vec![2, 2]).unwrap_err();

    assert_eq!(
        error,
        ReferenceError::DataLengthMismatch {
            expected: 4,
            actual: 6,
        }
    );
}

#[test]
fn reshape_rejects_zero_dimension() {
    let tensor = Tensor::new(vec![2, 3], vec![1.0; 6]).unwrap();

    let error = reshape(tensor, vec![2, 0, 3]).unwrap_err();

    assert_eq!(error, ReferenceError::ZeroDimension { axis: 1 });
}

#[test]
fn reshape_rejects_empty_shape() {
    let tensor = Tensor::new(vec![2, 3], vec![1.0; 6]).unwrap();

    let error = reshape(tensor, vec![]).unwrap_err();

    assert_eq!(error, ReferenceError::EmptyShape);
}

#[test]
fn elementwise_add_matches_exact_shape_golden_result() {
    let lhs = Tensor::new(vec![2, 2], vec![1.0, -2.0, 3.5, 4.0]).unwrap();
    let rhs = Tensor::new(vec![2, 2], vec![4.0, 2.0, 0.5, -1.0]).unwrap();

    let output = elementwise_add(&lhs, &rhs).unwrap();

    assert_eq!(output.shape(), &[2, 2]);
    assert_eq!(output.data(), &[5.0, 0.0, 4.0, 3.0]);
}

#[test]
fn elementwise_add_rejects_same_length_different_shape() {
    let lhs = Tensor::new(vec![2, 2], vec![1.0; 4]).unwrap();
    let rhs = Tensor::new(vec![4], vec![1.0; 4]).unwrap();

    let error = elementwise_add(&lhs, &rhs).unwrap_err();

    assert_eq!(
        error,
        ReferenceError::ShapeMismatch {
            operation: "elementwise_add",
        }
    );
}

#[test]
fn elementwise_add_rejects_non_finite_input() {
    let lhs = Tensor::new(vec![2], vec![1.0, f32::NAN]).unwrap();
    let rhs = Tensor::new(vec![2], vec![1.0, 2.0]).unwrap();

    let error = elementwise_add(&lhs, &rhs).unwrap_err();

    assert_eq!(
        error,
        ReferenceError::NonFiniteInput {
            operation: "elementwise_add",
            index: 1,
        }
    );
}

#[test]
fn elementwise_add_rejects_non_finite_result() {
    let lhs = Tensor::new(vec![1], vec![f32::MAX]).unwrap();
    let rhs = Tensor::new(vec![1], vec![f32::MAX]).unwrap();

    let error = elementwise_add(&lhs, &rhs).unwrap_err();

    assert_eq!(
        error,
        ReferenceError::NonFiniteResult {
            operation: "elementwise_add",
            index: 0,
        }
    );
}

#[test]
fn elementwise_mul_matches_exact_shape_golden_result() {
    let lhs = Tensor::new(vec![2, 2], vec![1.0, -2.0, 3.0, 4.0]).unwrap();
    let rhs = Tensor::new(vec![2, 2], vec![4.0, 2.0, 0.5, -1.0]).unwrap();

    let output = elementwise_mul(&lhs, &rhs).unwrap();

    assert_eq!(output.shape(), &[2, 2]);
    assert_eq!(output.data(), &[4.0, -4.0, 1.5, -4.0]);
}

#[test]
fn elementwise_mul_rejects_non_finite_input() {
    let lhs = Tensor::new(vec![2], vec![1.0, f32::NAN]).unwrap();
    let rhs = Tensor::new(vec![2], vec![1.0, 2.0]).unwrap();

    let error = elementwise_mul(&lhs, &rhs).unwrap_err();

    assert_eq!(
        error,
        ReferenceError::NonFiniteInput {
            operation: "elementwise_mul",
            index: 1,
        }
    );
}

#[test]
fn elementwise_mul_rejects_same_length_different_shape() {
    let lhs = Tensor::new(vec![2, 2], vec![1.0; 4]).unwrap();
    let rhs = Tensor::new(vec![4], vec![1.0; 4]).unwrap();

    let error = elementwise_mul(&lhs, &rhs).unwrap_err();

    assert_eq!(
        error,
        ReferenceError::ShapeMismatch {
            operation: "elementwise_mul",
        }
    );
}

#[test]
fn elementwise_mul_rejects_non_finite_result() {
    let lhs = Tensor::new(vec![1], vec![f32::MAX]).unwrap();
    let rhs = Tensor::new(vec![1], vec![2.0]).unwrap();

    let error = elementwise_mul(&lhs, &rhs).unwrap_err();

    assert_eq!(
        error,
        ReferenceError::NonFiniteResult {
            operation: "elementwise_mul",
            index: 0,
        }
    );
}

#[test]
fn embedding_gather_preserves_token_order_and_repetition() {
    let table = Tensor::new(vec![3, 2], vec![10.0, 11.0, 20.0, 21.0, 30.0, 31.0]).unwrap();

    let output = embedding_gather(&table, &[2, 0, 2]).unwrap();

    assert_eq!(output.shape(), &[3, 2]);
    assert_eq!(output.data(), &[30.0, 31.0, 10.0, 11.0, 30.0, 31.0]);
}

#[test]
fn embedding_gather_rejects_non_rank_two_table() {
    let table = Tensor::new(vec![3], vec![1.0, 2.0, 3.0]).unwrap();

    let error = embedding_gather(&table, &[0]).unwrap_err();

    assert_eq!(
        error,
        ReferenceError::RankMismatch {
            operation: "embedding_gather",
            expected: 2,
            actual: 1,
        }
    );
}

#[test]
fn embedding_gather_rejects_empty_token_ids() {
    let table = Tensor::new(vec![2, 2], vec![1.0, 2.0, 3.0, 4.0]).unwrap();

    let error = embedding_gather(&table, &[]).unwrap_err();

    assert_eq!(
        error,
        ReferenceError::EmptyInput {
            operation: "embedding_gather",
        }
    );
}

#[test]
fn embedding_gather_rejects_out_of_range_token_id() {
    let table = Tensor::new(vec![3, 2], vec![1.0; 6]).unwrap();

    let error = embedding_gather(&table, &[1, 3]).unwrap_err();

    assert_eq!(
        error,
        ReferenceError::IndexOutOfBounds {
            operation: "embedding_gather",
            index: 3,
            upper_bound: 3,
        }
    );
}

#[test]
fn embedding_gather_rejects_non_finite_table() {
    let table = Tensor::new(vec![2, 2], vec![1.0, 2.0, f32::INFINITY, 4.0]).unwrap();

    let error = embedding_gather(&table, &[0]).unwrap_err();

    assert_eq!(
        error,
        ReferenceError::NonFiniteInput {
            operation: "embedding_gather",
            index: 2,
        }
    );
}
