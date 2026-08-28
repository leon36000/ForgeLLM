use forgellm_reference::{ReferenceError, Tensor, dense_decode_single_token};

fn oracle_dense_decoder_token(
    embedding_table: &[f32],
    token_id: usize,
    rms_weights: &[f32],
    epsilon: f32,
    projection: &[f32],
    output_width: usize,
) -> usize {
    let hidden_width = rms_weights.len();
    let row_start = token_id * hidden_width;
    let row = &embedding_table[row_start..row_start + hidden_width];
    let mean_square = row
        .iter()
        .map(|value| f64::from(*value) * f64::from(*value))
        .sum::<f64>()
        / hidden_width as f64;
    let scale = (mean_square + f64::from(epsilon)).sqrt();

    let mut best_index = 0;
    let mut best_logit = f64::NEG_INFINITY;
    for output in 0..output_width {
        let logit = row
            .iter()
            .zip(rms_weights)
            .enumerate()
            .map(|(hidden, (value, weight))| {
                f64::from(*value) / scale
                    * f64::from(*weight)
                    * f64::from(projection[hidden * output_width + output])
            })
            .sum::<f64>();
        if logit > best_logit {
            best_logit = logit;
            best_index = output;
        }
    }
    best_index
}

#[test]
fn dense_decoder_matches_independent_golden_oracle() {
    let embedding_table = Tensor::new(vec![3, 2], vec![1.0, 2.0, 2.0, 1.0, -1.0, 3.0]).unwrap();
    let projection = Tensor::new(vec![2, 3], vec![1.0, 0.0, -1.0, 0.0, 1.0, 1.0]).unwrap();
    let weights = [1.0, 1.0];

    for token_id in 0..3 {
        let expected = oracle_dense_decoder_token(
            embedding_table.data(),
            token_id,
            &weights,
            1.0e-6,
            projection.data(),
            3,
        );
        let actual =
            dense_decode_single_token(&embedding_table, token_id, &weights, 1.0e-6, &projection)
                .unwrap();

        assert_eq!(actual, expected, "token_id={token_id}");
    }
}

#[test]
fn dense_decoder_uses_first_index_for_equal_logits() {
    let embedding_table = Tensor::new(vec![1, 2], vec![2.0, -1.0]).unwrap();
    let projection = Tensor::new(vec![2, 3], vec![0.0; 6]).unwrap();

    let token =
        dense_decode_single_token(&embedding_table, 0, &[1.0, 1.0], 1.0e-6, &projection).unwrap();

    assert_eq!(token, 0);
}

#[test]
fn dense_decoder_propagates_invalid_token_id() {
    let embedding_table = Tensor::new(vec![2, 2], vec![1.0; 4]).unwrap();
    let projection = Tensor::new(vec![2, 2], vec![1.0; 4]).unwrap();

    let error = dense_decode_single_token(&embedding_table, 2, &[1.0, 1.0], 1.0e-6, &projection)
        .unwrap_err();

    assert_eq!(
        error,
        ReferenceError::IndexOutOfBounds {
            operation: "embedding_gather",
            index: 2,
            upper_bound: 2,
        }
    );
}

#[test]
fn dense_decoder_propagates_projection_width_error() {
    let embedding_table = Tensor::new(vec![2, 2], vec![1.0; 4]).unwrap();
    let projection = Tensor::new(vec![3, 2], vec![1.0; 6]).unwrap();

    let error = dense_decode_single_token(&embedding_table, 0, &[1.0, 1.0], 1.0e-6, &projection)
        .unwrap_err();

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
fn dense_decoder_propagates_rms_validation_errors() {
    let embedding_table = Tensor::new(vec![1, 2], vec![1.0, 2.0]).unwrap();
    let projection = Tensor::new(vec![2, 2], vec![1.0; 4]).unwrap();

    let weight_error =
        dense_decode_single_token(&embedding_table, 0, &[1.0, f32::NAN], 1.0e-6, &projection)
            .unwrap_err();
    assert_eq!(
        weight_error,
        ReferenceError::NonFiniteWeight {
            operation: "rms_norm",
            index: 1,
        }
    );

    let epsilon_error =
        dense_decode_single_token(&embedding_table, 0, &[1.0, 1.0], 0.0, &projection).unwrap_err();
    assert_eq!(epsilon_error, ReferenceError::InvalidEpsilon);
}
