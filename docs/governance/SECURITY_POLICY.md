# ForgeLLM Security Policy

## Repository boundary

ForgeLLM's source repository is intentionally public under ADR-0003. Treat every tracked byte, issue, pull request, workflow log and artifact as disclosed. Public visibility is not a security boundary and is not permission to store private operational assets.

## Reporting

Report suspected vulnerabilities privately through GitHub private vulnerability reporting when available. Do not open a public issue containing exploit details, credentials, private model links, machine identifiers or confidential workloads.

## Protected assets

Never commit or publish:

- GitHub/GitLab, cloud, model-registry and package tokens;
- private datasets, prompts and model artifacts;
- GPU runner credentials, private network addresses and full hardware UUIDs;
- signing keys and provenance identities;
- crash dumps or traces that may contain prompts, weights or customer data.

Store secrets only in an approved encrypted secret store. Use short-lived identity federation instead of static credentials where supported. Restricted payloads belong in a separately approved private asset plane.

## Agent and external-tool rules

AI agents, plugins, MCP servers and RAG connectors must not:

- print, summarize, commit or upload secrets/restricted data;
- weaken branch protection, code review or CI checks;
- run destructive infrastructure commands without explicit authorization;
- execute untrusted pull-request code on privileged or self-hosted runners;
- install opaque binaries or pipe remote scripts into a shell without review;
- become the canonical memory of the project;
- upload code, model files or benchmark data to an unapproved external service.

Each integration receives the minimum permissions and data needed for one bounded task. Record tool/version, data scope, outputs and limitations.

## Supply-chain controls

- Pin CI actions and reusable workflows to full commit SHAs.
- Lock language dependencies and review lockfile changes.
- Enable secret scanning, push protection, Dependency Review and CodeQL when supported.
- Inspect findings directly; a green scanner job is not automatically a clean report.
- Generate an SBOM and artifact provenance for releases.
- Verify downloads by trusted signature or published checksum.
- Keep build, benchmark, signing and deployment permissions separate.

## Runner isolation

No self-hosted runner is currently authorized. A public repository runner requires all of the following before registration:

- protected `main` or an equivalent enforced ruleset;
- no fork or untrusted-event execution;
- no secrets on untrusted contexts;
- owner-approved workflow allow-list;
- environment approval;
- ephemeral or fully reset workers;
- minimal network egress and credentials;
- separate NVIDIA/AMD labels and machine scopes;
- external human security review before privileged activation.

## Vulnerability handling

1. preserve evidence without exposing sensitive data;
2. assign a private tracking identifier;
3. reproduce in an isolated environment;
4. assess impact and affected revisions;
5. implement a regression test before the fix when safe;
6. review, release and disclose according to an owner-approved timeline;
7. rotate exposed credentials immediately;
8. assume any secret committed publicly has been copied.
