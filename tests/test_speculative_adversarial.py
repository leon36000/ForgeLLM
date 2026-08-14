from __future__ import annotations

from fractions import Fraction
from itertools import product

import pytest

from forgellm_governance.exact_distribution import (
    ExactDistribution,
    RandomSourceError,
    RandomTape,
)
from forgellm_governance.speculative_decoding import (
    ProposalValidationError,
    SampledRoundRequest,
    SampledRoundResult,
    decide_one_token,
)
from forgellm_governance.speculative_exhaustive import (
    enumerate_speculative_law,
    enumerate_target_law,
)
from forgellm_governance.speculative_models import FiniteTableModel
from forgellm_governance.speculative_state import (
    DecoderState,
    TransactionStateError,
    begin_round,
    cancel_round,
    commit_round,
)
from forgellm_governance.speculative_trace import build_trace_document


def d(*pairs: tuple[int, int | Fraction]) -> ExactDistribution:
    return ExactDistribution.from_pairs(pairs)


def full_model(
    distribution: ExactDistribution,
    alphabet: tuple[int, ...],
    budget: int,
) -> FiniteTableModel:
    return FiniteTableModel.from_pairs(
        (tuple(prefix), distribution) for length in range(max(budget, 1)) for prefix in product(alphabet, repeat=length)
    )


def clean_state() -> DecoderState:
    return DecoderState((), (), (), None, (), (), False)


def test_random_tape_never_reduces_out_of_range_draw_modulo_bound() -> None:
    with pytest.raises(
        RandomSourceError,
        match="modulo reduction is forbidden",
    ):
        RandomTape((7,)).draw(3)


def test_zero_weight_duplicate_cannot_hide_duplicate_token_identity() -> None:
    with pytest.raises(ValueError, match="duplicate token"):
        ExactDistribution.from_pairs([(0, 0), (0, 1)])


def test_recorded_q_support_is_mandatory_for_proposed_token() -> None:
    target = d((0, 1))
    proposal = d((0, 1))
    with pytest.raises(ProposalValidationError, match="positive support"):
        decide_one_token(target, proposal, 1, RandomTape(()))


@pytest.mark.parametrize("draft_length", [1, 2, 3])
@pytest.mark.parametrize(
    ("target_weights", "proposal_weights"),
    [
        ((1, 1), (1, 1)),
        ((1, 2), (2, 1)),
        ((1, 3), (3, 1)),
        ((2, 3), (5, 1)),
    ],
)
def test_exact_law_grid_covers_overlap_and_imbalance(
    draft_length: int,
    target_weights: tuple[int, int],
    proposal_weights: tuple[int, int],
) -> None:
    budget = 3
    target_distribution = d((0, target_weights[0]), (1, target_weights[1]))
    proposal_distribution = d(
        (0, proposal_weights[0]),
        (2, proposal_weights[1]),
    )
    target = full_model(target_distribution, (0, 1, 2), budget)
    draft = full_model(proposal_distribution, (0, 1, 2), budget)
    assert enumerate_speculative_law(
        target,
        draft,
        (),
        budget,
        draft_length,
        9,
    ) == enumerate_target_law(target, (), budget, 9)


def test_eos_inside_emitted_sequence_is_rejected_by_result_invariants() -> None:
    with pytest.raises(
        ProposalValidationError,
        match="EOS must be the final emitted token",
    ):
        SampledRoundResult(
            prefix=(),
            proposed_tokens=(9, 0),
            accepted_count=2,
            emitted_tokens=(9, 0),
            acceptance_probabilities=(Fraction(1), Fraction(1)),
            correction_kind="none",
            termination="budget",
            tape=RandomTape(()),
            remaining_budget=2,
            eos_token_id=9,
        )


def test_state_transaction_cannot_be_committed_or_cancelled_twice() -> None:
    transaction = begin_round(clean_state(), (0,))
    result = SampledRoundResult(
        prefix=(),
        proposed_tokens=(0,),
        accepted_count=1,
        emitted_tokens=(0,),
        acceptance_probabilities=(Fraction(1),),
        correction_kind="none",
        termination="budget",
        tape=RandomTape(()),
        remaining_budget=1,
        eos_token_id=9,
    )
    _, closed = commit_round(transaction, result)
    with pytest.raises(TransactionStateError, match="closed"):
        commit_round(closed, result)
    with pytest.raises(TransactionStateError, match="closed"):
        cancel_round(closed)


def test_trace_rejects_request_result_budget_and_prefix_mismatch() -> None:
    result = SampledRoundResult(
        prefix=(),
        proposed_tokens=(0,),
        accepted_count=1,
        emitted_tokens=(0,),
        acceptance_probabilities=(Fraction(1),),
        correction_kind="none",
        termination="budget",
        tape=RandomTape(()),
        remaining_budget=1,
        eos_token_id=9,
    )
    with pytest.raises(ValueError, match="prefix"):
        build_trace_document(
            SampledRoundRequest((7,), 1, 1, 9),
            result,
        )
    with pytest.raises(ValueError, match="remaining_budget"):
        build_trace_document(
            SampledRoundRequest((), 1, 2, 9),
            result,
        )
    with pytest.raises(ValueError, match="eos_token_id"):
        build_trace_document(
            SampledRoundRequest((), 1, 1, 8),
            result,
        )
