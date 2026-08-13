from __future__ import annotations

import json
from collections.abc import Sequence

from forgellm_governance.hardware import CommandResult, collect_hardware_inventory
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
    def runner(command: Sequence[str], timeout: float) -> CommandResult:
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
        return CommandResult(argv, "unavailable", None, "", "command not found")

    inventory = sanitize_inventory(collect_hardware_inventory(runner=runner))
    network = inventory["probes"]["network"]["data"]
    assert network == [{"ifname": "eth0", "mtu": 1500, "operstate": "UP"}]


def test_published_inventory_removes_storage_mount_fields_recursively() -> None:
    def runner(command: Sequence[str], timeout: float) -> CommandResult:
        argv = list(command)
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

    inventory = sanitize_inventory(collect_hardware_inventory(runner=runner))
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
