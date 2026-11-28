#!/usr/bin/env python3
"""Grade build-task trials by building and running them, writing schema-v6 grades.

For every trial of an eval set whose cases carry a `build_check` object (see
evals/build-checks-evals.json), the checker:

1. extracts the answer's files: each `File: <path>` line followed by a fenced
   code block;
2. fetches dependencies from the answer's manifest in a pinned toolchain
   container, the only stage with network access;
3. builds without network in the same image;
4. runs the program in a pseudo-terminal inside a pinned Python container
   without network (this same file, `smoke` mode), driving it through fixed
   scenarios and recording what it observed for each assertion in CHECKS.

Images are pinned by digest. The checker file is copied into the run directory
as checker.py and hash-linked from grades.json (schema v6, kind "automated"),
and each trial's logs, screens, and resolved dependencies are kept under
checks/<trial_id>/ for audit.

Usage:
  python3 scripts/runners/build_checker.py --run evals/runs/RUN/run.json [--jobs 2]
Requires Docker. The `smoke` subcommand runs inside the container only.
"""

import argparse
import codecs
import fcntl
import hashlib
import json
import os
import re
import select
import shutil
import signal
import struct
import subprocess
import sys
import tempfile
import termios
import threading
import time
import unicodedata
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

CHECKER_VERSION = "build-checks-v1"
GRADES_SCHEMA_V6 = "https://raw.githubusercontent.com/gfargo/tui-design-skill/main/evals/schema/v6/grades.schema.json"

# Toolchain images, pinned by multi-platform index digest. The runtime image
# runs every program (Go builds static; Rust links against the same Debian
# trixie glibc; Python uses the virtual environment built in this image).
IMAGES = {
    "go": ("golang:1.27-trixie", "sha256:430985542100b871e108ccc00e8dcc5eef08ca14ee5825e98ebf563d8ffec4ee"),
    "rust": ("rust:1.100-trixie", "sha256:e84068000361bf3d4a5ba2b7647f62893528b1eb9f847d7a23b493f5ce8ea254"),
    "python": ("python:3.14-slim-trixie", "sha256:f57c4c23b985d95deea5bc5249e2f9c8a512b4cc9d5d3fd31900cbd2f5f0a604"),
}
RUNTIME = "python"
TOOL_VERSION_COMMANDS = {"go": ["go", "version"], "rust": ["rustc", "--version"], "python": ["python", "-VV"]}

# Assertion order. Every build_check case lists its assertions in this order.
CHECKS = (
    "builds",
    "starts",
    "shows_data",
    "names_quit_key",
    "q_quits",
    "q_restores",
    "redraws_on_resize",
    "survives_tiny",
    "ctrl_c_quits_and_restores",
    "honors_no_color",
)

FETCH_TIMEOUT = 600
FETCH_LOCKS = {language: threading.Lock() for language in IMAGES}
BUILD_TIMEOUT = 900
SMOKE_TIMEOUT = 180
CACHE_VOLUMES = {
    "go": {"tui-design-check-gomod": "/go/pkg/mod", "tui-design-check-gocache": "/root/.cache/go-build"},
    "rust": {"tui-design-check-cargo": "/usr/local/cargo/registry"},
    "python": {"tui-design-check-pip": "/root/.cache/pip"},
}

# Scripts run with `sh -ec` in the toolchain image, from /work.
FETCH_SCRIPTS = {
    "go": "test -f go.mod || { echo 'no go.mod in the answer'; exit 3; }\ngo mod tidy\n",
    "rust": (
        "test -f Cargo.toml || { echo 'no Cargo.toml in the answer'; exit 3; }\n"
        "test -f Cargo.lock || cargo generate-lockfile\ncargo fetch\n"
    ),
    "python": (
        "python -m venv /work/.check/venv\n"
        "if [ -f requirements.txt ]; then /work/.check/venv/bin/pip install --no-input --disable-pip-version-check -r requirements.txt\n"
        "elif [ -f pyproject.toml ]; then /work/.check/venv/bin/pip install --no-input --disable-pip-version-check .\n"
        "else echo 'no requirements.txt or pyproject.toml in the answer'; exit 3; fi\n"
    ),
}
BUILD_SCRIPTS = {
    "go": (
        "export GOFLAGS=-mod=mod GOPROXY=off CGO_ENABLED=0\n"
        "mains=$(go list -f '{{if eq .Name \"main\"}}{{.ImportPath}}{{end}}' ./... | sed '/^$/d')\n"
        "count=$(printf '%s\\n' \"$mains\" | sed '/^$/d' | wc -l)\n"
        "[ \"$count\" -eq 1 ] || { echo \"expected one main package, found $count: $mains\"; exit 3; }\n"
        "go build -o /work/.check/app \"$mains\"\n"
        "go version -m /work/.check/app > /work/.check/deps.txt\n"
    ),
    "rust": (
        "export CARGO_TARGET_DIR=/work/.check/target\n"
        "cargo build --offline --locked --bins\n"
        "bins=$(find /work/.check/target/debug -maxdepth 1 -type f -perm -u+x)\n"
        "count=$(printf '%s\\n' \"$bins\" | sed '/^$/d' | wc -l)\n"
        "[ \"$count\" -eq 1 ] || { echo \"expected one binary, found $count: $bins\"; exit 3; }\n"
        "cp \"$bins\" /work/.check/app\ncp Cargo.lock /work/.check/deps.txt\n"
    ),
    "python": (
        "/work/.check/venv/bin/python -m compileall -q -x '/\\.check/' /work\n"
        "/work/.check/venv/bin/pip freeze --disable-pip-version-check > /work/.check/deps.txt\n"
    ),
}

# ---------------------------------------------------------------------------
# Answer parsing (host)

FILE_HEADER = re.compile(r"^[#>*\s-]*\**File:\**\s*\**`?(?P<path>[^`*\s]+)`?\**\s*$", re.IGNORECASE)
FENCE_OPEN = re.compile(r"^(?P<indent> {0,3})(?P<fence>`{3,}|~{3,})(?P<info>.*)$")


def extract_files(response):
    """Return ({path: content}, problems) from `File: <path>` headers each followed by a fenced block."""
    lines = response.splitlines()
    files, problems = {}, []
    index = 0
    while index < len(lines):
        header = FILE_HEADER.match(lines[index])
        index += 1
        if not header:
            continue
        path = header.group("path").strip()
        while index < len(lines) and not lines[index].strip():
            index += 1
        opening = FENCE_OPEN.match(lines[index]) if index < len(lines) else None
        if not opening:
            problems.append(f"`File: {path}` is not followed by a fenced code block")
            continue
        fence = opening.group("fence")
        index += 1
        body = []
        while index < len(lines):
            stripped = lines[index].strip()
            if stripped.startswith(fence[0] * len(fence)) and not stripped.strip(fence[0]):
                break
            body.append(lines[index])
            index += 1
        index += 1
        parts = Path(path).parts
        if Path(path).is_absolute() or ".." in parts or not parts or parts[0] == ".check":
            problems.append(f"unsafe path rejected: {path!r}")
            continue
        files[str(Path(path))] = "\n".join(body) + "\n"
    if not files and not problems:
        problems.append("no `File: <path>` headers followed by fenced code blocks")
    return files, problems


# ---------------------------------------------------------------------------
# Docker (host)


def docker(args, timeout=None, check=False):
    return subprocess.run(["docker", *args], text=True, capture_output=True, timeout=timeout, check=check)


def image_ref(language):
    tag, digest = IMAGES[language]
    return f"{tag.split(':', 1)[0]}@{digest}"


def ensure_images():
    for language in IMAGES:
        ref = image_ref(language)
        if docker(["image", "inspect", ref]).returncode != 0:
            print(f"pulling {ref}", file=sys.stderr)
            docker(["pull", "-q", ref], check=True)


def run_container(language, script, work, network, timeout, extra_mounts=(), limits=()):
    name = f"tui-design-check-{uuid.uuid4().hex[:12]}"
    command = ["run", "--rm", "--name", name, "--network", "bridge" if network else "none", *limits,
               "-v", f"{work}:/work", "-w", "/work", "-e", "GOTOOLCHAIN=local"]
    for volume, target in CACHE_VOLUMES.get(language, {}).items():
        command += ["-v", f"{volume}:{target}"]
    for source, target in extra_mounts:
        command += ["-v", f"{source}:{target}:ro"]
    command += [image_ref(language), "sh", "-ec", script]
    started = time.monotonic()
    try:
        completed = docker(command, timeout=timeout)
    except subprocess.TimeoutExpired:
        docker(["rm", "-f", name])
        return None, f"timed out after {timeout} s", time.monotonic() - started
    output = (completed.stdout or "") + (completed.stderr or "")
    return completed.returncode, output, time.monotonic() - started


def tool_versions():
    server = docker(["version", "--format", "{{.Server.Version}} {{.Server.Os}}/{{.Server.Arch}}"], check=True).stdout.split()
    tools = {"docker": server[0], "platform": server[1], "checker": CHECKER_VERSION}
    for language, (tag, digest) in IMAGES.items():
        tools[tag] = digest
        completed = docker(["run", "--rm", "--network", "none", image_ref(language), *TOOL_VERSION_COMMANDS[language]], check=True)
        tools[TOOL_VERSION_COMMANDS[language][0]] = completed.stdout.strip().splitlines()[0]
    return tools


# ---------------------------------------------------------------------------
# Grading (host)


def tail(text, limit=600):
    text = text.strip()
    return text if len(text) <= limit else "..." + text[-limit:]


def all_failed(note):
    return [(False, note) for _ in CHECKS]


def grade_trial(trial, case, response, checks_dir, smoke_lock):
    config = case["build_check"]
    language = config["language"]
    trial_dir = checks_dir / trial["trial_id"]
    trial_dir.mkdir(parents=True, exist_ok=True)
    files, problems = extract_files(response)
    (trial_dir / "files.txt").write_text("".join(f"{path}\n" for path in sorted(files)) + "".join(f"problem: {p}\n" for p in problems))
    if not files:
        return all_failed("not built: " + "; ".join(problems))

    with tempfile.TemporaryDirectory(prefix="tui-design-check-") as temporary:
        work = Path(temporary).resolve()
        for path, content in files.items():
            target = work / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
        fixture = config["fixture"]
        (work / fixture["path"]).write_text(fixture["content"])
        (work / ".check").mkdir()

        with FETCH_LOCKS[language]:  # concurrent fetches into one shared cache volume can race
            code, output, seconds = run_container(language, FETCH_SCRIPTS[language], work, True, FETCH_TIMEOUT)
        (trial_dir / "fetch.log").write_text(output)
        if code != 0:
            return all_failed(f"not built: dependency fetch failed (exit {code}, {seconds:.0f} s): {tail(output)}")
        code, output, seconds = run_container(language, BUILD_SCRIPTS[language], work, False, BUILD_TIMEOUT)
        (trial_dir / "build.log").write_text(output)
        if (work / ".check/deps.txt").is_file():
            shutil.copyfile(work / ".check/deps.txt", trial_dir / "deps.txt")
        if code != 0:
            return all_failed(f"build failed without network (exit {code}, {seconds:.0f} s): {tail(output)}")
        build_note = (
            f"{'go build' if language == 'go' else 'cargo build' if language == 'rust' else 'pip install and compileall'} "
            f"succeeded ({seconds:.0f} s, offline); resolved dependencies in checks/{trial['trial_id']}/deps.txt"
        )

        if language == "python":
            command = ["/work/.check/venv/bin/python", config.get("entry", "app.py"), *config["args"]]
        else:
            command = ["/work/.check/app", *config["args"]]
        smoke_config = {"command": command, "cwd": "/work", "expect_any": config["expect_any"]}
        (work / ".check/smoke.json").write_text(json.dumps(smoke_config))
        checker = Path(__file__).resolve()
        # Timing checks run one at a time so concurrent builds cannot slow a launch.
        with smoke_lock:
            code, output, _ = run_container(
                RUNTIME,
                "python3 /checker/checker.py smoke /work/.check/smoke.json /work/.check/smoke-result.json",
                work, False, SMOKE_TIMEOUT, extra_mounts=[(checker, "/checker/checker.py")],
                limits=["--cpus", "2", "--memory", "2g", "--pids-limit", "512"],
            )
        result_path = work / ".check/smoke-result.json"
        if code != 0 or not result_path.is_file():
            (trial_dir / "smoke.log").write_text(output)
            note = f"smoke driver failed (exit {code}): {tail(output)}"
            return [(True, build_note)] + [(False, note) for _ in CHECKS[1:]]
        result = json.loads(result_path.read_text())
    (trial_dir / "smoke.json").write_text(json.dumps(result, indent=2) + "\n")
    verdicts = result["verdicts"]
    return [(True, build_note)] + [(verdicts[name]["passed"], verdicts[name]["note"]) for name in CHECKS[1:]]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    subcommands = parser.add_subparsers(dest="command")
    smoke_parser = subcommands.add_parser("smoke", help="(inside the runtime container) drive one program in a PTY")
    smoke_parser.add_argument("config", type=Path)
    smoke_parser.add_argument("output", type=Path)
    parser.add_argument("--run", type=Path)
    parser.add_argument("--jobs", type=int, default=2, help="trials to fetch and build concurrently")
    args = parser.parse_args()
    if args.command == "smoke":
        return smoke_main(args.config, args.output)
    if not args.run:
        parser.error("--run is required")

    repo_root = Path(__file__).resolve().parents[2]
    run_dir = args.run.resolve().parent
    manifest = json.loads(args.run.read_text())
    eval_path = repo_root / manifest["eval_set"]
    if hashlib.sha256(eval_path.read_bytes()).hexdigest() != manifest["eval_set_sha256"]:
        raise SystemExit(f"{eval_path} does not match the run's eval_set_sha256; check out the run's commit")
    cases = {str(case["id"]): case for case in json.loads(eval_path.read_text())["evals"]}
    for case in cases.values():
        if "build_check" not in case or len(case["assertions"]) != len(CHECKS):
            raise SystemExit(f"case {case['id']!r} needs a build_check object and {len(CHECKS)} assertions")

    ensure_images()
    tools = tool_versions()
    checker_copy = run_dir / "checker.py"
    shutil.copyfile(Path(__file__).resolve(), checker_copy)
    digest = hashlib.sha256(checker_copy.read_bytes()).hexdigest()
    checks_dir = run_dir / "checks"
    checks_dir.mkdir(exist_ok=True)
    smoke_lock = threading.Lock()

    def grade(trial):
        case = cases[str(trial["case_id"])]
        response = (run_dir / trial["response_file"]).read_text()
        results = grade_trial(trial, case, response, checks_dir, smoke_lock)
        print(f"checked {trial['trial_id']}: {sum(passed for passed, _ in results)}/{len(results)}", file=sys.stderr)
        return {
            "trial_id": trial["trial_id"],
            "assertions": [{"index": index, "passed": passed, "notes": note} for index, (passed, note) in enumerate(results)],
        }

    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        trials = list(pool.map(grade, manifest["trials"]))

    grades = {
        "schema_version": 6,
        "schema": GRADES_SCHEMA_V6,
        "artifact_type": "tui-design-eval-grades",
        "run_id": manifest["run_id"],
        "grader": {
            "kind": "automated",
            "name": "build and pseudo-terminal checker",
            "prompt_version": CHECKER_VERSION,
            "prompt_sha256": digest,
            "tools": tools,
        },
        "grading_prompt": {"path": "checker.py", "sha256": digest},
        "trials": trials,
    }
    (run_dir / "grades.json").write_text(json.dumps(grades, indent=2) + "\n")
    print(run_dir / "grades.json")
    return 0


# ---------------------------------------------------------------------------
# Terminal emulator (container): enough of xterm to read the screen back.

CSI = re.compile(r"\x1b\[([\x30-\x3f]*)([\x20-\x2f]*)([\x40-\x7e])")
CSI_PARTIAL = re.compile(r"\x1b\[[\x30-\x3f]*[\x20-\x2f]*\Z")
OSC = re.compile(r"\x1b\]([^\x07\x1b]*)(?:\x07|\x1b\\)")
STRING = re.compile(r"\x1b[PX^_].*?\x1b\\", re.DOTALL)
ESCAPE = re.compile(r"\x1b([\x20-\x2f]*)([\x30-\x7e])")
# Basic SGR colors with a hue; black, white, and their bright forms are grays.
CHROMATIC_SGR = set(range(31, 37)) | set(range(41, 47)) | set(range(91, 97)) | set(range(101, 107))
# 256-color indexes that are gray: black/white/grays of the 16, the cube's diagonal, and the gray ramp.
GRAY_INDEXES = {0, 7, 8, 15, 16, 59, 102, 145, 188, 231} | set(range(232, 256))
TRACKED_MODES = {
    47: "alternate screen (47)", 1047: "alternate screen (1047)", 1049: "alternate screen (1049)",
    1000: "mouse tracking (1000)", 1002: "mouse tracking (1002)", 1003: "mouse tracking (1003)",
    1005: "mouse encoding (1005)", 1006: "mouse encoding (1006)", 1015: "mouse encoding (1015)",
    1016: "mouse encoding (1016)", 1004: "focus events (1004)", 2004: "bracketed paste (2004)",
}


def char_width(char):
    if unicodedata.combining(char) or unicodedata.category(char) in ("Mn", "Me", "Cf"):
        return 0
    return 2 if unicodedata.east_asian_width(char) in ("W", "F") else 1


class Terminal:
    """A small VT emulator: cursor movement, erase, scroll regions, alternate screen, and query replies."""

    def __init__(self, cols, rows, reply):
        self.cols, self.rows, self.reply = cols, rows, reply
        self.main = self.blank(rows, cols)
        self.alt = self.blank(rows, cols)
        self.grid = self.main
        self.x = self.y = 0
        self.saved = (0, 0)
        self.wrap_pending = False
        self.autowrap = True
        self.top, self.bottom = 0, rows - 1
        self.modes = {}
        self.cursor_visible = True
        self.cursor_hidden_ever = False
        self.kitty_depth = 0
        self.modify_other_keys = 0
        self.color_sgr = []
        self.pending = ""
        self.decoder = codecs.getincrementaldecoder("utf-8")("replace")

    @staticmethod
    def blank(rows, cols):
        return [[" "] * cols for _ in range(rows)]

    def resize(self, cols, rows):
        was_alt = self.grid is self.alt
        for name in ("main", "alt"):
            old = getattr(self, name)
            new = self.blank(rows, cols)
            for y in range(min(rows, len(old))):
                for x in range(min(cols, len(old[y]))):
                    new[y][x] = old[y][x]
            setattr(self, name, new)
        self.grid = self.alt if was_alt else self.main
        self.cols, self.rows = cols, rows
        self.top, self.bottom = 0, rows - 1
        self.x, self.y = min(self.x, cols - 1), min(self.y, rows - 1)
        self.wrap_pending = False

    def text(self):
        return "\n".join("".join(cell for cell in row).rstrip() for row in self.grid).rstrip("\n")

    def feed(self, data):
        self.pending += self.decoder.decode(data)
        text, self.pending = self.pending, ""
        index = 0
        length = len(text)
        while index < length:
            char = text[index]
            if char == "\x1b":
                consumed = self.escape(text, index)
                if consumed is None:
                    self.pending = text[index:]
                    if len(self.pending) > 65536:
                        self.pending = ""
                    return
                index += consumed
            elif char < " " or char == "\x7f":
                self.control(char)
                index += 1
            else:
                end = index
                while end < length and text[end] >= " " and text[end] not in "\x1b\x7f":
                    end += 1
                for item in text[index:end]:
                    self.put(item)
                index = end

    def escape(self, text, index):
        if index + 1 >= len(text):
            return None
        kind = text[index + 1]
        if kind == "[":
            match = CSI.match(text, index)
            if match:
                self.csi(*match.groups())
                return match.end() - index
            return None if CSI_PARTIAL.match(text, index) else 1
        if kind == "]":
            match = OSC.match(text, index)
            if match:
                self.osc(match.group(1))
                return match.end() - index
            return None if "\x07" not in text[index:] and "\x1b\\" not in text[index:] else 1
        if kind in "PX^_":
            match = STRING.match(text, index)
            return match.end() - index if match else None
        match = ESCAPE.match(text, index)
        if not match:
            return None if re.match(r"\x1b[\x20-\x2f]*\Z", text[index:]) else 1
        intermediate, final = match.groups()
        if not intermediate:
            if final == "7":
                self.saved = (self.x, self.y)
            elif final == "8":
                self.x, self.y = self.saved
                self.wrap_pending = False
            elif final == "M":
                self.reverse_index()
            elif final == "D":
                self.index()
            elif final == "E":
                self.x = 0
                self.index()
            elif final == "c":
                self.__init__(self.cols, self.rows, self.reply)
        return match.end() - index

    def control(self, char):
        if char == "\r":
            self.x = 0
            self.wrap_pending = False
        elif char in "\n\x0b\x0c":
            self.index()
        elif char == "\b":
            self.x = max(0, self.x - 1)
            self.wrap_pending = False
        elif char == "\t":
            self.x = min(self.cols - 1, (self.x // 8 + 1) * 8)

    def index(self):
        self.wrap_pending = False
        if self.y == self.bottom:
            self.scroll_up(1)
        elif self.y < self.rows - 1:
            self.y += 1

    def reverse_index(self):
        self.wrap_pending = False
        if self.y == self.top:
            self.scroll_down(1)
        elif self.y > 0:
            self.y -= 1

    def scroll_up(self, count):
        for _ in range(min(count, self.bottom - self.top + 1)):
            del self.grid[self.top]
            self.grid.insert(self.bottom, [" "] * self.cols)

    def scroll_down(self, count):
        for _ in range(min(count, self.bottom - self.top + 1)):
            del self.grid[self.bottom]
            self.grid.insert(self.top, [" "] * self.cols)

    def put(self, char):
        width = char_width(char)
        if width == 0:
            return
        if self.wrap_pending and self.autowrap:
            self.x = 0
            self.index()
        if width == 2 and self.x == self.cols - 1:
            if not self.autowrap:
                return
            self.grid[self.y][self.x] = " "
            self.x = 0
            self.index()
        self.grid[self.y][self.x] = char
        if width == 2:
            self.grid[self.y][self.x + 1] = ""
        if self.x + width >= self.cols:
            self.x = self.cols - 1
            self.wrap_pending = True
        else:
            self.x += width
            self.wrap_pending = False

    def erase(self, y, start, end):
        row = self.grid[y]
        for x in range(max(0, start), min(self.cols, end)):
            row[x] = " "

    def csi(self, params, intermediate, final):
        prefix = params[:1] if params[:1] in ("?", ">", "<", "=") else ""
        body = params[len(prefix):]
        numbers = []
        for part in body.split(";") if body else []:
            head = part.split(":")[0]
            numbers.append(int(head) if head.isdigit() else 0)

        def arg(position, default=1):
            value = numbers[position] if position < len(numbers) else 0
            return value if value else default

        if prefix == "?" and final in "hl" and not intermediate:
            for mode in numbers:
                self.set_mode(mode, final == "h")
            return
        if prefix == "?" and intermediate == "$" and final == "p":
            self.reply(f"\x1b[?{arg(0, 0)};0$y")
            return
        if prefix == ">" and final == "u":
            self.kitty_depth += 1
            return
        if prefix == "<" and final == "u":
            self.kitty_depth = max(0, self.kitty_depth - arg(0))
            return
        if prefix == ">" and final == "m":
            if numbers[:1] == [4]:
                self.modify_other_keys = numbers[1] if len(numbers) > 1 else 0
            return
        if prefix == ">" and final == "c":
            self.reply("\x1b[>1;10;0c")
            return
        if prefix or intermediate:
            return
        if final == "m":
            self.sgr(body)
        elif final == "c":
            self.reply("\x1b[?62;22c")
        elif final == "n":
            if arg(0, 0) == 6:
                self.reply(f"\x1b[{self.y + 1};{self.x + 1}R")
            elif arg(0, 0) == 5:
                self.reply("\x1b[0n")
        elif final in "Hf":
            self.y = min(self.rows - 1, arg(0) - 1)
            self.x = min(self.cols - 1, arg(1) - 1)
            self.wrap_pending = False
        elif final == "A":
            self.y = max(0, self.y - arg(0))
            self.wrap_pending = False
        elif final in "Be":
            self.y = min(self.rows - 1, self.y + arg(0))
            self.wrap_pending = False
        elif final in "Ca":
            self.x = min(self.cols - 1, self.x + arg(0))
            self.wrap_pending = False
        elif final == "D":
            self.x = max(0, self.x - arg(0))
            self.wrap_pending = False
        elif final == "E":
            self.y = min(self.rows - 1, self.y + arg(0))
            self.x = 0
            self.wrap_pending = False
        elif final == "F":
            self.y = max(0, self.y - arg(0))
            self.x = 0
            self.wrap_pending = False
        elif final in "G`":
            self.x = min(self.cols - 1, arg(0) - 1)
            self.wrap_pending = False
        elif final == "d":
            self.y = min(self.rows - 1, arg(0) - 1)
            self.wrap_pending = False
        elif final == "K":
            mode = arg(0, 0)
            start, end = {0: (self.x, self.cols), 1: (0, self.x + 1), 2: (0, self.cols)}.get(mode, (0, 0))
            self.erase(self.y, start, end)
        elif final == "J":
            mode = arg(0, 0)
            if mode == 0:
                self.erase(self.y, self.x, self.cols)
                for y in range(self.y + 1, self.rows):
                    self.erase(y, 0, self.cols)
            elif mode == 1:
                for y in range(0, self.y):
                    self.erase(y, 0, self.cols)
                self.erase(self.y, 0, self.x + 1)
            elif mode in (2, 3):
                for y in range(self.rows):
                    self.erase(y, 0, self.cols)
        elif final == "X":
            self.erase(self.y, self.x, self.x + arg(0))
        elif final == "@":
            row = self.grid[self.y]
            count = min(arg(0), self.cols - self.x)
            row[self.x:] = ([" "] * count + row[self.x:])[: self.cols - self.x]
        elif final == "P":
            row = self.grid[self.y]
            count = min(arg(0), self.cols - self.x)
            row[self.x:] = row[self.x + count:] + [" "] * count
        elif final == "L" and self.top <= self.y <= self.bottom:
            for _ in range(min(arg(0), self.bottom - self.y + 1)):
                del self.grid[self.bottom]
                self.grid.insert(self.y, [" "] * self.cols)
        elif final == "M" and self.top <= self.y <= self.bottom:
            for _ in range(min(arg(0), self.bottom - self.y + 1)):
                del self.grid[self.y]
                self.grid.insert(self.bottom, [" "] * self.cols)
        elif final == "S":
            self.scroll_up(arg(0))
        elif final == "T":
            self.scroll_down(arg(0))
        elif final == "b":
            previous = self.grid[self.y][self.x - 1] if self.x > 0 else " "
            for _ in range(min(arg(0), self.cols * self.rows)):
                self.put(previous or " ")
        elif final == "r":
            top, bottom = arg(0) - 1, arg(1, self.rows) - 1
            if 0 <= top < bottom < self.rows:
                self.top, self.bottom = top, bottom
                self.x = self.y = 0
        elif final == "s":
            self.saved = (self.x, self.y)
        elif final == "u":
            self.x, self.y = self.saved

    def set_mode(self, mode, on):
        if mode in (47, 1047, 1049):
            was_alt = self.grid is self.alt
            if mode == 1049 and on and not was_alt:
                self.saved = (self.x, self.y)
            if on and not was_alt:
                self.alt = self.blank(self.rows, self.cols)
                self.grid = self.alt
            elif not on and was_alt:
                self.grid = self.main
                if mode == 1049:
                    self.x, self.y = self.saved
        elif mode == 25:
            self.cursor_visible = on
            self.cursor_hidden_ever = self.cursor_hidden_ever or not on
        elif mode == 7:
            self.autowrap = on
        self.modes[mode] = on

    def sgr(self, body):
        """Record the sequence if it sets a chromatic (non-gray) color; monochrome rendering may still set grays."""
        parts = body.split(";") if body else ["0"]
        index = 0
        while index < len(parts):
            fields = [int(field) if field.isdigit() else 0 for field in parts[index].split(":")]
            value = fields[0]
            if value in CHROMATIC_SGR:
                self.color_sgr.append(body)
                return
            if value in (38, 48, 58):
                if len(fields) > 1:  # colon form: 38:5:n or 38:2:[colorspace:]r:g:b
                    color, index = fields[1:], index + 1
                else:
                    kind = parts[index + 1] if index + 1 < len(parts) else ""
                    width = 2 if kind == "5" else 4 if kind == "2" else 1
                    color = [int(field) if field.isdigit() else 0 for field in parts[index + 1:index + 1 + width]]
                    index += 1 + width
                if color[:1] == [5] and len(color) > 1 and color[1] not in GRAY_INDEXES:
                    self.color_sgr.append(body)
                    return
                if color[:1] == [2] and len(color) >= 4 and len(set(color[-3:])) > 1:
                    self.color_sgr.append(body)
                    return
                continue
            index += 1

    def osc(self, body):
        number, _, value = body.partition(";")
        if value == "?" and number in ("10", "11", "12"):
            color = "ffff/ffff/ffff" if number == "10" else "0000/0000/0000"
            self.reply(f"\x1b]{number};rgb:{color}\x1b\\")

    def left_on(self):
        problems = [label for mode, label in TRACKED_MODES.items() if self.modes.get(mode)]
        if self.cursor_hidden_ever and not self.cursor_visible:
            problems.append("cursor left hidden (25)")
        if self.kitty_depth:
            problems.append(f"keyboard enhancement left pushed ({self.kitty_depth})")
        if self.modify_other_keys:
            problems.append(f"modifyOtherKeys left at {self.modify_other_keys}")
        return problems


# ---------------------------------------------------------------------------
# PTY driver (container)

QUIT_HINT = re.compile(r"(?i)(?<![a-z])q(?![a-z])[^\n]{0,20}\bquit\b|\bquit\b[^\n]{0,20}(?<![a-z])q(?![a-z])")
CRASH = re.compile(r"panic:|panicked at|Traceback \(most recent call last\)|fatal error:|SIGSEGV")
VISIBLE = re.compile(r"[^\s\x00-\x1f]")


def visible_text(data):
    text = data.decode("utf-8", "replace")
    text = OSC.sub("", STRING.sub("", text))
    return ESCAPE.sub("", CSI.sub("", text))


class Session:
    def __init__(self, config, cols, rows, extra_env=None):
        self.master, self.slave = os.openpty()
        self.set_size(cols, rows)
        # Read line settings through the master: it reaches the same tty on Linux and macOS, and macOS
        # revokes the slave descriptor once the program's session ends.
        self.before = termios.tcgetattr(self.master)
        self.terminal = Terminal(cols, rows, self.reply)
        self.output = bytearray()
        self.chunks = []
        env = {
            "PATH": "/usr/local/bin:/usr/bin:/bin",
            "HOME": "/root",
            "LANG": "C.UTF-8",
            "TERM": "xterm-256color",
            "COLORTERM": "truecolor",
            **(extra_env or {}),
        }
        self.started = time.monotonic()
        self.process = subprocess.Popen(
            config["command"], cwd=config["cwd"], env=env, stdin=self.slave, stdout=self.slave, stderr=self.slave,
            start_new_session=True, preexec_fn=lambda: fcntl.ioctl(0, termios.TIOCSCTTY, 0), close_fds=True,
        )
        flags = fcntl.fcntl(self.master, fcntl.F_GETFL)
        fcntl.fcntl(self.master, fcntl.F_SETFL, flags | os.O_NONBLOCK)

    def elapsed(self):
        return time.monotonic() - self.started

    def set_size(self, cols, rows):
        fcntl.ioctl(self.master, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))

    def resize(self, cols, rows):
        self.terminal.resize(cols, rows)
        self.set_size(cols, rows)

    def reply(self, text):
        try:
            os.write(self.master, text.encode())
        except OSError:
            pass

    def send(self, data):
        os.write(self.master, data)

    def pump(self, seconds):
        """Read output for up to `seconds`; return True if any arrived."""
        deadline = time.monotonic() + seconds
        got = False
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return got
            ready, _, _ = select.select([self.master], [], [], remaining)
            if not ready:
                return got
            try:
                data = os.read(self.master, 65536)
            except (BlockingIOError, InterruptedError):
                continue
            except OSError:
                return got
            if not data:
                return got
            got = True
            self.output += data
            self.chunks.append((self.elapsed(), len(data)))
            self.terminal.feed(data)

    def alive(self):
        return self.process.poll() is None

    def has_screen(self):
        return bool(VISIBLE.search(self.terminal.text()))

    def wait_screen(self, limit):
        """Pump until the screen shows something or `limit` seconds after launch; return the time or None."""
        while self.elapsed() < limit:
            self.pump(min(0.05, max(0.0, limit - self.elapsed())))
            if self.has_screen():
                return self.elapsed()
            if not self.alive():
                self.pump(0.1)
                return self.elapsed() if self.has_screen() else None
        return None

    def settle(self, cap, quiet=0.4):
        """Pump until no output for `quiet` seconds, or `cap` seconds from now."""
        deadline = time.monotonic() + cap
        while time.monotonic() < deadline:
            if not self.pump(min(quiet, max(0.0, deadline - time.monotonic()))):
                return

    def wait_exit(self, limit):
        deadline = time.monotonic() + limit
        while time.monotonic() < deadline:
            self.pump(0.05)
            if not self.alive():
                self.pump(0.2)
                return self.process.returncode
        return None

    def restore_problems(self):
        problems = []
        after = termios.tcgetattr(self.master)
        if after != self.before:
            changed = [name for name, a, b in zip(("iflag", "oflag", "cflag", "lflag", "ispeed", "ospeed", "cc"), self.before, after) if a != b]
            problems.append("line settings differ from before launch (" + ", ".join(changed) + ")")
        return problems + self.terminal.left_on()

    def close(self):
        if self.alive():
            for sig in (signal.SIGTERM, signal.SIGKILL):
                try:
                    os.killpg(self.process.pid, sig)
                except ProcessLookupError:
                    break
                try:
                    self.process.wait(1.0)
                    break
                except subprocess.TimeoutExpired:
                    continue
        os.close(self.master)
        os.close(self.slave)

    def record(self, screens):
        return {
            "screens": screens,
            "output_bytes": len(self.output),
            "output_head": self.output[:16384].decode("utf-8", "replace"),
            "exit_code": self.process.returncode,
        }


def describe_exit(code):
    return "still running" if code is None else f"exited {code}" if code >= 0 else f"killed by signal {-code}"


def scenario_main(config):
    """80x24 launch: starts, shows data, names quit, redraws at 60x20, then q."""
    verdicts, screens = {}, {}
    session = Session(config, 80, 24)
    try:
        shown_at = session.wait_screen(3.0)
        running = session.alive()
        if shown_at is not None and running:
            verdicts["starts"] = (True, f"drew a non-empty screen {shown_at:.2f} s after launch and kept running")
        elif shown_at is None:
            verdicts["starts"] = (False, f"no visible screen within 3 s ({describe_exit(session.process.poll())}): {tail(visible_text(session.output), 300)!r}")
        else:
            verdicts["starts"] = (False, f"drew a screen but then {describe_exit(session.process.poll())}: {tail(visible_text(session.output), 300)!r}")
        session.settle(cap=5.0)
        first = session.terminal.text()
        screens["first_80x24"] = first
        found = [item for item in config["expect_any"] if item in first]
        verdicts["shows_data"] = (
            (True, f"first settled screen shows {found[0]!r}") if found
            else (False, "first settled screen shows none of the data file's items")
        )
        hint = QUIT_HINT.search(first)
        verdicts["names_quit_key"] = (
            (True, f"first screen shows {hint.group(0).strip()!r}") if hint
            else (False, "first screen shows no q next to the word quit")
        )
        if not session.alive():
            note = f"not checked: the program had {describe_exit(session.process.returncode)} before the resize"
            verdicts["redraws_on_resize"] = (False, note)
            verdicts["q_quits"] = (False, note)
            verdicts["q_restores"] = (False, note)
            return verdicts, session.record(screens)
        mark = len(session.output)
        session.resize(60, 20)
        resized = time.monotonic()
        redrew_at = None
        while time.monotonic() - resized < 1.5:
            session.pump(0.05)
            if VISIBLE.search(visible_text(bytes(session.output[mark:]))):
                redrew_at = time.monotonic() - resized
                break
        verdicts["redraws_on_resize"] = (
            (True, f"wrote visible output {redrew_at:.2f} s after the resize to 60x20") if redrew_at is not None
            else (False, f"no visible output within 1.5 s of the resize to 60x20 ({describe_exit(session.process.poll())})")
        )
        session.settle(cap=2.0)
        screens["after_60x20"] = session.terminal.text()
        if not session.alive():
            note = f"not checked: the program {describe_exit(session.process.returncode)} after the resize"
            verdicts["q_quits"] = (False, note)
            verdicts["q_restores"] = (False, note)
            return verdicts, session.record(screens)
        pressed = time.monotonic()
        session.send(b"q")
        code = session.wait_exit(2.0)
        if code is None:
            verdicts["q_quits"] = (False, "still running 2 s after q")
            verdicts["q_restores"] = (False, "not checked: q did not quit")
        else:
            took = time.monotonic() - pressed
            verdicts["q_quits"] = (code == 0, f"exited {code} {took:.2f} s after q")
            problems = session.restore_problems()
            verdicts["q_restores"] = (
                (False, "after q: " + "; ".join(problems)) if problems
                else (True, "after q: line settings match launch; alternate screen, mouse, paste, focus and keyboard modes off; cursor visible")
            )
        screens["after_exit"] = session.terminal.text()
        return verdicts, session.record(screens)
    finally:
        session.close()


def scenario_tiny(config):
    session = Session(config, 80, 24)
    try:
        session.wait_screen(3.0)
        session.settle(cap=5.0)
        if not session.alive():
            return (False, f"not checked: the program {describe_exit(session.process.returncode)} before the resize"), session.record({})
        mark = len(session.output)
        session.resize(20, 6)
        session.pump(1.0)
        screen = session.terminal.text()
        after = visible_text(bytes(session.output[mark:]))
        crash = CRASH.search(after) or CRASH.search(screen)
        if not session.alive():
            evidence = f"printed {crash.group(0)!r}: " if crash else ""
            verdict = (False, f"{describe_exit(session.process.returncode)} within 1 s of the resize to 20x6; {evidence}{tail(after, 300)!r}")
        elif crash:
            verdict = (False, f"still running 1 s after the resize to 20x6, but printed {crash.group(0)!r}")
        else:
            verdict = (True, "still running 1 s after the resize to 20x6, with no panic or traceback")
        return verdict, session.record({"after_20x6": screen})
    finally:
        session.close()


def scenario_ctrl_c(config):
    session = Session(config, 80, 24)
    try:
        session.wait_screen(3.0)
        session.settle(cap=5.0)
        if not session.alive():
            return (False, f"not checked: the program {describe_exit(session.process.returncode)} before Ctrl+C"), session.record({})
        pressed = time.monotonic()
        session.send(b"\x03")
        code = session.wait_exit(2.0)
        if code is None:
            return (False, "still running 2 s after Ctrl+C"), session.record({"after_ctrl_c": session.terminal.text()})
        took = time.monotonic() - pressed
        problems = session.restore_problems()
        if problems:
            verdict = (False, f"{describe_exit(code)} {took:.2f} s after Ctrl+C, but: " + "; ".join(problems))
        else:
            verdict = (True, f"{describe_exit(code)} {took:.2f} s after Ctrl+C with the terminal restored")
        return verdict, session.record({"after_exit": session.terminal.text()})
    finally:
        session.close()


def scenario_no_color(config):
    session = Session(config, 80, 24, {"NO_COLOR": "1"})
    try:
        shown_at = session.wait_screen(3.0)
        session.pump(max(0.0, 3.0 - session.elapsed()))
        colors = session.terminal.color_sgr
        if shown_at is None:
            verdict = (False, f"no visible screen within 3 s with NO_COLOR=1 ({describe_exit(session.process.poll())})")
        elif colors:
            verdict = (False, f"set a chromatic color {len(colors)} times in its first 3 s with NO_COLOR=1, first SGR {colors[0]!r}")
        else:
            verdict = (True, f"drew a screen at {shown_at:.2f} s and set no chromatic color in its first 3 s with NO_COLOR=1")
        return verdict, session.record({"no_color_80x24": session.terminal.text()})
    finally:
        session.close()


def smoke_main(config_path, output_path):
    config = json.loads(config_path.read_text())
    verdicts, transcripts = {}, {}
    main_verdicts, transcripts["main"] = scenario_main(config)
    verdicts.update(main_verdicts)
    verdicts["survives_tiny"], transcripts["tiny"] = scenario_tiny(config)
    verdicts["ctrl_c_quits_and_restores"], transcripts["ctrl_c"] = scenario_ctrl_c(config)
    verdicts["honors_no_color"], transcripts["no_color"] = scenario_no_color(config)
    missing = [name for name in CHECKS[1:] if name not in verdicts]
    if missing:
        raise SystemExit(f"checks without a verdict: {missing}")
    result = {
        "checker": CHECKER_VERSION,
        "verdicts": {name: {"passed": bool(passed), "note": note} for name, (passed, note) in verdicts.items()},
        "transcripts": transcripts,
    }
    output_path.write_text(json.dumps(result, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
