# Native runtime build verification

Verified the local build after the user ran the pinned Nix environment.

- Framework HEAD: `f0f8a461496a4f23d9b0aeaa284b8d70ba7ab82b`; checkout clean.
- Build configuration: Debug, GCC 16.2.0, Ninja.
- All runtime static libraries exist, including kernel, graphics, audio/APU, NV2A, input, USB, video and platform support.
- Ninja dry run reports `no work to do`; the final kernel archive link is present in `.ninja_log`.
- This verifies compilation/archive creation, not game linking or execution.

## Warning triage

Do not suppress all warnings. In addition to unused symbols and comment warnings, the log contains format/ABI mismatches and potentially substantive issues:

1. `nv2a_pgraph_d3d11.c` locally redefines texture CONTROL0 as `0x1B08`, while the shared register header specifies `0x1B0C`. Determine reachability and intended register semantics before using this translator.
2. `nv2a_pb_replay.c` indexes a placeholder one-element menu array at offset 7455. The code is behind replay/menu gates, but must not be treated as a valid replay fixture for these games.
3. Kernel bridge `XBOX_TO_NATIVE` calls produce nonnull warnings. Trace the pointer conversion and runtime initialization before classifying these as benign or defective.

No upstream warning fixes have been applied. Next: inspect Linux host initialization, stage a copy of Obi-Wan's executable, and run the analysis/code-generation pipeline with per-title outputs.
