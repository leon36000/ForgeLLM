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
2. screenshots with usernames, email addresses, tokens, billing data, and unrelated organization projects redacted;
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

## Step 3 — Read the failed main analysis activity

Open Project Activity and locate a failed `main` analysis corresponding to one of these commits/checks:

```text
e81c1c0ad0b161844569df46ee62246c9de56698 / check 94890528740
e669f5e1a6913005fbba8d34e9ba8bdfce91c460 / check 94892860919
1b1a3621fcdf4129268663c497cdcd53aed48c29 / check 94894966719
```

Record:

```text
analysis or task ID
status
sanitized error message
commit or analysis date
analysis method, when displayed
```

The precise error message is required. `SonarQube Cloud analysis failed` from GitHub is not enough to classify the cause.

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

## Step 7 — Read plan/tier

Record only the plan name and feature statements relevant to:

```text
pull-request analysis
main-branch analysis
other branch analysis
automatic analysis
```

Do not include billing amounts or payment data.

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
failed main task message
quality gate
new code definition
scope and issue-ignore settings
plan/tier
external scanner confirmation
```

Until then:

```text
failure_classification = unknown_due_to_missing_authenticated_evidence
method_selection       = not_selected
configuration_changes  = none
```
