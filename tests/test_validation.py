from __future__ import annotations

import shutil
from pathlib import Path

import yaml

from forgellm_governance.validation import (
    scan_for_secrets,
    validate_benchmark_file,
    validate_project,
    validate_repository_automation,
    validate_research_catalogs,
    validate_task_packet_file,
)

ROOT = Path(__file__).resolve().parents[1]


def test_valid_benchmark_example_passes() -> None:
    issues = validate_benchmark_file(ROOT / "examples/benchmarks/valid-example.json", root=ROOT)
    assert issues == []


def test_valid_status_rejects_failed_correctness() -> None:
    issues = validate_benchmark_file(
        ROOT / "tests/fixtures/invalid-valid-status-with-failed-correctness.json",
        root=ROOT,
    )
    assert any("requires correctness.status 'pass'" in issue.message for issue in issues)


def test_task_packet_phase_and_schema_pass() -> None:
    issues = validate_task_packet_file(ROOT / "examples/tasks/P0-T02.yaml", root=ROOT)
    assert issues == []


def test_research_catalogs_cross_reference() -> None:
    assert validate_research_catalogs(ROOT) == []


def test_duplicate_claim_id_is_rejected(tmp_path: Path) -> None:
    for directory in ("research", "schemas", "docs/architecture"):
        shutil.copytree(ROOT / directory, tmp_path / directory)
    claims_path = tmp_path / "research/claims.yaml"
    claims = yaml.safe_load(claims_path.read_text(encoding="utf-8"))
    claims["claims"].append(dict(claims["claims"][0]))
    claims_path.write_text(yaml.safe_dump(claims, sort_keys=False), encoding="utf-8")
    issues = validate_research_catalogs(tmp_path)
    assert any("duplicate id CLM-001" in issue.message for issue in issues)


def test_secret_scanner_detects_high_confidence_pattern(tmp_path: Path) -> None:
    (tmp_path / "leak.txt").write_text("token=ghp_" + "A" * 36 + "\n", encoding="utf-8")
    issues = scan_for_secrets(tmp_path)
    assert any("GitHub classic token" in issue.message for issue in issues)


def test_project_scaffold_is_valid() -> None:
    assert validate_project(ROOT) == []


def test_repository_automation_is_pinned_and_well_formed() -> None:
    assert validate_repository_automation(ROOT) == []


def test_dependency_review_opt_in_guard_is_required(tmp_path: Path) -> None:
    shutil.copytree(ROOT / "schemas", tmp_path / "schemas")
    shutil.copytree(ROOT / ".github", tmp_path / ".github")
    shutil.copy2(ROOT / "pyproject.toml", tmp_path / "pyproject.toml")
    shutil.copy2(ROOT / ".gitlab-ci.yml", tmp_path / ".gitlab-ci.yml")

    workflow = tmp_path / ".github/workflows/dependency-review.yml"
    text = workflow.read_text(encoding="utf-8")
    marker = "vars.FORGELLM_ENABLE_DEPENDENCY_REVIEW == 'true'"
    assert marker in text
    workflow.write_text(text.replace(marker, "false"), encoding="utf-8")

    issues = validate_repository_automation(tmp_path)
    assert any("FORGELLM_ENABLE_DEPENDENCY_REVIEW" in issue.message for issue in issues)
