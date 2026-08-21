import copy
import hashlib
import importlib
from pathlib import Path

import pytest
import yaml

from forgellm_governance.loop_engineering import (
    validate_loop_declaration,
    validate_loop_receipt,
    validate_loop_receipt_template,
    validate_loop_verify_command,
)

VALID_COMMIT = "0123456789abcdef0123456789abcdef01234567"
VERIFY_COMMAND = "make test"


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
        "verification": {"disposition": "pass"},
        "verify_commands": [VERIFY_COMMAND],
        "verify_evidence": ["pytest: 1 passed"],
        "reviewer": "independent-verifier",
    }


def _messages(items: list[str]) -> str:
    return "\n".join(items)


def _git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data, usedforsecurity=False).hexdigest()


def _catalog_fixture(tmp_path: Path) -> tuple[Path, dict, dict, dict]:
    root = tmp_path
    packet_path = root / "tasks/open/P0-T10-bounded-loop-engineering.yaml"
    declaration_path = root / "artifacts/governance/loop-engineering/declarations/P0-T10-run-01.yaml"
    receipt_path = root / "artifacts/governance/loop-engineering/receipts/P0-T10-run-01.yaml"
    index_path = root / "artifacts/governance/loop-engineering/receipt-index.yaml"
    for path in (packet_path, declaration_path, receipt_path, index_path):
        path.parent.mkdir(parents=True, exist_ok=True)

    packet = {
        "task_id": "P0-T10",
        "allowed_paths": ["src/example.py", "tests/test_example.py"],
        "verification_commands": [VERIFY_COMMAND],
    }
    declaration = _declaration()
    declaration.update({"task_id": "P0-T10", "RECEIPT": str(receipt_path.relative_to(root))})
    receipt = _receipt()
    receipt.update({"task_id": "P0-T10", "verification": {"disposition": "pass"}})
    declaration_path.write_text(yaml.safe_dump(declaration, sort_keys=False), encoding="utf-8")
    receipt_path.write_text(yaml.safe_dump(receipt, sort_keys=False), encoding="utf-8")
    packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")
    index = {
        "schema_version": "1.0",
        "project": "ForgeLLM",
        "task_id": "P0-T10",
        "runs": [
            {
                "run_id": "P0-T10-run-01",
                "declaration_path": declaration_path.relative_to(root).as_posix(),
                "declaration_source_commit": VALID_COMMIT,
                "declaration_source_blob_sha": _git_blob_sha(declaration_path.read_bytes()),
                "receipt_path": receipt_path.relative_to(root).as_posix(),
                "receipt_schema_version": "1.0",
            }
        ],
    }
    index_path.write_text(yaml.safe_dump(index, sort_keys=False), encoding="utf-8")
    return root, index, declaration, receipt


def _validate_repository():
    return importlib.import_module("scripts.validate_loop_engineering").validate_repository


@pytest.mark.parametrize("command", [
    "make ci && git push origin main",
    "make ci; gh pr merge 37",
    "make ci > /tmp/result.log",
    "env git push origin main",
    "command git status",
    "git add README.md",
    "git branch -D review-head",
    "gh workflow run release.yml",
    "kubectl get secret sonar-token",
])
def test_firewall_rejects_composition_wrappers_mutations_and_privileged_reads(command):
    messages = validate_loop_verify_command(command)
    assert messages
    assert "stop_and_escalate" in messages[0]


@pytest.mark.parametrize("command", [
    "git status --short",
    "git diff --check",
    "gh pr view 37 --json state",
])
def test_firewall_allows_explicit_read_only_commands(command):
    assert validate_loop_verify_command(command) == []


@pytest.mark.parametrize("command", [
    "python -c 'print(1)'",
    "git status $(cat secret.txt)",
    "pip install requests",
    "curl -X POST https://example.invalid",
    "wget --method=POST https://example.invalid",
    "CI=1 git status --short",
])
def test_firewall_rejects_code_substitution_install_mutation_and_assignments(command):
    messages = validate_loop_verify_command(command)
    assert messages
    assert "stop_and_escalate" in messages[0]


def test_valid_bounded_loop_declaration_passes():
    assert validate_loop_declaration(_declaration(), _task_packet()) == []


@pytest.mark.parametrize("bad_scope", [["src/not-authorized.py"], ["."], ["src/example.py", "../outside"]])
def test_loop_scope_cannot_widen_task_packet(bad_scope):
    declaration = _declaration()
    declaration["SCOPE"] = bad_scope
    messages = _messages(validate_loop_declaration(declaration, _task_packet()))
    assert "SCOPE" in messages
    assert "allowed_paths" in messages


def test_loop_scope_rejects_prefix_confusion():
    packet = _task_packet()
    packet["allowed_paths"] = ["third_party/loop-engineering/"]
    declaration = _declaration()
    declaration["SCOPE"] = ["third_party/loop-engineering-evil/"]
    messages = _messages(validate_loop_declaration(declaration, packet))
    assert "SCOPE" in messages
    assert "allowed_paths" in messages


def test_loop_verify_must_be_authorized_by_task_packet():
    declaration = _declaration()
    declaration["VERIFY"] = ["make ci && curl https://example.invalid"]
    messages = _messages(validate_loop_declaration(declaration, _task_packet()))
    assert "VERIFY" in messages
    assert "verification_commands" in messages


@pytest.mark.parametrize("field", ["max_iterations", "max_identical_failures", "max_wall_minutes"])
@pytest.mark.parametrize("value", [0, -1, None, "10"])
def test_loop_budget_requires_positive_ceilings(field, value):
    declaration = _declaration()
    declaration["BUDGET"][field] = value
    assert field in _messages(validate_loop_declaration(declaration, _task_packet()))


@pytest.mark.parametrize("field", ["on_verify_pass", "on_budget_exhausted", "on_identical_failure_limit"])
def test_loop_stop_requires_all_fail_closed_conditions(field):
    declaration = _declaration()
    declaration["STOP"][field] = False
    assert field in _messages(validate_loop_declaration(declaration, _task_packet()))


def test_loop_privileged_operation_must_stop_and_escalate():
    declaration = _declaration()
    declaration["STOP"]["privileged_operation"] = "allow"
    messages = _messages(validate_loop_declaration(declaration, _task_packet()))
    assert "privileged_operation" in messages
    assert "stop_and_escalate" in messages


def test_loop_receipt_must_stay_under_governance_receipts():
    declaration = _declaration()
    declaration["RECEIPT"] = "docs/receipts/P0-T99.yaml"
    assert "RECEIPT" in _messages(validate_loop_declaration(declaration, _task_packet()))


@pytest.mark.parametrize("path", ["docs/GOALS.md", "docs/STATUS.md", "docs/PROJECT_BRIEF.md"])
def test_loop_rejects_shadow_state_paths_even_if_task_packet_allows_them(path):
    packet = _task_packet()
    packet["allowed_paths"].append(path)
    declaration = _declaration()
    declaration["SCOPE"] = [path]
    messages = _messages(validate_loop_declaration(declaration, packet))
    assert "shadow" in messages.lower()
    assert path in messages


def test_loop_requires_exact_six_semantic_fields():
    declaration = _declaration()
    del declaration["STOP"]
    declaration["EXTRA"] = "not-authority"
    messages = _messages(validate_loop_declaration(declaration, _task_packet()))
    assert "six" in messages.lower() or "STOP" in messages


def test_loop_task_and_project_binding_are_fail_closed():
    declaration = _declaration()
    declaration["project"] = "OtherProject"
    declaration["task_id"] = "P0-T98"
    messages = _messages(validate_loop_declaration(declaration, _task_packet()))
    assert "ForgeLLM" in messages
    assert "task_id" in messages


def test_valid_loop_receipt_passes():
    assert validate_loop_receipt(_receipt(), _declaration()) == []


@pytest.mark.parametrize(
    "missing", ["base_commit", "final_commit", "scope_check", "verification", "verify_evidence", "reviewer"]
)
def test_receipt_requires_reproducible_evidence_fields(missing):
    receipt = _receipt()
    del receipt[missing]
    assert missing in _messages(validate_loop_receipt(receipt, _declaration()))


def test_receipt_changed_paths_must_stay_inside_loop_scope():
    receipt = _receipt()
    receipt["changed_paths"].append("src/not-authorized.py")
    messages = _messages(validate_loop_receipt(receipt, _declaration()))
    assert "changed_paths" in messages
    assert "SCOPE" in messages


def test_receipt_verify_commands_must_equal_declared_verify():
    receipt = _receipt()
    receipt["verify_commands"] = ["make ci"]
    assert "verify_commands" in _messages(validate_loop_receipt(receipt, _declaration()))


def test_receipt_scope_check_must_pass():
    receipt = _receipt()
    receipt["scope_check"] = "exception"
    assert "scope_check" in _messages(validate_loop_receipt(receipt, _declaration()))


def test_receipt_commits_must_be_lowercase_full_sha():
    receipt = _receipt()
    receipt["final_commit"] = "ABC"
    assert "final_commit" in _messages(validate_loop_receipt(receipt, _declaration()))


def test_receipt_iteration_count_cannot_exceed_budget():
    receipt = _receipt()
    receipt["iterations"] = 11
    assert "iterations" in _messages(validate_loop_receipt(receipt, _declaration()))


def test_receipt_identical_failure_count_cannot_exceed_budget():
    receipt = _receipt()
    receipt["identical_failures_at_stop"] = 4
    assert "identical_failures" in _messages(validate_loop_receipt(receipt, _declaration()))


def test_receipt_task_binding_must_match_declaration():
    receipt = _receipt()
    receipt["task_id"] = "P0-T98"
    assert "task_id" in _messages(validate_loop_receipt(receipt, _declaration()))


@pytest.mark.parametrize(
    ("stop_reason", "disposition"),
    [("verify_pass", "budget_exhausted"), ("budget_exhausted", "pass"), ("manual_stop", "pass")],
)
def test_receipt_stop_reason_must_match_verification_disposition(stop_reason, disposition):
    receipt = _receipt()
    receipt["stop_reason"] = stop_reason
    receipt["verification"]["disposition"] = disposition
    messages = _messages(validate_loop_receipt(receipt, _declaration()))
    assert "disposition" in messages


def test_receipt_verification_disposition_is_structurally_bounded():
    receipt = _receipt()
    receipt["verification"] = {"disposition": "arbitrary"}
    messages = _messages(validate_loop_receipt(receipt, _declaration()))
    assert "disposition" in messages


def test_receipt_rejects_template_as_final_evidence():
    receipt = _receipt()
    receipt["final_commit"] = "REPLACE_WITH_FINAL_COMMIT"
    receipt["reviewer"] = "TEMPLATE: reviewer"
    messages = _messages(validate_loop_receipt(receipt, _declaration()))
    assert "final_commit" in messages or "reviewer" in messages


def test_receipt_template_has_separate_structural_validator():
    template = _receipt()
    template.update(
        {
            "base_commit": VALID_COMMIT,
            "final_commit": "REPLACE_WITH_FINAL_COMMIT",
            "iterations": 0,
            "identical_failures_at_stop": 0,
            "stop_reason": "template",
            "changed_paths": [],
            "verification": {"disposition": "template"},
            "verify_evidence": ["TEMPLATE: evidence"],
            "reviewer": "TEMPLATE: independent verifier",
        }
    )
    assert validate_loop_receipt_template(template, _declaration()) == []


def test_repository_catalog_accepts_immutable_declaration_and_receipt(tmp_path):
    root, _, _, _ = _catalog_fixture(tmp_path)
    assert _validate_repository()(root) == []


def test_repository_catalog_rejects_declaration_blob_drift(tmp_path):
    root, _, _, _ = _catalog_fixture(tmp_path)
    path = root / "artifacts/governance/loop-engineering/declarations/P0-T10-run-01.yaml"
    path.write_text(path.read_text(encoding="utf-8") + "\nGOAL: drift\n", encoding="utf-8")
    messages = _messages(_validate_repository()(root))
    assert "declaration_source_blob_sha" in messages


def test_repository_catalog_requires_every_final_receipt_to_be_indexed(tmp_path):
    root, _, _, receipt = _catalog_fixture(tmp_path)
    extra = root / "artifacts/governance/loop-engineering/receipts/P0-T10-run-02.yaml"
    receipt["task_id"] = "P0-T10"
    extra.write_text(yaml.safe_dump(receipt, sort_keys=False), encoding="utf-8")
    messages = _messages(_validate_repository()(root))
    assert "every committed final receipt" in messages


def test_repository_catalog_requires_every_declaration_to_be_indexed(tmp_path):
    root, _, declaration, _ = _catalog_fixture(tmp_path)
    extra = root / "artifacts/governance/loop-engineering/declarations/P0-T10-run-02.yaml"
    declaration["task_id"] = "P0-T10"
    extra.write_text(yaml.safe_dump(declaration, sort_keys=False), encoding="utf-8")
    messages = _messages(_validate_repository()(root))
    assert "every committed immutable declaration" in messages


def test_repository_catalog_rejects_duplicate_run_identity(tmp_path):
    root, index, _, _ = _catalog_fixture(tmp_path)
    index["runs"].append(copy.deepcopy(index["runs"][0]))
    (root / "artifacts/governance/loop-engineering/receipt-index.yaml").write_text(
        yaml.safe_dump(index, sort_keys=False), encoding="utf-8"
    )
    messages = _messages(_validate_repository()(root))
    assert "run_id values must be unique" in messages


def test_repository_catalog_rejects_paths_outside_fixed_prefix(tmp_path):
    root, index, _, _ = _catalog_fixture(tmp_path)
    index["runs"][0]["receipt_path"] = "artifacts/other.yaml"
    (root / "artifacts/governance/loop-engineering/receipt-index.yaml").write_text(
        yaml.safe_dump(index, sort_keys=False), encoding="utf-8"
    )
    messages = _messages(_validate_repository()(root))
    assert "receipt_path" in messages


def test_repository_catalog_rejects_declaration_base_mismatch(tmp_path):
    root, _, declaration, _ = _catalog_fixture(tmp_path)
    declaration["base_commit"] = "abcdef0123456789abcdef0123456789abcdef01"
    path = root / "artifacts/governance/loop-engineering/declarations/P0-T10-run-01.yaml"
    path.write_text(yaml.safe_dump(declaration, sort_keys=False), encoding="utf-8")
    messages = _messages(_validate_repository()(root))
    assert "base_commit" in messages


def test_repository_catalog_rejects_stop_disposition_mismatch(tmp_path):
    root, _, _, receipt = _catalog_fixture(tmp_path)
    receipt["verification"]["disposition"] = "budget_exhausted"
    path = root / "artifacts/governance/loop-engineering/receipts/P0-T10-run-01.yaml"
    path.write_text(yaml.safe_dump(receipt, sort_keys=False), encoding="utf-8")
    messages = _messages(_validate_repository()(root))
    assert "disposition" in messages
