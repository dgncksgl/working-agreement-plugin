"""Checks the marketplace, the plugin manifest, the hooks, the rules text and the README."""
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "plugins" / "working-agreement"
RULES = PLUGIN / "rules" / "working-agreement.md"
SESSION_START_LIMIT = 10_000

KEPT_LINES = [
    "- **Confidence**: NEVER make a change unless ≥95% confident. Otherwise ask the user.",
    "- **Phases**: Break large changes into phases. Summarize each phase and wait for explicit approval before the next.",
    "- **Clarity**: Don't assume. Don't hide confusion. Surface tradeoffs.",
    "- **Minimal scope**: Minimum code that solves the problem. Nothing speculative.",
    "- **Containment**: Touch only what you must. Clean up only your own mess.",
    "- **Verification**: Define success criteria. Loop until verified.",
    "- **Direct tools**: default for narrow checks (single file, known symbol, ≤3 files).",
]

EXCLUDED_PHRASES = [
    "loop independently",
    "impossible scenarios",
    "push back",
    "use judgment",
    "clean architecture",
    "turkish",
]


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def run_hook(event, plugin_root):
    command = load(plugin_root / "hooks" / "hooks.json")["hooks"][event][0]["hooks"][0]["command"]
    env = {**os.environ, "CLAUDE_PLUGIN_ROOT": str(plugin_root)}
    return subprocess.run(["sh", "-c", command], env=env, capture_output=True, text=True, check=True).stdout


class MarketplaceTest(unittest.TestCase):
    def test_entry_points_to_plugin_with_same_name(self):
        marketplace = load(ROOT / ".claude-plugin" / "marketplace.json")
        entry = marketplace["plugins"][0]
        manifest = load(PLUGIN / ".claude-plugin" / "plugin.json")
        self.assertEqual(entry["name"], manifest["name"])
        self.assertEqual((ROOT / entry["source"]).resolve(), PLUGIN.resolve())

    def test_no_version_so_users_track_commits(self):
        manifest = load(PLUGIN / ".claude-plugin" / "plugin.json")
        entry = load(ROOT / ".claude-plugin" / "marketplace.json")["plugins"][0]
        self.assertNotIn("version", manifest)
        self.assertNotIn("version", entry)


class HookTest(unittest.TestCase):
    def test_session_start_prints_rules_verbatim(self):
        hooks = load(PLUGIN / "hooks" / "hooks.json")["hooks"]["SessionStart"]
        self.assertEqual(len(hooks), 1)
        self.assertNotIn("matcher", hooks[0])
        command = hooks[0]["hooks"][0]["command"]
        env = {**os.environ, "CLAUDE_PLUGIN_ROOT": str(PLUGIN)}
        result = subprocess.run(["sh", "-c", command], env=env, capture_output=True, text=True, check=True)
        self.assertEqual(result.stdout, RULES.read_text(encoding="utf-8"))

    def test_subagent_start_injects_rules_verbatim(self):
        hooks = load(PLUGIN / "hooks" / "hooks.json")["hooks"]["SubagentStart"]
        self.assertEqual(len(hooks), 1)
        self.assertNotIn("matcher", hooks[0])
        command = hooks[0]["hooks"][0]["command"]
        env = {**os.environ, "CLAUDE_PLUGIN_ROOT": str(PLUGIN)}
        result = subprocess.run(["sh", "-c", command], env=env, capture_output=True, text=True, check=True)
        output = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], "SubagentStart")
        self.assertEqual(output["additionalContext"], RULES.read_text(encoding="utf-8"))

    def test_subagent_start_follows_edited_rules_with_special_characters(self):
        tricky = 'Quote " and \\ backslash\tTab — çğıöşü ≥95% ≠ {json}\n- **Rule**: `code` and "x"\n'
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "working-agreement"
            shutil.copytree(PLUGIN, root)
            (root / "rules" / "working-agreement.md").write_text(tricky, encoding="utf-8")
            output = json.loads(run_hook("SubagentStart", root))["hookSpecificOutput"]
            self.assertEqual(output["additionalContext"], tricky)

    def test_subagent_start_prints_no_partial_json_when_rules_are_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "working-agreement"
            shutil.copytree(PLUGIN, root)
            (root / "rules" / "working-agreement.md").unlink()
            command = load(root / "hooks" / "hooks.json")["hooks"]["SubagentStart"][0]["hooks"][0]["command"]
            env = {**os.environ, "CLAUDE_PLUGIN_ROOT": str(root)}
            result = subprocess.run(["sh", "-c", command], env=env, capture_output=True, text=True)
            self.assertEqual(result.stdout, "")
            self.assertEqual(result.returncode, 1)
            self.assertIn("working-agreement.md", result.stderr)

    def test_rules_have_a_single_source(self):
        self.assertEqual(sorted(p.name for p in (PLUGIN / "rules").iterdir()), ["working-agreement.md"])

    def test_rules_fit_session_start_limit(self):
        self.assertLess(len(RULES.read_text(encoding="utf-8")), SESSION_START_LIMIT)

    def test_subagent_context_fits_limit(self):
        output = json.loads(run_hook("SubagentStart", PLUGIN))["hookSpecificOutput"]
        self.assertLess(len(output["additionalContext"]), SESSION_START_LIMIT)

    def test_only_expected_events(self):
        self.assertEqual(set(load(PLUGIN / "hooks" / "hooks.json")["hooks"]), {"SessionStart", "SubagentStart"})

    def test_hooks_work_from_path_with_spaces_and_non_ascii(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "plugin dir çğüş" / "working-agreement"
            shutil.copytree(PLUGIN, root)
            rules = RULES.read_text(encoding="utf-8")
            self.assertEqual(run_hook("SessionStart", root), rules)
            self.assertEqual(json.loads(run_hook("SubagentStart", root))["hookSpecificOutput"]["additionalContext"], rules)


class RulesTest(unittest.TestCase):
    def setUp(self):
        self.text = RULES.read_text(encoding="utf-8")

    def test_kept_lines_are_verbatim(self):
        lines = self.text.splitlines()
        for line in KEPT_LINES:
            self.assertIn(line, lines)

    def test_excluded_rules_are_absent(self):
        lowered = self.text.lower()
        for phrase in EXCLUDED_PHRASES:
            self.assertNotIn(phrase, lowered)

    def test_ends_with_newline_so_both_hooks_see_identical_text(self):
        self.assertTrue(self.text.endswith("\n"))

    def test_no_control_characters_that_would_break_subagent_json(self):
        self.assertEqual([c for c in self.text if ord(c) < 32 and c != "\n"], [])

    def test_rule_names_are_unique_within_each_section(self):
        sections = re.split(r"^## ", self.text, flags=re.M)[1:]
        self.assertEqual([s.splitlines()[0] for s in sections], ["Glossary", "CRITICAL", "Tool Policy"])
        for section in sections:
            names = re.findall(r"^- \*\*([^*]+)\*\*:", section, re.M)
            self.assertEqual(len(names), len(set(names)), section.splitlines()[0])

    def test_only_claude_code_tool_names(self):
        for wrong in ("`Task`", "`Shell`", "`SemanticSearch`"):
            self.assertNotIn(wrong, self.text)


class ReadmeTest(unittest.TestCase):
    def setUp(self):
        self.text = (ROOT / "README.md").read_text(encoding="utf-8")

    def test_install_commands_match_manifests(self):
        marketplace = load(ROOT / ".claude-plugin" / "marketplace.json")["name"]
        plugin = load(PLUGIN / ".claude-plugin" / "plugin.json")["name"]
        self.assertIn(f"/plugin install {plugin}@{marketplace}", self.text)
        self.assertIn(f"claude plugin install {plugin}@{marketplace}", self.text)
        self.assertIn(f"claude plugin update {plugin}@{marketplace}", self.text)
        self.assertIn(f"claude plugin marketplace remove {marketplace}", self.text)
        self.assertIn("marketplace add dgncksgl/working-agreement-plugin", self.text)

    def test_update_section_refreshes_listing_before_updating_plugin(self):
        # `marketplace update` alone leaves the installed copy on its old commit, and
        # `plugin update` alone reports "already at the latest version" from the stale listing.
        marketplace = load(ROOT / ".claude-plugin" / "marketplace.json")["name"]
        plugin = load(PLUGIN / ".claude-plugin" / "plugin.json")["name"]
        update = self.text.split("\n## Update\n", 1)[1].split("\n## ", 1)[0]
        refresh = update.find(f"claude plugin marketplace update {marketplace}\n")
        install = update.find(f"claude plugin update {plugin}@{marketplace}\n")
        self.assertNotEqual(refresh, -1)
        self.assertGreater(install, refresh)

    def test_relative_links_exist(self):
        for target in re.findall(r"\]\((?!https?://)([^)#]+)\)", self.text):
            self.assertTrue((ROOT / target).exists(), target)

    def test_quoted_confidence_rule_matches_rules(self):
        self.assertIn("NEVER make a change unless ≥95% confident. Otherwise ask the user.", RULES.read_text(encoding="utf-8"))
        self.assertIn("NEVER make a change unless ≥95% confident. Otherwise ask the user.", self.text)


if __name__ == "__main__":
    unittest.main()
