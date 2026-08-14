from __future__ import annotations

from fractions import Fraction

import pytest

from forgellm_governance.exact_distribution import ExactDistribution
from forgellm_governance.speculative_exhaustive import (
    ExactSequenceLaw,
    LawNormalizationError,
    enumerate_target_law,
)
from forgellm_governance.speculative_models import FiniteTableModel, ModelTableError


def d(*pairs: tuple[int, int | Fraction]) -> ExactDistribution:
    return ExactDistribution.from_pairs(pairs)


def test_sequence_law_aggregates_duplicates_and_requires_unit_mass() -> None:
    law = ExactSequenceLaw.from_pairs(
        [
            ((0,), Fraction(1, 4)),
            ((0,), Fraction(1, 4)),
            ((1,), Fraction(1, 2)),
        ]
    )
    assert law.probabilities == (
        ((0,), Fraction(1, 2)),
        ((1,), Fraction(1, 2)),
    )
    assert law.probability((9,)) == 0
    with pytest.raises(LawNormalizationError, match="sum exactly to one"):
        ExactSequenceLaw.from_pairs([((0,), Fraction(1, 2))])
    with pytest.raises(LawNormalizationError, match="non-negative"):
        ExactSequenceLaw.from_pairs(
            [((0,), Fraction(2)), ((1,), Fraction(-1))]
        )
    with pytest.raises(LawNormalizationError, match="tuple"):
        ExactSequenceLaw.from_pairs(
            [([0], Fraction(1))]  # type: ignore[list-item]
        )


def test_zero_budget_target_law_is_empty_point_mass_without_lookup() -> None:
    class NoLookup:
        def distribution(self, prefix: tuple[int, ...]) -> ExactDistribution:
            raise AssertionError(prefix)

    assert enumerate_target_law(NoLookup(), (), 0, 9) == ExactSequenceLaw.from_pairs(
        [((), 1)]
    )


def test_target_law_branches_exactly_and_stops_at_budget() -> None:
    model = FiniteTableModel.from_pairs(
        [
            ((), d((0, 1), (1, 1))),
            ((0,), d((2, 1))),
            ((1,), d((3, 1))),
        ]
    )
    law = enumerate_target_law(model, (), 2, 9)
    assert law.probabilities == (
        ((0, 2), Fraction(1, 2)),
        ((1, 3), Fraction(1, 2)),
    )
    assert law.total_mass == 1


def test_target_law_stops_at_eos_and_does_not_require_eos_prefix_table() -> None:
    eos = 9
    model = FiniteTableModel.from_pairs(
        [
            ((), d((0, 1), (eos, 1))),
            ((0,), d((eos, 1))),
        ]
    )
    law = enumerate_target_law(model, (), 4, eos)
    assert law.probabilities == (
        ((0, eos), Fraction(1, 2)),
        ((eos,), Fraction(1, 2)),
    )


def test_non_empty_prefix_conditions_target_without_reemitting_it() -> None:
    model = FiniteTableModel.from_pairs(
        [
            ((7,), d((0, 1), (1, 1))),
            ((7, 0), d((2, 1))),
            ((7, 1), d((3, 1))),
        ]
    )
    law = enumerate_target_law(model, (7,), 2, 9)
    assert law.probabilities == (
        ((0, 2), Fraction(1, 2)),
        ((1, 3), Fraction(1, 2)),
    )


def test_invalid_budget_and_missing_prefix_fail_closed() -> None:
    model = FiniteTableModel.from_pairs([((), d((0, 1)))])
    with pytest.raises(LawNormalizationError, match="budget"):
        enumerate_target_law(model, (), True, 9)  # type: ignore[arg-type]
    with pytest.raises(ModelTableError, match="missing distribution"):
        enumerate_target_law(model, (0,), 1, 9)
