from __future__ import annotations

from fractions import Fraction

import pytest

from forgellm_governance.exact_distribution import ExactDistribution, RandomTape
from forgellm_governance.speculative_decoding import (
    ProposalValidationError,
    decide_one_token,
    exact_bernoulli,
)


def test_exact_bernoulli_zero_and_one_consume_no_draw() -> None:
    empty = RandomTape(())
    assert exact_bernoulli(Fraction(0), empty) == (False, empty)
    assert exact_bernoulli(Fraction(1), empty) == (True, empty)


def test_exact_bernoulli_uses_numerator_denominator_without_modulo() -> None:
    accepted, tape = exact_bernoulli(Fraction(2, 5), RandomTape((1, 99)))
    assert accepted is True
    assert tape.cursor == 1
    rejected, tape = exact_bernoulli(Fraction(2, 5), RandomTape((2,)))
    assert rejected is False
    assert tape.cursor == 1


@pytest.mark.parametrize("probability", [Fraction(-1, 2), Fraction(3, 2)])
def test_exact_bernoulli_rejects_invalid_probability(probability: Fraction) -> None:
    with pytest.raises(ProposalValidationError, match="between zero and one"):
        exact_bernoulli(probability, RandomTape(()))


def test_acceptance_probability_is_exact_and_accept_branch_emits_proposal() -> None:
    target = ExactDistribution.from_pairs([(0, 1), (1, 1)])
    proposal = ExactDistribution.from_pairs([(0, 3), (1, 1)])
    decision = decide_one_token(target, proposal, 0, RandomTape((1,)))
    assert decision.acceptance_probability == Fraction(2, 3)
    assert decision.accepted is True
    assert decision.emitted_token == 0
    assert decision.correction_kind == "accepted"
    assert decision.tape.cursor == 1


def test_acceptance_probability_above_one_clamps_and_consumes_no_draw() -> None:
    target = ExactDistribution.from_pairs([(0, 3), (1, 1)])
    proposal = ExactDistribution.from_pairs([(0, 1), (1, 1)])
    decision = decide_one_token(target, proposal, 0, RandomTape(()))
    assert decision.acceptance_probability == 1
    assert decision.accepted is True
    assert decision.tape.cursor == 0


def test_target_zero_proposal_is_rejected_and_corrected_from_residual() -> None:
    target = ExactDistribution.from_pairs([(1, 1)])
    proposal = ExactDistribution.from_pairs([(0, 1)])
    decision = decide_one_token(target, proposal, 0, RandomTape(()))
    assert decision.acceptance_probability == 0
    assert decision.accepted is False
    assert decision.emitted_token == 1
    assert decision.correction_kind == "residual"
    assert decision.tape.cursor == 0


def test_proposed_token_must_be_in_positive_proposal_support() -> None:
    target = ExactDistribution.from_pairs([(0, 1)])
    proposal = ExactDistribution.from_pairs([(0, 1), (1, 0)])
    with pytest.raises(ProposalValidationError, match="positive support"):
        decide_one_token(target, proposal, 1, RandomTape(()))


def test_rejection_samples_normalized_positive_residual() -> None:
    target = ExactDistribution.from_pairs([(0, 1), (1, 3)])
    proposal = ExactDistribution.from_pairs([(0, 3), (2, 1)])
    decision = decide_one_token(target, proposal, 0, RandomTape((1,)))
    assert decision.accepted is False
    assert decision.emitted_token == 1
    assert decision.tape.cursor == 1


def _one_token_output_law(
    target: ExactDistribution,
    proposal: ExactDistribution,
) -> dict[int, Fraction]:
    output: dict[int, Fraction] = {token: Fraction(0) for token in set(target.support()) | set(proposal.support())}
    for proposed, q_mass in proposal.probabilities:
        p_mass = target.probability(proposed)
        alpha = min(Fraction(1), p_mass / q_mass)
        output[proposed] = output.get(proposed, Fraction(0)) + q_mass * alpha
        rejection_mass = q_mass * (1 - alpha)
        if rejection_mass:
            residual = target.positive_residual(proposal)
            for token, residual_mass in residual.probabilities:
                output[token] = output.get(token, Fraction(0)) + rejection_mass * residual_mass
    return {token: mass for token, mass in output.items() if mass}


@pytest.mark.parametrize(
    ("target", "proposal"),
    [
        (
            ExactDistribution.from_pairs([(0, 1), (1, 1)]),
            ExactDistribution.from_pairs([(0, 1), (1, 1)]),
        ),
        (
            ExactDistribution.from_pairs([(0, 1), (1, 3)]),
            ExactDistribution.from_pairs([(0, 3), (2, 1)]),
        ),
        (
            ExactDistribution.from_pairs([(4, 1)]),
            ExactDistribution.from_pairs([(9, 1)]),
        ),
        (
            ExactDistribution.from_pairs([(0, 1), (1, 2), (2, 3)]),
            ExactDistribution.from_pairs([(0, 5), (1, 1), (3, 2)]),
        ),
    ],
)
def test_exhaustive_one_token_modified_rejection_law_equals_target(
    target: ExactDistribution,
    proposal: ExactDistribution,
) -> None:
    assert _one_token_output_law(target, proposal) == dict(target.probabilities)


def test_equal_distributions_never_enter_residual_or_consume_acceptance_draw() -> None:
    distribution = ExactDistribution.from_pairs([(0, 1), (1, 1)])
    decision = decide_one_token(distribution, distribution, 0, RandomTape(()))
    assert decision.accepted is True
    assert decision.correction_kind == "accepted"
    assert decision.tape.cursor == 0
