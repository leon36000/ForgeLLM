from __future__ import annotations

from pathlib import Path

import pytest

from scripts.hash_mobile_context import EXPECTED_FILES, build_records

ROOT = Path(__file__).resolve().parents[1]


def test_mobile_context_has_exact_canonical_files() -> None:
    records = build_records(ROOT)
    assert len(records) == len(EXPECTED_FILES) == 5
    for name, record in zip(EXPECTED_FILES, records, strict=True):
        digest, path = record.split("  ", maxsplit=1)
        assert len(digest) == 64
        assert int(digest, 16) >= 0
        assert path == f"chatgpt/mobile-core/{name}"


def test_mobile_context_rejects_extra_markdown_file(tmp_path: Path) -> None:
    mobile_dir = tmp_path / "chatgpt" / "mobile-core"
    mobile_dir.mkdir(parents=True)
    for name in EXPECTED_FILES:
        (mobile_dir / name).write_text(name, encoding="utf-8")
    (mobile_dir / "EXTRA.md").write_text("unexpected", encoding="utf-8")

    with pytest.raises(ValueError, match="mobile bundle mismatch"):
        build_records(tmp_path)
