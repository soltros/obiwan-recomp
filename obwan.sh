#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
GAME_DIR=${1:-"$(dirname "$PWD")/Star Wars - Obi-Wan (USA)"}
SAVE_DIR=${2:-build/save}
if [ ! -f "$GAME_DIR/default.xbe" ]; then
    echo "Missing $GAME_DIR/default.xbe; pass the extracted game directory as argument 1." >&2
    exit 1
fi
mkdir -p "$SAVE_DIR"
export RECOMP_FB_WINDOW=${RECOMP_FB_WINDOW:-1}
export RECOMP_TITLE_KEVENTS=${RECOMP_TITLE_KEVENTS:-1}
export RECOMP_VBLANK=${RECOMP_VBLANK:-paced}
export RECOMP_PB_EXEC=${RECOMP_PB_EXEC:-1}
export RECOMP_USB=${RECOMP_USB:-1}
export RECOMP_WATCHDOG_SECS=${RECOMP_WATCHDOG_SECS:-28}
exec build/obiwan_recomp "$GAME_DIR" "$SAVE_DIR"
