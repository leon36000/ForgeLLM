"""Strict JSON document loading, validation, hashing, and path confinement."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


@dataclass(frozen=True, slots=True, order=True)
class DocumentIssue:
    """One deterministic issue for an external JSON document."""

    path: str
    message: str

    def render(self) -> str:
        return f"{self.path}: {self.message}"


def _json_pointer(parts: object) -> str:
    escaped = [str(part).replace("~", "~0").replace("/", "~1") for part in parts]  # type: ignore[arg-type]
    return "/" + "/".join(escaped) if escaped else ""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def load_json_mapping(path: Path) -> Mapping[str, Any]:
    """Load one UTF-8 JSON object, rejecting malformed or non-object roots."""

    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ValueError(f"file does not exist: {path}") from exc
    except UnicodeDecodeError as exc:
        raise ValueError(f"file is not valid UTF-8: {path}") from exc

    try:
        value = json.loads(text, object_pairs_hook=_reject_duplicate_keys)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}") from exc
    if not isinstance(value, Mapping):
        raise ValueError("JSON root must be an object")
    return value


def validate_instance(
    instance: Mapping[str, Any],
    schema_path: Path,
    source_path: Path,
) -> tuple[DocumentIssue, ...]:
    """Validate an instance and return deterministically ordered issues."""

    schema = load_json_mapping(schema_path)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    issues = [
        DocumentIssue(f"{source_path}{_json_pointer(error.absolute_path)}", error.message)
        for error in validator.iter_errors(instance)
    ]
    return tuple(sorted(issues))


def sha256_file(path: Path) -> str:
    """Return the lowercase SHA-256 digest of a file."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require_within(path: Path, parent: Path, *, message: str) -> Path:
    resolved = path.resolve(strict=False)
    parent_resolved = parent.resolve(strict=True)
    try:
        resolved.relative_to(parent_resolved)
    except ValueError as exc:
        raise ValueError(message) from exc
    return resolved


def resolve_input_file(root: Path, path: Path) -> Path:
    """Resolve an existing repository input without allowing traversal/symlink escape."""

    root_resolved = root.resolve(strict=True)
    candidate = path if path.is_absolute() else root_resolved / path
    resolved = _require_within(candidate, root_resolved, message="path escapes repository root")
    if not resolved.exists():
        raise ValueError(f"input file does not exist: {path}")
    if not resolved.is_file():
        raise ValueError(f"input path is not a file: {path}")
    return resolved


def resolve_artifact_output(root: Path, path: Path) -> Path:
    """Resolve an output path strictly beneath the repository artifacts directory."""

    root_resolved = root.resolve(strict=True)
    artifacts_root = root_resolved / "artifacts"
    if artifacts_root.is_symlink():
        raise ValueError("artifacts directory cannot be a symlink")
    artifacts_root.mkdir(parents=False, exist_ok=True)
    candidate = path if path.is_absolute() else root_resolved / path

    if candidate.is_symlink():
        raise ValueError("output path cannot be a symlink")

    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(artifacts_root.resolve(strict=True))
    except ValueError as exc:
        raise ValueError("output path must be beneath artifacts") from exc

    if resolved.exists() and resolved.is_dir():
        raise ValueError("output path cannot be a directory")
    return resolved
