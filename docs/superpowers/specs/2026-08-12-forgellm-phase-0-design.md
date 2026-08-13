# ForgeLLM Phase 0 Operating System — Design Specification

**Date:** 2026-08-12  
**Status:** accepted for scaffold generation  
**Scope:** project memory, research governance, agent execution, validation and repository automation; no inference-engine implementation.

## 1. Purpose

ForgeLLM needs a durable operating system before multiple mobile and coding agents begin architecture or implementation work. The design prevents the project from depending on hidden chat memory, unsupported claims or ad-hoc agent behavior.

## 2. Source-of-truth model

The canonical state is a version-controlled repository. ChatGPT project files are a compact projection for mobile use, not an independent authority. Accepted ADRs, state registries, task packets, source records and raw experiment artifacts are append-only or explicitly superseded rather than silently rewritten.

Authority order:

1. explicit owner instruction;
2. project charter;
3. accepted ADRs;
4. current state and decision/risk/question registries;
5. active task packet;
6. repository agent instructions;
7. current conversation.

## 3. Mobile context design

The mobile bundle contains exactly five compact files:

- core mission and architecture;
- agent operating system;
- research and evidence protocol;
- current state and decisions;
- reusable prompts and workflows.

Project instructions require a startup readback and a closeout state update. Any detailed artifact remains in Git and is referenced by immutable commit or file path.

## 4. Agent execution design

`AGENTS.md` is the cross-agent root contract. `CLAUDE.md` imports it for Claude Code; `.github/copilot-instructions.md` adapts it for GitHub tooling. Specialized rules cover research, tests and security. Every task packet includes goal, non-goals, files, interfaces, acceptance tests, evidence requirements and completion report.

Agents work in isolated branches/worktrees, use test-first or oracle-first changes, and cannot alter architecture, dependencies, public interfaces or benchmark methods without an ADR or explicit task authorization.

## 5. Research design

Research is claim-centered rather than link-centered. The project stores:

- a repository catalog;
- a paper catalog;
- a claim ledger;
- repeatable discovery queries;
- evidence levels and reproduction status.

Official repositories, papers and specifications establish external support; they do not prove ForgeLLM performance. Every external benchmark claim is marked `external_unreproduced` until matched conditions and raw artifacts are reviewed.

The initial landscape has ten primary reference stacks plus specialized systems. “Primary” means broad architectural relevance, not a permanent popularity ranking.

## 6. Verification design

JSON Schema defines benchmark results and task packets. Python validators check required project files, YAML structure, unique identifiers, cross-references, benchmark invariants and absence of obvious secret-like content. Unit tests exercise valid and invalid cases. `make ci` is the complete local and CI gate; `make verify` remains the structural-and-test subset.

The benchmark schema captures source commits, clean-tree status, hardware/software/model/workload manifests, correctness gate, raw samples, statistics, artifacts and conclusion scope.

## 7. GitHub and GitLab design

GitHub is the recommended primary collaboration plane; GitLab templates and CI are supplied for mirroring or an alternative host. The repository includes issue forms, pull-request review fields, Dependabot configuration, CodeQL, SHA-pinned hosted CI and manual GPU inventory workflows.

GPU runners are private and privileged only as necessary. They never execute code from untrusted forks. Branch protection, required checks, merge queue, CODEOWNERS and secret controls are configured after the owner chooses account, organization, visibility and maintainers.

## 8. Error handling and failure policy

Validation failures print actionable paths and messages and return non-zero. Research refresh scripts preserve prior records and stage machine-readable candidates; they do not silently promote claims. Hardware probes tolerate missing vendor tools and record `unavailable` rather than inventing values. Missing verification is reported as unverified, never as success.

## 9. Security and licensing

No secret is committed. CI actions are SHA-pinned. Dependencies are locked and reviewed. No project license is assumed; the repository remains private until the owner accepts a licensing ADR. Phase 0 stores original analysis and citations but does not vendor third-party implementations.

## 10. Acceptance criteria

Phase 0 is structurally complete when:

- all required files exist;
- schemas validate supplied examples;
- catalog cross-references resolve;
- unit tests and `make ci` pass;
- mobile and full-repository archives have SHA-256 manifests;
- no external performance claim is labeled reproduced;
- unresolved owner decisions are explicit in state files.

## 11. Deliberate exclusions

This design does not select the first production model, target GPU, project license, repository organization or benchmark SLO. It does not install GPU drivers, publish a repository, execute paid workloads or implement ForgeRT. Those actions require owner and laboratory inputs recorded in Phase 0 tasks.
