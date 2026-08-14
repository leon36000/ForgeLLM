from __future__ import annotations

import json
from fractions import Fraction

from forgellm_governance.exact_distribution import RandomTape
from forgellm_governance.speculative_decoding import SampledRoundRequest, SampledRoundResult
from forgellm_governance.speculative_state import DecoderState
from forgellm_governance.speculative_trace import (
    TRACE_SCHEMA_VERSION,
    build_trace_document,
    canonical_trace_bytes,
    canonical_trace_document,
    fraction_document,
)


def sample_result() -> SampledRoundResult:
    return SampledRoundResult(
        prefix=(7,),
        proposed_tokens=(0, 1),
        accepted_count=1,
        emitted_tokens=(0, 5),
        acceptance_probabilities=(Fraction(2, 3), Fraction(0)),
        correction_kind="residual",
        termination="rejection",
        tape=RandomTape((4, 2, 9), cursor=2),
        remaining_budget=4,
        eos_token_id=9,
    )


def sample_state() -> DecoderState:
    return DecoderState(
        output_tokens=(7, 0, 5),
        target_materialized=(7, 0),
        draft_materialized=(7, 0),
        pending_token=5,
        sampler_tokens=(7, 0, 5),
        grammar_tokens=(7, 0, 5),
        finished=False,
    )


def test_fraction_document_is_exact_and_canonical() -> None:
    assert fraction_document(Fraction(2, 3)) == {"denominator": 3, "numerator": 2}


def test_canonical_trace_document_is_the_planned_public_name() -> None:
    request = SampledRoundRequest((7,), 2, 4, 9)
    assert canonical_trace_document(request, sample_result(), sample_state()) == build_trace_document(
        request,
        sample_result(),
        sample_state(),
    )


def test_trace_document_contains_exact_request_result_tape_and_optional_state() -> None:
    request = SampledRoundRequest((7,), 2, 4, 9)
    document = canonical_trace_document(request, sample_result(), sample_state())
    assert document["schema_version"] == TRACE_SCHEMA_VERSION
    assert document["evidence_boundary"] == "finite_exact_reference"
    assert document["request"] == {
        "draft_length": 2,
        "eos_token_id": 9,
        "prefix": [7],
        "remaining_budget": 4,
    }
    assert document["result"]["acceptance_probabilities"] == [
        {"denominator": 3, "numerator": 2},
        {"denominator": 1, "numerator": 0},
    ]
    assert document["result"]["tape"] == {"cursor": 2, "draws": [4, 2, 9]}
    assert document["state"]["pending_token"] == 5


def test_canonical_trace_bytes_are_byte_identical_and_have_no_environment_fields() -> None:
    request = SampledRoundRequest((7,), 2, 4, 9)
    first = canonical_trace_bytes(request, sample_result(), sample_state())
    second = canonical_trace_bytes(request, sample_result(), sample_state())
    assert first == second
    assert first.endswith(b"\n")
    decoded = first.decode("utf-8").lower()
    for forbidden in (
        "timestamp",
        "hostname",
        "absolute_path",
        "cwd",
        "platform",
        "processor",
        "nvidia",
        "amd",
        "intel",
    ):
        assert forbidden not in decoded
    assert json.loads(first) == canonical_trace_document(
        request,
        sample_result(),
        sample_state(),
    )


def test_trace_without_state_uses_explicit_null() -> None:
    request = SampledRoundRequest((7,), 2, 4, 9)
    assert canonical_trace_document(request, sample_result())["state"] is None
