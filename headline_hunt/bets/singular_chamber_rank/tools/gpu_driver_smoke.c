#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

typedef int CUresult;
typedef int CUdevice;
typedef void *CUcontext;
typedef void *CUmodule;
typedef void *CUfunction;
typedef uint64_t CUdeviceptr;

#define CUDA_SUCCESS 0

static void die_cuda(const char *what, CUresult r) {
    fprintf(stderr, "%s failed: %d\n", what, r);
    exit(1);
}

static void *sym(void *lib, const char *name) {
    void *p = dlsym(lib, name);
    if (!p) {
        fprintf(stderr, "missing CUDA symbol: %s\n", name);
        exit(1);
    }
    return p;
}

int main(void) {
    void *lib = dlopen("libcuda.so.1", RTLD_NOW);
    if (!lib) {
        fprintf(stderr, "dlopen libcuda.so.1 failed: %s\n", dlerror());
        return 1;
    }

    CUresult (*cuInit)(unsigned int) = sym(lib, "cuInit");
    CUresult (*cuDeviceGet)(CUdevice *, int) = sym(lib, "cuDeviceGet");
    CUresult (*cuCtxCreate)(CUcontext *, unsigned int, CUdevice) = sym(lib, "cuCtxCreate_v2");
    CUresult (*cuModuleLoadData)(CUmodule *, const void *) = sym(lib, "cuModuleLoadData");
    CUresult (*cuModuleLoadDataEx)(CUmodule *, const void *, unsigned int, void *, void **) =
        sym(lib, "cuModuleLoadDataEx");
    CUresult (*cuModuleGetFunction)(CUfunction *, CUmodule, const char *) = sym(lib, "cuModuleGetFunction");
    CUresult (*cuMemAlloc)(CUdeviceptr *, size_t) = sym(lib, "cuMemAlloc_v2");
    CUresult (*cuMemcpyDtoH)(void *, CUdeviceptr, size_t) = sym(lib, "cuMemcpyDtoH_v2");
    CUresult (*cuLaunchKernel)(CUfunction, unsigned int, unsigned int, unsigned int,
                               unsigned int, unsigned int, unsigned int,
                               unsigned int, void *, void **, void **) = sym(lib, "cuLaunchKernel");
    CUresult (*cuCtxSynchronize)(void) = sym(lib, "cuCtxSynchronize");
    CUresult (*cuMemFree)(CUdeviceptr) = sym(lib, "cuMemFree_v2");

    const char *ptx =
        ".version 7.0\n"
        ".target sm_70\n"
        ".address_size 64\n"
        ".visible .entry smoke(.param .u64 outp) {\n"
        "  .reg .u64 %out, %addr;\n"
        "  .reg .u32 %r_tid, %r_ctaid, %r_ntid, %i, %v;\n"
        "  ld.param.u64 %out, [outp];\n"
        "  mov.u32 %r_tid, %tid.x;\n"
        "  mov.u32 %r_ctaid, %ctaid.x;\n"
        "  mov.u32 %r_ntid, %ntid.x;\n"
        "  mad.lo.u32 %i, %r_ctaid, %r_ntid, %r_tid;\n"
        "  mul.wide.u32 %addr, %i, 4;\n"
        "  add.u64 %addr, %out, %addr;\n"
        "  xor.b32 %v, %i, 0x5a5a1234;\n"
        "  st.global.u32 [%addr], %v;\n"
        "  ret;\n"
        "}\n";

    CUresult r;
    CUdevice dev;
    CUcontext ctx;
    CUmodule mod;
    CUfunction fn;
    CUdeviceptr d_out;
    uint32_t out[256];

    r = cuInit(0);
    if (r != CUDA_SUCCESS) die_cuda("cuInit", r);
    r = cuDeviceGet(&dev, 0);
    if (r != CUDA_SUCCESS) die_cuda("cuDeviceGet", r);
    r = cuCtxCreate(&ctx, 0, dev);
    if (r != CUDA_SUCCESS) die_cuda("cuCtxCreate", r);
    char err_log[4096] = {0};
    char info_log[4096] = {0};
    unsigned int options[] = {3, 4, 5, 6};
    void *option_values[] = {
        info_log,
        (void *)(uintptr_t)sizeof(info_log),
        err_log,
        (void *)(uintptr_t)sizeof(err_log)
    };
    r = cuModuleLoadDataEx(&mod, ptx, 4, options, option_values);
    if (r != CUDA_SUCCESS) {
        fprintf(stderr, "cuModuleLoadDataEx failed: %d\ninfo: %s\nerror: %s\n",
                r, info_log, err_log);
        return 1;
    }
    r = cuModuleGetFunction(&fn, mod, "smoke");
    if (r != CUDA_SUCCESS) die_cuda("cuModuleGetFunction", r);
    r = cuMemAlloc(&d_out, sizeof(out));
    if (r != CUDA_SUCCESS) die_cuda("cuMemAlloc", r);

    void *args[] = {&d_out};
    r = cuLaunchKernel(fn, 1, 1, 1, 256, 1, 1, 0, NULL, args, NULL);
    if (r != CUDA_SUCCESS) die_cuda("cuLaunchKernel", r);
    r = cuCtxSynchronize();
    if (r != CUDA_SUCCESS) die_cuda("cuCtxSynchronize", r);
    r = cuMemcpyDtoH(out, d_out, sizeof(out));
    if (r != CUDA_SUCCESS) die_cuda("cuMemcpyDtoH", r);
    cuMemFree(d_out);

    uint32_t ok = 1;
    for (uint32_t i = 0; i < 256; i++) {
        if (out[i] != (i ^ 0x5a5a1234U)) ok = 0;
    }
    printf("{\"gpu_smoke\":\"%s\",\"first\":\"0x%08x\",\"last\":\"0x%08x\"}\n",
           ok ? "ok" : "bad", out[0], out[255]);
    return ok ? 0 : 1;
}
