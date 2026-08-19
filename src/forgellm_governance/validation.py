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

_SONAR_CHECKOUT_ACTION = "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1"
_SONAR_SCANNER_ACTION = "SonarSource/sonarqube-scan-action@22918119ff8e1ca75a623e15c8296b6ea4fbe28f"
_SONAR_TOKEN_REFERENCE = "${{ secrets.SONAR_TOKEN }}"
_SONAR_TRUSTED_ARGUMENTS = (
    "sonar.host.url=https://sonarcloud.io",
    "sonar.organization=leon36000",
    "sonar.projectKey=leon36000_ForgeLLM",
    "sonar.sca.enabled=false",
    "sonar.rust.clippy.enable=false",
    "sonar.qualitygate.wait=true",
    "sonar.qualitygate.timeout=300",
)


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
    claim_ids = collect_ids(claims, paths["claims"], "CLM-")
    source_ids = repo_ids | paper_ids | official_ids

    if len([r for r in repos if isinstance(r, Mapping) and r.get("tier") == "primary"]) != 10:
        issues.append(ValidationIssue(str(paths["repos"]), "exactly ten repositories must be marked tier 'primary' in the Phase 0 snapshot"))

    for index, source in enumerate(official):
        issues.extend(_validate_schema(source, root / "schemas/source-record.schema.json", Path(f"{paths['official']}/{index}")))

    for index, claim in enumerate(claims):
        issues.extend(_validate_schema(claim, root / "schemas/claim-record.schema.json", Path(f"{paths['claims']}/{index}")))
        if not isinstance(claim, Mapping):
            continue
        for source_id in claim.get("sources", []):
            if source_id.startswith("ADR-"):
                # ADR files have descriptive suffixes; check by prefix instead.
                if not list((root / "docs/architecture").glob(f"{source_id}-*.md")):
                    issues.append(ValidationIssue(f"{paths['claims']}/{index}", f"unresolved ADR source {source_id}"))
            elif source_id not in source_ids:
                issues.append(ValidationIssue(f"{paths['claims']}/{index}", f"unresolved source id {source_id}"))

    for index, repo in enumerate(repos):
        if not isinstance(repo, Mapping):
            continue
        url = repo.get("canonical_url")
        if not isinstance(url, str) or not url.startswith("https://"):
            issues.append(ValidationIssue(f"{paths['repos']}/{index}", "canonical_url must be HTTPS"))
        if not repo.get("license_spdx"):
            issues.append(ValidationIssue(f"{paths['repos']}/{index}", "license_spdx is required"))
        for claim_id in repo.get("claims_to_test", []):
            if claim_id not in claim_ids:
                issues.append(ValidationIssue(f"{paths['repos']}/{index}", f"unresolved claim id {claim_id}"))

    for index, paper in enumerate(papers):
        if not isinstance(paper, Mapping):
            continue
        url = paper.get("canonical_url")
        if not isinstance(url, str) or not url.startswith("https://"):
            issues.append(ValidationIssue(f"{paths['papers']}/{index}", "canonical_url must be HTTPS"))
        for claim_id in paper.get("claims", []):
            if claim_id not in claim_ids:
                issues.append(ValidationIssue(f"{paths['papers']}/{index}", f"unresolved claim id {claim_id}"))

    query_ids = collect_ids(queries, paths["queries"], "Q-")
    if len(query_ids) < 5:
        issues.append(ValidationIssue(str(paths["queries"]), "at least five independent discovery queries are required"))

    review_ids: set[str] = set()
    for collection_name, records, allowed_sources in (
        ("repository_reviews", repository_reviews, source_ids),
        ("paper_syntheses", paper_syntheses, paper_ids),
    ):
        for index, record in enumerate(records):
            pointer = f"{paths['review_queue']}/{collection_name}/{index}"
            if not isinstance(record, Mapping):
                issues.append(ValidationIssue(pointer, "review record must be an object"))
                continue
            review_id = record.get("id")
            if not isinstance(review_id, str) or not review_id:
                issues.append(ValidationIssue(pointer, "review id is required"))
            elif review_id in review_ids:
                issues.append(ValidationIssue(pointer, f"duplicate review id {review_id}"))
            else:
                review_ids.add(review_id)
            linked = record.get("source_ids")
            if not isinstance(linked, list) or not linked:
                issues.append(ValidationIssue(pointer, "source_ids must be a non-empty array"))
            else:
                for source_id in linked:
                    if source_id not in allowed_sources:
                        issues.append(ValidationIssue(pointer, f"unresolved or wrong-kind source id {source_id}"))
            output = record.get("output")
            if not isinstance(output, str) or not output.startswith("docs/research/") or not output.endswith(".md"):
                issues.append(ValidationIssue(pointer, "output must be a Markdown path under docs/research/"))
            if record.get("status") not in {"queued", "in_progress", "review", "complete", "blocked", "cancelled"}:
                issues.append(ValidationIssue(pointer, "invalid review status"))

    return issues


def _workflow_trigger_targets_main(value: Any) -> bool:
    if not isinstance(value, Mapping):
        return False
    branches = value.get("branches")
    if isinstance(branches, str):
        return branches == "main"
    return isinstance(branches, Sequence) and not isinstance(branches, (str, bytes)) and "main" in branches


def _validate_sonar_triggers(workflow_path: Path, document: Mapping[Any, Any]) -> list[ValidationIssue]:
    triggers = document.get("on", document.get(True))
    if not isinstance(triggers, Mapping):
        return [ValidationIssue(str(workflow_path), "Sonar workflow 'on' triggers must be a mapping")]

    issues = [
        ValidationIssue(str(workflow_path), f"Sonar workflow must define {event_name}")
        for event_name in ("push", "pull_request", "workflow_dispatch")
        if event_name not in triggers
    ]
    for event_name in ("push", "pull_request"):
        if event_name in triggers and not _workflow_trigger_targets_main(triggers[event_name]):
            issues.append(ValidationIssue(str(workflow_path), f"Sonar workflow {event_name} must target main"))
    if "workflow_run" in triggers:
        issues.append(ValidationIssue(str(workflow_path), "workflow_run is forbidden in Sonar workflow"))
    return issues


def _sonar_job_steps(job: Any) -> list[Any]:
    if not isinstance(job, Mapping):
        return []
    steps = job.get("steps")
    return steps if isinstance(steps, list) else []


def _find_action_step(steps: list[Any], prefix: str) -> Mapping[str, Any] | None:
    return next(
        (
            step
            for step in steps
            if isinstance(step, Mapping) and str(step.get("uses", "")).startswith(prefix)
        ),
        None,
    )


def _find_sonar_scanner_job(
    workflow_path: Path, document: Mapping[Any, Any]
) -> tuple[Mapping[str, Any] | None, list[Any], list[ValidationIssue]]:
    jobs = document.get("jobs")
    if not isinstance(jobs, Mapping):
        return None, [], [ValidationIssue(str(workflow_path), "Sonar workflow jobs must be a mapping")]

    candidates = []
    for job in jobs.values():
        steps = _sonar_job_steps(job)
        if _find_action_step(steps, "SonarSource/sonarqube-scan-action@") is not None:
            candidates.append((job, steps))
    if len(candidates) != 1:
        return None, [], [ValidationIssue(str(workflow_path), "Sonar workflow must contain exactly one scanner job")]
    scanner_job, steps = candidates[0]
    return scanner_job, steps, []


def _validate_sonar_job_guards(workflow_path: Path, scanner_job: Mapping[str, Any]) -> list[ValidationIssue]:
    job_if = str(scanner_job.get("if", ""))
    issues: list[ValidationIssue] = []
    if "vars.FORGELLM_SONAR_CI_ENABLED == 'true'" not in job_if:
        issues.append(
            ValidationIssue(
                str(workflow_path),
                "Sonar scanner job requires FORGELLM_SONAR_CI_ENABLED == 'true' guard",
            )
        )
    if "github.event.pull_request.head.repo.fork == false" not in job_if:
        issues.append(
            ValidationIssue(
                str(workflow_path),
                "Sonar scanner job requires fork guard github.event.pull_request.head.repo.fork == false",
            )
        )
    return issues


def _validate_sonar_checkout(workflow_path: Path, steps: list[Any]) -> list[ValidationIssue]:
    checkout_step = _find_action_step(steps, "actions/checkout@")
    if checkout_step is None:
        return [ValidationIssue(str(workflow_path), "Sonar scanner job requires actions/checkout")]

    issues: list[ValidationIssue] = []
    if checkout_step.get("uses") != _SONAR_CHECKOUT_ACTION:
        issues.append(ValidationIssue(str(workflow_path), "Sonar checkout action must use the reviewed immutable SHA"))
    checkout_with = checkout_step.get("with")
    if not isinstance(checkout_with, Mapping) or checkout_with.get("persist-credentials") is not False:
        issues.append(ValidationIssue(str(workflow_path), "Sonar checkout requires persist-credentials: false"))
    if not isinstance(checkout_with, Mapping) or checkout_with.get("fetch-depth") != 0:
        issues.append(ValidationIssue(str(workflow_path), "Sonar checkout requires fetch-depth: 0"))
    return issues


def _validate_sonar_scanner_step(workflow_path: Path, steps: list[Any]) -> list[ValidationIssue]:
    scanner_step = _find_action_step(steps, "SonarSource/sonarqube-scan-action@")
    if scanner_step is None:
        return [ValidationIssue(str(workflow_path), "Sonar scanner action is missing")]

    issues: list[ValidationIssue] = []
    if scanner_step.get("uses") != _SONAR_SCANNER_ACTION:
        issues.append(ValidationIssue(str(workflow_path), "Sonar scanner action must use the reviewed immutable SHA"))

    scanner_with = scanner_step.get("with")
    if not isinstance(scanner_with, Mapping):
        issues.append(ValidationIssue(str(workflow_path), "Sonar scanner step requires a with mapping"))
        scanner_with = {}
    scanner_version = scanner_with.get("scannerVersion")
    if not isinstance(scanner_version, str) or not scanner_version.strip():
        issues.append(ValidationIssue(str(workflow_path), "Sonar scanner requires non-empty scannerVersion"))

    scanner_args = scanner_with.get("args", "")
    scanner_args = scanner_args if isinstance(scanner_args, str) else ""
    issues.extend(
        ValidationIssue(str(workflow_path), f"Sonar scanner trusted argument is missing: {marker}")
        for marker in _SONAR_TRUSTED_ARGUMENTS
        if marker not in scanner_args
    )

    scanner_env = scanner_step.get("env")
    if not isinstance(scanner_env, Mapping) or scanner_env.get("SONAR_TOKEN") != _SONAR_TOKEN_REFERENCE:
        issues.append(ValidationIssue(str(workflow_path), "Sonar scanner auth must use exactly secrets.SONAR_TOKEN"))
    return issues


def _is_sonar_token_preflight(step: Mapping[str, Any], run_script: str) -> bool:
    step_env = step.get("env")
    return (
        isinstance(step_env, Mapping)
        and step_env.get("SONAR_TOKEN") == _SONAR_TOKEN_REFERENCE
        and "SONAR_TOKEN" in run_script
        and "-z" in run_script
        and "exit 1" in run_script
    )


def _run_step_command(run_script: str) -> str:
    first_command = next((line.strip() for line in run_script.splitlines() if line.strip()), "run")
    return first_command.split()[0] if first_command else "run"


def _validate_sonar_token_runs(
    workflow_path: Path, scanner_job: Mapping[str, Any], steps: list[Any]
) -> list[ValidationIssue]:
    if _SONAR_TOKEN_REFERENCE not in yaml.safe_dump(scanner_job, sort_keys=False):
        return []

    issues: list[ValidationIssue] = []
    for step in steps:
        if not isinstance(step, Mapping):
            continue
        run_script = step.get("run")
        if not isinstance(run_script, str) or _is_sonar_token_preflight(step, run_script):
            continue
        command = _run_step_command(run_script)
        issues.append(
            ValidationIssue(
                str(workflow_path),
                f"token-bearing Sonar job must not execute project commands; rejected run step starting with {command}",
            )
        )
    return issues


def _validate_sonar_workflow(workflow_path: Path, workflow_text: str) -> list[ValidationIssue]:
    document = yaml.safe_load(workflow_text)
    if not isinstance(document, Mapping):
        return [ValidationIssue(str(workflow_path), "Sonar workflow root must be a mapping")]

    issues = _validate_sonar_triggers(workflow_path, document)
    if document.get("permissions") != {"contents": "read"}:
        issues.append(ValidationIssue(str(workflow_path), "Sonar workflow permissions must be exactly contents: read"))

    scanner_job, steps, job_issues = _find_sonar_scanner_job(workflow_path, document)
    issues.extend(job_issues)
    if scanner_job is None:
        return issues

    issues.extend(_validate_sonar_job_guards(workflow_path, scanner_job))
    issues.extend(_validate_sonar_checkout(workflow_path, steps))
    issues.extend(_validate_sonar_scanner_step(workflow_path, steps))
    issues.extend(_validate_sonar_token_runs(workflow_path, scanner_job, steps))
    return issues


def validate_repository_automation(root: Path | str) -> list[ValidationIssue]:
    """Validate repository automation syntax and high-value security invariants."""

    root = Path(root).resolve()
    issues: list[ValidationIssue] = []

    # Validate JSON Schemas as schemas, not only as JSON documents.
    for schema_path in sorted((root / "schemas").glob("*.schema.json")):
        try:
            schema = _load_json(schema_path)
            Draft202012Validator.check_schema(schema)
        except Exception as exc:  # jsonschema raises several schema-specific subclasses.
            issues.append(ValidationIssue(str(schema_path), f"invalid JSON Schema: {exc}"))

    pyproject = root / "pyproject.toml"
    try:
        tomllib.loads(pyproject.read_text(encoding="utf-8"))
    except (FileNotFoundError, tomllib.TOMLDecodeError) as exc:
        issues.append(ValidationIssue(str(pyproject), f"invalid TOML: {exc}"))

    uses_pattern = re.compile(r"^\s*uses:\s*[^#\s]+@([^#\s]+)", re.MULTILINE)
    full_sha = re.compile(r"^[0-9a-f]{40}$")
    workflow_texts: dict[str, str] = {}
    for workflow in sorted((root / ".github/workflows").glob("*.yml")):
        try:
            workflow_text = workflow.read_text(encoding="utf-8")
            yaml.safe_load(workflow_text)
        except (UnicodeDecodeError, yaml.YAMLError) as exc:
            issues.append(ValidationIssue(str(workflow), f"invalid workflow YAML: {exc}"))
            continue
        workflow_texts[workflow.name] = workflow_text
        for match in uses_pattern.finditer(workflow_text):
            reference = match.group(1)
            if not full_sha.fullmatch(reference):
                line = workflow_text.count("\n", 0, match.start()) + 1
                issues.append(ValidationIssue(f"{workflow}:{line}", f"action reference is not pinned to a full commit SHA: {reference}"))
        if re.search(r"^\s*pull_request_target\s*:", workflow_text, flags=re.MULTILINE):
            issues.append(ValidationIssue(str(workflow), "pull_request_target is forbidden in ForgeLLM workflows"))
        if "self-hosted" in workflow_text and re.search(r"^\s*pull_request\s*:", workflow_text, flags=re.MULTILINE):
            issues.append(ValidationIssue(str(workflow), "a workflow containing a self-hosted runner must not be triggered by pull_request"))

    sonar_text = workflow_texts.get("sonar.yml")
    if sonar_text is not None:
        issues.extend(_validate_sonar_workflow(root / ".github/workflows/sonar.yml", sonar_text))

    guarded_workflows = {
        "dependency-review.yml": (
            "vars.FORGELLM_ENABLE_DEPENDENCY_REVIEW == 'true'",
            "github.event.pull_request.head.repo.fork == false",
        ),
        "codeql.yml": (
            "vars.FORGELLM_ENABLE_CODEQL == 'true'",
            "github.event.repository.visibility == 'public'",
        ),
    }
    for workflow_name, required_markers in guarded_workflows.items():
        workflow_path = root / ".github/workflows" / workflow_name
        workflow_text = workflow_texts.get(workflow_name)
        if workflow_text is None:
            issues.append(ValidationIssue(str(workflow_path), "required guarded workflow is missing or invalid"))
            continue
        for marker in required_markers:
            if marker not in workflow_text:
                issues.append(
                    ValidationIssue(
                        str(workflow_path),
                        f"required private-repository feature guard is missing: {marker}",
                    )
                )

    phase0_workflow = root / ".github/workflows/phase0.yml"
    phase0_text = workflow_texts.get("phase0.yml")
    if phase0_text is None:
        issues.append(ValidationIssue(str(phase0_workflow), "required Phase 0 workflow is missing or invalid"))
    elif "run: make ci" not in phase0_text:
        issues.append(ValidationIssue(str(phase0_workflow), "Phase 0 workflow must execute the complete 'make ci' gate"))

    for issue_form in sorted((root / ".github/ISSUE_TEMPLATE").glob("*.yml")):
        try:
            document = yaml.safe_load(issue_form.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            issues.append(ValidationIssue(str(issue_form), f"invalid issue-form YAML: {exc}"))
            continue
        if issue_form.name == "config.yml":
            if not isinstance(document, Mapping):
                issues.append(ValidationIssue(str(issue_form), "issue template config must be an object"))
            continue
        if not isinstance(document, Mapping):
            issues.append(ValidationIssue(str(issue_form), "issue form must be an object"))
            continue
        missing = {"name", "description", "body"} - set(document)
        if missing:
            issues.append(ValidationIssue(str(issue_form), f"issue form is missing keys: {', '.join(sorted(missing))}"))
        if "about" in document:
            issues.append(ValidationIssue(str(issue_form), "issue forms use 'description', not legacy 'about'"))
        if not isinstance(document.get("body"), list) or not document.get("body"):
            issues.append(ValidationIssue(str(issue_form), "issue form body must be a non-empty array"))

    gitlab_ci = root / ".gitlab-ci.yml"
    try:
        yaml.safe_load(gitlab_ci.read_text(encoding="utf-8"))
    except (FileNotFoundError, yaml.YAMLError) as exc:
        issues.append(ValidationIssue(str(gitlab_ci), f"invalid GitLab CI YAML: {exc}"))

    return issues


def scan_for_secrets(root: Path | str) -> list[ValidationIssue]:
    root = Path(root).resolve()
    issues: list[ValidationIssue] = []
    ignored_parts = {".git", ".venv", "__pycache__", ".pytest_cache"}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in _TEXT_SUFFIXES:
            continue
        if any(part in ignored_parts for part in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in _SECRET_PATTERNS.items():
            match = pattern.search(text)
            if match:
                line = text.count("\n", 0, match.start()) + 1
                issues.append(ValidationIssue(f"{path}:{line}", f"possible {label}"))
    return issues


def validate_project(root: Path | str) -> list[ValidationIssue]:
    root = Path(root).resolve()
    required = [
        "README.md",
        "AGENTS.md",
        "CLAUDE.md",
        "chatgpt/PROJECT_INSTRUCTIONS.txt",
        "docs/architecture/PROJECT_CHARTER.md",
        "docs/state/CURRENT_STATE.md",
        "docs/research/RESEARCH_PROTOCOL.md",
        "docs/benchmarks/BENCHMARK_STANDARD.md",
        "research/repos.yaml",
        "research/papers.yaml",
        "research/official_sources.yaml",
        "research/claims.yaml",
        "schemas/benchmark-result.schema.json",
        "schemas/task-packet.schema.json",
    ]
    issues: list[ValidationIssue] = []
    for relative in required:
        path = root / relative
        if not path.is_file():
            issues.append(ValidationIssue(relative, "required file is missing"))
        elif path.stat().st_size == 0:
            issues.append(ValidationIssue(relative, "required file is empty"))

    mobile_dir = root / "chatgpt/mobile-core"
    mobile_files = sorted(mobile_dir.glob("*.md")) if mobile_dir.is_dir() else []
    expected_mobile_names = [
        "00_FORGELLM_CORE_CONTEXT.md",
        "01_FORGELLM_AGENT_OPERATING_SYSTEM.md",
        "02_FORGELLM_RESEARCH_AND_EVIDENCE.md",
        "03_FORGELLM_STATE_AND_DECISIONS.md",
        "04_FORGELLM_PROMPTS_AND_WORKFLOWS.md",
    ]
    if [path.name for path in mobile_files] != expected_mobile_names:
        issues.append(ValidationIssue(str(mobile_dir), f"mobile bundle must contain exactly: {', '.join(expected_mobile_names)}"))

    issues.extend(validate_research_catalogs(root))

    benchmark_example = root / "examples/benchmarks/valid-example.json"
    if benchmark_example.exists():
        issues.extend(validate_benchmark_file(benchmark_example, root=root))
    else:
        issues.append(ValidationIssue(str(benchmark_example), "required valid benchmark example is missing"))

    task_example = root / "examples/tasks/P0-T02.yaml"
    if task_example.exists():
        issues.extend(validate_task_packet_file(task_example, root=root))
    else:
        issues.append(ValidationIssue(str(task_example), "required task packet example is missing"))

    issues.extend(validate_repository_automation(root))
    issues.extend(scan_for_secrets(root))
    return issues
