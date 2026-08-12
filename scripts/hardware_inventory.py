#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from forgellm_governance.hardware import write_hardware_inventory


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a redacted, non-privileged ForgeLLM hardware inventory.")
    parser.add_argument("--output", type=Path, default=Path("artifacts/hardware-local.json"))
    args = parser.parse_args()
    print(write_hardware_inventory(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
