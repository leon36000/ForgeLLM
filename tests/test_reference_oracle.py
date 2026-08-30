"""Tests for the stdlib-only differential reference oracle.

The round-trip property test is the load-bearing correctness net for
`fraction_to_f32_bits`: since the function contains no irrational
computation, it is fully deterministic and exhaustively characterizable by
property, not by a fixed table of examples.
"""

from __future__ import annotations

import math
import random
import struct
from fractions import Fraction

import pytest

# _margin_to_nearest_rounding_boundary is private; importing it directly is
# deliberate here, to regression-test the exact function a real reviewer
# found inverted (see test_margin_to_rounding_boundary_shrinks_toward_a_real_tie
# and test_escape_mechanism_does_not_confidently_misresolve_near_a_tie below).
from forgellm_governance.reference_oracle import (
    F32_CAST_HALF_ULP,
    ReferenceOracleAmbiguousRounding,
    _margin_to_nearest_rounding_boundary,
    assert_f64_exact_accumulation,
    attention_oracle,
    decimal_to_fraction,
    decimal_transcendental_with_escape,
    elementwise_add_exact,
    elementwise_mul_exact,
    embedding_gather_exact,
    f32_bits_to_fraction,
    f64_matmul_partial_sums_from_f32,
    fraction_to_decimal,
    fraction_to_f32_bits,
    matmul_exact,
    multi_query_attention_oracle,
    rms_norm_oracle,
    softmax_oracle,
    transpose_exact,
)


def _f32(value: float) -> float:
    """Round a Python float through f32 precision, matching Rust's `as f32` cast."""
    return struct.unpack("<f", struct.pack("<f", value))[0]


def _bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


# ---------------------------------------------------------------------------
# f32_bits_to_fraction / fraction_to_f32_bits round-trip.
# ---------------------------------------------------------------------------


class TestF32FractionRoundTrip:
    def test_nan_and_infinity_are_not_representable(self):
        assert f32_bits_to_fraction(_bits(float("nan"))) is None
        assert f32_bits_to_fraction(_bits(float("inf"))) is None
        assert f32_bits_to_fraction(_bits(float("-inf"))) is None

    def test_positive_and_negative_zero(self):
        assert fraction_to_f32_bits(Fraction(0)) == 0
        # Fraction has no signed zero; this is a documented limitation, not a
        # round-trip bug: -0.0 -> Fraction(0) -> 0x00000000 (+0), not -0.0's
        # bit pattern. Verified explicitly here rather than left implicit.
        assert f32_bits_to_fraction(_bits(-0.0)) == Fraction(0)

    @pytest.mark.parametrize(
        "value",
        [
            1.0,
            -1.0,
            0.5,
            -0.5,
            2.0,
            3.14159,
            1e10,
            1e-10,
            123456.789,
        ],
    )
    def test_round_trip_ordinary_values(self, value):
        bits = _bits(value)
        fraction = f32_bits_to_fraction(bits)
        assert fraction is not None
        assert fraction_to_f32_bits(fraction) == bits

    def test_round_trip_smallest_subnormal(self):
        bits = 1  # smallest positive subnormal
        fraction = f32_bits_to_fraction(bits)
        assert fraction == Fraction(1, 2**149)
        assert fraction_to_f32_bits(fraction) == bits

    def test_round_trip_largest_subnormal(self):
        bits = 0x007FFFFF
        fraction = f32_bits_to_fraction(bits)
        assert fraction_to_f32_bits(fraction) == bits

    def test_round_trip_smallest_normal(self):
        bits = 0x00800000
        fraction = f32_bits_to_fraction(bits)
        assert fraction_to_f32_bits(fraction) == bits

    def test_round_trip_largest_finite(self):
        bits = 0x7F7FFFFF  # f32::MAX
        fraction = f32_bits_to_fraction(bits)
        assert fraction_to_f32_bits(fraction) == bits

    def test_round_trip_negative_largest_finite(self):
        bits = 0xFF7FFFFF  # -f32::MAX
        fraction = f32_bits_to_fraction(bits)
        assert fraction_to_f32_bits(fraction) == bits

    def test_overflow_rounds_to_infinity(self):
        # A magnitude larger than the largest finite f32 must map to infinity's
        # bit pattern (exponent field all-ones, zero mantissa), sign preserved.
        huge = Fraction(2) ** 200
        assert fraction_to_f32_bits(huge) == (0xFF << 23)
        assert fraction_to_f32_bits(-huge) == (1 << 31) | (0xFF << 23)

    def test_round_up_overflow_at_max_finite_boundary(self):
        # A value just above f32::MAX's own value, but still below the next
        # representable step past it, must round UP to infinity (round-half-
        # to-even at the top boundary rounds away, since there is no even
        # finite candidate to round down to that is closer).
        max_finite = f32_bits_to_fraction(0x7F7FFFFF)
        ulp_at_max = Fraction(2) ** (127 - 23)
        just_above = max_finite + ulp_at_max  # exceeds representable range
        assert fraction_to_f32_bits(just_above) == (0xFF << 23)

    def test_underflow_to_zero_below_half_smallest_subnormal(self):
        tiny = Fraction(1, 2**151)  # well below half the smallest subnormal
        assert fraction_to_f32_bits(tiny) == 0

    def test_round_up_to_smallest_subnormal(self):
        # Strictly above the halfway point between 0 and the smallest
        # subnormal (2**-150) must round UP, not truncate to zero.
        above_half = Fraction(1, 2**150) + Fraction(1, 2**200)
        assert fraction_to_f32_bits(above_half) == 1

    def test_exact_tie_at_zero_boundary_rounds_to_even_zero(self):
        # Exactly at the halfway point (2**-150): mantissa=0 is even, so
        # round-half-to-even keeps it at zero, not the smallest subnormal.
        exact_half = Fraction(1, 2**150)
        assert fraction_to_f32_bits(exact_half) == 0

    def test_subnormal_rounds_up_into_normal_range(self):
        # Construct a value strictly between the largest subnormal and the
        # smallest normal, closer to the smallest normal, forcing a
        # subnormal-to-normal carry.
        largest_subnormal = f32_bits_to_fraction(0x007FFFFF)
        smallest_normal = f32_bits_to_fraction(0x00800000)
        near_normal = largest_subnormal + (smallest_normal - largest_subnormal) * Fraction(999, 1000)
        result_bits = fraction_to_f32_bits(near_normal)
        assert result_bits == 0x00800000

    @pytest.mark.parametrize("mantissa_parity", ["even", "odd"])
    def test_exact_tie_round_half_to_even_both_parities(self, mantissa_parity):
        # Build an exact f32 value, then add exactly half its ULP: an exact
        # tie must round to whichever neighbor has an even mantissa field.
        base_bits = 0x3F800000 if mantissa_parity == "even" else 0x3F800001  # 1.0 vs next-up
        base = f32_bits_to_fraction(base_bits)
        exponent = 0 if mantissa_parity == "even" else 0
        half_ulp = Fraction(2) ** (exponent - 24)
        tie = base + half_ulp
        result_bits = fraction_to_f32_bits(tie)
        # Whichever of base_bits/base_bits+1 the tie resolves to, the winning
        # mantissa field must be even.
        assert (result_bits & 1) == 0

    def test_round_trip_random_sample(self):
        rng = random.Random(20260828)
        mismatches = []
        for _ in range(20000):
            bits = rng.getrandbits(32)
            fraction = f32_bits_to_fraction(bits)
            if fraction is None:  # skip NaN/Inf patterns, no rational value
                continue
            round_tripped = fraction_to_f32_bits(fraction)
            if round_tripped != bits:
                mismatches.append((bits, fraction, round_tripped))
        assert not mismatches, f"{len(mismatches)} round-trip mismatches, e.g. {mismatches[:5]}"

    def test_round_trip_all_exponent_boundaries(self):
        # Every stored exponent value (0..254, excluding 255=inf/nan), with a
        # handful of mantissa/sign combinations each -- not exhaustive over
        # all 2**32 patterns, but exhaustive over every exponent field.
        NEGATIVE_ZERO_BITS = 0x80000000  # documented limitation, see test_positive_and_negative_zero
        mismatches = []
        for stored_exp in range(0, 255):
            for mantissa in (0, 1, 0x3FFFFF, 0x400000, 0x7FFFFE, 0x7FFFFF):
                for sign in (0, 1):
                    bits = (sign << 31) | (stored_exp << 23) | mantissa
                    if bits == NEGATIVE_ZERO_BITS:
                        continue
                    fraction = f32_bits_to_fraction(bits)
                    assert fraction is not None
                    round_tripped = fraction_to_f32_bits(fraction)
                    if round_tripped != bits:
                        mismatches.append((bits, fraction, round_tripped))
        assert not mismatches, f"{len(mismatches)} mismatches across exponent boundaries: {mismatches[:5]}"


# ---------------------------------------------------------------------------
# Exact-Fraction ops agree with f64-accumulate-then-cast-to-f32, for small
# fixture-scale magnitudes (the precondition the fixture generator enforces).
# ---------------------------------------------------------------------------


class TestExactOpsAgreeWithF64Path:
    def test_elementwise_add_matches_f32_cast_of_f64_sum(self):
        rng = random.Random(7)
        for _ in range(2000):
            a = _f32(rng.uniform(-8, 8))
            b = _f32(rng.uniform(-8, 8))
            exact = elementwise_add_exact([f32_bits_to_fraction(_bits(a))], [f32_bits_to_fraction(_bits(b))])
            expected_bits = _bits(_f32(a + b))
            assert fraction_to_f32_bits(exact[0]) == expected_bits

    def test_elementwise_mul_matches_f32_cast_of_f64_product(self):
        rng = random.Random(11)
        for _ in range(2000):
            a = _f32(rng.uniform(-8, 8))
            b = _f32(rng.uniform(-8, 8))
            exact = elementwise_mul_exact([f32_bits_to_fraction(_bits(a))], [f32_bits_to_fraction(_bits(b))])
            expected_bits = _bits(_f32(a * b))
            assert fraction_to_f32_bits(exact[0]) == expected_bits

    def test_matmul_matches_f32_cast_of_f64_accumulation(self):
        rng = random.Random(13)
        for _ in range(500):
            lhs = [[_f32(rng.uniform(-8, 8)) for _ in range(4)] for _ in range(3)]
            rhs = [[_f32(rng.uniform(-8, 8)) for _ in range(3)] for _ in range(4)]
            lhs_fraction = [[f32_bits_to_fraction(_bits(v)) for v in row] for row in lhs]
            rhs_fraction = [[f32_bits_to_fraction(_bits(v)) for v in row] for row in rhs]
            exact = matmul_exact(lhs_fraction, rhs_fraction)

            for i in range(3):
                for j in range(3):
                    acc = 0.0
                    for k in range(4):
                        acc += lhs[i][k] * rhs[k][j]  # f64 accumulation, Python float is f64
                    expected_bits = _bits(_f32(acc))
                    assert fraction_to_f32_bits(exact[i][j]) == expected_bits

    def test_embedding_gather_preserves_order_and_repetition(self):
        table = [[Fraction(1)], [Fraction(2)], [Fraction(3)]]
        result = embedding_gather_exact(table, [2, 0, 2, 1])
        assert result == [[Fraction(3)], [Fraction(1)], [Fraction(3)], [Fraction(2)]]

    def test_embedding_gather_rejects_out_of_range(self):
        table = [[Fraction(1)]]
        out_of_range_token_ids = [5]
        with pytest.raises(ValueError):
            embedding_gather_exact(table, out_of_range_token_ids)

    def test_transpose_exact_matches_hand_computed_result(self):
        matrix = [[Fraction(1), Fraction(2), Fraction(3)], [Fraction(4), Fraction(5), Fraction(6)]]
        assert transpose_exact(matrix) == [
            [Fraction(1), Fraction(4)],
            [Fraction(2), Fraction(5)],
            [Fraction(3), Fraction(6)],
        ]

    def test_transpose_exact_is_its_own_inverse(self):
        matrix = [[Fraction(1), Fraction(2), Fraction(3)], [Fraction(4), Fraction(5), Fraction(6)]]
        assert transpose_exact(transpose_exact(matrix)) == matrix

    def test_transpose_exact_rejects_ragged_matrix(self):
        ragged = [[Fraction(1), Fraction(2)], [Fraction(3)]]
        with pytest.raises(ValueError):
            transpose_exact(ragged)


class TestF64AccumulationProof:
    def test_guard_rejects_non_dyadic_intermediate_even_when_final_is_zero(self):
        with pytest.raises(ReferenceOracleAmbiguousRounding, match="dyadic"):
            assert_f64_exact_accumulation([Fraction(1, 3), Fraction(0)], context="masked_final")

    def test_guard_accepts_exact_power_of_two_at_53_bit_exponent(self):
        assert_f64_exact_accumulation([Fraction(2**53)], context="large_power_of_two")

    def test_guard_rejects_a_54_bit_normal_significand(self):
        with pytest.raises(ReferenceOracleAmbiguousRounding, match="54 significant bits"):
            assert_f64_exact_accumulation([Fraction(2**53 + 1)], context="wide_significand")

    def test_f32_matmul_trace_preserves_each_binary64_partial(self):
        lhs = [[f32_bits_to_fraction(_bits(1.5)), f32_bits_to_fraction(_bits(-0.5))]]
        rhs = [[f32_bits_to_fraction(_bits(2.0))], [f32_bits_to_fraction(_bits(4.0))]]

        traces = f64_matmul_partial_sums_from_f32(lhs, rhs)

        assert traces == [[[Fraction(3), Fraction(1)]]]

    def test_f32_matmul_trace_rejects_non_f32_fraction_inputs(self):
        with pytest.raises(ValueError, match="exact finite f32"):
            f64_matmul_partial_sums_from_f32([[Fraction(1, 3)]], [[Fraction(1)]])


# ---------------------------------------------------------------------------
# Decimal/Fraction transcendental oracle: agreement with f64 libm, and the
# Ziv escape mechanism.
# ---------------------------------------------------------------------------


class TestTranscendentalOracle:
    def test_exp_agrees_with_math_exp_within_derived_budget(self):
        rng = random.Random(17)
        for _ in range(500):
            x = rng.uniform(-30, 0)
            exact = decimal_transcendental_with_escape("exp", Fraction(x))
            libm = math.exp(x)
            delta = abs(float(exact) - libm)
            assert delta < 1e-9, f"x={x} exact={float(exact)} libm={libm} delta={delta}"

    def test_sqrt_agrees_with_math_sqrt_exactly_within_f64_rounding(self):
        rng = random.Random(19)
        for _ in range(500):
            x = rng.uniform(0.0001, 1000)
            exact = decimal_transcendental_with_escape("sqrt", Fraction(x))
            libm = math.sqrt(x)
            delta = abs(float(exact) - libm)
            assert delta < 1e-12, f"x={x} exact={float(exact)} libm={libm} delta={delta}"

    def test_escape_raises_when_max_prec_is_below_the_type_minimum(self):
        # base_prec=1 cannot possibly prove correct rounding to 24 bits (needs
        # ~7.3 decimal digits at minimum); with max_prec equal to base_prec,
        # the loop gets exactly one, insufficient attempt and must raise
        # rather than return an unproven low-precision guess.
        insufficient_value = Fraction(-1, 2)
        with pytest.raises(ReferenceOracleAmbiguousRounding):
            decimal_transcendental_with_escape("exp", insufficient_value, base_prec=1, max_prec=1)

    def test_escape_mechanism_is_reachable(self):
        # Directly exercise the precision-doubling loop by starting so low
        # that at least one escalation is required, and confirm it still
        # converges to the correct answer rather than returning a
        # low-precision guess.
        exact = decimal_transcendental_with_escape("exp", Fraction(-1, 2), base_prec=1, max_prec=320)
        libm = math.exp(-0.5)
        assert abs(float(exact) - libm) < 1e-9

    def test_fraction_to_decimal_never_touches_float(self):
        # A Fraction whose float() conversion would be lossy (huge
        # numerator/denominator) must still convert correctly via exact
        # integer division, proving no float ever appears in the path.
        odd_fraction = Fraction(10**30 + 1, 3)
        decimal_value = fraction_to_decimal(odd_fraction, prec=50)
        back = decimal_to_fraction(decimal_value)
        # Should match to the requested precision, not be corrupted by a
        # float round-trip (float(odd_fraction) would already have lost
        # precision before decimal ever saw it, if float() were used).
        relative_error = abs(back - odd_fraction) / abs(odd_fraction)
        assert relative_error < Fraction(1, 10**48)

    def test_margin_to_rounding_boundary_shrinks_toward_a_real_tie(self):
        # Regression test for a real BLOCKER found by an independent
        # reviewer (and reproduced here): an earlier version of this
        # function returned `abs(value - nearest)` -- the residual from
        # `value` to its own rounded neighbor -- which moves in the
        # *opposite* direction from safety (it is near `half_ulp` exactly
        # when `value` sits near a tie, and near 0 when `value` sits near
        # one specific representable point). The escape check's `>
        # error_bound` comparison was therefore accepting the inputs it
        # should have escalated, and vice versa. Confirmed: values placed
        # within 2**-135 of a real f32 tie were confidently, silently
        # resolved to the wrong bit pattern under the old logic (1063/4000
        # in the reviewer's adversarial battery).
        lo = f32_bits_to_fraction(0x3F800000)  # 1.0
        hi = f32_bits_to_fraction(0x3F800001)  # next float up
        tie = (lo + hi) / 2
        # Exponents chosen well above f32's own ULP scale at this magnitude
        # (half_ulp here is 2**-24 =~ 5.96e-8, i.e. exponent ~24): anything
        # coarser than that would land outside the [lo, hi] interval
        # entirely and compare against an unrelated neighbor, not exercise
        # "close to this specific tie" at all.
        margins = [
            float(_margin_to_nearest_rounding_boundary(tie + Fraction(1, 2**exponent)))
            for exponent in (30, 50, 70, 100, 130)
        ]
        # Must be monotonically non-increasing as the offset from the tie
        # shrinks (i.e. as the candidate gets closer to the danger zone).
        assert all(earlier >= later for earlier, later in zip(margins, margins[1:], strict=False)), margins
        # And must approach zero, not `half_ulp`, as the offset vanishes.
        assert margins[-1] < 1e-30, margins

    def test_escape_mechanism_does_not_confidently_misresolve_near_a_tie(self):
        # Direct reproduction of the reviewer's adversarial battery at the
        # module's real base_prec=40: construct candidates within
        # 2**-128..2**-138 of a genuine f32 tie and confirm the escape
        # check never both (a) declares confidence and (b) is wrong.
        rng = random.Random(2026)
        tested = 0
        confidently_wrong = 0
        for _ in range(2000):
            base_bits = rng.randint(0x3F000000, 0x41000000)
            lo_bits, hi_bits = base_bits, base_bits + 1
            lo = f32_bits_to_fraction(lo_bits)
            hi = f32_bits_to_fraction(hi_bits)
            if lo is None or hi is None:
                continue
            tie = (lo + hi) / 2
            exponent = rng.randint(128, 138)
            sign = rng.choice([1, -1])
            candidate = tie + sign * Fraction(1, 2**exponent)
            correct_bits = fraction_to_f32_bits(candidate)
            expected_bits = hi_bits if sign > 0 else lo_bits
            if correct_bits != expected_bits:
                continue  # construction sanity check failed; skip
            tested += 1

            error_bound = abs(candidate) * Fraction(1, 2) * Fraction(10) ** -(40 - 1)
            margin = _margin_to_nearest_rounding_boundary(candidate)
            confidently_accepted = margin > error_bound
            if confidently_accepted and correct_bits != expected_bits:
                confidently_wrong += 1
        assert tested > 1000, "construction sanity check itself may be broken"
        assert confidently_wrong == 0, f"{confidently_wrong}/{tested} confidently wrong near a real tie"


# ---------------------------------------------------------------------------
# End-to-end: softmax_oracle / rms_norm_oracle agree with the crate's actual
# f64-then-cast-f32 pipeline within their own derived budgets.
# ---------------------------------------------------------------------------


class TestEndToEndOracles:
    def test_softmax_oracle_matches_f64_softmax_within_derived_budget(self):
        rng = random.Random(23)
        for _ in range(200):
            logits_f32 = [_f32(rng.uniform(-8, 8)) for _ in range(5)]
            logits_fraction = [f32_bits_to_fraction(_bits(v)) for v in logits_f32]

            probabilities, epsilon = softmax_oracle(logits_fraction)

            shift = max(logits_f32)
            exp_values = [math.exp(v - shift) for v in logits_f32]
            total = sum(exp_values)
            expected = [_f32(v / total) for v in exp_values]

            for got, want in zip(probabilities, expected, strict=True):
                delta = abs(float(got) - want)
                assert delta <= float(epsilon), f"delta={delta} epsilon={float(epsilon)}"

    def test_softmax_oracle_matches_existing_crate_contract_extreme_shift(self):
        # Mirrors crates/forgellm-reference/tests/numerical_contract.rs
        # softmax_extreme_shift_remains_finite_and_bounded.
        max_f32 = f32_bits_to_fraction(0x7F7FFFFF)
        logits = [max_f32, max_f32, -max_f32]
        probabilities, epsilon = softmax_oracle(logits)
        assert abs(float(probabilities[0]) - 0.5) <= float(epsilon)
        assert abs(float(probabilities[1]) - 0.5) <= float(epsilon)
        assert float(probabilities[2]) == 0.0

    def test_softmax_oracle_matches_subnormal_tail_contract(self):
        # Mirrors numerical_contract.rs
        # softmax_preserves_a_subnormal_tail_within_the_reference_contract.
        logits = [Fraction(0), Fraction(-100)]
        probabilities, epsilon = softmax_oracle(logits)
        assert probabilities[0] <= 1
        assert probabilities[1] > 0
        assert float(probabilities[1]) < 2**-126  # f32::MIN_POSITIVE (smallest normal)

    def test_rms_norm_oracle_matches_f64_rms_norm_within_derived_budget(self):
        rng = random.Random(29)
        for _ in range(200):
            values_f32 = [_f32(rng.uniform(-8, 8)) for _ in range(5)]
            weights_f32 = [_f32(rng.uniform(0.1, 2)) for _ in range(5)]
            eps = 1e-6

            values_fraction = [f32_bits_to_fraction(_bits(v)) for v in values_f32]
            weights_fraction = [f32_bits_to_fraction(_bits(v)) for v in weights_f32]

            normalized, tolerances = rms_norm_oracle(values_fraction, weights_fraction, Fraction(eps))

            mean_square = sum(v * v for v in values_f32) / len(values_f32)
            scale = math.sqrt(mean_square + eps)
            expected = [_f32((v / scale) * w) for v, w in zip(values_f32, weights_f32, strict=True)]

            for got, want, tolerance in zip(normalized, expected, tolerances, strict=True):
                delta = abs(float(got) - want)
                assert delta <= float(tolerance), f"delta={delta} tolerance={float(tolerance)}"

    def test_rms_norm_oracle_tolerance_scales_with_output_magnitude(self):
        # Regression test for the exact bug an earlier draft had: a fixed
        # global tolerance is only valid near magnitude 1. Use inputs that
        # produce a large-magnitude output and confirm the returned
        # tolerance is correspondingly larger than the magnitude-1 constant.
        values = [f32_bits_to_fraction(_bits(8.0))] * 4
        weights = [f32_bits_to_fraction(_bits(2.0))] * 4
        _normalized, tolerances = rms_norm_oracle(values, weights, Fraction(0))
        assert all(tolerance > F32_CAST_HALF_ULP for tolerance in tolerances)

    @staticmethod
    def _simulated_rust_attention(query, keys, values, context_len, head_dim):
        """Independent third re-derivation of the real Rust pipeline, in pure Python f64
        floats with explicit f32 rounding (`_f32`) at exactly the points the real Rust code
        casts to f32 -- neither the Rust implementation nor attention_oracle's own
        Fraction/Decimal code, matching the same pattern already used for
        crates/forgellm-reference/tests/attention.rs's own independent oracle."""
        raw_scores = []
        for j in range(context_len):
            acc = 0.0
            for k in range(head_dim):
                acc += float(query[k]) * float(keys[j * head_dim + k])
            raw_scores.append(_f32(acc))
        scale = 1.0 / math.sqrt(head_dim)
        scaled = [_f32(float(s) * scale) for s in raw_scores]
        maximum = max(scaled)
        exponentials = [math.exp(float(s) - float(maximum)) for s in scaled]
        denominator = sum(exponentials)
        probabilities = [_f32(e / denominator) for e in exponentials]
        context = []
        for k in range(head_dim):
            acc = 0.0
            for j in range(context_len):
                acc += float(probabilities[j]) * float(values[j * head_dim + k])
            context.append(_f32(acc))
        return context

    @staticmethod
    def _assert_attention_oracle_matches_simulation(query, keys, values, context_len, head_dim, label):
        """Shared body for both randomized cross-check tests below: simulate the real Rust
        pipeline, convert the same f32 inputs to exact Fractions, call attention_oracle, and
        assert every context element stays within its derived tolerance of the simulation.
        Factored out (rather than duplicated per test) after SonarCloud flagged the two
        near-identical inline bodies as a real 9%-density duplication on this file."""
        simulated = TestEndToEndOracles._simulated_rust_attention(query, keys, values, context_len, head_dim)

        query_f = [f32_bits_to_fraction(_bits(v)) for v in query]
        keys_f = [
            [f32_bits_to_fraction(_bits(keys[j * head_dim + k])) for k in range(head_dim)] for j in range(context_len)
        ]
        values_f = [
            [f32_bits_to_fraction(_bits(values[j * head_dim + k])) for k in range(head_dim)] for j in range(context_len)
        ]

        context, tolerances = attention_oracle(query_f, keys_f, values_f)

        for got, want, tolerance in zip(context, simulated, tolerances, strict=True):
            delta = abs(float(got) - want)
            assert delta <= float(tolerance), f"{label}: delta={delta} tolerance={float(tolerance)}"

    def test_attention_oracle_matches_simulated_rust_within_derived_budget(self):
        # Small dimensions and plain rng.uniform, matching
        # test_matmul_matches_f32_cast_of_f64_accumulation's own scale: empirically, sums of
        # only a handful of terms over this magnitude range stay inside
        # assert_f64_exact_accumulation's checked range without needing deliberate
        # quantization (see attention_oracle's own docstring for why that precondition matters
        # at all). test_attention_oracle_matches_simulated_rust_at_larger_context_len below
        # covers context_len up to 64 with quantized inputs, at a smaller trial count chosen to
        # stay CI-fast.
        rng = random.Random(31)
        for _ in range(200):
            context_len = rng.choice([1, 2, 4])
            head_dim = rng.choice([1, 2, 4])
            query = [_f32(rng.uniform(-8, 8)) for _ in range(head_dim)]
            keys = [_f32(rng.uniform(-8, 8)) for _ in range(context_len * head_dim)]
            values = [_f32(rng.uniform(-8, 8)) for _ in range(context_len * head_dim)]

            self._assert_attention_oracle_matches_simulation(
                query, keys, values, context_len, head_dim, f"context_len={context_len} head_dim={head_dim}"
            )

    def test_attention_oracle_matches_simulated_rust_at_larger_context_len(self):
        # Covers context_len up to 64 (the task packet's stated upper bound) at a trial count
        # small enough to stay CI-fast. Inputs are quantized to small integers times a shared
        # power-of-two magnitude (magnitude/8 must itself be a power of 2) so that even
        # context_len=64 with head_dim=16 satisfies the exact-accumulation precondition
        # attention_oracle's docstring documents as a caller responsibility -- an
        # arbitrary-float sweep at this scale would not (and did, concretely, violate that
        # precondition when first tried).
        #
        # Magnitude is capped at 2**6 (not the packet's originally stated 1e3/2**10): measured
        # directly, magnitude=2**10 combined with head_dim=16 produces raw dot products in the
        # millions, whose softmax-shifted logits (~-7e5) make `Decimal.exp()`'s result underflow
        # to a value that is exactly representable only as a Fraction with a ~1,000,000-bit
        # denominator (`decimal_to_fraction`'s exact `as_integer_ratio()` conversion, working as
        # designed) -- and Python's arbitrary-precision Fraction arithmetic on numbers that
        # large, while correct, is genuinely slow (a single such trial measured at 12.9s;
        # summing several before division compounds further). This is real, understood, and
        # exponential in magnitude (0.09s at 2**6, 0.9s at 2**7, 12.9s at 2**8 for the same
        # context_len=64/head_dim=16 case) -- not a hang, not a bug in attention_oracle, and not
        # representative of real attention scores (well-scaled Q/K keep dot products bounded
        # for exactly this reason). Capping magnitude here still spans roughly three orders of
        # magnitude (2**-6..2**6) while keeping every trial well clear of that cost cliff; see
        # docs/quality/P0-T19-ATTENTION.md for the full investigation and measurements.
        def quantized_f32(rng, magnitude):
            step = magnitude / 8.0
            return _f32(rng.randint(-8, 8) * step)

        rng = random.Random(20260828)
        trials_per_config = 15
        for context_len in (8, 64):
            for magnitude in (2.0**-6, 2.0**0, 2.0**6):
                for _ in range(trials_per_config):
                    head_dim = rng.choice([1, 2, 3, 8, 16])
                    query = [quantized_f32(rng, magnitude) for _ in range(head_dim)]
                    keys = [quantized_f32(rng, magnitude) for _ in range(context_len * head_dim)]
                    values = [quantized_f32(rng, magnitude) for _ in range(context_len * head_dim)]

                    self._assert_attention_oracle_matches_simulation(
                        query,
                        keys,
                        values,
                        context_len,
                        head_dim,
                        f"context_len={context_len} head_dim={head_dim} magnitude={magnitude}",
                    )

    def test_attention_oracle_context_len_one_returns_values_row_exactly(self):
        # A single-position context makes softmax exactly 1.0 regardless of the score or
        # scale -- context must equal `values[0]` exactly, independent of query/keys.
        query = [f32_bits_to_fraction(_bits(3.0)), f32_bits_to_fraction(_bits(-1.0))]
        keys = [[f32_bits_to_fraction(_bits(5.0)), f32_bits_to_fraction(_bits(2.0))]]
        values = [[f32_bits_to_fraction(_bits(7.0)), f32_bits_to_fraction(_bits(-4.0))]]

        context, _tolerances = attention_oracle(query, keys, values)

        assert context == [Fraction(7), Fraction(-4)]

    def test_attention_oracle_rejects_key_head_dim_mismatch(self):
        query = [Fraction(1), Fraction(0)]
        keys = [[Fraction(1), Fraction(0), Fraction(0)]]
        values = [[Fraction(1), Fraction(0)]]
        with pytest.raises(ValueError):
            attention_oracle(query, keys, values)

    def test_attention_oracle_rejects_key_value_context_length_mismatch(self):
        query = [Fraction(1), Fraction(0)]
        keys = [[Fraction(1), Fraction(0)], [Fraction(0), Fraction(1)]]
        values = [[Fraction(1), Fraction(0)]]
        with pytest.raises(ValueError):
            attention_oracle(query, keys, values)


class TestMultiQueryAttentionOracle:
    @staticmethod
    def _simulated_rust_multi_query(queries, keys, values, query_count, context_len, head_dim):
        scale = 1.0 / math.sqrt(head_dim)
        result = []
        for query_row in range(query_count):
            raw_scores = []
            for key_row in range(context_len):
                accumulator = sum(
                    float(queries[query_row * head_dim + column]) * float(keys[key_row * head_dim + column])
                    for column in range(head_dim)
                )
                raw_scores.append(_f32(accumulator))
            scaled = [_f32(float(score) * scale) for score in raw_scores]
            maximum = max(scaled)
            exponentials = [math.exp(float(score) - float(maximum)) for score in scaled]
            denominator = sum(exponentials)
            probabilities = [_f32(exponential / denominator) for exponential in exponentials]
            for column in range(head_dim):
                accumulator = sum(
                    float(probabilities[key_row]) * float(values[key_row * head_dim + column])
                    for key_row in range(context_len)
                )
                result.append(_f32(accumulator))
        return result

    def test_oracle_returns_one_context_and_tolerance_row_per_query(self):
        queries = [[Fraction(1), Fraction(0)], [Fraction(0), Fraction(1)]]
        keys = [[Fraction(1), Fraction(0)], [Fraction(0), Fraction(1)], [Fraction(1), Fraction(1)]]
        values = [[Fraction(2), Fraction(0)], [Fraction(0), Fraction(2)], [Fraction(1), Fraction(3)]]

        contexts, tolerances = multi_query_attention_oracle(queries, keys, values)

        assert len(contexts) == len(queries)
        assert len(tolerances) == len(queries)
        assert all(len(row) == 2 for row in contexts)
        assert all(len(row) == 2 for row in tolerances)

        flat_queries = [float(value) for row in queries for value in row]
        flat_keys = [float(value) for row in keys for value in row]
        flat_values = [float(value) for row in values for value in row]
        simulated = self._simulated_rust_multi_query(flat_queries, flat_keys, flat_values, 2, 3, 2)
        for row, simulated_row, tolerance_row in zip(contexts, [simulated[:2], simulated[2:]], tolerances, strict=True):
            for got, want, tolerance in zip(row, simulated_row, tolerance_row, strict=True):
                assert abs(float(got) - want) <= float(tolerance)

    def test_oracle_keeps_query_rows_independent(self):
        queries = [[Fraction(1), Fraction(0)], [Fraction(0), Fraction(1)]]
        keys = [[Fraction(1), Fraction(0)], [Fraction(0), Fraction(1)]]
        values = [[Fraction(10), Fraction(0)], [Fraction(0), Fraction(20)]]

        contexts, _tolerances = multi_query_attention_oracle(queries, keys, values)

        assert float(contexts[0][0]) > float(contexts[0][1])
        assert float(contexts[1][1]) > float(contexts[1][0])

    def test_oracle_context_len_one_repeats_the_value_row_exactly(self):
        queries = [[Fraction(3), Fraction(-1)], [Fraction(0), Fraction(4)]]
        keys = [[Fraction(5), Fraction(2)]]
        values = [[Fraction(7), Fraction(-4)]]

        contexts, _tolerances = multi_query_attention_oracle(queries, keys, values)

        assert contexts == [[Fraction(7), Fraction(-4)], [Fraction(7), Fraction(-4)]]

    def test_oracle_rejects_ragged_queries(self):
        with pytest.raises(ValueError, match="rectangular"):
            multi_query_attention_oracle(
                [[Fraction(1), Fraction(0)], [Fraction(1)]], [[Fraction(1), Fraction(0)]], [[Fraction(1), Fraction(0)]]
            )

    def test_oracle_rejects_key_value_context_mismatch(self):
        with pytest.raises(ValueError, match="context length"):
            multi_query_attention_oracle(
                [[Fraction(1), Fraction(0)]],
                [[Fraction(1), Fraction(0)], [Fraction(0), Fraction(1)]],
                [[Fraction(1), Fraction(0)]],
            )

    def test_oracle_rejects_value_width_mismatch(self):
        with pytest.raises(ValueError, match="head_dim"):
            multi_query_attention_oracle(
                [[Fraction(1), Fraction(0)]],
                [[Fraction(1), Fraction(0)]],
                [[Fraction(1), Fraction(0), Fraction(2)]],
            )

    def test_oracle_matches_independent_simulation_for_bounded_random_inputs(self):
        rng = random.Random(20260829)
        for _ in range(80):
            query_count = rng.choice([1, 2, 3])
            context_len = rng.choice([1, 2, 4])
            head_dim = rng.choice([1, 2, 4])
            queries = [[_f32(rng.uniform(-2, 2)) for _ in range(head_dim)] for _ in range(query_count)]
            keys = [[_f32(rng.uniform(-2, 2)) for _ in range(head_dim)] for _ in range(context_len)]
            values = [[_f32(rng.uniform(-2, 2)) for _ in range(head_dim)] for _ in range(context_len)]

            queries_f = [[f32_bits_to_fraction(_bits(value)) for value in row] for row in queries]
            keys_f = [[f32_bits_to_fraction(_bits(value)) for value in row] for row in keys]
            values_f = [[f32_bits_to_fraction(_bits(value)) for value in row] for row in values]
            contexts, tolerances = multi_query_attention_oracle(queries_f, keys_f, values_f)

            simulated = self._simulated_rust_multi_query(
                [value for row in queries for value in row],
                [value for row in keys for value in row],
                [value for row in values for value in row],
                query_count,
                context_len,
                head_dim,
            )
            for query_index, (context, tolerance_row) in enumerate(zip(contexts, tolerances, strict=True)):
                simulated_row = simulated[query_index * head_dim : (query_index + 1) * head_dim]
                for got, want, tolerance in zip(context, simulated_row, tolerance_row, strict=True):
                    assert abs(float(got) - want) <= float(tolerance)

    def test_oracle_handles_f32_rounding_adjacent_inputs_per_row(self):
        lower = f32_bits_to_fraction(0x3F800000)
        upper = f32_bits_to_fraction(0x3F800001)
        queries = [[lower, upper], [upper, lower]]
        keys = [[upper, lower], [lower, upper]]
        values = [[Fraction(3), Fraction(-2)], [Fraction(-1), Fraction(4)]]

        contexts, tolerances = multi_query_attention_oracle(queries, keys, values)

        simulated = self._simulated_rust_multi_query(
            [float(value) for row in queries for value in row],
            [float(value) for row in keys for value in row],
            [float(value) for row in values for value in row],
            2,
            2,
            2,
        )
        for query_index, (context, tolerance_row) in enumerate(zip(contexts, tolerances, strict=True)):
            simulated_row = simulated[query_index * 2 : (query_index + 1) * 2]
            for got, want, tolerance in zip(context, simulated_row, tolerance_row, strict=True):
                assert abs(float(got) - want) <= float(tolerance)

    def test_oracle_rounds_a_raw_score_tie_before_each_row_softmax(self):
        # All inputs are representable f32 values, but their exact product is the midpoint
        # between two f32 values. This proves the multi-query path exercises the same explicit
        # intermediate raw-score cast as the compiled Rust operation, including tie-to-even.
        query = f32_bits_to_fraction(0x3FC00000)  # 1.5
        next_after_one = f32_bits_to_fraction(0x3F800001)
        lower = f32_bits_to_fraction(0x3FC00001)
        upper = f32_bits_to_fraction(0x3FC00002)
        raw_score_tie = query * next_after_one
        assert raw_score_tie == (lower + upper) / 2
        assert fraction_to_f32_bits(raw_score_tie) == 0x3FC00002

        queries = [[query], [query]]
        keys = [[next_after_one], [f32_bits_to_fraction(0x3F800000)]]
        values = [[Fraction(3)], [Fraction(-2)]]
        contexts, tolerances = multi_query_attention_oracle(queries, keys, values)

        simulated = self._simulated_rust_multi_query(
            [float(value) for row in queries for value in row],
            [float(value) for row in keys for value in row],
            [float(value) for row in values for value in row],
            2,
            2,
            1,
        )
        for query_index, (context, tolerance_row) in enumerate(zip(contexts, tolerances, strict=True)):
            assert abs(float(context[0]) - simulated[query_index]) <= float(tolerance_row[0])
