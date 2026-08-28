"""Stdlib-only, independently re-derivable reference oracle for `crates/forgellm-reference`.

This module replaces hand-copied golden-constant test assertions with values
computed from first principles, using only the Python standard library
(`fractions`, `decimal`). No third-party numerical dependency (NumPy, PyTorch,
mpmath) is introduced.

Two error regimes, derived rather than guessed
------------------------------------------------

IEEE 754-2019 SS5 requires correctly-rounded results for the basic operations
(``+ - * / sqrt``). It only *recommends* (SS9.2, not required) correct rounding
for ``exp``. This module treats the resulting two regimes differently:

* **Exact-`Fraction` ops** (`matmul`, `elementwise_add`, `elementwise_mul`,
  `embedding_gather`): every f32 input is an exact dyadic rational, and `+`/`*`
  on dyadic rationals stay dyadic, so the mathematically exact result is
  representable and comparable at *zero* tolerance -- provided every
  intermediate f64 accumulation step (the accumulation order Rust actually
  uses) stays within 53 bits of precision. The fixture generator checks this
  mechanically for every case (see `assert_f64_exact_accumulation`) rather
  than assuming it; fixture magnitudes are kept small specifically so this
  precondition is trivially satisfied.

* **`sqrt`-based ops** (`rms_norm`): IEEE 754 mandates correct rounding for
  `sqrt` and division, so the error budget is *provably* tight: propagating
  correctly-rounded-relative-error-`u` (`u = 2**-53`, f64 machine epsilon)
  through subtract/mean/sqrt/divide/cast gives a budget on the order of
  `4*u + 2**-24` (the `2**-24` term dominates -- a single correctly-rounded
  f64->f32 narrowing cast).

* **`exp`-based ops** (`softmax`): the budget is *derived*, not guessed, from
  a stated assumption about libm quality. Let `kappa` be the libm's ULP error
  bound for `exp` (this module assumes `kappa = 4`, a conservative pad over
  glibc's typically sub-2-ULP behavior -- an explicit, cited assumption, not
  a proof). Propagating through shift (exact) -> exp (`kappa` ULP each) ->
  sequential sum of `n` terms (forward error <= `(n-1)*u`, Higham Thm 4.2) ->
  divide (`+u`) -> f64->f32 cast (`2**-24`) gives
  `epsilon ~= (2*kappa + n + 2)*u + 2**-24`, dominated by the final cast for
  any realistic `n`. This module computes that budget per fixture case rather
  than reusing one repository-wide constant.

Avoiding double rounding
-------------------------

Converting a computed high-precision value to f32 via
``Decimal -> Python float (f64) -> struct.pack('<f', ...)`` performs *two*
roundings of the same quantity and can disagree with a single correct
rounding near a halfway point. This module never does that for a *computed*
value: `decimal_to_fraction` converts a `Decimal` to an exact `Fraction` via
`Decimal.as_integer_ratio()` (exact by definition for any finite Decimal --
every finite Decimal is a terminating decimal, hence rational), and
`fraction_to_f32_bits` rounds that Fraction directly to the nearest f32 bit
pattern in one step, round-half-to-even, using only integer and exact-Fraction
comparisons. (`f32_bits_to_fraction` still uses `struct.unpack`/`.pack` to
decode an *already f32-exact* literal test input -- that introduces no
rounding, since the value is already exactly representable.)

Residual risk, stated honestly
--------------------------------

No finite-precision oracle can rule out the Table Maker's Dilemma by
construction: `Decimal.exp()`/`.sqrt()` are correctly rounded *to the working
precision*, not to infinite precision, so rounding a P-digit approximation to
24 bits is technically a second rounding of the same transcendental value.
`decimal_transcendental_with_escape` mitigates this with Ziv's algorithm:
compute at precision `P`, check whether the result is providably farther from
the nearest f32 rounding boundary than the P-digit error bound; if not, double
`P` and retry, raising rather than silently guessing if a maximum precision is
exceeded. This module could not independently verify (no network access
during design) whether Python's `decimal` module unconditionally guarantees
correctly-rounded `exp`/`sqrt` per the General Decimal Arithmetic
Specification, versus "correctly rounded except in rare documented cases";
the wide starting precision margin (40 digits against a ~7.3-digit
requirement) is deliberately robust to that uncertainty either way.
"""

from __future__ import annotations

import math
import struct
from decimal import Decimal, getcontext
from fractions import Fraction

F64_EPSILON = Fraction(1, 2**53)
F32_CAST_HALF_ULP = Fraction(1, 2**24)
LIBM_EXP_ULP_ASSUMPTION = 4  # cited assumption, see module docstring; not a proof.


class ReferenceOracleAmbiguousRounding(Exception):
    """Raised when a high-precision computation cannot be proven correctly rounded.

    This is a fail-closed signal, not a silent approximation: the caller must
    either raise the precision ceiling deliberately or treat the input as
    genuinely ambiguous.
    """


# ---------------------------------------------------------------------------
# Exact f32 <-> Fraction conversion, and round-half-to-even rounding.
# ---------------------------------------------------------------------------


def f32_bits_to_fraction(bits: int) -> Fraction | None:
    """Exact conversion of an f32 bit pattern to a Fraction.

    Every finite f32 is an exact dyadic rational. Promoting to a Python
    ``float`` (f64) via struct is lossless (f32 has 24 significant bits, f64
    has 53), and ``float.as_integer_ratio()`` is documented to be exact.
    Returns ``None`` for NaN or infinity, which carry no rational value.
    """
    (value,) = struct.unpack("<f", struct.pack("<I", bits & 0xFFFFFFFF))
    if math.isnan(value) or math.isinf(value):
        return None
    return Fraction(*value.as_integer_ratio())


def fraction_to_f32_bits(value: Fraction) -> int:
    """Round an exact Fraction to the nearest f32 bit pattern, round-half-to-even.

    Uses only integer and exact-Fraction comparisons -- no intermediate
    ``float`` rounding of the input value occurs anywhere in this function.
    """
    if value == 0:
        return 0
    sign = 1 if value < 0 else 0
    magnitude = -value if value < 0 else value

    # Find e such that 2**e <= magnitude < 2**(e+1), exactly.
    e = magnitude.numerator.bit_length() - magnitude.denominator.bit_length()
    while Fraction(2) ** e > magnitude:
        e -= 1
    while Fraction(2) ** (e + 1) <= magnitude:
        e += 1

    if e > 127:
        # Magnitude alone (before any rounding) already exceeds the largest
        # finite f32 range; no rounding decision can bring it back down.
        return (sign << 31) | (0xFF << 23)

    field_exp = max(e, -126)  # subnormal floor
    scaled = magnitude / (Fraction(2) ** (field_exp - 23))
    mantissa = int(scaled)
    remainder = scaled - mantissa
    half = Fraction(1, 2)
    if remainder > half or (remainder == half and mantissa % 2 == 1):
        mantissa += 1
        if mantissa == (1 << 24):
            mantissa >>= 1
            field_exp += 1
            if field_exp > 127:
                return (sign << 31) | (0xFF << 23)

    # A subnormal mantissa that rounds up to exactly 2**23 is precisely the
    # smallest normal number (1.0 * 2**field_exp); this single comparison
    # handles both the normal and subnormal-to-normal-transition cases.
    stored_exp = (field_exp + 127) if mantissa >= (1 << 23) else 0
    return (sign << 31) | (stored_exp << 23) | (mantissa & 0x7FFFFF)


def decimal_to_fraction(value: Decimal) -> Fraction:
    """Exact conversion: every finite Decimal is a terminating decimal, hence rational."""
    numerator, denominator = value.as_integer_ratio()
    return Fraction(numerator, denominator)


# ---------------------------------------------------------------------------
# Exact-Fraction ops: matmul, elementwise add/mul, embedding gather.
# ---------------------------------------------------------------------------


def elementwise_add_exact(lhs: list[Fraction], rhs: list[Fraction]) -> list[Fraction]:
    if len(lhs) != len(rhs):
        raise ValueError("elementwise_add_exact requires equal-length operands")
    return [a + b for a, b in zip(lhs, rhs, strict=True)]


def elementwise_mul_exact(lhs: list[Fraction], rhs: list[Fraction]) -> list[Fraction]:
    if len(lhs) != len(rhs):
        raise ValueError("elementwise_mul_exact requires equal-length operands")
    return [a * b for a, b in zip(lhs, rhs, strict=True)]


def matmul_exact(lhs: list[list[Fraction]], rhs: list[list[Fraction]]) -> list[list[Fraction]]:
    """Row-major rank-2 matmul, exact. Accumulates left-to-right per output cell,
    matching the sequential fold order of Rust's f64 accumulation."""
    if not lhs or not rhs:
        raise ValueError("matmul_exact requires non-empty operands")
    inner = len(lhs[0])
    if any(len(row) != inner for row in lhs):
        raise ValueError("matmul_exact requires a rectangular left operand")
    if len(rhs) != inner:
        raise ValueError("matmul_exact inner dimension mismatch")
    cols = len(rhs[0])
    if any(len(row) != cols for row in rhs):
        raise ValueError("matmul_exact requires a rectangular right operand")

    result: list[list[Fraction]] = []
    for lhs_row in lhs:
        out_row: list[Fraction] = []
        for col in range(cols):
            accumulator = Fraction(0)
            for k in range(inner):
                accumulator += lhs_row[k] * rhs[k][col]
            out_row.append(accumulator)
        result.append(out_row)
    return result


def embedding_gather_exact(table: list[list[Fraction]], token_ids: list[int]) -> list[list[Fraction]]:
    """No arithmetic occurs; row lookup preserving order and repetition is exact by construction."""
    if not table:
        raise ValueError("embedding_gather_exact requires a non-empty table")
    width = len(table[0])
    if any(len(row) != width for row in table):
        raise ValueError("embedding_gather_exact requires a rectangular table")
    rows = len(table)
    result: list[list[Fraction]] = []
    for token_id in token_ids:
        if not (0 <= token_id < rows):
            raise ValueError(f"embedding_gather_exact token id {token_id} out of range")
        result.append(list(table[token_id]))
    return result


def assert_f64_exact_accumulation(partial_sums: list[Fraction], *, context: str) -> None:
    """Mechanically verify a fixture case's accumulation stays within 53-bit f64 precision.

    Fails closed (raises) rather than silently emitting a fixture case whose
    "exact" comparison would not actually match Rust's f64 accumulation.
    """
    for partial in partial_sums:
        if partial == 0:
            continue
        reduced = partial.numerator if partial.denominator == 1 else partial
        numerator = abs(reduced.numerator if isinstance(reduced, Fraction) else reduced)
        if numerator.bit_length() > 53:
            raise ReferenceOracleAmbiguousRounding(
                f"{context}: partial sum {partial} exceeds 53-bit f64-exact accumulation "
                "range; reduce fixture magnitude or dimension"
            )


# ---------------------------------------------------------------------------
# Decimal-based ops with derived, escalating precision: softmax, rms_norm.
# ---------------------------------------------------------------------------


def _distance_to_nearest_f32_boundary(value: Fraction) -> Fraction:
    """Exact distance from `value` to the nearer of its two neighboring f32
    representable values (or its own exact value if already exactly f32-representable)."""
    if value == 0:
        return Fraction(1, 2**149)  # smallest positive subnormal magnitude
    lower_bits = fraction_to_f32_bits(value)
    lower_fraction = f32_bits_to_fraction(lower_bits)
    if lower_fraction == value:
        # value is already exactly f32-representable; distance to a boundary
        # is at least half the local ULP.
        sign = 1 if value < 0 else 0
        magnitude = -value if sign else value
        e = magnitude.numerator.bit_length() - magnitude.denominator.bit_length()
        while Fraction(2) ** e > magnitude:
            e -= 1
        while Fraction(2) ** (e + 1) <= magnitude:
            e += 1
        field_exp = max(e, -126)
        ulp = Fraction(2) ** (field_exp - 23)
        return ulp / 2
    return abs(value - lower_fraction)


def fraction_to_decimal(value: Fraction, prec: int) -> Decimal:
    """Convert an exact Fraction to a Decimal correct to `prec` significant digits,
    via exact-integer Decimal division -- never through a Python float, so no
    rounding of the *input* is smuggled in ahead of the transcendental step."""
    context = getcontext()
    original_prec = context.prec
    try:
        context.prec = prec
        return Decimal(value.numerator) / Decimal(value.denominator)
    finally:
        context.prec = original_prec


def decimal_transcendental_with_escape(
    operation,
    value: Fraction,
    *,
    base_prec: int = 40,
    max_prec: int = 320,
):
    """Compute `operation` (``"exp"`` or ``"sqrt"``) of the exact Fraction `value`
    at an escalating precision until the result is provably farther from the
    nearest f32 rounding boundary than the working precision's own error bound
    (Ziv's algorithm).

    The Fraction -> Decimal conversion itself is redone at each trial
    precision (see `fraction_to_decimal`), so no float ever appears anywhere
    in this path -- avoiding double rounding both on the way in and on the
    way out.

    Raises `ReferenceOracleAmbiguousRounding` (fail-closed) rather than
    silently guessing if `max_prec` is exceeded.
    """
    if operation not in ("exp", "sqrt"):
        raise ValueError(f"unsupported operation {operation!r}")
    prec = base_prec
    context = getcontext()
    original_prec = context.prec
    try:
        while prec <= max_prec:
            context.prec = prec
            decimal_input = fraction_to_decimal(value, prec)
            decimal_result = decimal_input.exp() if operation == "exp" else decimal_input.sqrt()
            candidate = decimal_to_fraction(decimal_result)
            # General Decimal Arithmetic Specification bound: a correctly
            # rounded P-digit decimal result is within 0.5*10**-(P-1) relative.
            error_bound = abs(candidate) * Fraction(1, 2) * Fraction(10) ** -(prec - 1)
            if _distance_to_nearest_f32_boundary(candidate) > error_bound:
                return candidate
            prec *= 2
        raise ReferenceOracleAmbiguousRounding(f"could not prove correct rounding within max_prec={max_prec}")
    finally:
        context.prec = original_prec


def softmax_oracle(logits: list[Fraction]) -> tuple[list[Fraction], Fraction]:
    """Returns (probabilities, derived_abs_tolerance) mirroring the shift/exp/sum/divide/cast
    pipeline `crates/forgellm-reference::softmax` actually uses."""
    if not logits:
        raise ValueError("softmax_oracle requires non-empty input")
    shift = max(logits)
    shifted = [value - shift for value in logits]  # exact subtraction

    exponentials = [decimal_transcendental_with_escape("exp", value) for value in shifted]
    total = sum(exponentials, Fraction(0))
    probabilities = [value / total for value in exponentials]

    n = len(logits)
    kappa = LIBM_EXP_ULP_ASSUMPTION
    epsilon = (2 * kappa + n + 2) * F64_EPSILON + F32_CAST_HALF_ULP
    return probabilities, epsilon


def half_ulp_at(value: Fraction) -> Fraction:
    """Half the f32 ULP at the magnitude of `value` -- i.e. the maximum possible
    error a single correctly-rounded f64->f32 narrowing cast can introduce for
    a result of this magnitude. `F32_CAST_HALF_ULP` (2**-24) is only this
    value's special case at magnitude in [1, 2); using it as a global constant
    for outputs of unbounded magnitude (as an earlier draft of this module
    did for `rms_norm_oracle`, and which an empirical test caught: real error
    exceeded that fixed constant once output magnitude exceeded ~1) is wrong.
    """
    if value == 0:
        return Fraction(1, 2**150)
    magnitude = -value if value < 0 else value
    e = magnitude.numerator.bit_length() - magnitude.denominator.bit_length()
    while Fraction(2) ** e > magnitude:
        e -= 1
    while Fraction(2) ** (e + 1) <= magnitude:
        e += 1
    field_exp = max(e, -126)
    return Fraction(2) ** (field_exp - 24)


def rms_norm_oracle(
    values: list[Fraction], weights: list[Fraction], epsilon_param: Fraction
) -> tuple[list[Fraction], list[Fraction]]:
    """Returns (normalized_values, derived_per_element_abs_tolerance).

    Per-element, not one global scalar: rms_norm's output magnitude is not
    bounded to [0, 1] the way softmax's is (it scales with the input/weight
    magnitude), so a single fixed absolute tolerance is only valid near
    magnitude 1 and is wrong wherever the actual output is larger -- this
    was caught empirically by a failing test comparing against real,
    randomly-scaled fixture values before this per-element version replaced
    the earlier fixed-scalar one.

    sqrt and division are IEEE-754 correctly-rounded, so the relative-error
    term (`(n/2 + 4) * F64_EPSILON`, derived from propagating one
    correctly-rounded op's u=2**-53 relative error through square/sum/divide/
    sqrt/divide/multiply) is provable, not assumed; it is also many orders of
    magnitude smaller than the final f64->f32 cast term for any realistic n,
    which is why that cast term dominates and must be magnitude-aware.
    """
    if len(values) != len(weights):
        raise ValueError("rms_norm_oracle requires equal-length values and weights")
    if not values:
        raise ValueError("rms_norm_oracle requires non-empty input")
    n = len(values)
    mean_square = sum((value * value for value in values), Fraction(0)) / n
    variance = mean_square + epsilon_param

    scale = decimal_transcendental_with_escape("sqrt", variance)
    normalized = [(value / scale) * weight for value, weight in zip(values, weights, strict=True)]

    relative_multiplier = Fraction(n, 2) + 4
    tolerances = [relative_multiplier * F64_EPSILON * abs(result) + half_ulp_at(result) for result in normalized]
    return normalized, tolerances
