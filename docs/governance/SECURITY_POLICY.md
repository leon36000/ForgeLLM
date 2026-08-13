# ForgeLLM Security Policy

## Reporting

Before a public security contact is established, report suspected vulnerabilities privately to the repository owner. Do not open a public issue containing exploit details, credentials, private model links or machine identifiers.

## Protected assets

Treat the following as sensitive:

- GitHub/GitLab, cloud, model-registry and package tokens;
- private datasets, prompts and model artifacts;
- GPU runner credentials, network addresses and full hardware UUIDs;
- signing keys and provenance identities;
- crash dumps or traces that may contain prompts or weights.

Store secrets only in the selected platform's encrypted secret store or an approved external secret manager. Use short-lived identity federation instead of static credentials where supported.

## Agent rules

AI agents must not:

- print, summarize or commit secrets;
- weaken branch protection, code review or CI checks;
- run destructive infrastructure commands without explicit authorization;
- execute untrusted pull-request code on privileged or GPU runners;
- install opaque binaries or pipe remote scripts into a shell without review;
- upload code, model files or benchmark data to an unapproved external service.

## Supply-chain controls

- Pin CI actions and reusable workflows to full commit SHAs.
- Lock language dependencies and review lockfile changes.
- Enable secret scanning, push protection, dependency review and CodeQL when supported.
- Generate an SBOM and artifact provenance for releases.
- Verify downloads by trusted signature or published checksum.
- Keep build and deployment permissions separate.

## Runner isolation

Self-hosted GPU runners are permitted only for private, trusted workloads. Prefer ephemeral runners, minimum privileges, network egress controls, clean workspaces and separate labels for NVIDIA and AMD machines. Fork pull requests must never receive secrets or execute on those runners.

## Vulnerability handling

1. preserve evidence without exposing sensitive data;
2. assign a private tracking identifier;
3. reproduce in an isolated environment;
4. assess impact and affected revisions;
5. implement a regression test before the fix when safe;
6. review, release and disclose according to an owner-approved timeline;
7. rotate exposed credentials immediately.
