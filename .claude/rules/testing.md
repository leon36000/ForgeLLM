---
paths:
  - "src/**"
  - "tests/**"
  - "scripts/**"
---

# Testing rules

- Add the failing oracle before behavior code when feasible.
- Test invalid input and deterministic edge cases.
- Run focused tests first, then `make ci` before completion.
- Never weaken a test merely to make a change pass without documenting the semantic decision.
