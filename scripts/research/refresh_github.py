#!/usr/bin/env python3
"""Snapshot public GitHub repository metadata without modifying research decisions."""
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import yaml


def run_gh(slug: str) -> dict:
    fields = "nameWithOwner,url,description,defaultBranchRef,licenseInfo,stargazerCount,forkCount,updatedAt,isArchived"
    completed = subprocess.run(
        ["gh", "repo", "view", slug, "--json", fields],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if completed.returncode != 0:
        return {"slug": slug, "status": "error", "stderr": completed.stderr.strip()}
    data = json.loads(completed.stdout)
    branch = data.get("defaultBranchRef") or {}
    branch_name = branch.get("name")
    commit = None
    if branch_name:
        commit_result = subprocess.run(
            ["gh", "api", f"repos/{slug}/commits/{branch_name}", "--jq", ".sha"],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if commit_result.returncode == 0:
            commit = commit_result.stdout.strip()
    return {"slug": slug, "status": "ok", "metadata": data, "default_branch_commit": commit}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, default=Path("artifacts/research/github-snapshot.json"))
    parser.add_argument("--limit", type=int, default=0, help="0 means all catalog entries")
    args = parser.parse_args()
    catalog = yaml.safe_load((args.root / "research/repos.yaml").read_text(encoding="utf-8"))
    repos = catalog["repositories"][: args.limit or None]
    result = {
        "schema_version": "1.0",
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "policy": "Snapshot only; human review is required before catalog or claim changes.",
        "repositories": [run_gh(repo["slug"]) for repo in repos],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    errors = sum(item["status"] != "ok" for item in result["repositories"])
    print(f"wrote {args.output}; errors={errors}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
