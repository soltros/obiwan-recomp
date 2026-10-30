#!/usr/bin/env sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
GAME_DIR=${1:-"$ROOT/../Star Wars - Obi-Wan (USA)"}
GAME_DIR=$(CDPATH= cd -- "$GAME_DIR" && pwd)
RUNTIME=${XBOX_LINUX_DIR:-"$ROOT/../xbox-linux"}

command -v nix >/dev/null 2>&1 || { echo "Install Nix with flakes enabled, then rerun ./install.sh." >&2; exit 1; }
if [ ! -d "$RUNTIME/.git" ]; then
    if [ -e "$RUNTIME" ]; then echo "Runtime path exists but is not an Xbox Linux git checkout: $RUNTIME" >&2; exit 1; fi
    git clone https://github.com/soltros/xbox-linux.git "$RUNTIME"
fi

python3 - "$ROOT/target.json" "$GAME_DIR/default.xbe" <<'PY'
import hashlib,json,sys
target=json.load(open(sys.argv[1]))
actual=hashlib.sha256(open(sys.argv[2],'rb').read()).hexdigest()
if actual != target['sha256']:
    raise SystemExit(f"XBE hash mismatch: expected {target['sha256']}, got {actual}")
print(f"Verified {sys.argv[2]} ({actual})")
PY

"$RUNTIME/tools/install_runtime.sh"
export XBOXRECOMP_DIR="$RUNTIME/third_party/xboxrecomp"
cd "$ROOT"
nix develop --command python3 -m unittest discover -s tests -v
nix develop --command python3 tools/workspace.py verify --game-dir "$GAME_DIR"
nix develop --command python3 tools/generate_obiwan.py --game-dir "$GAME_DIR"
nix develop --command python3 tools/build_obiwan.py --jobs "${JOBS:-4}"

printf '\nObi-Wan recomp build is ready. Launch with:\n  %s/obwan.sh "%s"\n' "$ROOT" "$GAME_DIR"
