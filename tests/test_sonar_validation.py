from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
import yaml

from forgellm_governance.validation import validate_sonar_ci_configuration

_SCANNER_ACTION = "SonarSource/sonarqube-scan-action@22918119ff8e1ca75a623e15c8296b6ea4fbe28f"
_CHECKOUT_ACTION = "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1"
_UPLOAD_ARTIFACT_ACTION = "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a"
_DOWNLOAD_ARTIFACT_ACTION = "actions/download-artifact@3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c"
_ARTIFACT_NAME = "forgellm-sonar-input"
_ARTIFACT_PATH = ".sonar-input"
_TOKEN_KEY = "SONAR_" + "TOKEN"
_TOKEN_REFERENCE = "${{ secrets." + _TOKEN_KEY + " }}"


def _accepted_adr() -> str:
    return """# ADR-0004: Sonar analysis method

- **Status:** accepted

## Decision

Select exactly **`ci_based_only`** for ForgeLLM SonarQube Cloud analysis.
"""


def _scanner_arguments() -> str:
    return " ".join(
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


def _safe_workflow() -> dict[str, Any]:
    return {
        "name": "Prepared inactive SonarQube Cloud scanner",
        "on": {
            "push": {"branches": ["main"]},
            "workflow_dispatch": {},
        },
        "jobs": {
            "producer": {
                "permissions": {"contents": "read"},
                "runs-on": "ubuntu-24.04",
                "timeout-minutes": 10,
                "steps": [
                    {
                        "name": "Checkout trusted protected source",
                        "uses": _CHECKOUT_ACTION,
                        "with": {
                            "fetch-depth": 1,
                            "persist-credentials": False,
                            "repository": "${{ github.repository }}",
                            "ref": "${{ github.sha }}",
                        },
                    },
                    {
                        "name": "Prepare source and reports without privileged credentials",
                        "run": (
                            "set -euo pipefail\n"
                            "mkdir -p .sonar-input/source .sonar-input/reports\n"
                            "cp -a src .sonar-input/source/src\n"
                            "cp -a crates .sonar-input/source/crates\n"
                            "cargo clippy --workspace --all-targets --locked --message-format=json "
                            "-- -D warnings > .sonar-input/reports/clippy.json\n"
                        ),
                    },
                    {
                        "name": "Publish secretless source and reports",
                        "uses": _UPLOAD_ARTIFACT_ACTION,
                        "with": {
                            "name": _ARTIFACT_NAME,
                            "path": _ARTIFACT_PATH,
                            "if-no-files-found": "error",
                            "include-hidden-files": True,
                            "retention-days": 1,
                        },
                    },
                ],
            },
            "scanner": {
                "permissions": {"contents": "read"},
                "needs": ["producer"],
                "if": (
                    "vars.FORGELLM_ENABLE_SONAR_CI == 'true' && "
                    "vars.FORGELLM_AUTOMATIC_ANALYSIS_DISABLED == 'true' && "
                    "github.ref == 'refs/heads/main'"
                ),
                "runs-on": "ubuntu-24.04",
                "timeout-minutes": 20,
                "steps": [
                    {
                        "name": "Download secretless source and reports",
                        "uses": _DOWNLOAD_ARTIFACT_ACTION,
                        "with": {"name": _ARTIFACT_NAME, "path": _ARTIFACT_PATH},
                    },
                    {
                        "name": "Validate bounded source and report data",
                        "run": (
                            "set -euo pipefail\n"
                            "test -d .sonar-input/source\n"
                            "test -f .sonar-input/reports/clippy.json\n"
                            "if find .sonar-input -type l -print -quit | grep -q .; then\n"
                            "  echo 'symlinks are forbidden in the downloaded Sonar input' >&2\n"
                            "  exit 1\n"
                            "fi\n"
                        ),
                    },
                    {
                        "name": "Run reviewed immutable scanner",
                        "uses": _SCANNER_ACTION,
                        "env": {_TOKEN_KEY: _TOKEN_REFERENCE},
                        "with": {
                            "projectBaseDir": ".",
                            "scannerVersion": "8.1.0.6389",
                            "skipSignatureVerification": False,
                            "args": _scanner_arguments(),
                        },
                    },
                ],
            },
        },
    }


def _safe_properties() -> str:
    return """sonar.projectKey=leon36000_ForgeLLM
sonar.sourceEncoding=UTF-8
sonar.sources=.sonar-input/source
sonar.rust.clippy.enable=false
sonar.rust.clippyReport.reportPaths=.sonar-input/reports/clippy.json
"""


def _write_root(
    tmp_path: Path,
    *,
    workflow: dict[str, Any] | None = None,
    properties: str | None = None,
    include_workflow: bool = True,
    include_properties: bool = True,
) -> Path:
    root = tmp_path / "sonar-root"
    (root / "docs/architecture").mkdir(parents=True)
    (root / ".github/workflows").mkdir(parents=True)
    (root / "docs/architecture/ADR-0004-sonarqube-analysis-method.md").write_text(
        _accepted_adr(),
        encoding="utf-8",
    )
    if include_workflow:
        (root / ".github/workflows/sonar.yml").write_text(
            yaml.safe_dump(workflow or _safe_workflow(), sort_keys=False),
            encoding="utf-8",
        )
    if include_properties:
        (root / "sonar-project.properties").write_text(properties or _safe_properties(), encoding="utf-8")
    return root


def _codes(root: Path) -> set[str]:
    codes: set[str] = set()
    for issue in validate_sonar_ci_configuration(root):
        if issue.message.startswith("[") and "]" in issue.message:
            codes.add(issue.message[1 : issue.message.index("]")])
    return codes


def _assert_code(root: Path, code: str) -> None:
    issues = validate_sonar_ci_configuration(root)
    assert code in _codes(root), [issue.render() for issue in issues]


def _scanner_job(workflow: dict[str, Any]) -> dict[str, Any]:
    return workflow["jobs"]["scanner"]


def _scanner_step(workflow: dict[str, Any]) -> dict[str, Any]:
    return _scanner_job(workflow)["steps"][-1]


def test_sonar_validation_is_inert_before_candidate_configuration(tmp_path: Path) -> None:
    root = _write_root(tmp_path, include_workflow=False, include_properties=False)
    assert validate_sonar_ci_configuration(root) == []


def test_safe_prepared_inactive_configuration_passes(tmp_path: Path) -> None:
    root = _write_root(tmp_path)
    assert validate_sonar_ci_configuration(root) == []


@pytest.mark.parametrize("mutation", ("missing-upload", "missing-download", "mutable-download", "wrong-path"))
def test_secretless_source_report_transfer_is_bounded(tmp_path: Path, mutation: str) -> None:
    workflow = _safe_workflow()
    if mutation == "missing-upload":
        workflow["jobs"]["producer"]["steps"].pop()
    else:
        download = workflow["jobs"]["scanner"]["steps"][0]
        if mutation == "missing-download":
            workflow["jobs"]["scanner"]["steps"].pop(0)
        elif mutation == "mutable-download":
            download["uses"] = "actions/download-artifact@v8"
        else:
            download["with"]["path"] = "untrusted-input"
    root = _write_root(tmp_path, workflow=workflow)
    _assert_code(root, "SONAR_ARTIFACT_BOUNDARY")


def test_scanner_input_validation_must_reject_symlinks(tmp_path: Path) -> None:
    workflow = _safe_workflow()
    validation = _scanner_job(workflow)["steps"][1]
    validation["run"] = validation["run"].split("if find .sonar-input", maxsplit=1)[0]
    root = _write_root(tmp_path, workflow=workflow)
    _assert_code(root, "SONAR_ARTIFACT_BOUNDARY")


@pytest.mark.parametrize("input_name", ("repository", "ref"))
def test_producer_checkout_must_bind_the_trusted_repository_and_event_sha(
    tmp_path: Path,
    input_name: str,
) -> None:
    workflow = _safe_workflow()
    checkout = workflow["jobs"]["producer"]["steps"][0]
    checkout["with"].pop(input_name)
    root = _write_root(tmp_path, workflow=workflow)
    _assert_code(root, "SONAR_ARTIFACT_BOUNDARY")


def test_permissions_must_not_be_declared_at_workflow_scope(tmp_path: Path) -> None:
    workflow = _safe_workflow()
    workflow["permissions"] = {"contents": "read"}
    root = _write_root(tmp_path, workflow=workflow)
    _assert_code(root, "SONAR_ACTIVATION_GATE")


def test_every_sonar_job_requires_read_only_permissions(tmp_path: Path) -> None:
    workflow = _safe_workflow()
    del workflow["jobs"]["producer"]["permissions"]
    root = _write_root(tmp_path, workflow=workflow)
    _assert_code(root, "SONAR_ACTIVATION_GATE")


@pytest.mark.parametrize("job_name", ("producer", "scanner"))
def test_sonar_job_permissions_cannot_widen(tmp_path: Path, job_name: str) -> None:
    workflow = _safe_workflow()
    workflow["jobs"][job_name]["permissions"] = {"contents": "write"}
    root = _write_root(tmp_path, workflow=workflow)
    _assert_code(root, "SONAR_ACTIVATION_GATE")


@pytest.mark.parametrize(
    ("include_workflow", "include_properties"),
    ((True, False), (False, True)),
)
def test_workflow_and_properties_must_be_prepared_together(
    tmp_path: Path,
    include_workflow: bool,
    include_properties: bool,
) -> None:
    root = _write_root(
        tmp_path,
        include_workflow=include_workflow,
        include_properties=include_properties,
    )
    _assert_code(root, "SONAR_CONFIG_PAIR")


def test_automatic_and_ci_analysis_configuration_cannot_overlap(tmp_path: Path) -> None:
    root = _write_root(tmp_path)
    (root / ".sonarcloud.properties").write_text("sonar.exclusions=**/ignored.py\n", encoding="utf-8")
    _assert_code(root, "SONAR_METHOD_OVERLAP")


def test_activation_requires_the_disabled_automatic_analysis_gate(tmp_path: Path) -> None:
    workflow = _safe_workflow()
    scanner = _scanner_job(workflow)
    scanner["if"] = scanner["if"].replace("vars.FORGELLM_AUTOMATIC_ANALYSIS_DISABLED == 'true' && ", "")
    root = _write_root(tmp_path, workflow=workflow)
    _assert_code(root, "SONAR_ACTIVATION_GATE")


@pytest.mark.parametrize("event_name", ("pull_request", "pull_request_target", "workflow_run"))
def test_privileged_or_pull_request_events_are_forbidden(tmp_path: Path, event_name: str) -> None:
    workflow = _safe_workflow()
    workflow["on"][event_name] = {}
    root = _write_root(tmp_path, workflow=workflow)
    _assert_code(root, "SONAR_FORBIDDEN_EVENT")


@pytest.mark.parametrize("scope", ("workflow", "job", "container", "service"))
def test_token_is_rejected_outside_the_final_scanner_step(tmp_path: Path, scope: str) -> None:
    workflow = _safe_workflow()
    scanner = _scanner_job(workflow)
    if scope == "workflow":
        workflow["env"] = {_TOKEN_KEY: _TOKEN_REFERENCE}
    elif scope == "job":
        scanner["env"] = {_TOKEN_KEY: _TOKEN_REFERENCE}
    elif scope == "container":
        scanner["container"] = {"image": "ubuntu:24.04", "env": {_TOKEN_KEY: _TOKEN_REFERENCE}}
    else:
        scanner["services"] = {
            "helper": {"image": "ubuntu:24.04", "env": {_TOKEN_KEY: _TOKEN_REFERENCE}}
        }
    root = _write_root(tmp_path, workflow=workflow)
    _assert_code(root, "SONAR_TOKEN_SCOPE")


@pytest.mark.parametrize("secret_mapping", ({_TOKEN_KEY: _TOKEN_REFERENCE}, "inherit"))
def test_reusable_workflow_secret_forwarding_is_forbidden(
    tmp_path: Path,
    secret_mapping: dict[str, str] | str,
) -> None:
    workflow = _safe_workflow()
    workflow["jobs"]["forwarded"] = {
        "uses": "forgellm/reusable/.github/workflows/scan.yml@" + "a" * 40,
        "secrets": secret_mapping,
    }
    root = _write_root(tmp_path, workflow=workflow)
    _assert_code(root, "SONAR_REUSABLE_SECRET")


@pytest.mark.parametrize("channel", ("outputs", "state"))
def test_token_cannot_propagate_through_outputs_or_state(tmp_path: Path, channel: str) -> None:
    workflow = _safe_workflow()
    scanner = _scanner_job(workflow)
    if channel == "outputs":
        scanner["outputs"] = {"credential": _TOKEN_REFERENCE}
    else:
        scanner["steps"].insert(
            -1,
            {
                "name": "Propagate state",
                "env": {_TOKEN_KEY: _TOKEN_REFERENCE},
                "run": "printf '%s\\n' \"$" + _TOKEN_KEY + "\" >> \"$GITHUB_STATE\"",
            },
        )
    root = _write_root(tmp_path, workflow=workflow)
    _assert_code(root, "SONAR_TOKEN_PROPAGATION")


@pytest.mark.parametrize("using", ("composite", "node20"))
def test_local_or_composite_action_cannot_receive_the_token(tmp_path: Path, using: str) -> None:
    workflow = _safe_workflow()
    scanner_step = _scanner_step(workflow)
    scanner_step["uses"] = "./.github/actions/unreviewed-scanner"
    root = _write_root(tmp_path, workflow=workflow)
    action_dir = root / ".github/actions/unreviewed-scanner"
    action_dir.mkdir(parents=True)
    runs: dict[str, Any] = {"using": using}
    if using == "composite":
        runs["steps"] = [{"shell": "bash", "run": "printf '%s\\n' unreviewed"}]
    else:
        runs.update({"pre": "pre.js", "main": "main.js", "post": "post.js"})
    (action_dir / "action.yml").write_text(
        yaml.safe_dump({"name": "Unreviewed scanner", "runs": runs}, sort_keys=False),
        encoding="utf-8",
    )
    expected = "SONAR_LOCAL_ACTION" if using == "composite" else "SONAR_SCANNER_HOOKS"
    _assert_code(root, expected)


def test_repository_local_script_cannot_be_the_token_bearing_scanner(tmp_path: Path) -> None:
    workflow = _safe_workflow()
    scanner = _scanner_job(workflow)
    scanner["steps"][-1] = {
        "name": "Run repository scanner wrapper",
        "env": {_TOKEN_KEY: _TOKEN_REFERENCE},
        "run": "./scripts/run-sonar.sh",
    }
    root = _write_root(tmp_path, workflow=workflow)
    _assert_code(root, "SONAR_LOCAL_EXECUTION")


def test_scanner_job_cannot_checkout_contributor_source(tmp_path: Path) -> None:
    workflow = _safe_workflow()
    _scanner_job(workflow)["steps"].insert(
        0,
        {
            "name": "Checkout contributor source",
            "uses": _CHECKOUT_ACTION,
            "with": {"persist-credentials": False},
        },
    )
    root = _write_root(tmp_path, workflow=workflow)
    _assert_code(root, "SONAR_SCANNER_CHECKOUT")


def test_scanner_action_must_be_the_final_step_with_no_post_processing(tmp_path: Path) -> None:
    workflow = _safe_workflow()
    _scanner_job(workflow)["steps"].append(
        {"name": "Post-process result", "if": "always()", "run": "printf '%s\\n' done"}
    )
    root = _write_root(tmp_path, workflow=workflow)
    _assert_code(root, "SONAR_SCANNER_FINAL_STEP")


def test_token_bearing_step_cannot_execute_contributor_commands(tmp_path: Path) -> None:
    workflow = _safe_workflow()
    _scanner_job(workflow)["steps"][-1] = {
        "name": "Unsafe token-bearing command",
        "env": {_TOKEN_KEY: _TOKEN_REFERENCE},
        "run": "cargo test --workspace",
    }
    root = _write_root(tmp_path, workflow=workflow)
    _assert_code(root, "SONAR_TOKEN_EXECUTION")


@pytest.mark.parametrize("location", ("properties", "arguments"))
def test_automatic_clippy_must_remain_disabled(tmp_path: Path, location: str) -> None:
    workflow = _safe_workflow()
    properties = _safe_properties()
    if location == "properties":
        properties = properties.replace("sonar.rust.clippy.enable=false", "sonar.rust.clippy.enable=true")
    else:
        scanner_step = _scanner_step(workflow)
        scanner_step["with"]["args"] = scanner_step["with"]["args"].replace(
            "-Dsonar.rust.clippy.enable=false",
            "-Dsonar.rust.clippy.enable=true",
        )
    root = _write_root(tmp_path, workflow=workflow, properties=properties)
    _assert_code(root, "SONAR_CLIPPY")


@pytest.mark.parametrize(
    ("trusted", "untrusted"),
    (
        ("https://sonarcloud.io", "${{ inputs.sonar_host }}"),
        ("${{ vars.SONAR_ORGANIZATION }}", "${{ inputs.organization }}"),
        ("leon36000_ForgeLLM", "${{ github.event.pull_request.title }}"),
        (".sonar-input/reports/clippy.json", "../../reports/*.json"),
    ),
)
def test_scanner_configuration_and_report_paths_are_trusted_and_fixed(
    tmp_path: Path,
    trusted: str,
    untrusted: str,
) -> None:
    workflow = _safe_workflow()
    scanner_step = _scanner_step(workflow)
    scanner_step["with"]["args"] = scanner_step["with"]["args"].replace(trusted, untrusted)
    root = _write_root(tmp_path, workflow=workflow)
    _assert_code(root, "SONAR_TRUSTED_CONFIG")


def test_current_increment_rejects_unbounded_bridge_inputs(tmp_path: Path) -> None:
    workflow = _safe_workflow()
    workflow["on"]["workflow_dispatch"] = {
        "inputs": {
            "artifact_url": {
                "description": "Unbounded contributor-controlled artifact",
                "required": True,
                "type": "string",
            }
        }
    }
    _scanner_job(workflow)["steps"].insert(
        0,
        {
            "name": "Extract arbitrary bridge input",
            "run": "curl -L \"${{ inputs.artifact_url }}\" | tar -xz",
        },
    )
    root = _write_root(tmp_path, workflow=workflow)
    _assert_code(root, "SONAR_BRIDGE_BOUNDS")


@pytest.mark.parametrize("mutation", ("mutable-action", "scanner-version", "signature"))
def test_scanner_action_and_binary_provenance_are_separately_pinned(
    tmp_path: Path,
    mutation: str,
) -> None:
    workflow = _safe_workflow()
    scanner_step = _scanner_step(workflow)
    if mutation == "mutable-action":
        scanner_step["uses"] = "SonarSource/sonarqube-scan-action@v8.2.1"
    elif mutation == "scanner-version":
        scanner_step["with"].pop("scannerVersion")
    else:
        scanner_step["with"]["skipSignatureVerification"] = True
    root = _write_root(tmp_path, workflow=workflow)
    _assert_code(root, "SONAR_SCANNER_PROVENANCE")


@pytest.mark.parametrize("scope", ("step", "job"))
def test_scanner_failure_cannot_be_masked_as_success(tmp_path: Path, scope: str) -> None:
    workflow = _safe_workflow()
    if scope == "step":
        _scanner_step(workflow)["continue-on-error"] = True
    else:
        _scanner_job(workflow)["continue-on-error"] = True
    root = _write_root(tmp_path, workflow=workflow)
    _assert_code(root, "SONAR_RESULT_MASKING")


def test_token_reference_must_be_the_exact_github_secret_expression(tmp_path: Path) -> None:
    workflow = _safe_workflow()
    _scanner_step(workflow)["env"][_TOKEN_KEY] = "${{ vars." + _TOKEN_KEY + " }}"
    root = _write_root(tmp_path, workflow=workflow)
    _assert_code(root, "SONAR_TOKEN_REFERENCE")


def test_unaccepted_method_cannot_enable_ci_candidate(tmp_path: Path) -> None:
    root = _write_root(tmp_path)
    adr = root / "docs/architecture/ADR-0004-sonarqube-analysis-method.md"
    adr.write_text(_accepted_adr().replace("ci_based_only", "automatic_only"), encoding="utf-8")
    _assert_code(root, "SONAR_METHOD_DECISION")


def test_decision_section_does_not_consume_following_heading(tmp_path: Path) -> None:
    root = _write_root(tmp_path)
    adr = root / "docs/architecture/ADR-0004-sonarqube-analysis-method.md"
    adr.write_text(
        _accepted_adr().replace("ci_based_only", "automatic_only")
        + "\n## Historical note\nSelect exactly **`ci_based_only`** in a later section.\n",
        encoding="utf-8",
    )
    _assert_code(root, "SONAR_METHOD_DECISION")


@pytest.mark.parametrize("terminal_newline", ("", "\n"))
def test_decision_section_accepts_choice_at_absolute_end(
    tmp_path: Path,
    terminal_newline: str,
) -> None:
    root = _write_root(tmp_path)
    adr = root / "docs/architecture/ADR-0004-sonarqube-analysis-method.md"
    adr.write_text(_accepted_adr().rstrip("\n") + terminal_newline, encoding="utf-8")
    assert validate_sonar_ci_configuration(root) == []


def test_fixture_mutations_do_not_alias_the_safe_workflow() -> None:
    first = _safe_workflow()
    second = deepcopy(first)
    _scanner_job(second)["steps"].clear()
    assert len(_scanner_job(first)["steps"]) == 3


def test_issue_helper_uses_stable_codes(tmp_path: Path) -> None:
    root = _write_root(tmp_path, include_properties=False)
    issues = validate_sonar_ci_configuration(root)
    assert issues
    assert all(issue.message.startswith("[") and "]" in issue.message for issue in issues)
