#!/usr/bin/env python3
"""Validate one ForgeLLM component-profile document."""

from __future__ import annotations

import argparse
from pathlib import Path

from forgellm_governance.components import ComponentValidationError, load_component_document


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    try:
        document = load_component_document(args.path, args.root)
    except (ComponentValidationError, ValueError) as exc:
        issues = getattr(exc, "issues", None)
        if issues:
            for issue in issues:
                print(f"ERROR: {issue.render()}")
        else:
            print(f"ERROR: {exc}")
        return 1
    print(f"OK: {document.profile_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
