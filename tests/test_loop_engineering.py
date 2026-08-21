import pytest

from forgellm_governance.loop_engineering import validate_loop_verify_command


@pytest.mark.parametrize("command", [
    "make ci && git push origin main",
    "make ci; gh pr merge 37",
    "make ci > /tmp/result.log",
    "env git push origin main",
    "command git status",
    "git add README.md",
    "git branch -D review-head",
    "gh workflow run release.yml",
    "kubectl get secret sonar-token",
])
def test_firewall_rejects_composition_wrappers_mutations_and_privileged_reads(command):
    messages = validate_loop_verify_command(command)
    assert messages
    assert "stop_and_escalate" in messages[0]


@pytest.mark.parametrize("command", [
    "git status --short",
    "git diff --check",
    "gh pr view 37 --json state",
])
def test_firewall_allows_explicit_read_only_commands(command):
    assert validate_loop_verify_command(command) == []
