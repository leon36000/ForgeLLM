use forgellm_reference::{ReferenceError, Tensor, argmax, matmul, rms_norm, softmax};

fn assert_close(actual: f32, expected: f32, tolerance: f32) {
    let delta = (actual - expected).abs();
    assert!(
        delta <= tolerance,
        "actual={actual:?} expected={expected:?} delta={delta:?} tolerance={tolerance:?}"
    );
}

#[test]
fn tensor_rejects_empty_shape() {
    let error = Tensor::new(vec![], vec![]).unwrap_err();
    assert_eq!(error, ReferenceError::EmptyShape);
}

#[test]
fn tensor_rejects_zero_dimension() {
    let error = Tensor::new(vec![2, 0, 3], vec![]).unwrap_err();
    assert_eq!(error, ReferenceError::ZeroDimension { axis: 1 });
}

#[test]
fn tensor_rejects_element_count_overflow() {
    let error = Tensor::new(vec![usize::MAX, 2], vec![]).unwrap_err();
    assert_eq!(error, ReferenceError::ElementCountOverflow);
}

#[test]
fn tensor_rejects_data_length_mismatch() {
    let error = Tensor::new(vec![2, 2], vec![1.0, 2.0, 3.0]).unwrap_err();
    assert_eq!(
        error,
        ReferenceError::DataLengthMismatch {
            expected: 4,
            actual: 3,
        }
    );
}

#[test]
fn matmul_matches_golden_row_major_result() {
    let lhs = Tensor::new(vec![2, 3], vec![1.0, 2.0, 3.0, 4.0, 5.0, 6.0]).unwrap();
    let rhs = Tensor::new(vec![3, 2], vec![7.0, 8.0, 9.0, 10.0, 11.0, 12.0]).unwrap();

    let output = matmul(&lhs, &rhs).unwrap();

    assert_eq!(output.shape(), &[2, 2]);
    assert_eq!(output.data(), &[58.0, 64.0, 139.0, 154.0]);
}

#[test]
fn matmul_rejects_non_rank_two_tensor() {
    let lhs = Tensor::new(vec![2, 1, 2], vec![1.0, 2.0, 3.0, 4.0]).unwrap();
    let rhs = Tensor::new(vec![2, 2], vec![1.0, 0.0, 0.0, 1.0]).unwrap();

    let error = matmul(&lhs, &rhs).unwrap_err();
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
fn matmul_rejects_inner_dimension_mismatch() {
    let lhs = Tensor::new(vec![2, 3], vec![1.0; 6]).unwrap();
    let rhs = Tensor::new(vec![4, 2], vec![1.0; 8]).unwrap();

    let error = matmul(&lhs, &rhs).unwrap_err();
    assert_eq!(
        error,
        ReferenceError::DimensionMismatch {
            operation: "matmul",
            left: 3,
            right: 4,
        }
    );
}

#[test]
fn matmul_rejects_non_finite_input() {
    let lhs = Tensor::new(vec![1, 2], vec![1.0, f32::NAN]).unwrap();
    let rhs = Tensor::new(vec![2, 1], vec![1.0, 2.0]).unwrap();

    let error = matmul(&lhs, &rhs).unwrap_err();
    assert_eq!(
        error,
        ReferenceError::NonFiniteInput {
            operation: "matmul",
            index: 1,
        }
    );
}

#[test]
fn softmax_is_stable_for_large_logits() {
    let probabilities = softmax(&[1000.0, 1001.0, 1002.0]).unwrap();

    assert_close(probabilities[0], 0.090_030_57, 1.0e-6);
    assert_close(probabilities[1], 0.244_728_48, 1.0e-6);
    assert_close(probabilities[2], 0.665_240_94, 1.0e-6);
    assert_close(probabilities.iter().sum(), 1.0, 1.0e-6);
}

#[test]
fn softmax_is_shift_invariant_within_reference_budget() {
    let a = softmax(&[-2.0, 0.0, 4.0]).unwrap();
    let b = softmax(&[998.0, 1000.0, 1004.0]).unwrap();

    for (left, right) in a.into_iter().zip(b) {
        assert_close(left, right, 1.0e-6);
    }
}

#[test]
fn softmax_rejects_empty_input() {
    let error = softmax(&[]).unwrap_err();
    assert_eq!(
        error,
        ReferenceError::EmptyInput {
            operation: "softmax"
        }
    );
}

#[test]
fn softmax_rejects_non_finite_input() {
    let error = softmax(&[0.0, f32::INFINITY]).unwrap_err();
    assert_eq!(
        error,
        ReferenceError::NonFiniteInput {
            operation: "softmax",
            index: 1,
        }
    );
}

#[test]
fn rms_norm_matches_golden_values() {
    let output = rms_norm(&[3.0, 4.0], &[2.0, 0.5], 1.0e-6).unwrap();

    assert_close(output[0], 1.697_056_2, 1.0e-6);
    assert_close(output[1], 0.565_685_4, 1.0e-6);
}

#[test]
fn rms_norm_rejects_weight_length_mismatch() {
    let error = rms_norm(&[1.0, 2.0], &[1.0], 1.0e-6).unwrap_err();
    assert_eq!(
        error,
        ReferenceError::LengthMismatch {
            operation: "rms_norm",
            left: 2,
            right: 1,
        }
    );
}

#[test]
fn rms_norm_rejects_invalid_epsilon() {
    for epsilon in [0.0, -1.0, f32::INFINITY, f32::NAN] {
        let error = rms_norm(&[1.0], &[1.0], epsilon).unwrap_err();
        assert_eq!(error, ReferenceError::InvalidEpsilon);
    }
}

#[test]
fn rms_norm_rejects_non_finite_input_and_weight() {
    let input_error = rms_norm(&[1.0, f32::NEG_INFINITY], &[1.0, 1.0], 1.0e-6).unwrap_err();
    assert_eq!(
        input_error,
        ReferenceError::NonFiniteInput {
            operation: "rms_norm",
            index: 1,
        }
    );

    let weight_error = rms_norm(&[1.0, 2.0], &[1.0, f32::NAN], 1.0e-6).unwrap_err();
    assert_eq!(
        weight_error,
        ReferenceError::NonFiniteWeight {
            operation: "rms_norm",
            index: 1,
        }
    );
}

#[test]
fn argmax_uses_first_index_for_ties() {
    assert_eq!(argmax(&[1.0, 3.0, 3.0, 2.0]).unwrap(), 1);
}

#[test]
fn argmax_rejects_empty_input() {
    let error = argmax(&[]).unwrap_err();
    assert_eq!(
        error,
        ReferenceError::EmptyInput {
            operation: "argmax"
        }
    );
}

#[test]
fn argmax_rejects_non_finite_input() {
    let error = argmax(&[1.0, f32::NAN]).unwrap_err();
    assert_eq!(
        error,
        ReferenceError::NonFiniteInput {
            operation: "argmax",
            index: 1,
        }
    );
}
