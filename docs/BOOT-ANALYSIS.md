# Obi-Wan boot and first-run flow

This note records the current static and runtime evidence for the North
American Obi-Wan XBE (`default.xbe`). Addresses are Xbox virtual addresses
from the user's Ghidra project, `XBE_OBIWAN`.

## Verified path

- `RunTitleMainLoop` at `0x00025730` is the title's main dispatcher. It
  initializes XAPI gamepad devices, configures the file-system cache, obtains
  launch information, initializes three core subsystems (`0x00210BE0`,
  `0x00228C70`, and `0x00206850`), then chooses a launch path. The launch-info
  branch can set demo/multiplayer state and run a demo without entering the
  ordinary front end. The normal path calls `LoadOptionalStartupBundle` and
  `0x0002AEFC` when the startup flag is set, then invokes `StartFrontEnd`.
  After the selected path, it stays in the title loop while the title-active
  predicate remains true, pumping the title scheduler and servicing a pending
  device action. When the loop ends, the startup thread's caller falls back to
  the dashboard.
- `LoadOptionalStartupBundle` at `0x0020BB80` returns immediately when global
  `0x004F1C00` is zero. Otherwise it passes `d:\startup.bndl` to the bundle
  loader at `0x002C3E50` and returns that loader's result. The bundle is
  conditional title data, not the XBE's executable image.
- `StartFrontEnd` at `0x000A32E0` conditionally calls `0x0009E3C0(1, arg)`
  when global `0x004F150C` is zero, always calls `0x000A0A20(0xB)`, and then
  enters `RunFrontEndFlow` (`0x000B7830`). The helper names remain unresolved;
  the call order and condition are directly visible in Ghidra.
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
- Profile initialization is in `InitializePlayerProfiles` (`0x000B3080`). It clears the in-memory
  profile slots, attempts to read `Z:\CurPlayerName`, and enumerates saved
  profile records. `CommitActivePlayerProfile` (`0x000B33B0`) writes
  `Z:\CurPlayerName` when a profile is committed.
- `RunFrontEndFlow` (`0x000B7830`) initializes the Flash working directory and
  loads `start.swf`. On successful load it waits for the title's completion
  signal before proceeding to `mainMenu.swf`. A zero result from the main-menu
  movie provides `freeSlots` and `firstTime`; a nonzero result opens
  `newPlayer.swf`. If the new-player movie succeeds, the title checks generated
  `JEDI <number>` names against existing profiles and publishes the chosen
  name. Otherwise, it opens `selectPlayer.swf`; a successful selection then
  advances to `selectMission.swf`.
- The mission-unlock portion of `RunFrontEndFlow` constructs keys including
  `SA_01`, `SA_02`, `SA_03`, and `L05_7`, then asks `0x0009C080` for an index
  before publishing unlock flags to Flash. `0x0009C080` scans indices 0 through
  26 and returns the first index for which `0x0009BF30` reports a match, or
  `-1` if none match. `0x0009BF30` initializes two string-like objects and
  compares their backing data through `0x00012030`. This establishes a
  bounded string-match lookup, but the underlying record table and the exact
  meaning of its 27 slots are not yet identified.
- After `newPlayer.swf` returns success, the game checks up to seven generated
  `JEDI <number>` names against existing profiles and calls
  `PublishPlayerNameToFlash` (`0x000B70A0`) to set `playerName` and
  `playerNameLength`. `PopulateFlashPlayerList` (`0x000B73C0`) separately sends
  each active profile's `Name`, `Level`, and `Valid` fields to the player
  selection UI. The latter is not the profile creation commit itself.
- `LoadProfileSavegame` (`0x000B1D90`) opens the profile's `Savegame` record and
  validates its format before treating the slot as valid. The first 32-bit
  version field must equal `0x0F`; the parser hashes the serialized fields
  with the Xbox signature API and checks the trailing 20-byte signature. The
  record includes a fixed header and may include variable-length data when its
  flag at record offset `0xCC` is set. Missing, truncated, version-mismatched,
  or signature-mismatched files are rejected. Creating a `CurPlayerName` file
  alone would not create a valid profile.
- `WriteProfileSavegame` (`0x000B1490`) is the paired save path. Its Ghidra
  call site passes mode `"w"` to the file API; it serializes the profile/save
  state, computes an Xbox signature, and writes the resulting 20-byte digest
  after the payload. The decompiler labels the ambiguous stdio calls as
  `fread` because the XBE import signature is shared; the file mode and caller
  behavior establish that this routine writes. `CommitActivePlayerProfile`
  invokes it for both the selected profile record and the current-save record.

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

The remaining front-end target is the Flash callback that supplies
`playerName` to `CommitActivePlayerProfile`. Direct xrefs show the commit
routine is reached from profile management and game-flow dispatch, but the
exact callback that consumes the Flash property is still unresolved. The
structure and encoding of the variable profile fields also need to be
documented before attempting to seed save data. The next title-flow pass should
identify the 27-entry mission lookup table and trace the successful
`selectMission.swf` result into the level loader. The reported later crash still
has no accompanying bundle or crash log, so its cause remains unknown.
