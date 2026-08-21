@AGENTS.md

# Claude Code additions

- Keep this file small; shared rules belong in `AGENTS.md` or `.claude/rules/`.
- Use Plan Mode for changes spanning more than one independently testable component.
- Verify loaded memory with `/memory` when instructions appear absent.
- Prefer repository-tracked state over automatic memory.
- Before editing, locate and obey any nested `CLAUDE.md`, `.claude/rules/`, or `AGENTS.md` files in scope.
- Do not auto-install MCP servers, hooks, skills, drivers, toolchains, or credentials without explicit owner authorization.

<!-- forgellm-loop-engineering:begin -->
For authorized bounded loops, use the project-local ForgeLLM Loop Engineering bridge. Git task packets and accepted ADRs remain authoritative; loop declarations may narrow but never widen SCOPE/VERIFY/privilege. No upstream installer, eval runner, Stop hook, shadow GOALS/STATUS state, or privileged operation is permitted by a loop.
<!-- forgellm-loop-engineering:end -->
