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

expected_files=(
  "SKILL.md"
  "agents/openai.yaml"
  "references/cli-basics.md"
  "references/ecosystem-go.md"
  "references/ecosystem-python.md"
  "references/ecosystem-rust.md"
  "references/ecosystem-typescript.md"
  "references/exemplar-apps.md"
  "references/interaction-patterns.md"
  "references/visual-patterns.md"
)

# The installable artifact has an exact allowlist. Reject symlinks, caches,
# generated files, and new resources until the release contract is updated.
while IFS= read -r -d '' source_entry; do
  relative="${source_entry#"$skill_dir"/}"
  case "$relative" in
    agents|references)
      [ -d "$source_entry" ] && [ ! -L "$source_entry" ] || {
        echo "error: expected a real directory in skill source: $relative" >&2
        exit 1
      }
      ;;
    SKILL.md|agents/openai.yaml|references/cli-basics.md|references/ecosystem-go.md|references/ecosystem-python.md|references/ecosystem-rust.md|references/ecosystem-typescript.md|references/exemplar-apps.md|references/interaction-patterns.md|references/visual-patterns.md)
      [ -f "$source_entry" ] && [ ! -L "$source_entry" ] || {
        echo "error: expected a regular, non-symlink skill file: $relative" >&2
        exit 1
      }
      ;;
    *)
      echo "error: unexpected entry in skill source: $relative" >&2
      exit 1
      ;;
  esac
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

mkdir -p "$stage_root/$skill_name/agents" "$stage_root/$skill_name/references"
for relative in "${expected_files[@]}"; do
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
