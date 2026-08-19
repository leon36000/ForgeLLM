# ADR-0004: Use CI-based SonarQube Cloud analysis for ForgeLLM

- **Status:** proposed
- **Date:** 2026-08-18
- **Owners:** ForgeLLM project owner; independent quality/security reviewer
- **Related tasks/claims:** P0-T09 / QG-01; ADR-0001; D-0006; D-0009

## Context

P0-T09 exists to select exactly one SonarQube Cloud analysis method and make pull-request and protected-`main` results reproducible without hiding findings or weakening existing gates.

The immediate `main` failure was classified as `platform_limitation / subscription_loc_limit_exceeded`, not as a scanner defect. The owner-approved remediation changed only ForgeLLM Sonar visibility from private to public, matching the already-public GitHub repository and returning organization private LOC below the Free entitlement. This ADR therefore **must not** treat CI-based analysis as a workaround for the LOC limit.

The controlled remediation PR #32 merged as `main@86f32319847a011fb4d48c98f0c467282fcfbe49`. The PR-side SonarQube Cloud bot reported a passed Quality Gate with 0 new issues and 0 security hotspots. Post-merge controller evidence subsequently observed a successful exact-main Sonar check together with Phase 0 and CodeQL success, but that observation remains pending canonicalization until the P0-T09 closeout records the exact evidence in Git.

The architecture decision must also fit ForgeLLM's accepted target architecture, not only the current Phase-0 Python-heavy repository. ADR-0001 requires a Rust control plane/runtime with native C/C++ accelerator backends behind a versioned C ABI.

Current SonarQube Cloud documentation creates a decisive compatibility constraint:

- Automatic Analysis is recommended when a GitHub project is eligible and does not require unsupported features, but it currently excludes **Rust** from eligible languages.
- SonarQube Cloud supports Rust through the Rust analyzer run with SonarScanner; the analyzer integrates with Cargo/Clippy and can import coverage and Clippy reports.
- Automatic Analysis does not support coverage import, external rule-engine reports, analysis logs, non-PR branch analysis, or monorepo mode.
- CI-based analysis runs the scanner in the project's build environment and provides the control needed for compiled-language configuration and reproducible build context.

Primary external references reviewed 2026-08-18:

- https://docs.sonarsource.com/sonarqube-cloud/advanced-setup/automatic-analysis
- https://docs.sonarsource.com/sonarqube-cloud/advanced-setup/overview
- https://docs.sonarsource.com/sonarqube-cloud/advanced-setup/languages/rust
- https://docs.sonarsource.com/sonarqube-cloud/advanced-setup/languages/c-family/analysis-modes
- https://docs.sonarsource.com/sonarqube-cloud/advanced-setup/ci-based-analysis/github-actions-for-sonarcloud

## Decision

Select **`ci_based_only`** as the intended SonarQube Cloud architecture for ForgeLLM, subject to independent review and owner acceptance before any external configuration mutation.

Implementation is deliberately separate from this proposed ADR. Before the first CI scanner submission:

1. obtain an independent quality/security review with `ACCEPT` and resolve every BLOCKER/MAJOR finding;
2. record explicit owner acceptance of this ADR and the bounded Sonar method transition;
3. disable Automatic Analysis in SonarQube Cloud **before** enabling the CI scanner so the two methods never overlap;
4. store the required credential only as the GitHub Actions secret `SONAR_TOKEN`; never print or commit its value;
5. pin every third-party action/scanner integration to immutable commit SHAs and use least-privilege workflow permissions;
6. configure exact pull-request and protected-`main` triggers with sufficient Git history for attribution;
7. preserve Phase 0, CodeQL, GitGuardian, Dependency Review policy, branch protection, and P0-T08 exactness gates;
8. require exact-head PR success and exact resulting protected-`main` Sonar success before P0-T09 closeout.

This decision does not authorize source exclusions, finding suppression, Quality Gate weakening, project deletion, subscription purchase, or any change to speculative-decoding semantics.

## Alternatives considered

### `automatic_only`

**Benefits**

- minimal repository configuration and no scanner credential in GitHub Actions;
- low maintenance while the repository remains eligible;
- SonarQube Cloud currently reports Automatic Analysis as recommended for the present repository shape.

**Rejected because**

- Rust, an accepted core language under ADR-0001, is currently ineligible for Automatic Analysis;
- coverage and external analyzer report import are unavailable under Automatic Analysis;
- analysis logs are unavailable, reducing failure diagnosability;
- selecting it now would create a foreseeable method migration when the Rust runtime arrives.

Automatic Analysis remains a valid rollback candidate only through a reviewed superseding decision if Sonar's capabilities materially change or the CI path proves unsuitable.

### `ci_based_only`

**Benefits**

- supports the accepted Rust direction through SonarScanner/Cargo/Clippy;
- supports coverage and external reports needed for stronger evidence;
- exposes build/scanner logs and gives explicit control over build context;
- better aligns future Rust/C/C++ analysis with ForgeLLM's reproducibility requirements.

**Costs and risks**

- introduces a credential surface (`SONAR_TOKEN`) and CI maintenance;
- requires immutable pinning, least-privilege permissions, and explicit secret hygiene;
- C/C++ highest-fidelity analysis may later require a compilation database and build-specific configuration;
- a misordered migration could accidentally run Automatic and CI-based analysis concurrently.

These costs are acceptable only with the gates in this ADR and P0-T09.

## Consequences

- P0-T09's implementation path becomes Task 4B of the accepted recovery plan once this ADR is reviewed and accepted.
- No `.github/workflows/sonar.yml`, `sonar-project.properties`, Sonar method toggle, or GitHub secret change is authorized by the **proposed** status alone.
- The implementation must record scanner/action SHAs, workflow permissions, public project identifiers, secret name, and before/after Sonar method state without exposing secret material.
- The migration must be one-way during the verification cycle: Automatic Analysis off first, CI scanner on second, then PR/main evidence. No concurrent fallback.
- P0-T09 remains active until final PR and protected-`main` evidence, review, task archival, state/handoff update, and issue closeout are canonicalized.
- P0-T04 remains unchanged and independently blocked on owner host designation.

## Safety and correctness invariants

- Exactly one Sonar analysis method is active for ForgeLLM at any time.
- A missing, cancelled, skipped, absent, or annotation-free check is never treated as success.
- `SONAR_TOKEN` exists only in the approved secret boundary; its value never enters Git, logs, prompts, artifacts, or memory.
- No source is excluded merely to reduce LOC or obtain a green gate.
- No finding is suppressed or accepted without reviewed disposition.
- Third-party Actions are immutable-SHA pinned and use least privilege.
- Git remains canonical; Sonar, GitHub checks, UI readbacks and derived memory remain evidence inputs.
- Existing correctness/security gates cannot be weakened to make the migration pass.

## Evidence required for review

Before changing the analysis method, reviewers must verify:

1. ADR-0001 still requires Rust as a core control-plane/runtime language;
2. current official SonarQube Cloud documentation still states Rust is ineligible for Automatic Analysis and documents Rust SonarScanner/Clippy support;
3. PR #32's exact-head quality/security evidence and protected-main post-remediation evidence are correctly recorded without overstating queued or unavailable checks;
4. the proposed workflow uses supported official scanner guidance, immutable action SHAs and least-privilege permissions;
5. Automatic Analysis and CI-based configuration cannot overlap during migration;
6. rollback does not silently restore a second concurrent method.

The implementation review must then require `make ci`, task-packet validation, `git diff --check`, secret/configuration grep, exact PR checks, exact protected-`main` Sonar success, and a fresh independent configuration/security `ACCEPT`.

## Reversal condition

Reconsider `ci_based_only` through a superseding ADR if one or more of the following become true:

- SonarQube Cloud adds production-grade Automatic Analysis for Rust with the coverage/external-report/logging capabilities ForgeLLM needs and the simpler path is independently verified;
- CI-based analysis demonstrably cannot satisfy ForgeLLM's supported-language, reproducibility, security or maintenance requirements;
- the repository topology changes so materially that another supported Sonar architecture is required.

A reversal never enables both methods concurrently and must preserve the evidence history of P0-T09.
