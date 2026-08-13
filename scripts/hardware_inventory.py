#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from forgellm_governance.hardware import collect_hardware_inventory

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_ARTIFACTS_ROOT = (_PROJECT_ROOT / "artifacts").resolve()
_NETWORK_PUBLIC_FIELDS = frozenset(
    {
        "ifindex",
        "ifname",
        "flags",
        "mtu",
        "qdisc",
        "operstate",
        "linkmode",
        "group",
        "txqlen",
        "link_type",
    }
)
_STORAGE_OMIT_FIELDS = frozenset({"mountpoint", "mountpoints"})


def _remove_fields(value: Any, omitted: frozenset[str]) -> Any:
    if isinstance(value, list):
        return [_remove_fields(item, omitted) for item in value]
    if isinstance(value, dict):
        return {
            key: _remove_fields(item, omitted)
            for key, item in value.items()
            if str(key).casefold() not in omitted
        }
    return value


def _sanitize_json_probe(probe: dict[str, Any], *, expected_type: type) -> None:
    if isinstance(probe.get("data"), expected_type):
        probe["stderr"] = ""
        return
    probe["data"] = None
    probe["stderr"] = ""
    if probe.get("status") == "ok":
        probe["status"] = "error"


def sanitize_inventory(inventory: dict[str, Any]) -> dict[str, Any]:
    """Return a publication-safe copy of a collected inventory."""

    published = deepcopy(inventory)
    probes = published.get("probes", {})

    network = probes.get("network")
    if isinstance(network, dict):
        _sanitize_json_probe(network, expected_type=list)
        data = network.get("data")
        if isinstance(data, list):
            network["data"] = [
                {key: value for key, value in item.items() if key in _NETWORK_PUBLIC_FIELDS}
                for item in data
                if isinstance(item, dict)
            ]

    storage = probes.get("storage")
    if isinstance(storage, dict):
        _sanitize_json_probe(storage, expected_type=dict)
        data = storage.get("data")
        if isinstance(data, dict):
            storage["data"] = _remove_fields(data, _STORAGE_OMIT_FIELDS)

    return published


def _validated_output_path(path: Path) -> Path:
    candidate = path if path.is_absolute() else _PROJECT_ROOT / path
    resolved = candidate.resolve(strict=False)
    if _ARTIFACTS_ROOT not in resolved.parents:
        raise ValueError("inventory output must be a file inside the repository artifacts directory")
    return resolved


def write_sanitized_inventory(path: Path) -> Path:
    output = _validated_output_path(path)
    inventory = sanitize_inventory(collect_hardware_inventory())
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(inventory, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a redacted, non-privileged ForgeLLM hardware inventory.")
    parser.add_argument("--output", type=Path, default=Path("artifacts/hardware-local.json"))
    args = parser.parse_args()
    print(write_sanitized_inventory(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
