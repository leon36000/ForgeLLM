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
