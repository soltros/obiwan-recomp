# Star Wars: Obi-Wan Recomp

Title-specific static recompilation research and Linux bring-up for the Original Xbox release of *Star Wars: Obi-Wan*. This repository is independent from the general Xbox Linux runtime project; it consumes that runtime as a separately cloned build dependency.

## Legal and source boundaries

Original project code is GPL-3.0-only; see [LICENSE](LICENSE). The parser under `vendor/xboxrecomp-parser/` retains its upstream MIT license. No executable, extracted game data, save data, or generated translation of the game is included. You must provide your own legally obtained extraction. Generated code and build outputs remain local and ignored.

## Setup

For a one-command setup on x86-64 Linux with Nix flakes enabled, put your legally obtained extraction anywhere and run:

```sh
./install.sh "/path/to/Star Wars - Obi-Wan (USA)"
```

The installer checks the exact XBE hash, clones the shared runtime if needed, fetches and builds its pinned framework, runs the project checks, generates title C, and builds the launcher. It does not copy or upload your game files. `XBOX_LINUX_DIR=/path/to/xbox-linux` and `JOBS=8` can customize the runtime checkout and parallel build count.

You can also clone the repositories side by side:

```sh
git clone https://github.com/soltros/obiwan-recomp.git
git clone https://github.com/soltros/xbox-linux.git
```

The default extraction location is `../Star Wars - Obi-Wan (USA)/default.xbe`; alternatively pass any extraction directory to `install.sh`.

On x86-64 Linux with Nix:

```sh
nix develop
python3 -m unittest discover -s tests -v
../xbox-linux/tools/install_runtime.sh
XBOXRECOMP_DIR=../xbox-linux/third_party/xboxrecomp python3 tools/generate_obiwan.py --game-dir "../Star Wars - Obi-Wan (USA)"
XBOXRECOMP_DIR=../xbox-linux/third_party/xboxrecomp python3 tools/build_obiwan.py --jobs 4
```

For read-only checks of the extracted assets and font container tables, run `python3 tools/workspace.py fonts --game-dir "/path/to/extraction"`. The report is written under ignored `reports/obiwan/fonts.json`; it checks file layout and offsets but does not claim to decode glyphs or explain renderer output.

Generation writes game-specific C files under ignored `src/recomp/gen/`; do not commit them. Launch using `./obwan.sh "/path/to/extracted/game" [save-directory]`; by default saves go to `build/save/`. The script enables the SDL framebuffer window.

## Status

The title reaches its menu flow and renders the Obi-Wan logo and menu frame. Menu text and some content are still incorrect; gameplay and complete graphics/input behavior are not verified. See [SPRINT-01](docs/SPRINT-01.md) for current evidence and next steps.
