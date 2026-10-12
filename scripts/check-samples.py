#!/usr/bin/env python3
"""Extract checked code samples from the skill and render their harnesses.

A fence in SKILL.md or a reference opts in by adding a ``check=<harness>/<name>``
word to its info string::

    ```go check=go/counter

Each marked sample must appear in at least one placeholder line inside a
``*.tmpl`` file under ``tests/samples/<harness>/``::

    <<sample go/counter>>
    <<sample go/fetch-cmd until="// In Update">>

Rendering copies each harness to the output directory and replaces every
placeholder with the sample's text, indented to the placeholder's column, so
wrapper code (imports, ``main``, stub types) stays in the harness and the
published sample stays short. Placeholder options select part of a sample by
line prefix (compared after stripping indentation), so one fence that mixes
declarations and a statement fragment can be split across wrapper code:

    from="PREFIX"   start at the first line with PREFIX (inclusive)
    until="PREFIX"  stop before the first later line with PREFIX
    drop="PREFIX"   remove every line with PREFIX (repeatable)

A prefix that matches nothing is an error, so edits to a sample cannot
silently change what its template checks. ``scripts/check-samples.sh`` then builds and tests
the rendered projects. Unmarked fences are ignored.

Usage:
  check-samples.py list
  check-samples.py verify
  check-samples.py render --out DIR [HARNESS ...]
"""

import argparse
import re
import shlex
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = REPO_ROOT / "plugins/tui-design/skills/tui-design"
HARNESS_ROOT = REPO_ROOT / "tests/samples"

SAMPLE_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*/[a-z0-9]+(?:-[a-z0-9]+)*")
FENCE_OPEN = re.compile(r"^(?P<indent>[ \t]*)(?P<fence>`{3,}|~{3,})(?P<info>.*)$")
PLACEHOLDER = re.compile(r"^(?P<indent>[ \t]*)<<sample (?P<spec>[^\n]+?)>>[ \t]*$")
PLACEHOLDER_OPTIONS = {"from", "until", "drop"}
TEMPLATE_SUFFIX = ".tmpl"
# Build products and caches inside a harness directory are never copied.
IGNORED_NAMES = {"node_modules", "target", ".venv", "__pycache__", ".pytest_cache"}


class SampleError(Exception):
    """A marker, fence, or template problem that blocks rendering."""


@dataclass(frozen=True)
class Sample:
    id: str
    source: Path
    line: int  # 1-based line of the opening fence
    text: str

    @property
    def harness(self) -> str:
        return self.id.split("/", 1)[0]


@dataclass(frozen=True)
class Placeholder:
    id: str
    template: Path
    line: int
    indent: str
    options: Tuple[Tuple[str, str], ...] = ()

    @property
    def location(self) -> str:
        return f"{_relative(self.template)}:{self.line}"


def parse_placeholder(line: str, template: Path, number: int) -> Optional[Placeholder]:
    """Parse a ``<<sample ID [option="prefix" ...]>>`` line, or return None."""
    match = PLACEHOLDER.match(line)
    if not match:
        return None
    location = f"{_relative(template)}:{number}"
    try:
        words = shlex.split(match.group("spec"))
    except ValueError as error:
        raise SampleError(f"{location}: cannot parse placeholder: {error}") from None
    options: List[Tuple[str, str]] = []
    for word in words[1:]:
        key, separator, value = word.partition("=")
        if not separator or key not in PLACEHOLDER_OPTIONS or not value:
            raise SampleError(
                f"{location}: invalid placeholder option {word!r}; use from=, until=, or drop= with a quoted prefix"
            )
        if key != "drop" and any(existing == key for existing, _ in options):
            raise SampleError(f"{location}: placeholder repeats {key}=")
        options.append((key, value))
    return Placeholder(words[0], template, number, match.group("indent"), tuple(options))


def select_lines(sample: "Sample", placeholder: Placeholder) -> List[str]:
    """Apply a placeholder's from/until/drop options to a sample's lines."""
    lines = sample.text.splitlines()
    for key, prefix in placeholder.options:
        if key == "from":
            starts = [index for index, line in enumerate(lines) if line.strip().startswith(prefix)]
            if not starts:
                raise SampleError(f"{placeholder.location}: from={prefix!r} matches no line of {sample.id}")
            lines = lines[starts[0]:]
    for key, prefix in placeholder.options:
        if key == "until":
            ends = [index for index, line in enumerate(lines) if index and line.strip().startswith(prefix)]
            if not ends:
                raise SampleError(f"{placeholder.location}: until={prefix!r} matches no line of {sample.id}")
            lines = lines[: ends[0]]
    for key, prefix in placeholder.options:
        if key == "drop":
            kept = [line for line in lines if not line.strip().startswith(prefix)]
            if len(kept) == len(lines):
                raise SampleError(f"{placeholder.location}: drop={prefix!r} matches no line of {sample.id}")
            lines = kept
    # Trim blank edges left by a split so wrappers control spacing.
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    if not lines:
        raise SampleError(f"{placeholder.location}: options select no lines of {sample.id}")
    return lines


def skill_markdown_files(skill_dir: Path = SKILL_DIR) -> List[Path]:
    return [skill_dir / "SKILL.md", *sorted((skill_dir / "references").glob("*.md"))]


def _relative(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def parse_fences(path: Path) -> List[Sample]:
    """Return the marked samples in one Markdown file."""
    lines = path.read_text(encoding="utf-8").splitlines()
    samples: List[Sample] = []
    index = 0
    while index < len(lines):
        opening = FENCE_OPEN.match(lines[index])
        if not opening:
            index += 1
            continue
        indent = opening.group("indent")
        fence = opening.group("fence")
        words = opening.group("info").split()
        markers = [word[len("check="):] for word in words if word.startswith("check=")]
        start = index
        index += 1
        body: List[str] = []
        closed = False
        while index < len(lines):
            line = lines[index]
            stripped = line.strip()
            if stripped.startswith(fence[0] * len(fence)) and set(stripped) == {fence[0]}:
                closed = True
                index += 1
                break
            # Content inside an indented (list-item) fence carries the fence's indent.
            body.append(line[len(indent):] if line.startswith(indent) else line.lstrip())
            index += 1
        location = f"{_relative(path)}:{start + 1}"
        if not markers:
            continue
        if not closed:
            raise SampleError(f"{location}: marked fence is never closed")
        if len(markers) > 1:
            raise SampleError(f"{location}: fence has more than one check= marker")
        sample_id = markers[0]
        if not SAMPLE_ID.fullmatch(sample_id):
            raise SampleError(
                f"{location}: invalid sample id {sample_id!r}; use <harness>/<name> in lowercase kebab-case"
            )
        samples.append(Sample(sample_id, path, start + 1, "\n".join(body)))
    return samples


def collect_samples(paths: Iterable[Path]) -> Dict[str, Sample]:
    samples: Dict[str, Sample] = {}
    for path in paths:
        for sample in parse_fences(path):
            previous = samples.get(sample.id)
            if previous is not None:
                raise SampleError(
                    f"duplicate sample id {sample.id}: {_relative(previous.source)}:{previous.line} "
                    f"and {_relative(sample.source)}:{sample.line}"
                )
            samples[sample.id] = sample
    return samples


def harness_names(harness_root: Path = HARNESS_ROOT) -> List[str]:
    if not harness_root.is_dir():
        return []
    return sorted(
        path.name
        for path in harness_root.iterdir()
        if path.is_dir() and not path.name.startswith(".") and path.name not in IGNORED_NAMES
    )


def _harness_files(directory: Path) -> Iterable[Path]:
    for path in sorted(directory.rglob("*")):
        if any(part in IGNORED_NAMES for part in path.relative_to(directory).parts):
            continue
        if path.is_file():
            yield path


def collect_placeholders(harness_root: Path = HARNESS_ROOT) -> List[Placeholder]:
    placeholders: List[Placeholder] = []
    for harness in harness_names(harness_root):
        for path in _harness_files(harness_root / harness):
            if not path.name.endswith(TEMPLATE_SUFFIX):
                continue
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                placeholder = parse_placeholder(line, path, number)
                if placeholder is not None:
                    placeholders.append(placeholder)
    return placeholders


def verify(
    samples: Dict[str, Sample],
    placeholders: Sequence[Placeholder],
    harness_root: Path = HARNESS_ROOT,
) -> List[str]:
    """Return every consistency error between markers and harness templates."""
    errors: List[str] = []
    harnesses = set(harness_names(harness_root))
    used = {placeholder.id for placeholder in placeholders}
    for sample in sorted(samples.values(), key=lambda item: item.id):
        location = f"{_relative(sample.source)}:{sample.line}"
        if sample.harness not in harnesses:
            errors.append(
                f"{location}: sample {sample.id} has no harness directory "
                f"{_relative(harness_root / sample.harness)}"
            )
        elif sample.id not in used:
            errors.append(
                f"{location}: sample {sample.id} is not used by any *{TEMPLATE_SUFFIX} file in "
                f"{_relative(harness_root / sample.harness)}"
            )
    for placeholder in placeholders:
        harness = placeholder.template.relative_to(harness_root).parts[0]
        if placeholder.id not in samples:
            errors.append(f"{placeholder.location}: placeholder references unknown sample {placeholder.id}")
        elif placeholder.id.split("/", 1)[0] != harness:
            errors.append(f"{placeholder.location}: sample {placeholder.id} belongs to another harness than {harness}")
        else:
            try:
                select_lines(samples[placeholder.id], placeholder)
            except SampleError as error:
                errors.append(str(error))
    return errors


def render_template(
    text: str, samples: Dict[str, Sample], template: Path = Path("<template>")
) -> Tuple[str, List[Tuple[str, int, int]]]:
    """Fill placeholders; return the text and (id, first, last) rendered line spans."""
    output: List[str] = []
    spans: List[Tuple[str, int, int]] = []
    for number, line in enumerate(text.splitlines(), start=1):
        placeholder = parse_placeholder(line, template, number)
        if placeholder is None:
            output.append(line)
            continue
        if placeholder.id not in samples:
            raise SampleError(f"{placeholder.location}: placeholder references unknown sample {placeholder.id}")
        first = len(output) + 1
        output.extend(
            placeholder.indent + body_line if body_line.strip() else ""
            for body_line in select_lines(samples[placeholder.id], placeholder)
        )
        spans.append((placeholder.id, first, len(output)))
    return "\n".join(output) + "\n", spans


def render(
    samples: Dict[str, Sample],
    out_dir: Path,
    harnesses: Optional[Sequence[str]] = None,
    harness_root: Path = HARNESS_ROOT,
) -> List[str]:
    """Render harnesses into out_dir and return a source-map line per placed sample."""
    available = harness_names(harness_root)
    selected = list(harnesses) if harnesses else available
    unknown = sorted(set(selected) - set(available))
    if unknown:
        raise SampleError(f"unknown harness: {', '.join(unknown)} (available: {', '.join(available)})")
    source_map: List[str] = []
    for harness in selected:
        source = harness_root / harness
        target = out_dir / harness
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True)
        for path in _harness_files(source):
            relative = path.relative_to(source)
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            if not path.name.endswith(TEMPLATE_SUFFIX):
                shutil.copy2(path, destination)
                continue
            destination = destination.with_name(path.name[: -len(TEMPLATE_SUFFIX)])
            text, spans = render_template(path.read_text(encoding="utf-8"), samples, path)
            destination.write_text(text, encoding="utf-8")
            for sample_id, first, last in spans:
                sample = samples[sample_id]
                source_map.append(
                    f"{sample_id}  {_relative(sample.source)}:{sample.line}  ->  "
                    f"{harness}/{relative.with_name(destination.name).as_posix()}:{first}-{last}"
                )
    return source_map


def load(
    harnesses: Optional[Sequence[str]] = None,
    skill_dir: Path = SKILL_DIR,
    harness_root: Path = HARNESS_ROOT,
) -> Tuple[Dict[str, Sample], List[Placeholder]]:
    """Collect and verify samples, limited to the given harnesses when named."""
    samples = collect_samples(skill_markdown_files(skill_dir))
    placeholders = collect_placeholders(harness_root)
    if harnesses:
        selected = set(harnesses)
        samples = {key: sample for key, sample in samples.items() if sample.harness in selected}
        placeholders = [
            item for item in placeholders if item.template.relative_to(harness_root).parts[0] in selected
        ]
    errors = verify(samples, placeholders, harness_root)
    if errors:
        raise SampleError("\n".join(errors))
    return samples, placeholders


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list", help="list marked samples and where they are used")
    commands.add_parser("verify", help="check markers against harness templates")
    render_parser = commands.add_parser("render", help="render harness projects with samples filled in")
    render_parser.add_argument("--out", required=True, type=Path, help="output directory")
    render_parser.add_argument("harness", nargs="*", help="harnesses to render (default: all)")
    args = parser.parse_args(argv)

    try:
        samples, placeholders = load(getattr(args, "harness", None))
        if args.command == "list":
            uses: Dict[str, List[str]] = {}
            for placeholder in placeholders:
                uses.setdefault(placeholder.id, []).append(_relative(placeholder.template))
            for sample in sorted(samples.values(), key=lambda item: item.id):
                print(f"{sample.id}  {_relative(sample.source)}:{sample.line}  {', '.join(sorted(set(uses[sample.id])))}")
        elif args.command == "verify":
            print(f"Verified {len(samples)} checked samples against {len(placeholders)} template placeholders")
        else:
            for line in render(samples, args.out.resolve(), args.harness):
                print(line)
    except SampleError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
