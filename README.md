# Star Wars: Obi-Wan Recomp

Title-specific static recompilation research and Linux bring-up for the Original Xbox release of *Star Wars: Obi-Wan*. This repository is independent from the general Xbox Linux runtime project; it consumes that runtime as a separately cloned build dependency.

## Legal and source boundaries

Original project code is GPL-3.0-only; see [LICENSE](LICENSE). The parser under `vendor/xboxrecomp-parser/` retains its upstream MIT license. No executable, extracted game data, save data, or generated translation of the game is included. You must provide your own legally obtained extraction. Generated code and build outputs remain local and ignored.

## Setup

Clone this repository and the shared runtime side by side:

```sh
git clone https://github.com/soltros/obiwan-recomp.git
git clone https://github.com/soltros/xbox-linux.git
```

Place the extracted game folder beside both repositories as `../Star Wars - Obi-Wan (USA)/default.xbe`, or update `target.json` locally. The XBE SHA-256 is checked before analysis and generation.

On x86-64 Linux with Nix:

```sh
nix develop
python3 -m unittest discover -s tests -v
python3 tools/workspace.py baseline
python3 ../xbox-linux/tools/toolchain.py fetch
python3 ../xbox-linux/tools/toolchain.py check
XBOXRECOMP_DIR=../xbox-linux/third_party/xboxrecomp python3 tools/generate_obiwan.py
XBOXRECOMP_DIR=../xbox-linux/third_party/xboxrecomp python3 tools/build_obiwan.py --jobs 4
```

Copy the extracted game files into `build/game/` for runtime access, keeping saves separate in `build/save/`. Generation writes game-specific C files under ignored `src/recomp/gen/`; do not commit them. `obwan.sh` launches with the SDL framebuffer window enabled.

## Status

The title reaches its menu flow and renders the Obi-Wan logo and menu frame. Menu text and some content are still incorrect; gameplay and complete graphics/input behavior are not verified. See [SPRINT-01](docs/SPRINT-01.md) for current evidence and next steps.
