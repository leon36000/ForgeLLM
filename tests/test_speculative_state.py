from __future__ import annotations

from dataclasses import FrozenInstanceError
from fractions import Fraction

import pytest

from forgellm_governance.exact_distribution import RandomTape
from forgellm_governance.speculative_decoding import SampledRoundResult
from forgellm_governance.speculative_state import (
    DecoderState,
    RoundTransaction,
    StateInvariantError,
    TransactionStateError,
    begin_round,
    cancel_round,
    commit_round,
    synchronize_pending,
)


def clean_state(prefix: tuple[int, ...] = ()) -> DecoderState:
    return DecoderState(
        output_tokens=prefix,
        target_materialized=prefix,
        draft_materialized=prefix,
        pending_token=None,
        sampler_tokens=prefix,
        grammar_tokens=prefix,
        finished=False,
    )


def result(
    *,
    prefix: tuple[int, ...],
    proposals: tuple[int, ...],
    accepted: int,
    emitted: tuple[int, ...],
    correction: str,
    termination: str,
    budget: int,
    eos: int = 9,
) -> SampledRoundResult:
    probabilities = tuple(Fraction(1) for _ in range(accepted))
    if correction == "residual":
        probabilities += (Fraction(0),)
    return SampledRoundResult(
        prefix=prefix,
        proposed_tokens=proposals,
        accepted_count=accepted,
        emitted_tokens=emitted,
        acceptance_probabilities=probabilities,
        correction_kind=correction,  # type: ignore[arg-type]
        termination=termination,  # type: ignore[arg-type]
        tape=RandomTape(()),
        remaining_budget=budget,
        eos_token_id=eos,
    )


def test_clean_decoder_state_is_valid_and_immutable() -> None:
    state = clean_state((4,))
    assert state.materialized_prefix == (4,)
    with pytest.raises(FrozenInstanceError):
        state.finished = True  # type: ignore[misc]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"target_materialized": (0,), "draft_materialized": ()},
        {"output_tokens": (0,), "sampler_tokens": ()},
        {"output_tokens": (0,), "grammar_tokens": ()},
        {
            "output_tokens": (0,),
            "target_materialized": (),
            "draft_materialized": (),
            "pending_token": None,
        },
        {
            "output_tokens": (0, 1),
            "target_materialized": (0,),
            "draft_materialized": (0,),
            "pending_token": 2,
        },
    ],
)
def test_state_invariants_fail_closed(kwargs: dict[str, object]) -> None:
    base = dict(
        output_tokens=(),
        target_materialized=(),
        draft_materialized=(),
        pending_token=None,
        sampler_tokens=(),
        grammar_tokens=(),
        finished=False,
    )
    base.update(kwargs)
    if "output_tokens" in kwargs:
        if "sampler_tokens" not in kwargs:
            base["sampler_tokens"] = kwargs["output_tokens"]
        if "grammar_tokens" not in kwargs:
            base["grammar_tokens"] = kwargs["output_tokens"]
    with pytest.raises(StateInvariantError):
        DecoderState(**base)  # type: ignore[arg-type]


def test_round_transaction_class_api_records_original() -> None:
    state = clean_state((7,))
    transaction = RoundTransaction.begin(state, (0, 1))
    assert transaction.original is state
    assert transaction.proposed_tokens == (0, 1)
    assert transaction.closed is False


def test_begin_round_rejects_pending_finished_and_empty_proposals() -> None:
    pending = DecoderState(
        output_tokens=(0, 1),
        target_materialized=(0,),
        draft_materialized=(0,),
        pending_token=1,
        sampler_tokens=(0, 1),
        grammar_tokens=(0, 1),
        finished=False,
    )
    with pytest.raises(TransactionStateError, match="pending"):
        begin_round(pending, (2,))
    finished = DecoderState(
        output_tokens=(9,),
        target_materialized=(9,),
        draft_materialized=(9,),
        pending_token=None,
        sampler_tokens=(9,),
        grammar_tokens=(9,),
        finished=True,
    )
    with pytest.raises(TransactionStateError, match="finished"):
        begin_round(finished, (2,))
    with pytest.raises(TransactionStateError, match="at least one"):
        begin_round(clean_state(), ())


def test_commit_all_accepted_without_correction_materializes_every_token() -> None:
    transaction = begin_round(clean_state((7,)), (0, 1))
    round_result = result(
        prefix=(7,),
        proposals=(0, 1),
        accepted=2,
        emitted=(0, 1),
        correction="none",
        termination="budget",
        budget=2,
    )
    committed, closed = transaction.commit(round_result, 9)
    assert committed.output_tokens == (7, 0, 1)
    assert committed.target_materialized == committed.draft_materialized == committed.output_tokens
    assert committed.pending_token is None
    assert committed.sampler_tokens == committed.grammar_tokens == committed.output_tokens
    assert closed.closed is True


def test_commit_accepted_eos_is_materialized_without_pending_token() -> None:
    transaction = begin_round(clean_state(), (9,))
    round_result = result(
        prefix=(),
        proposals=(9,),
        accepted=1,
        emitted=(9,),
        correction="none",
        termination="eos",
        budget=2,
    )
    committed, _ = commit_round(transaction, round_result)
    assert committed.finished is True
    assert committed.pending_token is None
    assert committed.target_materialized == committed.draft_materialized == (9,)


def test_commit_residual_discards_suffix_and_leaves_correction_pending() -> None:
    transaction = begin_round(clean_state((7,)), (0, 1, 2))
    round_result = result(
        prefix=(7,),
        proposals=(0, 1, 2),
        accepted=1,
        emitted=(0, 5),
        correction="residual",
        termination="rejection",
        budget=4,
    )
    committed, _ = commit_round(transaction, round_result)
    assert committed.output_tokens == (7, 0, 5)
    assert committed.target_materialized == committed.draft_materialized == (7, 0)
    assert committed.pending_token == 5


def test_commit_bonus_leaves_bonus_pending_then_synchronizes() -> None:
    transaction = begin_round(clean_state(), (0, 1))
    round_result = result(
        prefix=(),
        proposals=(0, 1),
        accepted=2,
        emitted=(0, 1, 2),
        correction="bonus",
        termination="all_accepted",
        budget=3,
    )
    committed, _ = commit_round(transaction, round_result)
    assert committed.target_materialized == (0, 1)
    assert committed.pending_token == 2
    synchronized = synchronize_pending(committed)
    assert synchronized.target_materialized == synchronized.draft_materialized == synchronized.output_tokens
    assert synchronized.pending_token is None
    assert synchronize_pending(synchronized) is synchronized


def test_residual_and_bonus_eos_are_finished_while_pending() -> None:
    for correction, proposals, accepted, emitted in (
        ("residual", (0,), 0, (9,)),
        ("bonus", (0,), 1, (0, 9)),
    ):
        transaction = begin_round(clean_state(), proposals)
        round_result = result(
            prefix=(),
            proposals=proposals,
            accepted=accepted,
            emitted=emitted,
            correction=correction,
            termination="eos",
            budget=2,
        )
        committed, _ = commit_round(transaction, round_result)
        assert committed.finished is True
        assert committed.pending_token == 9
        synchronized = synchronize_pending(committed)
        assert synchronized.finished is True
        assert synchronized.target_materialized == synchronized.output_tokens


def test_cancel_restores_original_and_closed_transactions_cannot_repeat() -> None:
    original = clean_state((7,))
    transaction = RoundTransaction.begin(original, (0, 1))
    restored, closed = transaction.cancel()
    assert restored is original
    assert closed.closed is True
    with pytest.raises(TransactionStateError, match="closed"):
        cancel_round(closed)


def test_commit_rejects_prefix_proposal_and_eos_mismatch() -> None:
    transaction = begin_round(clean_state(), (0,))
    wrong_prefix = result(
        prefix=(7,),
        proposals=(0,),
        accepted=1,
        emitted=(0,),
        correction="none",
        termination="budget",
        budget=1,
    )
    with pytest.raises(TransactionStateError, match="prefix"):
        commit_round(transaction, wrong_prefix)

    wrong_proposal = result(
        prefix=(),
        proposals=(1,),
        accepted=1,
        emitted=(1,),
        correction="none",
        termination="budget",
        budget=1,
    )
    with pytest.raises(TransactionStateError, match="proposed tokens"):
        commit_round(transaction, wrong_proposal)

    correct = result(
        prefix=(),
        proposals=(0,),
        accepted=1,
        emitted=(0,),
        correction="none",
        termination="budget",
        budget=1,
    )
    with pytest.raises(TransactionStateError, match="eos_token_id"):
        transaction.commit(correct, 8)
