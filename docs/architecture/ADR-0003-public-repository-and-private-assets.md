# ADR-0003: Public source repository with strict private-asset separation

- **Status:** accepted
- **Date:** 2026-08-13
- **Owners:** ForgeLLM project owner; security and governance reviewer roles
- **Related issue:** #8
- **Related task:** P0-T03
- **Supersedes:** private-visibility assumptions in S-0003 and the original P0-T03 packet

## Context

The owner intentionally keeps `leon36000/ForgeLLM` public to use public GitHub CI, security analysis, agent skills and ecosystem integrations. Direct GitHub evidence on 2026-08-13 reports `visibility=public`, `main.protected=false`, and no repository rulesets. Existing state and task files incorrectly described the repository as private and therefore no longer matched reality.

The project also expects future restricted model weights, private prompts, machine inventories, raw traces, credentials and potentially confidential datasets. Public source collaboration and private operational assets must therefore be separated explicitly rather than relying on repository visibility as a security boundary.

## Decision

1. Keep the ForgeLLM source, governance and reproducibility repository public until a later ADR supersedes this decision.
2. Treat every Git-tracked byte, commit, issue, pull request, workflow log and artifact in this repository as public and permanently copyable.
3. Never store secrets, restricted model weights, private datasets, confidential prompts, raw customer data, private network details, stable hardware UUIDs or unredacted crash/trace payloads in this repository.
4. Introduce a separate private asset plane only when needed. Public records reference private assets through opaque identifiers, immutable revisions, hashes, licenses and redacted manifests; they do not contain the payload.
5. Public visibility does not grant an open-source license. Until a licensing ADR is accepted, the repository remains publicly visible but unlicensed for reuse except where individual third-party materials state otherwise.
6. Git remains canonical. Neon Postgres, vector databases, search indexes and other RAG systems may be derived indexes only. They cannot override Git history, ADRs, state or experiment evidence.
7. NVIDIA, AMD, Temporal, SonarQube, Consensus, Neon and other external tools are activated only by bounded tasks, least-privilege permissions and explicit data-classification review. Tool output is evidence input, not authority.
8. No self-hosted CPU or GPU runner may be registered while `main` is unprotected. A future runner requires a protected default branch or ruleset, trusted-only workflow triggers, environment approval, ephemeral isolation, no fork execution, no secrets on untrusted events and an external human security review before privileged activation.
9. Hosted CI, CodeQL and Dependency Review are preferred while the repository is public. A check becomes required only after it has executed successfully with a stable name on `main`.
10. Direct pushes to `main` remain prohibited by project policy even when GitHub has not yet technically enforced that rule.

## Alternatives considered

### Return to a private repository

Reduces accidental exposure but conflicts with the owner's current ecosystem-access decision and can limit free public-repository features.

### Split public source and private operations immediately

Provides a strong boundary but introduces synchronization and governance cost before private assets or runners exist.

### Public source now, private asset plane when first required

Selected. It preserves public tooling while making the future boundary explicit and testable.

## Consequences

### Positive

- Public CI, skills, research discussion and security tooling remain available.
- The disclosure boundary becomes explicit rather than accidental.
- A future private data plane can evolve without changing the public runtime architecture.
- RAG and external tools remain useful without becoming hidden project memory.

### Negative

- Any committed secret or restricted artifact must be considered disclosed and rotated or removed from all future use.
- Public issues and workflow logs require redaction discipline.
- Branch protection becomes a critical control before any privileged hardware connection.
- Public visibility without a license may confuse potential contributors unless notices remain prominent.

## Safety and correctness invariants

- `main` protection is a gate for self-hosted runners, not an optional hardening item.
- No external tool receives data classified above its approved level.
- Public manifests contain hashes and metadata, never private payloads.
- Derived RAG indexes record source commit and path and are disposable/rebuildable.
- Security findings with exploit value are handled through a private reporting path.
- A successful scanner workflow is not equivalent to zero findings unless findings were directly inspected.

## Evidence required for review

- direct repository visibility and default-branch evidence;
- direct branch/ruleset evidence;
- exact-head Phase 0, CodeQL and Dependency Review runs;
- secret and public-asset policy review;
- fresh-context review of the final diff;
- owner disposition.

## Reversal condition

Reconsider public visibility before any restricted model/data payload, private customer workload, privileged runner, confidential partner integration or distribution license requiring a different repository boundary is introduced.
