"""Canonical environment-free traces for exact speculative reference rounds."""

from __future__ import annotations

import json
from fractions import Fraction
from typing import Any

from .speculative_decoding import SampledRoundRequest, SampledRoundResult
from .speculative_state import DecoderState

TRACE_SCHEMA_VERSION = "1.0"


def fraction_document(value: Fraction) -> dict[str, int]:
    if not isinstance(value, Fraction):
        raise TypeError("value must be a Fraction")
    return {"denominator": value.denominator, "numerator": value.numerator}


def _state_document(state: DecoderState) -> dict[str, Any]:
    return {
        "draft_materialized": list(state.draft_materialized),
        "finished": state.finished,
        "grammar_tokens": list(state.grammar_tokens),
        "output_tokens": list(state.output_tokens),
        "pending_token": state.pending_token,
        "sampler_tokens": list(state.sampler_tokens),
        "target_materialized": list(state.target_materialized),
    }


def canonical_trace_document(
    request: SampledRoundRequest,
    result: SampledRoundResult,
    state: DecoderState | None = None,
) -> dict[str, Any]:
    """Build a deterministic finite-reference trace with no host-specific metadata."""

    if result.prefix != request.prefix:
        raise ValueError("result prefix must equal request prefix")
    if result.remaining_budget != request.remaining_budget:
        raise ValueError("result remaining_budget must equal request remaining_budget")
    if result.eos_token_id != request.eos_token_id:
        raise ValueError("result eos_token_id must equal request eos_token_id")
    return {
        "evidence_boundary": "finite_exact_reference",
        "request": {
            "draft_length": request.draft_length,
            "eos_token_id": request.eos_token_id,
            "prefix": list(request.prefix),
            "remaining_budget": request.remaining_budget,
        },
        "result": {
            "acceptance_probabilities": [fraction_document(value) for value in result.acceptance_probabilities],
            "accepted_count": result.accepted_count,
            "correction_kind": result.correction_kind,
            "emitted_tokens": list(result.emitted_tokens),
            "prefix": list(result.prefix),
            "proposed_tokens": list(result.proposed_tokens),
            "remaining_budget": result.remaining_budget,
            "tape": {"cursor": result.tape.cursor, "draws": list(result.tape.draws)},
            "termination": result.termination,
        },
        "schema_version": TRACE_SCHEMA_VERSION,
        "state": None if state is None else _state_document(state),
    }


def build_trace_document(
    request: SampledRoundRequest,
    result: SampledRoundResult,
    state: DecoderState | None = None,
) -> dict[str, Any]:
    """Compatibility wrapper for the canonical trace document API."""

    return canonical_trace_document(request, result, state)


def canonical_trace_bytes(
    request: SampledRoundRequest,
    result: SampledRoundResult,
    state: DecoderState | None = None,
) -> bytes:
    document = canonical_trace_document(request, result, state)
    return (json.dumps(document, indent=2, sort_keys=True, separators=(",", ": ")) + "\n").encode("utf-8")
