#!/usr/bin/env bash
# Render the reference code samples marked check=<harness>/<name> into their
# harnesses under tests/samples/ and build and test them against pinned versions.
#
# Usage: ./scripts/check-samples.sh [go] [rust] [python] [typescript]   (default: all)
#
# Toolchains: go (version from tests/samples/go/go.mod); cargo; a Python with
# tests/samples/python/requirements.txt installed (override with PYTHON=...);
# node and npm. Output goes to tests/samples/.build/ (override with SAMPLES_OUT).
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
out="${SAMPLES_OUT:-$repo_root/tests/samples/.build}"
python="${PYTHON:-python3}"

if [ "$#" -eq 0 ]; then
  set -- go rust python typescript
fi

require() {
  command -v "$1" >/dev/null || {
    echo "error: the $2 sample checks need $1 on PATH" >&2
    exit 1
  }
}

python3 "$repo_root/scripts/check-samples.py" render --out "$out" "$@"

for harness in "$@"; do
  echo "==> $harness samples"
  case "$harness" in
    go)
      require go go
      (cd "$out/go" && go vet ./... && go test ./...)
      ;;
    rust)
      require cargo rust
      export CARGO_TARGET_DIR="$out/.cargo-target"
      (cd "$out/rust" && cargo check --locked --all-targets && cargo test --locked --test '*')
      ;;
    python)
      require "$python" python
      (cd "$out/python" && "$python" -m compileall -q . && "$python" -m pytest -q)
      ;;
    typescript)
      require npm typescript
      (cd "$out/typescript" &&
        npm ci --ignore-scripts --no-audit --no-fund &&
        npx --no-install tsc --noEmit &&
        npx --no-install vitest run)
      ;;
  esac
done
