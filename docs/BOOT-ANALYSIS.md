# Obi-Wan boot and first-run flow

This note records the current static and runtime evidence for the North
American Obi-Wan XBE (`default.xbe`). Addresses are Xbox virtual addresses
from the user's Ghidra project, `XBE_OBIWAN`.

## Verified path

- The XBE entry at `0x0002B180` initializes the TLS index and starts the game
  thread with routine `0x0002B111`. If thread creation fails, it calls
  `XapiBootToDash`; otherwise startup continues in the game thread.
- `mainXapiStartup` at `0x0002B111` initializes the XAPI process and C runtime,
  then calls the title's main routine at `0x00025730`. Returning from that
  routine falls through to `XapiBootToDash`, so reaching the dashboard is a
  fallback after title termination rather than a startup step.
- The XAPI `CreateThread` wrapper at `0x0002E634` passes the title routine
  `0x0002B111` to `PsCreateSystemThreadEx`, along with the XAPI thread
  trampoline at `0x0002E59C`. The trampoline initializes TLS, invokes the
  passed title routine, and terminates the thread when it returns.
- Profile initialization is in `FUN_000B3080`. It clears the in-memory
  profile slots, attempts to read `Z:\CurPlayerName`, and enumerates saved
  profile records. `FUN_000B33B0` writes `Z:\CurPlayerName` when a profile is
  committed.
- Menu dispatch is in `FUN_000B7830`. It loads `mainMenu.swf`; when that menu
  returns the new-player choice, it loads `newPlayer.swf`.

## Runtime evidence

Diagnostic bundle `20261030T041645Z` confirms SDL initialized and opened the
host's Xbox controller (`045E:028E`). The title's USB report path returned
success. The timed Start press was followed by the main menu, and the timed A
press at about nine seconds caused `newPlayer.swf` to load. The capture shows
the new-player keyboard screen. A later sample includes D-pad-right (`0x0008`)
from the host controller.

The missing `Z:\CurPlayerName` read is expected for an empty save on first
launch. No `CurPlayerName` file was present in the diagnostic save directory
when inspected, so the first-run flow had not yet committed a player. The
reported later crash has no accompanying bundle or crash log in the shared
diagnostics directory, so its cause is still unknown.

## Next reverse-engineering target

Trace the `newPlayer.swf` callback/message names handled by `FUN_000B7830`,
then follow the selected-name commit path through `FUN_000B33B0` and the file
API. This will distinguish a title-side wait in the profile UI from a runtime
failure during profile creation. Do not seed `CurPlayerName` until its on-disk
format and related profile data are understood.
