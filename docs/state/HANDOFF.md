# ForgeLLM Handoff

**From state:** S-0007  
**To work:** P0-T09 evidence PR -> protected `main` Automatic Analysis verification, then ADR-0004
**Generated:** 2026-08-17

## Canonical status

- repository: `leon36000/ForgeLLM`;
- protected default branch: `main`;
- P0-T07: complete;
- P0-T08 / CA-03: complete;
- P0-T09 / QG-01: owner-authorized and `in_progress`;
- P0-T04: blocked only on owner host designation;
- P0-T05/P0-T06: blocked behind inventory and workload/SLO gates;
- no model, runtime, backend, kernel, or Transition Atlas implementation is authorized.

## P0-T09 authorization and source

```text
Owner command           autorise P0-T09 / subagent-driven
Recorded date           2026-08-14
Initial base            1b1a3621fcdf4129268663c497cdcd53aed48c29
Latest main recurrence  484fec34007fd89f554c9c03bffa9a5275676602
Tracking issue          #26
Task packet             tasks/open/P0-T09-sonarqube-main-analysis.yaml
```

## Analysis Method now confirmed

The owner supplied an authenticated screenshot of **SonarQube Cloud → ForgeLLM → Analysis method**.

Observed values:

```text
Automatic analysis      enabled
Recommendation          Recommended
CI method selected      no
```

The raw screenshot is not committed. Its sanitized transcription is stored in:

```text
artifacts/governance/P0-T09-sonar-analysis-method-readback.json
```

with SHA-256 evidence binding:

```text
bfab677e68396b0452bf6348be773e974a3f4325768b080961a0f5e936f7e5e1
```

This confirms the current project setting but does not yet choose the final architecture.

## Post-import probe

The owner imported the project into SonarQube Cloud and P0-T09 executed a new probe:

```text
PR #30 head             3bc75c6496953a4a13fece88d6547c2b1de520bd
PR Sonar                94945852247 / success / 0 new issues
main merge              bd03e479ff4649a254c41726b33f2b6e841a0e0c
main Sonar              94946081665 / cancelled / 0 annotations
```

Phase 0 and CodeQL succeeded on the probe path. Therefore project import alone did not repair the `main` analysis failure.

## 2026-08-17 independent read-only diagnosis

The canonical repository was verified clean at `main@484fec34007fd89f554c9c03bffa9a5275676602`, matching `origin/main` and the GitHub `main` head. Isolated Codex, Claude Code, and OpenHands reviews independently converged on the same result without repository modifications.

A fifth recurrence is visible after PR #31:

```text
PR #31 head             a2d68d910e270fe15f590808de5041814a416b1f
PR Sonar                94948153214 / success
main                    484fec34007fd89f554c9c03bffa9a5275676602
main Sonar GitHub check 94948378776 / conclusion cancelled / 0 annotations
Phase 0                 success
CodeQL                  success
```

The reviews also established an important evidence boundary: GitHub check conclusion `cancelled` does **not** establish the internal Sonar background-task status. The internal task may be failed, cancelled, superseded, or otherwise terminated; only authenticated Sonar activity/task evidence can classify it.

Sanitized session evidence is recorded in:

```text
artifacts/governance/P0-T09-readonly-diagnosis-2026-08-17.json
```

A prior controller-browser attempt found no authenticated Sonar session, so it captured no administration values and changed no settings. The owner subsequently supplied authenticated Sonar UI screenshots directly: one exposes the subscription LOC-limit error and analysis ID, and a second Background Tasks screenshot establishes the internal branch-analysis task status as `FAILED`.

## Current classification

```text
analysis_method_setting automatic_enabled
compatibility           recommended
failure_classification  platform_limitation
failure_subtype         subscription_loc_limit_exceeded
analysis_id             472eadb9-b554-47ca-8336-2033fb3b7408
background_task_id      AaADNoZ4U0I7o8og6Mb6
internal_task_status    FAILED
method_selection        not_selected
configuration_changes   sonar_visibility_private_to_public_only
```

## Current block

Experiment **`E-P0-T09-01`** is now classified by owner-authenticated Sonar UI evidence: the analysis failed because total lines of code in the organization exceed the current subscription limit. The screenshot exposes analysis ID `472eadb9-b554-47ca-8336-2033fb3b7408`; the raw image is not committed and its hash-bound sanitized transcription is stored in the diagnosis artifact.

A second owner-provided Background Tasks screenshot shows a branch analysis task `AaADNoZ4U0I7o8og6Mb6` with internal status `FAILED`, submitted/started at 22:18:20 and finished at 22:18:23, immediately after pull-request task `AaADNKJHGgg5GiBgCda_` succeeded from 22:16:16 to 22:16:18. Public GitHub correlation strongly maps this pair to PR #31 and current `main`: assuming the Sonar UI timestamps are UTC−04:00, their finish times match checks `94948153214` and `94948378776` exactly to the second, and the checks point to `pullRequest=31` and `branch=main`. This remains strong correlation rather than definitive ID binding because GitHub exposes no Sonar background-task ID.

Independent remediation reviews then established:

```text
CI-based analysis bypasses LOC limit      no
justified ForgeLLM source exclusions      none identified
ForgeLLM maintained non-test Python       ~5k physical lines
```

Switching scanners is not a remedy for the diagnosed subscription limit, and adding exclusions merely to reduce billing would violate QG-01.

The owner subsequently authenticated manually in the isolated OpenClaw browser. A targeted before/after readback verified `ForgeLLM / leon36000_ForgeLLM` was Private while bound to the already-public GitHub repository and using Automatic Analysis. The then-current P0-T09 packet still contained a broad no-Sonar/GitHub-setting freeze before ADR-0004; the owner-directed visibility change is recorded as a bounded exception to that packet, not as retroactive authorization by the pre-change packet. Under a local single-use approval recorded outside Git, OpenClaw changed **only** Project visibility from `Private` to `Public - Anyone`; project key, GitHub binding and Automatic Analysis remained unchanged.

Independent anonymous Sonar Web API reads then returned HTTP 200 and confirmed:

```text
visibility                    public
binding                       https://github.com/leon36000/ForgeLLM
automatic analysis            enabled
latest completed main ncloc   1658
quality gate                  OK / Sonar way
latest completed main         d5cd25bd9d6fc3f9cded27781c2051939dcdde85
canonical GitHub main         484fec34007fd89f554c9c03bffa9a5275676602
```

Billing & usage after the change reports:

```text
plan                           Free
private LOC entitlement        50000
private LOC consumed           48248
remaining                      approximately 1.8k
```

The organization is therefore back below the private-LOC limit. Final readback also records binding `leon36000/ForgeLLM`, New Code `previous_version`, no custom analysis-scope or issue-ignore values, Automatic Analysis/Autoscan, no CI method selected, and the default `Sonar way` Quality Gate. The latest completed Sonar main analysis is still stale relative to current GitHub `main`, so the visibility change alone is not proof of recovery. Use the evidence-update PR itself as the controlled trigger; no artificial probe commit is needed.

## Decision gate after readback

The organization LOC blocker has been remediated by the smallest evidence-supported action: align ForgeLLM Sonar visibility with its already-public canonical repository. No source exclusion, project deletion, subscription purchase or analysis-method change was needed.

Next: complete the evidence-update PR. Require Sonar, Phase 0, CodeQL and GitGuardian on its exact head; merge only after review; then require the resulting protected `main` Sonar check to complete successfully. If this cycle succeeds, ADR-0004 can select the retained analysis architecture from evidence rather than speculation.

ADR-0004 will select exactly one analysis method:

- `automatic_only`, or
- `ci_based_only`.

Method selection is orthogonal to the current LOC-limit failure: CI-based analysis does not bypass the subscription entitlement. The methods may never run concurrently.

## Exact oracle preserved

Future implementations must continue to use CA-03 as their correctness oracle. P0-T09 may not alter speculative-decoding semantics to satisfy a scanner.

## Evidence limits

P0-T09 now establishes Automatic Analysis enabled/recommended, the repeated PR-success/`main` failure pattern, internal branch-task status `FAILED`, direct failure classification `platform_limitation / subscription_loc_limit_exceeded`, owner-authorized visibility remediation, anonymous proof that ForgeLLM is now public, and post-change private LOC below the Free entitlement. It does **not** yet establish a healthy Sonar analysis on current GitHub `main` or the final ADR method selection.
