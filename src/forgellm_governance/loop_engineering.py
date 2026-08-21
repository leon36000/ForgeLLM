"""Pure validation helpers for the bounded Loop Engineering bridge."""

from __future__ import annotations

import re
import shlex
from collections.abc import Sequence

_SHELL_TOKENS = frozenset({";", "&", "|", "<", ">"})
_WRAPPERS = frozenset({"env", "command", "exec", "xargs", "parallel", "timeout", "nice", "setsid"})
_FORBIDDEN_TOOLS = frozenset(
    {
        "aws",
        "az",
        "curl",
        "docker",
        "gcloud",
        "kubectl",
        "nc",
        "netcat",
        "npm",
        "pip",
        "pip3",
        "podman",
        "ssh",
        "sudo",
        "wget",
    }
)
_ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")


def _split_verify_tokens(command: object) -> list[str] | None:
    if not isinstance(command, str) or not command.strip():
        return None
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        return list(lexer)
    except ValueError:
        return None


def _verify_shell_structure_issue(tokens: Sequence[str], command: str) -> str | None:
    if any(token in _SHELL_TOKENS or all(char in _SHELL_TOKENS for char in token) for token in tokens):
        return "shell composition or redirection is forbidden; stop_and_escalate"
    if "\n" in command or "\r" in command or "`" in command or "$((" in command:
        return "shell evaluation syntax is forbidden; stop_and_escalate"
    if "$(" in command:
        return "command substitution is forbidden; stop_and_escalate"
    return None


def _verify_wrapper_issue(tokens: Sequence[str]) -> str | None:
    if any(_ASSIGNMENT.match(token) for token in tokens):
        return "environment assignments are forbidden; stop_and_escalate"
    if tokens and tokens[0] in _WRAPPERS:
        return "command wrappers are forbidden; stop_and_escalate"
    return None


def _verify_tool_authority_issue(tokens: Sequence[str]) -> str | None:
    if not tokens:
        return "empty or invalid command is rejected; stop_and_escalate"
    tool = tokens[0].rsplit("/", 1)[-1]
    if tool in _FORBIDDEN_TOOLS:
        return "secret or infrastructure clients are forbidden; stop_and_escalate"
    if tool == "gh" and len(tokens) > 1 and tokens[1:3] == ["auth", "status"]:
        return "credential inspection is forbidden; stop_and_escalate"
    return None


def _is_allowed_git(tokens: Sequence[str]) -> bool:
    if not tokens or tokens[0] != "git" or len(tokens) < 2:
        return False
    subcommand = tokens[1]
    if subcommand == "status":
        return all(token in {"--short", "--porcelain", "--branch"} for token in tokens[2:])
    if subcommand == "diff":
        return all(token in {"--check", "--stat", "--name-only", "--name-status"} for token in tokens[2:])
    if subcommand == "log":
        return all(not token.startswith("-") or token in {"--oneline", "--decorate", "--stat"} for token in tokens[2:])
    if subcommand == "show":
        return all(not token.startswith("-") or token in {"--stat", "--oneline", "--name-only"} for token in tokens[2:])
    if subcommand == "rev-parse":
        return all(token in {"--show-toplevel", "--show-prefix", "HEAD"} for token in tokens[2:])
    if subcommand == "branch":
        return tokens[2:] == ["--show-current"]
    return False


def _is_allowed_make(tokens: Sequence[str]) -> bool:
    return len(tokens) == 2 and tokens[0] == "make" and tokens[1] in {
        "ci",
        "lint",
        "test",
        "validate",
        "verify",
        "verify-speculative",
    }


def _is_allowed_gh(tokens: Sequence[str]) -> bool:
    if len(tokens) < 3 or tokens[:3] != ["gh", "pr", "view"]:
        return False
    return all(token == "--json" or token.startswith("--json=") or not token.startswith("-") for token in tokens[3:])


def validate_loop_verify_command(command: object) -> list[str]:
    """Return diagnostics for a command proposed as a read-only verifier."""
    tokens = _split_verify_tokens(command)
    if tokens is None:
        return ["command cannot be safely tokenized; stop_and_escalate"]
    text = command if isinstance(command, str) else ""
    for check in (
        lambda: _verify_shell_structure_issue(tokens, text),
        lambda: _verify_wrapper_issue(tokens),
        lambda: _verify_tool_authority_issue(tokens),
    ):
        issue = check()
        if issue:
            return [issue]
    if _is_allowed_git(tokens) or _is_allowed_make(tokens) or _is_allowed_gh(tokens):
        return []
    return ["command is not on the read-only verifier allowlist; stop_and_escalate"]
