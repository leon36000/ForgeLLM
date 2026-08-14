from __future__ import annotations

import json
from pathlib import Path

import pytest

from forgellm_governance.schema_io import (
    load_json_mapping,
    resolve_artifact_output,
    resolve_input_file,
    sha256_file,
    validate_instance,
)


def test_load_json_mapping_accepts_object(tmp_path: Path) -> None:
    path = tmp_path / "valid.json"
    path.write_text('{"a": 1}\n', encoding="utf-8")
    assert load_json_mapping(path) == {"a": 1}


def test_load_json_mapping_rejects_array(tmp_path: Path) -> None:
    path = tmp_path / "array.json"
    path.write_text("[]\n", encoding="utf-8")
    with pytest.raises(ValueError, match="JSON root must be an object"):
        load_json_mapping(path)


def test_load_json_mapping_reports_line_and_column(tmp_path: Path) -> None:
    path = tmp_path / "broken.json"
    path.write_text('{\n  "a":,\n}\n', encoding="utf-8")
    with pytest.raises(ValueError, match=r"line 2, column 7"):
        load_json_mapping(path)


def test_resolve_input_file_accepts_repository_file(tmp_path: Path) -> None:
    path = tmp_path / "inputs" / "a.json"
    path.parent.mkdir()
    path.write_text("{}\n", encoding="utf-8")
    assert resolve_input_file(tmp_path, Path("inputs/a.json")) == path.resolve()


def test_resolve_input_file_rejects_traversal(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside.json"
    outside.write_text("{}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="path escapes repository root"):
        resolve_input_file(tmp_path, Path("../outside.json"))


def test_resolve_input_file_rejects_symlink_escape(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside-target.json"
    outside.write_text("{}\n", encoding="utf-8")
    link = tmp_path / "link.json"
    link.symlink_to(outside)
    with pytest.raises(ValueError, match="path escapes repository root"):
        resolve_input_file(tmp_path, Path("link.json"))


def test_resolve_artifact_output_accepts_nested_path(tmp_path: Path) -> None:
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    expected = artifacts / "simulations" / "result.json"
    assert resolve_artifact_output(tmp_path, Path("artifacts/simulations/result.json")) == expected.resolve()


def test_resolve_artifact_output_rejects_outside_path(tmp_path: Path) -> None:
    (tmp_path / "artifacts").mkdir()
    with pytest.raises(ValueError, match="output path must be beneath artifacts"):
        resolve_artifact_output(tmp_path, Path("result.json"))


def test_resolve_artifact_output_rejects_existing_symlink(tmp_path: Path) -> None:
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    outside = tmp_path.parent / "outside-output.json"
    link = artifacts / "result.json"
    link.symlink_to(outside)
    with pytest.raises(ValueError, match="output path cannot be a symlink"):
        resolve_artifact_output(tmp_path, Path("artifacts/result.json"))


def test_resolve_artifact_output_rejects_parent_symlink_escape(tmp_path: Path) -> None:
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    outside_dir = tmp_path.parent / "outside-artifacts"
    outside_dir.mkdir(exist_ok=True)
    (artifacts / "escape").symlink_to(outside_dir, target_is_directory=True)
    with pytest.raises(ValueError, match="output path must be beneath artifacts"):
        resolve_artifact_output(tmp_path, Path("artifacts/escape/result.json"))


def test_sha256_file_matches_known_value(tmp_path: Path) -> None:
    path = tmp_path / "bytes.bin"
    path.write_bytes(b"abc")
    assert sha256_file(path) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_validate_instance_orders_issues_deterministically(tmp_path: Path) -> None:
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "required": ["a", "b"],
        "properties": {"a": {"type": "integer"}, "b": {"type": "string"}},
    }
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(json.dumps(schema), encoding="utf-8")
    issues = validate_instance({"b": 1, "z": True}, schema_path, Path("input.json"))
    rendered = [(issue.path, issue.message) for issue in issues]
    assert rendered == sorted(rendered)
    assert len(rendered) == 3


def test_load_json_mapping_rejects_duplicate_object_keys(tmp_path: Path) -> None:
    path = tmp_path / "duplicate-key.json"
    path.write_text('{"a": 1, "a": 2}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate JSON object key: a"):
        load_json_mapping(path)


def test_resolve_artifact_output_rejects_symlinked_artifacts_root(tmp_path: Path) -> None:
    outside_dir = tmp_path.parent / "outside-artifacts-root"
    outside_dir.mkdir(exist_ok=True)
    (tmp_path / "artifacts").symlink_to(outside_dir, target_is_directory=True)
    with pytest.raises(ValueError, match="artifacts directory cannot be a symlink"):
        resolve_artifact_output(tmp_path, Path("artifacts/result.json"))
