#!/usr/bin/env python3
"""Generate Obi-Wan seeded-function stand-ins and the mega-dispatch clone.

Discovery misses whole classes of reachable code in this title: pad-bounded
methods named only by vtables, former fail-fast stubs, and ~400 interior
script-command entries inside the sub_0015E940 dispatch routine. The seed
list in tools/seed_functions.json makes the next full pipeline run discover
the function-start subset; until then, and for the interior entries no
discovery can split out, this script emits the stand-in bodies the manual
dispatch in src/manual.c registers:

  * one file per seeded method reached through an adjustor thunk,
  * combined files for the xref/vtable harvest batches,
  * real bodies replacing four former stop-stubs,
  * one dispatch clone of sub_0015E940 labelling every identified
    interior entry, entered through obiwan_mega_lookup.

Run after tools/make_obiwan_entry_stub.py (generate_obiwan.py does both).
Requires the pipeline analysis tree and the SDK checkout, resolved the
same way generate_obiwan.py resolves them.
"""
import bisect
import json
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SDK = Path(os.environ.get("XBOXRECOMP_DIR",
                          ROOT.parent / "xbox-linux/third_party/xboxrecomp"))
ANA = ROOT / "build/obiwan-analysis"
GEN = ROOT / "src/recomp/gen"
SEEDS = ROOT / "tools/seed_functions.json"

# Methods reached through adjustor thunks, generated one file each. Ends are
# the last ret before the following pad run in the disassembly listing.
SINGLES = {
    0x001CADB0: 0x001CAF62,
    0x001CC490: 0x001CCC75,
    0x002400F0: 0x00240428,
    0x0019A110: 0x0019A6A7,
}
# Former fail-fast stubs (manual.c stop_ cases): level loading reaches
# 0x00112940 through the double-adjust thunk at 0x002612B0.
STOPS = [0x00076A70, 0x000E5CB0, 0x00112940, 0x0012A720]
# First-instruction classes in the xref harvest that are hand entries in
# src/manual.c instead of generated bodies (forwarder / this-adjust tails).
MICRO = {0x00126130, 0x00126BE0, 0x0014A310, 0x001AA9E0, 0x001B8E00,
         0x001BAE50, 0x001BB730, 0x001BD4C0, 0x001C1C90, 0x001C1D70,
         0x00275F00, 0x00230000}
# Interior entries already covered by make_obiwan_entry_stub.py adapters.
ADAPTED = {0x0016C39F, 0x0016B82A, 0x0016C1C4, 0x00170EED, 0x0016B0F3,
           0x0016BDB3, 0x0016A393, 0x0016A59F, 0x0016A321, 0x0016A01F,
           0x0016E96C}
HEADER = """/*
 * {desc}
 * Generated stand-in from tools/make_obiwan_seed_stubs.py; a full
 * regeneration with seeded discovery emits these in the normal chunks
 * and this file must be removed then.
 */
#define RECOMP_GENERATED_CODE
#include "recomp_funcs.h"

"""

ADDR_RE = re.compile(r"^\s+0x([0-9A-F]+)\s+([0-9a-f]+)\s+(.*)$")


def load_asm():
    lines = (ANA / "disasm/asm/text.asm").read_text(errors="replace").splitlines()
    insns = []
    for line in lines:
        m = ADDR_RE.match(line)
        if m:
            insns.append((int(m.group(1), 16), len(m.group(2)) // 2,
                          m.group(3).strip()))
    insns.sort()
    return insns


def fnend(insns, start):
    """End (exclusive) at the last ret before a >=5 nop/int3 pad run."""
    run = last = None
    run = 0
    for addr, size, text in insns:
        if addr < start:
            continue
        if text.startswith("ret"):
            last, run = addr + size, 0
            continue
        if text in ("nop", "int3"):
            run += 1
            if run >= 5 and last:
                return last
        else:
            run = 0
        if addr > start + 0x10000:
            break
    return last


def pad_before(insn_index, insns, addr):
    i = insn_index[addr]
    run = 0
    j = i - 1
    while j >= 0 and insns[j][2] in ("nop", "int3"):
        run += 1
        j -= 1
    return run


def harvest(insns, funcs, idents):
    """Recompute the three generation batches from the analysis artifacts."""
    fstarts = {int(e["start"], 16) for e in funcs}
    index = {a: i for i, (a, _s, _t) in enumerate(insns)}
    first_text = {a: t for a, _s, t in insns}
    defined = set()
    for chunk in GEN.glob("recomp_0*.c"):
        defined.update(int(x, 16) for x in re.findall(
            r"^void sub_([0-9A-F]{8})\(void\)",
            chunk.read_text(errors="replace"), re.M))
    asm_lines = (ANA / "disasm/asm/text.asm").read_text(
        errors="replace").splitlines()

    # Batch 1: pad-bounded direct xref targets discovery never split out.
    xref_targets = set()
    for i, line in enumerate(asm_lines):
        if "; XREF:" in line and ("(jump)" in line or "(call)" in line):
            for nxt in asm_lines[i + 1:i + 4]:
                m = ADDR_RE.match(nxt)
                if m:
                    xref_targets.add(int(m.group(1), 16))
                    break
    batch1 = []
    for addr in sorted(xref_targets):
        if addr in fstarts or addr in MICRO or addr in STOPS:
            continue
        if addr in SINGLES or addr not in index:
            continue
        if pad_before(index, insns, addr) >= 3:
            end = fnend(insns, addr)
            if end and addr not in defined:
                batch1.append((addr, end))

    # Batch 2: 16-aligned vtable-identified method starts (the identified
    # list is noisy inference; alignment + pad boundary is the filter).
    batch2 = []
    for e in idents:
        if e.get("category") != "game_vtable":
            continue
        try:
            addr = int(e["start"], 16)
        except (KeyError, ValueError):
            continue
        if addr % 16 or addr in fstarts or addr in defined:
            continue
        if addr in SINGLES or addr in STOPS or addr in MICRO:
            continue
        if addr not in index:
            continue
        # Adjust-first bodies still translate to correct tail entries;
        # only the four pure adjustor thunks in MICRO-style hand entries
        # were excluded when this batch was first measured.
        if addr in (0x00077040, 0x000F83A0, 0x0022FFF0, 0x00245850,
                    0x001CAF70, 0x001CCF70, 0x00240680):
            continue
        if pad_before(index, insns, addr) < 3:
            continue
        end = fnend(insns, addr)
        if end and end - addr <= 0x800:
            batch2.append((addr, end))
    batch2 = sorted(set(batch2) - set(batch1))
    # Runtime-measured during L01_1 loading; no direct xref names it.
    if (0x0022F080, fnend(insns, 0x0022F080)) not in batch1:
        batch1.append((0x0022F080, fnend(insns, 0x0022F080)))
        batch1.sort()
    return batch1, batch2


def function_body(source: str, signature: str) -> str:
    start = source.index(signature)
    opening = source.index("{", start)
    depth = 0
    i = opening
    state = "code"
    while i < len(source):
        ch = source[i]
        nxt = source[i + 1] if i + 1 < len(source) else ""
        if state == "code":
            if ch == "/" and nxt == "*":
                state = "comment"; i += 1
            elif ch == "/" and nxt == "/":
                state = "line"; i += 1
            elif ch == '"':
                state = "string"
            elif ch == "'":
                state = "char"
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return source[start:i + 1]
        elif state == "comment" and ch == "*" and nxt == "/":
            state = "code"; i += 1
        elif state == "line" and ch == "\n":
            state = "code"
        elif state in ("string", "char"):
            if ch == "\\":
                i += 1
            elif (state == "string" and ch == '"') or \
                    (state == "char" and ch == "'"):
                state = "code"
        i += 1
    raise ValueError(f"unterminated C function: {signature}")


def write_bodies(codes, fname, desc):
    out = GEN / fname
    out.write_text(HEADER.format(desc=desc)
                   + "\n".join(c.rstrip() + "\n" for c in codes))
    print(f"Wrote {out} ({out.stat().st_size} bytes)")


def build_mega(insns, idents):
    """One dispatch clone of sub_0015E940 covering its interior entries."""
    starts = {a for a, _s, _t in insns}
    fstarts = set()
    raw = (GEN / "recomp_0048.c").read_text(errors="replace")
    body_src = function_body(raw, "void sub_0015E940(void)")
    cand = set()
    for e in idents:
        try:
            a = int(e["start"], 16)
        except (KeyError, ValueError, TypeError):
            continue
        if 0x0015E940 < a < 0x001760B0 and a in starts and a not in ADAPTED:
            cand.add(a)
    cand.add(0x0016F71F)
    lines = body_src.splitlines(True)
    loc_re = re.compile(r"^loc_([0-9A-F]{8}):")
    goto_re = re.compile(r"^\s+goto loc_([0-9A-F]{8});")

    def assign(lins):
        locs = [(int(m.group(1), 16), i) for i, l in enumerate(lins)
                if (m := loc_re.match(l))]
        addrs = [a for a, _i in locs]
        have = set(addrs)
        got, inserts = [], []
        for va in sorted(cand):
            if va in have:
                got.append(va)
                continue
            k = bisect.bisect_right(addrs, va) - 1
            if k < 0 or k + 1 >= len(locs):
                continue
            _lo, lo_i = locs[k]
            _hi, hi_i = locs[k + 1]
            g = next((j for j in range(lo_i, hi_i)
                      if goto_re.search(lins[j])), None)
            if g is None:
                continue
            j = g + 1
            while j < hi_i and not lins[j].strip():
                j += 1
            if j < hi_i:
                inserts.append((va, j))
                got.append(va)
        return got, inserts
    got, inserts = assign(lines)
    for va, j in sorted(inserts, key=lambda x: -x[1]):
        lines.insert(j, f"loc_{va:08X}: ;\n")
    body = "".join(lines).replace(
        "void sub_0015E940(void)", "void obiwan_mega_dispatch_0015E940(void)", 1)
    # The parent's own first block begins with its SEH prologue; entries
    # arrive with the dispatcher's frame, so jump straight to the block.
    first = body.find("\nloc_")
    cases = "".join(f"        case 0x{a:08X}u: goto loc_{a:08X};\n"
                    for a in sorted(set(got)))
    switch = ("\n    ebp = g_seh_ebp;\n"
              "    switch (g_obiwan_mega_va) {\n" + cases +
              "        default: break;\n    }\n")
    body = body[:first] + switch + body[first:]
    out = GEN / "recomp_mega_dispatch.c"
    out.write_text(
        "/*\n * Obi-Wan mega-dispatch clone of sub_0015E940 (script command\n"
        " * handlers). Generated by tools/make_obiwan_seed_stubs.py;\n"
        " * remove on full regeneration.\n */\n"
        "#define RECOMP_GENERATED_CODE\n"
        '#include "recomp_funcs.h"\n\n'
        "extern RECOMP_TLS uint32_t g_obiwan_mega_va;\n\n" + body)
    vas = sorted(set(got))
    lk = ["/* Obi-Wan mega-dispatch lookup. Generated stand-in. */",
          "#define RECOMP_GENERATED_CODE",
          '#include "recomp_funcs.h"', "",
          "RECOMP_TLS uint32_t g_obiwan_mega_va;",
          "void obiwan_mega_dispatch_0015E940(void);", "",
          "recomp_func_t obiwan_mega_lookup(uint32_t va)", "{",
          "    switch (va) {"]
    lk += [f"    case 0x{a:08X}u:" for a in vas]
    lk += ["        g_obiwan_mega_va = va;",
           "        return (recomp_func_t)obiwan_mega_dispatch_0015E940;",
           "    default: return NULL;", "    }", "}", ""]
    (GEN / "recomp_mega_lookup.c").write_text("\n".join(lk))
    print(f"mega dispatch covers {len(vas)} entries")
    return vas


def main():
    insns = load_asm()
    funcs = json.loads((ANA / "disasm/functions.json").read_text())
    idents = json.loads(
        (ANA / "func-id/identified_functions.json").read_text())
    batch1, batch2 = harvest(insns, funcs, idents)
    singles = sorted(SINGLES.items())
    stops = [(a, fnend(insns, a)) for a in STOPS]
    wanted = singles + batch1 + batch2 + stops
    for addr, end in wanted:
        if not end:
            raise ValueError(f"no bounded end for seed {addr:#x}")

    # Patch the function database in a scratch copy and translate every
    # wanted body in one translator load (the per-body cost after the
    # ~95s database load is negligible).
    have = {int(e["start"], 16) for e in funcs}
    for addr, end in wanted:
        if addr not in have:
            funcs.append({
                "start": f"0x{addr:08X}", "end": f"0x{end:08X}",
                "size": end - addr, "name": f"sub_{addr:08X}",
                "section": ".text", "confidence": 0.75,
                "detection_method": "manual_seed", "num_instructions": 0,
                "has_prologue": False, "calls_to": [], "called_by": []})
    patched = ANA / "seed_functions_patched.json"
    patched.write_text(json.dumps(funcs))

    sys.path.insert(0, str(SDK))
    os.chdir(SDK)
    from tools.recomp import config
    from tools.recomp.translator import BatchTranslator
    from tools.recomp.__main__ import find_data_files
    import tools.recomp.translator as tm
    tm.ENTRY_HOOKS = set()
    xbe = str(ANA / "default.xbe")
    files = find_data_files(
        disasm_dir=str(ANA / "disasm"), func_id_dir=str(ANA / "func-id"),
        abi_dir=str(ANA / "abi"),
        overrides={"functions": str(patched)})
    config.configure_from_xbe(xbe)
    t0 = time.time()
    batch = BatchTranslator(
        xbe_path=xbe, func_json_path=files["functions"],
        labels_json_path=files.get("labels"),
        identified_json_path=files.get("identified"),
        abi_json_path=files.get("abi"), output_dir=None,
        trace_functions=set(), force_returns={}, coalesce_json_paths=None,
        protected_function_starts=set(), seh_prolog=None, seh_epilog=None,
        icall_sites_json_path=str(
            SDK / "tools/recomp/output/icall_sites.json"),
        back_edge_yield=False, entry_stubs=False)
    print(f"loaded {len(batch.func_db)} functions in "
          f"{time.time() - t0:.1f}s", file=sys.stderr)
    codes = {}
    for addr, _end in wanted:
        code = batch.translate_single(addr)
        if not code:
            raise ValueError(f"could not translate seed {addr:#x}")
        codes[addr] = code
    for addr, _end in singles:
        write_bodies([codes[addr]], f"recomp_entry_{addr:08x}.c",
                     f"Seeded function sub_{addr:08X}.")
    write_bodies([codes[a] for a, _e in batch1],
                 "recomp_entry_seeds_batch.c",
                 "Seeded pad-bounded xref-target bodies.")
    write_bodies([codes[a] for a, _e in batch2],
                 "recomp_entry_seeds_batch2.c",
                 "Seeded vtable-class bodies.")
    write_bodies([codes[a] for a, _e in stops],
                 "recomp_entry_seeds_batch3.c",
                 "Bodies replacing former fail-fast stubs.")
    vas = build_mega(insns, idents)
    if 0x0016F71F not in vas:
        raise ValueError("mega dispatch lost the measured 0x16F71F entry")
    # The seeded stops must not also be emitted as stubs on this build.
    stubs = GEN / "recomp_stubs_unresolved.c"
    if stubs.exists():
        kept = [l for l in stubs.read_text().splitlines(True)
                if not any(l.startswith(f"void sub_{a:08X}(void)")
                           for a, _e in stops)]
        stubs.write_text("".join(kept))
    # Mega interior entries are not discovery seeds: seeding interior
    # addresses would clamp their containing functions (see the disasm
    # tool's --seed-functions warning). Only real starts are recorded.
    seeds = sorted({a for a, _e in wanted})
    existing = {int(e["start"], 16)
                for e in json.loads(SEEDS.read_text())} \
        if SEEDS.exists() else set()
    merged = sorted(existing | set(seeds))
    SEEDS.write_text(json.dumps([{"start": f"0x{a:08X}"} for a in merged],
                                indent=2) + "\n")
    print(f"seeds recorded: {len(merged)}")


if __name__ == "__main__":
    main()


