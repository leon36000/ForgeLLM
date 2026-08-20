use super::{ReferenceError, try_vec_with_capacity};

#[test]
fn capacity_overflow_maps_to_typed_allocation_error() {
    let error = try_vec_with_capacity::<f32>(usize::MAX, "allocation_probe").unwrap_err();

    assert_eq!(
        error,
        ReferenceError::AllocationFailed {
            operation: "allocation_probe",
            requested_elements: usize::MAX,
        }
    );
}

#[test]
fn embedding_gather_checks_invalid_id_before_output_capacity() {
    // This deliberately bypasses Tensor::new's storage invariant to exercise the
    // operation-order seam without allocating a huge embedding table. With the
    // old ordering, three rows of this width overflowed before the invalid ID was
    // reported; the public constructor cannot represent that table in memory.
    let table = super::Tensor {
        shape: vec![3, usize::MAX / 2 + 1],
        data: Vec::new(),
    };

    let error = super::embedding_gather(&table, &[3, 3, 3]).unwrap_err();

    assert_eq!(
        error,
        super::ReferenceError::IndexOutOfBounds {
            operation: "embedding_gather",
            index: 3,
            upper_bound: 3,
        }
    );
}
