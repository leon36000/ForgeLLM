"""Best-effort, non-privileged and privacy-aware hardware inventory."""

from __future__ import annotations

import json
import os
import platform
import subprocess
from collections.abc import Callable, Sequence
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
        return CommandResult(argv, "ok" if completed.returncode == 0 else "error", completed.returncode, completed.stdout, completed.stderr)
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
        "amd": _probe(runner, ["rocm-smi", "--showproductname", "--showmeminfo", "vram", "--showdriverversion", "--json"], timeout=10.0),
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


def write_hardware_inventory(path: Path | str, *, runner: Runner = run_command) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(collect_hardware_inventory(runner=runner), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output
