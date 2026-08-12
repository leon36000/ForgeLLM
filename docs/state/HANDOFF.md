# ForgeLLM Handoff

**From state:** S-0001  
**To task:** P0-T02  
**Generated:** 2026-08-12

## Verified package contents

The Phase 0 scaffold contains mobile context, agent instructions, charter and ADRs, state registers, a claim-centered research program, benchmark schemas, validators, tests, GitHub/GitLab controls, safe inventory tooling and installation documentation.

The last local gate before packaging was:

```text
make verify
11 passed
```

This proves structural consistency only; it is not an inference-performance result.

## What has not happened

- No remote repository has been created or modified.
- No branch protection, secret setting, project board or runner has been applied to an owner account.
- No GPU runner has been registered.
- No hardware inventory has been collected from the owner’s machines.
- No external engine benchmark has been reproduced.
- No ForgeLLM inference code has been written.
- No project license has been selected.

## Next operator procedure

1. Verify the external archive SHA-256 and the repository `MANIFEST.sha256`.
2. Extract on a trusted workstation.
3. Create an isolated Python environment and install `.[dev]`.
4. Run `make ci` and preserve the output.
5. Initialize Git, create the bootstrap commit and confirm a clean worktree.
6. Create a private remote under the owner-selected account.
7. Run `scripts/github/audit_repository.py` before any repository-admin write.
8. Create labels and protection only after reviewing the dry-run commands and satisfying their explicit confirmation gates.
9. Configure real maintainers/CODEOWNERS and required checks.
10. Install the project instructions and exactly five mobile files in ChatGPT.
11. Run `make inventory` on the first authorized laboratory machine.
12. Record owner decisions and create state S-0002.

## Continuity checksum

The next state must explicitly reference D-0001 through D-0007 and unresolved risks R-001, R-002, R-005, R-007 and R-008. A missing reference is a continuity warning, not proof that the item disappeared.
