from __future__ import annotations

from dataclasses import FrozenInstanceError
from fractions import Fraction

import pytest

from forgellm_governance.exact_distribution import (
    DistributionValidationError,
    ExactDistribution,
    RandomSourceError,
    RandomTape,
    UnreachableResidualError,
)


def test_distribution_normalizes_removes_zero_and_sorts() -> None:
    distribution = ExactDistribution.from_pairs([(3, 1), (1, 3), (2, 0)])
    assert distribution.probabilities == (
        (1, Fraction(3, 4)),
        (3, Fraction(1, 4)),
    )
    assert distribution.support() == (1, 3)
    assert distribution.probability(2) == 0
    with pytest.raises(FrozenInstanceError):
        distribution.probabilities = ()  # type: ignore[misc]


@pytest.mark.parametrize(
    ("pairs", "message"),
    [
        ([], "requires at least one"),
        ([(True, 1)], "non-boolean integer"),
        ([(-1, 1)], "non-negative"),
        ([(0, True)], "int or Fraction"),
        ([(0, -1)], "non-negative"),
        ([(0, 0)], "total weight must be positive"),
        ([(0, 0), (0, 1)], "duplicate token"),
    ],
)
def test_invalid_distribution_fails_closed(pairs: object, message: str) -> None:
    with pytest.raises(DistributionValidationError, match=message):
        ExactDistribution.from_pairs(pairs)  # type: ignore[arg-type]


def test_argmax_uses_smallest_token_on_tie() -> None:
    assert ExactDistribution.from_pairs([(9, 1), (2, 1)]).argmax() == 2


def test_random_tape_is_immutable_and_validated() -> None:
    tape = RandomTape((1, 1))
    value, advanced = tape.draw(2)
    assert value == 1
    assert tape.cursor == 0
    assert advanced.cursor == 1

    with pytest.raises(RandomSourceError, match="outside randbelow"):
        advanced.draw(1)
    with pytest.raises(RandomSourceError, match="exhausted"):
        RandomTape((), 0).draw(1)
    with pytest.raises(RandomSourceError, match="positive"):
        tape.draw(0)
    with pytest.raises(RandomSourceError, match="non-boolean integer"):
        tape.draw(True)  # type: ignore[arg-type]
    with pytest.raises(RandomSourceError, match="non-boolean integer"):
        RandomTape((True,))  # type: ignore[arg-type]
    with pytest.raises(RandomSourceError, match="non-negative"):
        RandomTape((-1,))


def test_exact_sampling_uses_common_denominator_and_advances_once() -> None:
    distribution = ExactDistribution.from_pairs([(0, Fraction(1, 2)), (1, Fraction(1, 3)), (2, Fraction(1, 6))])
    assert distribution.sample(RandomTape((0,)))[0] == 0
    assert distribution.sample(RandomTape((2,)))[0] == 0
    token, advanced = distribution.sample(RandomTape((3, 99)))
    assert token == 1
    assert advanced.cursor == 1
    assert distribution.sample(RandomTape((5,)))[0] == 2


def test_deterministic_distribution_consumes_no_draw() -> None:
    distribution = ExactDistribution.from_pairs([(7, 1)])
    tape = RandomTape(())
    token, returned = distribution.sample(tape)
    assert token == 7
    assert returned is tape


def test_positive_residual_is_exact_for_partial_and_disjoint_support() -> None:
    target = ExactDistribution.from_pairs([(0, 1), (1, 3)])
    proposal = ExactDistribution.from_pairs([(0, 3), (2, 1)])
    residual = target.positive_residual(proposal)
    assert residual.probabilities == ((1, Fraction(1, 1)),)

    disjoint = ExactDistribution.from_pairs([(9, 1)]).positive_residual(ExactDistribution.from_pairs([(8, 1)]))
    assert disjoint.probabilities == ((9, Fraction(1, 1)),)


def test_equal_distributions_have_unreachable_zero_mass_residual() -> None:
    distribution = ExactDistribution.from_pairs([(0, 1), (1, 2)])
    with pytest.raises(UnreachableResidualError, match="zero total mass"):
        distribution.positive_residual(distribution)
