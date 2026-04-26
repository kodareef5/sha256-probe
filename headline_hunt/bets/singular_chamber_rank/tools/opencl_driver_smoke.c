#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

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
#define CL_PLATFORM_NAME 0x0902
#define CL_DEVICE_NAME 0x102B
#define CL_PROGRAM_BUILD_LOG 0x1183

static void *sym(void *lib, const char *name) {
    void *p = dlsym(lib, name);
    if (!p) {
        fprintf(stderr, "missing OpenCL symbol: %s\n", name);
        exit(1);
    }
    return p;
}

int main(void) {
    void *lib = dlopen("libOpenCL.so.1", RTLD_NOW);
    if (!lib) {
        fprintf(stderr, "dlopen libOpenCL.so.1 failed: %s\n", dlerror());
        return 1;
    }

    cl_int (*clGetPlatformIDs)(cl_uint, cl_platform_id *, cl_uint *) = sym(lib, "clGetPlatformIDs");
    cl_int (*clGetPlatformInfo)(cl_platform_id, cl_uint, size_t, void *, size_t *) = sym(lib, "clGetPlatformInfo");
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

    cl_int err;
    cl_platform_id platforms[8];
    cl_uint nplatforms = 0;
    err = clGetPlatformIDs(8, platforms, &nplatforms);
    if (err != CL_SUCCESS || nplatforms == 0) {
        fprintf(stderr, "clGetPlatformIDs failed: %d platforms=%u\n", err, nplatforms);
        return 1;
    }

    cl_platform_id platform = platforms[0];
    cl_device_id device = NULL;
    for (cl_uint i = 0; i < nplatforms; i++) {
        cl_device_id dev;
        err = clGetDeviceIDs(platforms[i], CL_DEVICE_TYPE_GPU, 1, &dev, NULL);
        if (err == CL_SUCCESS) {
            platform = platforms[i];
            device = dev;
            break;
        }
    }
    if (!device) {
        fprintf(stderr, "no OpenCL GPU device found\n");
        return 1;
    }

    char pname[256] = {0};
    char dname[256] = {0};
    clGetPlatformInfo(platform, CL_PLATFORM_NAME, sizeof(pname), pname, NULL);
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

    const char *src =
        "__kernel void smoke(__global uint *out) {\n"
        "  uint i = get_global_id(0);\n"
        "  out[i] = i ^ 0xa5a51234u;\n"
        "}\n";
    cl_program prog = clCreateProgramWithSource(ctx, 1, &src, NULL, &err);
    if (err != CL_SUCCESS) {
        fprintf(stderr, "clCreateProgramWithSource failed: %d\n", err);
        return 1;
    }
    err = clBuildProgram(prog, 1, &device, "", NULL, NULL);
    if (err != CL_SUCCESS) {
        char log[4096] = {0};
        clGetProgramBuildInfo(prog, device, CL_PROGRAM_BUILD_LOG,
                              sizeof(log), log, NULL);
        fprintf(stderr, "clBuildProgram failed: %d\n%s\n", err, log);
        return 1;
    }
    cl_kernel k = clCreateKernel(prog, "smoke", &err);
    if (err != CL_SUCCESS) {
        fprintf(stderr, "clCreateKernel failed: %d\n", err);
        return 1;
    }
    uint32_t out[256];
    cl_mem buf = clCreateBuffer(ctx, CL_MEM_WRITE_ONLY, sizeof(out), NULL, &err);
    if (err != CL_SUCCESS) {
        fprintf(stderr, "clCreateBuffer failed: %d\n", err);
        return 1;
    }
    clSetKernelArg(k, 0, sizeof(buf), &buf);
    size_t global = 256;
    err = clEnqueueNDRangeKernel(q, k, 1, NULL, &global, NULL, 0, NULL, NULL);
    if (err != CL_SUCCESS) {
        fprintf(stderr, "clEnqueueNDRangeKernel failed: %d\n", err);
        return 1;
    }
    clFinish(q);
    err = clEnqueueReadBuffer(q, buf, CL_TRUE, 0, sizeof(out), out, 0, NULL, NULL);
    if (err != CL_SUCCESS) {
        fprintf(stderr, "clEnqueueReadBuffer failed: %d\n", err);
        return 1;
    }

    int ok = 1;
    for (uint32_t i = 0; i < 256; i++) {
        if (out[i] != (i ^ 0xa5a51234U)) ok = 0;
    }
    printf("{\"opencl_smoke\":\"%s\",\"platform\":\"%s\",\"device\":\"%s\","
           "\"first\":\"0x%08x\",\"last\":\"0x%08x\"}\n",
           ok ? "ok" : "bad", pname, dname, out[0], out[255]);

    clReleaseMemObject(buf);
    clReleaseKernel(k);
    clReleaseProgram(prog);
    clReleaseCommandQueue(q);
    clReleaseContext(ctx);
    return ok ? 0 : 1;
}
