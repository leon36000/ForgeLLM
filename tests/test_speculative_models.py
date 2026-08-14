from __future__ import annotations

from fractions import Fraction

import pytest

from forgellm_governance.exact_distribution import ExactDistribution
from forgellm_governance.speculative_models import FiniteTableModel, ModelTableError


def d(*pairs: tuple[int, int | Fraction]) -> ExactDistribution:
    return ExactDistribution.from_pairs(pairs)


def test_model_requires_at_least_one_prefix_and_exact_distribution_values() -> None:
    with pytest.raises(ModelTableError, match="at least one"):
        FiniteTableModel.from_pairs([])
    with pytest.raises(ModelTableError, match="ExactDistribution"):
        FiniteTableModel.from_pairs([((), object())])  # type: ignore[list-item]


def test_source_order_is_canonicalized_and_stored_order_is_enforced() -> None:
    model = FiniteTableModel.from_pairs([((1,), d((2, 1))), ((), d((1, 1)))])
    assert tuple(prefix for prefix, _ in model.table) == ((), (1,))
    with pytest.raises(ModelTableError, match="unique and sorted"):
        FiniteTableModel((((1,), d((2, 1))), ((), d((1, 1)))))


def test_duplicate_prefix_rejected_even_if_distribution_is_equal() -> None:
    distribution = d((0, 1))
    with pytest.raises(ModelTableError, match="duplicate prefix"):
        FiniteTableModel.from_pairs([((), distribution), ((), distribution)])


@pytest.mark.parametrize("prefix", [[0], (True,), (-1,), (0, "x")])
def test_invalid_prefixes_fail_closed(prefix: object) -> None:
    with pytest.raises(ModelTableError):
        FiniteTableModel.from_pairs([(prefix, d((0, 1)))])  # type: ignore[list-item]


def test_missing_lookup_has_stable_prefix_message() -> None:
    model = FiniteTableModel.from_pairs([((), d((0, 1)))])
    with pytest.raises(ModelTableError, match=r"missing distribution for prefix: \(0,\)"):
        model.distribution((0,))
