from __future__ import annotations

from pathlib import Path

import pytest

from forgellm_governance import snapshot


def _write_canonical_state(root: Path) -> None:
    state_dir = root / "docs/state"
    state_dir.mkdir(parents=True)
    for name in ("CURRENT_STATE.md", "DECISIONS.md", "RISKS.md", "OPEN_QUESTIONS.md", "HANDOFF.md"):
        (state_dir / name).write_text(f"# {name}\n", encoding="utf-8")


def test_session_snapshot_does_not_serialize_absolute_repository_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "private-user-name" / "ForgeLLM"
    _write_canonical_state(root)

    def fake_git(_: Path, *args: str) -> str:
        commands = {
            ("branch", "--show-current"): "main",
            ("rev-parse", "HEAD"): "a" * 40,
            ("status", "--short"): "empty",
        }
        return commands[args]

    monkeypatch.setattr(snapshot, "_git", fake_git)
    output = root / "artifacts/session-snapshot.md"
    result = snapshot.create_session_snapshot(root, output)
    text = result.read_text(encoding="utf-8")

    assert result == output
    assert str(root) not in text
    assert "private-user-name" not in text
    assert "Repository: `ForgeLLM`" in text
    assert "Branch: `main`" in text
    assert f"Commit: `{'a' * 40}`" in text
    assert "`docs/state/CURRENT_STATE.md`" in text


def test_session_snapshot_does_not_publish_dirty_file_names(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "ForgeLLM"
    _write_canonical_state(root)

    def fake_git(_: Path, *args: str) -> str:
        commands = {
            ("branch", "--show-current"): "main",
            ("rev-parse", "HEAD"): "b" * 40,
            ("status", "--short"): "?? private-customer-name.txt\n M docs/state/CURRENT_STATE.md",
        }
        return commands[args]

    monkeypatch.setattr(snapshot, "_git", fake_git)
    output = root / "artifacts/session-snapshot.md"
    text = snapshot.create_session_snapshot(root, output).read_text(encoding="utf-8")

    assert "private-customer-name" not in text
    assert "docs/state/CURRENT_STATE.md" not in text.split("Dirty status:", maxsplit=1)[1].split(
        "## Canonical state files",
        maxsplit=1,
    )[0]
    assert "Dirty status: `dirty`" in text
