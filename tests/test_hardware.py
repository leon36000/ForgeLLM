from __future__ import annotations

from collections.abc import Sequence

from forgellm_governance.hardware import CommandResult, collect_hardware_inventory


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


def test_inventory_removes_link_layer_addresses_from_network_data() -> None:
    def runner(command: Sequence[str], timeout: float) -> CommandResult:
        argv = list(command)
        if argv[0] == "ip":
            return CommandResult(
                argv,
                "ok",
                0,
                '[{"ifname":"eth0","address":"aa:bb:cc:dd:ee:ff","broadcast":"ff:ff:ff:ff:ff:ff",'
                '"permaddr":"11:22:33:44:55:66","mtu":1500,"operstate":"UP"}]',
                "",
            )
        return CommandResult(argv, "unavailable", None, "", "command not found")

    inventory = collect_hardware_inventory(runner=runner)
    network = inventory["probes"]["network"]["data"]
    assert network == [{"ifname": "eth0", "mtu": 1500, "operstate": "UP"}]


def test_inventory_does_not_request_storage_mountpoints() -> None:
    commands: list[list[str]] = []

    def recorder(command: Sequence[str], timeout: float) -> CommandResult:
        argv = list(command)
        commands.append(argv)
        return CommandResult(argv, "unavailable", None, "", "command not found")

    collect_hardware_inventory(runner=recorder)
    storage_command = next(command for command in commands if command[0] == "lsblk")
    assert all("MOUNTPOINT" not in argument.upper() for argument in storage_command)
