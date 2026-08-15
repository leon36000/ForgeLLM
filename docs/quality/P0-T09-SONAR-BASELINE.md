# P0-T09 SonarQube Cloud Read-Only Baseline

- **Task:** P0-T09 / QG-01
- **Owner authorization:** `P0-T09 / subagent-driven`, recorded 2026-08-14
- **Canonical base:** `1b1a3621fcdf4129268663c497cdcd53aed48c29`
- **Mode:** read-only diagnosis
- **Configuration changes:** none
- **Method selection:** not selected
- **Current classification:** `automatic_analysis_enabled_root_cause_unknown`

Machine-readable evidence:

- `artifacts/governance/P0-T09-sonar-baseline.json`;
- `artifacts/governance/P0-T09-sonar-analysis-method-readback.json`.

## Evidence question

Why does the SonarQube Cloud GitHub App repeatedly produce a successful pull-request quality gate for ForgeLLM while its automatic check on the resulting protected `main` commit is completed as `cancelled` with the title `SonarQube Cloud analysis failed` and no GitHub annotations?

The public GitHub evidence establishes the pattern. The owner-authenticated Analysis Method screenshot now proves that automatic analysis is enabled and recommended for this project, but the failed `main` analysis activity/task message is still missing, so root cause remains unclassified.

## Canonical project identifiers

| Field | Readback | Evidence quality |
|---|---|---|
| GitHub repository | `leon36000/ForgeLLM` | canonical Git |
| Sonar project key | `leon36000_ForgeLLM` | GitHub check `details_url` |
| Sonar instance | `https://sonarcloud.io` | GitHub check `details_url` |
| GitHub App | `sonarqubecloud`, app ID `12526` | GitHub check-run payload |
| Sonar binding | not yet read back | missing |
| Analysis Method setting | `Automatic analysis` enabled | owner-authenticated screenshot |
| Compatibility/recommendation | `Recommended` | owner-authenticated screenshot |
| CI method selected | no | owner-authenticated screenshot |
| Last analysis method | not displayed/read back | missing |

The sanitized screenshot transcription is stored in `artifacts/governance/P0-T09-sonar-analysis-method-readback.json`. The raw image is not committed; its SHA-256 is recorded as `bfab677e68396b0452bf6348be773e974a3f4325768b080961a0f5e936f7e5e1`.

## Observed analysis matrix

| Context | Commit | Sonar check | Sonar result | Annotations | Phase 0 | CodeQL |
|---|---|---:|---|---:|---|---|
| PR #24 implementation | `16d65288…` | `94869018087` | cancelled / analysis failed | 36 | success | success |
| PR #25 remediation | `a7f508fe…` | `94889986512` | Quality Gate passed | 0 | success | success |
| `main` after remediation | `e81c1c0a…` | `94890528740` | cancelled / analysis failed | 0 | success | success |
| PR #27 closeout | `5c1f7c6c…` | `94892322303` | Quality Gate passed | 0 | success | success |
| `main` after closeout | `e669f5e1…` | `94892860919` | cancelled / analysis failed | 0 | success | success |
| PR #28 planning | `f60373b3…` | `94894565075` | Quality Gate passed | 0 | success | success |
| `main` after planning | `1b1a3621…` | `94894966719` | cancelled / analysis failed | 0 | success | success |
| PR #30 post-import probe | `3bc75c64…` | `94945852247` | Quality Gate passed | 0 | success | success |
| `main` after post-import probe | `bd03e479…` | `94946081665` | cancelled / analysis failed | 0 | success | success |

The post-import probe shows that importing the project was not sufficient to repair the `main` analysis path: the PR quality gate passed after import, while the resulting `main` check still failed in the same annotation-free way.

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

The official automatic-analysis documentation states that automatic and CI-based analysis must not be used concurrently for the same project. It also states that automatic-analysis logs are unavailable; CI-based analysis is required when scanner logs are needed. The Web API documentation states that administrative services require the appropriate authorization.

## Evidence that is still required

The read-only gate still requires:

1. project key and bound GitHub repository readback;
2. binding status;
3. **last analysis method** if available;
4. activity/compute-task message for at least one failed `main` analysis;
5. quality-gate definition and current project status;
6. new-code definition;
7. analysis scope, exclusions, and issue-ignore settings;
8. project plan/tier relevant to pull-request and branch analysis;
9. confirmation that no external CI scanner submits to this project.

Administrative payloads must be sanitized or represented by cryptographic hashes. Credentials, user lists, email addresses, tokens, and private organization data must not enter Git.

## Current classification

```text
analysis_method_setting = automatic_enabled
compatibility           = recommended
failure_classification  = automatic_analysis_enabled_root_cause_unknown
method_selection        = not_selected
configuration_changes   = none
```

Possible root-cause categories remain:

- automatic-analysis configuration error;
- binding or permission error;
- source-detection or scope error;
- automatic-analysis platform limitation;
- transient Sonar service failure;
- unknown because the failed-task evidence is unavailable.

The most important missing item is now the detailed **Project Activity / failed main analysis** message. Choosing `automatic_only` or `ci_based_only` before reading that message would still be conjectural.

## Safe next operation

The next operation remains read-only: open **Project Activity**, select the latest failed `main` analysis associated with commit `bd03e479ff4649a254c41726b33f2b6e841a0e0c` / check `94946081665`, and capture the analysis/task ID, status, and detailed sanitized error message. No Sonar toggle or setting should be changed yet.
