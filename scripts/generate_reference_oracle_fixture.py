#!/usr/bin/env python3
"""Generate the stdlib-only differential-oracle fixture for `crates/forgellm-reference`.

Deterministic: sorted keys, sorted case order, every float as an 8-hex-digit
f32 bit-pattern string. `--check` regenerates in memory and diffs byte-for-
byte against the committed file without ever mutating it.
"""

from __future__ import annotations

import argparse
import json
import struct
import sys
from fractions import Fraction
from pathlib import Path

from forgellm_governance.reference_oracle import (
    assert_f64_exact_accumulation,
    elementwise_add_exact,
    elementwise_mul_exact,
    embedding_gather_exact,
    f32_bits_to_fraction,
    fraction_to_f32_bits,
    matmul_exact,
    rms_norm_oracle,
    softmax_oracle,
)

FIXTURE_PATH = Path("crates/forgellm-reference/tests/fixtures/reference_ops_oracle.json")
HASH_PATH = Path("crates/forgellm-reference/tests/fixtures/reference_ops_oracle.sha256")


def _f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def _bits_hex(value: float) -> str:
    return f"{struct.unpack('<I', struct.pack('<f', value))[0]:08x}"


def _fraction_bits_hex(value: Fraction) -> str:
    return f"{fraction_to_f32_bits(value):08x}"


def _tensor(shape: list[int], values: list[float]) -> dict:
    return {"shape": shape, "data_hex": [_bits_hex(v) for v in values]}


def _tensor_fraction(shape: list[int], values: list[Fraction]) -> dict:
    return {"shape": shape, "data_hex": [_fraction_bits_hex(v) for v in values]}


def _flatten(rows: list[list[float]]) -> list[float]:
    return [value for row in rows for value in row]


def _to_fraction_matrix(rows: list[list[float]]) -> list[list[Fraction]]:
    return [[f32_bits_to_fraction(struct.unpack("<I", struct.pack("<f", v))[0]) for v in row] for row in rows]


def _build_cases() -> list[dict]:
    cases: list[dict] = []

    # --- elementwise_add ---
    lhs = [1.0, -2.5, 3.0, 0.125]
    rhs = [0.5, 1.5, -1.0, 4.0]
    lhs_f = [f32_bits_to_fraction(struct.unpack("<I", struct.pack("<f", v))[0]) for v in lhs]
    rhs_f = [f32_bits_to_fraction(struct.unpack("<I", struct.pack("<f", v))[0]) for v in rhs]
    result = elementwise_add_exact(lhs_f, rhs_f)
    assert_f64_exact_accumulation(result, context="elementwise_add_basic")
    cases.append(
        {
            "op": "elementwise_add",
            "case_id": "elementwise_add_basic",
            "inputs": {"lhs": _tensor([4], lhs), "rhs": _tensor([4], rhs)},
            "expected": _tensor_fraction([4], result),
            "comparison": {"mode": "exact"},
        }
    )

    # --- elementwise_mul ---
    lhs = [2.0, -1.5, 0.25, 8.0]
    rhs = [3.0, 4.0, -2.0, 0.5]
    lhs_f = [f32_bits_to_fraction(struct.unpack("<I", struct.pack("<f", v))[0]) for v in lhs]
    rhs_f = [f32_bits_to_fraction(struct.unpack("<I", struct.pack("<f", v))[0]) for v in rhs]
    result = elementwise_mul_exact(lhs_f, rhs_f)
    assert_f64_exact_accumulation(result, context="elementwise_mul_basic")
    cases.append(
        {
            "op": "elementwise_mul",
            "case_id": "elementwise_mul_basic",
            "inputs": {"lhs": _tensor([4], lhs), "rhs": _tensor([4], rhs)},
            "expected": _tensor_fraction([4], result),
            "comparison": {"mode": "exact"},
        }
    )

    # --- matmul (2x3 @ 3x2, small magnitudes for f64-exact accumulation) ---
    lhs_rows = [[1.0, 2.0, -1.0], [0.5, -2.0, 3.0]]
    rhs_rows = [[2.0, 1.0], [-1.0, 0.5], [4.0, -2.0]]
    lhs_frac = _to_fraction_matrix(lhs_rows)
    rhs_frac = _to_fraction_matrix(rhs_rows)
    matmul_result = matmul_exact(lhs_frac, rhs_frac)
    for row in matmul_result:
        assert_f64_exact_accumulation(row, context="matmul_2x3_3x2")
    cases.append(
        {
            "op": "matmul",
            "case_id": "matmul_2x3_3x2",
            "inputs": {
                "lhs": _tensor([2, 3], _flatten(lhs_rows)),
                "rhs": _tensor([3, 2], _flatten(rhs_rows)),
            },
            "expected": _tensor_fraction([2, 2], _flatten(matmul_result)),
            "comparison": {"mode": "exact"},
        }
    )

    # --- embedding_gather ---
    table_rows = [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]
    table_frac = _to_fraction_matrix(table_rows)
    token_ids = [2, 0, 2, 1]
    gather_result = embedding_gather_exact(table_frac, token_ids)
    cases.append(
        {
            "op": "embedding_gather",
            "case_id": "embedding_gather_repeated_tokens",
            "inputs": {
                "table": _tensor([3, 2], _flatten(table_rows)),
                "token_ids": token_ids,
            },
            "expected": _tensor_fraction([4, 2], _flatten(gather_result)),
            "comparison": {"mode": "exact"},
        }
    )

    # --- softmax (basic + the two existing crate-contract edge cases) ---
    def softmax_case(case_id: str, logits: list[float]) -> dict:
        logits_f = [f32_bits_to_fraction(struct.unpack("<I", struct.pack("<f", v))[0]) for v in logits]
        probabilities, epsilon = softmax_oracle(logits_f)
        return {
            "op": "softmax",
            "case_id": case_id,
            "inputs": {"logits": _tensor([len(logits)], logits)},
            "expected": _tensor_fraction([len(logits)], probabilities),
            "comparison": {
                "mode": "abs_tolerance_hex",
                "tolerance_hex": _fraction_bits_hex(epsilon) if epsilon > 0 else "00000000",
                "tolerance_value_for_reference_only": str(epsilon),
                "tolerance_derivation": (
                    "(2*kappa + n + 2) * 2**-53 + 2**-24, kappa=4 (cited libm ULP "
                    "assumption for exp), n=len(logits); dominated by the final "
                    "f64->f32 cast term 2**-24 for any realistic n."
                ),
            },
        }

    cases.append(softmax_case("softmax_basic", [1.0, 2.0, 3.0]))
    cases.append(softmax_case("softmax_equal_logits", [0.5, 0.5, 0.5]))

    # --- rms_norm (per-element tolerance, since output magnitude is unbounded) ---
    def rms_norm_case(case_id: str, values: list[float], weights: list[float], epsilon: float) -> dict:
        # epsilon is f32 in the real Rust signature (rms_norm(values, weights,
        # epsilon: f32)); round it through f32 before building the exact
        # Fraction, exactly like every other input, rather than using the
        # raw f64 Python-float value (they differ, if only in the far digits
        # -- e.g. 1e-6 as f64 vs. its f32 rounding are literally unequal).
        epsilon_f32 = _f32(epsilon)
        values_f = [f32_bits_to_fraction(struct.unpack("<I", struct.pack("<f", v))[0]) for v in values]
        weights_f = [f32_bits_to_fraction(struct.unpack("<I", struct.pack("<f", v))[0]) for v in weights]
        epsilon_f = f32_bits_to_fraction(struct.unpack("<I", struct.pack("<f", epsilon_f32))[0])
        normalized, tolerances = rms_norm_oracle(values_f, weights_f, epsilon_f)
        return {
            "op": "rms_norm",
            "case_id": case_id,
            "inputs": {
                "values": _tensor([len(values)], values),
                "weights": _tensor([len(weights)], weights),
                "epsilon": _bits_hex(epsilon),
            },
            "expected": _tensor_fraction([len(values)], normalized),
            "comparison": {
                "mode": "abs_tolerance_hex_per_element",
                "tolerance_hex": [_fraction_bits_hex(t) for t in tolerances],
                "tolerance_derivation": (
                    "(n/2 + 4) * 2**-53 * |result| + half_ulp_at(result); the "
                    "relative term is provable from sqrt/div correct rounding, "
                    "the half-ULP term scales with each result's own magnitude "
                    "rather than assuming magnitude ~1."
                ),
            },
        }

    cases.append(rms_norm_case("rms_norm_basic", [1.0, -2.0, 3.0, 0.5], [1.0, 1.0, 1.0, 1.0], 1e-6))
    cases.append(rms_norm_case("rms_norm_large_magnitude", [8.0, 8.0, 8.0, 8.0], [2.0, 2.0, 2.0, 2.0], 1e-6))

    return sorted(cases, key=lambda case: (case["op"], case["case_id"]))


def build_fixture() -> dict:
    return {
        "schema_version": "1.0",
        "generator": "scripts/generate_reference_oracle_fixture.py",
        "float_encoding": "ieee754-binary32-hex-be",
        "cases": _build_cases(),
    }


def serialize(fixture: dict) -> str:
    return json.dumps(fixture, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--check",
        action="store_true",
        help="regenerate in memory and diff against the committed fixture; never writes",
    )
    args = parser.parse_args()

    fixture_path = args.root / FIXTURE_PATH
    expected_text = serialize(build_fixture())

    if args.check:
        try:
            actual_text = fixture_path.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"FAILED: cannot read {fixture_path}: {exc}")
            return 1
        if actual_text != expected_text:
            import difflib

            diff = "".join(
                difflib.unified_diff(
                    actual_text.splitlines(keepends=True),
                    expected_text.splitlines(keepends=True),
                    fromfile=str(fixture_path),
                    tofile="regenerated",
                )
            )
            print(f"FAILED: {fixture_path} is stale relative to the generator")
            print(diff)
            return 1
        print(f"OK: {fixture_path} matches the regenerated fixture exactly")
        return 0

    fixture_path.parent.mkdir(parents=True, exist_ok=True)
    fixture_path.write_text(expected_text, encoding="utf-8")

    import hashlib

    digest = hashlib.sha256(expected_text.encode("utf-8")).hexdigest()
    hash_path = args.root / HASH_PATH
    # Repo-root-relative path (not just the bare filename), matching the
    # existing artifacts/simulations/P0-T07-evidence.sha256 convention: `make
    # ci` runs `sha256sum -c` from the repository root, so the listed path
    # must resolve from there.
    hash_path.write_text(f"{digest}  {FIXTURE_PATH.as_posix()}\n", encoding="utf-8")
    print(f"Wrote {fixture_path} and {hash_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
