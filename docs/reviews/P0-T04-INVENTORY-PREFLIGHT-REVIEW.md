# P0-T04 Inventory Publication Preflight Review

- **Task:** P0-T04 preflight
- **Pull request:** #14
- **Date:** 2026-08-13
- **Reviewed implementation head:** `4ef5f3552ee5f7a301b7da1b8270b7e5130ae555`
- **Review role:** fresh verification context
- **Verdict:** `ACCEPT`, subject to final exact-head gates after this report is committed

## Scope

This review covers only the publication boundary used by the first hardware/software inventory. No owner machine has been queried and no inventory result is included in this pull request.

Changed implementation surface:

- `scripts/hardware_inventory.py`;
- `tests/test_hardware.py`.

## TDD evidence

### Initial RED

Run `31750190859`, job `94613963129` failed as expected with two regressions:

1. network link-address fields survived in the data intended for publication;
2. storage collection exposed mount-related fields to the publication pipeline.

The run reported `2 failed, 17 passed`.

### First GREEN

After introducing an explicit publication sanitizer, run `31750481703`, job `94614860905` succeeded with `20 passed`.

The sanitizer:

- allowlists the network fields that may be published;
- recursively removes storage mount fields;
- fails closed for network/storage data that is not valid structured JSON;
- clears structured-probe stderr from the publication copy.

### Static-analysis finding and correction

SonarQube Cloud then rejected the first implementation because the CLI output path could escape the repository artifact area. The finding was accepted as valid.

A path-confinement regression was added and the writer now resolves the candidate path canonically before collection or writing. The path is accepted only when it is a file below the repository `artifacts/` directory. This also rejects existing parent/file symlinks that resolve outside that directory.

### Final GREEN on reviewed implementation

Run `31750729623`, job `94615638799` succeeded with:

- Ruff: pass;
- project/research/benchmark/task validators: pass;
- mobile-context validation: pass;
- Python tests: **21 passed**;
- bootstrap dry-run: pass.

CodeQL completed successfully and reported no new alerts in code changed by PR #14.

SonarQube Cloud Quality Gate passed on the reviewed head with:

- 0 new issues;
- 0 accepted issues;
- 0 security hotspots.

## Security and privacy assessment

### Publication boundary

`sanitize_inventory()` deep-copies the collected result before transformation. Network publication uses an allowlist. Storage publication recursively removes mount-related keys. Unparsed network/storage outputs are replaced with `null` data rather than copied as raw text.

### Output confinement

`write_sanitized_inventory()` validates and canonicalizes the output path before running collection. Output outside `artifacts/` is rejected.

### Residual limitation

The lower-level collector still requests some data that the publication boundary later removes. This is a data-minimization improvement opportunity, not a known public-output leak in the reviewed path. The connector blocked a direct change to that lower-level collector, so this review does not claim collection-time minimization is complete.

### Evidence boundary

This review does not prove anything about the owner's actual hardware, drivers, accelerators, topology or performance. It verifies only that the current publication path is safer before P0-T04 inventory execution.

## Verdict

`ACCEPT` after the final head containing this review report passes:

1. `Validate and test`;
2. CodeQL;
3. SonarQube Cloud Quality Gate.

No hardware command or benchmark should be executed until this preflight is merged and the owner designates the P0-T04 host/execution mode.
