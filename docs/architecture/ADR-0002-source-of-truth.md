# ADR-0002: Versioned repository state is the durable project memory

- **Status:** accepted
- **Date:** 2026-08-12
- **Owners:** ForgeLLM project owner; governance reviewer role
- **Related claims:** CLM-010

## Context

ForgeLLM will be developed across ChatGPT mobile, Codex, Claude Code and human tools. Conversation histories and automatic memories are not guaranteed to be complete, auditable, conflict-free or visible to every agent.

## Decision

Use Git-tracked charter, ADRs, state, decisions, risks, open questions, research catalogs, claim records, task packets, experiment manifests and handoff files as the canonical memory. ChatGPT receives a compact five-file projection. Every significant session ends by generating state updates suitable for committing.

## Alternatives considered

- Rely only on one long chat: fragile, difficult to audit and hard for coding agents to consume.
- Rely only on issue trackers: insufficient for architecture and machine-readable experiment records.
- Use an external vector database as canonical memory: useful later for retrieval, but it adds synchronization and provenance problems.

## Consequences

The repository gains documentation maintenance cost. In return, state is reviewable, diffable, testable and portable across agents. Automated validators must detect missing or stale continuity fields.

## Safety and correctness invariants

- A conversation cannot silently override an accepted ADR.
- The current state has an identifier, timestamp and next authorized task.
- Claims and experiments retain provenance.
- Mobile context is a projection, not an independent fork.

## Reversal condition

A future knowledge system may become canonical only if it offers versioned history, review, offline export, deterministic references and bidirectional synchronization without losing provenance.
