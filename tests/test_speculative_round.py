from __future__ import annotations

from fractions import Fraction

import pytest

from forgellm_governance.exact_distribution import ExactDistribution, RandomTape
from forgellm_governance.speculative_decoding import (
    ProposalValidationError,
    SampledRoundRequest,
    SampledRoundResult,
    sample_speculative_round,
)
from forgellm_governance.speculative_models import FiniteTableModel, ModelTableError


def d(*pairs: tuple[int, int | Fraction]) -> ExactDistribution:
    return ExactDistribution.from_pairs(pairs)


def model(*rows: tuple[tuple[int, ...], ExactDistribution]) -> FiniteTableModel:
    return FiniteTableModel.from_pairs(rows)


def test_finite_table_model_is_canonical_and_lookup_is_deterministic() -> None:
    table = model(((1,), d((2, 1))), ((), d((1, 1))))
    assert tuple(prefix for prefix, _ in table.table) == ((), (1,))
    assert table.distribution(()).support() == (1,)
    with pytest.raises(ModelTableError, match="missing distribution for prefix"):
        table.distribution((9,))


def test_finite_table_rejects_duplicate_and_invalid_prefixes() -> None:
    with pytest.raises(ModelTableError, match="duplicate prefix"):
        model(((), d((0, 1))), ((), d((1, 1))))
    with pytest.raises(ModelTableError, match="prefix.*tuple"):
        FiniteTableModel.from_pairs([([0], d((1, 1)))])  # type: ignore[list-item]
    with pytest.raises(ModelTableError, match="non-boolean integer"):
        model(((True,), d((1, 1))))  # type: ignore[arg-type]


class NoLookupModel:
    def distribution(self, prefix: tuple[int, ...]) -> ExactDistribution:
        raise AssertionError(f"unexpected lookup at {prefix}")


def test_zero_budget_performs_no_model_lookup_or_random_draw() -> None:
    tape = RandomTape(())
    result = sample_speculative_round(
        NoLookupModel(),  # type: ignore[arg-type]
        NoLookupModel(),  # type: ignore[arg-type]
        SampledRoundRequest(prefix=(), draft_length=2, remaining_budget=0, eos_token_id=9),
        tape,
    )
    assert result.proposed_tokens == ()
    assert result.emitted_tokens == ()
    assert result.termination == "budget"
    assert result.correction_kind == "none"
    assert result.tape is tape


@pytest.mark.parametrize(
    "kwargs",
    [
        {"draft_length": 0, "remaining_budget": 1, "eos_token_id": 9},
        {"draft_length": True, "remaining_budget": 1, "eos_token_id": 9},
        {"draft_length": 1, "remaining_budget": -1, "eos_token_id": 9},
        {"draft_length": 1, "remaining_budget": True, "eos_token_id": 9},
        {"draft_length": 1, "remaining_budget": 1, "eos_token_id": True},
    ],
)
def test_round_request_rejects_invalid_fields(kwargs: dict[str, object]) -> None:
    with pytest.raises((ProposalValidationError, ValueError)):
        SampledRoundRequest(prefix=(), **kwargs)  # type: ignore[arg-type]


def test_all_accepted_block_emits_target_bonus() -> None:
    target = model(((), d((0, 1))), ((0,), d((1, 1))), ((0, 1), d((2, 1))))
    draft = model(((), d((0, 1))), ((0,), d((1, 1))))
    result = sample_speculative_round(
        target,
        draft,
        SampledRoundRequest((), 2, 3, 9),
        RandomTape(()),
    )
    assert result.proposed_tokens == (0, 1)
    assert result.accepted_count == 2
    assert result.emitted_tokens == (0, 1, 2)
    assert result.acceptance_probabilities == (Fraction(1), Fraction(1))
    assert result.correction_kind == "bonus"
    assert result.termination == "all_accepted"


def test_first_rejection_emits_one_residual_and_discards_generated_suffix() -> None:
    target = model(((), d((1, 1))))
    draft = model(((), d((0, 1))), ((0,), d((2, 1))))
    result = sample_speculative_round(
        target,
        draft,
        SampledRoundRequest((), 2, 3, 9),
        RandomTape(()),
    )
    assert result.proposed_tokens == (0, 2)
    assert result.accepted_count == 0
    assert result.emitted_tokens == (1,)
    assert result.acceptance_probabilities == (Fraction(0),)
    assert result.correction_kind == "residual"
    assert result.termination == "rejection"


def test_acceptance_uses_recorded_q_and_does_not_requery_draft_during_verification() -> None:
    class OneShotDraft:
        def __init__(self) -> None:
            self.calls: list[tuple[int, ...]] = []

        def distribution(self, prefix: tuple[int, ...]) -> ExactDistribution:
            self.calls.append(prefix)
            if len(self.calls) > 1:
                raise AssertionError("draft was queried during target verification")
            return d((0, 3), (1, 1))

    draft = OneShotDraft()
    target = model(((), d((0, 1), (1, 1))))
    result = sample_speculative_round(
        target,
        draft,  # type: ignore[arg-type]
        SampledRoundRequest((), 1, 1, 9),
        RandomTape((0, 0)),
    )
    assert result.proposed_tokens == (0,)
    assert result.accepted_count == 1
    assert draft.calls == [()]


def test_accepted_eos_stops_without_bonus() -> None:
    target = model(((), d((9, 1))))
    draft = model(((), d((9, 1))))
    result = sample_speculative_round(
        target,
        draft,
        SampledRoundRequest((), 3, 4, 9),
        RandomTape(()),
    )
    assert result.proposed_tokens == (9,)
    assert result.emitted_tokens == (9,)
    assert result.accepted_count == 1
    assert result.correction_kind == "none"
    assert result.termination == "eos"


def test_residual_eos_has_eos_precedence_over_rejection() -> None:
    target = model(((), d((9, 1))))
    draft = model(((), d((0, 1))))
    result = sample_speculative_round(
        target,
        draft,
        SampledRoundRequest((), 1, 2, 9),
        RandomTape(()),
    )
    assert result.emitted_tokens == (9,)
    assert result.correction_kind == "residual"
    assert result.termination == "eos"


def test_fully_accepted_block_that_exhausts_budget_has_no_bonus() -> None:
    target = model(((), d((0, 1))), ((0,), d((1, 1))))
    draft = model(((), d((0, 1))), ((0,), d((1, 1))))
    result = sample_speculative_round(
        target,
        draft,
        SampledRoundRequest((), 2, 2, 9),
        RandomTape(()),
    )
    assert result.emitted_tokens == (0, 1)
    assert result.correction_kind == "none"
    assert result.termination == "budget"


def test_bonus_eos_has_eos_precedence() -> None:
    target = model(((), d((0, 1))), ((0,), d((9, 1))))
    draft = model(((), d((0, 1))))
    result = sample_speculative_round(
        target,
        draft,
        SampledRoundRequest((), 1, 2, 9),
        RandomTape(()),
    )
    assert result.emitted_tokens == (0, 9)
    assert result.correction_kind == "bonus"
    assert result.termination == "eos"


def test_result_invariants_reject_inconsistent_branch() -> None:
    with pytest.raises(ProposalValidationError, match="accepted proposal prefix"):
        SampledRoundResult(
            prefix=(),
            proposed_tokens=(0,),
            accepted_count=1,
            emitted_tokens=(1,),
            acceptance_probabilities=(Fraction(1),),
            correction_kind="none",
            termination="budget",
            tape=RandomTape(()),
            remaining_budget=1,
            eos_token_id=9,
        )
