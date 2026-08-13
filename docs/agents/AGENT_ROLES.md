# ForgeLLM Agent Roles

## Architect

Maintains charter, boundaries, ADR quality and phase sequencing. Does not waive evidence gates to accelerate implementation.

## Researcher

Builds primary-source records, adversarial literature reviews and reproduction plans. Does not convert author-reported results into ForgeLLM facts.

## Implementer

Completes one task packet in one worktree. Writes tests, minimal implementation and a factual completion report.

## Correctness reviewer

Owns semantics, numerical budgets, differential/property tests and failure cases. Independent from the implementer for critical work.

## Performance reviewer

Validates baseline parity, methodology, statistics, traces and result scope. Can reject a faster result that lacks correctness or reproducibility.

## Security reviewer

Reviews unsafe/FFI boundaries, supply chain, secrets, runners, permissions and release provenance.

## Lab operator

Controls hardware changes, drivers, firmware, clocks, thermal conditions and machine access. Agents do not assume this authority.

## Release steward

Assembles signed source/artifacts, SBOM, provenance, model/data notices, changelog and reproduction instructions.

One agent context may fill multiple low-risk roles, but implementation and final verification remain separate for architecture, unsafe code, distributed code, security and performance claims.
