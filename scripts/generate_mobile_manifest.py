#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from forgellm_governance.validation import build_mobile_manifest

_DEFAULT_OUTPUT = Path("chatgpt/mobile-core/DERIVED-MANIFEST.yaml")


def main() -> int:
    parser = argparse.ArgumentParser(description="Regenerate the derived ForgeLLM mobile projection manifest.")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, default=_DEFAULT_OUTPUT)
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output if args.output.is_absolute() else root / args.output
    output = output.resolve()
    try:
        output.relative_to(root)
    except ValueError:
        parser.error("output must remain beneath root")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(yaml.safe_dump(build_mobile_manifest(root), sort_keys=False), encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
