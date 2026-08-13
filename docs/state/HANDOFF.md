# ForgeLLM Handoff

**From state:** S-0004  
**To task:** P0-T03 owner-admin completion  
**Generated:** 2026-08-13

## Canonical decision

The owner intentionally keeps `leon36000/ForgeLLM` public. Issue #8 and ADR-0003 supersede every prior private-visibility assumption.

The public repository contains source, governance, public research metadata and sanitized evidence only. Restricted weights, datasets, prompts, traces, operational identifiers and secrets remain outside Git. Git is canonical; any RAG or external app is a derived service.

## Direct repository state

- visibility: public;
- default branch: main;
- main before P0-T03: `843f8127f76a0c7f2ef9863853dccaddeff90aa8`;
- `main.protected=false`;
- required-status-check enforcement off;
- rulesets: none;
- protection, Actions-permission and code-alert admin endpoints: integration `403`.

## Reviewed implementation evidence

Head `9d3b47365aa017f37b16a6f8c7e307677a7526cf`:

- Phase 0 run `31681837631`, job `94388820133`: success; Ruff, all active validators, five mobile hashes, **17 tests** and bootstrap dry-run passed;
- CodeQL run `31681837665`, job `94388813356`: success; 62 modules, 52 queries, SARIF uploaded/processed; alert details unknown;
- Dependency Review run `31681837651`: skipped by opt-in;
- earlier Dependency Review probe `31681032967` / `94386280488`: failed because Dependency Graph is disabled, with no dependency result.

Fresh review: `docs/reviews/P0-T03-PUBLIC-REPOSITORY-REVIEW.md`, verdict `ACCEPT` for the PR while P0-T03 remains blocked.

The review discovered and fixed a security false positive: an unrelated or disabled ruleset no longer counts as protection for `main`; the branch endpoint must report `protected=true`.

## Implemented on PR #9

- ADR-0003 and public repository policy;
- public security reporting entry point;
- public-data, private-asset and no-license notices;
- typed read-only audit with pass/fail/unknown states;
- solo branch-protection payload with zero fabricated human approvals;
- tests for inaccessible controls, unrelated rulesets and protection payload;
- S-0004 state, decisions, risks, roadmap and mobile projection;
- explicit failed Dependency Review capability probe.

## Remaining owner-admin checkpoint

### Protect `main`

From an owner-authenticated workstation with GitHub CLI:

```bash
python scripts/github/apply_branch_protection.py \
  --repo leon36000/ForgeLLM \
  --human-approvals 0

FORGELLM_CONFIRM_GITHUB_ADMIN_WRITE=YES \
python scripts/github/apply_branch_protection.py \
  --repo leon36000/ForgeLLM \
  --human-approvals 0 \
  --apply
```

Then verify:

```bash
python scripts/github/audit_repository.py \
  --repo leon36000/ForgeLLM \
  --expected-visibility public \
  --output artifacts/governance/github-audit-s0004.json \
  --strict
```

If classic protection rejects zero approvals, configure an equivalent repository ruleset that requires PRs and checks without inventing another identity. Preserve the exact write, response and rollback.

### Optional Dependency Review

Enable **Dependency graph** in repository security settings. Then set `FORGELLM_ENABLE_DEPENDENCY_REVIEW=true`, open an internal PR and observe a successful run before considering the check required.

### CodeQL triage

Inspect code-scanning alerts through an owner-authorized UI or `gh` session. Do not infer zero alerts from the successful workflow.

## Hard blocker

No self-hosted runner, secret-bearing workflow, P0-T04 hardware inventory or inference work may start until direct evidence reports `main` protected or an enforced equivalent ruleset.

## Tool routing

Use GitHub/CodeQL and Codex Engineering Guardrails for this task. SonarQube requires a reachable configured server. Fallow is not applicable to the current languages. Consensus, Neon, Temporal and NVIDIA/AMD skills require separate bounded tasks and must not expand P0-T03.
