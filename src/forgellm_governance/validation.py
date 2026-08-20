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
_SONAR_WORKFLOW_PATH = ".github/workflows/sonar.yml"
_SONAR_PROPERTIES_PATH = "sonar-project.properties"
_SONAR_AUTOMATIC_PROPERTIES_PATH = ".sonarcloud.properties"
_SONAR_ADR_PATH = "docs/architecture/ADR-0004-sonarqube-analysis-method.md"
_SONAR_SCANNER_ACTION = "SonarSource/sonarqube-scan-action@22918119ff8e1ca75a623e15c8296b6ea4fbe28f"
_SONAR_CHECKOUT_PREFIX = "actions/checkout@"
_SONAR_TOKEN_NAME = "SONAR_TOKEN"
_SONAR_TOKEN_REFERENCE = "${{ secrets.SONAR_TOKEN }}"
_SONAR_SCANNER_VERSION = "8.1.0.6389"
_SONAR_EXPECTED_PROPERTIES = {
    "sonar.projectKey": "leon36000_ForgeLLM",
    "sonar.sourceEncoding": "UTF-8",
    "sonar.sources": ".sonar-input/source",
    "sonar.rust.clippy.enable": "false",
    "sonar.rust.clippyReport.reportPaths": ".sonar-input/reports/clippy.json",
}
_SONAR_EXPECTED_ARGS = " ".join(
    (
        "-Dsonar.host.url=https://sonarcloud.io",
        "-Dsonar.organization=${{ vars.SONAR_ORGANIZATION }}",
        "-Dsonar.projectKey=leon36000_ForgeLLM",
        "-Dsonar.sources=.sonar-input/source",
        "-Dsonar.rust.clippy.enable=false",
        "-Dsonar.rust.clippyReport.reportPaths=.sonar-input/reports/clippy.json",
        "-Dsonar.qualitygate.wait=true",
        "-Dsonar.qualitygate.timeout=300",
    )
)
_SONAR_CONTRIBUTOR_COMMAND = re.compile(
    r"(?:^|[;&|]\s*|\s)(?:\./|cargo(?:\s|$)|make(?:\s|$)|cmake(?:\s|$)|ninja(?:\s|$)|"
    r"pytest(?:\s|$)|python(?:3)?\s+(?:-m\s+)?(?:pytest|build|pip)|npm(?:\s|$)|pnpm(?:\s|$)|"
    r"yarn(?:\s|$)|git\s+(?:clone|checkout|switch)|bash\s+(?:\./)?(?:scripts?/|\.github/)|"
    r"sh\s+(?:\./)?(?:scripts?/|\.github/))"
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


def _sonar_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sonar_sequence(value: Any) -> list[Any]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return list(value)
    return []


def _sonar_truthy(value: Any) -> bool:
    return value is True or (isinstance(value, str) and value.lower() == "true")


def _sonar_contains_token(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(
            _SONAR_TOKEN_NAME in str(key) or _sonar_contains_token(item)
            for key, item in value.items()
        )
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_sonar_contains_token(item) for item in value)
    return isinstance(value, str) and _SONAR_TOKEN_NAME in value


def _sonar_add_issue(
    issues: list[ValidationIssue],
    path: Path | str,
    code: str,
    message: str,
) -> None:
    issue = ValidationIssue(str(path), f"[{code}] {message}")
    if issue not in issues:
        issues.append(issue)


def _sonar_method_is_accepted(root: Path) -> bool:
    adr_path = root / _SONAR_ADR_PATH
    try:
        text = adr_path.read_text(encoding="utf-8")
    except (FileNotFoundError, UnicodeDecodeError):
        return False
    status_accepted = re.search(r"(?mi)^\s*-\s+\*\*Status:\*\*\s+accepted\s*$", text) is not None
    decision = re.search(r"(?ms)^\s*##\s+Decision\s*$\n(?P<body>.*?)(?:(?=^\s*##\s+)|(?=\Z))", text)
    return (
        status_accepted
        and decision is not None
        and re.search(r"Select exactly[^\n]*`ci_based_only`", decision.group("body")) is not None
    )


def _sonar_load_workflow(path: Path, issues: list[ValidationIssue]) -> Mapping[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        _sonar_add_issue(
            issues,
            path,
            "SONAR_CONFIG_PAIR",
            "Sonar workflow and properties must be prepared together",
        )
        return {}
    except UnicodeDecodeError as exc:
        _sonar_add_issue(issues, path, "SONAR_WORKFLOW_YAML", f"workflow must be UTF-8: {exc}")
        return {}
    try:
        document = yaml.load(text, Loader=yaml.BaseLoader)
    except yaml.YAMLError as exc:
        _sonar_add_issue(issues, path, "SONAR_WORKFLOW_YAML", f"invalid workflow YAML: {exc}")
        return {}
    if not isinstance(document, Mapping):
        _sonar_add_issue(issues, path, "SONAR_WORKFLOW_YAML", "workflow root must be an object")
        return {}
    return document


def _sonar_load_properties(path: Path, issues: list[ValidationIssue]) -> Mapping[str, str]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        _sonar_add_issue(
            issues,
            path,
            "SONAR_CONFIG_PAIR",
            "Sonar workflow and properties must be prepared together",
        )
        return {}
    except UnicodeDecodeError as exc:
        _sonar_add_issue(issues, path, "SONAR_TRUSTED_CONFIG", f"properties must be UTF-8: {exc}")
        return {}

    properties: dict[str, str] = {}
    invalid = False
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            invalid = True
            _sonar_add_issue(
                issues,
                f"{path}:{line_number}",
                "SONAR_TRUSTED_CONFIG",
                "property lines must be deterministic key=value assignments",
            )
            continue
        key, value = (part.strip() for part in line.split("=", maxsplit=1))
        if key in properties:
            invalid = True
            _sonar_add_issue(
                issues,
                f"{path}:{line_number}",
                "SONAR_TRUSTED_CONFIG",
                f"duplicate property key: {key}",
            )
            continue
        properties[key] = value

    if properties.get("sonar.rust.clippy.enable") != "false":
        _sonar_add_issue(
            issues,
            path,
            "SONAR_CLIPPY",
            "automatic Clippy must be disabled in the token-bearing scanner",
        )
    if invalid or properties != _SONAR_EXPECTED_PROPERTIES:
        _sonar_add_issue(
            issues,
            path,
            "SONAR_TRUSTED_CONFIG",
            "Sonar properties must contain only the reviewed fixed source, report, project, encoding, and Clippy settings",
        )
    return properties


def _sonar_local_action_metadata(root: Path, uses: str) -> Mapping[str, Any]:
    action_root = root / uses.removeprefix("./")
    for name in ("action.yml", "action.yaml"):
        path = action_root / name
        if not path.is_file():
            continue
        try:
            document = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
        except (UnicodeDecodeError, yaml.YAMLError):
            return {}
        return _sonar_mapping(document)
    return {}


def _sonar_validate_events(
    workflow_path: Path,
    workflow: Mapping[str, Any],
    issues: list[ValidationIssue],
) -> None:
    events = _sonar_mapping(workflow.get("on"))
    allowed = {"push", "workflow_dispatch"}
    forbidden = {"pull_request", "pull_request_target", "workflow_run"}
    if forbidden.intersection(events) or set(events) - allowed:
        _sonar_add_issue(
            issues,
            workflow_path,
            "SONAR_FORBIDDEN_EVENT",
            "pull-request, workflow-run, and other unreviewed privileged scanner events are forbidden",
        )
    if set(events) != allowed:
        _sonar_add_issue(
            issues,
            workflow_path,
            "SONAR_ACTIVATION_GATE",
            "prepared scanner workflow events must be exactly push on main and trusted manual dispatch",
        )

    push = _sonar_mapping(events.get("push"))
    if push.get("branches") != ["main"]:
        _sonar_add_issue(
            issues,
            workflow_path,
            "SONAR_ACTIVATION_GATE",
            "push activation must target only the protected main branch",
        )

    dispatch = _sonar_mapping(events.get("workflow_dispatch"))
    if dispatch.get("inputs") not in (None, {}):
        _sonar_add_issue(
            issues,
            workflow_path,
            "SONAR_BRIDGE_BOUNDS",
            "Task 4B.0 forbids contributor-controlled dispatch inputs before the bridge design is accepted",
        )

    if workflow.get("permissions") is not None:
        _sonar_add_issue(
            issues,
            workflow_path,
            "SONAR_ACTIVATION_GATE",
            "permissions must be declared per job, not at workflow scope",
        )


def _sonar_validate_job_scopes(
    workflow_path: Path,
    workflow: Mapping[str, Any],
    jobs: Mapping[str, Any],
    issues: list[ValidationIssue],
) -> None:
    if _sonar_contains_token(workflow.get("env")):
        _sonar_add_issue(
            issues,
            workflow_path,
            "SONAR_TOKEN_SCOPE",
            "Sonar credentials are forbidden at workflow scope",
        )

    for job_name in sorted(jobs):
        job = _sonar_mapping(jobs[job_name])
        job_path = f"{workflow_path}#jobs.{job_name}"
        secrets = job.get("secrets")
        if "uses" in job and (secrets == "inherit" or _sonar_contains_token(secrets)):
            _sonar_add_issue(
                issues,
                job_path,
                "SONAR_REUSABLE_SECRET",
                "reusable workflows must not receive inherited or explicit Sonar credentials",
            )
        if _sonar_contains_token(job.get("env")):
            _sonar_add_issue(
                issues,
                job_path,
                "SONAR_TOKEN_SCOPE",
                "Sonar credentials are forbidden at job scope",
            )
        if _sonar_contains_token(_sonar_mapping(job.get("container")).get("env")):
            _sonar_add_issue(
                issues,
                job_path,
                "SONAR_TOKEN_SCOPE",
                "Sonar credentials are forbidden at container scope",
            )
        services = _sonar_mapping(job.get("services"))
        if any(_sonar_contains_token(_sonar_mapping(service).get("env")) for service in services.values()):
            _sonar_add_issue(
                issues,
                job_path,
                "SONAR_TOKEN_SCOPE",
                "Sonar credentials are forbidden at service scope",
            )
        if _sonar_contains_token(job.get("outputs")):
            _sonar_add_issue(
                issues,
                job_path,
                "SONAR_TOKEN_PROPAGATION",
                "Sonar credentials must not propagate through job outputs",
            )
        if _sonar_truthy(job.get("continue-on-error")):
            _sonar_add_issue(
                issues,
                job_path,
                "SONAR_RESULT_MASKING",
                "scanner job failure must not be converted to success",
            )
        job_permissions = job.get("permissions")
        if dict(_sonar_mapping(job_permissions)) != {"contents": "read"}:
            _sonar_add_issue(
                issues,
                job_path,
                "SONAR_ACTIVATION_GATE",
                "every Sonar job must declare exactly contents: read at job scope",
            )


def _sonar_find_scanner_job(jobs: Mapping[str, Any]) -> tuple[str | None, Mapping[str, Any]]:
    named = _sonar_mapping(jobs.get("scanner"))
    if named:
        return "scanner", named
    for job_name in sorted(jobs):
        job = _sonar_mapping(jobs[job_name])
        for step in _sonar_sequence(job.get("steps")):
            if not isinstance(step, Mapping):
                continue
            if str(step.get("uses", "")).startswith("SonarSource/sonarqube-scan-action@"):
                return job_name, job
            if _sonar_contains_token(step):
                return job_name, job
    return None, {}


def _sonar_validate_scanner_job(
    root: Path,
    workflow_path: Path,
    scanner_name: str | None,
    scanner_job: Mapping[str, Any],
    jobs: Mapping[str, Any],
    issues: list[ValidationIssue],
) -> None:
    if scanner_name is None:
        _sonar_add_issue(
            issues,
            workflow_path,
            "SONAR_SCANNER_PROVENANCE",
            "exactly one reviewed scanner job is required",
        )
        return

    job_path = f"{workflow_path}#jobs.{scanner_name}"
    condition = str(scanner_job.get("if", ""))
    required_guards = (
        "vars.FORGELLM_ENABLE_SONAR_CI == 'true'",
        "vars.FORGELLM_AUTOMATIC_ANALYSIS_DISABLED == 'true'",
        "github.ref == 'refs/heads/main'",
    )
    if any(marker not in condition for marker in required_guards):
        _sonar_add_issue(
            issues,
            job_path,
            "SONAR_ACTIVATION_GATE",
            "scanner activation must be default-off, require the disabled-Automatic-Analysis gate, and target protected main",
        )
    if scanner_job.get("runs-on") != "ubuntu-24.04":
        _sonar_add_issue(
            issues,
            job_path,
            "SONAR_ACTIVATION_GATE",
            "scanner job must run on ubuntu-24.04",
        )
    try:
        timeout = int(str(scanner_job.get("timeout-minutes", "0")))
    except ValueError:
        timeout = 0
    if not 1 <= timeout <= 20:
        _sonar_add_issue(
            issues,
            job_path,
            "SONAR_ACTIVATION_GATE",
            "scanner job timeout must be bounded to at most 20 minutes",
        )

    needs_value = scanner_job.get("needs")
    needs = [needs_value] if isinstance(needs_value, str) else [str(item) for item in _sonar_sequence(needs_value)]
    if not needs or any(name not in jobs for name in needs):
        _sonar_add_issue(
            issues,
            job_path,
            "SONAR_PRODUCER_BOUNDARY",
            "scanner must consume a separately reviewed secretless producer boundary",
        )

    raw_steps = scanner_job.get("steps")
    all_steps = _sonar_sequence(raw_steps)
    steps = [step for step in all_steps if isinstance(step, Mapping)]
    if not isinstance(raw_steps, Sequence) or isinstance(raw_steps, (str, bytes, bytearray)) or len(steps) != len(all_steps):
        _sonar_add_issue(
            issues,
            job_path,
            "SONAR_SCANNER_PROVENANCE",
            "scanner job steps must be a deterministic array of objects",
        )

    action_indexes = [
        index
        for index, step in enumerate(steps)
        if str(step.get("uses", "")).startswith("SonarSource/sonarqube-scan-action@")
    ]
    token_indexes = [index for index, step in enumerate(steps) if _sonar_contains_token(step)]
    if len(action_indexes) != 1:
        _sonar_add_issue(
            issues,
            job_path,
            "SONAR_SCANNER_PROVENANCE",
            "exactly one reviewed scanner action is required",
        )
    if len(token_indexes) != 1:
        _sonar_add_issue(
            issues,
            job_path,
            "SONAR_TOKEN_SCOPE",
            "exactly one final scanner step may reference the Sonar credential",
        )

    if len(action_indexes) == 1:
        scanner_index = action_indexes[0]
    elif token_indexes:
        scanner_index = token_indexes[-1]
    else:
        return

    scanner_step = steps[scanner_index]
    scanner_path = f"{job_path}.steps[{scanner_index}]"
    if scanner_index != len(steps) - 1:
        _sonar_add_issue(
            issues,
            scanner_path,
            "SONAR_SCANNER_FINAL_STEP",
            "the token-bearing scanner action must be the final job step with no post-processing",
        )

    for index, step in enumerate(steps):
        step_path = f"{job_path}.steps[{index}]"
        uses = str(step.get("uses", ""))
        run = str(step.get("run", ""))
        if uses.startswith(_SONAR_CHECKOUT_PREFIX) or re.search(
            r"\bgit\s+(?:clone|checkout|switch)\b|github\.event\.pull_request|github\.head_ref",
            run,
        ):
            _sonar_add_issue(
                issues,
                step_path,
                "SONAR_SCANNER_CHECKOUT",
                "scanner job must not checkout contributor-originated source",
            )
        if uses.startswith("./"):
            _sonar_add_issue(
                issues,
                step_path,
                "SONAR_LOCAL_ACTION",
                "repository-local or composite actions are forbidden in the scanner job",
            )
            metadata = _sonar_local_action_metadata(root, uses)
            runs = _sonar_mapping(metadata.get("runs"))
            if any(key in runs for key in ("pre", "pre-if", "post", "post-if")):
                _sonar_add_issue(
                    issues,
                    step_path,
                    "SONAR_SCANNER_HOOKS",
                    "unreviewed scanner action pre/post hooks are forbidden",
                )
        if run and _SONAR_CONTRIBUTOR_COMMAND.search(run):
            _sonar_add_issue(
                issues,
                step_path,
                "SONAR_TOKEN_EXECUTION",
                "scanner job must not execute repository or contributor-controlled code",
            )
        if _sonar_truthy(step.get("continue-on-error")) or "|| true" in run:
            _sonar_add_issue(
                issues,
                step_path,
                "SONAR_RESULT_MASKING",
                "scanner failure must not be masked as success",
            )
        if _sonar_contains_token(step.get("outputs")):
            _sonar_add_issue(
                issues,
                step_path,
                "SONAR_TOKEN_PROPAGATION",
                "Sonar credentials must not propagate through step outputs",
            )
        if _sonar_contains_token(step) and any(
            marker in run for marker in ("GITHUB_OUTPUT", "GITHUB_STATE", "GITHUB_ENV")
        ):
            _sonar_add_issue(
                issues,
                step_path,
                "SONAR_TOKEN_PROPAGATION",
                "Sonar credentials must not propagate through GitHub output, state, or environment files",
            )
        if index != scanner_index and _sonar_contains_token(step):
            _sonar_add_issue(
                issues,
                step_path,
                "SONAR_TOKEN_SCOPE",
                "only the final reviewed scanner action may reference the Sonar credential",
            )

    uses = str(scanner_step.get("uses", ""))
    run = str(scanner_step.get("run", ""))
    if run:
        _sonar_add_issue(
            issues,
            scanner_path,
            "SONAR_TOKEN_EXECUTION",
            "token-bearing shell or contributor commands are forbidden",
        )
        if "./" in run or "scripts/" in run:
            _sonar_add_issue(
                issues,
                scanner_path,
                "SONAR_LOCAL_EXECUTION",
                "repository-local scripts must not execute with the Sonar credential",
            )
    if uses.startswith("./"):
        metadata = _sonar_local_action_metadata(root, uses)
        runs = _sonar_mapping(metadata.get("runs"))
        if any(key in runs for key in ("pre", "pre-if", "post", "post-if")):
            _sonar_add_issue(
                issues,
                scanner_path,
                "SONAR_SCANNER_HOOKS",
                "unreviewed scanner action pre/post hooks are forbidden",
            )

    if uses != _SONAR_SCANNER_ACTION:
        _sonar_add_issue(
            issues,
            scanner_path,
            "SONAR_SCANNER_PROVENANCE",
            "scanner action must be pinned to the reviewed immutable commit",
        )
    if scanner_step.get("if") is not None:
        _sonar_add_issue(
            issues,
            scanner_path,
            "SONAR_RESULT_MASKING",
            "the final scanner action must not be conditionally skipped",
        )

    scanner_env = _sonar_mapping(scanner_step.get("env"))
    if scanner_env.get(_SONAR_TOKEN_NAME) != _SONAR_TOKEN_REFERENCE or set(scanner_env) != {_SONAR_TOKEN_NAME}:
        _sonar_add_issue(
            issues,
            scanner_path,
            "SONAR_TOKEN_REFERENCE",
            "scanner credential must be the exact GitHub secret expression and the only scanner environment entry",
        )

    scanner_with = _sonar_mapping(scanner_step.get("with"))
    if (
        scanner_with.get("projectBaseDir") != "."
        or scanner_with.get("scannerVersion") != _SONAR_SCANNER_VERSION
        or scanner_with.get("skipSignatureVerification") != "false"
    ):
        _sonar_add_issue(
            issues,
            scanner_path,
            "SONAR_SCANNER_PROVENANCE",
            "action commit, scanner binary version, project base, and signature verification must be pinned separately",
        )

    arguments = str(scanner_with.get("args", ""))
    if "-Dsonar.rust.clippy.enable=false" not in arguments:
        _sonar_add_issue(
            issues,
            scanner_path,
            "SONAR_CLIPPY",
            "automatic Clippy must remain disabled in scanner arguments",
        )
    if arguments != _SONAR_EXPECTED_ARGS:
        _sonar_add_issue(
            issues,
            scanner_path,
            "SONAR_TRUSTED_CONFIG",
            "scanner host, organization, project, source, report paths, and quality-gate settings must be fixed and reviewed",
        )


def _sonar_validate_bridge_markers(
    workflow_path: Path,
    jobs: Mapping[str, Any],
    issues: list[ValidationIssue],
) -> None:
    bridge_markers = (
        "${{ inputs.",
        "github.event.workflow_run",
        "download-artifact",
        "| tar",
        "tar -",
        "unzip ",
    )
    for job_name in sorted(jobs):
        job = _sonar_mapping(jobs[job_name])
        for index, step in enumerate(_sonar_sequence(job.get("steps"))):
            if not isinstance(step, Mapping):
                continue
            text = str(step.get("run", ""))
            if any(marker in text for marker in bridge_markers):
                _sonar_add_issue(
                    issues,
                    f"{workflow_path}#jobs.{job_name}.steps[{index}]",
                    "SONAR_BRIDGE_BOUNDS",
                    "PR/artifact bridge input and extraction semantics require the separately blocked Task 4B.3 design",
                )


def validate_sonar_ci_configuration(root: Path | str) -> list[ValidationIssue]:
    """Validate the prepared, inactive CI-based Sonar trust boundary selected by ADR-0004."""

    root = Path(root).resolve()
    workflow_path = root / _SONAR_WORKFLOW_PATH
    properties_path = root / _SONAR_PROPERTIES_PATH
    automatic_path = root / _SONAR_AUTOMATIC_PROPERTIES_PATH
    workflow_exists = workflow_path.is_file()
    properties_exists = properties_path.is_file()
    automatic_exists = automatic_path.exists()

    if not workflow_exists and not properties_exists and not automatic_exists:
        return []

    issues: list[ValidationIssue] = []
    if workflow_exists != properties_exists:
        _sonar_add_issue(
            issues,
            root,
            "SONAR_CONFIG_PAIR",
            "Sonar workflow and properties must be prepared together",
        )
    if automatic_exists:
        _sonar_add_issue(
            issues,
            automatic_path,
            "SONAR_METHOD_OVERLAP",
            "Automatic Analysis configuration must not overlap the selected CI-only method",
        )
    if not _sonar_method_is_accepted(root):
        _sonar_add_issue(
            issues,
            root / _SONAR_ADR_PATH,
            "SONAR_METHOD_DECISION",
            "Sonar CI configuration requires accepted ADR-0004 decision ci_based_only",
        )

    if not workflow_exists or not properties_exists:
        return sorted(issues, key=lambda issue: (issue.path, issue.message))

    _sonar_load_properties(properties_path, issues)
    workflow = _sonar_load_workflow(workflow_path, issues)
    if not workflow:
        return sorted(issues, key=lambda issue: (issue.path, issue.message))

    _sonar_validate_events(workflow_path, workflow, issues)
    jobs = _sonar_mapping(workflow.get("jobs"))
    _sonar_validate_job_scopes(workflow_path, workflow, jobs, issues)
    scanner_name, scanner_job = _sonar_find_scanner_job(jobs)
    _sonar_validate_scanner_job(root, workflow_path, scanner_name, scanner_job, jobs, issues)
    _sonar_validate_bridge_markers(workflow_path, jobs, issues)
    return sorted(issues, key=lambda issue: (issue.path, issue.message))


def validate_repository_automation(root: Path | str) -> list[ValidationIssue]:
    """Validate repository automation syntax and high-value security invariants."""

    root = Path(root).resolve()
    issues: list[ValidationIssue] = []
    issues.extend(validate_sonar_ci_configuration(root))

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
