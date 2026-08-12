# ForgeLLM Licensing Decision Gate

## Current status

No project license has been selected. Until the owner accepts an ADR choosing a license, ForgeLLM should remain in a private repository and must not copy third-party source code into this tree.

## Why this is a gate

ForgeLLM will study and potentially interoperate with projects under multiple licenses. Architectural ideas and independently implemented interfaces may be usable, but copied code, generated bindings, model assets, test vectors and benchmark datasets can carry separate obligations.

## Required decision inputs

Before public release, record in a licensing ADR:

1. intended use: private research, open source, commercial distribution, hosted service or a combination;
2. preferred project license and contributor policy;
3. patent posture;
4. treatment of GPL/AGPL/LGPL dependencies and subprocess boundaries;
5. model, tokenizer and dataset licensing policy;
6. acceptable inbound licenses for copied or adapted code;
7. attribution and NOTICE generation process;
8. whether a contributor license agreement or developer certificate of origin is required.

## Dependency intake gate

Every new dependency or code import must include:

- exact package/repository and immutable revision;
- declared SPDX license and independent verification source;
- transitive-license report when applicable;
- intended linkage or process boundary;
- copied/adapted file inventory;
- security and maintenance assessment;
- reviewer approval.

Unknown, custom, source-available or conflicting terms block integration until reviewed.

## Safe Phase 0 policy

Phase 0 may store citations, metadata, original analysis and clean-room interface specifications. It must not vendor external implementation code. Repository metadata that names third-party projects does not imply endorsement or license compatibility.
