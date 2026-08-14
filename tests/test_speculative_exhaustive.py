from __future__ import annotations

from fractions import Fraction
from itertools import product

import pytest

from forgellm_governance.exact_distribution import ExactDistribution
from forgellm_governance.speculative_exhaustive import (
    ExactSequenceLaw,
    LawNormalizationError,
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
    depth = max(budget, 1)
    return FiniteTableModel.from_pairs(
        (tuple(prefix), distribution) for length in range(depth) for prefix in product(alphabet, repeat=length)
    )


def eos_prefix_model(
    distribution: ExactDistribution,
    *,
    non_eos_tokens: tuple[int, ...],
    budget: int,
) -> FiniteTableModel:
    depth = max(budget, 1)
    return FiniteTableModel.from_pairs(
        (tuple(prefix), distribution) for length in range(depth) for prefix in product(non_eos_tokens, repeat=length)
    )


def prefix_dependent_model(
    root: ExactDistribution,
    by_last_token: dict[int, ExactDistribution],
    *,
    alphabet: tuple[int, ...],
    budget: int,
) -> FiniteTableModel:
    depth = max(budget, 1)
    rows: list[tuple[tuple[int, ...], ExactDistribution]] = []
    for length in range(depth):
        for raw_prefix in product(alphabet, repeat=length):
            prefix = tuple(raw_prefix)
            distribution = root if not prefix else by_last_token[prefix[-1]]
            rows.append((prefix, distribution))
    return FiniteTableModel.from_pairs(rows)


def assert_laws_equal(left: ExactSequenceLaw, right: ExactSequenceLaw) -> None:
    assert left.probabilities == right.probabilities
    assert left.total_mass == right.total_mass == 1


MODEL_FAMILIES = (
    (
        d((0, 1), (1, 2)),
        d((0, 1), (1, 2)),
        (0, 1),
    ),
    (
        d((0, 1), (1, 3)),
        d((0, 3), (2, 1)),
        (0, 1, 2),
    ),
    (
        d((0, 1)),
        d((2, 1)),
        (0, 2),
    ),
    (
        d((0, 2), (1, 3)),
        d((0, 9), (1, 1)),
        (0, 1),
    ),
)


@pytest.mark.parametrize("budget", range(5))
@pytest.mark.parametrize("draft_length", (1, 2, 3))
@pytest.mark.parametrize(
    ("target_distribution", "draft_distribution", "alphabet"),
    MODEL_FAMILIES,
)
def test_required_finite_model_grid_matches_target_law_exactly(
    budget: int,
    draft_length: int,
    target_distribution: ExactDistribution,
    draft_distribution: ExactDistribution,
    alphabet: tuple[int, ...],
) -> None:
    target = full_prefix_model(
        target_distribution,
        alphabet=alphabet,
        budget=budget,
    )
    draft = full_prefix_model(
        draft_distribution,
        alphabet=alphabet,
        budget=budget,
    )
    assert_laws_equal(
        enumerate_target_law(target, (), budget, 9),
        enumerate_speculative_law(
            target,
            draft,
            (),
            budget,
            draft_length,
            9,
        ),
    )


@pytest.mark.parametrize("budget", range(5))
@pytest.mark.parametrize("draft_length", (1, 2, 3))
def test_prefix_dependent_target_and_draft_match_exactly(
    budget: int,
    draft_length: int,
) -> None:
    alphabet = (0, 1, 2)
    target = prefix_dependent_model(
        d((0, 1), (1, 2)),
        {
            0: d((0, 3), (1, 1)),
            1: d((0, 1), (1, 3)),
            2: d((0, 1), (1, 1)),
        },
        alphabet=alphabet,
        budget=budget,
    )
    draft = prefix_dependent_model(
        d((0, 3), (2, 1)),
        {
            0: d((1, 1), (2, 3)),
            1: d((0, 5), (2, 1)),
            2: d((0, 1), (1, 1)),
        },
        alphabet=alphabet,
        budget=budget,
    )
    if budget > 1:
        assert target.distribution(()) != target.distribution((0,))
        assert draft.distribution(()) != draft.distribution((0,))
    assert_laws_equal(
        enumerate_target_law(target, (), budget, 9),
        enumerate_speculative_law(
            target,
            draft,
            (),
            budget,
            draft_length,
            9,
        ),
    )


@pytest.mark.parametrize("budget", range(5))
@pytest.mark.parametrize("draft_length", (1, 2, 3))
def test_eos_model_grid_matches_and_never_emits_after_eos(
    budget: int,
    draft_length: int,
) -> None:
    eos = 9
    target = eos_prefix_model(
        d((0, 1), (eos, 1)),
        non_eos_tokens=(0,),
        budget=budget,
    )
    draft = eos_prefix_model(
        d((0, 3), (eos, 1)),
        non_eos_tokens=(0,),
        budget=budget,
    )
    baseline = enumerate_target_law(target, (), budget, eos)
    speculative = enumerate_speculative_law(
        target,
        draft,
        (),
        budget,
        draft_length,
        eos,
    )
    assert_laws_equal(baseline, speculative)
    for sequence, mass in speculative.probabilities:
        assert mass > 0
        if eos in sequence:
            assert sequence[-1] == eos


def test_sharply_perturbed_drafts_change_branches_not_final_law() -> None:
    budget = 4
    target_distribution = d((0, 2), (1, 3))
    target = full_prefix_model(
        target_distribution,
        alphabet=(0, 1, 2),
        budget=budget,
    )
    draft_a = full_prefix_model(
        d((0, 99), (1, 1)),
        alphabet=(0, 1, 2),
        budget=budget,
    )
    draft_b = full_prefix_model(
        d((0, 1), (2, 99)),
        alphabet=(0, 1, 2),
        budget=budget,
    )
    baseline = enumerate_target_law(target, (), budget, 9)
    law_a = enumerate_speculative_law(target, draft_a, (), budget, 3, 9)
    law_b = enumerate_speculative_law(target, draft_b, (), budget, 3, 9)
    assert_laws_equal(baseline, law_a)
    assert_laws_equal(baseline, law_b)
    assert law_a == law_b


def test_round_law_has_unit_mass_and_respects_budget() -> None:
    target = full_prefix_model(
        d((0, 1), (1, 1)),
        alphabet=(0, 1, 2),
        budget=3,
    )
    draft = full_prefix_model(
        d((0, 3), (2, 1)),
        alphabet=(0, 1, 2),
        budget=3,
    )
    law = enumerate_speculative_round_law(target, draft, (), 3, 2, 9)
    assert law.total_mass == 1
    assert all(1 <= len(sequence) <= 3 for sequence, _ in law.probabilities)


def test_non_empty_prefix_is_conditioning_context_not_reemitted_output() -> None:
    distribution = d((0, 1), (1, 1))
    model = FiniteTableModel.from_pairs(
        [
            ((7,), distribution),
            ((7, 0), distribution),
            ((7, 1), distribution),
        ]
    )
    baseline = enumerate_target_law(model, (7,), 2, 9)
    speculative = enumerate_speculative_law(model, model, (7,), 2, 2, 9)
    assert_laws_equal(baseline, speculative)
    assert all(not sequence or sequence[0] != 7 for sequence, _ in baseline.probabilities)


def test_zero_budget_speculative_law_uses_no_model_lookup() -> None:
    class NoLookup:
        def distribution(self, prefix: tuple[int, ...]) -> ExactDistribution:
            raise AssertionError(prefix)

    expected = ExactSequenceLaw.from_pairs([((), 1)])
    assert (
        enumerate_speculative_law(
            NoLookup(),
            NoLookup(),
            (),
            0,
            2,
            9,
        )
        == expected
    )


def test_invalid_budget_draft_length_and_eos_fail_closed() -> None:
    model = FiniteTableModel.from_pairs([((), d((0, 1)))])
    with pytest.raises(LawNormalizationError, match="budget"):
        enumerate_speculative_law(
            model,
            model,
            (),
            True,  # type: ignore[arg-type]
            1,
            9,
        )
    with pytest.raises(LawNormalizationError, match="draft_length"):
        enumerate_speculative_law(model, model, (), 1, 0, 9)
    with pytest.raises(LawNormalizationError, match="eos_token_id"):
        enumerate_speculative_law(
            model,
            model,
            (),
            1,
            1,
            True,  # type: ignore[arg-type]
        )
