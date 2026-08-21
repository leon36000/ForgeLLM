#!/usr/bin/env python3
"""Validate the immutable repository catalog for bounded Loop Engineering runs."""

from __future__ import annotations

import argparse
import hashlib
import posixpath
import re
import subprocess
from collections.abc import Mapping
from pathlib import Path

import yaml

from forgellm_governance.loop_engineering import (
    validate_loop_declaration,
    validate_loop_receipt,
    validate_vendor_provenance,
)

TASK_PACKET_PATH = Path("tasks/open/P0-T10-bounded-loop-engineering.yaml")
DECLARATION_PREFIX = Path("artifacts/governance/loop-engineering/declarations")
RECEIPT_PREFIX = Path("artifacts/governance/loop-engineering/receipts")
INDEX_PATH = Path("artifacts/governance/loop-engineering/receipt-index.yaml")
TEMPLATE_RECEIPT_PATH = RECEIPT_PREFIX / "TEMPLATE.yaml"

_FULL_SHA = re.compile(r"^[0-9a-f]{40}$")
_INDEX_HEADER_FIELDS = frozenset({"schema_version", "project", "task_id", "runs"})
_INDEX_RECORD_FIELDS = frozenset(
    {
        "run_id",
        "declaration_path",
        "declaration_source_commit",
        "declaration_source_blob_sha",
        "receipt_path",
        "receipt_schema_version",
    }
)


def _key_set_issue(data: Mapping[object, object], expected: frozenset[str], name: str) -> list[str]:
    actual = set(data)
    issues: list[str] = []
    missing = sorted(expected - actual)
    extra = sorted(actual - expected, key=str)
    if missing:
        issues.append(f"{name} is missing required fields: {', '.join(missing)}")
    if extra:
        issues.append(f"{name} contains unknown fields: {', '.join(map(str, extra))}")
    return issues


def _safe_relative_yaml_path(value: object) -> str | None:
    if not isinstance(value, str) or not value or "\x00" in value or "\\" in value:
        return None
    if value.startswith(("/", "~")):
        return None
    parts = value.split("/")
    if any(not part or part in {".", ".."} for part in parts):
        return None
    normalized = posixpath.normpath(value)
    if normalized in {"", ".", ".."} or normalized.startswith("../"):
        return None
    if not normalized.endswith((".yaml", ".yml")):
        return None
    return normalized


def _under_prefix(path: str, prefix: Path) -> bool:
    prefix_text = prefix.as_posix().rstrip("/")
    return path.startswith(f"{prefix_text}/")


def _valid_sha(value: object) -> bool:
    return isinstance(value, str) and bool(_FULL_SHA.fullmatch(value)) and any(char != "0" for char in value)


def _git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data, usedforsecurity=False).hexdigest()


def _git_read(root: Path, arguments: list[str]) -> subprocess.CompletedProcess[str]:
    if not arguments or any("\x00" in argument or "\n" in argument or "\r" in argument for argument in arguments):
        return subprocess.CompletedProcess(arguments, 2, "", "unsafe Git argument")
    # NOSONAR: shell=False plus strict SHA/path token validation prevents command interpretation.
    return subprocess.run(  # NOSONAR
        ["git", "-C", str(root), *arguments],
        capture_output=True,
        text=True,
        check=False,
        shell=False,
    )


def _ensure_revision(root: Path, revision: str) -> bool:
    check = _git_read(root, ["cat-file", "-e", f"{revision}^{{commit}}"])
    if check.returncode == 0:
        return True
    shallow_marker = root / ".git" / "shallow"
    if not shallow_marker.is_file():
        return False
    fetch = _git_read(root, ["fetch", "--no-tags", "--quiet", "origin", revision])
    if fetch.returncode != 0:
        return False
    return _git_read(root, ["cat-file", "-e", f"{revision}^{{commit}}"]).returncode == 0


def _validate_committed_declaration(
    root: Path,
    commit: object,
    declaration_path: str,
    expected_blob: object,
    issues: list[str],
    prefix: str,
) -> None:
    if not isinstance(commit, str) or not _valid_sha(commit) or not isinstance(expected_blob, str):
        return
    if not _ensure_revision(root, commit):
        issues.append(f"{prefix}.declaration_source_commit must exist in the repository")
        return
    tree_check = _git_read(root, ["ls-tree", "-r", "--full-tree", commit, "--", declaration_path])
    records = [line for line in tree_check.stdout.splitlines() if line]
    if tree_check.returncode != 0 or len(records) != 1:
        issues.append(f"{prefix}.declaration_source_commit must contain {declaration_path}")
        return
    metadata, recorded_path = records[0].split("\t", 1)
    fields = metadata.split()
    if len(fields) != 3 or fields[0] != "100644" or fields[1] != "blob" or fields[2] != expected_blob:
        issues.append(f"{prefix}.declaration_source_commit must bind {declaration_path} to its declared blob")
    if recorded_path != declaration_path:
        issues.append(f"{prefix}.declaration_source_commit path binding is not exact")


def _filesystem_path(root: Path, relative: str) -> Path:
    root_resolved = root.resolve()
    candidate = (root_resolved / Path(*relative.split("/"))).resolve()
    candidate.relative_to(root_resolved)
    return candidate


def _load_mapping(
    root: Path, relative: Path | str, issues: list[str], label: str
) -> tuple[Mapping[object, object] | None, bytes | None]:
    relative_text = relative.as_posix() if isinstance(relative, Path) else relative
    try:
        path = _filesystem_path(root, relative_text)
    except (OSError, RuntimeError, ValueError):
        issues.append(f"{label} path is not safely contained under repository root: {relative_text}")
        return None, None
    if path.is_symlink():
        issues.append(f"{label} must not be a symlink: {relative_text}")
        return None, None
    try:
        data = path.read_bytes()
    except OSError as exc:
        issues.append(f"{label} cannot be read at {relative_text}: {exc}")
        return None, None
    try:
        loaded = yaml.safe_load(data)
    except yaml.YAMLError as exc:
        issues.append(f"{label} is not valid safe YAML at {relative_text}: {exc}")
        return None, data
    if not isinstance(loaded, Mapping):
        issues.append(f"{label} must contain a YAML mapping at {relative_text}")
        return None, data
    return loaded, data


def _discover_yaml_files(root: Path, prefix: Path, issues: list[str], label: str) -> set[str]:
    directory = root / prefix
    try:
        entries = list(directory.rglob("*")) if directory.is_dir() else []
    except OSError as exc:
        issues.append(f"{label} prefix cannot be scanned: {exc}")
        return set()
    discovered: set[str] = set()
    for path in entries:
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if path.suffix.casefold() not in {".yaml", ".yml"}:
            continue
        if path.is_symlink():
            issues.append(f"{label} file must not be a symlink: {relative}")
        discovered.add(relative)
    return discovered


def _indexed_path(
    value: object, field: str, prefix: Path, issues: list[str], *, allow_template: bool = False
) -> str | None:
    parsed = _safe_relative_yaml_path(value)
    if parsed is None:
        issues.append(f"{field} must be a safe relative YAML path")
        return None
    if not _under_prefix(parsed, prefix):
        issues.append(f"{field} must be contained under {prefix.as_posix()}")
        return None
    if not allow_template and parsed == TEMPLATE_RECEIPT_PATH.as_posix():
        issues.append(f"{field} must not index {TEMPLATE_RECEIPT_PATH.as_posix()}")
        return None
    return parsed


def _index_record_identity(
    record: Mapping[object, object], prefix: str, issues: list[str]
) -> tuple[str | None, str | None, str | None]:
    issues.extend(_key_set_issue(record, _INDEX_RECORD_FIELDS, prefix))
    run_id = record.get("run_id")
    if not isinstance(run_id, str) or not run_id.strip():
        issues.append(f"{prefix}.run_id must be a non-empty string")
    declaration_path = _indexed_path(
        record.get("declaration_path"), f"{prefix}.declaration_path", DECLARATION_PREFIX, issues
    )
    receipt_path = _indexed_path(record.get("receipt_path"), f"{prefix}.receipt_path", RECEIPT_PREFIX, issues)
    for field in ("declaration_source_commit", "declaration_source_blob_sha"):
        if not _valid_sha(record.get(field)):
            issues.append(f"{prefix}.{field} must be a lowercase non-zero full 40-character SHA-1")
    if record.get("receipt_schema_version") != "1.0":
        issues.append(f"{prefix}.receipt_schema_version must be '1.0'")
    return run_id if isinstance(run_id, str) else None, declaration_path, receipt_path


def _load_index_declaration(
    root: Path, record: Mapping[object, object], prefix: str, declaration_path: str | None, issues: list[str]
) -> Mapping[object, object] | None:
    if declaration_path is not None:
        declaration, declaration_bytes = _load_mapping(
            root, declaration_path, issues, f"declaration {declaration_path}"
        )
        if declaration_bytes is not None and _valid_sha(record.get("declaration_source_blob_sha")):
            actual_blob_sha = _git_blob_sha(declaration_bytes)
            if actual_blob_sha != record.get("declaration_source_blob_sha"):
                issues.append(f"{prefix}.declaration_source_blob_sha does not match declaration {declaration_path}")
        _validate_committed_declaration(
            root,
            record.get("declaration_source_commit"),
            declaration_path,
            record.get("declaration_source_blob_sha"),
            issues,
            prefix,
        )
        return declaration
    return None


def _validate_index_declaration(
    declaration: Mapping[object, object] | None,
    declaration_path: str | None,
    receipt_path: str | None,
    task_packet: Mapping[object, object],
    issues: list[str],
) -> None:
    if declaration is None:
        return
    issues.extend(
        f"declaration {declaration_path}: {message}" for message in validate_loop_declaration(declaration, task_packet)
    )
    declared_receipt = _safe_relative_yaml_path(declaration.get("RECEIPT"))
    if receipt_path is not None and declared_receipt != receipt_path:
        issues.append(f"declaration {declaration_path}: RECEIPT must match indexed receipt_path {receipt_path}")


def _validate_index_receipt(
    root: Path,
    receipt_path: str | None,
    declaration_path: str | None,
    declaration: Mapping[object, object] | None,
    prefix: str,
    record: Mapping[object, object],
    issues: list[str],
) -> None:
    if receipt_path is not None:
        receipt, _ = _load_mapping(root, receipt_path, issues, f"receipt {receipt_path}")
    else:
        receipt = None
    if receipt is not None:
        issues.extend(
            f"receipt {receipt_path}: {message}" for message in validate_loop_receipt(receipt, declaration or {})
        )
        _validate_receipt_changed_paths(root, receipt, issues)
        if receipt.get("schema_version") != record.get("receipt_schema_version"):
            issues.append(f"{prefix}.receipt_schema_version must match receipt {receipt_path}")


def _validate_index_artifacts(
    root: Path,
    record: Mapping[object, object],
    prefix: str,
    declaration_path: str | None,
    receipt_path: str | None,
    task_packet: Mapping[object, object],
    issues: list[str],
) -> None:
    declaration = _load_index_declaration(root, record, prefix, declaration_path, issues)
    _validate_index_declaration(declaration, declaration_path, receipt_path, task_packet, issues)
    _validate_index_receipt(root, receipt_path, declaration_path, declaration, prefix, record, issues)


def _validate_index_record(
    root: Path,
    record: object,
    index_number: int,
    task_packet: Mapping[object, object],
    issues: list[str],
) -> tuple[str | None, str | None, str | None]:
    prefix = f"index.runs[{index_number}]"
    if not isinstance(record, Mapping):
        issues.append(f"{prefix} must be a YAML mapping")
        return None, None, None
    run_id, declaration_path, receipt_path = _index_record_identity(record, prefix, issues)
    _validate_index_artifacts(root, record, prefix, declaration_path, receipt_path, task_packet, issues)
    return run_id, declaration_path, receipt_path


def _coverage_issue(indexed: set[str], discovered: set[str], kind: str) -> str | None:
    missing = sorted(discovered - indexed)
    extra = sorted(indexed - discovered)
    if not missing and not extra:
        return None
    details: list[str] = []
    if missing:
        details.append(f"missing {', '.join(missing)}")
    if extra:
        details.append(f"unexpected {', '.join(extra)}")
    return f"index must cover every committed {kind} exactly: {'; '.join(details)}"


def _validate_receipt_changed_paths(root: Path, receipt: Mapping[object, object], issues: list[str]) -> None:
    base_commit = receipt.get("base_commit")
    final_commit = receipt.get("final_commit")
    if not _valid_sha(base_commit) or not _valid_sha(final_commit):
        return
    result = _git_read(
        root,
        ["diff", "--name-only", "--diff-filter=ACDMRTUXB", f"{base_commit}..{final_commit}", "--"],
    )
    if result.returncode != 0:
        issues.append("receipt base_commit..final_commit must be a readable Git revision range")
        return
    actual = {line for line in result.stdout.splitlines() if line}
    claimed = {path for path in receipt.get("changed_paths", []) if isinstance(path, str)}
    if actual != claimed:
        issues.append(
            "receipt changed_paths must exactly match Git base_commit..final_commit; "
            f"missing={sorted(actual - claimed)}, extra={sorted(claimed - actual)}"
        )


def _load_catalog_mappings(root: Path, issues: list[str]) -> tuple[Mapping[object, object], Mapping[object, object]]:
    task_packet, _ = _load_mapping(root, TASK_PACKET_PATH, issues, "task packet")
    if task_packet is None:
        task_packet = {}
    index, _ = _load_mapping(root, INDEX_PATH, issues, "receipt index")
    if index is None:
        index = {}
    return task_packet, index


def _validate_catalog_header(
    task_packet: Mapping[object, object], index: Mapping[object, object], issues: list[str]
) -> None:
    if task_packet.get("task_id") != "P0-T10":
        issues.append("task packet task_id must be 'P0-T10'")
    issues.extend(_key_set_issue(index, _INDEX_HEADER_FIELDS, "receipt index"))
    if index.get("schema_version") != "1.0":
        issues.append("receipt index schema_version must be '1.0'")
    if index.get("project") != "ForgeLLM":
        issues.append("receipt index project must be 'ForgeLLM'")
    if index.get("task_id") != "P0-T10":
        issues.append("receipt index task_id must be 'P0-T10'")


def _validate_catalog_records(
    root: Path, index: Mapping[object, object], task_packet: Mapping[object, object], issues: list[str]
) -> tuple[set[str], set[str], set[str]]:
    indexed_declarations: set[str] = set()
    indexed_receipts: set[str] = set()
    run_ids: set[str] = set()
    runs = index.get("runs")
    if not isinstance(runs, list):
        issues.append("receipt index runs must be a list")
        runs = []
    for index_number, record in enumerate(runs):
        run_id, declaration_path, receipt_path = _validate_index_record(root, record, index_number, task_packet, issues)
        if run_id is not None:
            if run_id in run_ids:
                issues.append("run_id values must be unique")
            run_ids.add(run_id)
        if declaration_path is not None:
            if declaration_path in indexed_declarations:
                issues.append("declaration_path values must be unique")
            indexed_declarations.add(declaration_path)
        if receipt_path is not None:
            if receipt_path in indexed_receipts:
                issues.append("receipt_path values must be unique")
            indexed_receipts.add(receipt_path)
    return indexed_declarations, indexed_receipts, run_ids


def validate_repository(root: Path) -> list[str]:
    """Return diagnostics for the fixed P0-T10 loop declaration/receipt catalog."""
    root = Path(root)
    issues: list[str] = []
    task_packet, index = _load_catalog_mappings(root, issues)
    _validate_catalog_header(task_packet, index, issues)
    indexed_declarations, indexed_receipts, _ = _validate_catalog_records(root, index, task_packet, issues)

    discovered_declarations = _discover_yaml_files(root, DECLARATION_PREFIX, issues, "declaration")
    discovered_receipts = _discover_yaml_files(root, RECEIPT_PREFIX, issues, "receipt")
    discovered_receipts.discard(TEMPLATE_RECEIPT_PATH.as_posix())
    for message in (
        _coverage_issue(indexed_declarations, discovered_declarations, "immutable declaration"),
        _coverage_issue(indexed_receipts, discovered_receipts, "final receipt"),
    ):
        if message:
            issues.append(message)
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the ForgeLLM P0-T10 loop receipt catalog.")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    issues = [*validate_vendor_provenance(args.root), *validate_repository(args.root)]
    for issue in issues:
        print(issue)
    if issues:
        print(f"FAILED: {len(issues)} issue(s)")
        return 1
    print("OK: ForgeLLM loop engineering catalog is consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
