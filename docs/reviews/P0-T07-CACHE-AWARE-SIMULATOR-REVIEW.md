# P0-T07 Cache-Aware Placement Simulator — Verification Review

- **Task:** P0-T07
- **Authorization:** owner-authorized `subagent-driven`
- **Pull request:** #20
- **Base:** `d5cd25bd9d6fc3f9cded27781c2051939dcdde85`
- **Final reviewed head:** `99c1c1488f622a6d4290e21a17ff313a1c3568c6`
- **Merge commit:** `b0f3f241537b50de0dd3c0cb7bc2e6bf274a7034`
- **Review date:** 2026-08-14
- **Verdict:** `ACCEPT`
- **Evidence boundary:** `synthetic_only`

## Scope reviewed

The review inspected the complete task packet and implementation surfaces for:

- schema strictness;
- immutable topology and component models;
- integer unit safety;
- legality and fallback invariants;
- deterministic selection;
- input/output path confinement;
- atomic output;
- canonical synthetic examples;
- adversarial tests;
- hosted CI and CodeQL evidence;
- preservation of P0-T04/P0-T05 gates.

No hardware, model, runtime, ABI or kernel work was in scope.

## Findings resolved before acceptance

### MAJOR — missing canonical example inputs

The Make validation referenced example files that were absent from the branch. The product-neutral topology and component examples were added and entered the hosted gate.

### MAJOR — invalid JSON escaping in result schema

The semantic-version regex used an invalid JSON escape. The pattern was corrected and validated as Draft 2020-12 JSON Schema.

### MAJOR — duplicate JSON keys accepted

Standard JSON parsing would silently keep the last duplicate key. `load_json_mapping` now rejects duplicate object keys deterministically.

### MAJOR — symlinked artifact root

The output resolver rejected output and parent escapes but did not reject an `artifacts/` root that was itself a symlink. This now fails closed.

### MAJOR — canonical scenario not part of hosted CI

`make ci` now executes `make simulate-cache-draft`, and the target logs the topology, component and result SHA-256 values.

### MINOR — determinism wording too broad

The documentation previously implied a byte-identical complete result after reordering input arrays. The selected plan and ranking are invariant, but complete results correctly retain different input hashes when source bytes change.

## Exact-head pull-request verification

On `99c1c1488f622a6d4290e21a17ff313a1c3568c6`:

- Phase 0 run `31784275654`, job `94716606110`: `success`;
- Ruff: pass;
- project, research, benchmark and task validators: pass;
- topology and component example validators: pass;
- complete suite: **102 passed**;
- canonical synthetic simulation: pass;
- bootstrap dry-run: pass;
- CodeQL run `31784275655`, job `94716597658`: `success`;
- Dependency Review `31784275656`: skipped by policy, not counted as executed evidence.

Synthetic hashes:

```text
6738d9596a2a9b9224a68e071a94463cdcbe7cff10a7cd30c4de29cd3381aa2f  topology
3aa6dcb2504aebee7c3db236abdd59867efe25296420bdc7e9ba1883061f4cb5  component profile
e5eb661bb48eca62b778714670000f963922ca459cb8590b3717150993a921ae  result
```

## Post-merge verification

On `main` commit `b0f3f241537b50de0dd3c0cb7bc2e6bf274a7034`:

- Phase 0 run `31784610893`, job `94717633943`: `success`;
- CodeQL run `31784610881`, job `94717633957`: `success`.

CodeQL alert count and severity are not asserted by these workflow conclusions.

## Acceptance-criteria assessment

- strict public schemas: satisfied;
- malformed/duplicate/unresolved/path-escape rejection: satisfied;
- immutable deterministic models: satisfied;
- integer byte/rate/nanosecond accounting: satisfied;
- deterministic legal candidates and stable rejection codes: satisfied;
- legal generic fallback retained: satisfied;
- deterministic selected plan and tie-breaking: satisfied;
- atomic artifact-confined output: satisfied;
- synthetic-only canonical example: satisfied;
- adversarial coverage: satisfied;
- exact-head `make ci`: satisfied;
- fresh-context structured review: satisfied.

## Residual limitations

The simulator deliberately does not model queueing, interference, energy, cache misses, overlap, speculative acceptance-rate feedback or multi-hop routing. Its outputs cannot support a real performance claim.

## Verdict

`ACCEPT` and close P0-T07. Preserve P0-T04/P0-T05 as hardware and workload gates. CA-03 may use the simulator's immutable synthetic infrastructure but must define exact speculative semantics in a separate task.
