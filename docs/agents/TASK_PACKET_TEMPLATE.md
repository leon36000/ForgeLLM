# ForgeLLM Task Packet Template

Save each instantiated task under `tasks/<phase>/<task-id>.yaml` and link it to one issue.

```yaml
schema_version: "1.0"
task_id: "P1-T01"
title: "Capture immutable hardware and software inventory"
status: "ready"
owner_role: "lab-operator"
reviewer_role: "reproducibility-reviewer"
charter_goals:
  - "reproducible performance evidence"
non_goals:
  - "install or replace GPU drivers"
  - "benchmark an inference engine"
problem: >-
  Performance experiments cannot be compared until the first laboratory machine
  has an immutable, machine-readable inventory and topology record.
inputs:
  - "ForgeLLM Phase 0 repository"
  - "authorized laboratory machine"
outputs:
  - "artifacts/inventory/<host-fingerprint>.json"
  - "state S-0003 update"
files_allowed:
  - "artifacts/inventory/**"
  - "docs/state/CURRENT_STATE.md"
  - "docs/state/HANDOFF.md"
interfaces:
  consumes:
    - "forgellm-governance inventory CLI"
  produces:
    - "hardware inventory JSON schema version 1.0"
acceptance_criteria:
  - "inventory command exits zero"
  - "CPU, RAM, OS, kernel and storage data are present"
  - "available NVIDIA/AMD tools are captured without failing when absent"
  - "machine-specific secrets and user paths are redacted"
  - "artifact SHA-256 is recorded"
verification:
  commands:
    - "forgellm-governance inventory --output artifacts/inventory/first-host.json"
    - "python -m json.tool artifacts/inventory/first-host.json >/dev/null"
    - "sha256sum artifacts/inventory/first-host.json"
  expected:
    - "all commands exit zero"
risks:
  - "hardware identifiers may contain sensitive information"
rollback: "delete the uncommitted inventory artifact and restore state files"
state_updates:
  - "CURRENT_STATE"
  - "HANDOFF"
```
