"""Exact speculative-decoding sampling kernels and sampled block rounds."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Literal, Protocol

from .exact_distribution import (
    ExactDistribution,
    RandomTape,
    validate_non_negative_int,
    validate_positive_int,
    validate_prefix,
    validate_token_id,
)


class ProposalValidationError(ValueError):
    """Raised when a proposal or exact sampling decision is inconsistent."""


CorrectionKind = Literal["accepted", "residual"]


@dataclass(frozen=True, slots=True)
class OneTokenDecision:
    proposed_token: int
    acceptance_probability: Fraction
    accepted: bool
    emitted_token: int
    correction_kind: CorrectionKind
    tape: RandomTape

    def __post_init__(self) -> None:
        validate_token_id(self.proposed_token, name="proposed_token")
        validate_token_id(self.emitted_token, name="emitted_token")
        if not isinstance(self.tape, RandomTape):
            raise ProposalValidationError("tape must be a RandomTape")
        if not isinstance(self.acceptance_probability, Fraction):
            raise ProposalValidationError("acceptance_probability must be a Fraction")
        if not 0 <= self.acceptance_probability <= 1:
            raise ProposalValidationError("acceptance_probability must be between zero and one")
        if not isinstance(self.accepted, bool):
            raise ProposalValidationError("accepted must be a boolean")
        expected_kind: CorrectionKind = "accepted" if self.accepted else "residual"
        if self.correction_kind != expected_kind:
            raise ProposalValidationError(f"decision must use correction_kind {expected_kind}")
        if self.accepted and self.emitted_token != self.proposed_token:
            raise ProposalValidationError("accepted decision must emit the proposed token")


def exact_bernoulli(
    probability: Fraction,
    tape: RandomTape,
) -> tuple[bool, RandomTape]:
    """Sample an exact Bernoulli choice using an immutable integer tape."""

    if not isinstance(probability, Fraction):
        raise ProposalValidationError("probability must be a Fraction")
    if not 0 <= probability <= 1:
        raise ProposalValidationError("probability must be between zero and one")
    if probability.denominator == 1:
        return probability.numerator == 1, tape
    draw, advanced = tape.draw(probability.denominator)
    return draw < probability.numerator, advanced


def acceptance_probability(
    target: ExactDistribution,
    proposal: ExactDistribution,
    proposed_token: int,
) -> Fraction:
    """Return min(1, p(x)/q(x)), requiring x to be in positive q support."""

    token = validate_token_id(proposed_token, name="proposed_token")
    q_mass = proposal.probability(token)
    if q_mass <= 0:
        raise ProposalValidationError(
            f"proposed token {token} must belong to positive support of proposal distribution"
        )
    p_mass = target.probability(token)
    return min(Fraction(1), p_mass / q_mass)


def decide_one_token(
    target: ExactDistribution,
    proposal: ExactDistribution,
    proposed_token: int,
    tape: RandomTape,
) -> OneTokenDecision:
    """Apply exact modified rejection sampling to one recorded proposal token."""

    alpha = acceptance_probability(target, proposal, proposed_token)
    accepted, tape_after_acceptance = exact_bernoulli(alpha, tape)
    if accepted:
        return OneTokenDecision(
            proposed_token=proposed_token,
            acceptance_probability=alpha,
            accepted=True,
            emitted_token=proposed_token,
            correction_kind="accepted",
            tape=tape_after_acceptance,
        )
    residual = target.positive_residual(proposal)
    correction, tape_after_correction = residual.sample(tape_after_acceptance)
    return OneTokenDecision(
        proposed_token=proposed_token,
        acceptance_probability=alpha,
        accepted=False,
        emitted_token=correction,
        correction_kind="residual",
        tape=tape_after_correction,
    )


class DistributionModel(Protocol):
    def distribution(self, prefix: tuple[int, ...]) -> ExactDistribution: ...


@dataclass(frozen=True, slots=True)
class ProposalRecord:
    prefix: tuple[int, ...]
    distribution: ExactDistribution
    token: int

    def __post_init__(self) -> None:
        validate_prefix(self.prefix)
        if not isinstance(self.distribution, ExactDistribution):
            raise ProposalValidationError("proposal distribution must be an ExactDistribution")
        token = validate_token_id(self.token)
        if self.distribution.probability(token) <= 0:
            raise ProposalValidationError("proposal token must belong to positive proposal support")


@dataclass(frozen=True, slots=True)
class SampledRoundRequest:
    prefix: tuple[int, ...]
    draft_length: int
    remaining_budget: int
    eos_token_id: int

    def __post_init__(self) -> None:
        try:
            validate_prefix(self.prefix)
            validate_positive_int(self.draft_length, name="draft_length")
            validate_non_negative_int(
                self.remaining_budget,
                name="remaining_budget",
            )
            validate_token_id(self.eos_token_id, name="eos_token_id")
        except ValueError as exc:
            raise ProposalValidationError(str(exc)) from exc


RoundCorrectionKind = Literal["none", "residual", "bonus"]
RoundTermination = Literal["budget", "eos", "rejection", "all_accepted"]


@dataclass(frozen=True, slots=True)
class SampledRoundResult:
    prefix: tuple[int, ...]
    proposed_tokens: tuple[int, ...]
    accepted_count: int
    emitted_tokens: tuple[int, ...]
    acceptance_probabilities: tuple[Fraction, ...]
    correction_kind: RoundCorrectionKind
    termination: RoundTermination
    tape: RandomTape
    remaining_budget: int
    eos_token_id: int

    def __post_init__(self) -> None:
        _validate_round_primitives(self)
        _validate_round_structure(self)
        _validate_round_branch(self)
        _validate_round_termination(self)


def _validate_round_primitives(result: SampledRoundResult) -> None:
    try:
        validate_prefix(result.prefix)
        validate_prefix(result.proposed_tokens, name="proposed_tokens")
        validate_prefix(result.emitted_tokens, name="emitted_tokens")
        validate_non_negative_int(result.accepted_count, name="accepted_count")
        validate_non_negative_int(result.remaining_budget, name="remaining_budget")
        validate_token_id(result.eos_token_id, name="eos_token_id")
    except ValueError as exc:
        raise ProposalValidationError(str(exc)) from exc
    if not isinstance(result.tape, RandomTape):
        raise ProposalValidationError("tape must be a RandomTape")
    if any(not isinstance(value, Fraction) or not 0 <= value <= 1 for value in result.acceptance_probabilities):
        raise ProposalValidationError("acceptance probabilities must be Fractions between zero and one")


def _validate_round_structure(result: SampledRoundResult) -> None:
    if result.remaining_budget > 0 and not result.proposed_tokens:
        raise ProposalValidationError("positive budget requires at least one proposal")
    if result.eos_token_id in result.proposed_tokens[:-1]:
        raise ProposalValidationError("EOS must be the final proposed token")
    if result.accepted_count > len(result.proposed_tokens):
        raise ProposalValidationError("accepted_count exceeds proposed token count")
    if len(result.emitted_tokens) > result.remaining_budget:
        raise ProposalValidationError("round emitted more tokens than remaining budget")
    if result.proposed_tokens[: result.accepted_count] != result.emitted_tokens[: result.accepted_count]:
        raise ProposalValidationError("accepted proposal prefix must equal emitted proposal prefix")
    if result.eos_token_id in result.emitted_tokens[:-1]:
        raise ProposalValidationError("EOS must be the final emitted token")


def _validate_residual_branch(result: SampledRoundResult) -> None:
    if result.accepted_count >= len(result.proposed_tokens):
        raise ProposalValidationError("residual correction requires a rejected proposal")
    if len(result.acceptance_probabilities) != result.accepted_count + 1:
        raise ProposalValidationError("residual branch must record through first rejection")
    if len(result.emitted_tokens) != result.accepted_count + 1:
        raise ProposalValidationError("residual branch emits accepted prefix plus one correction")


def _validate_bonus_branch(result: SampledRoundResult) -> None:
    if result.accepted_count != len(result.proposed_tokens):
        raise ProposalValidationError("bonus requires every proposal to be accepted")
    if len(result.acceptance_probabilities) != result.accepted_count:
        raise ProposalValidationError("bonus branch must record exactly every accepted proposal")
    if len(result.emitted_tokens) != len(result.proposed_tokens) + 1:
        raise ProposalValidationError("bonus branch emits proposals plus one target token")


def _validate_none_branch(result: SampledRoundResult) -> None:
    if result.accepted_count != len(result.proposed_tokens):
        raise ProposalValidationError("none branch requires every generated proposal to be accepted")
    if len(result.acceptance_probabilities) != result.accepted_count:
        raise ProposalValidationError("none branch must record exactly every accepted proposal")
    if result.emitted_tokens != result.proposed_tokens:
        raise ProposalValidationError("none branch can emit only all accepted proposals")


def _validate_round_branch(result: SampledRoundResult) -> None:
    validators = {
        "residual": _validate_residual_branch,
        "bonus": _validate_bonus_branch,
        "none": _validate_none_branch,
    }
    try:
        validator = validators[result.correction_kind]
    except KeyError as exc:
        raise ProposalValidationError("invalid round correction_kind") from exc
    validator(result)


def _expected_termination(result: SampledRoundResult) -> RoundTermination:
    if result.emitted_tokens and result.emitted_tokens[-1] == result.eos_token_id:
        return "eos"
    if result.correction_kind == "residual":
        return "rejection"
    if result.correction_kind == "bonus":
        return "all_accepted"
    if not result.emitted_tokens or len(result.emitted_tokens) == result.remaining_budget:
        return "budget"
    raise ProposalValidationError("fully accepted non-EOS block with remaining budget requires bonus")


def _validate_round_termination(result: SampledRoundResult) -> None:
    expected = _expected_termination(result)
    if result.termination != expected:
        raise ProposalValidationError(f"termination {result.termination} inconsistent with branch; expected {expected}")


@dataclass(frozen=True, slots=True)
class _AcceptedPrefix:
    emitted_tokens: tuple[int, ...]
    acceptance_probabilities: tuple[Fraction, ...]
    verification_prefix: tuple[int, ...]
    tape: RandomTape


def _proposal_tokens(records: tuple[ProposalRecord, ...]) -> tuple[int, ...]:
    return tuple(record.token for record in records)


def _make_round_result(
    request: SampledRoundRequest,
    records: tuple[ProposalRecord, ...],
    accepted_count: int,
    emitted_tokens: tuple[int, ...],
    acceptance_probabilities: tuple[Fraction, ...],
    correction_kind: RoundCorrectionKind,
    termination: RoundTermination,
    tape: RandomTape,
) -> SampledRoundResult:
    return SampledRoundResult(
        prefix=request.prefix,
        proposed_tokens=_proposal_tokens(records),
        accepted_count=accepted_count,
        emitted_tokens=emitted_tokens,
        acceptance_probabilities=acceptance_probabilities,
        correction_kind=correction_kind,
        termination=termination,
        tape=tape,
        remaining_budget=request.remaining_budget,
        eos_token_id=request.eos_token_id,
    )


def _empty_budget_result(request: SampledRoundRequest, tape: RandomTape) -> SampledRoundResult:
    return _make_round_result(
        request,
        (),
        0,
        (),
        (),
        "none",
        "budget",
        tape,
    )


def _generate_proposals(
    draft: DistributionModel,
    request: SampledRoundRequest,
    tape: RandomTape,
) -> tuple[tuple[ProposalRecord, ...], RandomTape]:
    proposal_limit = min(request.draft_length, request.remaining_budget)
    records: list[ProposalRecord] = []
    proposal_prefix = request.prefix
    current_tape = tape
    for _ in range(proposal_limit):
        proposal_distribution = draft.distribution(proposal_prefix)
        proposed_token, current_tape = proposal_distribution.sample(current_tape)
        records.append(ProposalRecord(proposal_prefix, proposal_distribution, proposed_token))
        proposal_prefix = proposal_prefix + (proposed_token,)
        if proposed_token == request.eos_token_id:
            break
    return tuple(records), current_tape


def _rejected_round_result(
    request: SampledRoundRequest,
    records: tuple[ProposalRecord, ...],
    accepted_tokens: tuple[int, ...],
    acceptance_probabilities: tuple[Fraction, ...],
    decision: OneTokenDecision,
) -> SampledRoundResult:
    emitted_tokens = accepted_tokens + (decision.emitted_token,)
    termination: RoundTermination = "eos" if decision.emitted_token == request.eos_token_id else "rejection"
    return _make_round_result(
        request,
        records,
        len(accepted_tokens),
        emitted_tokens,
        acceptance_probabilities,
        "residual",
        termination,
        decision.tape,
    )


def _accepted_eos_result(
    request: SampledRoundRequest,
    records: tuple[ProposalRecord, ...],
    accepted_tokens: tuple[int, ...],
    acceptance_probabilities: tuple[Fraction, ...],
    tape: RandomTape,
) -> SampledRoundResult:
    return _make_round_result(
        request,
        records,
        len(accepted_tokens),
        accepted_tokens,
        acceptance_probabilities,
        "none",
        "eos",
        tape,
    )


def _verify_proposals(
    target: DistributionModel,
    request: SampledRoundRequest,
    records: tuple[ProposalRecord, ...],
    tape: RandomTape,
) -> SampledRoundResult | _AcceptedPrefix:
    accepted_tokens: tuple[int, ...] = ()
    acceptance_probabilities: tuple[Fraction, ...] = ()
    verification_prefix = request.prefix
    current_tape = tape
    for record in records:
        if record.prefix != verification_prefix:
            raise ProposalValidationError("proposal prefix does not match consecutive verification prefix")
        decision = decide_one_token(
            target.distribution(verification_prefix),
            record.distribution,
            record.token,
            current_tape,
        )
        current_tape = decision.tape
        acceptance_probabilities += (decision.acceptance_probability,)
        if not decision.accepted:
            return _rejected_round_result(
                request,
                records,
                accepted_tokens,
                acceptance_probabilities,
                decision,
            )
        accepted_tokens += (record.token,)
        verification_prefix += (record.token,)
        if record.token == request.eos_token_id:
            return _accepted_eos_result(
                request,
                records,
                accepted_tokens,
                acceptance_probabilities,
                current_tape,
            )
    return _AcceptedPrefix(
        accepted_tokens,
        acceptance_probabilities,
        verification_prefix,
        current_tape,
    )


def _complete_all_accepted(
    target: DistributionModel,
    request: SampledRoundRequest,
    records: tuple[ProposalRecord, ...],
    accepted: _AcceptedPrefix,
) -> SampledRoundResult:
    if len(accepted.emitted_tokens) >= request.remaining_budget:
        return _make_round_result(
            request,
            records,
            len(accepted.emitted_tokens),
            accepted.emitted_tokens,
            accepted.acceptance_probabilities,
            "none",
            "budget",
            accepted.tape,
        )
    bonus, advanced = target.distribution(accepted.verification_prefix).sample(accepted.tape)
    termination: RoundTermination = "eos" if bonus == request.eos_token_id else "all_accepted"
    return _make_round_result(
        request,
        records,
        len(accepted.emitted_tokens),
        accepted.emitted_tokens + (bonus,),
        accepted.acceptance_probabilities,
        "bonus",
        termination,
        advanced,
    )


def sample_speculative_round(
    target: DistributionModel,
    draft: DistributionModel,
    request: SampledRoundRequest,
    tape: RandomTape,
) -> SampledRoundResult:
    """Sample one exact speculative round from finite distribution models."""

    if request.remaining_budget == 0:
        return _empty_budget_result(request, tape)
    records, tape_after_proposals = _generate_proposals(draft, request, tape)
    verified = _verify_proposals(target, request, records, tape_after_proposals)
    if isinstance(verified, SampledRoundResult):
        return verified
    return _complete_all_accepted(target, request, records, verified)
