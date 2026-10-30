# Sprint 01: static baseline and first blockers

Assessment date: 2026-10-29. Runtime work below is based on bounded, instrumented runs of the staged Obi-Wan extraction; UC2 remains static-only.

## Completed and verified

- Fingerprinted every file: Obi-Wan **8,383 files / 2,210,953,742 bytes**; UC2 **1,607 / 2,267,519,104**. Re-read and verified both manifests. No file-path case collisions.
- Validated XBE raw/virtual section bounds and file-backed VA translation. Cross-checked entry points, section addresses/sizes and all kernel ordinals against xboxrecomp's standalone parser.
- Obi-Wan: **11 sections / 112 imports**, entry `0x0002B180`.
- UC2: **18 sections / 156 imports**, entry `0x0026867F`.
- Created bounded x86 entry disassembly and a source-string anchor index: **370 Obi-Wan anchors** with **3,052 raw address occurrences**; **6 UC2 anchors** with **4 occurrences** under the deliberately narrow source-path filter. These are not function counts.
- Wrote meaningful synthetic tests for malformed XBE bounds, zero-fill translation, package indices and outer cycles, bundle truncation and paths, and manifest drift/collisions/symlinks.

## Obi-Wan: concrete asset findings

`startup.bndl`, `snapshot/__L01_1_ss.bndl`, and `snapshot/__ui_ss.bndl` parse completely into **111**, **149**, and **29** entries. Every entry matches its loose resource hash.

`crawl.bndl` has **482 complete entries**, of which **481** match loose resources. One complete entry, `data/voice/bad/b500c41.wav`, differs from the loose file. This may be intentional: preserve both variants and trace resource precedence.

The following entry declares `data/sfx/music_flourish/m_battle_15_lp.wav`, **2,904,072 bytes**, at payload offset **149,657,978**. Only **1,369,734 bytes** remain in the bundle; those bytes match the prefix of the complete loose WAV. This is strong evidence of a truncated bundle record under the observed layout, but does not establish whether the shipped loader needs it or falls back to the loose file. Do not repair the original. Check against another verified extraction or runtime file-read traces before selecting a repair strategy.

Training's readable export declares **9 zones, 24 regions and 7 portals**. It references `Tr.CMM`; that name alone does not establish that runtime script source is missing. The actor/world exports and generated `reports/obiwan/training.json` provide a concrete scene to inspect next.

## UC2: package metadata recovered

**140 ordinary packages** parse with bounded names/imports/exports and object-reference validation: **59,295 name entries, 10,813 imports and 65,333 exports**. Counts sum records across files, not unique semantic objects. Their root package imports all match names among this parsed set; this is not full import-link validation.

`UCGameplay.u` exposes **232 class exports, 2,383 function exports and 80 state exports**. Its **249 TextBuffer exports** are all 19 bytes; inspected records contain a single-space text string. Their existence is not recovery of UnrealScript source. Object payloads and bytecode still need decoding.

**58 `.LIN` files** are deferred rather than misparsed as ordinary packages. For example, `XboxMaps/CTF-Aqueduct.LIN` is **3,153,067 bytes**, while its header advertises import/export offsets **3,278,950 / 3,279,958**. `System/Script.lin` has in-file offsets but fails ordinary import-name interpretation. Determine the actual linearized loading/transform procedure from executable loader code. Do not guess that all LIN files use one compression codec.

`System/Packages.md5` has Unreal magic and version **125/0**; it is binary metadata, not a text checksum listing. It is separately deferred. Supported ordinary packages use **151/0** or **151/1**; the parser intentionally rejects other versions.

## Native toolchain and first execution

Pinned xboxrecomp `f0f8a461496a4f23d9b0aeaa284b8d70ba7ab82b` (v0.16.0) was fetched and built with the host's Nix toolchain. Obi-Wan's XBE was copied into ignored build output before upstream analysis. The full pipeline generated **27,401 functions** into **279 C files / 151 MB**, and the launcher plus generated code link successfully.

The Linux framebuffer viewer is opt-in in the runtime. The `obwan.sh` test launcher now sets `RECOMP_FB_WINDOW=1`; without it, a normal run executes the guest headlessly and no window appears. SDL explicitly reports a visible window as `[FBWIN] framebuffer window open (...)`; if it reports `SDL video unavailable`, inspect the shell's display/session environment. The Codex execution environment has no video device, so the viewer can only be confirmed on the user's graphical desktop.

The launcher verifies the pinned XBE hash, initializes guest memory, kernel bridges, and dispatch, then enters `0x0002B180`. Both input-check and runtime-init smoke checks pass. A 20-second run from a staged extraction reached startup, spawned its first system thread, and loaded assets. The run was intentionally time-bounded and did not verify a menu or frame.

Two initial bring-up blockers have concrete fixes: `0x002CDFD8` is a short vtable getter missed by broad code discovery and now has a guest-register implementation in the manual dispatch; POSIX file opens now resolve existing path components case-insensitively so Xbox paths match extracted assets such as `AudioTableEntries.txt`/`audiotableentries.txt`.

With `RECOMP_PB_EXEC=1`, the existing software pushbuffer executor consumes an initial submission and reports a clear plus two rasterized triangles. The title's GPU-read pointer is `device 0x003770A0 + 0x3F0 -> 0x8001D000`; its write sequence reaches `9` while the pointed-to progress word stays at `3`. The pushbuffer scan confirms two `BACK_END_WRITE_SEMAPHORE_RELEASE` (`0x1D70`) commands. The launcher now registers that progress word with the executor, which writes release values `5` and `7` and clears the original ring-space wait. The USER DMA PUT/GET pair reaches `0x00052C88`.

The next wait is an embedded notification event at `0x00379590`. `RECOMP_TITLE_KEVENTS=1` translates its guest event header, and `RECOMP_VBLANK=paced` delivers the title's vector-3 ISR on each enabled PCRTC vblank. The ISR at `0x00371F10` checks bit 24 of PMC interrupt status (`base + 0x100`) against the corresponding enable (`base + 0x140`), queues its DPC, and the DPC signals the event. This unblocks startup and leads to more asset loading. A run without the event adapter passes a guest event address as a host handle and faults.

The game initially reached unresolved indirect entries inside a large overlapping routine: `0x0016C39F`, `0x0016B82A`, `0x0016C1C4`, `0x00170EED`, `0x0016B0F3`, and `0x0016BDB3`. `tools/make_obiwan_entry_stub.py` now clones the corresponding generated parent bodies, restores each omitted compare/branch sequence from the XBE bytes, and `manual.c` dispatches those entry adapters. The first two-entry D3D queue stall was caused by the title waiting for its completed counter (`0x003795B8`) to catch the submitted counter (`0x00379C00`). The software pushbuffer executor processes submissions synchronously, so the launcher now mirrors the submitted counter at device offset `0x2B60` to the completed counter at `0x2518`. With title events, paced vblank, pushbuffer execution and USB enabled, the game renders without unresolved-target stops.

The Linux host initially chose a guest-memory base near `0x7fff...`, making some guest aperture addresses non-canonical. The runtime now attempts a safe, fixed 4-GiB guest-memory base on Linux x86-64, falling back to its prior placement if occupied. A smoke run confirms guest RAM, contiguous-memory, NV2A, MCPX, and OHCI mappings succeed at that base.

Input is now traced through the full guest XID path. Successful OHCI periodic TDs (`ED 0x1610`, `TD 0x2E70`, completion code 0) copy 20-byte reports to `0x010816AA`. The HID DPC drains its completion list and the generic callback dispatcher invokes title callback `0x003B53DC`; that callback selects per-device handler `0x003B5503`. The handler copies the 18-byte input payload from context `0x01081678 + 0x34` into its stored state at `+0x14`. Dynamic traces show Start (`0x10`) and A (`0xFF` in the analog A byte) both appear in the input buffer and then in stored state on the following poll. The scripted `a` is correctly an analog pressure button on Xbox. Input transport and state-copy are therefore verified; remaining work is to determine why input does not advance the UI.

Timing affects the observed screens: Start at 6 seconds advances the splash sequence; A at 15 seconds loads `d:\data\interface\flash\mainMenu.swf`. A subsequent menu action reaches a “SELECT” screen, and scripted D-pad movement changes its highlighted row. Thus XID transport, input-state copying, menu navigation, and at least part of the menu transition are working. The captured SELECT frame has visible panels and a highlight, but most labels/content are absent or rendered incorrectly; the issue is now narrower than “input does not advance the UI.” The game remains active until the watchdog. The watchdog's 18 missing `d:\snapshot\__ui_ss.*` probes are file-not-found results, not a fault; no later failed read or shutdown is associated with them yet. `wbinvd` remains untranslated but has not stopped execution. Captures and logs are ignored under `build/obiwan/`.

Two more control-flow holes in generated routine `sub_0015E940` were exposed by menu actions: `0x0016A393` omitted `cmp [esp+0x33c4],1` / `jl 0x1754b1`, and `0x0016A59F` omitted `mov ebp,[esp+0x33c4]` / `cmp ebp,1` / `mov ecx,esi` / `jl 0x1754b3`. `tools/make_obiwan_entry_stub.py` now clones the parent routine, restores each block from the XBE bytes, and `manual.c` dispatches both entries. Regeneration and a repeated 32-second scripted input run now pass these paths without unresolved-target stops. The guest still runs until the deliberate watchdog cutoff; the watchdog dump is a liveness snapshot, not a host crash.

The hottest lock (`0x00F81610`) belongs to heap object `0x003BD7F0`: `sub_0002CCFC` rounds requests into 16-byte size classes and updates free lists; its callback path dispatches registered callbacks through `sub_002D45B4`. Thread tracing maps host thread `1004` to `guest-main`; worker thread `1007` runs callback `0x002C3E10`, opens `startup.bndl.MARK`, and exits normally.

The video/audio path is not validated. The initial run also attempted to open `d:\data\aud\AudioTableEntries.txt`, which case-folding now resolves. Game writes were directed to a separate save root and runs used a staged copy, leaving original extractions untouched.

## Screenshot and font-container follow-up

The user-provided captures show the title animation and menu panels rendering, but menu labels can become oversized, clipped, or blocky. The panel geometry and character animation remain visible in the same captures, so the immediate fault is localized to text/UI rendering; the screenshots alone do not distinguish bad font metrics, SWF text transforms, texture sampling, or blend state.

Added `python3 tools/workspace.py fonts --game-dir "/path/to/Star Wars - Obi-Wan (USA)"` to validate the observed LAF font container boundaries and produce `reports/obiwan/fonts.json`. All **24** extracted `.laf` files pass: each declares 256 slots, its exact metadata/payload extent, ordered in-range bitmap offsets, and a stable payload hash. The report leaves per-glyph record fields and bitmap encoding opaque. This rules out basic container truncation/offset corruption for those files, but does not prove their rendering is correct. Next, capture a short focused runtime trace around a text draw and correlate loaded LAF font, font atlas upload/bind, text quad coordinates, texture sampling, and blend state before changing renderer behavior.

## Next implementation tasks

1. Determine the SELECT-screen action sequence needed to enter gameplay, using released pulses and framebuffer captures. The current five-step run reaches the screen without unresolved targets but does not load another SWF or exit before watchdog.
2. Correlate the blank/misrendered menu content with SWF, texture, font, and script reads. The current log proves `mainMenu.swf`, `trademarkerLight_12.laf`, and `trademarkerLight_14.laf` open and read to EOF; compare their decoded glyph atlas and draw calls before implementing broad renderer changes.
3. Inspect the 181 unhandled NV097 method IDs by frequency and implement those demonstrated to affect the menu; preserve validation of pushbuffer completion-counter mirroring.
4. Identify the guest loop behind repeated indirect targets `0xFE000144` and `0xFE000064`; establish whether it is normal render/event work or a device/audio wait.
5. Map the worker callback at `0x002C3E10` and create-thread wrapper `0x0002E59C`; confirm guest scheduling, TLS, event waits, and shutdown under repeat runs.
6. Validate case-insensitive lookup for directory enumeration, rename, and creation flows as well as the current existing-file open path. Trace `crawl.bndl` resource precedence and behavior at its truncated final record.
7. For UC2, locate the `.LIN` loader and package-to-native registration. Follow metadata names into bytecode/native boundaries; defer broad renderer or VM replacement.

The two runtime bring-up edits are preserved in `patches/xboxrecomp-linux.patch`. `tools/toolchain.py fetch` applies it automatically at the exact pinned revision, and `tools/toolchain.py patch` checks/applies it idempotently for an existing checkout.
The overlapping entry adapter is regenerated after the full codegen pass by `tools/make_obiwan_entry_stub.py` and added to manual indirect dispatch.

## Reproducible evidence

- `manifests/*.json`: complete per-file hashes.
- `reports/<title>/xbe.json`, `section-map.json`, `entry-disassembly.txt`, `string-anchors.json`.
- `reports/obiwan/bundles.json`, `training.json`.
- `reports/toolchain-preflight.json`: actual PATH/dependency checks.

## Technical references

- [Pinned xboxrecomp parser](https://github.com/sp00nznet/xboxrecomp/blob/f0f8a461496a4f23d9b0aeaa284b8d70ba7ab82b/tools/xbe_parser/xbe_parser.py), retained with its license and provenance.
- [Pinned game template](https://github.com/sp00nznet/xboxrecomp/blob/f0f8a461496a4f23d9b0aeaa284b8d70ba7ab82b/templates/new-game/CMakeLists.txt) and [host main](https://github.com/sp00nznet/xboxrecomp/blob/f0f8a461496a4f23d9b0aeaa284b8d70ba7ab82b/templates/new-game/src/main.c).
- [UE Viewer package imports](https://github.com/gildor2/UEViewer/blob/master/Unreal/UnrealPackage/UnPackage.cpp) and [UE2X exports](https://github.com/gildor2/UEViewer/blob/master/Unreal/UnrealPackage/UnPackage2.cpp), consulted 2026-10-29. The local reader is independently written Python based on the documented field layout and verified file bounds.
