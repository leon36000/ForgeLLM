"""Best-effort, non-privileged and privacy-aware hardware inventory."""

from __future__ import annotations

import json
import os
import platform
import subprocess
from collections.abc import Callable, Sequence
from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class CommandResult:
    command: list[str]
    status: str
    returncode: int | None
    stdout: str
    stderr: str


Runner = Callable[[Sequence[str], float], CommandResult]

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


def run_command(command: Sequence[str], timeout: float = 5.0) -> CommandResult:
    argv = list(command)
    try:
        completed = subprocess.run(
            argv,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, "LC_ALL": "C"},
        )
        return CommandResult(
            argv,
            "ok" if completed.returncode == 0 else "error",
            completed.returncode,
            completed.stdout,
            completed.stderr,
        )
    except FileNotFoundError:
        return CommandResult(argv, "unavailable", None, "", "command not found")
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return CommandResult(argv, "timeout", None, stdout, stderr)


def _try_json(result: CommandResult) -> Any:
    if result.status != "ok" or not result.stdout.strip():
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


def _probe(runner: Runner, command: Sequence[str], timeout: float = 5.0) -> dict[str, Any]:
    result = runner(command, timeout)
    parsed = _try_json(result)
    return {
        "command": result.command,
        "status": result.status,
        "returncode": result.returncode,
        "data": parsed if parsed is not None else result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def collect_hardware_inventory(*, runner: Runner = run_command) -> dict[str, Any]:
    """Collect topology evidence without privilege or stable device UUIDs."""

    os_release: dict[str, str] = {}
    release_path = Path("/etc/os-release")
    if release_path.exists():
        for line in release_path.read_text(encoding="utf-8", errors="replace").splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                os_release[key] = value.strip().strip('"')

    probes = {
        "cpu": _probe(runner, ["lscpu", "--json"]),
        "memory": _probe(runner, ["free", "-b"]),
        "pci": _probe(runner, ["lspci", "-nn"]),
        "nvidia": _probe(
            runner,
            [
                "nvidia-smi",
                "--query-gpu=name,driver_version,memory.total,pci.bus_id,compute_cap",
                "--format=csv,noheader,nounits",
            ],
            timeout=10.0,
        ),
        "amd": _probe(
            runner,
            ["rocm-smi", "--showproductname", "--showmeminfo", "vram", "--showdriverversion", "--json"],
            timeout=10.0,
        ),
        "network": _probe(runner, ["ip", "-j", "link"]),
        "storage": _probe(runner, ["lsblk", "-J", "-o", "NAME,TYPE,SIZE,ROTA,TRAN,FSTYPE,MOUNTPOINTS"]),
        "numa": _probe(runner, ["numactl", "--hardware"]),
    }

    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "privacy": {
            "hostname": "redacted",
            "device_uuids": "omitted",
            "network_addresses": "omitted",
            "note": "PCI bus locations and product names are retained for topology analysis.",
        },
        "system": {
            "os_release": os_release,
            "kernel": platform.release(),
            "machine": platform.machine(),
            "python": platform.python_version(),
        },
        "probes": probes,
    }


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


def _validated_public_output_path(root: Path | str, path: Path | str) -> Path:
    project_root = Path(root).resolve()
    artifacts_root = (project_root / "artifacts").resolve()
    requested = Path(path)
    candidate = requested if requested.is_absolute() else project_root / requested
    resolved = candidate.resolve(strict=False)
    if artifacts_root not in resolved.parents:
        raise ValueError("inventory output must be a file inside the repository artifacts directory")
    return resolved


def write_public_hardware_inventory(
    root: Path | str,
    path: Path | str,
    *,
    runner: Runner = run_command,
) -> Path:
    """Collect, sanitize and write one publication-safe inventory under root/artifacts."""

    output = _validated_public_output_path(root, path)
    inventory = sanitize_inventory(collect_hardware_inventory(runner=runner))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(inventory, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output
