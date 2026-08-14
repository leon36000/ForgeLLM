"""Deterministic greedy target and speculative reference oracles."""

from __future__ import annotations

from dataclasses import dataclass

from .exact_distribution import (
    DistributionValidationError,
    validate_non_negative_int,
    validate_positive_int,
    validate_prefix,
    validate_token_id,
)
from .speculative_decoding import DistributionModel


class GreedyDecodeError(ValueError):
    """Raised when a greedy reference decode request is invalid."""


def _validated(
    prefix: tuple[int, ...],
    budget: int,
    eos_token_id: int,
) -> tuple[tuple[int, ...], int, int]:
    try:
        return (
            validate_prefix(prefix),
            validate_non_negative_int(budget, name="budget"),
            validate_token_id(eos_token_id, name="eos_token_id"),
        )
    except DistributionValidationError as exc:
        raise GreedyDecodeError(str(exc)) from exc


def greedy_target_decode(
    target: DistributionModel,
    prefix: tuple[int, ...],
    budget: int,
    eos_token_id: int,
) -> tuple[int, ...]:
    """Decode greedily from the target using stable smallest-token tie breaking."""

    current_prefix, remaining, eos = _validated(prefix, budget, eos_token_id)
    emitted: list[int] = []
    if current_prefix and current_prefix[-1] == eos:
        return ()
    while remaining:
        token = target.distribution(current_prefix).argmax()
        emitted.append(token)
        remaining -= 1
        current_prefix += (token,)
        if token == eos:
            break
    return tuple(emitted)


@dataclass(frozen=True, slots=True)
class _GreedyRoundState:
    emitted_tokens: tuple[int, ...]
    prefix: tuple[int, ...]
    remaining_budget: int
    all_accepted: bool
    stop: bool


def _generate_greedy_proposals(
    draft: DistributionModel,
    prefix: tuple[int, ...],
    limit: int,
    eos_token_id: int,
) -> tuple[int, ...]:
    proposals: list[int] = []
    proposal_prefix = prefix
    for _ in range(limit):
        token = draft.distribution(proposal_prefix).argmax()
        proposals.append(token)
        proposal_prefix += (token,)
        if token == eos_token_id:
            break
    return tuple(proposals)


def _mismatch_state(
    emitted_tokens: tuple[int, ...],
    prefix: tuple[int, ...],
    remaining_budget: int,
    target_token: int,
    eos_token_id: int,
) -> _GreedyRoundState:
    emitted = emitted_tokens + (target_token,)
    updated_prefix = prefix + (target_token,)
    return _GreedyRoundState(
        emitted,
        updated_prefix,
        remaining_budget - 1,
        all_accepted=False,
        stop=target_token == eos_token_id,
    )


def _accepted_state(
    emitted_tokens: tuple[int, ...],
    prefix: tuple[int, ...],
    remaining_budget: int,
    proposed_token: int,
    eos_token_id: int,
) -> _GreedyRoundState:
    emitted = emitted_tokens + (proposed_token,)
    updated_prefix = prefix + (proposed_token,)
    updated_budget = remaining_budget - 1
    return _GreedyRoundState(
        emitted,
        updated_prefix,
        updated_budget,
        all_accepted=True,
        stop=proposed_token == eos_token_id or updated_budget == 0,
    )


def _verify_greedy_proposals(
    target: DistributionModel,
    prefix: tuple[int, ...],
    remaining_budget: int,
    proposals: tuple[int, ...],
    eos_token_id: int,
) -> _GreedyRoundState:
    emitted: tuple[int, ...] = ()
    current_prefix = prefix
    current_budget = remaining_budget
    for proposed in proposals:
        target_token = target.distribution(current_prefix).argmax()
        if proposed != target_token:
            return _mismatch_state(
                emitted,
                current_prefix,
                current_budget,
                target_token,
                eos_token_id,
            )
        accepted = _accepted_state(
            emitted,
            current_prefix,
            current_budget,
            proposed,
            eos_token_id,
        )
        emitted = accepted.emitted_tokens
        current_prefix = accepted.prefix
        current_budget = accepted.remaining_budget
        if accepted.stop:
            return accepted
    return _GreedyRoundState(
        emitted,
        current_prefix,
        current_budget,
        all_accepted=True,
        stop=False,
    )


def _append_greedy_bonus(
    target: DistributionModel,
    state: _GreedyRoundState,
    eos_token_id: int,
) -> _GreedyRoundState:
    bonus = target.distribution(state.prefix).argmax()
    emitted = state.emitted_tokens + (bonus,)
    prefix = state.prefix + (bonus,)
    remaining = state.remaining_budget - 1
    return _GreedyRoundState(
        emitted,
        prefix,
        remaining,
        all_accepted=True,
        stop=bonus == eos_token_id or remaining == 0,
    )


def _run_greedy_round(
    target: DistributionModel,
    draft: DistributionModel,
    prefix: tuple[int, ...],
    remaining_budget: int,
    draft_length: int,
    eos_token_id: int,
) -> _GreedyRoundState:
    proposals = _generate_greedy_proposals(
        draft,
        prefix,
        min(draft_length, remaining_budget),
        eos_token_id,
    )
    verified = _verify_greedy_proposals(
        target,
        prefix,
        remaining_budget,
        proposals,
        eos_token_id,
    )
    if verified.stop or not verified.all_accepted:
        return verified
    return _append_greedy_bonus(target, verified, eos_token_id)


def greedy_speculative_decode(
    target: DistributionModel,
    draft: DistributionModel,
    prefix: tuple[int, ...],
    budget: int,
    draft_length: int,
    eos_token_id: int,
) -> tuple[int, ...]:
    """Decode with exact greedy speculative verification and target bonus tokens."""

    current_prefix, remaining, eos = _validated(prefix, budget, eos_token_id)
    try:
        block_length = validate_positive_int(draft_length, name="draft_length")
    except DistributionValidationError as exc:
        raise GreedyDecodeError(str(exc)) from exc
    if current_prefix and current_prefix[-1] == eos:
        return ()

    emitted: tuple[int, ...] = ()
    while remaining:
        round_state = _run_greedy_round(
            target,
            draft,
            current_prefix,
            remaining,
            block_length,
            eos,
        )
        emitted += round_state.emitted_tokens
        current_prefix = round_state.prefix
        remaining = round_state.remaining_budget
        if round_state.stop:
            break
    return emitted
