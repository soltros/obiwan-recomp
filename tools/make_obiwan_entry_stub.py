#!/usr/bin/env python3
"""Generate manually dispatched interior entries in Obi-Wan's large tail routine."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/recomp/gen/recomp_0048.c"
OUTPUT = ROOT / "src/recomp/gen/recomp_entry_0016c39f.c"
OUTPUT_B = ROOT / "src/recomp/gen/recomp_entry_0016b82a.c"
OUTPUT_C = ROOT / "src/recomp/gen/recomp_entry_0016c1c4.c"
OUTPUT_D = ROOT / "src/recomp/gen/recomp_entry_00170eed.c"
OUTPUT_E = ROOT / "src/recomp/gen/recomp_entry_0016b0f3.c"
OUTPUT_F = ROOT / "src/recomp/gen/recomp_entry_0016bdb3.c"
OUTPUT_G = ROOT / "src/recomp/gen/recomp_entry_0016a393.c"
OUTPUT_H = ROOT / "src/recomp/gen/recomp_entry_0016a59f.c"


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
                state = "comment"
                i += 1
            elif ch == "/" and nxt == "/":
                state = "line"
                i += 1
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
            state = "code"
            i += 1
        elif state == "line" and ch == "\n":
            state = "code"
        elif state in ("string", "char"):
            if ch == "\\":
                i += 1
            elif (state == "string" and ch == '"') or (state == "char" and ch == "'"):
                state = "code"
        i += 1
    raise ValueError(f"unterminated C function: {signature}")


def main() -> None:
    source = SOURCE.read_text()
    body = function_body(source, "void sub_0016C311(void)")
    body = body.replace("void sub_0016C311(void)", "void obiwan_entry_0016C39F(void)", 1)
    inherited = "    ebp = g_seh_ebp; /* fpo_leaf: inherit caller's frame */"
    if body.count(inherited) != 1:
        raise ValueError("unexpected generated parent prologue")
    body = body.replace(inherited, inherited + "\n    goto loc_0016C39F;", 1)
    marker = "loc_0016C3AF: ;"
    entry = """loc_0016C39F: ;
    _fa = (uint32_t)(MEM32(esp + 0x33C4)) & 0xFFFFFFFFu;
    _fb = 2u;
    _fas = (int32_t)_fa;
    _fbs = (int32_t)_fb;
    _cf = (int)(_fa < _fb);
    ecx = esi;
    if (CMP_L(_fas, _fbs)) goto loc_001754B3;

"""
    if body.count(marker) != 1:
        raise ValueError("expected interior block boundary is missing or ambiguous")
    body = body.replace(marker, entry + marker, 1)
    output = """/*
 * Obi-Wan interior entry adapter for 0x0016C39F.
 * Generated parent body is cloned and entered at the recovered basic block;
 * the adjacent omitted cmp/mov/jl instructions are restored from XBE bytes.
 * Regenerate with tools/make_obiwan_entry_stub.py after recompilation.
 */
#define RECOMP_GENERATED_CODE
#include "recomp_funcs.h"

""" + body + "\n"
    OUTPUT.write_text(output)
    print(f"Wrote {OUTPUT} ({len(output)} bytes)")

    # The entry at 0x16B82A is another instruction boundary omitted by the
    # overlapping-function scan. Its continuation is present in sub_16AC24.
    source_b = function_body(source, "void sub_0016AC24(void)")
    source_b = source_b.replace("void sub_0016AC24(void)",
                                "void obiwan_entry_0016B82A(void)", 1)
    if source_b.count(inherited) != 1:
        raise ValueError("unexpected generated parent prologue for 0x16B82A")
    source_b = source_b.replace(inherited,
                                inherited + "\n    goto loc_0016B82A;", 1)
    marker_b = "loc_0016B83A: ;"
    entry_b = """loc_0016B82A: ;
    _fa = (uint32_t)(MEM32(esp + 0x33C4)) & 0xFFFFFFFFu;
    _fb = 2u;
    _fas = (int32_t)_fa;
    _fbs = (int32_t)_fb;
    _cf = (int)(_fa < _fb);
    ecx = esi;
    if (CMP_L(_fas, _fbs)) goto loc_001754B3;

"""
    if source_b.count(marker_b) != 1:
        raise ValueError("expected 0x16B83A continuation is missing or ambiguous")
    source_b = source_b.replace(marker_b, entry_b + marker_b, 1)
    output_b = """/*
 * Obi-Wan interior entry adapter for 0x0016B82A.
 * Clones the generated tail routine and restores the omitted cmp/mov/jl block.
 * Regenerate with tools/make_obiwan_entry_stub.py after recompilation.
 */
#define RECOMP_GENERATED_CODE
#include "recomp_funcs.h"

""" + source_b + "\n"
    OUTPUT_B.write_text(output_b)
    print(f"Wrote {OUTPUT_B} ({len(output_b)} bytes)")

    source_c = function_body(source, "void sub_0016AC24(void)")
    source_c = source_c.replace("void sub_0016AC24(void)",
                                "void obiwan_entry_0016C1C4(void)", 1)
    if source_c.count(inherited) != 1:
        raise ValueError("unexpected generated parent prologue for 0x16C1C4")
    source_c = source_c.replace(inherited,
                                inherited + "\n    goto loc_0016C1C4;", 1)
    marker_c = "loc_0016C1D2: ;"
    entry_c = """loc_0016C1C4: ;
    _fa = (uint32_t)(MEM32(esp + 0x33C4)) & 0xFFFFFFFFu;
    _fb = 2u;
    _fas = (int32_t)_fa;
    _fbs = (int32_t)_fb;
    _cf = (int)(_fa < _fb);
    if (CMP_L(_fas, _fbs)) goto loc_001754B1;

"""
    if source_c.count(marker_c) != 1:
        raise ValueError("expected 0x16C1D2 continuation is missing or ambiguous")
    source_c = source_c.replace(marker_c, entry_c + marker_c, 1)
    output_c = """/*
 * Obi-Wan interior entry adapter for 0x0016C1C4.
 * Restores the omitted cmp/jl block and enters the generated continuation.
 * Regenerate with tools/make_obiwan_entry_stub.py after recompilation.
 */
#define RECOMP_GENERATED_CODE
#include "recomp_funcs.h"

""" + source_c + "\n"
    OUTPUT_C.write_text(output_c)
    print(f"Wrote {OUTPUT_C} ({len(output_c)} bytes)")

    # This branch can loop back to 0x15E9E4, so use the larger generated parent
    # that contains both the entry block and that target label.
    source_d = function_body(source, "void sub_0015E940(void)")
    source_d = source_d.replace("void sub_0015E940(void)",
                                "void obiwan_entry_00170EED(void)", 1)
    if source_d.count(inherited) != 1:
        raise ValueError("unexpected generated parent prologue for 0x170EED")
    source_d = source_d.replace(inherited,
                                inherited + "\n    goto loc_00170EED;", 1)
    marker_d = "loc_00170EFB: ;"
    entry_d = """loc_00170EED: ;
    SET_LO8(eax, MEM8(esi + 0x490));
    _fa = (uint32_t)(LO8(eax)) & 0xFFu;
    _fb = 0u;
    _fas = (int32_t)(int8_t)_fa;
    _fbs = 0;
    if (CMP_NE(_fa, _fb)) goto loc_0015E9E4;

"""
    if source_d.count(marker_d) != 1:
        raise ValueError("expected 0x170EFB continuation is missing or ambiguous")
    source_d = source_d.replace(marker_d, entry_d + marker_d, 1)
    output_d = """/*
 * Obi-Wan interior entry adapter for 0x00170EED.
 * Restores the omitted mov/test/jne block and enters the generated continuation.
 * Regenerate with tools/make_obiwan_entry_stub.py after recompilation.
 */
#define RECOMP_GENERATED_CODE
#include "recomp_funcs.h"

""" + source_d + "\n"
    OUTPUT_D.write_text(output_d)
    print(f"Wrote {OUTPUT_D} ({len(output_d)} bytes)")

    source_e = function_body(source, "void sub_0016AC24(void)")
    source_e = source_e.replace("void sub_0016AC24(void)",
                                "void obiwan_entry_0016B0F3(void)", 1)
    if source_e.count(inherited) != 1:
        raise ValueError("unexpected generated parent prologue for 0x16B0F3")
    source_e = source_e.replace(inherited,
                                inherited + "\n    goto loc_0016B0F3;", 1)
    marker_e = "loc_0016B105: ;"
    entry_e = """loc_0016B0F3: ;
    ebx = MEM32(esp + 0x33C4);
    _fa = (uint32_t)(ebx) & 0xFFFFFFFFu;
    _fb = 1u;
    _fas = (int32_t)_fa;
    _fbs = (int32_t)_fb;
    ecx = esi;
    if (CMP_L(_fas, _fbs)) goto loc_001754B3;

"""
    if source_e.count(marker_e) != 1:
        raise ValueError("expected 0x16B105 continuation is missing or ambiguous")
    source_e = source_e.replace(marker_e, entry_e + marker_e, 1)
    output_e = """/*
 * Obi-Wan interior entry adapter for 0x0016B0F3.
 * Restores the omitted mov/cmp/mov/jl block from the guest instruction bytes.
 * Regenerate with tools/make_obiwan_entry_stub.py after recompilation.
 */
#define RECOMP_GENERATED_CODE
#include "recomp_funcs.h"

""" + source_e + "\n"
    OUTPUT_E.write_text(output_e)
    print(f"Wrote {OUTPUT_E} ({len(output_e)} bytes)")

    source_f = function_body(source, "void sub_0016AC24(void)")
    source_f = source_f.replace("void sub_0016AC24(void)",
                                "void obiwan_entry_0016BDB3(void)", 1)
    if source_f.count(inherited) != 1:
        raise ValueError("unexpected generated parent prologue for 0x16BDB3")
    source_f = source_f.replace(inherited,
                                inherited + "\n    goto loc_0016BDB3;", 1)
    marker_f = "loc_0016BDC1: ;"
    entry_f = """loc_0016BDB3: ;
    _fa = (uint32_t)(MEM32(esp + 0x33C4)) & 0xFFFFFFFFu;
    _fb = 1u;
    _fas = (int32_t)_fa;
    _fbs = (int32_t)_fb;
    if (CMP_L(_fas, _fbs)) goto loc_001754B1;

"""
    if source_f.count(marker_f) != 1:
        raise ValueError("expected 0x16BDC1 continuation is missing or ambiguous")
    source_f = source_f.replace(marker_f, entry_f + marker_f, 1)
    output_f = """/*
 * Obi-Wan interior entry adapter for 0x0016BDB3.
 * Restores the omitted cmp/jl block from guest instruction bytes.
 * Regenerate with tools/make_obiwan_entry_stub.py after recompilation.
 */
#define RECOMP_GENERATED_CODE
#include "recomp_funcs.h"

""" + source_f + "\n"
    OUTPUT_F.write_text(output_f)
    print(f"Wrote {OUTPUT_F} ({len(output_f)} bytes)")

    # A menu selection reaches another interior block in the same large
    # overlapping routine. Restore cmp [esp+0x33c4],1 / jl 0x1754b1 before
    # joining the generated continuation at 0x16A3A1.
    source_g = function_body(source, "void sub_0015E940(void)")
    source_g = source_g.replace("void sub_0015E940(void)",
                                "void obiwan_entry_0016A393(void)", 1)
    if source_g.count(inherited) != 1:
        raise ValueError("unexpected generated parent prologue for 0x16A393")
    source_g = source_g.replace(inherited,
                                inherited + "\n    goto loc_0016A393;", 1)
    marker_g = "loc_0016A3A1: ;"
    entry_g = """loc_0016A393: ;
    _fa = (uint32_t)(MEM32(esp + 0x33C4)) & 0xFFFFFFFFu;
    _fb = 1u;
    _fas = (int32_t)_fa;
    _fbs = (int32_t)_fb;
    _cf = (int)(_fa < _fb);
    if (CMP_L(_fas, _fbs)) goto loc_001754B1;

"""
    if source_g.count(marker_g) != 1:
        raise ValueError("expected 0x16A3A1 continuation is missing or ambiguous")
    source_g = source_g.replace(marker_g, entry_g + marker_g, 1)
    output_g = """/*
 * Obi-Wan interior entry adapter for 0x0016A393.
 * Restores the omitted cmp/jl block from guest instruction bytes.
 * Regenerate with tools/make_obiwan_entry_stub.py after recompilation.
 */
#define RECOMP_GENERATED_CODE
#include "recomp_funcs.h"

""" + source_g + "\n"
    OUTPUT_G.write_text(output_g)
    print(f"Wrote {OUTPUT_G} ({len(output_g)} bytes)")

    # A later SELECT-screen action reaches another dropped interior block in
    # the same routine. Restore mov/cmp/mov/jl before its generated join.
    source_h = function_body(source, "void sub_0015E940(void)")
    source_h = source_h.replace("void sub_0015E940(void)",
                                "void obiwan_entry_0016A59F(void)", 1)
    if source_h.count(inherited) != 1:
        raise ValueError("unexpected generated parent prologue for 0x16A59F")
    source_h = source_h.replace(inherited,
                                inherited + "\n    goto loc_0016A59F;", 1)
    marker_h = "loc_0016A5B1: ;"
    entry_h = """loc_0016A59F: ;
    _fa = (uint32_t)(MEM32(esp + 0x33C4)) & 0xFFFFFFFFu;
    _fb = 1u;
    _fas = (int32_t)_fa;
    _fbs = (int32_t)_fb;
    ecx = esi;
    _cf = (int)(_fa < _fb);
    if (CMP_L(_fas, _fbs)) goto loc_001754B3;

"""
    if source_h.count(marker_h) != 1:
        raise ValueError("expected 0x16A5B1 continuation is missing or ambiguous")
    source_h = source_h.replace(marker_h, entry_h + marker_h, 1)
    output_h = """/*
 * Obi-Wan interior entry adapter for 0x0016A59F.
 * Restores the omitted mov/cmp/mov/jl block from guest instruction bytes.
 * Regenerate with tools/make_obiwan_entry_stub.py after recompilation.
 */
#define RECOMP_GENERATED_CODE
#include "recomp_funcs.h"

""" + source_h + "\n"
    OUTPUT_H.write_text(output_h)
    print(f"Wrote {OUTPUT_H} ({len(output_h)} bytes)")


if __name__ == "__main__":
    main()
