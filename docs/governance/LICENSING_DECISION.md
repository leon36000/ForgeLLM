# ForgeLLM Licensing Decision Gate

## Current status

No project license has been selected. ForgeLLM is publicly visible under ADR-0003, but public visibility is not a license. Unless a file or third-party component states otherwise, no permission to copy, redistribute, modify or create derivative works is granted.

No third-party implementation code may be copied into this tree before provenance and license compatibility are reviewed. External code contributions require an owner-linked task and explicit inbound-license handling until the contributor policy is accepted.

## Why this is a gate

ForgeLLM will study and potentially interoperate with projects under multiple licenses. Architectural ideas and independently implemented interfaces may be usable, but copied code, generated bindings, model assets, test vectors and benchmark datasets can carry separate obligations.

## Required decision inputs

Before an open-source or binary release, record in a licensing ADR:

1. intended use: research, open source, commercial distribution, hosted service or a combination;
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

Phase 0 may publish citations, metadata, original analysis, schemas and clean-room interface specifications. It must not vendor external implementation code or restricted assets. Repository metadata that names third-party projects does not imply endorsement or license compatibility.
