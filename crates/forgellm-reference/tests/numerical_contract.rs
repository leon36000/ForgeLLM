use forgellm_reference::{SOFTMAX_ABS_TOLERANCE, softmax};

fn assert_close(actual: f32, expected: f32) {
    let delta = (actual - expected).abs();
    assert!(
        delta <= SOFTMAX_ABS_TOLERANCE,
        "actual={actual:?} expected={expected:?} delta={delta:?} tolerance={SOFTMAX_ABS_TOLERANCE:?}"
    );
}

#[test]
fn softmax_contract_uses_explicit_absolute_tolerance() {
    assert_eq!(SOFTMAX_ABS_TOLERANCE, 1.0e-6);

    let probabilities = softmax(&[1000.0, 1001.0, 1002.0]).unwrap();
    assert_close(probabilities[0], 0.090_030_57);
    assert_close(probabilities[1], 0.244_728_48);
    assert_close(probabilities[2], 0.665_240_94);
    assert_close(probabilities.iter().sum(), 1.0);
}

#[test]
fn softmax_preserves_a_subnormal_tail_within_the_reference_contract() {
    let probabilities = softmax(&[0.0, -100.0]).unwrap();

    assert_eq!(probabilities.len(), 2);
    assert!(probabilities[0] <= 1.0);
    assert!(probabilities[1] > 0.0);
    assert!(probabilities[1] < f32::MIN_POSITIVE);
    assert_close(probabilities.iter().sum(), 1.0);
}

#[test]
fn softmax_extreme_shift_remains_finite_and_bounded() {
    let probabilities = softmax(&[f32::MAX, f32::MAX, -f32::MAX]).unwrap();

    assert_close(probabilities[0], 0.5);
    assert_close(probabilities[1], 0.5);
    assert_eq!(probabilities[2], 0.0);
    assert!(
        probabilities
            .iter()
            .all(|probability| probability.is_finite())
    );
}
