"""Create a portable session-continuity snapshot from canonical repository state."""

from __future__ import annotations

import hashlib
import subprocess
from datetime import UTC, datetime
from pathlib import Path


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(["git", "-C", str(root), *args], check=False, capture_output=True, text=True, timeout=5)
    if completed.returncode != 0:
        return "unavailable"
    return completed.stdout.strip() or "empty"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def create_session_snapshot(root: Path | str, output: Path | str) -> Path:
    root = Path(root).resolve()
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    state_paths = [
        root / "docs/state/CURRENT_STATE.md",
        root / "docs/state/DECISIONS.md",
        root / "docs/state/RISKS.md",
        root / "docs/state/OPEN_QUESTIONS.md",
        root / "docs/state/HANDOFF.md",
    ]
    generated = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    lines = [
        "# ForgeLLM Session Continuity Snapshot",
        "",
        f"Generated: `{generated}`",
        "Repository: `ForgeLLM`",
        f"Branch: `{_git(root, 'branch', '--show-current')}`",
        f"Commit: `{_git(root, 'rev-parse', 'HEAD')}`",
        f"Dirty status: `{_git(root, 'status', '--short')}`",
        "",
        "## Canonical state files",
        "",
    ]
    for path in state_paths:
        if path.exists():
            lines.append(f"- `{path.relative_to(root)}` — SHA-256 `{_sha256(path)}`")
        else:
            lines.append(f"- `{path.relative_to(root)}` — missing")
    lines.extend(["", "## Current state projection", ""])
    current_state = state_paths[0]
    lines.append(current_state.read_text(encoding="utf-8") if current_state.exists() else "Current state file is missing.")
    output.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return output
