from __future__ import annotations

import subprocess
from pathlib import Path

import yaml

from forgellm_governance.validation import (
    build_mobile_manifest,
    validate_derived_state,
    validate_task_lifecycle,
    validate_tree_projection,
)

ROOT = Path(__file__).resolve().parents[1]


def _packet(
    task_id: str = "P0-T01",
    *,
    status: str = "ready",
    decision_ids: list[str] | None = None,
    dependencies: list[str] | None = None,
) -> dict:
    packet = {
        "schema_version": "1.0",
        "task_id": task_id,
        "title": "Bounded lifecycle fixture",
        "phase": "P0",
        "status": status,
        "charter_goals": ["Preserve auditable project state"],
        "goal": "Validate lifecycle state without changing runtime behavior.",
        "non_goals": ["Implement an inference runtime"],
        "inputs": ["ForgeLLM repository"],
        "outputs": ["Deterministic lifecycle evidence"],
        "allowed_paths": ["tests/"],
        "forbidden_actions": ["Change external systems or secrets"],
        "acceptance_criteria": ["Reject contradictory lifecycle metadata"],
        "verification_commands": ["python3 -m pytest"],
        "evidence_requirements": ["Record deterministic validator output"],
        "dependencies": dependencies or [],
        "owner_role": "project owner",
        "reviewer_role": "independent reviewer",
    }
    if decision_ids is not None:
        packet["decision_ids"] = decision_ids
    return packet


def _task_root(tmp_path: Path) -> Path:
    (tmp_path / "tasks/open").mkdir(parents=True)
    (tmp_path / "tasks/closed").mkdir(parents=True)
    (tmp_path / "schemas").mkdir()
    (tmp_path / "docs/architecture").mkdir(parents=True)
    (tmp_path / "schemas/task-packet.schema.json").write_bytes((ROOT / "schemas/task-packet.schema.json").read_bytes())
    return tmp_path


def _write_packet(root: Path, directory: str, filename: str, packet: dict) -> None:
    path = root / directory / filename
    path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")


def _write_adr(root: Path, name: str, status: str, successor: str | None = None) -> None:
    lines = [f"# {name}", "", f"- **Status:** {status}"]
    if successor is not None:
        lines.append(f"- **Successor:** {successor}")
    (root / "docs/architecture" / f"{name}-decision.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_lifecycle_rejects_complete_packet_in_open_directory(tmp_path: Path) -> None:
    root = _task_root(tmp_path)
    _write_packet(root, "tasks/open", "P0-T01-bad.yaml", _packet(status="complete"))

    issues = validate_task_lifecycle(root)

    assert any("tasks/open" in issue.path and "non-terminal" in issue.message for issue in issues)


def test_lifecycle_rejects_nonterminal_packet_in_closed_directory(tmp_path: Path) -> None:
    root = _task_root(tmp_path)
    _write_packet(root, "tasks/closed", "P0-T01-bad.yaml", _packet(status="review"))

    issues = validate_task_lifecycle(root)

    assert any("tasks/closed" in issue.path and "terminal" in issue.message for issue in issues)


def test_lifecycle_rejects_duplicate_task_id_across_directories(tmp_path: Path) -> None:
    root = _task_root(tmp_path)
    _write_packet(root, "tasks/open", "P0-T01-open.yaml", _packet(status="ready"))
    _write_packet(root, "tasks/closed", "P0-T01-closed.yaml", _packet(status="complete"))

    issues = validate_task_lifecycle(root)

    assert any("duplicate task ID P0-T01" in issue.message for issue in issues)


def test_lifecycle_rejects_filename_task_id_mismatch(tmp_path: Path) -> None:
    root = _task_root(tmp_path)
    _write_packet(root, "tasks/open", "P0-T02-wrong-prefix.yaml", _packet(task_id="P0-T01"))

    issues = validate_task_lifecycle(root)

    assert any("filename must start with task ID" in issue.message for issue in issues)


def test_lifecycle_rejects_unresolved_dependency(tmp_path: Path) -> None:
    root = _task_root(tmp_path)
    _write_packet(root, "tasks/open", "P0-T01.yaml", _packet(dependencies=["P0-T99"]))

    issues = validate_task_lifecycle(root)

    assert any("unresolved dependency P0-T99" in issue.message for issue in issues)


def test_lifecycle_rejects_complete_task_governed_by_proposed_adr(tmp_path: Path) -> None:
    root = _task_root(tmp_path)
    _write_adr(root, "ADR-0005", "proposed")
    _write_packet(
        root,
        "tasks/closed",
        "P0-T10-loop.yaml",
        _packet(task_id="P0-T10", status="complete", decision_ids=["ADR-0005"]),
    )

    issues = validate_task_lifecycle(root)

    assert any("ADR-0005" in issue.message and "accepted" in issue.message for issue in issues)


def test_lifecycle_rejects_missing_decision_for_nonterminal_task(tmp_path: Path) -> None:
    root = _task_root(tmp_path)
    _write_packet(
        root,
        "tasks/open",
        "P0-T10-loop.yaml",
        _packet(task_id="P0-T10", status="review", decision_ids=["ADR-0005"]),
    )

    issues = validate_task_lifecycle(root)

    assert any("unresolved decision ADR-0005" in issue.message for issue in issues)


def test_lifecycle_rejects_superseded_adr_without_successor(tmp_path: Path) -> None:
    root = _task_root(tmp_path)
    _write_adr(root, "ADR-0005", "superseded")
    _write_packet(
        root,
        "tasks/closed",
        "P0-T10-loop.yaml",
        _packet(task_id="P0-T10", status="complete", decision_ids=["ADR-0005"]),
    )

    issues = validate_task_lifecycle(root)

    assert any("superseded ADR-0005" in issue.message for issue in issues)


def test_lifecycle_accepts_complete_task_with_accepted_successor(tmp_path: Path) -> None:
    root = _task_root(tmp_path)
    _write_adr(root, "ADR-0005", "superseded", successor="ADR-0006")
    _write_adr(root, "ADR-0006", "accepted")
    _write_packet(
        root,
        "tasks/closed",
        "P0-T10-loop.yaml",
        _packet(task_id="P0-T10", status="complete", decision_ids=["ADR-0005"]),
    )

    assert validate_task_lifecycle(root) == []


def _projection_repo(tmp_path: Path) -> Path:
    root = tmp_path / "projection"
    (root / "docs/state").mkdir(parents=True)
    (root / "docs/roadmap").mkdir(parents=True)
    (root / "chatgpt/mobile-core").mkdir(parents=True)
    initial_state = "- **State ID:** S-0099\n- **Canonical source commit:** `" + "0" * 40 + "`\n"
    (root / "docs/state/CURRENT_STATE.md").write_text(initial_state, encoding="utf-8")
    for relative in (
        "docs/state/DECISIONS.md",
        "docs/state/RISKS.md",
        "docs/state/OPEN_QUESTIONS.md",
        "docs/state/HANDOFF.md",
        "docs/roadmap/PHASE0_TASKS.md",
    ):
        (root / relative).write_text(f"# {relative}\n", encoding="utf-8")
    subprocess.run(["git", "init", "--quiet"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Lifecycle Test"], cwd=root, check=True)
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "--quiet", "-m", "base"], cwd=root, check=True)
    source_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()
    (root / "docs/state/CURRENT_STATE.md").write_text(
        f"- **State ID:** S-0099\n- **Canonical source commit:** `{source_commit}`\n", encoding="utf-8"
    )
    (root / "chatgpt/mobile-core/03_FORGELLM_STATE_AND_DECISIONS.md").write_text(
        "# Derived state\n"
        "**Canonical state ID:** S-0099\n"
        f"**Canonical source commit:** `{source_commit}`\n"
        "**Derived manifest:** `chatgpt/mobile-core/DERIVED-MANIFEST.yaml`\n",
        encoding="utf-8",
    )
    manifest = build_mobile_manifest(root)
    (root / "chatgpt/mobile-core/DERIVED-MANIFEST.yaml").write_text(
        yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8"
    )
    (root / "README.md").write_text(
        "<!-- forgellm:current-state:begin -->\n"
        "State ID: `S-0099`\n"
        f"Canonical source commit: `{source_commit}`\n"
        "Task statuses: <none>\n"
        "<!-- forgellm:current-state:end -->\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "--quiet", "-m", "derived"], cwd=root, check=True)
    return root


def test_derived_state_projection_matches_manifest(tmp_path: Path) -> None:
    assert validate_derived_state(_projection_repo(tmp_path)) == []


def test_derived_state_accepts_shallow_checkout_without_source_object(tmp_path: Path) -> None:
    full = _projection_repo(tmp_path)
    shallow = tmp_path / "shallow"
    subprocess.run(["git", "clone", "--quiet", "--depth=1", f"file://{full}", str(shallow)], check=True)

    assert validate_derived_state(shallow) == []


def test_derived_state_rejects_stale_mobile_state_id(tmp_path: Path) -> None:
    root = _projection_repo(tmp_path)
    path = root / "chatgpt/mobile-core/03_FORGELLM_STATE_AND_DECISIONS.md"
    path.write_text(path.read_text(encoding="utf-8").replace("S-0099", "S-0001"), encoding="utf-8")

    issues = validate_derived_state(root)

    assert any("mobile projection state ID" in issue.message for issue in issues)


def test_derived_state_rejects_stale_manifest_hash(tmp_path: Path) -> None:
    root = _projection_repo(tmp_path)
    path = root / "chatgpt/mobile-core/DERIVED-MANIFEST.yaml"
    manifest = yaml.safe_load(path.read_text(encoding="utf-8"))
    manifest["projections"][0]["source_sha256"]["docs/state/CURRENT_STATE.md"] = "0" * 64
    path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")

    issues = validate_derived_state(root)

    assert any("manifest is stale" in issue.message for issue in issues)


def test_derived_state_rejects_stale_readme_state_id(tmp_path: Path) -> None:
    root = _projection_repo(tmp_path)
    path = root / "README.md"
    path.write_text(path.read_text(encoding="utf-8").replace("S-0099", "S-0001"), encoding="utf-8")

    issues = validate_derived_state(root)

    assert any("README current-state block" in issue.message for issue in issues)


def test_tree_projection_rejects_stale_listing(tmp_path: Path) -> None:
    root = tmp_path / "tree"
    root.mkdir()
    (root / "README.md").write_text("# fixture\n", encoding="utf-8")
    (root / "TREE.txt").write_text("README.md\n", encoding="utf-8")
    subprocess.run(["git", "init", "--quiet"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Lifecycle Test"], cwd=root, check=True)
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "--quiet", "-m", "base"], cwd=root, check=True)

    issues = validate_tree_projection(root)

    assert any("TREE.txt is stale" in issue.message for issue in issues)
