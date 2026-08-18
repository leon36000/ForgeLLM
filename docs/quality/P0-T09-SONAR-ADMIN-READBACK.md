# P0-T09 Owner-Authenticated Sonar Readback

## Purpose

This procedure collects the minimum read-only SonarQube Cloud evidence required to classify QG-01 without exposing credentials or changing project configuration.

Do not toggle a setting, create a token, accept an issue, change a quality gate, or add an exclusion while following this procedure.

## Project

Open the ForgeLLM SonarQube Cloud project while signed in as the project owner or administrator:

```text
https://sonarcloud.io/dashboard?id=leon36000_ForgeLLM&branch=main
```

Use `artifacts/governance/P0-T09-sonar-admin-readback.template.json` as the field checklist.

## Safe evidence formats

Provide one of:

1. the completed template with private values removed;
2. screenshots with usernames, email addresses, tokens, prices/payment details, billing contacts, and unrelated private project identities redacted; LOC entitlement/usage values needed by P0-T09 may remain visible;
3. sanitized text readback with the visible labels and values;
4. hashes of private screenshots plus a sanitized transcription of the fields that affect the decision.

Never provide a token value, browser cookie, request authorization header, or full private API response.

## Step 1 — Confirm project binding

Locate the project binding or repository information page. Record only:

```text
project key
DevOps provider
bound repository owner/name
binding status
public organization slug, when already public
```

Expected repository:

```text
leon36000/ForgeLLM
```

Do not record user lists or email addresses.

## Step 2 — Read Analysis Method

Navigate to:

```text
Project → Administration → Analysis Method
```

Record exactly:

```text
Automatic Analysis: enabled / disabled
compatibility result or recommendation text
last analysis method, when displayed
CI tutorial or scanner method selected, when displayed
```

Do not change the toggle.

A screenshot of this page is the most load-bearing evidence for choosing `automatic_only` or `ci_based_only`.

## Step 3 — Read the main analysis activity behind a failed/cancelled GitHub check

Open Project Activity and locate a failed `main` analysis corresponding to one of these commits/checks:

```text
e81c1c0ad0b161844569df46ee62246c9de56698 / check 94890528740
e669f5e1a6913005fbba8d34e9ba8bdfce91c460 / check 94892860919
1b1a3621fcdf4129268663c497cdcd53aed48c29 / check 94894966719
bd03e479ff4649a254c41726b33f2b6e841a0e0c / check 94946081665
484fec34007fd89f554c9c03bffa9a5275676602 / check 94948378776
```

Record:

```text
analysis or task ID
status
sanitized error message
commit or analysis date
analysis method, when displayed
```

The precise internal status and error message are required. GitHub check conclusion `cancelled` and title `SonarQube Cloud analysis failed` describe the GitHub check-run surface; they do not prove that the Sonar background task itself had status `CANCELED` and are not enough to classify the cause.

## Step 4 — Read Quality Gate

Open the project quality-gate view or administration page. Record:

```text
quality gate name
current main project status
condition names, operators, thresholds, and whether they apply to new code or overall code
```

Do not change a threshold or assign a different gate.

## Step 5 — Read New Code definition

Navigate to the project New Code settings and record:

```text
definition type
reference branch, previous version, or number of days
visible parameter value
```

Do not modify it.

## Step 6 — Read analysis scope and issue exclusions

Inspect project settings for:

```text
source inclusions and exclusions
test inclusions and exclusions
coverage exclusions
duplication exclusions
issue exclusions
Ignore Issues on Multiple Criteria entries
```

For each multi-criteria entry, record the rule key and whether a file pattern is present. A previous Sonar community case shows that an incomplete multi-criteria entry can make automatic analysis fail; this is a hypothesis to check, not an assumed cause.

Do not reveal private paths outside this public repository.

## Step 7 — Read Billing & usage / LOC entitlement

Open the organization **Billing & usage** view. Record only the fields needed to resolve the diagnosed LOC blocker:

```text
plan/tier name
organization LOC entitlement / limit
current organization LOC consumption
remaining or exceeded LOC, if displayed
per-project counted LOC
per-project Sonar visibility: public / private
largest counted branch, when displayed
last analysis date or activity age, when useful to identify an obsolete project
```

For unrelated or private projects, do not commit their names or keys. Use stable sanitized labels such as `private_project_A` and preserve any private screenshot only outside Git with a cryptographic hash. Public project names may be recorded only when already public and relevant to the decision.

Do not record prices, card/payment data, invoices, personal billing contacts, or unrelated organization metadata. Do not click Upgrade, Change plan, Delete, or visibility controls during this readback.

The LOC blocker cannot be remediated by switching Automatic Analysis to CI-based analysis: the organization entitlement is enforced by SonarQube Cloud after submission. Do not add exclusions merely to reduce billing; exclusions require a reviewed source-ownership rationale independent of quota pressure.

## Step 8 — Confirm external scanner absence or presence

Confirm whether any system outside the canonical GitHub workflows submits Sonar analyses for project `leon36000_ForgeLLM`:

```text
another GitHub Actions workflow
GitLab CI mirror
local scanner
Jenkins, CircleCI, TravisCI, or other CI
scheduled automation
```

Record `false` only when verified. Otherwise use `unknown` and identify what remains unchecked.

## Step 9 — Timestamp and sanitize

For every readback section, record an absolute UTC timestamp.

Before sharing or committing evidence, remove:

- token values;
- cookies and authorization headers;
- personal emails;
- usernames not already public through GitHub;
- unrelated organization/project names;
- billing and payment information.

## Completion criterion

The read-only gate is complete only when the following fields have evidence:

```text
binding
analysis method
failed main task status/error and task/analysis-to-SHA binding
quality gate
new code definition
scope and issue-ignore settings
plan/tier
organization LOC entitlement and current usage
ForgeLLM visibility/LOC contribution before/after remediation, plus organization entitlement/current usage sufficient to prove the selected LOC remedy
external scanner confirmation or bounded evidence that no canonical/selected CI scanner exists
```

For the current P0-T09 evidence after owner-authorized remediation:

```text
failure_classification = platform_limitation
failure_subtype        = subscription_loc_limit_exceeded
internal_task_status   = FAILED
visibility_before      = private
visibility_after       = public
private_loc_after      = 48248 / 50000
new_code_definition    = previous_version
scope_customizations   = none/default
method_selection       = not_selected
configuration_changes  = sonar_visibility_private_to_public_only
```

The historical failed task/analysis-to-SHA field may remain explicitly `strongly_correlated_not_shared_identifier_verified` when the failure class/status are directly observed and no public/shared task identifier exists. This does not substitute for the required post-remediation current-head PR/main verification.
