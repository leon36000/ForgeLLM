# ForgeLLM Manifest and Integrity Policy

## Live repository integrity

The canonical identity of a live ForgeLLM revision is its Git commit SHA and Git tree SHA. Git already hashes every object and makes later modifications visible in history.

A repository-wide `MANIFEST.sha256` generated for a delivery archive is a snapshot of that archive. It is not expected to continue validating after normal commits change tracked files. Treating a delivery manifest as a continuously current repository manifest would create false failures or misleading assurance.

## Delivery manifests

A release or exported context package must contain a SHA-256 manifest generated from the exact packaged bytes. The verification report records:

- source commit and tree;
- packaging command;
- file list;
- manifest SHA-256;
- extraction and verification result.

The root `MANIFEST.sha256` in the Phase 0 bootstrap remains historical evidence for the original package described by `artifacts/verification-report.json`. It must not be cited as proof for later commits.

## Mobile context integrity

The live five-file mobile projection is checked separately by `scripts/hash_mobile_context.py`.

The script:

- requires exactly the five canonical Markdown files;
- rejects missing or additional Markdown files in `chatgpt/mobile-core/`;
- prints deterministic SHA-256 records suitable for a session handoff or package manifest.

CI runs this check on every pull request. A mobile ZIP intended for upload stores the resulting hashes beside the archive.

## Benchmark and research artifacts

Benchmark outputs, hardware inventories, models, datasets and profiler traces use their own manifests attached to the experiment record. They are never inferred from the repository delivery manifest.
