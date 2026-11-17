# Sprint 02: SELECT screen to L01_1 gameplay

Assessment date: 2026-11-16. Every claim below is tied to a bounded,
scripted diagnostic run on the staged extraction. Game files and generated
title C stay local and ignored, as before.

## Verified path into gameplay

Starting from the SELECT screen that Sprint 01 ended on, scripted runs now
cover the whole front-end and the first level:

1. `mainMenu.swf` (SELECT) accepts input and opens `newPlayer.swf`.
2. On the ENTER NAME keyboard, B returns to `mainMenu.swf`. Navigation is
   index arithmetic starting at `keyCurrent = 25` (decoded from the SWF
   bytecode in `newPlayer.swf`): Right x3, Down x2 lands on key 43,
   `FINISHED`.
3. Confirming with A commits a profile: the title writes `Z:\CurPlayerName`
   and `U:\<id>\Savegame`/`SaveMeta.xbx` (default name `JEDI 1` when the
   name is empty), loads the loading placards, and asks for a quick reboot
   with a launch page naming `default.xbe` and level token `01_1`.
4. With that launch page installed on the next boot (runtime support
   below), the title skips the menus, loads the L01_1 snapshot set, level
   geometry, actors, AI, node map, light BSP, HUD, and `l01_1.script`,
   plays the briefing/crawl sequence, and reaches third-person gameplay:
   Obi-Wan in the Coruscant street with the saber-meter HUD, an NPC ahead,
   changing camera/player positions across frame dumps, and a working
   Start pause menu. Runs last until the deliberate watchdog cutoff (100 s,
   645 flips at ~3.5 fps in the software renderer).

## Why input froze at newPlayer

Sprint 01 localized input to "state copying works"; it stopped working the
moment `newPlayer.swf` loaded, and every guest-side suspect measured clean:

- `Xbe_XInputGetState` returns success on all 518 probed calls, before and
  after the transition (and `handle+0xA3 == 1` is its error case, not its
  ready flag).
- The HID callback and copy functions keep being entered after the
  transition; no close/reopen happens. The copy length gate
  (`handle+0x66`) stays valid and the packet counter keeps rising.

The break was in the runtime's OHCI DMA handling: `bus_resolve` sent every
guest address below the contiguous allocator's high-water mark to the
window. When allocations passed the XID report buffer at `0x0108174A`
(the contiguous print at the transition reads 17068 KB against the buffer
at 16899 KB), report bytes went to the window while the guest CPU kept
reading RAM. The fix resolves with the allocator's own page maps first,
mirroring the APU resolver; it is carried in the runtime patch below.

## Seeded discovery and script dispatch

Level loading reaches code the initial discovery never split out. The
fixes are measured, not speculative:

- Methods reached only through adjustor thunks, pad-bounded xref targets,
  16-aligned vtable-identified starts, and four bodies that were
  previously fail-fast stubs are translated by
  `tools/make_obiwan_seed_stubs.py` in one translator load, seeded from
  `tools/seed_functions.json` (also fed to the disasm stage). A census
  found only 15 strict `sub ecx,[ecx-4]; jmp` adjustor thunks game-wide;
  the 3,166 func-id "vtable_thunk" entries are mostly inference noise and
  are not used as seeds.
- The script-command routine rooted at `sub_0015E940` is entered at ~400
  interior addresses from its command table. One clone cannot be
  regenerated per entry, and the translator's `--entry-stubs` cannot reach
  these (direct referenced calls only; `entry_stub()` returns None under
  this routine's recovered CFG, and its symbols get no dispatch-table
  entries). Instead, one dispatch clone labels 388 of the identified
  interior entries — 233 already labelled in the parent body, the rest at
  dead blocks following exit jumps — and selects among them by guest VA
  through `obiwan_mega_lookup` in manual dispatch. Two further entries
  (`0x0016E96C`, `0x0016F71F`) use the existing per-entry adapter tool.
- All stand-ins carry headers saying to delete them on full regeneration;
  the seeds, not the generated files, are the durable input.

## Runtime dependency

This title work needs the companion runtime changes in xbox-linux
(`patches/xboxrecomp-obiwan-input-launch.patch`, applied third by
`tools/toolchain.py`): the OHCI resolution fix above,
`RECOMP_LAUNCH_FILE` launch-page capture/install for quick-reboot
hand-off (without it the title simply exits after profile commit), and
two env-gated diagnostics used above (`RECOMP_USB_TD_PROBE`,
`RECOMP_GPU_METHODS`). Applying all three patches to a pristine pinned
checkout reproduces the live runtime tree byte-identically for the
changed files.

## Text rendering and NV097 (correlated, not fixed)

Menus, the briefing, and the crawl render with text at roughly 20x scale
(clipped glyph strips) while 3D rendering is coherent. Menu draw ranges
span x -6390..12938, y -4800..9698 against a 640x480 clip — almost
exactly the surface scaled by the Flash twip factor — which localizes
the defect to the UI/text transform path rather than the font data (the
24 LAF containers validate; glyph textures are bound). In-level runs
report 184 distinct unhandled NV097 methods; the census
(`RECOMP_GPU_METHODS=1`) is dominated by `0x0314`, `0x03B8`, `0x0294`,
`0x17C4` and groups `0x03C0-0x03C8`, `0x0420-0x042C`,
`0x0394/0x0398`, `0x06C0-0x06D8`. Identifying which of these control the
UI viewport transform is the next task; no renderer behavior was changed
on correlation alone.

## Not verified

- Play beyond the opening minutes, combat, checkpoints, mission
  completion/transitions (`NextLevel` graph is mapped statically in
  `MISSION-FLOW.md` but not exercised).
- Audio correctness and performance (software rasterizer at ~1-3.5 fps).
- Whether the remaining unhandled methods produce other latent defects.
- A full regeneration cycle with the seeded discovery (stand-ins are
  verified in place; regeneration must re-check stub interaction for the
  four seeded former stubs).
