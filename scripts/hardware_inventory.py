#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from forgellm_governance.hardware import write_public_hardware_inventory

_PROJECT_ROOT = Path(__file__).resolve().parents[1]


def write_sanitized_inventory(path: Path) -> Path:
    """Write a publication-safe inventory through the canonical package boundary."""

    return write_public_hardware_inventory(_PROJECT_ROOT, path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a redacted, non-privileged ForgeLLM hardware inventory.")
    parser.add_argument("--output", type=Path, default=Path("artifacts/hardware-local.json"))
    args = parser.parse_args()
    print(write_sanitized_inventory(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
