"""Allow `python -m forgellm_governance ...`."""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
