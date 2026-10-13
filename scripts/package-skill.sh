#!/usr/bin/env bash
# Package the tui-design skill into an installable `.skill` file (a zip whose
# root is the complete skill directory: SKILL.md, agents metadata, and references.
# Output: dist/tui-design.skill
#
# Usage: ./scripts/package-skill.sh [output-dir]   (default: dist)
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
skill_dir="$repo_root/plugins/tui-design/skills/tui-design"
skill_name="tui-design"
out_dir="${1:-$repo_root/dist}"


files_list="$repo_root/scripts/skill-files.txt"
[ -f "$files_list" ] || { echo "error: file allowlist not found at $files_list" >&2; exit 1; }

# One allowlist, shared with validate-release.sh and tests/test_packaging.py.
# A while-read loop keeps this working on macOS's bash 3.2 (no mapfile).
expected_files=()
while IFS= read -r line || [ -n "$line" ]; do
  case "$line" in
    ''|'#'*) continue ;;
  esac
  expected_files+=("$line")
done < "$files_list"
[ "${#expected_files[@]}" -gt 0 ] || { echo "error: $files_list lists no files" >&2; exit 1; }

is_expected_file() {
  local candidate
  for candidate in "${expected_files[@]}"; do
    [ "$candidate" = "$1" ] && return 0
  done
  return 1
}

is_expected_dir() {
  local candidate
  for candidate in "${expected_files[@]}"; do
    case "$candidate" in
      "$1"/*) return 0 ;;
    esac
  done
  return 1
}

# The installable artifact has an exact allowlist. Reject symlinks, caches,
# generated files, and new resources until the release contract is updated.
while IFS= read -r -d '' source_entry; do
  relative="${source_entry#"$skill_dir"/}"
  if is_expected_dir "$relative"; then
    if [ ! -d "$source_entry" ] || [ -L "$source_entry" ]; then
      echo "error: expected a real directory in skill source: $relative" >&2
      exit 1
    fi
  elif is_expected_file "$relative"; then
    if [ ! -f "$source_entry" ] || [ -L "$source_entry" ]; then
      echo "error: expected a regular, non-symlink skill file: $relative" >&2
      exit 1
    fi
  else
    echo "error: unexpected entry in skill source: $relative" >&2
    exit 1
  fi
done < <(find "$skill_dir" -mindepth 1 -print0)

# Resolve out_dir to an absolute path *before* the cd below, so a relative
# argument (e.g. "dist") still works once the working directory changes.
mkdir -p "$out_dir"
out_dir="$(cd "$out_dir" && pwd)"
out_file="$out_dir/$skill_name.skill"
rm -f "$out_file"

# Stage normalized content so file order, timestamps, and permissions do not
# make two builds from the same source produce different archives.
stage_root="$(mktemp -d "${TMPDIR:-/tmp}/tui-design-package.XXXXXX")"
cleanup() {
  rm -rf "$stage_root"
}
trap cleanup EXIT

for relative in "${expected_files[@]}"; do
  [ -f "$skill_dir/$relative" ] || { echo "error: listed skill file is missing: $relative" >&2; exit 1; }
  mkdir -p "$(dirname "$stage_root/$skill_name/$relative")"
  cp "$skill_dir/$relative" "$stage_root/$skill_name/$relative"
done
find "$stage_root/$skill_name" -type d -exec chmod 755 {} +
find "$stage_root/$skill_name" -type f -exec chmod 644 {} +
find "$stage_root/$skill_name" -exec touch -t 198001010000.00 {} +

( cd "$stage_root" \
  && LC_ALL=C find "$skill_name" -type f ! -path '*/.*' -print \
     | LC_ALL=C sort \
     | zip -0 -X -q "$out_file" -@ )

echo "Built $out_file"
unzip -l "$out_file"
