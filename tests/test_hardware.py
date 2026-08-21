from __future__ import annotations

import json
import sys
from collections.abc import Sequence
from pathlib import Path

import pytest

from forgellm_governance import cli, hardware
from forgellm_governance.hardware import CommandResult, collect_hardware_inventory
from scripts import hardware_inventory as publication
from scripts.hardware_inventory import sanitize_inventory


def fake_runner(command: Sequence[str], timeout: float) -> CommandResult:
    argv = list(command)
    if argv[0] == "lscpu":
        return CommandResult(argv, "ok", 0, '{"lscpu":[{"field":"Architecture:","data":"x86_64"}]}', "")
    if argv[0] == "ip":
        return CommandResult(argv, "ok", 0, '[{"ifname":"lo"}]', "")
    if argv[0] == "lsblk":
        return CommandResult(argv, "ok", 0, '{"blockdevices":[]}', "")
    if argv[0] in {"nvidia-smi", "rocm-smi", "numactl"}:
        return CommandResult(argv, "unavailable", None, "", "command not found")
    return CommandResult(argv, "ok", 0, "example", "")


def privacy_runner(command: Sequence[str], timeout: float) -> CommandResult:
    argv = list(command)
    if argv[0] == "ip":
        return CommandResult(
            argv,
            "ok",
            0,
            '[{"ifname":"eth0","address":"REMOVE-ME","broadcast":"REMOVE-ME",'
            '"permaddr":"REMOVE-ME","mtu":1500,"operstate":"UP"}]',
            "",
        )
    if argv[0] == "lsblk":
        return CommandResult(
            argv,
            "ok",
            0,
            '{"blockdevices":[{"name":"disk0","mountpoints":["REMOVE-ME"],'
            '"children":[{"name":"part0","mountpoint":"REMOVE-ME"}]}]}',
            "",
        )
    return CommandResult(argv, "unavailable", None, "", "command not found")


def test_inventory_is_redacted_and_tolerates_missing_gpu_tools() -> None:
    inventory = collect_hardware_inventory(runner=fake_runner)
    assert inventory["privacy"]["hostname"] == "redacted"
    assert inventory["privacy"]["device_uuids"] == "omitted"
    assert inventory["probes"]["nvidia"]["status"] == "unavailable"
    assert inventory["probes"]["amd"]["status"] == "unavailable"
    assert inventory["probes"]["cpu"]["data"]["lscpu"][0]["data"] == "x86_64"


def test_inventory_never_queries_uuid_fields() -> None:
    commands: list[list[str]] = []

    def recorder(command: Sequence[str], timeout: float) -> CommandResult:
        argv = list(command)
        commands.append(argv)
        return CommandResult(argv, "unavailable", None, "", "command not found")

    collect_hardware_inventory(runner=recorder)
    flattened = " ".join(" ".join(command).lower() for command in commands)
    assert "uuid" not in flattened


def test_published_inventory_keeps_only_allowed_network_fields() -> None:
    inventory = sanitize_inventory(collect_hardware_inventory(runner=privacy_runner))
    network = inventory["probes"]["network"]["data"]
    assert network == [{"ifname": "eth0", "mtu": 1500, "operstate": "UP"}]


def test_published_inventory_removes_storage_mount_fields_recursively() -> None:
    inventory = sanitize_inventory(collect_hardware_inventory(runner=privacy_runner))
    serialized = json.dumps(inventory["probes"]["storage"]["data"]).casefold()
    assert "mountpoint" not in serialized
    assert "remove-me" not in serialized


def test_published_inventory_fails_closed_on_unparsed_structured_probes() -> None:
    raw = {
        "probes": {
            "network": {"status": "ok", "data": "REMOVE-ME", "stderr": "REMOVE-ME"},
            "storage": {"status": "ok", "data": "REMOVE-ME", "stderr": "REMOVE-ME"},
        }
    }

    inventory = sanitize_inventory(raw)
    for name in ("network", "storage"):
        probe = inventory["probes"][name]
        assert probe["status"] == "error"
        assert probe["data"] is None
        assert probe["stderr"] == ""
    assert "REMOVE-ME" not in json.dumps(inventory)


def test_inventory_output_cannot_escape_artifacts(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(publication, "_PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(publication, "_ARTIFACTS_ROOT", (tmp_path / "artifacts").resolve())
    monkeypatch.setattr(publication, "collect_hardware_inventory", lambda: {"probes": {}})

    outside = tmp_path / "outside.json"
    with pytest.raises(ValueError, match="artifacts"):
        publication.write_sanitized_inventory(outside)
    assert not outside.exists()


def test_canonical_public_inventory_writer_sanitizes_and_confines_output(tmp_path: Path) -> None:
    writer = getattr(hardware, "write_public_hardware_inventory", None)
    assert callable(writer), "canonical publication-safe hardware writer is missing"

    output = writer(tmp_path, Path("artifacts/published.json"), runner=privacy_runner)
    payload = json.loads(output.read_text(encoding="utf-8"))
    serialized = json.dumps(payload).casefold()
    assert "remove-me" not in serialized
    assert payload["probes"]["network"]["data"] == [
        {"ifname": "eth0", "mtu": 1500, "operstate": "UP"}
    ]
    assert output == (tmp_path / "artifacts/published.json").resolve()

    outside = tmp_path / "outside.json"
    with pytest.raises(ValueError, match="artifacts"):
        writer(tmp_path, outside, runner=privacy_runner)
    assert not outside.exists()


def test_cli_inventory_routes_through_canonical_public_writer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    calls: list[tuple[Path, Path]] = []

    def safe_writer(root: Path, output: Path) -> Path:
        calls.append((root, output))
        destination = root / output
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text("{}\n", encoding="utf-8")
        return destination

    def reject_raw_writer(*args: object, **kwargs: object) -> Path:
        raise AssertionError("CLI called the raw unsanitized hardware writer")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "write_public_hardware_inventory", safe_writer, raising=False)
    monkeypatch.setattr(cli, "write_hardware_inventory", reject_raw_writer, raising=False)
    monkeypatch.setattr(
        sys,
        "argv",
        ["forgellm-governance", "inventory", "--output", "artifacts/cli.json"],
    )

    assert cli.main() == 0
    assert calls == [(tmp_path, Path("artifacts/cli.json"))]
    assert capsys.readouterr().out.strip() == str(tmp_path / "artifacts/cli.json")
