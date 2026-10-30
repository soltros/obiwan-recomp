#define _GNU_SOURCE
#include <errno.h>
#include <limits.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ucontext.h>
#include <execinfo.h>
#include <unistd.h>
#include <openssl/evp.h>
#include "kernel.h"
#include "xbox_memory_layout.h"
#include "video_player.h"
#include "recomp_types.h"

#define ENTRY 0x0002B180u
#define XBE_SIZE 4710400u
#define XBE_SHA256 "3511048a815085f78a8f1c298355b0c887a9d1040e211f888f39376cf101da53"
static void *image;
static size_t image_size;
static char game_dir[PATH_MAX],save_dir[PATH_MAX];
static int init_only;
extern void xbox_path_init(const char *,const char *);
extern void nv2a_pb_set_semaphore_target(uint32_t guest_va);
extern void xbox_OhciInit(void);
extern int xbox_Nv2aMirrorCounter(uint32_t device_ptr_va,
                                  uint32_t src_off, uint32_t dst_off);

/* write() and _exit() keep the fatal path independent of stdio locks/allocators. */
static void fault_hex(const char *label, size_t len, uint64_t value) {
    char digits[17]; const char *hex="0123456789abcdef";
    for(int i=0;i<16;i++)digits[i]=hex[(value >> (60-4*i))&15];digits[16]='\n';
    (void)write(STDERR_FILENO,label,len);(void)write(STDERR_FILENO,digits,sizeof digits);
}
static void fault(int sig,siginfo_t *info,void *ctx) {
    void *frames[24];
    int frame_count;
    if(xbox_PosixMmioFault(ctx,(uintptr_t)info->si_addr))return;
    const char msg[]="[FATAL] host signal; guest execution stopped\n";
    (void)write(STDERR_FILENO,msg,sizeof(msg)-1);
    fault_hex("fault_address=0x",16,(uintptr_t)info->si_addr);
    ucontext_t *uc=ctx;
    fault_hex("host_pc=0x",10,(uint64_t)uc->uc_mcontext.gregs[REG_RIP]);
    fault_hex("guest_esp=0x",12,g_esp);
    fault_hex("guest_eax=0x",12,g_eax);
    frame_count = backtrace(frames, (int)(sizeof frames / sizeof frames[0]));
    (void)write(STDERR_FILENO, "native_backtrace:\n", 18);
    backtrace_symbols_fd(frames, frame_count, STDERR_FILENO);
    _exit(128+sig);
}
static int install_handlers(void) {
    struct sigaction sa={0};sa.sa_sigaction=fault;sa.sa_flags=SA_SIGINFO;sigemptyset(&sa.sa_mask);
    return sigaction(SIGSEGV,&sa,NULL)==0 && sigaction(SIGBUS,&sa,NULL)==0;
}
static int load_and_check(void) {
    char path[PATH_MAX];
    if(snprintf(path,sizeof path,"%s/default.xbe",game_dir)>=(int)sizeof path)return 0;
    FILE *f=fopen(path,"rb");if(!f){perror(path);return 0;}
    if(fseek(f,0,SEEK_END)!=0){fclose(f);return 0;}
    long length=ftell(f);
    if(length!=(long)XBE_SIZE || fseek(f,0,SEEK_SET)!=0){fprintf(stderr,"Unsupported XBE size\n");fclose(f);return 0;}
    image_size=(size_t)length;image=malloc(image_size);
    if(!image){fclose(f);return 0;}
    size_t got=fread(image,1,image_size,f);fclose(f);if(got!=image_size)return 0;
    unsigned char md[EVP_MAX_MD_SIZE];unsigned int count=0;char text[65];
    if(!EVP_Digest(image,image_size,md,&count,EVP_sha256(),NULL) || count!=32)return 0;
    for(unsigned i=0;i<32;i++)snprintf(text+2*i,3,"%02x",md[i]);
    if(strcmp(text,XBE_SHA256)){fprintf(stderr,"Unsupported XBE SHA-256: %s\n",text);return 0;}
    fprintf(stderr,"[BOOT] exact Obi-Wan XBE verified (%zu bytes)\n",image_size);return 1;
}
static int guest_main(void) {
    if(!xbox_MemoryLayoutInit(image,image_size)){fprintf(stderr,"[BOOT] memory initialization failed\n");return 3;}
    fprintf(stderr,"[BOOT] memory layout initialized\n");
    /* D3D device 0x003770A0 points its GPU-read sequence word at this guest
     * address (device+0x3F0 -> 0x8001D000). Its make-space path waits for
     * BACK_END_WRITE_SEMAPHORE_RELEASE to advance this word. */
    nv2a_pb_set_semaphore_target(0x8001D000u);
    xbox_kernel_init();xbox_path_init(game_dir,save_dir);xbox_kernel_bridge_init();
    /* D3D's two-entry swap throttle compares submitted (+0x2B60) against
     * GPU-completed (+0x2518) on the device pointer at 0x00379C30. The
     * software executor consumes commands synchronously, so mirror that
     * completion field rather than letting the title wait for a GPU write
     * that this host does not produce. */
    if (xbox_Nv2aMirrorCounter(0x00379C30u, 0x2B60u, 0x2518u) != 0)
        fprintf(stderr, "[BOOT] could not register D3D completion counter\n");
    /* Bring up the optional Xbox USB controller model after guest memory,
     * kernel bridges, and fault handlers are ready. */
    xbox_OhciInit();
    g_esp=XBOX_STACK_TOP;
    if(!recomp_dispatch_init())fprintf(stderr,"[BOOT] flat dispatch unavailable; using binary search\n");
    recomp_func_t entry=recomp_lookup(ENTRY);
    if(!entry){fprintf(stderr,"[BOOT] missing generated entry 0x%08x\n",ENTRY);return 4;}
    fprintf(stderr,"[BOOT] runtime initialized; entry=0x%08x esp=0x%08x\n",ENTRY,g_esp);
    if(init_only){xbox_kernel_shutdown();xbox_MemoryLayoutShutdown();return 0;}
    if (getenv("RECOMP_OBIWAN_D3D_SOFT_COMPLETE") &&
        !strcmp(getenv("RECOMP_OBIWAN_D3D_SOFT_COMPLETE"), "1")) {
        volatile uint32_t *complete = (volatile uint32_t *)(uintptr_t)
                (0x00379C60u + xbox_GetMemoryOffset());
        *complete = 1;
        fprintf(stderr, "[DIAGNOSTIC] software D3D queue completion enabled\n");
    }
    xbox_WatchdogStart();
    fprintf(stderr,"[BOOT] entering recompiled game\n");entry();
    fprintf(stderr,"[BOOT] entry returned; stopping diagnostic process\n");
    /* Xbox startup may create worker threads. Do not unmap their memory while alive. */
    fflush(NULL);_exit(0);
}
int main(int argc,char **argv) {
    setvbuf(stderr,NULL,_IONBF,0);
    if(argc<3 || argc>4 || (argc==4 && strcmp(argv[3],"--check-input") && strcmp(argv[3],"--init-only"))){
        fprintf(stderr,"Usage: %s GAME_DIRECTORY SAVE_DIRECTORY [--check-input|--init-only]\n",argv[0]);return 2;}
    if(!realpath(argv[1],game_dir)){perror("game directory");return 2;}
    /* Require an explicit, existing save root; do not default to HOME during bring-up. */
    if(!realpath(argv[2],save_dir)){perror("save directory");return 2;}
    /* Upstream path storage is MAX_PATH-sized; leave room for its subdirectories. */
    if(strlen(game_dir)>180 || strlen(save_dir)>180){fprintf(stderr,"Runtime paths too long\n");return 2;}
    if(!strcmp(game_dir,save_dir)){fprintf(stderr,"Game and save directories must differ\n");return 2;}
    if(!load_and_check()){free(image);return 2;}
    if(argc==4 && !strcmp(argv[3],"--check-input")){free(image);return 0;}
    init_only=argc==4;
    if(!install_handlers()){perror("sigaction");free(image);return 3;}
    int result=init_only ? guest_main() : xbox_HostWindowMain(guest_main);
    free(image);return result;
}
