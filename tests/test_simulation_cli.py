from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from forgellm_governance.schema_io import sha256_file

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "simulate_placement.py"


def _make_root(tmp_path: Path) -> tuple[Path, Path, Path]:
    root = tmp_path / "repo"
    (root / "schemas").mkdir(parents=True)
    (root / "artifacts" / "simulations").mkdir(parents=True)
    for name in ("topology.schema.json", "component-profile.schema.json", "placement-result.schema.json"):
        shutil.copy2(ROOT / "schemas" / name, root / "schemas" / name)
    topology = root / "topology.json"
    components = root / "components.json"
    shutil.copy2(ROOT / "tests" / "fixtures" / "topology" / "valid-synthetic.json", topology)
    shutil.copy2(ROOT / "tests" / "fixtures" / "components" / "valid-cache-draft.json", components)
    return root, topology, components


def _run(root: Path, topology: Path, components: Path, output: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--root",
            str(root),
            "--topology",
            str(topology),
            "--components",
            str(components),
            "--output",
            str(output),
            *extra,
        ],
        check=False,
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )


def test_successful_cli_writes_schema_valid_synthetic_result(tmp_path: Path) -> None:
    root, topology, components = _make_root(tmp_path)
    output = root / "artifacts" / "simulations" / "result.json"
    completed = _run(root, topology, components, output)
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == str(output.resolve())
    document = json.loads(output.read_text(encoding="utf-8"))
    schema = json.loads((root / "schemas" / "placement-result.schema.json").read_text(encoding="utf-8"))
    assert list(Draft202012Validator(schema).iter_errors(document)) == []
    assert document["evidence_boundary"] == "synthetic_only"
    assert document["inputs"] == {
        "components_sha256": sha256_file(components),
        "topology_sha256": sha256_file(topology),
    }
    assert document["components"]


def test_output_is_byte_identical_across_artifact_paths(tmp_path: Path) -> None:
    root, topology, components = _make_root(tmp_path)
    first = root / "artifacts" / "simulations" / "first.json"
    second = root / "artifacts" / "simulations" / "second.json"
    assert _run(root, topology, components, first).returncode == 0
    assert _run(root, topology, components, second).returncode == 0
    assert first.read_bytes() == second.read_bytes()


def test_malformed_input_writes_no_partial_output(tmp_path: Path) -> None:
    root, topology, components = _make_root(tmp_path)
    topology.write_text('{"broken":', encoding="utf-8")
    output = root / "artifacts" / "simulations" / "result.json"
    completed = _run(root, topology, components, output)
    assert completed.returncode == 1
    assert completed.stderr.startswith("ERROR:")
    assert "Traceback" not in completed.stderr
    assert not output.exists()


def test_existing_output_is_unchanged_after_validation_failure(tmp_path: Path) -> None:
    root, topology, components = _make_root(tmp_path)
    output = root / "artifacts" / "simulations" / "result.json"
    output.write_text("sentinel\n", encoding="utf-8")
    components.write_text("[]\n", encoding="utf-8")
    completed = _run(root, topology, components, output)
    assert completed.returncode == 1
    assert output.read_text(encoding="utf-8") == "sentinel\n"


def test_output_traversal_is_rejected(tmp_path: Path) -> None:
    root, topology, components = _make_root(tmp_path)
    output = root / "artifacts" / ".." / "escape.json"
    completed = _run(root, topology, components, output)
    assert completed.returncode == 1
    assert "output path must be beneath artifacts" in completed.stderr
    assert not (root / "escape.json").exists()


def test_output_symlink_escape_is_rejected(tmp_path: Path) -> None:
    root, topology, components = _make_root(tmp_path)
    outside = tmp_path / "outside.json"
    link = root / "artifacts" / "simulations" / "result.json"
    link.symlink_to(outside)
    completed = _run(root, topology, components, link)
    assert completed.returncode == 1
    assert "output path cannot be a symlink" in completed.stderr
    assert not outside.exists()


def test_unknown_argument_uses_argparse_exit_two(tmp_path: Path) -> None:
    root, topology, components = _make_root(tmp_path)
    output = root / "artifacts" / "simulations" / "result.json"
    completed = _run(root, topology, components, output, "--unknown")
    assert completed.returncode == 2
    assert "unrecognized arguments" in completed.stderr
    assert not output.exists()


def test_build_result_document_keeps_the_planned_public_signature() -> None:
    import inspect

    from forgellm_governance.simulation import build_result_document

    assert tuple(inspect.signature(build_result_document).parameters) == (
        "topology_path",
        "component_path",
        "topology",
        "plans",
    )


def test_output_path_cannot_overwrite_an_input_document(tmp_path: Path) -> None:
    from forgellm_governance.simulation import run_simulation

    root, topology, components = _make_root(tmp_path)
    topology_under_artifacts = root / "artifacts" / "topology.json"
    shutil.copy2(topology, topology_under_artifacts)
    original = topology_under_artifacts.read_bytes()
    with pytest.raises(ValueError, match="output path must differ from input paths"):
        run_simulation(root, topology_under_artifacts, components, topology_under_artifacts)
    assert topology_under_artifacts.read_bytes() == original


def test_input_mutation_during_planning_fails_without_output(tmp_path: Path, monkeypatch) -> None:
    import forgellm_governance.simulation as simulation

    root, topology, components = _make_root(tmp_path)
    output = root / "artifacts" / "simulations" / "result.json"
    original_plan_components = simulation.plan_components

    def mutate_after_planning(topology_snapshot, component_profiles):
        plans = original_plan_components(topology_snapshot, component_profiles)
        document = json.loads(components.read_text(encoding="utf-8"))
        document["description"] = "mutated after validated planning"
        components.write_text(json.dumps(document), encoding="utf-8")
        return plans

    monkeypatch.setattr(simulation, "plan_components", mutate_after_planning)
    with pytest.raises(simulation.SimulationError, match="input changed during simulation"):
        simulation.run_simulation(root, topology, components, output)
    assert not output.exists()
