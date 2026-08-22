# P0-T09 inactive Sonar checkpoint review

**Review date:** 2026-08-21
**Scope:** protected-ref Task 4B.1 preparation only
**Status:** accepted for the inactive checkpoint; P0-T09 remains `in_progress`

## Exact implementation and publication

- PR #67 exact head: `a58ee2f0a705f73bcc769330547f1b6bb7de6a67`
- Protected-main merge: `83f8ea624bc4382f22e2e168c5444df5304b189a`
- Analysis method: ADR-0004 `ci_based_only`; no activation in this review
- Independent gate: GPT-5.6-Sol exact-head verdict `GO`; no Critical or Major finding

## Reviewed boundary

The secretless producer checks out the canonical repository at the event SHA with pinned immutable actions, installs the pinned Rust toolchain, copies only the reviewed source roots, generates Clippy JSON without `SONAR_TOKEN`, and uploads one fixed artifact. The scanner downloads that artifact first, validates the fixed source/report paths, fails closed on symlinks, and invokes the pinned Sonar action only as its final token-bearing step. The validator rejects missing or mutable artifact pins, wrong names/paths, checkout repository/ref overrides, missing source/report preparation, missing symlink rejection, token propagation, and forbidden events.

## Evidence

Local exact-head evidence:

- `make validate`: passed;
- `make lint`: passed;
- `make ci`: passed — 471 Python tests and 230 focused speculative tests;
- `PYTHONPATH=src python3 -m pytest -q tests/test_sonar_validation.py`: 53 passed;
- `git diff --check`: passed;
- GitGuardian pre-commit scan: no leaks found.

Hosted PR #67 evidence:

- Validate and test: success (`32531975996`);
- SonarCloud Code Analysis: success;
- CodeQL: success (`96925821594`);
- GitGuardian Security Checks: success;
- Dependency Review: terminal `SKIPPED`, not counted as success.

Hosted protected-main evidence:

- Phase 0 verification run `32532087564`: success;
- CodeQL run `32532087569`: success;
- prepared Sonar run `32532087558`: success, with `producer=success` and `scanner=skipped`.

## Pre-activation token lifecycle checkpoint

The separate token review is recorded in [`P0-T09-token-lifecycle-review.json`](../../artifacts/governance/P0-T09-token-lifecycle-review.json). It is explicitly `not_ready_for_activation`: the repository-level GitHub secret listing confirms the `SONAR_TOKEN` secret name with update metadata `2026-08-22T08:08:16Z`, the repository variable listing is empty, and neither command reads secret values. Those readbacks are repository-scoped and do not establish token validity, issuer, scope, lifecycle controls, or organization- and environment-level state.

The official SonarQube Cloud documentation recommends a Scoped Organization Token where the plan supports it because it is non-user-specific, project-scoped and can be limited to Execute Analysis. The recorded project plan is Free, so the documented Free-plan candidate is a Personal Access Token. Issuing identity, non-administrator project permission, minimum scope, storage approval, expiry/rotation, revocation, audit and incident-response controls remain open; secret presence alone does not authorize activation. A personal owner/administrator token chosen for convenience is rejected. See the [Scoped Organization Token documentation](https://docs.sonarsource.com/sonarqube-cloud/administering-sonarcloud/scoped-organization-tokens), [Personal Access Token documentation](https://docs.sonarsource.com/sonarqube-cloud/managing-your-account/managing-tokens), and [GitHub Actions secret guidance](https://docs.github.com/en/actions/concepts/security/secrets).

This checkpoint reads only sanitized GitHub secret metadata; it does not read or record the token value, mutate Sonar/GitHub settings, change Automatic Analysis, activate the scanner or submit an analysis.

## Explicit limitations

This review does not establish `SONAR_TOKEN` readiness, token identity/lifecycle approval, Automatic Analysis disablement, CI scanner activation, a Sonar CI submission, a pull-request trusted-data bridge, zero repository-wide Sonar findings, or P0-T09 completion. Dependency Review remains skipped by the existing workflow configuration. The scanner archive digest remains an open limitation.
