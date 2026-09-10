#!/usr/bin/env bash
# Revalidate every committed evidence bundle under evals/results/ from any
# checkout location. Each bundle is checked against a clean snapshot of the
# git commit recorded in its run.json, so the current tree's skill and eval
# files are never substituted for the originals (see evals/README.md).
# Usage: ./scripts/validate-evidence.sh
# Requires the full git history: run `git fetch --unshallow` on a shallow clone.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
harness="$repo_root/scripts/eval_harness.py"

# Every with-skill bundle recorded before schema v5 embedded this absolute
# skill path in its prompts without recording it in run.json. Schema-v5
# bundles record skill_invocation_path and need no override.
legacy_skill_path="/Users/gfargo/dev/gfargo/tui-design-skill/plugins/tui-design/skills/tui-design"

snapshots="$(mktemp -d "${TMPDIR:-/tmp}/tui-design-evidence.XXXXXX")"
cleanup() {
  rm -rf "$snapshots"
}
trap cleanup EXIT

count=0
while IFS= read -r manifest; do
  bundle="$(dirname "$manifest")"
  read -r commit condition schema_version < <(python3 - "$manifest" <<'PY'
import json
import sys

manifest = json.load(open(sys.argv[1]))
commit = (manifest.get("git") or {}).get("commit")
if not commit:
    raise SystemExit(f"{sys.argv[1]} records no git commit")
print(commit, manifest["condition"], manifest["schema_version"])
PY
)
  snapshot="$snapshots/$commit"
  if [ ! -d "$snapshot" ]; then
    mkdir -p "$snapshot"
    git -C "$repo_root" archive "$commit" | tar -x -C "$snapshot"
  fi
  args=(--source-root "$snapshot")
  if [ "$condition" = "with-skill" ] && [ "$schema_version" -lt 5 ]; then
    args+=(--recorded-skill-path "$legacy_skill_path")
  fi
  python3 "$harness" validate \
    --run "$manifest" \
    --grades "$bundle/grades.json" \
    --summary "$bundle/summary.json" \
    --require-completed \
    "${args[@]}"
  count=$((count + 1))
done < <(find "$repo_root/evals/results" -mindepth 2 -name run.json | sort)

if [ "$count" -eq 0 ]; then
  echo "error: no evidence bundles found under evals/results" >&2
  exit 1
fi
echo "Validated $count evidence bundles from $repo_root"
