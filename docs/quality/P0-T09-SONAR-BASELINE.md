# P0-T09 SonarQube Cloud Read-Only Baseline

- **Task:** P0-T09 / QG-01
- **Owner authorization:** `P0-T09 / subagent-driven`, recorded 2026-08-14
- **Canonical base:** `1b1a3621fcdf4129268663c497cdcd53aed48c29`
- **Mode:** read-only diagnosis plus one owner-authorized minimal visibility remediation
- **Configuration changes:** `ForgeLLM Sonar visibility: private -> public` only
- **Method selection:** not selected
- **Current classification:** `platform_limitation / subscription_loc_limit_exceeded`

Machine-readable evidence:

- `artifacts/governance/P0-T09-sonar-baseline.json`;
- `artifacts/governance/P0-T09-sonar-analysis-method-readback.json`;
- `artifacts/governance/P0-T09-readonly-diagnosis-2026-08-17.json`.

## Evidence question

Why does the SonarQube Cloud GitHub App repeatedly produce a successful pull-request quality gate for ForgeLLM while the GitHub check-run on the resulting protected `main` commit repeatedly has conclusion `cancelled`, title `SonarQube Cloud analysis failed`, and no GitHub annotations?

The public GitHub evidence establishes the pattern. The owner-authenticated Analysis Method screenshot proves that automatic analysis is enabled and recommended for this project. A second owner-authenticated Sonar UI screenshot supplied on 2026-08-17 states that the analysis failed because the organization's total lines of code exceed the current subscription limit and exposes analysis ID `472eadb9-b554-47ca-8336-2033fb3b7408`. A third owner-provided Background Tasks screenshot establishes internal status `FAILED` for branch-analysis task `AaADNoZ4U0I7o8og6Mb6`, immediately after pull-request task `AaADNKJHGgg5GiBgCda_` completed `SUCCESS`. This classifies the immediate failure as `platform_limitation` with subtype `subscription_loc_limit_exceeded`. The exact task/analysis-to-commit binding remains to be read back. A GitHub check-run conclusion of `cancelled` must not be treated as proof that the Sonar background task itself had status `CANCELED`.

## Canonical project identifiers

| Field | Readback | Evidence quality |
|---|---|---|
| GitHub repository | `leon36000/ForgeLLM` | canonical Git |
| Sonar project key | `leon36000_ForgeLLM` | GitHub check `details_url` |
| Sonar instance | `https://sonarcloud.io` | GitHub check `details_url` |
| GitHub App | `sonarqubecloud`, app ID `12526` | GitHub check-run payload |
| Sonar binding | `https://github.com/leon36000/ForgeLLM` | owner-authenticated UI + anonymous Web API |
| Sonar visibility | `public` (previously `private`) | owner-authenticated before/after UI + anonymous Web API |
| Analysis Method setting | `Automatic analysis` enabled | owner-authenticated screenshot + anonymous navigation API |
| Compatibility/recommendation | `Recommended` | owner-authenticated screenshot |
| CI method selected | no | owner-authenticated screenshot |
| Last analysis method | `Analyzed by SonarQube Cloud / Autoscan` | owner-authenticated final readback + anonymous navigation API |

The sanitized screenshot transcription is stored in `artifacts/governance/P0-T09-sonar-analysis-method-readback.json`. The raw image is not committed; its SHA-256 is recorded as `bfab677e68396b0452bf6348be773e974a3f4325768b080961a0f5e936f7e5e1`.

## Observed analysis matrix

| Context | Commit | Sonar check | Sonar result | Annotations | Phase 0 | CodeQL |
|---|---|---:|---|---:|---|---|
| PR #24 implementation | `16d65288…` | `94869018087` | GitHub conclusion `cancelled` / analysis failed | 36 | success | success |
| PR #25 remediation | `a7f508fe…` | `94889986512` | Quality Gate passed | 0 | success | success |
| `main` after remediation | `e81c1c0a…` | `94890528740` | GitHub conclusion `cancelled` / analysis failed | 0 | success | success |
| PR #27 closeout | `5c1f7c6c…` | `94892322303` | Quality Gate passed | 0 | success | success |
| `main` after closeout | `e669f5e1…` | `94892860919` | GitHub conclusion `cancelled` / analysis failed | 0 | success | success |
| PR #28 planning | `f60373b3…` | `94894565075` | Quality Gate passed | 0 | success | success |
| `main` after planning | `1b1a3621…` | `94894966719` | GitHub conclusion `cancelled` / analysis failed | 0 | success | success |
| PR #30 post-import probe | `3bc75c64…` | `94945852247` | Quality Gate passed | 0 | success | success |
| `main` after post-import probe | `bd03e479…` | `94946081665` | GitHub conclusion `cancelled` / analysis failed | 0 | success | success |
| PR #31 analysis-method readback | `a2d68d91…` | `94948153214` | Quality Gate passed | 0 | success | success |
| `main` after PR #31 | `484fec34…` | `94948378776` | GitHub conclusion `cancelled` / analysis failed | 0 | success | success |

The post-import probe shows that importing the project was not sufficient to repair the `main` analysis path: the PR quality gate passed after import, while the resulting `main` check still failed in the same annotation-free way. PR #31 and current `main@484fec34007fd89f554c9c03bffa9a5275676602` reproduce the same split a fifth time.

The 2026-08-17 independent diagnosis is stored in `artifacts/governance/P0-T09-readonly-diagnosis-2026-08-17.json`. Codex, Claude Code, and OpenHands independently found no committed Sonar scanner configuration. Subsequent owner-authenticated UI evidence resolved the immediate failure cause as the organization LOC subscription limit and established internal branch-task status `FAILED`. After explicit owner approval, only ForgeLLM Sonar visibility changed from private to public. Independent anonymous Web API reads now return HTTP 200 and confirm visibility public, binding `leon36000/ForgeLLM`, Automatic Analysis enabled, `ncloc=1658`, Quality Gate `OK`, and latest completed main revision `d5cd25bd9d6fc3f9cded27781c2051939dcdde85`. The exact old task/analysis-to-revision binding remains correlation rather than a shared-ID proof, but it is no longer needed to guess the failure class.

## PR #24 annotation classification

The failed PR #24 check published 36 annotations:

- **2 production-code failures**;
- **34 test-code warnings**.

The production findings were:

1. `src/forgellm_governance/speculative_decoding.py`: centralize the repeated `tape must be a RandomTape` literal;
2. `src/forgellm_governance/speculative_exhaustive.py`: make the completion helper return one consistent container shape.

They were corrected in PR #25. Its exact-head Sonar result reported:

```text
Quality Gate passed
0 new issues
0 accepted issues
0 security hotspots
```

The 34 test warnings shared one rule family: exception assertions should contain only one invocation capable of throwing. They remain recorded baseline debt; they are not silently accepted or suppressed by P0-T09.

## Repository and Analysis Method readback

The canonical Git tree contains:

- no `.github/workflows/sonar.yml`;
- no `sonar-project.properties`;
- no `.sonarcloud.properties`.

The owner-authenticated SonarQube Cloud **Analysis method** page now confirms:

```text
Automatic analysis: enabled
Recommendation: Recommended
CI analysis method selected: no
```

Therefore the earlier inference can be promoted to an observed project setting: ForgeLLM is currently configured for automatic analysis. This does **not** yet prove why `main` fails or that `automatic_only` should remain the final architecture.

## Official-document constraints

The diagnosis uses these primary SonarQube Cloud references:

- <https://docs.sonarsource.com/sonarqube-cloud/advanced-setup/automatic-analysis>
- <https://docs.sonarsource.com/sonarqube-cloud/analyzing-source-code/ci-based-analysis/overview-of-integrated-cis>
- <https://docs.sonarsource.com/sonarqube-cloud/appendices/troubleshooting>
- <https://docs.sonarsource.com/sonarqube-cloud/appendices/web-api>
- <https://docs.sonarsource.com/sonarqube-cloud/administering-sonarcloud/resources-structure/projects>
- <https://docs.sonarsource.com/sonarqube-cloud/managing-your-projects/administering-your-projects/setting-permissions>
- <https://docs.sonarsource.com/sonarqube-cloud/administering-sonarcloud/managing-subscription/subscription-plans>

The official automatic-analysis documentation states that automatic and CI-based analysis must not be used concurrently for the same project. Sonar's subscription documentation states that analyses exceeding the organization's LOC entitlement are not performed; moving scanner execution to CI does not bypass that service-level entitlement. LOC consumption is based on analyzed private-project code, using the largest counted branch per project, and excludes test code, excluded files, unsupported-language code, comments and blank lines. The Web API documentation states that administrative services require the appropriate authorization.

Independent remediation reviews inspected the canonical ForgeLLM tree and found no generated, vendored, duplicated build-output, fixture, or third-party production source that is legitimately excludable. The maintained non-test Python footprint is approximately 5k physical lines, so no scope exclusion is justified as a quota workaround.

Owner-authenticated Billing & usage after the visibility change reports Free plan, 50,000 private-LOC entitlement, 48,248 private LOC consumed and approximately 1.8k remaining. The organization is therefore below the private-LOC limit after ForgeLLM becomes public, though it remains close to the limit. No price, payment or unrelated private-project identity is recorded.

## Evidence that is still required

The administrative read-only gate is now materially complete:

- repository binding: `leon36000/ForgeLLM`;
- Analysis Method: Automatic Analysis enabled, no CI method selected, latest method shown as SonarQube Cloud / Autoscan;
- New Code: `previous_version`;
- analysis-scope custom values: none/default for source/test inclusions and exclusions, coverage and duplication exclusions;
- issue-ignore multicriteria: none/default;
- Quality Gate: default `Sonar way`, latest completed main status `OK`;
- no canonical or selected CI scanner observed.

The only historical field without a shared identifier is the old failed task/analysis-to-revision binding; its timestamps and scopes remain strongly correlated. It is not needed to infer the cause because the LOC-limit error and internal `FAILED` status were directly observed. The load-bearing remaining evidence is a controlled post-remediation pull-request and protected-`main` cycle proving the current head can complete Sonar successfully.

Administrative payloads must be sanitized or represented by cryptographic hashes. Credentials, user lists, email addresses, tokens, and private organization data must not enter Git.

## Current classification

```text
analysis_method_setting = automatic_enabled
compatibility           = recommended
failure_classification  = platform_limitation
failure_subtype         = subscription_loc_limit_exceeded
analysis_id             = 472eadb9-b554-47ca-8336-2033fb3b7408
background_task_id      = AaADNoZ4U0I7o8og6Mb6
internal_task_status    = FAILED
method_selection        = not_selected
configuration_changes   = sonar_visibility_private_to_public_only
```

The P0-T09 task taxonomy still recognizes configuration, binding/permission, source/scope, platform, transient-service, and unavailable-evidence classes, but those are no longer competing hypotheses for the **immediate observed failure**. Owner-authenticated Sonar evidence classifies that failure as `platform_limitation / subscription_loc_limit_exceeded`, and Background Tasks establishes internal status `FAILED`.

The old task pair is strongly correlated to PR #31 / `main@484fec3…` through exact finish-time alignment and GitHub scopes, but GitHub exposes no shared Sonar task ID. Since the failure class is directly observed and the administrative readback is now complete, the remaining decision evidence is the post-remediation current-head PR/main cycle.

## Remediation constraints

The LOC-limit diagnosis rules out several tempting but invalid fixes:

- do **not** switch to CI-based analysis to bypass the quota; it cannot bypass SonarQube Cloud's organization LOC entitlement and would add workflow/secret surface without addressing the cause;
- do **not** exclude maintained ForgeLLM code merely to reduce LOC; no justified generated/vendor/build production source was found;
- do **not** delete Sonar projects without proving they are obsolete and obtaining explicit destructive approval;
- do **not** change a private project to public unless the underlying repository and analysis data are already intended to be public and a confidentiality review confirms no restricted asset would be exposed;
- do **not** increase the LOC entitlement or paid plan without explicit financial approval.

The smallest evidence-supported remediation has now been applied: ForgeLLM Sonar visibility was aligned from private to public with the already-public canonical GitHub repository under explicit owner approval. Post-change Billing & usage is below the Free 50k private-LOC entitlement. No deletion, subscription purchase, source exclusion, Quality Gate change or analysis-method change was needed.

## Safe next operation

`E-P0-T09-01` classified the failure and records the bounded owner-approved visibility remediation that returned private LOC below entitlement. `E-P0-T09-02` is the pending controlled evidence-PR → protected-`main` verification cycle. Sonar's latest completed main analysis is still revision `d5cd25bd…`, while canonical GitHub `main` is `484fec34…`; the visibility change did not itself establish a fresh current-main analysis. Push the reviewed evidence branch, require Sonar/Phase 0/CodeQL/GitGuardian (and Dependency Review when present) on the exact PR head, merge only through protected `main`, then require the Sonar check on the exact resulting `main` SHA to complete `success`. No artificial probe commit is needed.
