/* Fail at the first unresolved direct call instead of returning guessed guest state. */
#include <stdio.h>
#include <stdlib.h>
#include "recomp_types.h"

extern void obiwan_entry_0016C39F(void);
extern void obiwan_entry_0016B82A(void);
extern void obiwan_entry_0016C1C4(void);
extern void obiwan_entry_00170EED(void);
extern void obiwan_entry_0016B0F3(void);
extern void obiwan_entry_0016BDB3(void);
extern void obiwan_entry_0016A393(void);
extern void obiwan_entry_0016A59F(void);
extern void obiwan_entry_0016A321(void);
extern void obiwan_entry_0016A01F(void);
extern void obiwan_entry_0016E96C(void);
extern void obiwan_entry_0016F71F(void);
extern recomp_func_t obiwan_mega_lookup(uint32_t);
extern void sub_0019A110(void);
extern void sub_001CADB0(void);
extern void sub_001CC490(void);
extern void sub_002400F0(void);
extern void sub_00125DC0(void);
extern void sub_00149F50(void);
extern void sub_001B6020(void);
extern void sub_001AB510(void);
extern void sub_000642D0(void);
extern void sub_00044930(void);
extern void sub_000F0C90(void);
extern void sub_0003F640(void);
extern void sub_0003AB80(void);
extern void sub_000E5C40(void);
extern void sub_000E8700(void);
extern void sub_00111BF0(void);
extern void sub_0012D150(void);
extern void sub_0012D180(void);
extern void sub_0012D1B0(void);
extern void sub_0014DCF0(void);
extern void sub_0014E6E0(void);
extern void sub_0014EC70(void);
extern void sub_0014ECA0(void);
extern void sub_0014ECD0(void);
extern void sub_0014EE80(void);
extern void sub_0014EEB0(void);
extern void sub_0014EEE0(void);
extern void sub_0014F090(void);
extern void sub_0014F0C0(void);
extern void sub_0014F0F0(void);
extern void sub_0014F2B0(void);
extern void sub_0014F2E0(void);
extern void sub_0014F310(void);
extern void sub_0014F870(void);
extern void sub_0014F8A0(void);
extern void sub_0014F8D0(void);
extern void sub_0014F900(void);
extern void sub_0014F980(void);
extern void sub_0014FA50(void);
extern void sub_0014FA80(void);
extern void sub_0014FAB0(void);
extern void sub_0014FAE0(void);
extern void sub_0014FB60(void);
extern void sub_0014FCF0(void);
extern void sub_0014FD20(void);
extern void sub_0014FD50(void);
extern void sub_0014FD80(void);
extern void sub_00153090(void);
extern void sub_001530C0(void);
extern void sub_001530F0(void);
extern void sub_00153120(void);
extern void sub_001531A0(void);
extern void sub_00158C70(void);
extern void sub_00158CA0(void);
extern void sub_00158CD0(void);
extern void sub_00158D00(void);
extern void sub_00158D30(void);
extern void sub_00158D60(void);
extern void sub_0015AEF0(void);
extern void sub_0015AF70(void);
extern void sub_0015AFF0(void);
extern void sub_0015B070(void);
extern void sub_00184BE0(void);
extern void sub_001AA820(void);
extern void sub_001BD420(void);
extern void sub_001D6C90(void);
extern void sub_001DDA00(void);
extern void sub_002805F0(void);
extern void sub_0028BDA0(void);
extern void sub_0029D380(void);
extern void sub_002A9770(void);
extern void sub_0031E3D0(void);
extern void sub_000577E0(void);
extern void sub_00125450(void);
extern void sub_00210E50(void);
extern void sub_002127B0(void);
extern void sub_00212870(void);
extern void sub_00212910(void);
extern void sub_0021A920(void);
extern void sub_0021AA30(void);
extern void sub_0022F080(void);
extern void sub_0028ADA0(void);

extern void sub_00023D11(void);
extern void sub_00023D1F(void);
extern void sub_00076A70(void);
extern void sub_000E5CB0(void);
extern void sub_00112940(void);
extern void sub_0012A720(void);
extern void sub_00143903(void);
extern void sub_0028A6FA(void);
extern void sub_003A9207(void);
extern void sub_003A920A(void);
extern void sub_003A9221(void);
extern void sub_003A9244(void);
extern void sub_3D025672(void);
extern void sub_F822E348(void);

static void unresolved(uint32_t va) {
    fprintf(stderr,"[UNRESOLVED] guest target=0x%08x esp=0x%08x\n",va,g_esp);
    fflush(stderr);_Exit(86);
}
static void stop_sub_00023D11(void) { unresolved(0x00023d11u); }
static void stop_sub_00023D1F(void) { unresolved(0x00023d1fu); }
static void stop_sub_00076A70(void) { unresolved(0x00076a70u); }
static void stop_sub_000E5CB0(void) { unresolved(0x000e5cb0u); }
static void stop_sub_00112940(void) { unresolved(0x00112940u); }
static void stop_sub_0012A720(void) { unresolved(0x0012a720u); }
static void stop_sub_00143903(void) { unresolved(0x00143903u); }
static void stop_sub_0028A6FA(void) { unresolved(0x0028a6fau); }
static void stop_sub_003A9207(void) { unresolved(0x003a9207u); }
static void stop_sub_003A920A(void) { unresolved(0x003a920au); }
static void stop_sub_003A9221(void) { unresolved(0x003a9221u); }
static void stop_sub_003A9244(void) { unresolved(0x003a9244u); }
static void stop_sub_3D025672(void) { unresolved(0x3d025672u); }
static void stop_sub_F822E348(void) { unresolved(0xf822e348u); }

/* The vtable detector found this getter at 0x2CDFD8, but the broad code
 * scanner coalesced the surrounding overlapping tail-dispatch helpers and
 * omitted this entry from generated dispatch. Preserve the exact epilogue
 * present at this address: mov eax,[ebp+8]; pop esi; pop edi; leave; ret. */
static void sub_002CDFD8(void) {
    g_eax = MEM32(g_ebp + 8);
    g_esi = MEM32(g_esp); g_esp += 4;
    g_edi = MEM32(g_esp); g_esp += 4;
    g_esp = g_ebp;
    g_ebp = MEM32(g_esp);
    g_esp += 8;
}

/* Adjacent overlapping cls_168 vtable helper: copy two bytes, return the
 * original [ebp+8] value, then use the same saved-register epilogue. */
static void sub_002CDFEC(void) {
    uint8_t lo = MEM8(g_esi);
    MEM8(g_edi) = lo;
    uint8_t hi = MEM8(g_esi + 1);
    MEM8(g_edi + 1) = hi;
    g_eax = MEM32(g_ebp + 8);
    g_esi = MEM32(g_esp); g_esp += 4;
    g_edi = MEM32(g_esp); g_esp += 4;
    g_esp = g_ebp;
    g_ebp = MEM32(g_esp);
    g_esp += 8;
}

/* cls_761 adjustor thunk at 0x001CAF70 (XBE bytes 2b49fc e938feffff):
 * sub ecx,[ecx-4]; jmp sub_001CADB0. Flags from the sub are dead on entry
 * to the callee's prologue. */
static void sub_001CAF70(void) {
    g_ecx = g_ecx - MEM32(g_ecx - 4);
    sub_001CADB0();
}

/* cls adjustor thunk at 0x001CCF70: sub ecx,[ecx-4]; jmp sub_001CC490. */
static void sub_001CCF70(void) {
    g_ecx = g_ecx - MEM32(g_ecx - 4);
    sub_001CC490();
}

/* cls adjustor thunk at 0x00240680: sub ecx,[ecx-4]; jmp sub_002400F0. */
static void sub_00240680(void) {
    g_ecx = g_ecx - MEM32(g_ecx - 4);
    sub_002400F0();
}

/* Harvested forwarder / this-adjust entries (XBE bytes in each
 * comment); bodies are the jump targets, already generated. */
/* 0x00126130: forwarder to 0x00125450 (jmp). */
static void sub_00126130(void) {
    sub_00125450();
}
/* 0x00126BE0: forwarder to 0x00125DC0 (jmp). */
static void sub_00126BE0(void) {
    sub_00125DC0();
}
/* 0x0014A310: forwarder to 0x00149F50 (jmp). */
static void sub_0014A310(void) {
    sub_00149F50();
}
/* 0x001AA9E0: scalar adjust to 0x0003AB80 (mov edx,[ecx-0xa4]; mov eax,[edx+0x10]; lea ecx,[eax+ecx+0x18]; jmp). */
static void sub_001AA9E0(void) {
    g_ecx = MEM32(MEM32(g_ecx - 0xA4) + 0x10) + g_ecx + 0x18;
    sub_0003AB80();
}
/* 0x001B8E00: this-adjust -0x1C to 0x001AB510. */
static void sub_001B8E00(void) {
    g_ecx -= 0x1C;
    sub_001AB510();
}
/* 0x001BAE50: forwarder to 0x001B6020 (jmp). */
static void sub_001BAE50(void) {
    sub_001B6020();
}
/* 0x001BB730: this-adjust -4 to 0x001AB510. */
static void sub_001BB730(void) {
    g_ecx -= 4;
    sub_001AB510();
}
/* 0x001BD4C0: this-adjust -0x1F0 to 0x000642D0. */
static void sub_001BD4C0(void) {
    g_ecx += 0xFFFFFE10u;
    sub_000642D0();
}
/* 0x001C1C90: this-adjust -0x21 to 0x00044930. */
static void sub_001C1C90(void) {
    g_ecx += 0xFFFFFFDFu;
    sub_00044930();
}
/* 0x001C1D70: this-adjust -0x99 to 0x000F0C90. */
static void sub_001C1D70(void) {
    g_ecx += 0xFFFFFF67u;
    sub_000F0C90();
}
/* 0x00275F00: this-adjust -8 to 0x0003F640. */
static void sub_00275F00(void) {
    g_ecx -= 8;
    sub_0003F640();
}

/* 0x002612B0 double-adjust thunk: sub ecx,[ecx-4]; sub ecx,0x238;
 * jmp sub_00112940. */
static void sub_002612B0(void) {
    g_ecx = g_ecx - MEM32(g_ecx - 4) - 0x238;
    sub_00112940();
}

recomp_func_t recomp_lookup_manual(uint32_t va) {
    switch(va) {
    case 0x002cdfd8u:return sub_002CDFD8;
    case 0x002cdfecu:return sub_002CDFEC;
    case 0x0016c39fu:return obiwan_entry_0016C39F;
    case 0x0016b82au:return obiwan_entry_0016B82A;
    case 0x0016c1c4u:return obiwan_entry_0016C1C4;
    case 0x00170eedu:return obiwan_entry_00170EED;
    case 0x0016b0f3u:return obiwan_entry_0016B0F3;
    case 0x0016bdb3u:return obiwan_entry_0016BDB3;
    case 0x0016a393u:return obiwan_entry_0016A393;
    case 0x0016a59fu:return obiwan_entry_0016A59F;
    case 0x0016a321u:return obiwan_entry_0016A321;
    case 0x0016a01fu:return obiwan_entry_0016A01F;
    case 0x0016e96cu:return obiwan_entry_0016E96C;
    case 0x0016f71fu:return obiwan_entry_0016F71F;
    case 0x0019a110u:return sub_0019A110;
    case 0x001cadb0u:return sub_001CADB0;
    case 0x001caf70u:return sub_001CAF70;
    case 0x001cc490u:return sub_001CC490;
    case 0x001ccf70u:return sub_001CCF70;
    case 0x002400f0u:return sub_002400F0;
    case 0x00240680u:return sub_00240680;
    case 0x002612b0u:return sub_002612B0;
    case 0x000e5c40u:return sub_000E5C40;
    case 0x000e8700u:return sub_000E8700;
    case 0x00111bf0u:return sub_00111BF0;
    case 0x0012d150u:return sub_0012D150;
    case 0x0012d180u:return sub_0012D180;
    case 0x0012d1b0u:return sub_0012D1B0;
    case 0x0014dcf0u:return sub_0014DCF0;
    case 0x0014e6e0u:return sub_0014E6E0;
    case 0x0014ec70u:return sub_0014EC70;
    case 0x0014eca0u:return sub_0014ECA0;
    case 0x0014ecd0u:return sub_0014ECD0;
    case 0x0014ee80u:return sub_0014EE80;
    case 0x0014eeb0u:return sub_0014EEB0;
    case 0x0014eee0u:return sub_0014EEE0;
    case 0x0014f090u:return sub_0014F090;
    case 0x0014f0c0u:return sub_0014F0C0;
    case 0x0014f0f0u:return sub_0014F0F0;
    case 0x0014f2b0u:return sub_0014F2B0;
    case 0x0014f2e0u:return sub_0014F2E0;
    case 0x0014f310u:return sub_0014F310;
    case 0x0014f870u:return sub_0014F870;
    case 0x0014f8a0u:return sub_0014F8A0;
    case 0x0014f8d0u:return sub_0014F8D0;
    case 0x0014f900u:return sub_0014F900;
    case 0x0014f980u:return sub_0014F980;
    case 0x0014fa50u:return sub_0014FA50;
    case 0x0014fa80u:return sub_0014FA80;
    case 0x0014fab0u:return sub_0014FAB0;
    case 0x0014fae0u:return sub_0014FAE0;
    case 0x0014fb60u:return sub_0014FB60;
    case 0x0014fcf0u:return sub_0014FCF0;
    case 0x0014fd20u:return sub_0014FD20;
    case 0x0014fd50u:return sub_0014FD50;
    case 0x0014fd80u:return sub_0014FD80;
    case 0x00153090u:return sub_00153090;
    case 0x001530c0u:return sub_001530C0;
    case 0x001530f0u:return sub_001530F0;
    case 0x00153120u:return sub_00153120;
    case 0x001531a0u:return sub_001531A0;
    case 0x00158c70u:return sub_00158C70;
    case 0x00158ca0u:return sub_00158CA0;
    case 0x00158cd0u:return sub_00158CD0;
    case 0x00158d00u:return sub_00158D00;
    case 0x00158d30u:return sub_00158D30;
    case 0x00158d60u:return sub_00158D60;
    case 0x0015aef0u:return sub_0015AEF0;
    case 0x0015af70u:return sub_0015AF70;
    case 0x0015aff0u:return sub_0015AFF0;
    case 0x0015b070u:return sub_0015B070;
    case 0x00184be0u:return sub_00184BE0;
    case 0x001aa820u:return sub_001AA820;
    case 0x001bd420u:return sub_001BD420;
    case 0x001d6c90u:return sub_001D6C90;
    case 0x001dda00u:return sub_001DDA00;
    case 0x002805f0u:return sub_002805F0;
    case 0x0028bda0u:return sub_0028BDA0;
    case 0x0029d380u:return sub_0029D380;
    case 0x002a9770u:return sub_002A9770;
    case 0x0031e3d0u:return sub_0031E3D0;
    case 0x000577e0u:return sub_000577E0;
    case 0x00125450u:return sub_00125450;
    case 0x00126130u:return sub_00126130;
    case 0x00126be0u:return sub_00126BE0;
    case 0x0014a310u:return sub_0014A310;
    case 0x001aa9e0u:return sub_001AA9E0;
    case 0x001b8e00u:return sub_001B8E00;
    case 0x001bae50u:return sub_001BAE50;
    case 0x001bb730u:return sub_001BB730;
    case 0x001bd4c0u:return sub_001BD4C0;
    case 0x001c1c90u:return sub_001C1C90;
    case 0x001c1d70u:return sub_001C1D70;
    case 0x00210e50u:return sub_00210E50;
    case 0x002127b0u:return sub_002127B0;
    case 0x00212870u:return sub_00212870;
    case 0x00212910u:return sub_00212910;
    case 0x0021a920u:return sub_0021A920;
    case 0x0021aa30u:return sub_0021AA30;
    case 0x0022f080u:return sub_0022F080;
    case 0x00275f00u:return sub_00275F00;
    case 0x0028ada0u:return sub_0028ADA0;
    case 0x00023d11u:return stop_sub_00023D11;
    case 0x00023d1fu:return stop_sub_00023D1F;
    case 0x00076a70u:return sub_00076A70;
    case 0x000e5cb0u:return sub_000E5CB0;
    case 0x00112940u:return sub_00112940;
    case 0x0012a720u:return sub_0012A720;
    case 0x00143903u:return stop_sub_00143903;
    case 0x0028a6fau:return stop_sub_0028A6FA;
    case 0x003a9207u:return stop_sub_003A9207;
    case 0x003a920au:return stop_sub_003A920A;
    case 0x003a9221u:return stop_sub_003A9221;
    case 0x003a9244u:return stop_sub_003A9244;
    case 0x3d025672u:return stop_sub_3D025672;
    case 0xf822e348u:return stop_sub_F822E348;
    default:return obiwan_mega_lookup(va);
    }
}

void recomp_icall_fail_log(uint32_t va) { unresolved(va); }

/* Keep generator diagnostics visible during bring-up. Invalid indirect calls
 * are logged and skipped by the generated guarded-call path; untranslated
 * instructions remain no-ops unless they corrupt state and fail downstream. */
void recomp_icall_not_code_log(uint32_t va) {
    fprintf(stderr, "[ICALL] target 0x%08x is not translated code\n", va);
    fflush(stderr);
}

void recomp_unimpl(const char *text, uint32_t va) {
    fprintf(stderr, "[UNIMPL] untranslated instruction at 0x%08x: %s\n",
            va, text ? text : "(unknown)");
    fflush(stderr);
}
