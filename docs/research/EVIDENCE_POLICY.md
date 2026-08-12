# ForgeLLM Evidence Policy

## 1. Objective

Ensure that architecture, compatibility and performance decisions can be traced to primary sources or reproducible ForgeLLM measurements.

## 2. Claim classes

Every nontrivial statement recorded in project artifacts must be classified:

- `fact`: directly supported by a primary source;
- `inference`: reasoned from named evidence;
- `hypothesis`: falsifiable statement awaiting experiment;
- `decision`: chosen action with alternatives and consequences;
- `measurement`: result produced by a declared experiment.

## 3. Evidence levels

| Level | Evidence | Typical use |
|---|---|---|
| E0 | unsupported statement | discovery only; never a decision basis |
| E1 | official documentation/specification or official repository | feature, interface, compatibility |
| E2 | official preprint with method and artifacts | research hypothesis and reproduction plan |
| E3 | peer-reviewed paper and accessible artifacts | stronger design evidence |
| E4 | independent reproduction on comparable conditions | local design validation |
| E5 | multiple independent reproductions across target profiles | broad project claim |

Popularity, stars, social posts and vendor marketing are not performance evidence. They can be recorded as dated ecosystem signals.

## 4. Source record requirements

Each source record includes:

- stable identifier;
- canonical URL;
- title and authors/organization;
- publication or release date;
- access date;
- source type and evidence level;
- immutable revision when possible;
- claims supported;
- limitations, conflicts and hardware scope;
- license/artifact availability;
- reading and reproduction status.

## 5. Claim lifecycle

1. `proposed`: claim entered but not evaluated.
2. `externally_supported`: primary source supports it within stated scope.
3. `reproduction_planned`: task and protocol exist.
4. `partially_reproduced`: subset of scope reproduced.
5. `reproduced`: declared scope reproduced with raw artifacts.
6. `refuted`: valid evidence contradicts the tested formulation.
7. `inconclusive`: experiment cannot decide.
8. `superseded`: more precise claim replaces it.

No external result skips directly to `reproduced`.

## 6. Performance evidence

A performance record must satisfy `docs/benchmarks/BENCHMARK_STANDARD.md` and validate against `schemas/benchmark-result.schema.json`. It must identify baseline and candidate, correctness status, raw sample artifacts and environment fingerprint.

Claims such as “up to N×” are recorded as author-reported, with the exact workload and baseline. ForgeLLM summaries do not repeat a maximum number without its domain.

## 7. Negative and null results

Negative results are first-class evidence. Store them when the experiment is valid. Record why the approach failed, where it might still apply and the cost avoided by not repeating it.

## 8. Conflicts

When reliable sources disagree:

- preserve both records;
- compare versions, hardware, workloads and assumptions;
- narrow the claim rather than choosing by popularity;
- design a discriminating experiment when material.

## 9. Freshness

Current facts such as versions, supported hardware, APIs, licenses, activity and security guidance require a dated refresh before use. Stable mathematical or historical facts do not require routine refresh.
