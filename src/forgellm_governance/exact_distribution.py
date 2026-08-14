"""Exact finite probability distributions for speculative-decoding proofs."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, replace
from fractions import Fraction
from math import lcm


class DistributionValidationError(ValueError):
    """Raised when a finite distribution is malformed."""


class RandomSourceError(ValueError):
    """Raised when an immutable random tape cannot satisfy a draw."""


class UnreachableResidualError(ValueError):
    """Raised when a positive residual has zero total mass."""


def validate_token_id(token: object, *, name: str = "token") -> int:
    """Return a valid non-negative token ID or fail closed."""

    if isinstance(token, bool) or not isinstance(token, int):
        raise DistributionValidationError(f"{name} must be a non-boolean integer")
    if token < 0:
        raise DistributionValidationError(f"{name} must be non-negative")
    return token


def validate_non_negative_int(value: object, *, name: str) -> int:
    """Validate a non-negative, non-boolean integer."""

    if isinstance(value, bool) or not isinstance(value, int):
        raise DistributionValidationError(f"{name} must be a non-boolean integer")
    if value < 0:
        raise DistributionValidationError(f"{name} must be non-negative")
    return value


def validate_positive_int(value: object, *, name: str) -> int:
    """Validate a positive, non-boolean integer."""

    validated = validate_non_negative_int(value, name=name)
    if validated == 0:
        raise DistributionValidationError(f"{name} must be positive")
    return validated


def validate_prefix(prefix: object, *, name: str = "prefix") -> tuple[int, ...]:
    """Validate an immutable token prefix."""

    if not isinstance(prefix, tuple):
        raise DistributionValidationError(f"{name} must be a tuple")
    return tuple(
        validate_token_id(token, name=f"{name}[{index}]")
        for index, token in enumerate(prefix)
    )


def _coerce_weight(weight: object) -> Fraction:
    if isinstance(weight, bool) or not isinstance(weight, (int, Fraction)):
        raise DistributionValidationError("weight must be an int or Fraction")
    value = Fraction(weight)
    if value < 0:
        raise DistributionValidationError("weight must be non-negative")
    return value


@dataclass(frozen=True, slots=True)
class RandomTape:
    """Immutable predetermined integer draws for reproducible exact tests."""

    draws: tuple[int, ...]
    cursor: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.draws, tuple):
            raise RandomSourceError("draws must be a tuple")
        if isinstance(self.cursor, bool) or not isinstance(self.cursor, int):
            raise RandomSourceError("cursor must be a non-boolean integer")
        if self.cursor < 0 or self.cursor > len(self.draws):
            raise RandomSourceError("cursor is outside the random tape")
        for index, draw in enumerate(self.draws):
            if isinstance(draw, bool) or not isinstance(draw, int):
                raise RandomSourceError(f"draw {index} must be a non-boolean integer")
            if draw < 0:
                raise RandomSourceError(f"draw {index} must be non-negative")

    def draw(self, upper_bound: int) -> tuple[int, RandomTape]:
        if isinstance(upper_bound, bool) or not isinstance(upper_bound, int):
            raise RandomSourceError("upper_bound must be a non-boolean integer")
        if upper_bound <= 0:
            raise RandomSourceError("upper_bound must be positive")
        if self.cursor >= len(self.draws):
            raise RandomSourceError("random tape exhausted")
        value = self.draws[self.cursor]
        if value >= upper_bound:
            raise RandomSourceError(
                f"draw {value} is outside randbelow({upper_bound}); modulo reduction is forbidden"
            )
        return value, replace(self, cursor=self.cursor + 1)


@dataclass(frozen=True, slots=True)
class ExactDistribution:
    """Canonical normalized finite categorical distribution."""

    probabilities: tuple[tuple[int, Fraction], ...]

    def __post_init__(self) -> None:
        if not isinstance(self.probabilities, tuple):
            raise DistributionValidationError("stored probabilities must be a tuple")
        if not self.probabilities:
            raise DistributionValidationError("distribution support cannot be empty")
        tokens: list[int] = []
        total = Fraction(0)
        for pair in self.probabilities:
            if not isinstance(pair, tuple) or len(pair) != 2:
                raise DistributionValidationError(
                    "stored probability entries must be token/probability pairs"
                )
            token, probability = pair
            validate_token_id(token)
            if not isinstance(probability, Fraction):
                raise DistributionValidationError("stored probability must be a Fraction")
            if probability <= 0:
                raise DistributionValidationError("stored probability must be positive")
            tokens.append(token)
            total += probability
        if tokens != sorted(tokens) or len(tokens) != len(set(tokens)):
            raise DistributionValidationError("stored support must be unique and sorted")
        if total != 1:
            raise DistributionValidationError(
                "stored probabilities must sum exactly to one"
            )

    @classmethod
    def from_pairs(
        cls,
        pairs: Iterable[tuple[int, int | Fraction]],
    ) -> ExactDistribution:
        seen: set[int] = set()
        weighted: list[tuple[int, Fraction]] = []
        pair_count = 0
        for raw_pair in pairs:
            pair_count += 1
            if not isinstance(raw_pair, tuple) or len(raw_pair) != 2:
                raise DistributionValidationError(
                    "each distribution entry must be a token/weight pair"
                )
            raw_token, raw_weight = raw_pair
            token = validate_token_id(raw_token)
            if token in seen:
                raise DistributionValidationError(f"duplicate token id: {token}")
            seen.add(token)
            weight = _coerce_weight(raw_weight)
            if weight > 0:
                weighted.append((token, weight))
        if pair_count == 0:
            raise DistributionValidationError(
                "distribution requires at least one token/weight pair"
            )
        total = sum((weight for _, weight in weighted), Fraction(0))
        if total <= 0:
            raise DistributionValidationError(
                "distribution total weight must be positive"
            )
        return cls(
            tuple(
                sorted(
                    ((token, weight / total) for token, weight in weighted),
                    key=lambda item: item[0],
                )
            )
        )

    def probability(self, token: int) -> Fraction:
        validated = validate_token_id(token)
        for item_token, probability in self.probabilities:
            if item_token == validated:
                return probability
        return Fraction(0)

    def support(self) -> tuple[int, ...]:
        return tuple(token for token, _ in self.probabilities)

    def argmax(self) -> int:
        return min(self.probabilities, key=lambda item: (-item[1], item[0]))[0]

    def sample(self, tape: RandomTape) -> tuple[int, RandomTape]:
        if not isinstance(tape, RandomTape):
            raise RandomSourceError("tape must be a RandomTape")
        if len(self.probabilities) == 1:
            return self.probabilities[0][0], tape
        denominator = 1
        for _, probability in self.probabilities:
            denominator = lcm(denominator, probability.denominator)
        integer_weights = tuple(
            (
                token,
                probability.numerator
                * (denominator // probability.denominator),
            )
            for token, probability in self.probabilities
        )
        total = sum(weight for _, weight in integer_weights)
        draw, advanced = tape.draw(total)
        cumulative = 0
        for token, weight in integer_weights:
            cumulative += weight
            if draw < cumulative:
                return token, advanced
        raise AssertionError("unreachable categorical sampling state")

    def positive_residual(
        self,
        proposal: ExactDistribution,
    ) -> ExactDistribution:
        if not isinstance(proposal, ExactDistribution):
            raise DistributionValidationError(
                "proposal must be an ExactDistribution"
            )
        tokens = sorted(set(self.support()) | set(proposal.support()))
        residual = [
            (
                token,
                max(
                    Fraction(0),
                    self.probability(token) - proposal.probability(token),
                ),
            )
            for token in tokens
        ]
        if sum((weight for _, weight in residual), Fraction(0)) == 0:
            raise UnreachableResidualError(
                "positive residual has zero total mass"
            )
        return ExactDistribution.from_pairs(residual)
