from __future__ import annotations

import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from forgellm_governance.components import (
    ComponentValidationError,
    load_component_document,
    load_component_profile,
)
from forgellm_governance.topology import ComputeKind, MemoryKind

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "components"


def test_load_component_document_constructs_immutable_profiles() -> None:
    document = load_component_document(FIXTURES / "valid-cache-draft.json", ROOT)
    assert document.profile_id == "cache-draft-components-v1"
    assert tuple(component.id for component in document.components) == ("confidence-head", "markov-head")

    confidence = document.components[0]
    assert confidence.resident_bytes == 9_441_280
    assert confidence.implementations[0].compute_kind is ComputeKind.CPU_GROUP
    assert confidence.implementations[0].allowed_memory_kinds == frozenset({MemoryKind.LLC})
    assert confidence.fallback().id == "cpu-generic"

    with pytest.raises(FrozenInstanceError):
        confidence.phase = "decode"  # type: ignore[misc]


def test_load_component_profile_compatibility_returns_tuple() -> None:
    components = load_component_profile(FIXTURES / "valid-cache-draft.json", ROOT)
    assert tuple(component.id for component in components) == ("confidence-head", "markov-head")


def test_missing_or_non_generic_fallback_is_rejected() -> None:
    with pytest.raises(ComponentValidationError) as caught:
        load_component_document(FIXTURES / "missing-fallback.json", ROOT)
    assert any("exactly one generic fallback" in issue.message for issue in caught.value.issues)
    assert any("fallback_implementation_id" in issue.message for issue in caught.value.issues)


def test_duplicate_implementation_id_is_rejected() -> None:
    with pytest.raises(ComponentValidationError) as caught:
        load_component_document(FIXTURES / "duplicate-implementation.json", ROOT)
    assert any("duplicate implementation id" in issue.message for issue in caught.value.issues)


def test_duplicate_component_id_is_rejected(tmp_path: Path) -> None:
    data = json.loads((FIXTURES / "valid-cache-draft.json").read_text(encoding="utf-8"))
    data["components"].append(dict(data["components"][0]))
    (tmp_path / "schemas").mkdir()
    (tmp_path / "schemas" / "component-profile.schema.json").write_text(
        (ROOT / "schemas" / "component-profile.schema.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    path = tmp_path / "duplicate-component.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ComponentValidationError) as caught:
        load_component_document(path, tmp_path)
    assert any("duplicate component id" in issue.message for issue in caught.value.issues)


def test_exact_profile_rejects_undeclared_approximate_only_flag(tmp_path: Path) -> None:
    data = json.loads((FIXTURES / "valid-cache-draft.json").read_text(encoding="utf-8"))
    data["components"][0]["implementations"][0]["approximate_only"] = True
    (tmp_path / "schemas").mkdir()
    (tmp_path / "schemas" / "component-profile.schema.json").write_text(
        (ROOT / "schemas" / "component-profile.schema.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    path = tmp_path / "approximate-only.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ComponentValidationError) as caught:
        load_component_document(path, tmp_path)
    assert any("Additional properties are not allowed" in issue.message for issue in caught.value.issues)
