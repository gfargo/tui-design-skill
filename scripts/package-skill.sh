#!/usr/bin/env bash
# Package the tui-design skill into an installable `.skill` file (a zip whose
# root is the skill directory: tui-design/SKILL.md + tui-design/references/*).
# Output: dist/tui-design.skill
#
# Usage: ./scripts/package-skill.sh [output-dir]   (default: dist)
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
skill_dir="$repo_root/plugins/tui-design/skills/tui-design"
skill_name="tui-design"
out_dir="${1:-$repo_root/dist}"
out_file="$out_dir/$skill_name.skill"

[ -f "$skill_dir/SKILL.md" ] || { echo "error: SKILL.md not found at $skill_dir" >&2; exit 1; }

mkdir -p "$out_dir"
rm -f "$out_file"

# Zip with the skill folder as the archive root, deterministically, excluding cruft.
( cd "$(dirname "$skill_dir")" \
  && zip -r -X -q "$out_file" "$skill_name" \
       -x '*/.DS_Store' '*/.*' )

echo "Built $out_file"
unzip -l "$out_file"
