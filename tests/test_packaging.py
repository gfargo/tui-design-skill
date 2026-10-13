from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
PACKAGE_SCRIPT = REPO_ROOT / "scripts/package-skill.sh"
SKILL_DIR = REPO_ROOT / "plugins/tui-design/skills/tui-design"
FILES_LIST = REPO_ROOT / "scripts/skill-files.txt"


def listed_files(path: Path = FILES_LIST) -> list[str]:
    return [
        line.strip()
        for line in path.read_text().splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


class PackagingTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "repo"
        (self.root / "scripts").mkdir(parents=True)
        shutil.copy2(PACKAGE_SCRIPT, self.root / "scripts/package-skill.sh")
        shutil.copy2(FILES_LIST, self.root / "scripts/skill-files.txt")
        shutil.copytree(SKILL_DIR, self.root / "plugins/tui-design/skills/tui-design")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def package(self, expected: int = 0) -> subprocess.CompletedProcess[str]:
        completed = subprocess.run(
            ["bash", str(self.root / "scripts/package-skill.sh"), str(self.root / "dist")],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, expected, completed.stderr)
        return completed

    def test_package_contains_exact_allowlist(self) -> None:
        self.package()
        with zipfile.ZipFile(self.root / "dist/tui-design.skill") as archive:
            self.assertEqual(archive.namelist(), ["tui-design/" + name for name in listed_files()])

    def test_allowlist_matches_the_skill_directory_in_archive_order(self) -> None:
        names = listed_files()
        self.assertEqual(names, sorted(names))
        actual = sorted(
            path.relative_to(SKILL_DIR).as_posix() for path in SKILL_DIR.rglob("*") if path.is_file()
        )
        self.assertEqual(actual, names)

    def test_package_reads_the_shared_allowlist(self) -> None:
        listed = self.root / "scripts/skill-files.txt"
        listed.write_text(listed.read_text() + "references/new-topic.md\n")
        completed = self.package(expected=1)
        self.assertIn("listed skill file is missing: references/new-topic.md", completed.stderr)
        (self.root / "plugins/tui-design/skills/tui-design/references/new-topic.md").write_text("# New\n")
        self.package()
        with zipfile.ZipFile(self.root / "dist/tui-design.skill") as archive:
            self.assertIn("tui-design/references/new-topic.md", archive.namelist())

    def test_package_rejects_unexpected_files(self) -> None:
        cache = self.root / "plugins/tui-design/skills/tui-design/references/__pycache__"
        cache.mkdir()
        cache.joinpath("junk.pyc").write_bytes(b"junk")
        completed = self.package(expected=1)
        self.assertIn("unexpected entry in skill source", completed.stderr)

    def test_package_rejects_symlinked_references(self) -> None:
        reference = self.root / "plugins/tui-design/skills/tui-design/references/exemplar-apps.md"
        external = self.root / "external.md"
        external.write_text(reference.read_text())
        reference.unlink()
        reference.symlink_to(external)
        completed = self.package(expected=1)
        self.assertIn("regular, non-symlink", completed.stderr)


if __name__ == "__main__":
    unittest.main()
