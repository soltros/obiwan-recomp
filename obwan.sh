#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
mkdir -p build/game build/save
export RECOMP_FB_WINDOW=${RECOMP_FB_WINDOW:-1}
export RECOMP_TITLE_KEVENTS=${RECOMP_TITLE_KEVENTS:-1}
export RECOMP_VBLANK=${RECOMP_VBLANK:-paced}
export RECOMP_PB_EXEC=${RECOMP_PB_EXEC:-1}
export RECOMP_USB=${RECOMP_USB:-1}
export RECOMP_WATCHDOG_SECS=${RECOMP_WATCHDOG_SECS:-28}
exec build/obiwan_recomp build/game build/save "$@"
