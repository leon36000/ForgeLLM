# ForgeLLM Handoff

**From state:** S-0004  
**To task:** P0-T03 completion  
**Generated:** 2026-08-13

## Canonical decision

The owner intentionally keeps `leon36000/ForgeLLM` public. Issue #8 and ADR-0003 supersede every prior private-visibility assumption.

The public repository contains source, governance, public research metadata and sanitized evidence only. Restricted weights, datasets, prompts, traces, operational identifiers and secrets remain outside Git. Git is canonical; any RAG or external app is a derived service.

## Direct evidence before the P0-T03 PR

- visibility: public;
- default branch: main;
- main commit: `843f8127f76a0c7f2ef9863853dccaddeff90aa8`;
- main `protected=false`;
- required-status-check enforcement off;
- rulesets: none;
- protection, Actions-permission and code-alert admin endpoints: integration `403`.

## Implemented on `agent/p0-t03-public-repository-hardening`

- ADR-0003 and public repository policy;
- public security reporting entry point;
- public-data, private-asset and no-license notices;
- Dependency Review enabled for internal public PRs;
- read-only audit with pass/fail/unknown semantics;
- solo branch-protection payload with zero fabricated human approvals;
- unit tests for repository audit and protection payload;
- S-0004 state, decisions, risks, open questions and mobile projection.

## Remaining evidence to collect

1. exact PR head and commit tree;
2. `Validate and test` run/job and 16 expected tests if all new tests are collected;
3. CodeQL run/job and explicit alert-visibility limitation;
4. Dependency Review run/job and conclusion;
5. fresh-context review report and owner disposition;
6. direct protection/ruleset evidence after the owner-admin action.

## Manual owner-admin checkpoint

From an authenticated workstation with GitHub CLI:

```bash
python scripts/github/apply_branch_protection.py \
  --repo leon36000/ForgeLLM \
  --human-approvals 0

FORGELLM_CONFIRM_GITHUB_ADMIN_WRITE=YES \
python scripts/github/apply_branch_protection.py \
  --repo leon36000/ForgeLLM \
  --human-approvals 0 \
  --apply

python scripts/github/audit_repository.py \
  --repo leon36000/ForgeLLM \
  --expected-visibility public \
  --output artifacts/governance/github-audit-s0004.json \
  --strict
```

Review the dry-run payload before setting the confirmation variable. Preserve output and rollback instructions. If the API rejects zero approvals, use a GitHub ruleset that still requires pull requests and checks without inventing another identity.

## Hard blocker

No self-hosted runner, secret-bearing workflow or P0-T04 hardware inventory may start until direct evidence reports `main` protected or an enforced equivalent ruleset.

## Tool routing

Use GitHub/CodeQL and Codex Engineering Guardrails now. SonarQube needs a reachable configured server before its results can count. Fallow is not applicable to the current language surface. Consensus, Neon, Temporal and NVIDIA/AMD skills require separate bounded tasks and must not expand P0-T03.
