"""Exhaustive exact sequence-law enumerators for finite speculative decoding."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from fractions import Fraction

from .exact_distribution import (
    DistributionValidationError,
    validate_non_negative_int,
    validate_positive_int,
    validate_prefix,
    validate_token_id,
)
from .speculative_decoding import (
    DistributionModel,
    ProposalRecord,
    acceptance_probability,
)


class LawNormalizationError(ValueError):
    """Raised when an exact finite output law is malformed or cannot normalize."""


def _coerce_mass(value: object) -> Fraction:
    if isinstance(value, bool) or not isinstance(value, (int, Fraction)):
        raise LawNormalizationError("sequence mass must be an int or Fraction")
    mass = Fraction(value)
    if mass < 0:
        raise LawNormalizationError("sequence mass must be non-negative")
    return mass


@dataclass(frozen=True, slots=True)
class ExactSequenceLaw:
    """Canonical finite probability law over emitted token tuples."""

    probabilities: tuple[tuple[tuple[int, ...], Fraction], ...]

    def __post_init__(self) -> None:
        if not isinstance(self.probabilities, tuple) or not self.probabilities:
            raise LawNormalizationError("sequence law support cannot be empty")
        sequences: list[tuple[int, ...]] = []
        total = Fraction(0)
        for entry in self.probabilities:
            if not isinstance(entry, tuple) or len(entry) != 2:
                raise LawNormalizationError("stored law entries must be sequence/mass pairs")
            sequence, mass = entry
            try:
                validated = validate_prefix(sequence, name="sequence")
            except DistributionValidationError as exc:
                raise LawNormalizationError(str(exc)) from exc
            if validated != sequence:
                raise LawNormalizationError("stored sequence must be a tuple")
            if not isinstance(mass, Fraction) or mass <= 0:
                raise LawNormalizationError("stored sequence mass must be a positive Fraction")
            sequences.append(sequence)
            total += mass
        if sequences != sorted(sequences) or len(sequences) != len(set(sequences)):
            raise LawNormalizationError("stored sequences must be unique and sorted")
        if total != 1:
            raise LawNormalizationError("sequence law probabilities must sum exactly to one")

    @classmethod
    def from_pairs(
        cls,
        pairs: Iterable[tuple[tuple[int, ...], int | Fraction]],
    ) -> ExactSequenceLaw:
        aggregate: dict[tuple[int, ...], Fraction] = {}
        count = 0
        for raw in pairs:
            count += 1
            if not isinstance(raw, tuple) or len(raw) != 2:
                raise LawNormalizationError("law entries must be sequence/mass pairs")
            raw_sequence, raw_mass = raw
            try:
                sequence = validate_prefix(raw_sequence, name="sequence")
            except DistributionValidationError as exc:
                raise LawNormalizationError(str(exc)) from exc
            mass = _coerce_mass(raw_mass)
            if mass:
                aggregate[sequence] = aggregate.get(sequence, Fraction(0)) + mass
        if count == 0 or not aggregate:
            raise LawNormalizationError("sequence law requires positive support")
        total = sum(aggregate.values(), Fraction(0))
        if total != 1:
            raise LawNormalizationError(f"sequence law probabilities must sum exactly to one; observed {total}")
        return cls(tuple(sorted(aggregate.items(), key=lambda item: item[0])))

    @property
    def total_mass(self) -> Fraction:
        return sum((mass for _, mass in self.probabilities), Fraction(0))

    def probability(self, sequence: tuple[int, ...]) -> Fraction:
        try:
            validated = validate_prefix(sequence, name="sequence")
        except DistributionValidationError as exc:
            raise LawNormalizationError(str(exc)) from exc
        for item_sequence, mass in self.probabilities:
            if item_sequence == validated:
                return mass
        return Fraction(0)


def _validate_common(
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
        raise LawNormalizationError(str(exc)) from exc


def enumerate_target_law(
    target: DistributionModel,
    prefix: tuple[int, ...],
    budget: int,
    eos_token_id: int,
) -> ExactSequenceLaw:
    """Enumerate the exact autoregressive target output law."""

    validated_prefix, validated_budget, eos = _validate_common(
        prefix,
        budget,
        eos_token_id,
    )
    memo: dict[tuple[tuple[int, ...], int], ExactSequenceLaw] = {}

    def rec(current_prefix: tuple[int, ...], remaining: int) -> ExactSequenceLaw:
        key = (current_prefix, remaining)
        if key in memo:
            return memo[key]
        if remaining == 0 or (current_prefix and current_prefix[-1] == eos):
            law = ExactSequenceLaw.from_pairs([((), 1)])
            memo[key] = law
            return law
        distribution = target.distribution(current_prefix)
        outcomes: list[tuple[tuple[int, ...], Fraction]] = []
        for token, mass in distribution.probabilities:
            if token == eos or remaining == 1:
                outcomes.append(((token,), mass))
                continue
            suffix_law = rec(current_prefix + (token,), remaining - 1)
            for suffix, suffix_mass in suffix_law.probabilities:
                outcomes.append(((token,) + suffix, mass * suffix_mass))
        law = ExactSequenceLaw.from_pairs(outcomes)
        memo[key] = law
        return law

    return rec(validated_prefix, validated_budget)


def _enumerate_proposal_paths(
    draft: DistributionModel,
    prefix: tuple[int, ...],
    limit: int,
    eos_token_id: int,
) -> tuple[tuple[tuple[ProposalRecord, ...], Fraction], ...]:
    if limit <= 0:
        return (((), Fraction(1)),)
    distribution = draft.distribution(prefix)
    paths: list[tuple[tuple[ProposalRecord, ...], Fraction]] = []
    for token, mass in distribution.probabilities:
        record = ProposalRecord(prefix, distribution, token)
        if token == eos_token_id or limit == 1:
            paths.append(((record,), mass))
            continue
        for suffix_records, suffix_mass in _enumerate_proposal_paths(
            draft,
            prefix + (token,),
            limit - 1,
            eos_token_id,
        ):
            paths.append(((record,) + suffix_records, mass * suffix_mass))
    return tuple(paths)


def _verification_outcomes(
    target: DistributionModel,
    prefix: tuple[int, ...],
    records: tuple[ProposalRecord, ...],
    remaining_budget: int,
    eos_token_id: int,
) -> tuple[tuple[tuple[int, ...], Fraction], ...]:
    emitted_accepted: tuple[int, ...] = ()
    verification_prefix = prefix
    continuation_mass = Fraction(1)
    outcomes: list[tuple[tuple[int, ...], Fraction]] = []

    for record in records:
        if continuation_mass == 0:
            break
        if record.prefix != verification_prefix:
            raise LawNormalizationError("proposal path prefix is not consecutive")
        target_distribution = target.distribution(verification_prefix)
        alpha = acceptance_probability(
            target_distribution,
            record.distribution,
            record.token,
        )
        rejection_mass = continuation_mass * (1 - alpha)
        if rejection_mass:
            residual = target_distribution.positive_residual(record.distribution)
            for correction, correction_mass in residual.probabilities:
                outcomes.append(
                    (
                        emitted_accepted + (correction,),
                        rejection_mass * correction_mass,
                    )
                )
        continuation_mass *= alpha
        if continuation_mass == 0:
            break
        emitted_accepted = emitted_accepted + (record.token,)
        verification_prefix = verification_prefix + (record.token,)
        if record.token == eos_token_id:
            outcomes.append((emitted_accepted, continuation_mass))
            continuation_mass = Fraction(0)
            break

    if continuation_mass:
        if len(emitted_accepted) >= remaining_budget:
            outcomes.append((emitted_accepted, continuation_mass))
        else:
            bonus_distribution = target.distribution(verification_prefix)
            for bonus, bonus_mass in bonus_distribution.probabilities:
                outcomes.append(
                    (
                        emitted_accepted + (bonus,),
                        continuation_mass * bonus_mass,
                    )
                )
    total = sum((mass for _, mass in outcomes), Fraction(0))
    if total != 1:
        raise LawNormalizationError(f"conditional verification outcomes must sum exactly to one; observed {total}")
    return tuple(outcomes)


def enumerate_speculative_round_law(
    target: DistributionModel,
    draft: DistributionModel,
    prefix: tuple[int, ...],
    budget: int,
    draft_length: int,
    eos_token_id: int,
) -> ExactSequenceLaw:
    """Enumerate one exact speculative round, including proposal randomness."""

    validated_prefix, validated_budget, eos = _validate_common(
        prefix,
        budget,
        eos_token_id,
    )
    try:
        validated_draft_length = validate_positive_int(
            draft_length,
            name="draft_length",
        )
    except DistributionValidationError as exc:
        raise LawNormalizationError(str(exc)) from exc
    if validated_budget == 0 or (validated_prefix and validated_prefix[-1] == eos):
        return ExactSequenceLaw.from_pairs([((), 1)])

    proposal_limit = min(validated_draft_length, validated_budget)
    outcomes: list[tuple[tuple[int, ...], Fraction]] = []
    for records, proposal_mass in _enumerate_proposal_paths(
        draft,
        validated_prefix,
        proposal_limit,
        eos,
    ):
        for emitted, conditional_mass in _verification_outcomes(
            target,
            validated_prefix,
            records,
            validated_budget,
            eos,
        ):
            outcomes.append((emitted, proposal_mass * conditional_mass))
    return ExactSequenceLaw.from_pairs(outcomes)


def enumerate_speculative_law(
    target: DistributionModel,
    draft: DistributionModel,
    prefix: tuple[int, ...],
    budget: int,
    draft_length: int,
    eos_token_id: int,
) -> ExactSequenceLaw:
    """Enumerate the exact multi-round speculative output law."""

    validated_prefix, validated_budget, eos = _validate_common(
        prefix,
        budget,
        eos_token_id,
    )
    try:
        validated_draft_length = validate_positive_int(
            draft_length,
            name="draft_length",
        )
    except DistributionValidationError as exc:
        raise LawNormalizationError(str(exc)) from exc
    memo: dict[tuple[tuple[int, ...], int], ExactSequenceLaw] = {}

    def rec(current_prefix: tuple[int, ...], remaining: int) -> ExactSequenceLaw:
        key = (current_prefix, remaining)
        if key in memo:
            return memo[key]
        if remaining == 0 or (current_prefix and current_prefix[-1] == eos):
            law = ExactSequenceLaw.from_pairs([((), 1)])
            memo[key] = law
            return law
        round_law = enumerate_speculative_round_law(
            target,
            draft,
            current_prefix,
            remaining,
            validated_draft_length,
            eos,
        )
        outcomes: list[tuple[tuple[int, ...], Fraction]] = []
        for emitted, round_mass in round_law.probabilities:
            if not emitted:
                raise LawNormalizationError("positive-budget speculative round emitted no token")
            if emitted[-1] == eos or len(emitted) >= remaining:
                outcomes.append((emitted, round_mass))
                continue
            suffix_law = rec(
                current_prefix + emitted,
                remaining - len(emitted),
            )
            for suffix, suffix_mass in suffix_law.probabilities:
                outcomes.append((emitted + suffix, round_mass * suffix_mass))
        law = ExactSequenceLaw.from_pairs(outcomes)
        memo[key] = law
        return law

    return rec(validated_prefix, validated_budget)
