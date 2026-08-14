"""Deterministic greedy target and speculative reference oracles."""

from __future__ import annotations

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
        current_prefix = current_prefix + (token,)
        if token == eos:
            break
    return tuple(emitted)


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
    emitted: list[int] = []
    if current_prefix and current_prefix[-1] == eos:
        return ()

    while remaining:
        proposal_limit = min(block_length, remaining)
        proposals: list[int] = []
        proposal_prefix = current_prefix
        for _ in range(proposal_limit):
            token = draft.distribution(proposal_prefix).argmax()
            proposals.append(token)
            proposal_prefix = proposal_prefix + (token,)
            if token == eos:
                break

        accepted_all = True
        for proposed in proposals:
            target_token = target.distribution(current_prefix).argmax()
            if proposed != target_token:
                emitted.append(target_token)
                remaining -= 1
                current_prefix = current_prefix + (target_token,)
                accepted_all = False
                if target_token == eos:
                    return tuple(emitted)
                break
            emitted.append(proposed)
            remaining -= 1
            current_prefix = current_prefix + (proposed,)
            if proposed == eos:
                return tuple(emitted)
            if remaining == 0:
                return tuple(emitted)

        if not accepted_all:
            continue

        if remaining:
            bonus = target.distribution(current_prefix).argmax()
            emitted.append(bonus)
            remaining -= 1
            current_prefix = current_prefix + (bonus,)
            if bonus == eos:
                return tuple(emitted)

    return tuple(emitted)
