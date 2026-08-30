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
  representable and comparable at *zero* tolerance. `matmul` accumulates its
  inner-product sum in `f64` before a single final cast to `f32` (the
  fixture generator reconstructs the actual f32-input products, records every
  sequential binary64 partial, and mechanically checks exact finite binary64
  representability -- see `f64_matmul_partial_sums_from_f32` and
  `assert_f64_exact_accumulation` -- rather than checking only a final result).
  Fixture magnitudes are kept small specifically so this precondition is
  satisfied. `elementwise_add`/`elementwise_mul`
  are actually single `f32`-native operations in the real implementation (no
  `f64` promotion at all) -- this makes no difference to the zero-tolerance
  comparison here, since exact-then-round-to-`f32` and direct `f32` arithmetic
  necessarily agree for a lone correctly-rounded add/multiply (Figueroa's
  double-rounding-safety bound: `f64`'s 53 bits comfortably exceed the
  `2*24+2=50`-bit threshold below which routing a single `f32` op through a
  wider intermediate format could ever change the result).

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


def f64_matmul_partial_sums_from_f32(
    lhs: list[list[Fraction]], rhs: list[list[Fraction]]
) -> list[list[list[Fraction]]]:
    """Return every sequential binary64 accumulator state for an f32-input matmul.

    The inputs must be exact f32 values represented as ``Fraction`` instances. Each product
    and addition is performed by Python's binary64 ``float`` arithmetic, then converted back
    to an exact Fraction from ``as_integer_ratio``. The nested result is indexed as
    ``[output_row][output_column][partial_index]`` and therefore preserves the actual
    left-to-right accumulation trace that a Rust ``f64`` fold uses. This is intentionally a
    proof helper for small deterministic fixtures, not a replacement production matmul.
    """
    matmul_exact(lhs, rhs)  # validates rank, rectangularity and inner dimensions once.
    for row_index, row in enumerate(lhs):
        for column_index, value in enumerate(row):
            bits = fraction_to_f32_bits(value)
            if f32_bits_to_fraction(bits) != value:
                raise ValueError(
                    f"f64_matmul_partial_sums_from_f32 lhs[{row_index}][{column_index}] "
                    "is not an exact finite f32 value"
                )
    for row_index, row in enumerate(rhs):
        for column_index, value in enumerate(row):
            bits = fraction_to_f32_bits(value)
            if f32_bits_to_fraction(bits) != value:
                raise ValueError(
                    f"f64_matmul_partial_sums_from_f32 rhs[{row_index}][{column_index}] "
                    "is not an exact finite f32 value"
                )

    inner = len(lhs[0])
    columns = len(rhs[0])
    traces: list[list[list[Fraction]]] = []
    for lhs_row in lhs:
        output_row: list[list[Fraction]] = []
        for column in range(columns):
            accumulator = 0.0
            partials: list[Fraction] = []
            for index in range(inner):
                accumulator += float(lhs_row[index]) * float(rhs[index][column])
                if not math.isfinite(accumulator):
                    raise ReferenceOracleAmbiguousRounding(
                        "f64_matmul_partial_sums_from_f32 produced a non-finite "
                        f"accumulator at output column {column}, partial {index}"
                    )
                partials.append(Fraction(*accumulator.as_integer_ratio()))
            output_row.append(partials)
        traces.append(output_row)
    return traces


def transpose_exact(matrix: list[list[Fraction]]) -> list[list[Fraction]]:
    """Exact rank-two transpose. Pure rearrangement of already-exact Fractions -- no
    arithmetic occurs, so there is zero rounding to reason about, exactly like
    `embedding_gather_exact`."""
    if not matrix:
        raise ValueError("transpose_exact requires a non-empty matrix")
    width = len(matrix[0])
    if any(len(row) != width for row in matrix):
        raise ValueError("transpose_exact requires a rectangular matrix")
    return [[matrix[row][col] for row in range(len(matrix))] for col in range(width)]


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
    """Mechanically verify every sequential accumulator state is exactly finite binary64.

    ``partial_sums`` must be the left-to-right accumulator trace from the actual f32-input
    products, not merely the final exact result. A value is binary64-exact only when its
    reduced denominator is a power of two, its normalized significand fits the 53-bit
    precision of a normal value, and its exponent is within the normal or subnormal range.
    Fails closed rather than silently emitting a fixture whose exact comparison does not match
    Rust's f64 accumulation.
    """
    for index, partial in enumerate(partial_sums):
        if partial == 0:
            continue

        denominator = partial.denominator
        if denominator & (denominator - 1):
            raise ReferenceOracleAmbiguousRounding(
                f"{context}: partial[{index}]={partial} is not a dyadic value and cannot be "
                "represented exactly as binary64"
            )

        numerator = abs(partial.numerator)
        denominator_exponent = denominator.bit_length() - 1
        exponent = numerator.bit_length() - 1 - denominator_exponent
        odd_numerator = numerator
        while odd_numerator % 2 == 0:
            odd_numerator //= 2
        significant_bits = odd_numerator.bit_length()

        if exponent > 1023:
            raise ReferenceOracleAmbiguousRounding(
                f"{context}: partial[{index}]={partial} exceeds the finite binary64 exponent "
                "range; reduce fixture magnitude or dimension"
            )
        if exponent < -1022:
            if denominator_exponent > 1074:
                raise ReferenceOracleAmbiguousRounding(
                    f"{context}: partial[{index}]={partial} is below the exact binary64 "
                    "subnormal quantum; reduce fixture magnitude"
                )
        elif significant_bits > 53:
            raise ReferenceOracleAmbiguousRounding(
                f"{context}: partial[{index}]={partial} needs {significant_bits} significant "
                "bits, exceeding binary64's 53-bit precision"
            )


# ---------------------------------------------------------------------------
# Decimal-based ops with derived, escalating precision: softmax, rms_norm.
# ---------------------------------------------------------------------------


def _margin_to_nearest_rounding_boundary(value: Fraction) -> Fraction:
    """How far `value` sits from the nearest f32 rounding *tie* (the halfway
    point between two adjacent representable values) -- the safety margin
    the Ziv escape check in `decimal_transcendental_with_escape` needs.

    LARGE means `value` is safely far from any tie, so which f32 it rounds
    to is unambiguous even if `value` itself has some residual imprecision.
    SMALL (near zero) means `value` sits dangerously close to a tie, where a
    tiny error in `value` could flip which neighbor is actually closer --
    exactly the case that must trigger a precision escalation, not a
    confident answer.

    An earlier version of this function returned `abs(value - nearest)` --
    the residual from `value` to its own rounded neighbor -- which moves in
    the *opposite* direction from safety: that residual is *small* when
    `value` sits close to one specific representable point (genuinely safe)
    and grows toward `half_ulp` as `value` approaches a tie (genuinely
    dangerous), so the escape check's `> error_bound` comparison was
    accepting exactly the inputs it should have escalated, and vice versa.
    Confirmed by construction: values placed within 2**-135 of a real f32
    tie were confidently accepted without escalation under the old logic.
    This version returns `half_ulp - residual`, which has the correct sign
    in both directions.
    """
    nearest_bits = fraction_to_f32_bits(value)
    nearest = f32_bits_to_fraction(nearest_bits)
    if nearest is None:
        # `value` is so large it rounds to +/-infinity. That is itself an
        # unambiguous rounding decision in every practical case this module
        # exercises (softmax/rms_norm operate on normalized magnitudes far
        # from the overflow boundary) -- treat it as maximally safe rather
        # than attempt a finite margin computation against a boundary that
        # does not exist in finite f32 space.
        return Fraction(2**128)
    return half_ulp_at(nearest) - abs(value - nearest)


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
            if _margin_to_nearest_rounding_boundary(candidate) > error_bound:
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
    term is provable, not assumed. It is derived by propagating one
    correctly-rounded op's u=2**-53 relative error through
    square/sum/divide/sqrt, giving roughly `(n/2 + 2) * u` at the scale
    factor. The real Rust `rms_norm` then computes `inverse_rms = 1/sqrt(...)`
    once and multiplies (`value * inverse_rms * weight`) rather than dividing
    each value by the scale directly -- two correctly-rounded operations
    (reciprocal, then multiply) where this oracle's `value / scale` uses one.
    That is a real, deliberate difference: computing an f64-rounded
    reciprocal here would introduce an f64 rounding step into what is
    otherwise an exact/high-precision pipeline, contradicting this module's
    purpose. The two extra `+u` terms below (`+ 5` rather than `+ 2`)
    conservatively cover that gap rather than silently assuming the two
    computation orders are equivalent; empirically (10,000+ randomized
    trials spanning n up to 64 and magnitudes from 1e-3 to 1e4 during
    review) the true gap is far smaller than this margin, so `+ 5` is
    intentionally generous, not tuned to just barely pass. This relative
    term is many orders of magnitude smaller than the final f64->f32 cast
    term for any realistic n, which is why that cast term dominates and
    must be magnitude-aware.
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

    relative_multiplier = Fraction(n, 2) + 5
    tolerances = [relative_multiplier * F64_EPSILON * abs(result) + half_ulp_at(result) for result in normalized]
    return normalized, tolerances


# ---------------------------------------------------------------------------
# Single-query scaled dot-product attention (P0-T19).
# ---------------------------------------------------------------------------


def attention_oracle(
    query: list[Fraction], keys: list[list[Fraction]], values: list[list[Fraction]]
) -> tuple[list[Fraction], list[Fraction]]:
    """Returns (context_vector, derived_per_element_abs_tolerance) for
    `crates/forgellm-reference::attention_decode_single_query`'s exact composition:
    matmul/transpose for the raw scores, one f64-domain-multiply-cast-once-to-f32 scale by
    `1/sqrt(head_dim)`, the existing softmax_oracle, then matmul again for the weighted sum.

    The returned tolerance applies to the *context vector itself*, since that is the only
    value `attention_decode_single_query` actually returns -- a Rust-side fixture-driven test
    has no way to observe or compare the intermediate scores or probabilities directly, so a
    tolerance derived for an intermediate quantity (an earlier draft of this function computed
    exactly that mistake) would not describe anything the contract test can check.

    Tolerance derivation (full rationale in
    docs/superpowers/specs/2026-08-28-p0-t19-attention-design.md):

    0. **Every intermediate value real Rust actually holds as an `f32` is rounded to `f32`
       here too, explicitly, before being used for the next step** (`raw_scores` right after
       the first `matmul`; `scaled` right after the scale multiply). An earlier draft of this
       function skipped this and fed `softmax_oracle` the *unrounded* exact `Fraction` scores
       instead -- which is a strictly more precise input than real Rust's `softmax` call
       actually receives, so `softmax_oracle`'s own epsilon (which bounds *its own* internal
       rounding relative to whatever input it is given) silently stopped bounding anything
       about the real gap to Rust. Concretely caught by a randomized cross-check: a
       `context_len=2, head_dim=1` case where the true product needed 48 mantissa bits (every
       normal f32-times-f32 product does) violated the derived tolerance by ~3.4x before this
       fix, and holds comfortably (~70x margin) after it. This is exactly why every rounding
       step in this module is meant to be explicit, never implicit -- see the module docstring.
    1. With that rounding applied, `raw_scores` matches the real Rust value *exactly*, under
       the same mechanically-checked f64-exact-accumulation precondition every other
       `matmul_exact` caller in this module already relies on (a lone product of two f32
       values is always within this precondition, needing at most 48 significant bits;
       longer dot products are not, in general -- see the caller precondition note below).
    2. The scale step's own rounding gap (the real `1.0f64/(head_dim as f64).sqrt()` versus
       this oracle's near-exact reciprocal of an already-Ziv-escape-verified sqrt) is at most a
       couple of correctly-rounded f64 relative-error terms (~2*`F64_EPSILON`) -- many orders
       of magnitude below the f32 cast's own half-ULP, so it is dropped as provably negligible
       rather than silently ignored (the same dominated-term argument `rms_norm_oracle` already
       makes for its own reciprocal-vs-divide gap); the explicit rounding in step 0 is what
       then makes `scaled` match real Rust's own value, to that same excellent approximation.
    3. `softmax_oracle`'s own already-derived `epsilon` is therefore the real per-element
       absolute error on `probabilities` relative to this oracle's values -- reused completely
       unmodified, not re-derived, and now actually describing the real gap (see step 0).
    4. That per-probability error is propagated, worst-case-linearly (triangle inequality) with no
       assumption of cancellation, through the final `matmul(probabilities, values)`:
       `context[k]`'s error from this source is bounded by `epsilon * sum_j abs(values[j][k])`
       (call this `B`), plus *two* `half_ulp_at`-scale terms for the two independent f64->f32
       narrowing casts now in play -- the real Rust value's own cast, and the comparand's cast
       when a caller rounds this function's exact `context[k]` to build a fixture value -- unlike
       `matmul_exact`'s other callers, neither cast is covered by the zero-tolerance
       exact-accumulation treatment here, because `probabilities` are no longer exact inputs by
       the time they reach this matmul. An independent adversarial reviewer proved algebraically
       that `B` alone already strictly exceeds one `half_ulp_at(context[k])` term (since
       softmax's convex-combination property gives `abs(context[k]) <= sum_j abs(values[j][k])`,
       and `epsilon > F32_CAST_HALF_ULP` strictly), and confirmed it empirically against the
       *compiled* Rust binary with thousands of deliberately tie-adjacent adversarial
       constructions -- zero violations, but with worst-case observed margins as tight as
       `delta/tolerance = 0.9988` at `B + 1*half_ulp_at(context[k])`. A margin that thin on a
       claimed-safe numerical bound is precisely the risk profile that produced this module's
       own P0-T18 BLOCKER (a different tight-margin assumption that turned out to have a sign
       error) -- rather than ship a bound whose correctness rests on a razor-thin proved
       inequality, this function includes the *second* `half_ulp_at(context[k])` term the naive
       triangle-inequality bound already calls for, giving real headroom instead of a knife's
       edge. This is the same "derive honestly, then pad deliberately rather than tune to just
       barely pass" choice `rms_norm_oracle` already makes for its own reciprocal-vs-divide gap.

    Caller-visible precondition, inherited from step 1 (this function does *not* assert it
    itself, matching `softmax_oracle`/`rms_norm_oracle`'s existing precondition-free style --
    unlike them, though, this function's tolerance derivation genuinely depends on it): the
    returned tolerance is only proven to bound the real Rust value when the dot product behind
    every entry of `raw_scores` and the final weighted sum behind every entry of `context` each
    individually satisfy the exact finite-binary64 condition. The generator enforces this by
    reconstructing the f64 folds from the actual rounded f32 operands, checking every partial
    sum rather than only the final value; for the final fold it uses the f32 probabilities
    produced by the same f64 exp/divide/cast sequence. This always holds for a single-term dot
    product (`head_dim == 1`, at most 48 significant bits) regardless of magnitude; for longer
    dot products it holds for every committed fixture case and for any input built from small,
    low-bit-count f32 values, but is not proven for arbitrary full-mantissa f32 inputs at large
    `context_len`/`head_dim`. This function does not fail closed if that precondition is violated
    -- it will simply return a tolerance that may understate the true error. Random/property-
    based testing against this function must therefore also respect that precondition (small
    dimensions, or quantized inputs at larger ones), not sample fully arbitrary floats at large
    dimensions.
    """
    if not keys or not values:
        raise ValueError("attention_oracle requires non-empty keys and values")
    head_dim = len(query)
    context_len = len(keys)
    if any(len(row) != head_dim for row in keys):
        raise ValueError("attention_oracle requires every key row to match query's head_dim")
    if len(values) != context_len:
        raise ValueError("attention_oracle requires keys and values to share one context length")

    def _round_to_f32(value: Fraction) -> Fraction:
        return f32_bits_to_fraction(fraction_to_f32_bits(value))

    # No `assert_f64_exact_accumulation` call here, deliberately: this function computes a
    # *derived tolerance* (like `softmax_oracle`/`rms_norm_oracle`), not a zero-tolerance exact
    # result, so unlike `matmul_exact`'s direct callers it carries no precondition of its own.
    # The derivation above (step 1) assumes `raw_scores`/`context` are exact under the
    # exact-accumulation precondition; the *caller* is responsible for that check when it wants
    # to treat this function's output as a zero-tolerance-safe fixture value (the fixture
    # generator does so explicitly from actual f32 operand traces, exactly like it already does
    # for the other exact ops).
    raw_scores = matmul_exact([query], transpose_exact(keys))[0]
    raw_scores = [_round_to_f32(score) for score in raw_scores]  # matches matmul's own cast

    sqrt_head_dim = decimal_transcendental_with_escape("sqrt", Fraction(head_dim))
    scale = Fraction(1) / sqrt_head_dim
    scaled = [_round_to_f32(score * scale) for score in raw_scores]  # matches the scale step's own cast

    probabilities, softmax_epsilon = softmax_oracle(scaled)

    context = matmul_exact([probabilities], values)[0]

    tolerances = [
        softmax_epsilon * sum(abs(values[row][column]) for row in range(context_len))
        + 2 * half_ulp_at(context[column])  # two independent casts; see docstring step 4
        for column in range(head_dim)
    ]
    return context, tolerances


# Multi-query scaled dot-product attention (P0-T20).
# ---------------------------------------------------------------------------


def multi_query_attention_oracle(
    queries: list[list[Fraction]], keys: list[list[Fraction]], values: list[list[Fraction]]
) -> tuple[list[list[Fraction]], list[list[Fraction]]]:
    """Return per-query contexts and matching per-element tolerances.

    The Rust `attention_decode_multi_query` operation has one shared key/value context but a
    distinct score vector and softmax denominator for every query row. Calling the reviewed
    `attention_oracle` composition once per row mirrors that boundary exactly: raw scores and
    scaled scores are rounded to f32 before each row's softmax, and the existing derived softmax
    budget is propagated through that row's final weighted sum. The returned matrices have shape
    `[query_count][head_dim]`; no tolerance or intermediate probability is shared across rows.

    Query rows must form a non-empty rectangular matrix with a non-zero width, matching the
    non-zero rank-two dimensions accepted by the Rust `Tensor` constructor. Key/value validation
    and the exact-accumulation precondition remain those documented by `attention_oracle`.
    """
    if not queries or not queries[0]:
        raise ValueError("multi_query_attention_oracle requires non-empty queries")
    head_dim = len(queries[0])
    if any(len(row) != head_dim for row in queries):
        raise ValueError("multi_query_attention_oracle requires rectangular queries")
    if any(len(row) != head_dim for row in values):
        raise ValueError("multi_query_attention_oracle requires values with query head_dim")

    contexts: list[list[Fraction]] = []
    tolerances: list[list[Fraction]] = []
    for query in queries:
        context, query_tolerances = attention_oracle(query, keys, values)
        contexts.append(context)
        tolerances.append(query_tolerances)
    return contexts, tolerances
