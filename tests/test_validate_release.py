from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL = Path("plugins/tui-design/skills/tui-design")
METADATA_OK = "Validated skill metadata and content for"


class ValidateReleaseTest(unittest.TestCase):
    """Each test breaks one release invariant in a copy of the repo and expects a named failure."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "repo"
        for relative in ("scripts", "plugins", ".claude-plugin", "evals/schema"):
            shutil.copytree(REPO_ROOT / relative, self.root / relative)
        shutil.copy2(REPO_ROOT / "CHANGELOG.md", self.root / "CHANGELOG.md")
        for eval_set in (REPO_ROOT / "evals").glob("*.json"):
            shutil.copy2(eval_set, self.root / "evals" / eval_set.name)
        self.version = json.loads((self.root / ".claude-plugin/marketplace.json").read_text())["version"]

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def validate(self, tag: str = "") -> subprocess.CompletedProcess[str]:
        # Only the metadata stage matters here; later stages need the full tree.
        return subprocess.run(
            ["bash", str(self.root / "scripts/validate-release.sh"), *([tag] if tag else [])],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
        )

    def assert_fails_with(self, message: str, tag: str = "") -> None:
        completed = self.validate(tag)
        self.assertNotEqual(completed.returncode, 0)
        self.assertNotIn(METADATA_OK, completed.stdout)
        self.assertIn(message, completed.stderr)

    def edit(self, relative: str, old: str, new: str, count: int = 1) -> None:
        path = self.root / relative
        text = path.read_text()
        self.assertEqual(text.count(old), count, old)
        path.write_text(text.replace(old, new))

    def set_versions(self, version: str) -> None:
        for relative in (".claude-plugin/marketplace.json", "plugins/tui-design/.claude-plugin/plugin.json"):
            path = self.root / relative
            path.write_text(path.read_text().replace(f'"version": "{self.version}"', f'"version": "{version}"'))

    def test_unmodified_copy_passes_metadata_checks(self) -> None:
        self.assertIn(METADATA_OK, self.validate().stdout)

    def test_manifest_version_mismatch(self) -> None:
        self.edit("plugins/tui-design/.claude-plugin/plugin.json", f'"version": "{self.version}"', '"version": "9.9.9"')
        self.assert_fails_with("manifest versions disagree")

    def test_tag_must_match_manifest_version(self) -> None:
        self.assert_fails_with("does not match manifest version", tag="v9.0.0")

    def test_changelog_needs_a_section_for_the_version(self) -> None:
        self.set_versions("9.9.9")
        self.assert_fails_with("CHANGELOG.md has no section for 9.9.9")

    def test_changelog_needs_compare_links(self) -> None:
        changelog = self.root / "CHANGELOG.md"
        changelog.write_text(re.sub(rf"^\[{re.escape(self.version)}\]: .*\n", "", changelog.read_text(), flags=re.M))
        self.assert_fails_with(f"no compare link for [{self.version}]")

    def test_unreleased_link_must_compare_from_the_current_version(self) -> None:
        self.edit("CHANGELOG.md", f"compare/v{self.version}...HEAD", "compare/v0.0.1...HEAD")
        self.assert_fails_with("CHANGELOG.md needs [Unreleased]")

    def test_extra_skill_file(self) -> None:
        (self.root / SKILL / "references/extra.md").write_text("# Extra\n")
        self.assert_fails_with("allowlist mismatch")

    def test_missing_skill_file(self) -> None:
        (self.root / SKILL / "references/exemplar-apps.md").unlink()
        self.assert_fails_with("allowlist mismatch")

    def test_skill_md_line_budget(self) -> None:
        skill_md = self.root / SKILL / "SKILL.md"
        skill_md.write_text(skill_md.read_text() + "\n" * 200)
        self.assert_fails_with("exceeds the 200-line core budget")

    def test_unbalanced_fence(self) -> None:
        reference = self.root / SKILL / "references/cli-basics.md"
        reference.write_text(reference.read_text() + "\n```bash\necho unclosed\n")
        self.assert_fails_with("unbalanced fenced code block")

    def test_manifest_descriptions_must_match_each_other(self) -> None:
        path = self.root / "plugins/tui-design/.claude-plugin/plugin.json"
        manifest = json.loads(path.read_text())
        manifest["description"] = manifest["description"] + " Extra."
        path.write_text(json.dumps(manifest, indent=2) + "\n")
        self.assert_fails_with("plugin.json and marketplace.json plugin descriptions differ")

    def test_manifest_descriptions_must_follow_skill_md(self) -> None:
        for relative in ("plugins/tui-design/.claude-plugin/plugin.json", ".claude-plugin/marketplace.json"):
            path = self.root / relative
            path.write_text(path.read_text().replace("Design, build, refactor, or review", "Design or review"))
        self.assert_fails_with("must start with SKILL.md's first description sentence")

    def test_folded_frontmatter_description_is_accepted(self) -> None:
        skill_md = self.root / SKILL / "SKILL.md"
        text = skill_md.read_text()
        match = re.search(r"^description: (.*)$", text, flags=re.M)
        words = match.group(1).split(" ")
        folded = "description: >-\n  " + " ".join(words[:12]) + "\n  " + " ".join(words[12:]) + "\n  Note: colons in continuation lines are not keys."
        skill_md.write_text(text.replace(match.group(0), folded))
        self.assertIn(METADATA_OK, self.validate().stdout)


if __name__ == "__main__":
    unittest.main()
