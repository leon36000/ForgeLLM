# CODEOWNERS Activation Policy

No active `.github/CODEOWNERS` file is included while ForgeLLM has only one human maintainer. A fabricated team name or a second account controlled by the same person would create a false control rather than independent review.

The active solo-project review model is defined in `docs/governance/SOLO_PROJECT_REVIEW_POLICY.md`:

- a distinct agent or fresh context reviews the task, diff and evidence;
- GitHub Actions validates the exact head commit;
- the owner makes the final merge decision;
- the review report is preserved in Git or on the pull request.

After a second real human collaborator exists:

1. create appropriate `architecture`, `runtime`, `accelerators`, `security`, `benchmarks` and `governance` maintainer groups or named owners;
2. verify every referenced user/team has repository access;
3. add `.github/CODEOWNERS` with the narrowest useful paths;
4. enable required code-owner review through the repository ruleset;
5. test the rule with a draft pull request before treating it as active.

Suggested ownership domains:

```text
/AGENTS.md                                      governance owners
/chatgpt/                                      governance owners
/docs/architecture/                            architecture owners
/docs/research/ /research/                     research owners
/docs/benchmarks/ /schemas/benchmark-*         benchmark owners
/.github/ /.gitlab/ /docs/governance/          security + governance owners
/src/forgellm_governance/ /scripts/            tooling owners
/crates/runtime/                               runtime owners
/backends/cuda/                                NVIDIA backend owners
/backends/hip/                                 AMD backend owners
/backends/cpu/                                 CPU backend owners
```

Do not enable code-owner enforcement until the file resolves to real independent reviewers; otherwise merges may become either falsely trusted or permanently blocked.
