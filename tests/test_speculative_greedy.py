from __future__ import annotations

from fractions import Fraction
from itertools import product

import pytest

from forgellm_governance.exact_distribution import ExactDistribution
from forgellm_governance.speculative_greedy import (
    GreedyDecodeError,
    greedy_speculative_decode,
    greedy_target_decode,
)
from forgellm_governance.speculative_models import FiniteTableModel


def d(*pairs: tuple[int, int | Fraction]) -> ExactDistribution:
    return ExactDistribution.from_pairs(pairs)


def full_model(
    distribution: ExactDistribution,
    alphabet: tuple[int, ...],
    budget: int,
) -> FiniteTableModel:
    return FiniteTableModel.from_pairs(
        (tuple(prefix), distribution)
        for length in range(max(budget, 1))
        for prefix in product(alphabet, repeat=length)
    )


def test_greedy_target_uses_smallest_token_on_tie() -> None:
    model = full_model(d((5, 1), (2, 1)), (2, 5), 3)
    assert greedy_target_decode(model, (), 3, 9) == (2, 2, 2)


@pytest.mark.parametrize("draft_length", [1, 2, 3, 4])
@pytest.mark.parametrize("budget", [0, 1, 2, 3, 4])
def test_identical_target_and_draft_match_greedy_baseline(
    draft_length: int,
    budget: int,
) -> None:
    distribution = d((0, 1), (1, 3))
    model = full_model(distribution, (0, 1), budget)
    assert greedy_speculative_decode(
        model,
        model,
        (),
        budget,
        draft_length,
        9,
    ) == greedy_target_decode(model, (), budget, 9)


def test_mismatch_discards_suffix_and_emits_target_token() -> None:
    target = full_model(d((0, 3), (1, 1)), (0, 1, 2), 4)
    draft = full_model(d((2, 4), (0, 1)), (0, 1, 2), 4)
    baseline = greedy_target_decode(target, (), 4, 9)
    speculative = greedy_speculative_decode(target, draft, (), 4, 3, 9)
    assert baseline == speculative == (0, 0, 0, 0)


def test_fully_matching_block_gets_target_bonus_when_budget_remains() -> None:
    target = FiniteTableModel.from_pairs(
        [
            ((), d((0, 1))),
            ((0,), d((1, 1))),
            ((0, 1), d((2, 1))),
        ]
    )
    draft = FiniteTableModel.from_pairs(
        [((), d((0, 1))), ((0,), d((1, 1)))]
    )
    assert greedy_speculative_decode(target, draft, (), 3, 2, 9) == (0, 1, 2)


def test_eos_stops_without_suffix_or_bonus() -> None:
    eos = 9
    target = FiniteTableModel.from_pairs([((), d((eos, 1)))])
    draft = FiniteTableModel.from_pairs([((), d((eos, 1)))])
    assert greedy_target_decode(target, (), 4, eos) == (eos,)
    assert greedy_speculative_decode(target, draft, (), 4, 4, eos) == (eos,)


def test_mismatch_target_eos_has_precedence() -> None:
    eos = 9
    target = FiniteTableModel.from_pairs([((), d((eos, 1)))])
    draft = FiniteTableModel.from_pairs(
        [((), d((0, 1))), ((0,), d((1, 1)))]
    )
    assert greedy_speculative_decode(target, draft, (), 4, 2, eos) == (eos,)


def test_non_empty_prefix_conditions_output_but_is_not_reemitted() -> None:
    target = FiniteTableModel.from_pairs(
        [((7,), d((0, 1))), ((7, 0), d((1, 1)))]
    )
    draft = FiniteTableModel.from_pairs([((7,), d((0, 1)))])
    assert greedy_target_decode(target, (7,), 2, 9) == (0, 1)
    assert greedy_speculative_decode(target, draft, (7,), 2, 1, 9) == (0, 1)


@pytest.mark.parametrize(
    "call",
    [
        lambda model: greedy_target_decode(model, (), True, 9),
        lambda model: greedy_target_decode(model, (), -1, 9),
        lambda model: greedy_speculative_decode(model, model, (), 1, 0, 9),
        lambda model: greedy_speculative_decode(model, model, (), 1, True, 9),
        lambda model: greedy_speculative_decode(model, model, (), True, 1, 9),
        lambda model: greedy_speculative_decode(model, model, (), 1, 1, True),
    ],
)
def test_invalid_greedy_arguments_fail_closed(call) -> None:
    model = FiniteTableModel.from_pairs([((), d((0, 1)))])
    with pytest.raises(GreedyDecodeError):
        call(model)
