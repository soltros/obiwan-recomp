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
- `HandleFrontEndAction` at `0x00082B1D` dispatches title UI actions from an
  event object. It first requires the event's active bit, checks the event
  kind (`0x200`/`0x208` versus `0x201`/`0x209`), verifies the UI object's
  lifetime, and reads an action code from the nested event data. Its action
  cases load `newPlayer.swf`, `selectPlayer.swf`, `selectMission.swf`,
  `mainMenu.swf`, and `vsBattle_Player.swf`; separate cases commit the active
  profile or pass a parsed profile index to the profile-management routine.
  This confirms that menu transitions are driven through a native event
  dispatcher. The `selectMission.swf` case only opens the movie; the function
  contains no level or mission bundle load call, so it is not the gameplay
  launch path.
- The extracted `data/interface/flash/selectMission.swf` provides the next
  handoff. It is an uncompressed SWF v5 (`FWS`), 367,058 bytes, SHA-256
  `671b10f0b31c35586822f62d0a5cc384b44517447f2754c13c2fb9abc625f3e2`.
  Its ActionScript `DoAction` tag at file offset `0x5846A` (793-byte payload)
  builds the value `"NextLevel " + misCurrent` and stores it in the
  `loadMission` variable. The script then selects a fade command for certain
  mission indices and issues a `GetURL2` action with the fade sequence joined
  to `loadMission`. This establishes the movie's mission-launch command
  format, including that `misCurrent` is the value interpolated into the
  command. The XBE contains `NextLevel` and `NextLevelHelper` tokens, and their
  code references pass through a shared string-keyed object-table helper; the
  stored values and the function that executes `loadMission` remain to be
  resolved.
- The same command vocabulary appears in native post-mission code. The
  routine at `0x0008C4E0` waits on a timer, then submits
  `FadeDownAndWait 1 | UnlockedScreenOff | Pause .5 | NextLevelHelper` to the
  script engine. This is strong evidence that `NextLevelHelper` is a script
  command, although the routine's broader unlock-message work and its exact
  entry conditions are not yet fully named.
- `0x00157470` is the command-string runner. It creates a script context,
  splits the input at `|`, and sends each segment through
  `0x001573E0`. That parser extracts a command name and its remaining text,
  then calls `0x000E2FD0` to dispatch it. The dispatcher parses command
  arguments, resolves the command name through `0x000E14D0`, and invokes the
  resolved object's callback. This identifies the generic execution path from
  the Flash `GetURL2` bridge to command lookup, but not the `NextLevel`
  callback or its level-loading behavior.
- The mission-unlock portion of `RunFrontEndFlow` constructs keys including
  `SA_01`, `SA_02`, `SA_03`, and `L05_7`, then asks `0x0009C080` for an index
  before publishing unlock flags to Flash. `0x0009C080` scans indices 0 through
  26 and returns the first index for which `0x0009BF30` reports a match, or
  `-1` if none match. `0x0009BF30` initializes two string-like objects and
  compares their backing data through `0x00012030`. This establishes a
  bounded string-match lookup, but the underlying record table and the exact
  meaning of its 27 slots are not yet identified.
- `UpdateUnlockNotifications` at `0x0008C7F0` reads the title's
  `T:\HighestUnlockedLevelNumber` file (defaulting to zero when absent),
  compares that value with the in-memory progression value at
  `DAT_0049B960 + 0x132C`, and writes the newer value back when progression
  advanced. It then looks up mission IDs `L01_4a`, `L02_1a`, `L03_2a`,
  `L05_3a`, and `CUT_JC4` through `FindMissionIdIndex`. Matching the current
  progression index selects a localized unlock message such as
  `/MessageBodyUnlockedMission/`; certain cases also enqueue character or
  arena unlock messages. This function records progression notification
  state and schedules UI messages; it does not itself load a level.
- `ReadHighestUnlockedLevelNumber` at `0x00096170` reads one 32-bit value from
  `T:\HighestUnlockedLevelNumber`, returning `1` if the file is missing or a
  complete 32-bit read fails. This is a separate accessor from the notification
  code's direct read/write logic.
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

The gameplay launch target remains unresolved. The selected-mission SWF emits
`NextLevel <misCurrent>` through `loadMission`, while the XBE's
string-keyed object table contains `NextLevel` and `NextLevelHelper` tokens.
The generic script path now traces through `0x00157470` (command-string
runner), `0x001573E0` (segment parser), `0x000E2FD0` (argument parser and
dispatcher), and `0x000E14D0` (name lookup). The next pass should identify the
value associated with `NextLevel`, then trace its callback into bundle and
level initialization.
Separately, the exact Flash callback that supplies
`playerName` to `CommitActivePlayerProfile` remains unresolved, as do the
variable profile-field encoding and the 27-entry mission lookup table. The
reported later crash still has no accompanying bundle or crash log, so its
cause remains unknown.
