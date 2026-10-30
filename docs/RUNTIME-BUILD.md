# Runtime build note

This title project uses a separately cloned Xbox Linux runtime. Its upstream revision is pinned in `toolchain.json`; Linux changes are applied by the runtime repository's `tools/toolchain.py`. Configure this project with `XBOXRECOMP_DIR=/path/to/xbox-linux/third_party/xboxrecomp` when the two repositories are not siblings.

A successful runtime build verifies compilation only. It does not establish that the title is playable.
