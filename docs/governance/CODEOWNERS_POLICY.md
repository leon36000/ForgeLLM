# CODEOWNERS Activation Policy

No active `.github/CODEOWNERS` file is included because the owner, organization and teams do not yet exist in canonical state. A fabricated team name would create a false control.

After P0-T02 establishes the private remote:

1. create at least `architecture`, `runtime`, `accelerators`, `security`, `benchmarks` and `governance` maintainer groups or named owners;
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

Do not enable code-owner enforcement until the file resolves to real reviewers; otherwise merges may become either falsely trusted or permanently blocked.
