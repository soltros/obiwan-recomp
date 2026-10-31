# Obi-Wan mission transition map

This map is extracted from the plaintext mission scripts in the game data (`data/scripts/*.script`); the `old/` directory is excluded. It records command sites, not runtime-verified outcomes. The XBE registers native script-command stubs for `NextLevel` (`0x00346160`), `NextLevelHelper` (`0x003461C0`), and `SelectMission` (`0x00348F80`). The selected-mission Flash movie independently emits `NextLevel <misCurrent>`.

The scripts show `NextLevel` used to move between named mission/cutscene resources. A comment in `cut_jc4.script` says the command deletes the current script, which explains why that script places cleanup before the transition. `NextPart` links lettered parts within a mission sequence. These observations establish expected transition names and graph edges, but do not reveal how the native callback locates or loads level bundles.

## NextLevel

| Script | Target token | Line |
|---|---|---:|
| `L01_1` | `CUT_JC1` | 842 |
| `L01_4b` | `L01_8` | 308 |
| `L01_8` | `CUT_JC2` | 893 |
| `L02_1b` | `L02_3` | 441 |
| `L02_3` | `L02_4` | 695 |
| `L02_4` | `cut_jc3` | 824 |
| `L03_2B` | `L03_4` | 1125 |
| `L03_4` | `L03_6a` | 1139 |
| `L03_6b` | `L03_7a` | 207 |
| `L03_7b` | `L03_8a` | 940 |
| `L03_8c` | `L04_3a` | 115 |
| `L04_3b` | `L04_7` | 253 |
| `L04_7` | `cut_jc4` | 288 |
| `L05_3C` | `L05_4a` | 310 |
| `L05_4b` | `L05_6` | 799 |
| `L05_5C` | `L05_6` | 223 |
| `L05_6` | `L05_7` | 856 |
| `L05_7` | `cut_hg` | 198 |
| `L05_7` | `cut_hg` | 241 |
| `L05_7` | `cut_hg` | 284 |
| `L05_7` | `cut_hg` | 327 |
| `L05_7` | `cut_hg` | 346 |
| `SA_01` | `l01_4a` | 159 |
| `SA_02` | `L02_1a` | 162 |
| `SA_03` | `L03_2a` | 149 |
| `SA_04` | `L05_3a` | 151 |
| `cut_jc1` | `sa_01` | 109 |
| `cut_jc2` | `sa_02` | 140 |
| `cut_jc3` | `sa_03` | 126 |
| `cut_jc4` | `sa_04` | 117 |
| `cut_jc5` | `sa_10` | 7 |
| `cut_sp` | `L05_3a` | 96 |
| `demo3` | `cut_hg` | 181 |
| `demo3` | `cut_hg` | 224 |
| `demo3` | `cut_hg` | 267 |
| `demo3` | `cut_hg` | 310 |
| `demo3` | `cut_hg` | 329 |

## NextPart

| Script | Target token | Line |
|---|---|---:|
| `L01_4a` | `L01_4b` | 1146 |
| `L01_4b` | `L01_4a` | 90 |
| `L02_1a` | `L02_1b` | 529 |
| `L03_2A` | `L03_2B` | 625 |
| `L03_2B` | `L03_2A` | 1188 |
| `L03_6a` | `L03_6b` | 290 |
| `L03_7a` | `L03_7b` | 415 |
| `L03_8a` | `L03_8b` | 119 |
| `L03_8b` | `L03_8a` | 195 |
| `L03_8b` | `L03_8c` | 238 |
| `L04_3a` | `L04_3b` | 664 |
| `L05_3A` | `L05_3B` | 264 |
| `L05_3B` | `L05_3A` | 355 |
| `L05_3B` | `L05_3C` | 362 |
| `L05_3C` | `L05_3B` | 415 |
| `L05_4a` | `L05_4b` | 233 |
| `L05_4b` | `L05_4a` | 277 |
| `L05_5A` | `L05_5B` | 209 |
| `L05_5B` | `L05_5A` | 183 |
| `L05_5B` | `L05_5C` | 196 |
| `L05_5C` | `L05_5B` | 275 |

Extracted 37 `NextLevel` sites and 21 `NextPart` sites. Rebuild this map from the extracted game data if those files change.
