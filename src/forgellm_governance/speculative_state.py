"""Transactional speculative-decoding state with exact commit, rollback, and pending sync."""

from __future__ import annotations

from dataclasses import dataclass

from .exact_distribution import DistributionValidationError, validate_prefix, validate_token_id
from .speculative_decoding import SampledRoundResult


class StateInvariantError(ValueError):
    """Raised when speculative decoder state or a transaction violates invariants."""


@dataclass(frozen=True, slots=True)
class DecoderState:
    output_tokens: tuple[int, ...]
    target_materialized: tuple[int, ...]
    draft_materialized: tuple[int, ...]
    pending_token: int | None
    sampler_tokens: tuple[int, ...]
    grammar_tokens: tuple[int, ...]
    finished: bool

    def __post_init__(self) -> None:
        try:
            validate_prefix(self.output_tokens, name="output_tokens")
            validate_prefix(self.target_materialized, name="target_materialized")
            validate_prefix(self.draft_materialized, name="draft_materialized")
            validate_prefix(self.sampler_tokens, name="sampler_tokens")
            validate_prefix(self.grammar_tokens, name="grammar_tokens")
            if self.pending_token is not None:
                validate_token_id(self.pending_token, name="pending_token")
        except DistributionValidationError as exc:
            raise StateInvariantError(str(exc)) from exc
        if not isinstance(self.finished, bool):
            raise StateInvariantError("finished must be a boolean")
        if self.target_materialized != self.draft_materialized:
            raise StateInvariantError("target and draft materialized prefixes must be identical")
        if self.sampler_tokens != self.output_tokens or self.grammar_tokens != self.output_tokens:
            raise StateInvariantError("sampler and grammar state must equal emitted output")
        expected_output = self.target_materialized
        if self.pending_token is not None:
            expected_output = expected_output + (self.pending_token,)
        if self.output_tokens != expected_output:
            raise StateInvariantError(
                "output must equal materialized prefix plus at most one pending token"
            )

    @property
    def materialized_prefix(self) -> tuple[int, ...]:
        return self.target_materialized


@dataclass(frozen=True, slots=True)
class RoundTransaction:
    original: DecoderState
    proposed_tokens: tuple[int, ...]
    closed: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.original, DecoderState):
            raise StateInvariantError("transaction original must be a DecoderState")
        try:
            validate_prefix(self.proposed_tokens, name="proposed_tokens")
        except DistributionValidationError as exc:
            raise StateInvariantError(str(exc)) from exc
        if not isinstance(self.closed, bool):
            raise StateInvariantError("closed must be a boolean")


def begin_round(state: DecoderState, proposed_tokens: tuple[int, ...]) -> RoundTransaction:
    if state.finished:
        raise StateInvariantError("cannot begin a round from finished state")
    if state.pending_token is not None:
        raise StateInvariantError("cannot begin a round while a correction token is pending")
    try:
        proposals = validate_prefix(proposed_tokens, name="proposed_tokens")
    except DistributionValidationError as exc:
        raise StateInvariantError(str(exc)) from exc
    if not proposals:
        raise StateInvariantError("round must contain at least one proposed token")
    return RoundTransaction(original=state, proposed_tokens=proposals, closed=False)


def _require_open(transaction: RoundTransaction) -> None:
    if transaction.closed:
        raise StateInvariantError("round transaction is already closed")


def commit_round(
    transaction: RoundTransaction,
    result: SampledRoundResult,
) -> tuple[DecoderState, RoundTransaction]:
    _require_open(transaction)
    original = transaction.original
    if result.prefix != original.output_tokens:
        raise StateInvariantError("round result prefix does not equal transaction original output")
    if result.proposed_tokens != transaction.proposed_tokens:
        raise StateInvariantError("round result proposed tokens do not equal transaction proposals")

    accepted_prefix = result.proposed_tokens[: result.accepted_count]
    materialized = original.target_materialized + accepted_prefix
    pending: int | None = None
    if result.correction_kind in {"residual", "bonus"}:
        if not result.emitted_tokens:
            raise StateInvariantError("correction branch must emit a final token")
        pending = result.emitted_tokens[-1]
    else:
        expected_materialized = original.target_materialized + result.emitted_tokens
        if materialized != expected_materialized:
            raise StateInvariantError("non-correction branch must materialize every emitted token")

    output = original.output_tokens + result.emitted_tokens
    finished = bool(output and output[-1] == result.eos_token_id)
    committed = DecoderState(
        output_tokens=output,
        target_materialized=materialized,
        draft_materialized=materialized,
        pending_token=pending,
        sampler_tokens=output,
        grammar_tokens=output,
        finished=finished,
    )
    return committed, RoundTransaction(
        original=transaction.original,
        proposed_tokens=transaction.proposed_tokens,
        closed=True,
    )


def cancel_round(transaction: RoundTransaction) -> tuple[DecoderState, RoundTransaction]:
    _require_open(transaction)
    return transaction.original, RoundTransaction(
        original=transaction.original,
        proposed_tokens=transaction.proposed_tokens,
        closed=True,
    )


def synchronize_pending(state: DecoderState) -> DecoderState:
    if state.pending_token is None:
        return state
    materialized = state.target_materialized + (state.pending_token,)
    return DecoderState(
        output_tokens=state.output_tokens,
        target_materialized=materialized,
        draft_materialized=materialized,
        pending_token=None,
        sampler_tokens=state.sampler_tokens,
        grammar_tokens=state.grammar_tokens,
        finished=state.finished,
    )
