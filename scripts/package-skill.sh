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

[ -f "$skill_dir/SKILL.md" ] || { echo "error: SKILL.md not found at $skill_dir" >&2; exit 1; }
[ -f "$skill_dir/agents/openai.yaml" ] || { echo "error: agents/openai.yaml not found at $skill_dir" >&2; exit 1; }
[ -d "$skill_dir/references" ] || { echo "error: references not found at $skill_dir/references" >&2; exit 1; }

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

cp -R "$skill_dir" "$stage_root/$skill_name"
find "$stage_root/$skill_name" -name '.DS_Store' -delete
find "$stage_root/$skill_name" -type d -exec chmod 755 {} +
find "$stage_root/$skill_name" -type f -exec chmod 644 {} +
find "$stage_root/$skill_name" -exec touch -t 198001010000.00 {} +

( cd "$stage_root" \
  && LC_ALL=C find "$skill_name" -type f ! -path '*/.*' -print \
     | LC_ALL=C sort \
     | zip -0 -X -q "$out_file" -@ )

echo "Built $out_file"
unzip -l "$out_file"
