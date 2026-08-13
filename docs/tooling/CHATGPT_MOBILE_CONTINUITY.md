# ChatGPT Mobile Continuity for ForgeLLM

## Principle

ChatGPT project memory is useful context, but ForgeLLM does not depend on an invisible or exhaustive memory list. The five-file mobile core and Git repository are explicit, inspectable and replaceable.

## Installation

1. Open the ForgeLLM project in ChatGPT mobile or web.
2. Copy `chatgpt/PROJECT_INSTRUCTIONS.txt` into the project instructions.
3. Upload the five files listed in `chatgpt/UPLOAD_MANIFEST.md`.
4. Start the next discussion with `chatgpt/SESSION_BOOTSTRAP_PROMPT.md`.
5. Confirm the continuity readback before approving work.

## Session lifecycle

### Start

The assistant reads all five files, reports state ID, phase, next authorized task, accepted decisions, risks, non-goals and contradictions. Unknowns remain explicit.

### During work

New facts are tied to primary sources or repository evidence. Architecture decisions become ADR proposals. Experiments receive IDs and raw artifacts. Out-of-scope discoveries enter the question registry.

### Close

Use `chatgpt/SESSION_CLOSEOUT_PROMPT.md`. Save the generated patches in Git. Regenerate and replace `03_FORGELLM_STATE_AND_DECISIONS.md`; update other mobile files only when their stable content changed.

## Conflict handling

When chat memory and uploaded files disagree, uploaded files win. When uploaded files and the repository disagree, the repository at the declared commit wins. When repository artifacts conflict, the authority order in `README.md` and accepted ADRs determines the resolution; the contradiction is recorded before work continues.

## References checked for this design

- OpenAI Help Center, “Projects in ChatGPT,” accessed 2026-08-12.
- OpenAI Codex documentation, `AGENTS.md` instruction behavior, accessed 2026-08-12.
- Anthropic Claude Code documentation, memory and `CLAUDE.md`, accessed 2026-08-12.
- GitHub documentation, custom instructions for coding agents, accessed 2026-08-12.

Current product limits and behavior must be rechecked before changing the five-file strategy.
