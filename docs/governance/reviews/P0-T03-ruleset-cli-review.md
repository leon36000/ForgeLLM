# P0-T03 Main Ruleset CLI Review Record

- **Review mode:** solo
- **Task:** P0-T03
- **Change class:** repository-governance tooling and tests
- **Opened:** 2026-08-13
- **Verdict:** `PENDING`

## Implementer context

- **ID:** `chatgpt-forgellm-p0-t03-ruleset-cli-2026-08-13`
- **Scope:** add a dry-run-by-default, idempotent CLI that validates ADR-0003 invariants before creating or updating the named GitHub ruleset

## Required automated evidence

- Ruff succeeds.
- Project, research, benchmark, task, governance-policy, mobile-hash, and manifest-policy validation succeed.
- The full pytest suite includes the new ruleset tests and succeeds.
- `MANIFEST.sha256` includes the new stable source, script, and test files.
- The CLI dry-run exits zero and performs no administrative write.
- The temporary verification workflow is absent from the final tree.

## Required adversarial review

The verifier must attempt to falsify at least these properties:

1. an approval count greater than zero is rejected in solo mode;
2. CODEOWNERS enforcement and bypass actors are rejected;
3. a wrong branch target or non-strict required check is rejected;
4. applying without both explicit confirmations is rejected;
5. an absent named ruleset uses `POST`;
6. an existing named ruleset uses `PUT` against its numeric ID;
7. malformed or surprising GitHub responses fail closed;
8. no token, credential, or administrative response body is committed.

## Verifier context

- **ID:** pending distinct context
- **Inherited private reasoning:** must be `false`
- **Reviewed head SHA:** pending
- **Commands reproduced:** pending
- **Findings:** pending
- **Verdict:** `PENDING`

## Owner authorization

- **GitHub user:** `leon36000`
- **Merge authorization:** `PENDING`
- **Ruleset application authorization:** `PENDING`

This record does not authorize merge or repository-administration writes before exact-head CI, context-separated review, and explicit owner authorization.
