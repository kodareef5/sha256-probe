/*
 * n32_kernel_finder.c — Find valid M[0] candidates for non-MSB kernels at N=32
 *
 * For each kernel bit: scan M[0] values until da56=0.
 * At N=32, this may need up to 2^32 candidates per kernel bit.
 * Uses OpenMP for parallel scanning.
 *
 * Usage: ./n32_kernel_finder [kernel_bit] [max_scan]
 * Default: test bits 10, 17, 19, 31 with 2^28 scan each
 *
 * Compile: gcc -O3 -march=native -Xclang -fopenmp \
 *          -I/opt/homebrew/opt/libomp/include \
 *          -L/opt/homebrew/opt/libomp/lib -lomp \
 *          -o n32_kernel_finder n32_kernel_finder.c -lm
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <omp.h>

#define N 32
#define MASK 0xFFFFFFFFU

static inline uint32_t ror32(uint32_t x, int k) {
    return (x >> k) | (x << (32 - k));
}
static inline uint32_t Sigma0(uint32_t a) { return ror32(a,2)^ror32(a,13)^ror32(a,22); }
static inline uint32_t Sigma1(uint32_t e) { return ror32(e,6)^ror32(e,11)^ror32(e,25); }
static inline uint32_t sigma0(uint32_t x) { return ror32(x,7)^ror32(x,18)^(x>>3); }
static inline uint32_t sigma1(uint32_t x) { return ror32(x,17)^ror32(x,19)^(x>>10); }
static inline uint32_t Ch(uint32_t e,uint32_t f,uint32_t g) { return (e&f)^(~e&g); }
static inline uint32_t Maj(uint32_t a,uint32_t b,uint32_t c) { return (a&b)^(a&c)^(b&c); }

static const uint32_t K[64] = {
    0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
    0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
    0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
    0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
    0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
    0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
    0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
    0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
static const uint32_t IV[8] = {
    0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,
    0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};

static uint32_t compress_get_a56(const uint32_t M[16]) {
    uint32_t W[57];
    for (int i=0;i<16;i++) W[i]=M[i];
    for (int i=16;i<57;i++) W[i]=sigma1(W[i-2])+W[i-7]+sigma0(W[i-15])+W[i-16];
    uint32_t a=IV[0],b=IV[1],c=IV[2],d=IV[3],e=IV[4],f=IV[5],g=IV[6],h=IV[7];
    for (int i=0;i<57;i++) {
        uint32_t T1=h+Sigma1(e)+Ch(e,f,g)+K[i]+W[i];
        uint32_t T2=Sigma0(a)+Maj(a,b,c);
        h=g;g=f;f=e;e=d+T1;d=c;c=b;b=a;a=T1+T2;
    }
    return a; /* a register after round 56 */
}

int main(int argc, char **argv) {
    setbuf(stdout, NULL);
    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);

    int target_kbit = (argc > 1) ? atoi(argv[1]) : -1;
    uint64_t max_scan = (argc > 2) ? strtoull(argv[2], NULL, 0) : (1ULL << 28);
    uint32_t fill = MASK;

    int kbits[] = {10, 17, 19, 31};
    int n_kbits = 4;
    if (target_kbit >= 0) {
        kbits[0] = target_kbit;
        n_kbits = 1;
    }

    printf("=== N=32 Kernel Candidate Finder ===\n");
    printf("Fill: 0x%08x, Max scan: %llu per kernel bit\n", fill, (unsigned long long)max_scan);
    printf("Threads: %d\n\n", omp_get_max_threads());

    for (int ki = 0; ki < n_kbits; ki++) {
        int kbit = kbits[ki];
        uint32_t delta = 1U << kbit;
        printf("Kernel bit %d (delta=0x%08x):\n", kbit, delta);

        volatile int found = 0;
        uint32_t found_m0 = 0;

        #pragma omp parallel for schedule(dynamic, 1024)
        for (uint64_t m0 = 0; m0 < max_scan; m0++) {
            if (found) continue;

            uint32_t M1[16], M2[16];
            for (int i=0;i<16;i++) { M1[i]=fill; M2[i]=fill; }
            M1[0] = (uint32_t)m0;
            M2[0] = (uint32_t)m0 ^ delta;
            M2[9] = fill ^ delta;

            uint32_t a1 = compress_get_a56(M1);
            uint32_t a2 = compress_get_a56(M2);

            if (a1 == a2) {
                #pragma omp critical
                {
                    if (!found) {
                        found = 1;
                        found_m0 = (uint32_t)m0;
                        printf("  FOUND: M[0]=0x%08x (da56=0) at scan #%llu\n",
                               found_m0, (unsigned long long)m0);
                    }
                }
            }

            if (m0 > 0 && (m0 & 0xFFFFFFF) == 0 && !found) {
                clock_gettime(CLOCK_MONOTONIC, &t1);
                double el = (t1.tv_sec-t0.tv_sec)+(t1.tv_nsec-t0.tv_nsec)/1e9;
                printf("  [%llu/%llu] %.1fs\n", (unsigned long long)m0,
                       (unsigned long long)max_scan, el);
            }
        }

        if (!found) {
            printf("  NOT FOUND in %llu candidates\n", (unsigned long long)max_scan);
        }
        printf("\n");
    }

    clock_gettime(CLOCK_MONOTONIC, &t1);
    double total = (t1.tv_sec-t0.tv_sec)+(t1.tv_nsec-t0.tv_nsec)/1e9;
    printf("Total time: %.1fs\n", total);
    return 0;
}
