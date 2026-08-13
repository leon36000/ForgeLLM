# ForgeLLM Solo-Project Review Policy

**Status:** active while ForgeLLM has one human maintainer  
**Effective date:** 2026-08-13

## Purpose

ForgeLLM must preserve meaningful independence between implementation, verification and final authorization without manufacturing a second GitHub identity controlled by the same person.

A second account owned by the project owner is not an independent reviewer and must not be used to satisfy an approval rule.

## Current operating model

While the project has one human maintainer:

1. one agent or isolated context authors the change;
2. a different agent or fresh review context evaluates the task packet, diff, tests, evidence and residual risks;
3. GitHub Actions runs the required reproducibility gate on the exact head commit;
4. the human owner makes the final merge decision;
5. the review report is committed or attached to the pull request.

The reviewer must start from the task requirements and resulting diff, not from the implementer’s private reasoning. It must record inspected files, commands or CI evidence, findings, limitations and a verdict.

## GitHub approval settings

Until a second real human collaborator exists, ForgeLLM does not require a GitHub approval count that the sole author cannot legitimately satisfy. The repository should still require:

- pull requests for changes to `main` after bootstrap;
- the `Validate and test` status check;
- resolved conversations;
- no force push or deletion of `main`;
- owner review of the committed independent-agent report.

When a real second maintainer joins, the project must enable at least one human approval and CODEOWNERS review for relevant paths.

## High-risk exception

Independent human review remains required before any public release or irreversible high-risk deployment involving:

- unsafe Rust or memory ownership across the C ABI;
- CUDA/HIP kernels whose failure could corrupt memory;
- repository credentials, signing, release provenance or privileged runners;
- security-sensitive network services;
- published headline performance claims;
- destructive migration or compatibility removal.

Such work may be researched and prototyped privately, but it is not released or declared production-ready without a qualified human reviewer other than the author.

## Evidence requirements

A solo-project review report records:

- task ID and exact base/head commits;
- review context identity or role;
- files and mechanisms inspected;
- CI run and job identifiers;
- findings by severity;
- unresolved risks and unverified areas;
- verdict: `ACCEPT`, `CHANGES_REQUIRED` or `REJECTED`;
- owner disposition.

## Transition condition

This policy is superseded when ForgeLLM has a second real human maintainer with repository access. At that point, update `tools/repository-policy.yaml`, create an active `.github/CODEOWNERS`, and require human approval in the branch ruleset.
