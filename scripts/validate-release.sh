#!/usr/bin/env bash
# Validate release metadata, skill structure, eval tooling, and deterministic output.
# Usage: ./scripts/validate-release.sh [expected-tag]
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
expected_tag="${1:-}"

for command_name in python3 zip unzip cmp; do
  command -v "$command_name" >/dev/null || {
    echo "error: required command not found: $command_name" >&2
    exit 1
  }
done

bash -n "$repo_root/scripts/package-skill.sh"

python3 - "$repo_root" "$expected_tag" <<'PY'
import json
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
expected_tag = sys.argv[2]
skill_dir = root / "plugins/tui-design/skills/tui-design"
skill_file = skill_dir / "SKILL.md"
agent_file = skill_dir / "agents/openai.yaml"
expected_skill_files = {
    "SKILL.md",
    "agents/openai.yaml",
    "references/cli-basics.md",
    "references/ecosystem-go.md",
    "references/ecosystem-python.md",
    "references/ecosystem-rust.md",
    "references/ecosystem-typescript.md",
    "references/exemplar-apps.md",
    "references/interaction-patterns.md",
    "references/visual-patterns.md",
}
expected_skill_dirs = {"agents", "references"}

actual_skill_files = set()
actual_skill_dirs = set()
for path in skill_dir.rglob("*"):
    relative = path.relative_to(skill_dir).as_posix()
    if path.is_symlink():
        raise SystemExit(f"skill source must not contain symlinks: {relative}")
    if path.is_file():
        actual_skill_files.add(relative)
    elif path.is_dir():
        actual_skill_dirs.add(relative)
    else:
        raise SystemExit(f"skill source contains a non-file entry: {relative}")
if actual_skill_files != expected_skill_files:
    missing = sorted(expected_skill_files - actual_skill_files)
    extra = sorted(actual_skill_files - expected_skill_files)
    raise SystemExit(f"skill source file allowlist mismatch; missing={missing}, extra={extra}")
if actual_skill_dirs != expected_skill_dirs:
    missing = sorted(expected_skill_dirs - actual_skill_dirs)
    extra = sorted(actual_skill_dirs - expected_skill_dirs)
    raise SystemExit(f"skill source directory allowlist mismatch; missing={missing}, extra={extra}")

plugin = json.loads((root / "plugins/tui-design/.claude-plugin/plugin.json").read_text())
marketplace = json.loads((root / ".claude-plugin/marketplace.json").read_text())
marketplace_plugins = marketplace.get("plugins", [])
if len(marketplace_plugins) != 1:
    raise SystemExit("marketplace must contain exactly one plugin")
marketplace_plugin = marketplace_plugins[0]
versions = {
    plugin["version"],
    marketplace["version"],
    marketplace_plugin["version"],
}
if len(versions) != 1:
    raise SystemExit(f"manifest versions disagree: {sorted(versions)}")
version = versions.pop()
if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?", version):
    raise SystemExit(f"manifest version is not valid semver: {version!r}")
if marketplace_plugin.get("name") != plugin.get("name") or marketplace_plugin.get("source") != "./plugins/tui-design":
    raise SystemExit("marketplace plugin identity/source does not match the plugin manifest")
expected_version = expected_tag[1:] if expected_tag.startswith("v") else expected_tag
if expected_tag and expected_version != version:
    raise SystemExit(f"tag {expected_tag!r} does not match manifest version {version!r}")

changelog = (root / "CHANGELOG.md").read_text()
if f"## [{version}]" not in changelog:
    raise SystemExit(f"CHANGELOG.md has no section for {version}")

text = skill_file.read_text()
match = re.match(r"\A---\n(.*?)\n---\n", text, flags=re.DOTALL)
if not match:
    raise SystemExit("SKILL.md must begin with YAML frontmatter")
frontmatter_keys = [line.split(":", 1)[0] for line in match.group(1).splitlines() if ":" in line]
if frontmatter_keys != ["name", "description"]:
    raise SystemExit(f"SKILL.md frontmatter keys must be name, description; got {frontmatter_keys}")
if not re.search(r"^name:\s+tui-design$", match.group(1), flags=re.MULTILINE):
    raise SystemExit("SKILL.md frontmatter name must match its directory")
if len(text.splitlines()) > 200:
    raise SystemExit(f"SKILL.md exceeds the 200-line core budget: {len(text.splitlines())}")

if not agent_file.is_file():
    raise SystemExit("skill is missing agents/openai.yaml")
agent_text = agent_file.read_text()
agent_fields = re.findall(r'^  ([a-z_]+): "((?:[^"\\]|\\.)*)"$', agent_text, flags=re.MULTILINE)
if not agent_text.startswith("interface:\n") or [key for key, _ in agent_fields] != [
    "display_name",
    "short_description",
    "default_prompt",
]:
    raise SystemExit("agents/openai.yaml must contain only the generated interface fields")
agent_values = {key: json.loads(f'"{value}"') for key, value in agent_fields}
if not 25 <= len(agent_values["short_description"]) <= 64:
    raise SystemExit("agents/openai.yaml short_description must be 25-64 characters")
if "$tui-design" not in agent_values["default_prompt"]:
    raise SystemExit("agents/openai.yaml default_prompt must explicitly invoke $tui-design")

for relative in sorted(set(re.findall(r"`(references/[^`]+\.md)`", text))):
    if any(marker in relative for marker in "*?["):
        exists = any(skill_dir.glob(relative))
    else:
        exists = (skill_dir / relative).is_file()
    if not exists:
        raise SystemExit(f"SKILL.md references missing file or pattern: {relative}")

markdown_files = [skill_file, *sorted((skill_dir / "references").glob("*.md"))]
for path in markdown_files:
    body = path.read_text()
    if sum(line.startswith("```") for line in body.splitlines()) % 2:
        raise SystemExit(f"unbalanced fenced code block: {path.relative_to(root)}")
    if path != skill_file and len(body.splitlines()) >= 100:
        has_navigation = "**Contents:**" in body[:2500] or "## How to use this file" in body[:2500]
        if not has_navigation:
            raise SystemExit(f"long reference lacks an early contents/index section: {path.relative_to(root)}")

# Exact long paragraphs should have one owner. This is deliberately limited to
# long prose outside code fences so shared labels and short contracts stay legal.
paragraph_owners = {}
for path in markdown_files:
    without_code = re.sub(r"```.*?```", "", path.read_text(), flags=re.DOTALL)
    for paragraph in re.split(r"\n\s*\n", without_code):
        normalized = re.sub(r"\s+", " ", paragraph).strip().lower()
        if len(normalized) < 160:
            continue
        previous = paragraph_owners.get(normalized)
        if previous is not None and previous != path:
            raise SystemExit(
                "duplicated long paragraph across skill files: "
                f"{previous.relative_to(root)} and {path.relative_to(root)}"
            )
        paragraph_owners[normalized] = path

for path in sorted((root / "evals").glob("*.json")):
    data = json.loads(path.read_text())
    if data.get("skill_name") != "tui-design":
        raise SystemExit(f"invalid eval-set skill name: {path.relative_to(root)}")
    if isinstance(data.get("queries"), list):
        query_ids = [case.get("id") for case in data["queries"]]
        if len(query_ids) != len(set(query_ids)):
            raise SystemExit(f"trigger eval ids must be unique: {path.relative_to(root)}")
        for case in data["queries"]:
            if not isinstance(case.get("query"), str) or not isinstance(case.get("should_trigger"), bool):
                raise SystemExit(f"invalid trigger eval: {path.relative_to(root)} id={case.get('id')!r}")
        continue
    if not isinstance(data.get("evals"), list):
        raise SystemExit(f"invalid eval-set envelope: {path.relative_to(root)}")
    ids = []
    names = []
    for case in data["evals"]:
        ids.append(case.get("id"))
        names.append(case.get("name"))
        if not isinstance(case.get("prompt"), str) or not case["prompt"].strip():
            raise SystemExit(f"eval has no prompt: {path.relative_to(root)} id={case.get('id')!r}")
        assertions = case.get("assertions")
        if not isinstance(assertions, list) or not assertions or not all(isinstance(item, str) and item.strip() for item in assertions):
            raise SystemExit(f"eval has invalid assertions: {path.relative_to(root)} id={case.get('id')!r}")
    if len(ids) != len(set(ids)) or len(names) != len(set(names)):
        raise SystemExit(f"eval ids/names must be unique: {path.relative_to(root)}")

if any(path.name == ".DS_Store" for path in skill_dir.rglob(".DS_Store")):
    raise SystemExit("skill source contains .DS_Store cruft")

print(f"Validated skill metadata and content for {version}")
PY

python3 -m unittest discover -s "$repo_root/tests" -v

build_a="$(mktemp -d "${TMPDIR:-/tmp}/tui-design-validate-a.XXXXXX")"
build_b="$(mktemp -d "${TMPDIR:-/tmp}/tui-design-validate-b.XXXXXX")"
cleanup() {
  rm -rf "$build_a" "$build_b"
}
trap cleanup EXIT

"$repo_root/scripts/package-skill.sh" "$build_a" >/dev/null
"$repo_root/scripts/package-skill.sh" "$build_b" >/dev/null
cmp "$build_a/tui-design.skill" "$build_b/tui-design.skill"
unzip -tq "$build_a/tui-design.skill" >/dev/null

archive_entries="$(unzip -Z1 "$build_a/tui-design.skill")"
while IFS= read -r entry; do
  case "$entry" in
    tui-design/*) ;;
    *)
      echo "error: archive entry is outside tui-design/: $entry" >&2
      exit 1
      ;;
  esac
done <<< "$archive_entries"
python3 - "$build_a/tui-design.skill" <<'PY'
import sys
import zipfile
from pathlib import Path

archive = Path(sys.argv[1])
expected = [
    "tui-design/SKILL.md",
    "tui-design/agents/openai.yaml",
    "tui-design/references/cli-basics.md",
    "tui-design/references/ecosystem-go.md",
    "tui-design/references/ecosystem-python.md",
    "tui-design/references/ecosystem-rust.md",
    "tui-design/references/ecosystem-typescript.md",
    "tui-design/references/exemplar-apps.md",
    "tui-design/references/interaction-patterns.md",
    "tui-design/references/visual-patterns.md",
]
with zipfile.ZipFile(archive) as package:
    names = package.namelist()
    if names != expected:
        raise SystemExit(f"archive allowlist/order mismatch; expected={expected}, actual={names}")
    for info in package.infolist():
        if info.date_time != (1980, 1, 1, 0, 0, 0):
            raise SystemExit(f"archive timestamp is not normalized: {info.filename} {info.date_time}")
        if (info.external_attr >> 16) & 0o777 != 0o644:
            raise SystemExit(f"archive mode is not 0644: {info.filename}")
PY

echo "Validated deterministic package output"
