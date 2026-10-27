# working-agreement

A Claude Code plugin that loads one shared set of working rules into every session, in every project, on every machine where it is installed.

Instead of copying the same rules into each project's `CLAUDE.md`, install this plugin once. Projects keep only their own rules (architecture, language, style) in `CLAUDE.md`.

## What it does

At the start of every session, including after `/clear`, `--resume` and compaction, a `SessionStart` hook adds [`rules/working-agreement.md`](plugins/working-agreement/rules/working-agreement.md) to Claude's context. Subagents don't see session context, so a `SubagentStart` hook gives every subagent the same rules. The rules in short:

| Rule | In one line |
|---|---|
| Confidence | Change nothing unless ≥95% confident; otherwise ask. |
| Phases | Split large changes into phases; wait for approval after each. |
| Clarity / Interpretations | Don't assume; if a request reads two ways, list them and ask. |
| Minimal scope / Containment | Minimum code, nothing speculative; touch only what you must. |
| Unrelated problems | Mention unrelated dead code or problems; don't change them. |
| Existing style | Match the style of the code you edit. |
| Verification / Bugs | Define success criteria; show a bug failing before fixing it. |
| Tool Policy | Use matching skills; verify every subagent claim before acting on it. |

The rules are always loaded rather than shipped as a skill, because a skill loads only when Claude decides it is relevant. That is too late for a rule like "ask before changing anything you are unsure of".

## Requirements

- Claude Code with plugin support
- `git` (Claude Code clones the marketplace)
- A POSIX shell with `cat` (macOS, Linux, WSL)

## Install

In a Claude Code session:

```
/plugin marketplace add dgncksgl/working-agreement-plugin
/plugin install working-agreement@working-agreement
```

Or from your shell:

```bash
claude plugin marketplace add dgncksgl/working-agreement-plugin
claude plugin install working-agreement@working-agreement
```

Start a new session (or run `/reload-plugins`) for the rules to load.

If your machine has no GitHub SSH key, set `CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1` before installing. Otherwise installs and updates from inside a session can fail.

### Share it with everyone in a repository

Run this once in the repository and commit the `.claude/settings.json` it writes:

```bash
claude plugin marketplace add dgncksgl/working-agreement-plugin --scope project
```

Teammates who trust the folder get the marketplace registered and can install the plugin with the command above.

## Verify it works

Open a new session in any folder and ask:

```
Quote the Confidence rule from the working agreement.
```

Claude should answer with `NEVER make a change unless ≥95% confident. Otherwise ask the user.`. You can also check that `claude plugin list` shows `working-agreement@working-agreement` as enabled.

## Update

The plugin has no `version` field, so every new commit counts as an update. To pull it, run both commands in your shell, in this order:

```bash
claude plugin marketplace update working-agreement
claude plugin update working-agreement@working-agreement
```

The first fetches the new commit but leaves the installed copy on the old one. The second installs it. Run alone, the second reports `already at the latest version`, because it compares against the listing it fetched last time.

The new rules load in your next session, or after `/reload-plugins` in a running one.

To get updates automatically, open `/plugin`, go to **Marketplaces**, select `working-agreement` and choose **Enable auto-update**. Claude Code then checks for updates during interactive sessions and installs them in the background; you see `Plugin updated: working-agreement · Run /reload-plugins to apply`.

## Uninstall

```bash
claude plugin uninstall working-agreement@working-agreement
claude plugin marketplace remove working-agreement
```

## Using it with project rules

- Put project-specific rules (architecture, language, naming, tooling) in the project's `CLAUDE.md`.
- Don't repeat rules from this plugin there. If both say the same thing, the text loads twice.
- If a project rule contradicts a rule here, the working agreement tells Claude to ask before acting. Claude Code does not rank the two sources, so keep them consistent.

## Repository layout

```
.claude-plugin/marketplace.json           marketplace catalog
plugins/working-agreement/
  .claude-plugin/plugin.json              plugin manifest
  hooks/hooks.json                        SessionStart and SubagentStart hooks
  hooks/subagent-context.sh               wraps the rules in the JSON that SubagentStart requires
  rules/working-agreement.md              the rules (single source of truth)
tests/test_working_agreement.py           checks for manifests, hook output, rules text and README
```

## Development

Edit only `rules/working-agreement.md`. Both hooks read it at run time, so there is nothing to regenerate. Run the checks:

```bash
python3 tests/test_working_agreement.py
claude plugin validate .
```

Python is needed only for the tests. The hooks themselves use `cat`, `sh` and `awk`.

To try local changes without pushing:

```bash
claude plugin marketplace add ./
claude plugin install working-agreement@working-agreement
```

A marketplace added from a local path loads the files in place, so edits apply at the next session start or after `/reload-plugins`.

The hook output is capped by Claude Code at 10,000 characters, and the tests check that the rules stay under that cap.

## Credits

Four rules (Interpretations, Unrelated problems, Existing style, Bugs) are adapted from [andrej-karpathy-skills](https://github.com/forrestchang/andrej-karpathy-skills) (MIT). Those guidelines are themselves derived from Andrej Karpathy's observations on LLM coding pitfalls.

## License

[MIT](LICENSE)
