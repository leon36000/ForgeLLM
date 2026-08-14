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
        if not isinstance(self.acceptance_probability, Fraction):
            raise ProposalValidationError("acceptance_probability must be a Fraction")
        if not 0 <= self.acceptance_probability <= 1:
            raise ProposalValidationError("acceptance_probability must be between zero and one")
        if not isinstance(self.accepted, bool):
            raise ProposalValidationError("accepted must be a boolean")
        if self.correction_kind not in {"accepted", "residual"}:
            raise ProposalValidationError("invalid correction_kind")
        if self.accepted and self.correction_kind != "accepted":
            raise ProposalValidationError("accepted decision must use correction_kind accepted")
        if not self.accepted and self.correction_kind != "residual":
            raise ProposalValidationError("rejected decision must use correction_kind residual")
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
    if probability == 0:
        return False, tape
    if probability == 1:
        return True, tape
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
            validate_non_negative_int(self.remaining_budget, name="remaining_budget")
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
        try:
            validate_prefix(self.prefix)
            validate_prefix(self.proposed_tokens, name="proposed_tokens")
            validate_prefix(self.emitted_tokens, name="emitted_tokens")
            validate_non_negative_int(self.accepted_count, name="accepted_count")
            validate_non_negative_int(self.remaining_budget, name="remaining_budget")
            validate_token_id(self.eos_token_id, name="eos_token_id")
        except ValueError as exc:
            raise ProposalValidationError(str(exc)) from exc
        if self.accepted_count > len(self.proposed_tokens):
            raise ProposalValidationError("accepted_count exceeds proposed token count")
        if len(self.emitted_tokens) > self.remaining_budget:
            raise ProposalValidationError("round emitted more tokens than remaining budget")
        if self.proposed_tokens[: self.accepted_count] != self.emitted_tokens[: self.accepted_count]:
            raise ProposalValidationError("accepted proposal prefix must equal emitted proposal prefix")
        if any(not isinstance(value, Fraction) or not 0 <= value <= 1 for value in self.acceptance_probabilities):
            raise ProposalValidationError("acceptance probabilities must be Fractions between zero and one")
        if len(self.acceptance_probabilities) < self.accepted_count:
            raise ProposalValidationError("missing acceptance probability for accepted proposal")
        if self.correction_kind == "residual":
            if self.accepted_count >= len(self.proposed_tokens):
                raise ProposalValidationError("residual correction requires a rejected proposal")
            if len(self.acceptance_probabilities) != self.accepted_count + 1:
                raise ProposalValidationError("residual branch must record through first rejection")
            if len(self.emitted_tokens) != self.accepted_count + 1:
                raise ProposalValidationError("residual branch emits accepted prefix plus one correction")
        elif self.correction_kind == "bonus":
            if self.accepted_count != len(self.proposed_tokens):
                raise ProposalValidationError("bonus requires every proposal to be accepted")
            if len(self.emitted_tokens) != len(self.proposed_tokens) + 1:
                raise ProposalValidationError("bonus branch emits proposals plus one target token")
        elif self.correction_kind == "none":
            if self.emitted_tokens != self.proposed_tokens[: self.accepted_count]:
                raise ProposalValidationError("none branch can emit only accepted proposals")
        else:
            raise ProposalValidationError("invalid round correction_kind")
        contains_eos = self.eos_token_id in self.emitted_tokens
        if contains_eos and self.emitted_tokens[-1] != self.eos_token_id:
            raise ProposalValidationError("EOS must be the final emitted token")
        expected_termination: RoundTermination
        if self.emitted_tokens and self.emitted_tokens[-1] == self.eos_token_id:
            expected_termination = "eos"
        elif self.correction_kind == "residual":
            expected_termination = "rejection"
        elif not self.emitted_tokens or len(self.emitted_tokens) == self.remaining_budget:
            expected_termination = "budget"
        elif self.correction_kind == "bonus":
            expected_termination = "all_accepted"
        else:
            raise ProposalValidationError("fully accepted non-EOS block with remaining budget requires bonus")
        if self.termination != expected_termination:
            raise ProposalValidationError(
                f"termination {self.termination} inconsistent with branch; expected {expected_termination}"
            )


def sample_speculative_round(
    target: DistributionModel,
    draft: DistributionModel,
    request: SampledRoundRequest,
    tape: RandomTape,
) -> SampledRoundResult:
    """Sample one exact speculative round from finite distribution models."""

    if request.remaining_budget == 0:
        return SampledRoundResult(
            prefix=request.prefix,
            proposed_tokens=(),
            accepted_count=0,
            emitted_tokens=(),
            acceptance_probabilities=(),
            correction_kind="none",
            termination="budget",
            tape=tape,
            remaining_budget=0,
            eos_token_id=request.eos_token_id,
        )

    proposal_limit = min(request.draft_length, request.remaining_budget)
    records: list[ProposalRecord] = []
    proposal_prefix = request.prefix
    current_tape = tape
    for _ in range(proposal_limit):
        proposal_distribution = draft.distribution(proposal_prefix)
        proposed_token, current_tape = proposal_distribution.sample(current_tape)
        record = ProposalRecord(proposal_prefix, proposal_distribution, proposed_token)
        records.append(record)
        proposal_prefix = proposal_prefix + (proposed_token,)
        if proposed_token == request.eos_token_id:
            break

    emitted: list[int] = []
    acceptance_probabilities: list[Fraction] = []
    accepted_count = 0
    verification_prefix = request.prefix

    for record in records:
        if record.prefix != verification_prefix:
            raise ProposalValidationError("proposal prefix does not match consecutive verification prefix")
        target_distribution = target.distribution(verification_prefix)
        decision = decide_one_token(
            target_distribution,
            record.distribution,
            record.token,
            current_tape,
        )
        current_tape = decision.tape
        acceptance_probabilities.append(decision.acceptance_probability)
        if decision.accepted:
            emitted.append(record.token)
            accepted_count += 1
            verification_prefix = verification_prefix + (record.token,)
            if record.token == request.eos_token_id:
                return SampledRoundResult(
                    prefix=request.prefix,
                    proposed_tokens=tuple(item.token for item in records),
                    accepted_count=accepted_count,
                    emitted_tokens=tuple(emitted),
                    acceptance_probabilities=tuple(acceptance_probabilities),
                    correction_kind="none",
                    termination="eos",
                    tape=current_tape,
                    remaining_budget=request.remaining_budget,
                    eos_token_id=request.eos_token_id,
                )
            continue

        emitted.append(decision.emitted_token)
        termination: RoundTermination = "eos" if decision.emitted_token == request.eos_token_id else "rejection"
        return SampledRoundResult(
            prefix=request.prefix,
            proposed_tokens=tuple(item.token for item in records),
            accepted_count=accepted_count,
            emitted_tokens=tuple(emitted),
            acceptance_probabilities=tuple(acceptance_probabilities),
            correction_kind="residual",
            termination=termination,
            tape=current_tape,
            remaining_budget=request.remaining_budget,
            eos_token_id=request.eos_token_id,
        )

    if len(emitted) >= request.remaining_budget:
        return SampledRoundResult(
            prefix=request.prefix,
            proposed_tokens=tuple(item.token for item in records),
            accepted_count=accepted_count,
            emitted_tokens=tuple(emitted),
            acceptance_probabilities=tuple(acceptance_probabilities),
            correction_kind="none",
            termination="budget",
            tape=current_tape,
            remaining_budget=request.remaining_budget,
            eos_token_id=request.eos_token_id,
        )

    bonus_distribution = target.distribution(verification_prefix)
    bonus, current_tape = bonus_distribution.sample(current_tape)
    emitted.append(bonus)
    return SampledRoundResult(
        prefix=request.prefix,
        proposed_tokens=tuple(item.token for item in records),
        accepted_count=accepted_count,
        emitted_tokens=tuple(emitted),
        acceptance_probabilities=tuple(acceptance_probabilities),
        correction_kind="bonus",
        termination="eos" if bonus == request.eos_token_id else "all_accepted",
        tape=current_tape,
        remaining_budget=request.remaining_budget,
        eos_token_id=request.eos_token_id,
    )
