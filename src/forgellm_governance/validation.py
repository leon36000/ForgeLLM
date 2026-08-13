"""Machine-enforced ForgeLLM project, research, task and benchmark rules."""

from __future__ import annotations

import json
import math
import re
import statistics
import tomllib
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker


_ID_PATTERNS = {
    "claim": re.compile(r"^CLM-[0-9]{3,}$"),
    "source": re.compile(r"^(REP|PAP|OFF)-[A-Z0-9][A-Z0-9-]*$"),
    "adr": re.compile(r"^ADR-[0-9]{4}$"),
}
_SECRET_PATTERNS = {
    "GitHub classic token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    "GitHub fine-grained token": re.compile(r"\bgithub_pat_[A-Za-z0-9_]{40,}\b"),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "OpenAI-style project key": re.compile(r"\bsk-proj-[A-Za-z0-9_-]{20,}\b"),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}
_TEXT_SUFFIXES = {".md", ".txt", ".yaml", ".yml", ".json", ".toml", ".py", ".sh"}


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """One actionable validation issue."""

    path: str
    message: str
    severity: str = "error"

    def render(self) -> str:
        return f"{self.severity.upper()}: {self.path}: {self.message}"


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"file does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}") from exc


def _load_yaml(path: Path) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"file does not exist: {path}") from exc
    except yaml.YAMLError as exc:
        raise ValueError(f"invalid YAML: {exc}") from exc


def _json_pointer(parts: Iterable[Any]) -> str:
    escaped = [str(part).replace("~", "~0").replace("/", "~1") for part in parts]
    return "/" + "/".join(escaped) if escaped else "/"


def _validate_schema(instance: Any, schema_path: Path, instance_path: Path) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    try:
        schema = _load_json(schema_path)
    except ValueError as exc:
        return [ValidationIssue(str(schema_path), str(exc))]

    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    for error in sorted(validator.iter_errors(instance), key=lambda item: list(item.absolute_path)):
        pointer = _json_pointer(error.absolute_path)
        issues.append(ValidationIssue(f"{instance_path}{pointer}", error.message))
    return issues


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _close(actual: float, expected: float) -> bool:
    return math.isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-12)


def _expected_summary(samples: Sequence[float]) -> dict[str, float | int]:
    ordered = sorted(samples)
    p95_index = max(0, math.ceil(0.95 * len(ordered)) - 1)
    return {
        "count": len(samples),
        "mean": statistics.fmean(samples),
        "median": statistics.median(samples),
        "stdev": statistics.stdev(samples),
        "min": min(samples),
        "max": max(samples),
        "p95": ordered[p95_index],
    }


def validate_benchmark_data(data: Mapping[str, Any], *, source_path: Path, root: Path) -> list[ValidationIssue]:
    """Validate benchmark schema plus cross-field reproducibility invariants."""

    issues = _validate_schema(data, root / "schemas/benchmark-result.schema.json", source_path)
    if issues:
        return issues

    status = data["status"]
    correctness = data["correctness"]["status"]
    source = data["source"]
    reviewer_status = data["people"]["reviewer"]["status"]

    if status == "valid":
        if correctness != "pass":
            issues.append(ValidationIssue(str(source_path), "status 'valid' requires correctness.status 'pass'"))
        if not source["baseline_clean"] or not source["candidate_clean"]:
            issues.append(ValidationIssue(str(source_path), "status 'valid' requires clean baseline and candidate worktrees"))
        if reviewer_status != "approved":
            issues.append(ValidationIssue(str(source_path), "status 'valid' requires an approved independent review"))

    try:
        if _parse_datetime(data["timestamps"]["ended_at"]) <= _parse_datetime(data["timestamps"]["started_at"]):
            issues.append(ValidationIssue(str(source_path), "ended_at must be later than started_at"))
    except (TypeError, ValueError) as exc:
        issues.append(ValidationIssue(str(source_path), f"could not compare timestamps: {exc}"))

    repetitions = data["workload"]["repetitions"]
    for index, measurement in enumerate(data["measurements"]):
        base = measurement["baseline_samples"]
        candidate = measurement["candidate_samples"]
        pointer = f"{source_path}/measurements/{index}"
        if len(base) != repetitions or len(candidate) != repetitions:
            issues.append(
                ValidationIssue(
                    pointer,
                    f"sample counts must equal workload.repetitions ({repetitions}); got {len(base)} and {len(candidate)}",
                )
            )
        for name, samples in (("baseline_summary", base), ("candidate_summary", candidate)):
            expected = _expected_summary(samples)
            supplied = measurement[name]
            for metric, expected_value in expected.items():
                actual = supplied[metric]
                if isinstance(expected_value, int):
                    matches = actual == expected_value
                else:
                    matches = _close(float(actual), float(expected_value))
                if not matches:
                    issues.append(
                        ValidationIssue(
                            f"{pointer}/{name}/{metric}",
                            f"summary does not match raw samples: expected {expected_value!r}, got {actual!r}",
                        )
                    )

    artifact_paths = [item["path"] for item in data["artifacts"]]
    if len(artifact_paths) != len(set(artifact_paths)):
        issues.append(ValidationIssue(str(source_path), "artifact paths must be unique"))

    if data["source"]["baseline_commit"] == data["source"]["candidate_commit"]:
        issues.append(ValidationIssue(str(source_path), "baseline and candidate commits must differ for a comparative result"))

    return issues


def validate_benchmark_file(path: Path | str, *, root: Path | str | None = None) -> list[ValidationIssue]:
    path = Path(path).resolve()
    project_root = Path(root).resolve() if root is not None else path.parents[2]
    try:
        data = _load_json(path)
    except ValueError as exc:
        return [ValidationIssue(str(path), str(exc))]
    if not isinstance(data, Mapping):
        return [ValidationIssue(str(path), "benchmark root must be an object")]
    return validate_benchmark_data(data, source_path=path, root=project_root)


def validate_task_packet_file(path: Path | str, *, root: Path | str | None = None) -> list[ValidationIssue]:
    path = Path(path).resolve()
    project_root = Path(root).resolve() if root is not None else path.parents[2]
    try:
        data = _load_yaml(path)
    except ValueError as exc:
        return [ValidationIssue(str(path), str(exc))]
    if not isinstance(data, Mapping):
        return [ValidationIssue(str(path), "task packet root must be an object")]
    issues = _validate_schema(data, project_root / "schemas/task-packet.schema.json", path)
    if issues:
        return issues
    task_phase = data["task_id"].split("-", maxsplit=1)[0]
    if task_phase != data["phase"]:
        issues.append(ValidationIssue(str(path), f"task_id phase {task_phase!r} does not match phase {data['phase']!r}"))
    if data["task_id"] in data["dependencies"]:
        issues.append(ValidationIssue(str(path), "a task cannot depend on itself"))
    return issues


def _require_mapping(path: Path, data: Any, key: str) -> tuple[list[Any], list[ValidationIssue]]:
    if not isinstance(data, Mapping):
        return [], [ValidationIssue(str(path), "document root must be an object")]
    value = data.get(key)
    if not isinstance(value, list):
        return [], [ValidationIssue(str(path), f"required key {key!r} must be an array")]
    return value, []


def validate_research_catalogs(root: Path | str) -> list[ValidationIssue]:
    root = Path(root).resolve()
    paths = {
        "repos": root / "research/repos.yaml",
        "papers": root / "research/papers.yaml",
        "official": root / "research/official_sources.yaml",
        "claims": root / "research/claims.yaml",
        "queries": root / "research/queries.yaml",
        "review_queue": root / "research/review_queue.yaml",
    }
    loaded: dict[str, Any] = {}
    issues: list[ValidationIssue] = []
    for name, path in paths.items():
        try:
            loaded[name] = _load_yaml(path)
        except ValueError as exc:
            issues.append(ValidationIssue(str(path), str(exc)))
    if issues:
        return issues

    repos, repo_issues = _require_mapping(paths["repos"], loaded["repos"], "repositories")
    papers, paper_issues = _require_mapping(paths["papers"], loaded["papers"], "papers")
    official, official_issues = _require_mapping(paths["official"], loaded["official"], "sources")
    claims, claim_issues = _require_mapping(paths["claims"], loaded["claims"], "claims")
    queries, query_issues = _require_mapping(paths["queries"], loaded["queries"], "queries")
    repository_reviews, repository_review_issues = _require_mapping(
        paths["review_queue"], loaded["review_queue"], "repository_reviews"
    )
    paper_syntheses, paper_synthesis_issues = _require_mapping(
        paths["review_queue"], loaded["review_queue"], "paper_syntheses"
    )
    issues.extend(
        repo_issues
        + paper_issues
        + official_issues
        + claim_issues
        + query_issues
        + repository_review_issues
        + paper_synthesis_issues
    )
    if issues:
        return issues

    def collect_ids(records: list[Any], path: Path, prefix: str) -> set[str]:
        ids: set[str] = set()
        for index, record in enumerate(records):
            pointer = f"{path}/{index}"
            if not isinstance(record, Mapping):
                issues.append(ValidationIssue(pointer, "record must be an object"))
                continue
            record_id = record.get("id")
            if not isinstance(record_id, str) or not record_id.startswith(prefix):
                issues.append(ValidationIssue(pointer, f"id must start with {prefix!r}"))
                continue
            if record_id in ids:
                issues.append(ValidationIssue(pointer, f"duplicate id {record_id}"))
            ids.add(record_id)
        return ids

    repo_ids = collect_ids(repos, paths["repos"], "REP-")
    paper_ids = collect_ids(papers, paths["papers"], "PAP-")
    official_ids = collect_ids(official, paths["official"], "OFF-")
    claim_ids = collect_ids(claims, paths["claims"], "CLM-4T4 