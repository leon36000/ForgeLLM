# ForgeLLM Public Repository Policy

**Effective:** 2026-08-13  
**Authority:** ADR-0003  
**Repository:** `leon36000/ForgeLLM`

## Public-by-construction rule

Assume that every tracked file, commit, branch, issue, pull request, review, Actions log and uploaded artifact can be copied permanently. Deleting or rewriting later history is not a confidentiality control.

## Data classes

| Class | Examples | Allowed in this repository |
|---|---|---|
| Public source | original code, ADRs, sanitized tests, public citations | yes |
| Public evidence | redacted manifests, synthetic workloads, public benchmark data | yes |
| Restricted asset | licensed weights, private datasets, private prompts, partner artifacts | no |
| Operationally sensitive | hostnames, private IPs, topology labels, device UUIDs, raw traces | only redacted or one-way fingerprinted when justified |
| Secret | tokens, passwords, signing keys, cloud/model credentials | never |

## Private asset plane

When restricted assets become necessary, create an owner-approved private store or repository with:

- separate access control and audit history;
- immutable asset identifiers and hashes;
- retention and deletion rules;
- license and provenance records;
- no implicit synchronization into the public repository.

Public experiment records may reference an opaque asset ID, revision, hash and access procedure. They must not embed the asset.

## External tools and agent skills

Before enabling a plugin, app, MCP server, CI integration or RAG connector:

1. map the task and exact data it needs;
2. inspect permissions and retention where available;
3. grant least privilege;
4. prohibit restricted/secret data unless an owner-approved private-data task explicitly permits it;
5. store outputs with source, timestamp, version and limitations;
6. revoke or reduce access after the task when practical.

Current applicability:

- **GitHub / CodeQL / Codex Engineering Guardrails:** relevant to P0-T03 and active governance work.
- **SonarQube:** useful as an additional code-quality/security verifier once a callable server/project is configured; not a substitute for CodeQL or tests.
- **Fallow:** intended for TypeScript/JavaScript; not a primary fit for the current Python/Markdown scaffold.
- **Consensus:** useful for bounded scientific reviews in the research backlog.
- **Neon Postgres:** candidate for a derived RAG/index; never canonical and requires an ADR/task before storing project text.
- **Temporal:** candidate for durable agent-workflow orchestration after task semantics and failure recovery are designed.
- **NVIDIA/AMD skills:** relevant during hardware inventory, backend and profiling phases; not used to bypass P0 gates.

## Public contribution and licensing notice

Public visibility does not imply permission to copy, redistribute or create derivative works. Until a licensing ADR is accepted, external code contributions require an owner-linked task and explicit inbound-license handling.

## Incident response

If sensitive information is committed:

1. treat it as disclosed;
2. rotate/revoke affected credentials immediately;
3. preserve incident evidence privately;
4. remove the material from the current tree and assess history cleanup separately;
5. document the incident without repeating the secret;
6. review plugin, workflow and log exposure.
