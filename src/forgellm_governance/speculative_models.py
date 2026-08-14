"""Finite table-defined autoregressive models for exact reference tests."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from .exact_distribution import (
    DistributionValidationError,
    ExactDistribution,
    validate_prefix,
)


class ModelTableError(ValueError):
    """Raised when a finite autoregressive table is invalid or incomplete."""


@dataclass(frozen=True, slots=True)
class FiniteTableModel:
    """Immutable canonical mapping from token prefixes to exact distributions."""

    table: tuple[tuple[tuple[int, ...], ExactDistribution], ...]

    def __post_init__(self) -> None:
        if not isinstance(self.table, tuple):
            raise ModelTableError("table must be a tuple")
        prefixes: list[tuple[int, ...]] = []
        for entry in self.table:
            if not isinstance(entry, tuple) or len(entry) != 2:
                raise ModelTableError("table entries must be prefix/distribution pairs")
            prefix, distribution = entry
            try:
                validated = validate_prefix(prefix)
            except DistributionValidationError as exc:
                raise ModelTableError(str(exc)) from exc
            if validated != prefix:
                raise ModelTableError("prefix must be a canonical tuple")
            if not isinstance(distribution, ExactDistribution):
                raise ModelTableError("table value must be an ExactDistribution")
            prefixes.append(prefix)
        if prefixes != sorted(prefixes) or len(prefixes) != len(set(prefixes)):
            raise ModelTableError("stored table prefixes must be unique and sorted")

    @classmethod
    def from_pairs(
        cls,
        pairs: Iterable[tuple[tuple[int, ...], ExactDistribution]],
    ) -> FiniteTableModel:
        seen: set[tuple[int, ...]] = set()
        entries: list[tuple[tuple[int, ...], ExactDistribution]] = []
        for raw in pairs:
            if not isinstance(raw, tuple) or len(raw) != 2:
                raise ModelTableError("table entries must be prefix/distribution pairs")
            raw_prefix, distribution = raw
            try:
                prefix = validate_prefix(raw_prefix)
            except DistributionValidationError as exc:
                raise ModelTableError(str(exc)) from exc
            if prefix in seen:
                raise ModelTableError(f"duplicate prefix: {prefix}")
            seen.add(prefix)
            if not isinstance(distribution, ExactDistribution):
                raise ModelTableError("table value must be an ExactDistribution")
            entries.append((prefix, distribution))
        if not entries:
            raise ModelTableError("finite table requires at least one prefix")
        return cls(tuple(sorted(entries, key=lambda item: item[0])))

    def distribution(self, prefix: tuple[int, ...]) -> ExactDistribution:
        try:
            validated = validate_prefix(prefix)
        except DistributionValidationError as exc:
            raise ModelTableError(str(exc)) from exc
        for item_prefix, distribution in self.table:
            if item_prefix == validated:
                return distribution
        raise ModelTableError(f"missing distribution for prefix: {validated}")
