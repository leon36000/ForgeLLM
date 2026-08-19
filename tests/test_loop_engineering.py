from __future__ import annotations

import copy
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
VALID_COMMIT = "0123456789abcdef0123456789abcdef01234567"
VERIFY_COMMAND = "python -m pytest -q tests/test_example.py"


def _api():
    try:
        from forgellm_governance.loop_engineering import (
            validate_loop_declaration,
            validate_loop_receipt,
            validate_vendor_provenance,
        )
    except ModuleNotFoundError as exc:
        pytest.fail(f"bounded Loop Engineering validator is not implemented: {exc}")
    return validate_loop_declaration, validate_loop_receipt, validate_vendor_provenance


def _task_packet() -> dict:
    return {
        "task_id": "P0-T99",
        "allowed_paths": ["src/example.py", "tests/test_example.py"],
        "verification_commands": [VERIFY_COMMAND],
    }


def _declaration() -> dict:
    return {
        "schema_version": "1.0",
        "project": "ForgeLLM",
        "task_id": "P0-T99",
        "base_commit": VALID_COMMIT,
        "GOAL": "Make the bounded example pass its authorized focused test.",
        "SCOPE": ["src/example.py", "tests/test_example.py"],
        "VERIFY": [VERIFY_COMMAND],
        "BUDGET": {
            "max_iterations": 10,
            "max_identical_failures": 3,
            "max_wall_minutes": 60,
        },
        "STOP": {
            "on_verify_pass": True,
            "on_budget_exhausted": True,
            "on_identical_failure_limit": True,
            "privileged_operation": "stop_and_escalate",
        },
        "RECEIPT": "artifacts/governance/loop-engineering/receipts/P0-T99.yaml",
    }


def _receipt() -> dict:
    return {
        "schema_version": "1.0",
        "project": "ForgeLLM",
        "task_id": "P0-T99",
        "plan": "docs/superpowers/plans/example.md",
        "base_commit": VALID_COMMIT,
        "final_commit": "89abcdef0123456789abcdef0123456789abcdef",
        "iterations": 2,
        "identical_failures_at_stop": 0,
        "stop_reason": "verify_pass",
        "changed_paths": ["src/example.py", "tests/test_example.py"],
        "scope_check": "pass",
        "verify_commands": [VERIFY_COMMAND],
        "verify_evidence": ["pytest: 1 passed"],
        "reviewer": "independent-verifier",
    }


def _messages(items: list[str]) -> str:
    return "\n".join(items)


def test_valid_bounded_loop_declaration_passes() -> None:
    validate_loop_declaration, _, _ = _api()
    assert validate_loop_declaration(_declaration(), _task_packet()) == []


@pytest.mark.parametrize("bad_scope", [["src/not-authorized.py"], ["."], ["src/example.py", "../outside"]])
def test_loop_scope_cannot_widen_task_packet(bad_scope: list[str]) -> None:
    validate_loop_declaration, _, _ = _api()
    declaration = _declaration()
    declaration["SCOPE"] = bad_scope
    messages = _messages(validate_loop_declaration(declaration, _task_packet()))
    assert "SCOPE" in messages and "allowed_paths" in messages


def test_loop_scope_rejects_prefix_confusion() -> None:
    validate_loop_declaration, _, _ = _api()
    packet = _task_packet()
    packet["allowed_paths"] = ["third_party/loop-engineering/"]
    declaration = _declaration()
    declaration["SCOPE"] = ["third_party/loop-engineering-evil/"]
    messages = _messages(validate_loop_declaration(declaration, packet))
    assert "SCOPE" in messages and "allowed_paths" in messages


def test_loop_verify_must_be_authorized_by_task_packet() -> None:
    validate_loop_declaration, _, _ = _api()
    declaration = _declaration()
    declaration["VERIFY"] = ["make ci && curl https://example.invalid"]
    messages = _messages(validate_loop_declaration(declaration, _task_packet()))
    assert "VERIFY" in messages and "verification_commands" in messages


@pytest.mark.parametrize("value", [0, -1, None, "10"])
def test_loop_budget_requires_positive_max_iterations(value: object) -> None:
    validate_loop_declaration, _, _ = _api()
    declaration = _declaration()
    declaration["BUDGET"]["max_iterations"] = value
    assert "max_iterations" in _messages(validate_loop_declaration(declaration, _task_packet()))


@pytest.mark.parametrize("value", [0, -1, None, "3"])
def test_loop_budget_requires_positive_identical_failure_limit(value: object) -> None:
    validate_loop_declaration, _, _ = _api()
    declaration = _declaration()
    declaration["BUDGET"]["max_identical_failures"] = value
    assert "max_identical_failures" in _messages(validate_loop_declaration(declaration, _task_packet()))


@pytest.mark.parametrize("value", [0, -1, None, "60"])
def test_loop_budget_requires_positive_wall_time(value: object) -> None:
    validate_loop_declaration, _, _ = _api()
    declaration = _declaration()
    declaration["BUDGET"]["max_wall_minutes"] = value
    assert "max_wall_minutes" in _messages(validate_loop_declaration(declaration, _task_packet()))


@pytest.mark.parametrize(
    "field",
    ["on_verify_pass", "on_budget_exhausted", "on_identical_failure_limit"],
)
def test_loop_stop_requires_all_fail_closed_conditions(field: str) -> None:
    validate_loop_declaration, _, _ = _api()
    declaration = _declaration()
    declaration["STOP"][field] = False
    assert field in _messages(validate_loop_declaration(declaration, _task_packet()))


def test_loop_privileged_operation_must_stop_and_escalate() -> None:
    validate_loop_declaration, _, _ = _api()
    declaration = _declaration()
    declaration["STOP"]["privileged_operation"] = "allow"
    messages = _messages(validate_loop_declaration(declaration, _task_packet()))
    assert "privileged_operation" in messages and "stop_and_escalate" in messages


def test_loop_receipt_must_stay_under_governance_receipts() -> None:
    validate_loop_declaration, _, _ = _api()
    declaration = _declaration()
    declaration["RECEIPT"] = "docs/receipts/P0-T99.yaml"
    assert "RECEIPT" in _messages(validate_loop_declaration(declaration, _task_packet()))


@pytest.mark.parametrize("path", ["docs/GOALS.md", "docs/STATUS.md", "docs/PROJECT_BRIEF.md"])
def test_loop_rejects_shadow_state_paths_even_if_task_packet_allows_them(path: str) -> None:
    validate_loop_declaration, _, _ = _api()
    packet = _task_packet()
    packet["allowed_paths"].append(path)
    declaration = _declaration()
    declaration["SCOPE"] = [path]
    messages = _messages(validate_loop_declaration(declaration, packet))
    assert "shadow" in messages.lower() and path in messages


def test_loop_requires_exact_six_semantic_fields() -> None:
    validate_loop_declaration, _, _ = _api()
    declaration = _declaration()
    del declaration["STOP"]
    declaration["EXTRA"] = "not-authority"
    messages = _messages(validate_loop_declaration(declaration, _task_packet()))
    assert "six" in messages.lower() or "STOP" in messages


def test_loop_task_and_project_binding_are_fail_closed() -> None:
    validate_loop_declaration, _, _ = _api()
    declaration = _declaration()
    declaration["project"] = "OtherProject"
    declaration["task_id"] = "P0-T98"
    messages = _messages(validate_loop_declaration(declaration, _task_packet()))
    assert "ForgeLLM" in messages and "task_id" in messages


def test_vendor_provenance_accepts_pinned_snapshot() -> None:
    _, _, validate_vendor_provenance = _api()
    assert validate_vendor_provenance(ROOT) == []


def test_vendor_provenance_requires_exact_upstream_commit(tmp_path: Path) -> None:
    _, _, validate_vendor_provenance = _api()
    vendor = tmp_path / "third_party" / "loop-engineering"
    shutil.copytree(ROOT / "third_party" / "loop-engineering", vendor)
    provenance_path = vendor / "PROVENANCE.yaml"
    provenance = yaml.safe_load(provenance_path.read_text(encoding="utf-8"))
    provenance["upstream_commit"] = "0" * 40
    provenance_path.write_text(yaml.safe_dump(provenance, sort_keys=False), encoding="utf-8")
    messages = _messages(validate_vendor_provenance(tmp_path))
    assert "upstream_commit" in messages


def test_vendor_provenance_detects_byte_drift(tmp_path: Path) -> None:
    _, _, validate_vendor_provenance = _api()
    vendor = tmp_path / "third_party" / "loop-engineering"
    shutil.copytree(ROOT / "third_party" / "loop-engineering", vendor)
    methodology = vendor / "core" / "METHODOLOGY.md"
    methodology.write_text(methodology.read_text(encoding="utf-8") + "\nDRIFT\n", encoding="utf-8")
    messages = _messages(validate_vendor_provenance(tmp_path))
    assert "METHODOLOGY.md" in messages and "blob" in messages.lower()


def test_vendor_snapshot_contains_no_shell_scripts() -> None:
    shell_files = list((ROOT / "third_party" / "loop-engineering").rglob("*.sh"))
    assert shell_files == []


def test_valid_loop_receipt_passes() -> None:
    _, validate_loop_receipt, _ = _api()
    assert validate_loop_receipt(_receipt(), _declaration()) == []


@pytest.mark.parametrize("missing", ["base_commit", "final_commit", "scope_check", "verify_evidence", "reviewer"])
def test_receipt_requires_reproducible_evidence_fields(missing: str) -> None:
    _, validate_loop_receipt, _ = _api()
    receipt = _receipt()
    del receipt[missing]
    assert missing in _messages(validate_loop_receipt(receipt, _declaration()))


def test_receipt_changed_paths_must_stay_inside_loop_scope() -> None:
    _, validate_loop_receipt, _ = _api()
    receipt = _receipt()
    receipt["changed_paths"].append("src/not-authorized.py")
    messages = _messages(validate_loop_receipt(receipt, _declaration()))
    assert "changed_paths" in messages and "SCOPE" in messages


def test_receipt_verify_commands_must_equal_declared_verify() -> None:
    _, validate_loop_receipt, _ = _api()
    receipt = _receipt()
    receipt["verify_commands"] = ["make ci"]
    assert "verify_commands" in _messages(validate_loop_receipt(receipt, _declaration()))


def test_receipt_scope_check_must_pass() -> None:
    _, validate_loop_receipt, _ = _api()
    receipt = _receipt()
    receipt["scope_check"] = "exception"
    assert "scope_check" in _messages(validate_loop_receipt(receipt, _declaration()))


def test_receipt_commits_must_be_lowercase_full_sha() -> None:
    _, validate_loop_receipt, _ = _api()
    receipt = _receipt()
    receipt["final_commit"] = "ABC"
    assert "final_commit" in _messages(validate_loop_receipt(receipt, _declaration()))


def test_receipt_iteration_count_cannot_exceed_budget() -> None:
    _, validate_loop_receipt, _ = _api()
    receipt = _receipt()
    receipt["iterations"] = 11
    assert "iterations" in _messages(validate_loop_receipt(receipt, _declaration()))


def test_receipt_task_binding_must_match_declaration() -> None:
    _, validate_loop_receipt, _ = _api()
    receipt = _receipt()
    receipt["task_id"] = "P0-T98"
    assert "task_id" in _messages(validate_loop_receipt(receipt, _declaration()))


def test_fixture_copy_is_independent() -> None:
    original = _declaration()
    cloned = copy.deepcopy(original)
    cloned["BUDGET"]["max_iterations"] = 1
    assert original["BUDGET"]["max_iterations"] == 10


def test_repository_loop_gate_runs_successfully() -> None:
    command = [sys.executable, str(ROOT / "scripts/validate_loop_engineering.py"), "--root", str(ROOT)]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "OK: bounded Loop Engineering contract is valid" in result.stdout


LOOP_SKILL_PATHS = (
    ROOT / ".agents/skills/forgellm-loop-engineering/SKILL.md",
    ROOT / ".claude/skills/forgellm-loop-engineering/SKILL.md",
)
LOOP_AGREEMENT_BEGIN = "<!-- forgellm-loop-engineering:begin -->"
LOOP_AGREEMENT_END = "<!-- forgellm-loop-engineering:end -->"


def test_project_local_loop_agent_skills_exist_and_match() -> None:
    texts = []
    for path in LOOP_SKILL_PATHS:
        assert path.is_file(), f"missing project-local bounded loop skill: {path}"
        texts.append(path.read_text(encoding="utf-8"))
    assert texts[0] == texts[1]


def test_project_local_loop_agent_skills_preserve_authority_and_bounds() -> None:
    for path in LOOP_SKILL_PATHS:
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for marker in ("GOAL", "SCOPE", "VERIFY", "BUDGET", "STOP", "RECEIPT"):
            assert marker in text
        for marker in (
            "task packet",
            "accepted adr",
            "stop_and_escalate",
            "independent",
            "isolated",
            "worktree",
            "never execute vendored scripts",
        ):
            assert marker in lowered
        for forbidden in (".claude/hooks", ".codex/hooks", "stop-verify.sh", "./install.sh"):
            assert forbidden not in text


def test_agent_working_agreement_installs_bounded_loop_precedence() -> None:
    for relative in ("AGENTS.md", "CLAUDE.md"):
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert text.count(LOOP_AGREEMENT_BEGIN) == 1
        assert text.count(LOOP_AGREEMENT_END) == 1
        bounded = text.split(LOOP_AGREEMENT_BEGIN, 1)[1].split(LOOP_AGREEMENT_END, 1)[0]
        assert "task packets and accepted ADRs remain authoritative" in bounded
        assert "may narrow but never widen SCOPE/VERIFY/privilege" in bounded
        assert "No upstream installer, eval runner, Stop hook" in bounded


def test_project_local_loop_skills_are_reference_only_for_upstream_content() -> None:
    for path in LOOP_SKILL_PATHS:
        text = path.read_text(encoding="utf-8")
        assert "third_party/loop-engineering/core/METHODOLOGY.md" in text
        assert "third_party/loop-engineering/core/COMMANDS.md" in text
        assert "reference only" in text.lower()


def test_makefile_wires_p0_t10_into_normal_validation_without_dropping_p0_t09() -> None:
    text = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert "validate-loop" in text
    assert "validate: validate-loop" in text
    assert "$(PYTHON) scripts/validate_task_packet.py tasks/open/P0-T10-bounded-loop-engineering.yaml --root ." in text
    assert "$(PYTHON) scripts/validate_loop_engineering.py --root ." in text
    assert "$(PYTHON) scripts/validate_task_packet.py tasks/open/P0-T09-sonarqube-main-analysis.yaml --root ." in text


def test_makefile_formats_new_loop_python_surface() -> None:
    text = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert "LOOP_FORMAT_FILES" in text
    for path in (
        "src/forgellm_governance/loop_engineering.py",
        "scripts/validate_loop_engineering.py",
        "tests/test_loop_engineering.py",
    ):
        assert path in text
    assert "$(PYTHON) -m ruff format --check $(SPECULATIVE_FORMAT_FILES) $(LOOP_FORMAT_FILES)" in text
