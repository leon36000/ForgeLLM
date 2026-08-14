from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_NAMES = (
    "topology.schema.json",
    "component-profile.schema.json",
    "placement-result.schema.json",
)


def test_cache_aware_schemas_are_valid_draft_2020_12() -> None:
    for name in SCHEMA_NAMES:
        schema = json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["additionalProperties"] is False


def test_cache_aware_schemas_reject_undeclared_top_level_properties() -> None:
    for name in SCHEMA_NAMES:
        schema = json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))
        assert schema["additionalProperties"] is False
