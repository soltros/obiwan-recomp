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
    case 0x00023d11u:return stop_sub_00023D11;
    case 0x00023d1fu:return stop_sub_00023D1F;
    case 0x00076a70u:return stop_sub_00076A70;
    case 0x000e5cb0u:return stop_sub_000E5CB0;
    case 0x00112940u:return stop_sub_00112940;
    case 0x0012a720u:return stop_sub_0012A720;
    case 0x00143903u:return stop_sub_00143903;
    case 0x0028a6fau:return stop_sub_0028A6FA;
    case 0x003a9207u:return stop_sub_003A9207;
    case 0x003a920au:return stop_sub_003A920A;
    case 0x003a9221u:return stop_sub_003A9221;
    case 0x003a9244u:return stop_sub_003A9244;
    case 0x3d025672u:return stop_sub_3D025672;
    case 0xf822e348u:return stop_sub_F822E348;
    default:return NULL;
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
