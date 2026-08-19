from __future__ import annotations

import shutil
from pathlib import Path

import pytest
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


def test_private_feature_workflow_guard_is_required(tmp_path: Path) -> None:
    shutil.copytree(ROOT / "schemas", tmp_path / "schemas")
    shutil.copytree(ROOT / ".github", tmp_path / ".github")
    shutil.copy2(ROOT / "pyproject.toml", tmp_path / "pyproject.toml")
    shutil.copy2(ROOT / ".gitlab-ci.yml", tmp_path / ".gitlab-ci.yml")

    workflow = tmp_path / ".github/workflows/dependency-review.yml"
    text = workflow.read_text(encoding="utf-8")
    workflow.write_text(text.replace("vars.FORGELLM_ENABLE_DEPENDENCY_REVIEW == 'true' && ", ""), encoding="utf-8")

    issues = validate_repository_automation(tmp_path)
    assert any("FORGELLM_ENABLE_DEPENDENCY_REVIEW" in issue.message for issue in issues)


SONAR_TRUSTED_SETTINGS_PATH = "${{ runner.temp }}/forgellm-sonar.properties"
SONAR_TRUSTED_SCOPE_LINES = (
    "sonar.sources=.",
    "sonar.tests=tests",
    "sonar.exclusions=tests/**",
)
SONAR_TRUSTED_SETTINGS_BLOCK = """      - name: Create trusted Sonar settings
        shell: bash
        run: |
          umask 077
          printf '%s\\n' \\
            'sonar.sources=.' \\
            'sonar.tests=tests' \\
            'sonar.exclusions=tests/**' \\
            > "${RUNNER_TEMP}/forgellm-sonar.properties"
"""
SONAR_TRUSTED_MARKERS = (
    "sonar.host.url=https://sonarcloud.io",
    "sonar.organization=leon36000",
    "sonar.projectKey=leon36000_ForgeLLM",
    f"project.settings={SONAR_TRUSTED_SETTINGS_PATH}",
    "sonar.sca.enabled=false",
    "sonar.rust.clippy.enable=false",
    "sonar.qualitygate.wait=true",
    "sonar.qualitygate.timeout=300",
)
SONAR_PR_MARKERS = (
    "sonar.pullrequest.key=${{ inputs.pr_number }}",
    "sonar.pullrequest.branch=${{ inputs.head_ref }}",
    "sonar.pullrequest.base=main",
)


def _sonar_workflow_text() -> str:
    return """name: Sonar CI

on:
  push:
    branches: [main]
  workflow_dispatch:
    inputs:
      pr_number:
        description: Pull request number
        required: true
        type: number
      head_sha:
        description: Exact pull request head SHA
        required: true
        type: string
      head_ref:
        description: Pull request head branch
        required: true
        type: string

permissions:
  contents: read

jobs:
  main:
    if: vars.FORGELLM_SONAR_CI_ENABLED == 'true' && github.event_name == 'push' && github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Create trusted Sonar settings
        shell: bash
        run: |
          umask 077
          printf '%s\\n' \\
            'sonar.sources=.' \\
            'sonar.tests=tests' \\
            'sonar.exclusions=tests/**' \\
            > "${RUNNER_TEMP}/forgellm-sonar.properties"
      - name: Require SONAR_TOKEN
        shell: bash
        env:
          SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
        run: |
          if [[ -z "${SONAR_TOKEN}" ]]; then
            echo "::error::SONAR_TOKEN is not configured"
            exit 1
          fi
      - name: Checkout
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1
        with:
          persist-credentials: false
          fetch-depth: 0
      - name: Sonar scan
        uses: SonarSource/sonarqube-scan-action@22918119ff8e1ca75a623e15c8296b6ea4fbe28f
        env:
          SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
        with:
          scannerVersion: 8.1.0.6389
          args: >-
            -Dsonar.host.url=https://sonarcloud.io
            -Dsonar.organization=leon36000
            -Dsonar.projectKey=leon36000_ForgeLLM
            -Dproject.settings=${{ runner.temp }}/forgellm-sonar.properties
            -Dsonar.sca.enabled=false
            -Dsonar.rust.clippy.enable=false
            -Dsonar.qualitygate.wait=true
            -Dsonar.qualitygate.timeout=300
  pull_request:
    if: vars.FORGELLM_SONAR_CI_ENABLED == 'true' && github.event_name == 'workflow_dispatch' && github.ref == 'refs/heads/main' && github.actor == github.repository_owner
    runs-on: ubuntu-latest
    steps:
      - name: Create trusted Sonar settings
        shell: bash
        run: |
          umask 077
          printf '%s\\n' \\
            'sonar.sources=.' \\
            'sonar.tests=tests' \\
            'sonar.exclusions=tests/**' \\
            > "${RUNNER_TEMP}/forgellm-sonar.properties"
      - name: Require SONAR_TOKEN
        shell: bash
        env:
          SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
        run: |
          if [[ -z "${SONAR_TOKEN}" ]]; then
            echo "::error::SONAR_TOKEN is not configured"
            exit 1
          fi
      - name: Checkout exact PR head
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1
        with:
          ref: ${{ inputs.head_sha }}
          persist-credentials: false
          fetch-depth: 0
      - name: Sonar PR scan
        uses: SonarSource/sonarqube-scan-action@22918119ff8e1ca75a623e15c8296b6ea4fbe28f
        env:
          SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
        with:
          scannerVersion: 8.1.0.6389
          args: >-
            -Dsonar.host.url=https://sonarcloud.io
            -Dsonar.organization=leon36000
            -Dsonar.projectKey=leon36000_ForgeLLM
            -Dproject.settings=${{ runner.temp }}/forgellm-sonar.properties
            -Dsonar.sca.enabled=false
            -Dsonar.rust.clippy.enable=false
            -Dsonar.qualitygate.wait=true
            -Dsonar.qualitygate.timeout=300
            -Dsonar.pullrequest.key=${{ inputs.pr_number }}
            -Dsonar.pullrequest.branch=${{ inputs.head_ref }}
            -Dsonar.pullrequest.base=main
"""


def _sonar_automation_root(tmp_path: Path, *, include_sonar: bool = True) -> Path:
    root = tmp_path / "sonar-root"
    shutil.copytree(ROOT / "schemas", root / "schemas")
    shutil.copytree(ROOT / ".github", root / ".github")
    shutil.copy2(ROOT / "pyproject.toml", root / "pyproject.toml")
    shutil.copy2(ROOT / ".gitlab-ci.yml", root / ".gitlab-ci.yml")
    sonar_path = root / ".github/workflows/sonar.yml"
    sonar_path.unlink(missing_ok=True)
    if include_sonar:
        sonar_path.write_text(_sonar_workflow_text(), encoding="utf-8")
    return root


def _sonar_messages(root: Path) -> list[str]:
    return [issue.message for issue in validate_repository_automation(root)]


def test_sonar_workflow_is_valid_when_trusted_dispatch_scaffold_is_complete(tmp_path: Path) -> None:
    root = _sonar_automation_root(tmp_path)
    assert _sonar_messages(root) == []


def test_sonar_validation_is_inactive_when_workflow_is_absent(tmp_path: Path) -> None:
    root = _sonar_automation_root(tmp_path, include_sonar=False)
    assert _sonar_messages(root) == []


def test_sonar_pull_request_trigger_is_forbidden(tmp_path: Path) -> None:
    root = _sonar_automation_root(tmp_path)
    workflow = root / ".github/workflows/sonar.yml"
    text = workflow.read_text(encoding="utf-8")
    workflow.write_text(text.replace("  workflow_dispatch:\n", "  pull_request:\n    branches: [main]\n  workflow_dispatch:\n"), encoding="utf-8")
    assert any("pull_request" in message and "forbidden" in message.lower() for message in _sonar_messages(root))


@pytest.mark.parametrize(
    ("input_name", "block"),
    [
        (
            "pr_number",
            "      pr_number:\n        description: Pull request number\n        required: true\n        type: number\n",
        ),
        (
            "head_sha",
            "      head_sha:\n        description: Exact pull request head SHA\n        required: true\n        type: string\n",
        ),
        (
            "head_ref",
            "      head_ref:\n        description: Pull request head branch\n        required: true\n        type: string\n",
        ),
    ],
)
def test_sonar_dispatch_inputs_are_required(tmp_path: Path, input_name: str, block: str) -> None:
    root = _sonar_automation_root(tmp_path)
    workflow = root / ".github/workflows/sonar.yml"
    text = workflow.read_text(encoding="utf-8")
    workflow.write_text(text.replace(block, ""), encoding="utf-8")
    assert any(input_name in message for message in _sonar_messages(root))


def test_sonar_dispatch_requires_repository_owner_actor(tmp_path: Path) -> None:
    root = _sonar_automation_root(tmp_path)
    workflow = root / ".github/workflows/sonar.yml"
    text = workflow.read_text(encoding="utf-8")
    workflow.write_text(text.replace(" && github.actor == github.repository_owner", ""), encoding="utf-8")
    assert any("repository_owner" in message for message in _sonar_messages(root))


def test_sonar_dispatch_requires_main_workflow_ref(tmp_path: Path) -> None:
    root = _sonar_automation_root(tmp_path)
    workflow = root / ".github/workflows/sonar.yml"
    text = workflow.read_text(encoding="utf-8")
    old = "github.event_name == 'workflow_dispatch' && github.ref == 'refs/heads/main' && github.actor == github.repository_owner"
    new = "github.event_name == 'workflow_dispatch' && github.actor == github.repository_owner"
    workflow.write_text(text.replace(old, new), encoding="utf-8")
    assert any("refs/heads/main" in message and "dispatch" in message.lower() for message in _sonar_messages(root))


@pytest.mark.parametrize("required_marker", ("github.event_name == 'push'", "github.ref == 'refs/heads/main'"))
def test_sonar_main_job_requires_push_main_guard(tmp_path: Path, required_marker: str) -> None:
    root = _sonar_automation_root(tmp_path)
    workflow = root / ".github/workflows/sonar.yml"
    text = workflow.read_text(encoding="utf-8")
    workflow.write_text(text.replace(f" && {required_marker}", "", 1), encoding="utf-8")
    assert any(required_marker in message for message in _sonar_messages(root))


def test_sonar_enable_guard_is_required_on_both_jobs(tmp_path: Path) -> None:
    root = _sonar_automation_root(tmp_path)
    workflow = root / ".github/workflows/sonar.yml"
    text = workflow.read_text(encoding="utf-8")
    workflow.write_text(text.replace("vars.FORGELLM_SONAR_CI_ENABLED == 'true' && ", ""), encoding="utf-8")
    messages = _sonar_messages(root)
    assert sum("FORGELLM_SONAR_CI_ENABLED" in message for message in messages) >= 2


def test_sonar_pr_checkout_requires_exact_input_head_sha(tmp_path: Path) -> None:
    root = _sonar_automation_root(tmp_path)
    workflow = root / ".github/workflows/sonar.yml"
    text = workflow.read_text(encoding="utf-8")
    workflow.write_text(text.replace("          ref: ${{ inputs.head_sha }}", "          ref: main"), encoding="utf-8")
    assert any("inputs.head_sha" in message for message in _sonar_messages(root))


@pytest.mark.parametrize(
    ("old", "new", "expected"),
    [
        ("contents: read", "contents: write", "contents: read"),
        ("persist-credentials: false", "persist-credentials: true", "persist-credentials"),
        ("fetch-depth: 0", "fetch-depth: 1", "fetch-depth"),
        ("scannerVersion: 8.1.0.6389", "scannerVersion: ''", "scannerVersion"),
    ],
)
def test_sonar_workflow_security_fields_are_required(tmp_path: Path, old: str, new: str, expected: str) -> None:
    root = _sonar_automation_root(tmp_path)
    workflow = root / ".github/workflows/sonar.yml"
    text = workflow.read_text(encoding="utf-8")
    workflow.write_text(text.replace(old, new), encoding="utf-8")
    assert any(expected in message for message in _sonar_messages(root))


@pytest.mark.parametrize("marker", SONAR_TRUSTED_MARKERS)
def test_sonar_trusted_scanner_markers_are_required(tmp_path: Path, marker: str) -> None:
    root = _sonar_automation_root(tmp_path)
    workflow = root / ".github/workflows/sonar.yml"
    text = workflow.read_text(encoding="utf-8")
    workflow.write_text(text.replace(f"            -D{marker}\n", ""), encoding="utf-8")
    assert any(marker in message for message in _sonar_messages(root))


@pytest.mark.parametrize("marker", SONAR_PR_MARKERS)
def test_sonar_pr_parameters_are_required(tmp_path: Path, marker: str) -> None:
    root = _sonar_automation_root(tmp_path)
    workflow = root / ".github/workflows/sonar.yml"
    text = workflow.read_text(encoding="utf-8")
    workflow.write_text(text.replace(f"            -D{marker}\n", ""), encoding="utf-8")
    assert any(marker in message for message in _sonar_messages(root))


def test_sonar_trusted_settings_initializer_is_required(tmp_path: Path) -> None:
    root = _sonar_automation_root(tmp_path)
    workflow = root / ".github/workflows/sonar.yml"
    text = workflow.read_text(encoding="utf-8")
    workflow.write_text(text.replace(SONAR_TRUSTED_SETTINGS_BLOCK, ""), encoding="utf-8")
    assert any("trusted Sonar settings" in message for message in _sonar_messages(root))


@pytest.mark.parametrize(
    ("old", "new"),
    [
        ("sonar.sources=.", "sonar.sources=src"),
        ("sonar.tests=tests", "sonar.tests=src"),
        ("sonar.exclusions=tests/**", "sonar.exclusions=src/**"),
    ],
)
def test_sonar_trusted_settings_scope_is_fixed(tmp_path: Path, old: str, new: str) -> None:
    root = _sonar_automation_root(tmp_path)
    workflow = root / ".github/workflows/sonar.yml"
    text = workflow.read_text(encoding="utf-8")
    workflow.write_text(text.replace(old, new), encoding="utf-8")
    assert any(old in message for message in _sonar_messages(root))


def test_sonar_trusted_settings_must_precede_checkout(tmp_path: Path) -> None:
    root = _sonar_automation_root(tmp_path)
    workflow = root / ".github/workflows/sonar.yml"
    text = workflow.read_text(encoding="utf-8")
    text = text.replace(SONAR_TRUSTED_SETTINGS_BLOCK, "", 1)
    text = text.replace("      - name: Sonar scan\n", SONAR_TRUSTED_SETTINGS_BLOCK + "      - name: Sonar scan\n", 1)
    workflow.write_text(text, encoding="utf-8")
    assert any("before checkout" in message.lower() for message in _sonar_messages(root))


def test_sonar_trusted_settings_step_must_not_receive_token(tmp_path: Path) -> None:
    root = _sonar_automation_root(tmp_path)
    workflow = root / ".github/workflows/sonar.yml"
    text = workflow.read_text(encoding="utf-8")
    old = "        shell: bash\n        run: |\n          umask 077\n"
    new = "        shell: bash\n        env:\n          SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}\n        run: |\n          umask 077\n"
    workflow.write_text(text.replace(old, new), encoding="utf-8")
    assert any("trusted Sonar settings" in message and "SONAR_TOKEN" in message for message in _sonar_messages(root))


def test_sonar_scanner_requires_exact_secret_reference(tmp_path: Path) -> None:
    root = _sonar_automation_root(tmp_path)
    workflow = root / ".github/workflows/sonar.yml"
    text = workflow.read_text(encoding="utf-8")
    workflow.write_text(text.replace("secrets.SONAR_TOKEN", "secrets.OTHER_TOKEN"), encoding="utf-8")
    assert any("SONAR_TOKEN" in message for message in _sonar_messages(root))


def test_sonar_workflow_run_trigger_is_forbidden(tmp_path: Path) -> None:
    root = _sonar_automation_root(tmp_path)
    workflow = root / ".github/workflows/sonar.yml"
    text = workflow.read_text(encoding="utf-8")
    workflow.write_text(text.replace("  workflow_dispatch:\n", "  workflow_run:\n  workflow_dispatch:\n"), encoding="utf-8")
    assert any("workflow_run" in message for message in _sonar_messages(root))


def test_sonar_token_bearing_job_must_not_execute_project_code(tmp_path: Path) -> None:
    root = _sonar_automation_root(tmp_path)
    workflow = root / ".github/workflows/sonar.yml"
    text = workflow.read_text(encoding="utf-8")
    text = text.replace(
        "      - name: Checkout exact PR head\n",
        "      - name: Unsafe build\n        run: cargo clippy --all-targets\n      - name: Checkout exact PR head\n",
    )
    workflow.write_text(text, encoding="utf-8")
    assert any("token-bearing" in message.lower() and "cargo" in message.lower() for message in _sonar_messages(root))


def _copy_simulation_root(tmp_path: Path) -> Path:
    root = tmp_path / "simulation-root"
    (root / "schemas").mkdir(parents=True)
    (root / "examples" / "simulations").mkdir(parents=True)
    (root / "artifacts" / "simulations").mkdir(parents=True)
    for name in ("topology.schema.json", "component-profile.schema.json", "placement-result.schema.json"):
        shutil.copy2(ROOT / "schemas" / name, root / "schemas" / name)
    for name in ("synthetic-cache-draft-topology.json", "synthetic-cache-draft-components.json"):
        shutil.copy2(
            ROOT / "examples" / "simulations" / name,
            root / "examples" / "simulations" / name,
        )
    return root


def test_cli_validate_topology_dispatches(monkeypatch, capsys) -> None:
    from forgellm_governance.cli import main

    monkeypatch.setattr(
        "sys.argv",
        [
            "forgellm-governance",
            "validate-topology",
            str(ROOT / "examples/simulations/synthetic-cache-draft-topology.json"),
            "--root",
            str(ROOT),
        ],
    )
    assert main() == 0
    assert "OK:" in capsys.readouterr().out


def test_cli_validate_components_dispatches(monkeypatch, capsys) -> None:
    from forgellm_governance.cli import main

    monkeypatch.setattr(
        "sys.argv",
        [
            "forgellm-governance",
            "validate-components",
            str(ROOT / "examples/simulations/synthetic-cache-draft-components.json"),
            "--root",
            str(ROOT),
        ],
    )
    assert main() == 0
    assert "OK:" in capsys.readouterr().out


def test_cli_simulate_placement_dispatches(tmp_path: Path, monkeypatch, capsys) -> None:
    from forgellm_governance.cli import main

    root = _copy_simulation_root(tmp_path)
    output = root / "artifacts" / "simulations" / "result.json"
    monkeypatch.setattr(
        "sys.argv",
        [
            "forgellm-governance",
            "simulate-placement",
            "--root",
            str(root),
            "--topology",
            "examples/simulations/synthetic-cache-draft-topology.json",
            "--components",
            "examples/simulations/synthetic-cache-draft-components.json",
            "--output",
            "artifacts/simulations/result.json",
        ],
    )
    assert main() == 0
    assert capsys.readouterr().out.strip() == str(output.resolve())
    assert output.exists()
