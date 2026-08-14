from __future__ import annotations

from fractions import Fraction
from itertools import product

import pytest

from forgellm_governance.exact_distribution import ExactDistribution
from forgellm_governance.exact_enumeration import (
    ExactSequenceLaw,
    SequenceLawError,
    enumerate_speculative_law,
    enumerate_speculative_round_law,
    enumerate_target_law,
)
from forgellm_governance.speculative_models import FiniteTableModel


def d(*pairs: tuple[int, int | Fraction]) -> ExactDistribution:
    return ExactDistribution.from_pairs(pairs)


def full_prefix_model(
    distribution: ExactDistribution,
    *,
    alphabet: tuple[int, ...],
    budget: int,
) -> FiniteTableModel:
    rows: list[tuple[tuple[int, ...], ExactDistribution]] = []
    for length in range(budget):
        for prefix in product(alphabet, repeat=length):
            rows.append((tuple(prefix), distribution))
    return FiniteTableModel.from_pairs(rows)


def eos_prefix_model(
    distribution: ExactDistribution,
    *,
    non_eos_tokens: tuple[int, ...],
    budget: int,
) -> FiniteTableModel:
    rows: list[tuple[tuple[int, ...], ExactDistribution]] = []
    for length in range(budget):
        for prefix in product(non_eos_tokens, repeat=length):
            rows.append((tuple(prefix), distribution))
    return FiniteTableModel.from_pairs(rows)


def assert_laws_equal(left: ExactSequenceLaw, right: ExactSequenceLaw) -> None:
    assert left.probabilities == right.probabilities
    assert left.total_mass == right.total_mass == 1


def test_sequence_law_aggregates_duplicates_and_requires_unit_mass() -> None:
    law = ExactSequenceLaw.from_pairs(
        [((0,), Fraction(1, 4)), ((0,), Fraction(1, 4)), ((1,), Fraction(1, 2))]
    )
    assert law.probabilities == (((0,), Fraction(1, 2)), ((1,), Fraction(1, 2)))
    assert law.probability((9,)) == 0
    with pytest.raises(SequenceLawError, match="sum exactly to one"):
        ExactSequenceLaw.from_pairs([((0,), Fraction(1, 2))])
    with pytest.raises(SequenceLawError, match="non-negative"):
        ExactSequenceLaw.from_pairs([((0,), Fraction(2)), ((1,), Fraction(-1))])
    with pytest.raises(SequenceLawError, match="tuple"):
        ExactSequenceLaw.from_pairs([([0], Fraction(1))])  # type: ignore[list-item]


def test_zero_budget_laws_are_point_mass_on_empty_sequence_without_lookup() -> None:
    class NoLookup:
        def distribution(self, prefix: tuple[int, ...]) -> ExactDistribution:
            raise AssertionError(prefix)

    expected = ExactSequenceLaw.from_pairs([((), 1)])
    assert enumerate_target_law(NoLookup(), (), 0, 9) == expected  # type: ignore[arg-type]
    assert enumerate_speculative_law(NoLookup(), NoLookup(), (), 2, 0, 9) == expected  # type: ignore[arg-type]


@pytest.mark.parametrize("draft_length", [1, 2, 3, 4])
@pytest.mark.parametrize("budget", [1, 2, 3, 4])
def test_identical_stochastic_target_and_draft_have_exact_same_sequence_law(
    draft_length: int,
    budget: int,
) -> None:
    distribution = d((0, 1), (1, 2))
    model = full_prefix_model(distribution, alphabet=(0, 1), budget=budget)
    assert_laws_equal(
        enumerate_target_law(model, (), budget, 9),
        enumerate_speculative_law(model, model, (), draft_length, budget, 9),
    )


@pytest.mark.parametrize("draft_length", [1, 2, 3, 4])
def test_disjoint_support_draft_still_matches_target_law(draft_length: int) -> None:
    budget = 4
    target = full_prefix_model(d((0, 1)), alphabet=(0, 1), budget=budget)
    draft = full_prefix_model(d((1, 1)), alphabet=(0, 1), budget=budget)
    assert_laws_equal(
        enumerate_target_law(target, (), budget, 9),
        enumerate_speculative_law(target, draft, (), draft_length, budget, 9),
    )


@pytest.mark.parametrize("draft_length", [1, 2, 3])
def test_partial_overlap_and_target_zero_proposals_match_exactly(draft_length: int) -> None:
    budget = 3
    target_distribution = d((0, 1), (1, 3))
    proposal_distribution = d((0, 3), (2, 1))
    target = full_prefix_model(target_distribution, alphabet=(0, 1, 2), budget=budget)
    draft = full_prefix_model(proposal_distribution, alphabet=(0, 1, 2), budget=budget)
    assert_laws_equal(
        enumerate_target_law(target, (), budget, 9),
        enumerate_speculative_law(target, draft, (), draft_length, budget, 9),
    )


def test_eos_early_stop_matches_target_and_never_emits_after_eos() -> None:
    eos = 9
    budget = 4
    target = eos_prefix_model(d((0, 1), (eos, 1)), non_eos_tokens=(0,), budget=budget)
    draft = eos_prefix_model(d((0, 3), (eos, 1)), non_eos_tokens=(0,), budget=budget)
    baseline = enumerate_target_law(target, (), budget, eos)
    speculative = enumerate_speculative_law(target, draft, (), 3, budget, eos)
    assert_laws_equal(baseline, speculative)
    for sequence, mass in speculative.probabilities:
        assert mass > 0
        if eos in sequence:
            assert sequence[-1] == eos


def test_round_law_has_unit_mass_and_respects_budget() -> None:
    target = full_prefix_model(d((0, 1), (1, 1)), alphabet=(0, 1, 2), budget=3)
    draft = full_prefix_model(d((0, 3), (2, 1)), alphabet=(0, 1, 2), budget=3)
    law = enumerate_speculative_round_law(target, draft, (), 2, 3, 9)
    assert law.total_mass == 1
    assert all(1 <= len(sequence) <= 3 for sequence, _ in law.probabilities)


def test_non_empty_prefix_is_preserved_as_conditioning_but_not_reemitted() -> None:
    distribution = d((0, 1), (1, 1))
    rows = [((7,), distribution), ((7, 0), distribution), ((7, 1), distribution)]
    model = FiniteTableModel.from_pairs(rows)
    baseline = enumerate_target_law(model, (7,), 2, 9)
    speculative = enumerate_speculative_law(model, model, (7,), 2, 2, 9)
    assert_laws_equal(baseline, speculative)
    assert all(not sequence or sequence[0] != 7 for sequence, _ in baseline.probabilities)


def test_invalid_budget_draft_length_and_eos_fail_closed() -> None:
    model = FiniteTableModel.from_pairs([((), d((0, 1)))])
    with pytest.raises(SequenceLawError, match="budget"):
        enumerate_target_law(model, (), True, 9)  # type: ignore[arg-type]
    with pytest.raises(SequenceLawError, match="draft_length"):
        enumerate_speculative_law(model, model, (), 0, 1, 9)
    with pytest.raises(SequenceLawError, match="eos_token_id"):
        enumerate_speculative_law(model, model, (), 1, 1, True)  # type: ignore[arg-type]
