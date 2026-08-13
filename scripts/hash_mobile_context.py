#!/usr/bin/env python3
"""Validate and print deterministic SHA-256 records for the five mobile context files."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

EXPECTED_FILES = (
    "00_FORGELLM_CORE_CONTEXT.md",
    "01_FORGELLM_AGENT_OPERATING_SYSTEM.md",
    "02_FORGELLM_RESEARCH_AND_EVIDENCE.md",
    "03_FORGELLM_STATE_AND_DECISIONS.md",
    "04_FORGELLM_PROMPTS_AND_WORKFLOWS.md",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_records(root: Path) -> list[str]:
    mobile_dir = root / "chatgpt" / "mobile-core"
    observed = tuple(path.name for path in sorted(mobile_dir.glob("*.md")))
    if observed != EXPECTED_FILES:
        expected = ", ".join(EXPECTED_FILES)
        actual = ", ".join(observed) or "<none>"
        raise ValueError(f"mobile bundle mismatch; expected [{expected}], observed [{actual}]")
    return [f"{sha256(mobile_dir / name)}  chatgpt/mobile-core/{name}" for name in EXPECTED_FILES]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        records = build_records(args.root.resolve())
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 1

    text = "\n".join(records) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        print(args.output)
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
