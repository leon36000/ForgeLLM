# P0-T09 SonarQube Cloud Read-Only Baseline

- **Task:** P0-T09 / QG-01
- **Owner authorization:** `P0-T09 / subagent-driven`, recorded 2026-08-14
- **Canonical base:** `1b1a3621fcdf4129268663c497cdcd53aed48c29`
- **Branch:** `feat/p0-t09-sonar-diagnosis`
- **Mode:** read-only diagnosis
- **Configuration changes:** none
- **Method selection:** not selected
- **Current classification:** `unknown_due_to_missing_authenticated_evidence`

The machine-readable baseline is `artifacts/governance/P0-T09-sonar-baseline.json`.

## Evidence question

Why does the SonarQube Cloud GitHub App repeatedly produce a successful pull-request quality gate for ForgeLLM while its automatic check on the resulting protected `main` commit is completed as `cancelled` with the title `SonarQube Cloud analysis failed` and no GitHub annotations?

The public evidence establishes the pattern. It does not expose the Sonar project administration setting or the failed analysis task message needed to establish the cause.

## Canonical project identifiers

| Field | Readback | Evidence quality |
|---|---|---|
| GitHub repository | `leon36000/ForgeLLM` | canonical Git |
| Sonar project key | `leon36000_ForgeLLM` | GitHub check `details_url` |
| Sonar instance | `https://sonarcloud.io` | GitHub check `details_url` |
| GitHub App | `sonarqubecloud`, app ID `12526` | GitHub check-run payload |
| Sonar binding | not authenticated/read back | missing |
| Analysis Method setting | not authenticated/read back | missing |
| Last analysis method | not authenticated/read back | missing |

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

The three successive pull-request/`main` pairs reproduce the same separation. A general repository test or CodeQL failure is therefore not established by the public evidence.

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

The 34 test warnings shared one rule family: exception assertions should contain only one invocation capable of throwing. They are recorded as baseline debt rather than silently accepted or suppressed by P0-T09.

## Repository configuration readback

The canonical Git tree at `3996362aa40dd951a3a4cd97b87ad9cb1988b710` contains:

- no `.github/workflows/sonar.yml`;
- no `sonar-project.properties`;
- no `.sonarcloud.properties`.

The SonarQube Cloud GitHub App nevertheless produces pull-request and `main` checks. This is **consistent with** automatic analysis, but it is not an authenticated readback of **Administration → Analysis Method**. External CI submission to the same project also remains unknown.

## Official-document constraints

The diagnosis uses these primary SonarQube Cloud references:

- <https://docs.sonarsource.com/sonarqube-cloud/advanced-setup/automatic-analysis>
- <https://docs.sonarsource.com/sonarqube-cloud/analyzing-source-code/ci-based-analysis/overview-of-integrated-cis>
- <https://docs.sonarsource.com/sonarqube-cloud/appendices/troubleshooting>
- <https://docs.sonarsource.com/sonarqube-cloud/appendices/web-api>
- <https://docs.sonarsource.com/sonarqube-cloud/administering-sonarcloud/resources-structure/projects>

The official automatic-analysis documentation states that automatic and CI-based analysis must not be used concurrently for the same project. It also states that automatic-analysis logs are unavailable; CI-based analysis is required when scanner logs are needed. The Web API documentation states that administrative services require the appropriate authorization.

## Evidence that is still required

The read-only gate cannot select an analysis method until the owner-authenticated Sonar project readback supplies:

1. project key and bound GitHub repository;
2. project binding status;
3. **Administration → Analysis Method** value;
4. last analysis method;
5. automatic-analysis compatibility result;
6. activity/compute-task message for at least one failed `main` analysis;
7. quality-gate definition and current project status;
8. new-code definition;
9. analysis scope, exclusions, and issue-ignore settings;
10. project plan/tier relevant to pull-request and branch analysis;
11. confirmation that no external CI scanner submits to this project.

Administrative payloads must be sanitized or represented by cryptographic hashes. Credentials, user lists, email addresses, tokens, and private organization data must not enter Git.

## Current classification

```text
failure_classification = unknown_due_to_missing_authenticated_evidence
method_selection       = not_selected
configuration_changes  = none
```

Possible categories remain:

- configuration error;
- binding or permission error;
- source-detection or scope error;
- automatic-analysis platform limitation;
- transient Sonar service failure;
- unknown because evidence is unavailable.

Choosing `automatic_only` or `ci_based_only` now would be conjectural and would violate the approved plan.

## Safe next operation

The next operation is still read-only: capture the listed Sonar project fields through the owner-authenticated UI or API. Only after that evidence is committed in sanitized form may ADR-0004 select exactly one analysis method and authorize a configuration change.
