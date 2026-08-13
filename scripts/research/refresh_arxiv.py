#!/usr/bin/env python3
"""Fetch an arXiv discovery snapshot; never promotes claims automatically."""
from __future__ import annotations

import argparse
import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path

import yaml

ATOM = {"atom": "http://www.w3.org/2005/Atom"}


def fetch(query: str, max_results: int) -> list[dict]:
    params = urllib.parse.urlencode({"search_query": f"all:{query}", "start": 0, "max_results": max_results, "sortBy": "submittedDate", "sortOrder": "descending"})
    request = urllib.request.Request(
        f"https://export.arxiv.org/api/query?{params}",
        headers={"User-Agent": "ForgeLLM-Research/0.1 (metadata discovery; contact repository owner)"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        root = ET.fromstring(response.read())
    records = []
    for entry in root.findall("atom:entry", ATOM):
        authors = [node.findtext("atom:name", default="", namespaces=ATOM) for node in entry.findall("atom:author", ATOM)]
        records.append({
            "id": entry.findtext("atom:id", default="", namespaces=ATOM),
            "title": " ".join(entry.findtext("atom:title", default="", namespaces=ATOM).split()),
            "published": entry.findtext("atom:published", default="", namespaces=ATOM),
            "updated": entry.findtext("atom:updated", default="", namespaces=ATOM),
            "authors": authors,
            "summary": " ".join(entry.findtext("atom:summary", default="", namespaces=ATOM).split()),
        })
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--query-id", required=True)
    parser.add_argument("--max-results", type=int, default=20)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    catalog = yaml.safe_load((args.root / "research/queries.yaml").read_text(encoding="utf-8"))
    record = next((item for item in catalog["queries"] if item["id"] == args.query_id), None)
    if record is None:
        raise SystemExit(f"unknown query id: {args.query_id}")
    output = args.output or Path(f"artifacts/research/arxiv-{args.query_id.lower()}.json")
    payload = {
        "schema_version": "1.0",
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "query_id": args.query_id,
        "query": record["arxiv"],
        "policy": "Discovery candidates only; human source review and claim linkage are mandatory.",
        "records": fetch(record["arxiv"], args.max_results),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
