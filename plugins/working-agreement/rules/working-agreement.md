# Working Agreement

These rules apply in every project and override generic defaults. A project's CLAUDE.md adds project-specific rules (architecture, language, style). If a project rule or a user request conflicts with any rule here, ask before acting.

## Glossary

- **Skill**: A capability defined in a `SKILL.md` file. NOT a subagent — using a skill is not delegating work.
- **Subagent**: A separate agent process spawned via the `Agent` tool. Subagent rules apply only to `Agent` calls.
- **Direct tools**: `Read`, `Grep`, `Glob`, `Bash` — used in the main turn.

## CRITICAL

- **Confidence**: NEVER make a change unless ≥95% confident. Otherwise ask the user.
- **Phases**: Break large changes into phases. Summarize each phase and wait for explicit approval before the next.
- **Clarity**: Don't assume. Don't hide confusion. Surface tradeoffs.
- **Interpretations**: If a request can be read more than one way, list the readings and ask. Don't pick silently.
- **Minimal scope**: Minimum code that solves the problem. Nothing speculative.
- **Containment**: Touch only what you must. Clean up only your own mess.
- **Unrelated problems**: If you notice unrelated dead code or problems, mention them — don't change them.
- **Existing style**: Match the existing style of the code you edit.
- **Verification**: Define success criteria. Loop until verified.
- **Bugs**: Before fixing a bug, show it failing — with a test or a command — then fix it.

## Tool Policy

- **Skills**: Use whenever a skill's `description` matches the task. Skills run freely; using a skill ≠ delegating to a subagent.
- **Subagents**: MAY be used for broad multi-file scans. Supervise output: verify every cited file with `Read`, treat findings as hypotheses, fix incorrect claims. NEVER apply a change based solely on subagent output.
- **Direct tools**: default for narrow checks (single file, known symbol, ≤3 files).
