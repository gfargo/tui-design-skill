from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("build_checker", REPO_ROOT / "scripts/runners/build_checker.py")
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)

# A well-behaved raw-mode program: alternate screen, redraw on SIGWINCH, q and Ctrl+C quit and restore.
GOOD_PROGRAM = r'''
import os, signal, sys, termios, tty
fd = sys.stdin.fileno()
saved = termios.tcgetattr(fd)
def draw(*_):
    cols, rows = os.get_terminal_size(fd)
    sys.stdout.write("\x1b[H\x1b[2J\x1b[1mapi-gateway\x1b[0m  up\r\n" + "-" * (cols - 1) + "\r\n\x1b[%d;1Hq quit" % rows)
    sys.stdout.flush()
tty.setraw(fd)
sys.stdout.write("\x1b[?1049h\x1b[?25l")
signal.signal(signal.SIGWINCH, draw)
draw()
while True:
    key = os.read(fd, 1)
    if key in (b"q", b"\x03"):
        break
sys.stdout.write("\x1b[?25h\x1b[?1049l")
sys.stdout.flush()
termios.tcsetattr(fd, termios.TCSADRAIN, saved)
'''

# Ignores NO_COLOR, crashes below 30 columns, ignores Ctrl+C, and leaves the terminal raw after q.
BAD_PROGRAM = r'''
import os, signal, sys, tty
fd = sys.stdin.fileno()
def draw(*_):
    cols, rows = os.get_terminal_size(fd)
    if cols < 30:
        raise SystemExit("Traceback (most recent call last):\n  too narrow")
    sys.stdout.write("\x1b[H\x1b[2J\x1b[31mapi-gateway\x1b[0m down")
    sys.stdout.flush()
tty.setraw(fd)
sys.stdout.write("\x1b[?1049h\x1b[?1000h")
signal.signal(signal.SIGWINCH, draw)
draw()
while os.read(fd, 1) != b"q":
    pass
'''


def run_smoke(source: str) -> dict:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        (root / "program.py").write_text(source)
        config = {"command": [sys.executable, "program.py"], "cwd": str(root), "expect_any": ["auth-service", "api-gateway"]}
        (root / "smoke.json").write_text(json.dumps(config))
        checker.smoke_main(root / "smoke.json", root / "result.json")
        return json.loads((root / "result.json").read_text())


class ExtractFilesTest(unittest.TestCase):
    def test_headers_in_common_markdown_forms(self) -> None:
        answer = (
            "Here you go.\n\nFile: go.mod\n```\nmodule x\n```\n\n"
            "**File:** `src/main.rs`\n\n```rust\nfn main() {}\n```\n"
            "### File: app.py\n````python\nprint('```')\n````\n"
        )
        files, problems = checker.extract_files(answer)
        self.assertEqual(problems, [])
        self.assertEqual(files, {"go.mod": "module x\n", "src/main.rs": "fn main() {}\n", "app.py": "print('```')\n"})

    def test_unsafe_paths_and_missing_blocks_are_reported(self) -> None:
        answer = "File: ../escape.txt\n```\nx\n```\nFile: /etc/passwd\n```\nx\n```\nFile: .check/app\n```\nx\n```\nFile: lonely.txt\nno fence\n"
        files, problems = checker.extract_files(answer)
        self.assertEqual(files, {})
        self.assertEqual(len(problems), 4)

    def test_an_answer_without_headers_is_a_problem(self) -> None:
        files, problems = checker.extract_files("```go\npackage main\n```\n")
        self.assertEqual(files, {})
        self.assertIn("no `File: <path>` headers", problems[0])


class TerminalTest(unittest.TestCase):
    def feed(self, data: str, cols: int = 20, rows: int = 5) -> tuple[object, list[str]]:
        replies: list[str] = []
        terminal = checker.Terminal(cols, rows, replies.append)
        terminal.feed(data.encode())
        return terminal, replies

    def test_cursor_addressing_erase_and_wrap(self) -> None:
        terminal, _ = self.feed("hello\x1b[3;5Hworld\x1b[1;3H\x1b[K\x1b[5;18Habcdef")
        # "abc" fills the last row; "d" wraps, scrolling the screen up one row and dropping "he".
        self.assertEqual(terminal.text().split("\n"), ["", "    world", "", "                 abc", "def"])

    def test_sequences_split_across_reads(self) -> None:
        replies: list[str] = []
        terminal = checker.Terminal(20, 3, replies.append)
        for chunk in (b"\x1b[2", b";3Hx", b"\xe2\x94", b"\x80"):
            terminal.feed(chunk)
        self.assertEqual(terminal.text().split("\n")[1], "  x─")

    def test_alternate_screen_and_tracked_modes(self) -> None:
        terminal, _ = self.feed("main\x1b[?1049h\x1b[?25l\x1b[?1000;1006h\x1b[>1u\x1b[Halt")
        self.assertEqual(terminal.text(), "alt")
        self.assertEqual(set(terminal.left_on()), {
            "alternate screen (1049)", "mouse tracking (1000)", "mouse encoding (1006)",
            "cursor left hidden (25)", "keyboard enhancement left pushed (1)",
        })
        terminal.feed(b"\x1b[<u\x1b[?1000;1006l\x1b[?25h\x1b[?1049l")
        self.assertEqual(terminal.text(), "main")
        self.assertEqual(terminal.left_on(), [])

    def test_wide_characters_take_two_cells(self) -> None:
        terminal, _ = self.feed("中文x")
        self.assertEqual(terminal.text(), "中文x")
        self.assertEqual(terminal.x, 5)

    def test_queries_get_xterm_replies(self) -> None:
        _, replies = self.feed("\x1b[2;4H\x1b[6n\x1b[c\x1b]11;?\x07\x1b[?2026$p")
        self.assertEqual(replies, ["\x1b[2;4R", "\x1b[?62;22c", "\x1b]11;rgb:0000/0000/0000\x1b\\", "\x1b[?2026;0$y"])

    def test_only_chromatic_colors_count_under_no_color(self) -> None:
        grays = ["0", "1;7", "39;49", "37", "90;107", "38;5;244", "48;5;16", "38;2;10;10;10", "1;38;2;224;224;224;48;2;54;54;54", "38:2::9:9:9"]
        hues = ["31", "1;44", "96", "38;5;196", "48;2;10;20;10", "38:5:202", "38:2::1:2:3", "58;5;9", "38;2;9;9;9;31"]
        for body in grays:
            terminal, _ = self.feed(f"\x1b[{body}m")
            self.assertEqual(terminal.color_sgr, [], body)
        for body in hues:
            terminal, _ = self.feed(f"\x1b[{body}m")
            self.assertEqual(terminal.color_sgr, [body], body)
        terminal, _ = self.feed("\x1b[>4;2m")  # modifyOtherKeys, not SGR
        self.assertEqual((terminal.color_sgr, terminal.left_on()), ([], ["modifyOtherKeys left at 2"]))

    def test_quit_hint_pattern(self) -> None:
        for text in ("q quit", "^q Quit", "quit: q", "[q] Quit", "esc/q quit"):
            self.assertRegex(text, checker.QUIT_HINT)
        for text in ("queue quit", "quit with esc", "q: back", "squid quit"):
            self.assertNotRegex(text, checker.QUIT_HINT)


@unittest.skipUnless(sys.platform.startswith(("linux", "darwin")), "needs a POSIX pseudo-terminal")
class SmokeTest(unittest.TestCase):
    def test_a_well_behaved_program_passes_every_check(self) -> None:
        result = run_smoke(GOOD_PROGRAM)
        failed = {name: verdict["note"] for name, verdict in result["verdicts"].items() if not verdict["passed"]}
        self.assertEqual(failed, {})
        self.assertIn("api-gateway", result["transcripts"]["main"]["screens"]["first_80x24"])

    def test_a_careless_program_fails_where_it_should(self) -> None:
        verdicts = run_smoke(BAD_PROGRAM)["verdicts"]
        outcome = {name: verdict["passed"] for name, verdict in verdicts.items()}
        self.assertEqual(outcome, {
            "starts": True, "shows_data": True, "names_quit_key": False, "q_quits": True, "q_restores": False,
            "redraws_on_resize": True, "survives_tiny": False, "ctrl_c_quits_and_restores": False, "honors_no_color": False,
        })
        self.assertIn("line settings differ", verdicts["q_restores"]["note"])
        self.assertIn("mouse tracking (1000)", verdicts["q_restores"]["note"])
        self.assertIn("'31'", verdicts["honors_no_color"]["note"])


class GradeTrialTest(unittest.TestCase):
    CASE = {"build_check": {"language": "go", "fixture": {"path": "d.json", "content": "[]"}, "args": ["d.json"], "expect_any": ["x"]}}

    def grade(self, response: str) -> list[tuple[bool, str]]:
        with tempfile.TemporaryDirectory() as temporary:
            return checker.grade_trial({"trial_id": "t-r1"}, self.CASE, response, Path(temporary), threading.Lock())

    def test_unparseable_answers_fail_every_check_with_a_note(self) -> None:
        results = self.grade("no files here")
        self.assertEqual(len(results), len(checker.CHECKS))
        self.assertTrue(all(not passed and note.startswith("not built:") for passed, note in results))

    def test_a_failed_fetch_fails_every_check_with_its_log(self) -> None:
        original = checker.run_container
        checker.run_container = lambda *args, **kwargs: (1, "go: module example.com/missing: not found", 2.0)
        try:
            results = self.grade("File: go.mod\n```\nmodule x\n```\n")
        finally:
            checker.run_container = original
        self.assertTrue(all(not passed for passed, _ in results))
        self.assertIn("dependency fetch failed (exit 1", results[0][1])
        self.assertIn("example.com/missing", results[-1][1])

    def test_every_build_check_case_matches_the_checker(self) -> None:
        eval_set = json.loads((REPO_ROOT / "evals/build-checks-evals.json").read_text())
        for case in eval_set["evals"]:
            config = case["build_check"]
            self.assertIn(config["language"], checker.IMAGES)
            self.assertEqual(len(case["assertions"]), len(checker.CHECKS), case["id"])
            self.assertIn(config["fixture"]["content"], case["prompt"], case["id"])
            self.assertTrue(all(item in config["fixture"]["content"] for item in config["expect_any"]), case["id"])


if __name__ == "__main__":
    unittest.main()
