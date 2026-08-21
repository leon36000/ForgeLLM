# ADR-0004: Use CI-based SonarQube Cloud analysis for ForgeLLM

- **Status:** accepted
- **Date:** 2026-08-18
- **Owners:** ForgeLLM project owner; chief architect; independent quality and security reviewer roles
- **Related issue:** #26
- **Related task:** P0-T09
- **Supersedes:** none
- **Security-hardening amendment:** proposed 2026-08-19 on the P0-T09 implementation branch; non-operative until independently reviewed and merged to canonical `main`.

## Context

P0-T09 requires exactly one reproducible SonarQube Cloud analysis method. The previously diagnosed subscription LOC incident is a service-level platform limitation and was resolved for ForgeLLM by the separately authorized visibility correction; moving scanner execution into CI does not bypass that entitlement.

### Observed ForgeLLM evidence

- The accepted project charter and ADR-0001 make Rust the default runtime and control-plane language. Python remains outside the hot path.
- At canonical `main` commit `86f32319847a011fb4d48c98f0c467282fcfbe49`, the repository has no committed Sonar scanner workflow or properties file and the Sonar project still reports Automatic Analysis / Autoscan as the active method.
- Post-remediation pull request #32 exact head `4c6b9be358c68aaae7f440d78b1a6b5eb25d3e02` passed the Sonar pull-request Quality Gate, Phase 0 run `32093231786`, CodeQL run `32093231780`, and GitGuardian check-run `95579459513`. Dependency Review run `32093231806` / job `95579461797` was terminal `skipped`; it is not counted as success.
- The resulting `main` commit `86f32319847a011fb4d48c98f0c467282fcfbe49` has Sonar check `95580373383` success, Phase 0 check `95580302118` success, `analyze-python` check `95580302432` success, and anonymous Sonar readback whose revision equals exact `main` with Quality Gate `OK`, public visibility and `ncloc=6939`.

These facts prove that current Automatic Analysis recovered after the LOC remediation. They do not prove that Automatic Analysis can cover the accepted Rust architecture.

### Current external product facts

Official SonarQube Cloud documentation reviewed on 2026-08-18 states that:

- Automatic Analysis and CI-based scanner analysis are mutually exclusive for the same project;
- Automatic Analysis is not eligible for Rust and does not provide analysis logs, coverage import or external rule-report import;
- Rust is supported through SonarScanner CI analysis, with Cargo and Clippy prerequisites and support for Clippy and coverage-report import;
- the Rust analyzer automatically runs `cargo clippy` by default, but that behavior can be disabled and a pre-generated Clippy JSON report can be imported instead;
- GitHub Actions CI requires `SONAR_TOKEN`; on the current Free-plan path the documented credential is a user personal access token; and
- CI-based execution does not bypass organization LOC entitlement.

GitHub documents that repository secrets are not passed to ordinary `pull_request` workflows from public forks. GitHub also documents the pwn-request class of vulnerability created when a secret-bearing workflow executes untrusted checked-out code or its build scripts, dependencies or configuration. ForgeLLM already forbids `pull_request_target` in repository automation.

### Architectural inference

Selecting `automatic_only` would intentionally canonize a method already ineligible for the language designated as ForgeLLM's default runtime and control plane. Its lower present-day operational surface does not outweigh that known architectural mismatch. The durable choice is therefore CI-based analysis, subject to security and reproducibility gates before activation.

## Decision

Select exactly **`ci_based_only`** for ForgeLLM SonarQube Cloud analysis.

1. Automatic Analysis remains the known-working method only during the migration-preparation window. It must be disabled before the first CI scanner submission. Automatic and CI-based analyses must never overlap.
2. Task 4B implements the selected method. Task 4A is rejected and must not execute unless a later accepted ADR supersedes this decision.
3. The CI workflow must use least-privilege GitHub permissions, immutable full-SHA third-party action pins, non-persistent checkout credentials, sufficient Git history for attribution, and a clear secret-absence failure that never prints secret material.
4. `SONAR_TOKEN` is available only to the final approved scanner step. Workflow-, job-, container-, and service-level secret environments are forbidden, as are reusable-workflow secret forwarding, `secrets: inherit`, token propagation through outputs/state, and token exposure to any earlier or later step. Checkout, source/report acquisition, extraction, normalization and validation must complete without `SONAR_TOKEN`; no token-bearing post-processing is permitted. The final scanner step may invoke only an immutable reviewed external scanner action or an equivalently pinned trusted scanner invocation whose complete pre/main/post behavior has been reviewed; repository-local/composite actions, local scripts and contributor-controlled action metadata are forbidden in that token-bearing step. No token value or private administrative payload may enter Git, logs, task artifacts or chat evidence.
5. The job that eventually contains the final token-bearing scanner step must not check out contributor-originated source or execute repository-local/contributor-controlled code. Source and reports may enter that job only as data through a separately reviewed, secretless transfer and validation boundary; trusted workflow, connection and scanner configuration come from protected canonical context. A token-bearing process must not execute contributor-controlled commands, build scripts, package-manager hooks, proc macros, test binaries or dependencies. This remains true when fork-originated content is cherry-picked or promoted to a maintainer branch; ref ownership does not make executable content intrinsically trusted.
6. For Rust, the token-bearing Sonar scanner must disable the analyzer's automatic Clippy execution. Cargo/Clippy, coverage generation and any other command that can execute project or dependency code run in a separate job or environment with no `SONAR_TOKEN` or other privileged credential. The scanner may import bounded, validated reports as untrusted data and must not execute them. Duplicate Clippy ingestion must be avoided.
7. The secret-bearing scanner must use trusted workflow and connection/project configuration. Untrusted source must not be able to override the Sonar host, organization, project key, token handling, scanner binary source/version or trusted report paths. Scanner/action versions and download verification remain pinned and reviewable.
8. Before activation, the token identity and lifecycle must pass security review. On the current Free-plan path, an over-privileged owner or administrator PAT is not accepted merely for convenience. A dedicated least-privilege analysis identity is preferred where the service permits it. A plan purchase or upgrade is never implied by this ADR and requires separate owner approval.
9. Ordinary fork and same-repository `pull_request` workflows remain secretless with respect to `SONAR_TOKEN`. ForgeLLM will not use `pull_request_target` for Sonar and the current Task 4B implementation also forbids `workflow_run`; any later privileged follow-up trigger requires a separately reviewed design amendment. If pre-merge Sonar proof is required, Task 4B must implement and independently review a trusted-data bridge that treats source and reports strictly as validated data, binds them immutably to the intended repository/workflow/run/PR/head/artifact provenance, and supplies metadata and scanner configuration from trusted context; otherwise Sonar is deferred to a protected trusted ref. An absent or skipped Sonar check on the original pull request is not success.
10. If the selected Sonar scanner/analyzer cannot inspect required Rust source without executing contributor-controlled code in the token-bearing context, CI activation is blocked until a safe split or alternative is proven. The security boundary must not be weakened merely to obtain a green check.
11. P0-T09 is not complete until the selected CI method proves a successful exact-head pull-request analysis and a successful resulting protected-`main` analysis while Phase 0, CodeQL and GitGuardian remain green and Dependency Review is characterized truthfully.

## Alternatives considered

### `automatic_only`

Rejected as the durable method. It is operationally simpler and is proven to work for the current codebase, but official product eligibility excludes Rust and it lacks the logs, coverage import and external-report import needed for stronger reproducibility and future Rust evidence.

### Defer the decision until Rust lands

Rejected. P0-T09 explicitly requires a method decision, and deferral would knowingly move a required migration onto the critical path of first Rust adoption.

### Drop Sonar coverage for Rust

Rejected because it would weaken the intended quality and security evidence surface rather than adapt the analysis method to the accepted architecture.

## Consequences

### Positive

- The selected method aligns with the accepted Rust architecture instead of merely the current repository language mix.
- CI logs and versioned workflow/configuration increase reproducibility and reviewability.
- Clippy, coverage and external-report evidence can be integrated without granting a scanner secret to code-producing jobs.
- Analysis-method configuration becomes visible in Git and can be checked mechanically.

### Negative

- CI introduces credential lifecycle, scanner/action supply-chain and workflow maintenance surface.
- Rust requires an explicit secretless build/lint/report stage because Sonar's default automatic Clippy execution is unsafe in a token-bearing context for untrusted changes.
- Fork pull requests cannot receive the repository secret and need a separately reviewed trusted-data analysis path or deferred Sonar proof.
- Migration creates a bounded interval after Automatic Analysis is disabled and before CI is proven.
- CI does not solve service-level LOC entitlement failures.

## Transition and rollback

1. Prepare and independently review the workflow, project properties and governance checks without submitting a CI scanner analysis.
2. Demonstrate the trust split: Rust Cargo/Clippy/coverage and source/report acquisition/validation are secretless; the eventual scanner job does not check out contributor-originated source; the final scanner step alone receives `SONAR_TOKEN`; the pinned scanner action/invocation including pre/main/post behavior is reviewed; automatic Clippy is disabled; and untrusted source/configuration cannot redirect or reconfigure the authenticated scanner.
3. Establish an acceptable token identity/lifecycle and store only the value as GitHub `SONAR_TOKEN`.
4. Immediately before the first controlled CI submission, after the token identity/lifecycle review and explicit activation authorization, read back the current Automatic Analysis state, perform the disable action, read back the disabled state, and only then submit the reviewed CI candidate while recording each transition. The two methods never overlap.
5. If the first CI validation fails before Rust is materially analyzed, stop scanner submissions, confirm no CI path can submit, and re-enable Automatic Analysis only through reviewed rollback.
6. Once Rust is materially analyzed, Automatic Analysis is not a valid steady-state rollback while official Rust ineligibility remains. Repair the CI path or adopt a later reviewed ADR.

## Failure conditions

Do not activate or accept the CI method if any of the following holds:

- token identity or lifecycle is unacceptable;
- an action or scanner dependency is not immutable-pinned and verified as required;
- workflow permissions exceed documented need;
- `SONAR_TOKEN` can escape the final approved scanner step through workflow/job/container/service scope, reusable-workflow forwarding, `secrets: inherit`, outputs/state, action hooks, or post-processing;
- the eventual scanner job checks out contributor-originated source, executes repository-local/contributor-controlled code, or uses an unreviewed local/composite/reusable action in the token-bearing boundary;
- a secret-bearing process can execute contributor-controlled code or dependencies;
- untrusted configuration can redirect the scanner or authenticated connection;
- the required pull-request and `main` Quality Gate exactness cannot be proven;
- a paid plan, destructive setting or confidentiality change is required without explicit owner approval; or
- any existing Phase 0, CodeQL, GitGuardian, Dependency Review or correctness gate is weakened.

## Owner authorization and review state

Issue #26 records owner authorization `P0-T09 / subagent-driven` on 2026-08-14. In the 2026-08-18 owner session, the owner delegated operational and project decisions for continued ForgeLLM execution to the chief architect and directed rigorous continued execution. The owner did **not** personally select `ci_based_only`; the chief architect selected it under that delegation.

This ADR is accepted for architecture and Task 4B design. The initial independent review rejected an unsafe fork-retest formulation because a maintainer-controlled ref can still contain executable untrusted code. The revised design separates secretless code execution from the token-bearing scanner and was independently accepted; a second independent review accepted the exact two-file pull-request diff.

## Evidence supporting acceptance and required for implementation

- exact canonical base and final diff;
- task-packet validation and full repository validation;
- independent architecture/security review of the final text;
- secret-hygiene and workflow trust-boundary review;
- current primary SonarQube Cloud and GitHub Actions documentation;
- exact PR #32 recovery and resulting `main` evidence; and
- later selected-method implementation evidence on exact pull-request and protected-`main` commits.

## Primary references

- <https://docs.sonarsource.com/sonarqube-cloud/advanced-setup/automatic-analysis>
- <https://docs.sonarsource.com/sonarqube-cloud/analyzing-source-code/ci-based-analysis/overview-of-integrated-cis>
- <https://docs.sonarsource.com/sonarqube-cloud/advanced-setup/languages/rust>
- <https://docs.sonarsource.com/sonarqube-cloud/advanced-setup/ci-based-analysis/github-actions-for-sonarcloud>
- <https://docs.github.com/en/actions/reference/security/secure-use>
- <https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows>

## Reversal condition

Reconsider through a new ADR if Automatic Analysis gains production-grade Rust eligibility together with the required logs, coverage and external-report capabilities; if Sonar's credential/trust model changes materially; or if ForgeLLM replaces Sonar with another reviewed evidence system.
