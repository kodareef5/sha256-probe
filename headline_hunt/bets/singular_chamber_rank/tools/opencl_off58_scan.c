#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "lib/sha256.h"

typedef int32_t cl_int;
typedef uint32_t cl_uint;
typedef uint64_t cl_ulong;
typedef uintptr_t cl_device_type;
typedef uintptr_t cl_mem_flags;
typedef uint32_t cl_bool;
typedef struct _cl_platform_id *cl_platform_id;
typedef struct _cl_device_id *cl_device_id;
typedef struct _cl_context *cl_context;
typedef struct _cl_command_queue *cl_command_queue;
typedef struct _cl_program *cl_program;
typedef struct _cl_kernel *cl_kernel;
typedef struct _cl_mem *cl_mem;

#define CL_SUCCESS 0
#define CL_TRUE 1
#define CL_DEVICE_TYPE_GPU (1UL << 2)
#define CL_MEM_WRITE_ONLY (1UL << 1)
#define CL_MEM_READ_ONLY (1UL << 2)
#define CL_MEM_COPY_HOST_PTR (1UL << 5)
#define CL_PLATFORM_NAME 0x0902
#define CL_DEVICE_NAME 0x102B
#define CL_PROGRAM_BUILD_LOG 0x1183

typedef struct {
    const char *id;
    uint32_t m0;
    uint32_t fill;
    int bit;
} candidate_t;

static const candidate_t CANDIDATES[] = {
    {"msb_cert_m17149975_ff_bit31", 0x17149975U, 0xffffffffU, 31},
    {"bit19_m51ca0b34_55",         0x51ca0b34U, 0x55555555U, 19},
    {"msb_m9cfea9ce_00",           0x9cfea9ceU, 0x00000000U, 31},
    {"bit20_m294e1ea8_ff",         0x294e1ea8U, 0xffffffffU, 20},
    {"bit28_md1acca79_ff",         0xd1acca79U, 0xffffffffU, 28},
    {"bit28_m3e57289c_ff",         0x3e57289cU, 0xffffffffU, 28},
    {"bit18_m99bf552b_ff",         0x99bf552bU, 0xffffffffU, 18},
    {"bit18_mcbe11dc1_ff",         0xcbe11dc1U, 0xffffffffU, 18},
    {"bit3_m33ec77ca_ff",          0x33ec77caU, 0xffffffffU, 3},
    {"bit3_m5fa301aa_ff",          0x5fa301aaU, 0xffffffffU, 3},
    {"bit1_m6fbc8d8e_ff",          0x6fbc8d8eU, 0xffffffffU, 1},
    {"bit14_m67043cdd_ff",         0x67043cddU, 0xffffffffU, 14},
    {"bit14_mb5541a6e_ff",         0xb5541a6eU, 0xffffffffU, 14},
    {"bit14_m40fde4d2_ff",         0x40fde4d2U, 0xffffffffU, 14},
    {"bit25_ma2f498b1_ff",         0xa2f498b1U, 0xffffffffU, 25},
    {"bit4_m39a03c2d_ff",          0x39a03c2dU, 0xffffffffU, 4},
    {"bit29_m17454e4b_ff",         0x17454e4bU, 0xffffffffU, 29},
    {"bit15_m28c09a5a_ff",         0x28c09a5aU, 0xffffffffU, 15},
};

static int hw32(uint32_t x) {
    return __builtin_popcount(x);
}

static int prepare_candidate(const candidate_t *cand,
                             sha256_precomp_t *p1,
                             sha256_precomp_t *p2) {
    uint32_t M1[16], M2[16];
    uint32_t diff = 1U << cand->bit;
    for (int i = 0; i < 16; i++) {
        M1[i] = cand->fill;
        M2[i] = cand->fill;
    }
    M1[0] = cand->m0;
    M2[0] = cand->m0 ^ diff;
    M2[9] = cand->fill ^ diff;
    sha256_precompute(M1, p1);
    sha256_precompute(M2, p2);
    return p1->state[0] == p2->state[0];
}

static void *sym(void *lib, const char *name) {
    void *p = dlsym(lib, name);
    if (!p) {
        fprintf(stderr, "missing OpenCL symbol: %s\n", name);
        exit(1);
    }
    return p;
}

static const char *KERNEL_SRC =
"uint ror32(uint x, uint k) { return (x >> k) | (x << (32u - k)); }\n"
"uint S0(uint a) { return ror32(a,2u) ^ ror32(a,13u) ^ ror32(a,22u); }\n"
"uint S1(uint e) { return ror32(e,6u) ^ ror32(e,11u) ^ ror32(e,25u); }\n"
"uint Ch(uint e, uint f, uint g) { return (e & f) ^ ((~e) & g); }\n"
"uint Maj(uint a, uint b, uint c) { return (a & b) ^ (a & c) ^ (b & c); }\n"
"uint cascade(__private uint s1[8], __private uint s2[8]) {\n"
"  uint dh = s1[7] - s2[7];\n"
"  uint dSig1 = S1(s1[4]) - S1(s2[4]);\n"
"  uint dCh = Ch(s1[4], s1[5], s1[6]) - Ch(s2[4], s2[5], s2[6]);\n"
"  uint dT2 = (S0(s1[0]) + Maj(s1[0], s1[1], s1[2])) -\n"
"             (S0(s2[0]) + Maj(s2[0], s2[1], s2[2]));\n"
"  return dh + dSig1 + dCh + dT2;\n"
"}\n"
"void round57(__private uint s[8], uint w, uint k57) {\n"
"  uint a=s[0], b=s[1], c=s[2], d=s[3], e=s[4], f=s[5], g=s[6], h=s[7];\n"
"  uint T1 = h + S1(e) + Ch(e,f,g) + k57 + w;\n"
"  uint T2 = S0(a) + Maj(a,b,c);\n"
"  s[7]=g; s[6]=f; s[5]=e; s[4]=d+T1; s[3]=c; s[2]=b; s[1]=a; s[0]=T1+T2;\n"
"}\n"
"uint splitmix32(ulong *state) {\n"
"  ulong z = (*state += 0x9e3779b97f4a7c15UL);\n"
"  z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9UL;\n"
"  z = (z ^ (z >> 27)) * 0x94d049bb133111ebUL;\n"
"  z ^= z >> 31;\n"
"  return (uint)z;\n"
"}\n"
"__kernel void off58_scan(__global const uint *state1, __global const uint *state2,\n"
"                         uint k57, ulong seed, ulong samples,\n"
"                         __global uint *out_w57, __global uint *out_off58) {\n"
"  ulong gid = get_global_id(0);\n"
"  if (gid >= samples) return;\n"
"  ulong st = seed ^ (gid * 0xd1342543de82ef95UL);\n"
"  uint w57 = splitmix32(&st);\n"
"  uint s1[8]; uint s2[8];\n"
"  for (int i = 0; i < 8; i++) { s1[i] = state1[i]; s2[i] = state2[i]; }\n"
"  uint off57 = cascade(s1, s2);\n"
"  round57(s1, w57, k57);\n"
"  round57(s2, w57 + off57, k57);\n"
"  out_w57[gid] = w57;\n"
"  out_off58[gid] = cascade(s1, s2);\n"
"}\n";

int main(int argc, char **argv) {
    int idx = (argc >= 2) ? atoi(argv[1]) : 8;
    size_t samples = (argc >= 3) ? strtoull(argv[2], NULL, 0) : 1048576ULL;
    uint64_t seed = (argc >= 4) ? strtoull(argv[3], NULL, 0) : 0x0ff58123456789abULL;
    int n_cands = (int)(sizeof(CANDIDATES) / sizeof(CANDIDATES[0]));
    if (idx < 0 || idx >= n_cands) {
        fprintf(stderr, "candidate index must be 0..%d.\n", n_cands - 1);
        return 2;
    }

    sha256_init(32);
    sha256_precomp_t p1, p2;
    const candidate_t *cand = &CANDIDATES[idx];
    if (!prepare_candidate(cand, &p1, &p2)) {
        printf("{\"mode\":\"opencl_off58_scan\",\"candidate\":\"%s\",\"error\":\"not_cascade_eligible\"}\n",
               cand->id);
        return 0;
    }

    void *lib = dlopen("libOpenCL.so.1", RTLD_NOW);
    if (!lib) {
        fprintf(stderr, "dlopen libOpenCL.so.1 failed: %s\n", dlerror());
        return 1;
    }

    cl_int (*clGetPlatformIDs)(cl_uint, cl_platform_id *, cl_uint *) = sym(lib, "clGetPlatformIDs");
    cl_int (*clGetDeviceIDs)(cl_platform_id, cl_device_type, cl_uint, cl_device_id *, cl_uint *) = sym(lib, "clGetDeviceIDs");
    cl_int (*clGetDeviceInfo)(cl_device_id, cl_uint, size_t, void *, size_t *) = sym(lib, "clGetDeviceInfo");
    cl_context (*clCreateContext)(const void *, cl_uint, const cl_device_id *, void *, void *, cl_int *) = sym(lib, "clCreateContext");
    cl_command_queue (*clCreateCommandQueue)(cl_context, cl_device_id, cl_ulong, cl_int *) = sym(lib, "clCreateCommandQueue");
    cl_program (*clCreateProgramWithSource)(cl_context, cl_uint, const char **, const size_t *, cl_int *) = sym(lib, "clCreateProgramWithSource");
    cl_int (*clBuildProgram)(cl_program, cl_uint, const cl_device_id *, const char *, void *, void *) = sym(lib, "clBuildProgram");
    cl_int (*clGetProgramBuildInfo)(cl_program, cl_device_id, cl_uint, size_t, void *, size_t *) = sym(lib, "clGetProgramBuildInfo");
    cl_kernel (*clCreateKernel)(cl_program, const char *, cl_int *) = sym(lib, "clCreateKernel");
    cl_mem (*clCreateBuffer)(cl_context, cl_mem_flags, size_t, void *, cl_int *) = sym(lib, "clCreateBuffer");
    cl_int (*clSetKernelArg)(cl_kernel, cl_uint, size_t, const void *) = sym(lib, "clSetKernelArg");
    cl_int (*clEnqueueNDRangeKernel)(cl_command_queue, cl_kernel, cl_uint, const size_t *, const size_t *, const size_t *, cl_uint, const void *, void *) = sym(lib, "clEnqueueNDRangeKernel");
    cl_int (*clFinish)(cl_command_queue) = sym(lib, "clFinish");
    cl_int (*clEnqueueReadBuffer)(cl_command_queue, cl_mem, cl_bool, size_t, size_t, void *, cl_uint, const void *, void *) = sym(lib, "clEnqueueReadBuffer");
    cl_int (*clReleaseMemObject)(cl_mem) = sym(lib, "clReleaseMemObject");
    cl_int (*clReleaseKernel)(cl_kernel) = sym(lib, "clReleaseKernel");
    cl_int (*clReleaseProgram)(cl_program) = sym(lib, "clReleaseProgram");
    cl_int (*clReleaseCommandQueue)(cl_command_queue) = sym(lib, "clReleaseCommandQueue");
    cl_int (*clReleaseContext)(cl_context) = sym(lib, "clReleaseContext");

    cl_platform_id platforms[8];
    cl_uint nplatforms = 0;
    cl_int err = clGetPlatformIDs(8, platforms, &nplatforms);
    if (err != CL_SUCCESS || nplatforms == 0) {
        fprintf(stderr, "clGetPlatformIDs failed: %d platforms=%u\n", err, nplatforms);
        return 1;
    }
    cl_device_id device = NULL;
    for (cl_uint i = 0; i < nplatforms; i++) {
        cl_device_id dev;
        err = clGetDeviceIDs(platforms[i], CL_DEVICE_TYPE_GPU, 1, &dev, NULL);
        if (err == CL_SUCCESS) {
            device = dev;
            break;
        }
    }
    if (!device) {
        fprintf(stderr, "no OpenCL GPU device found\n");
        return 1;
    }
    char dname[256] = {0};
    clGetDeviceInfo(device, CL_DEVICE_NAME, sizeof(dname), dname, NULL);

    cl_context ctx = clCreateContext(NULL, 1, &device, NULL, NULL, &err);
    if (err != CL_SUCCESS) {
        fprintf(stderr, "clCreateContext failed: %d\n", err);
        return 1;
    }
    cl_command_queue q = clCreateCommandQueue(ctx, device, 0, &err);
    if (err != CL_SUCCESS) {
        fprintf(stderr, "clCreateCommandQueue failed: %d\n", err);
        return 1;
    }
    cl_program prog = clCreateProgramWithSource(ctx, 1, &KERNEL_SRC, NULL, &err);
    if (err != CL_SUCCESS) {
        fprintf(stderr, "clCreateProgramWithSource failed: %d\n", err);
        return 1;
    }
    err = clBuildProgram(prog, 1, &device, "", NULL, NULL);
    if (err != CL_SUCCESS) {
        char log[8192] = {0};
        clGetProgramBuildInfo(prog, device, CL_PROGRAM_BUILD_LOG,
                              sizeof(log), log, NULL);
        fprintf(stderr, "clBuildProgram failed: %d\n%s\n", err, log);
        return 1;
    }
    cl_kernel kernel = clCreateKernel(prog, "off58_scan", &err);
    if (err != CL_SUCCESS) {
        fprintf(stderr, "clCreateKernel failed: %d\n", err);
        return 1;
    }

    uint32_t *w57 = malloc(samples * sizeof(uint32_t));
    uint32_t *off58 = malloc(samples * sizeof(uint32_t));
    if (!w57 || !off58) {
        fprintf(stderr, "allocation failed for %zu samples\n", samples);
        return 1;
    }

    cl_mem d_state1 = clCreateBuffer(ctx, CL_MEM_READ_ONLY | CL_MEM_COPY_HOST_PTR,
                                     8 * sizeof(uint32_t), p1.state, &err);
    cl_mem d_state2 = clCreateBuffer(ctx, CL_MEM_READ_ONLY | CL_MEM_COPY_HOST_PTR,
                                     8 * sizeof(uint32_t), p2.state, &err);
    cl_mem d_w57 = clCreateBuffer(ctx, CL_MEM_WRITE_ONLY,
                                  samples * sizeof(uint32_t), NULL, &err);
    cl_mem d_off58 = clCreateBuffer(ctx, CL_MEM_WRITE_ONLY,
                                    samples * sizeof(uint32_t), NULL, &err);
    if (!d_state1 || !d_state2 || !d_w57 || !d_off58 || err != CL_SUCCESS) {
        fprintf(stderr, "clCreateBuffer failed: %d\n", err);
        return 1;
    }

    uint32_t k57 = sha256_K[57];
    cl_ulong cl_seed = seed;
    cl_ulong cl_samples = samples;
    clSetKernelArg(kernel, 0, sizeof(d_state1), &d_state1);
    clSetKernelArg(kernel, 1, sizeof(d_state2), &d_state2);
    clSetKernelArg(kernel, 2, sizeof(k57), &k57);
    clSetKernelArg(kernel, 3, sizeof(cl_seed), &cl_seed);
    clSetKernelArg(kernel, 4, sizeof(cl_samples), &cl_samples);
    clSetKernelArg(kernel, 5, sizeof(d_w57), &d_w57);
    clSetKernelArg(kernel, 6, sizeof(d_off58), &d_off58);

    size_t local = 256;
    size_t global = ((samples + local - 1) / local) * local;
    err = clEnqueueNDRangeKernel(q, kernel, 1, NULL, &global, &local, 0, NULL, NULL);
    if (err != CL_SUCCESS) {
        fprintf(stderr, "clEnqueueNDRangeKernel failed: %d\n", err);
        return 1;
    }
    clFinish(q);
    clEnqueueReadBuffer(q, d_w57, CL_TRUE, 0, samples * sizeof(uint32_t),
                        w57, 0, NULL, NULL);
    clEnqueueReadBuffer(q, d_off58, CL_TRUE, 0, samples * sizeof(uint32_t),
                        off58, 0, NULL, NULL);

    uint64_t hist[33] = {0};
    uint32_t best_w57 = 0, best_off58 = 0xffffffffU;
    int best_hw = 99;
    uint32_t best_w57_by_hw[33] = {0};
    uint32_t best_off58_by_hw[33];
    for (int h = 0; h <= 32; h++) best_off58_by_hw[h] = 0xffffffffU;
    for (size_t i = 0; i < samples; i++) {
        int h = hw32(off58[i]);
        hist[h]++;
        if (h < best_hw || (h == best_hw && off58[i] < best_off58)) {
            best_hw = h;
            best_w57 = w57[i];
            best_off58 = off58[i];
        }
        if (off58[i] < best_off58_by_hw[h]) {
            best_off58_by_hw[h] = off58[i];
            best_w57_by_hw[h] = w57[i];
        }
    }

    printf("{\"mode\":\"opencl_off58_scan\",\"candidate\":\"%s\",\"idx\":%d,"
           "\"device\":\"%s\",\"samples\":%zu,\"seed\":\"0x%016llx\","
           "\"best_hw\":%d,\"best_w57\":\"0x%08x\",\"best_off58\":\"0x%08x\","
           "\"hist\":[",
           cand->id, idx, dname, samples, (unsigned long long)seed,
           best_hw, best_w57, best_off58);
    for (int h = 0; h <= 32; h++) {
        if (h) printf(",");
        printf("%llu", (unsigned long long)hist[h]);
    }
    printf("],\"best_by_hw\":[");
    int printed = 0;
    for (int h = 0; h <= 8; h++) {
        if (best_off58_by_hw[h] == 0xffffffffU) continue;
        if (printed++) printf(",");
        printf("{\"hw\":%d,\"w57\":\"0x%08x\",\"off58\":\"0x%08x\"}",
               h, best_w57_by_hw[h], best_off58_by_hw[h]);
    }
    printf("]}\n");

    clReleaseMemObject(d_state1);
    clReleaseMemObject(d_state2);
    clReleaseMemObject(d_w57);
    clReleaseMemObject(d_off58);
    clReleaseKernel(kernel);
    clReleaseProgram(prog);
    clReleaseCommandQueue(q);
    clReleaseContext(ctx);
    free(w57);
    free(off58);
    return 0;
}
