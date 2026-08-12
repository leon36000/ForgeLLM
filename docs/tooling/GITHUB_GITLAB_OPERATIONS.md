# GitHub and GitLab Operating Model

## 1. Repository bootstrap

Keep the repository private while self-hosted GPU infrastructure and security controls are being established.

### GitHub path

```bash
gh auth status
gh repo create ForgeLLM --private --source=. --remote=origin --push
```

### GitLab path

```bash
glab auth status
glab repo create ForgeLLM --private --source=. --remote-name=origin
```

Review the command and target account before execution. Repository creation is an owner-authorized write action.

## 2. Branch and merge policy

Configure `main` with:

- pull/merge request required;
- at least one independent approval, two for unsafe/FFI/security/release changes;
- stale approvals dismissed after new commits;
- code-owner review after a real team is configured;
- strict required checks;
- resolved conversations required;
- signed commits or verified signatures for release paths where operationally feasible;
- force pushes and deletion disabled;
- linear history or squash policy selected once and documented;
- merge queue only after CI handles merge-group events.

No agent receives blanket bypass rights.

## 3. Issue taxonomy

Use issue forms for:

- research review;
- experiment/reproduction;
- engineering task;
- defect/regression;
- ADR proposal;
- security report through a private channel, not a public issue.

Labels should encode type, phase, backend, evidence status, risk and priority. Avoid using labels as the only state record.

## 4. Pull/Merge request contract

Every PR/MR contains:

- linked task and charter goal;
- scope and non-goals;
- design/ADR impact;
- tests and observed results;
- correctness evidence;
- benchmark evidence when applicable;
- security/supply-chain impact;
- documentation/state updates;
- rollback plan;
- reviewer checklist.

Draft early, merge only when independently verified.

## 5. Actions and CI security

- Minimize `GITHUB_TOKEN` permissions per workflow/job.
- Pin third-party actions to full commit SHAs and annotate the intended release.
- Allow only selected actions/owners at the organization level where available.
- Run untrusted PR validation on hosted or disposable isolated runners without secrets.
- Keep GPU runners in restricted groups accessible only to named private repositories and approved workflows.
- Prefer ephemeral GPU workers; clean model caches and workspaces between jobs.
- Never use `pull_request_target` to execute checkout code from an untrusted fork.
- Separate validation, privileged release and hardware benchmark workflows.

GitLab equivalents use protected branches, protected variables, protected runners/tags and merge-request approval rules. Fork pipelines require the same untrusted-code discipline.

## 6. Required checks

Initial required check: `phase0 / verify`.

Later checks are stable aggregate jobs rather than many path-filtered required jobs, preventing a PR from waiting forever for a skipped check. Merge-queue workflows must listen for the platform's merge-group event.

The included CodeQL and dependency-review jobs are deliberately opt-in for a private bootstrap repository so unsupported plan features cannot deadlock every pull request. After confirming the features are enabled, create repository variables with the exact values below, run each workflow successfully on `main`, and only then add its check to the ruleset:

```text
FORGELLM_ENABLE_CODEQL=true
FORGELLM_ENABLE_DEPENDENCY_REVIEW=true
```

Never make a conditionally skipped check required. Public repositories run the included CodeQL workflow without the opt-in variable, but the private self-hosted GPU policy remains the recommended ForgeLLM starting point.

## 7. Security features

Enable when supported by the selected plan:

- dependency graph and dependency review;
- Dependabot/Renovate updates;
- secret scanning and push protection;
- CodeQL/default code scanning;
- private vulnerability reporting;
- immutable releases;
- artifact attestations and SBOM for distributable binaries;
- rulesets at organization and repository level.

Local Gitleaks/OSV/Trivy checks remain useful even when hosted features are unavailable.

## 8. GitHub Projects and milestones

Use a project board for phase execution, but keep canonical requirements in issues/task packets and Git. Suggested fields:

- phase;
- task ID;
- status;
- owner/reviewer;
- backend;
- risk;
- evidence status;
- target milestone;
- blocked-by.

Automations may move cards based on PR state; they may not mark claims reproduced.

## 9. Releases

A release contains source commit, changelog, supported hardware matrix, known limitations, container digest, model/data notices, SBOM, provenance/attestation, checksums and reproduction command. Nightly benchmark artifacts are not automatically called releases.
