# ForgeLLM Source Catalog Guide

The machine-readable catalogs are:

- `research/repos.yaml`
- `research/papers.yaml`
- `research/official_sources.yaml`
- `research/claims.yaml`
- `research/queries.yaml`

## Canonical URL families

- arXiv abstracts: `https://arxiv.org/abs/<id>`
- GitHub repositories: `https://github.com/<owner>/<repo>`
- GitLab projects: canonical project URL from the hosting instance
- conference proceedings: official USENIX, ACM, IEEE, MLSys, NeurIPS or OpenReview page
- vendor documentation: official NVIDIA, AMD, Intel or platform documentation

## Review rule

A URL in the catalog proves only that a source exists. An agent must inspect the source and connect a specific supported claim. Repository metrics are snapshots and must include `observed_at`.
