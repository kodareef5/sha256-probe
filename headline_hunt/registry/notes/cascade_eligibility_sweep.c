/*
 * cascade_eligibility_sweep.c — full 2^32 m0 sweep for cascade-eligibility at
 * (0,9) word-pair, fixed bit position, fixed fill. N=32.
 *
 * Tests the Σ1/σ1 alignment hypothesis: are σ0-aligned bits (3, 7, 18) eligible?
 * If 0 eligible at 2^32 sweep → hypothesis strengthened.
 * If many eligible → hypothesis falsified.
 *
 * Compile:
 *   gcc -O3 -mcpu=apple-m4 -mtune=apple-m4 -Xclang -fopenmp \
 *       -I/opt/homebrew/opt/libomp/include -L/opt/homebrew/opt/libomp/lib -lomp \
 *       -o cascade_eligibility_sweep cascade_eligibility_sweep.c -lm
 *
 * Usage: ./cascade_eligibility_sweep BIT FILL_HEX
 *   e.g. ./cascade_eligibility_sweep 7  0xffffffff   (σ0 bit, full fill)
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <omp.h>

#define MASK 0xFFFFFFFFU

static inline uint32_t ror32(uint32_t x, int k) { return (x >> k) | (x << (32 - k)); }
static inline uint32_t Sigma0(uint32_t a){ return ror32(a,2)^ror32(a,13)^ror32(a,22); }
static inline uint32_t Sigma1(uint32_t e){ return ror32(e,6)^ror32(e,11)^ror32(e,25); }
static inline uint32_t sigma0(uint32_t x){ return ror32(x,7)^ror32(x,18)^(x>>3); }
static inline uint32_t sigma1(uint32_t x){ return ror32(x,17)^ror32(x,19)^(x>>10); }
static inline uint32_t Ch(uint32_t e,uint32_t f,uint32_t g){ return (e&f)^((~e)&g); }
static inline uint32_t Maj(uint32_t a,uint32_t b,uint32_t c){ return (a&b)^(a&c)^(b&c); }

static const uint32_t K[64] = {
    0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
    0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
    0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
    0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
    0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
    0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
    0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
    0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2
};
static const uint32_t IV[8] = {
    0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19
};

/* Returns a-register at slot 57 (after 57 rounds) for message M (16 32-bit words).
 * This matches lib.sha256.precompute_state which loops `for i in range(57)`. */
static uint32_t a_at_slot57(const uint32_t M[16]) {
    uint32_t W[57];
    for (int i = 0; i < 16; i++) W[i] = M[i];
    for (int i = 16; i < 57; i++)
        W[i] = sigma1(W[i-2]) + W[i-7] + sigma0(W[i-15]) + W[i-16];
    uint32_t a=IV[0], b=IV[1], c=IV[2], d=IV[3], e=IV[4], f=IV[5], g=IV[6], h=IV[7];
    for (int i = 0; i < 57; i++) {
        uint32_t T1 = h + Sigma1(e) + Ch(e,f,g) + K[i] + W[i];
        uint32_t T2 = Sigma0(a) + Maj(a,b,c);
        h=g; g=f; f=e; e=d+T1; d=c; c=b; b=a; a=T1+T2;
    }
    return a;
}

int main(int argc, char *argv[]) {
    int bit = (argc >= 2) ? atoi(argv[1]) : 7;
    uint32_t fill = (argc >= 3) ? (uint32_t)strtoul(argv[2], NULL, 0) : 0xFFFFFFFF;
    uint32_t kernel_diff = 1U << bit;

    fprintf(stderr, "Sweeping (0,9) bit=%d fill=0x%08x — full 2^32 m0\n", bit, fill);
    fprintf(stderr, "kernel_diff = 0x%08x (xor m[0] and m[9])\n", kernel_diff);

    long long n_eligible = 0;
    int n_threads = omp_get_max_threads();
    fprintf(stderr, "OpenMP threads: %d\n", n_threads);

    #pragma omp parallel reduction(+:n_eligible)
    {
        uint32_t M1[16], M2[16];
        for (int i = 0; i < 16; i++) M1[i] = M2[i] = fill;
        M2[9] = fill ^ kernel_diff;

        long long local_eligible = 0;
        #pragma omp for schedule(dynamic, 65536)
        for (long long m = 0; m <= 0xFFFFFFFFLL; m++) {
            M1[0] = (uint32_t)m;
            M2[0] = (uint32_t)m ^ kernel_diff;
            uint32_t a1 = a_at_slot57(M1);
            uint32_t a2 = a_at_slot57(M2);
            if (a1 == a2) {
                local_eligible++;
                if (local_eligible <= 10) {
                    #pragma omp critical
                    fprintf(stderr, "  ELIGIBLE: m=0x%08lx (thread %d)\n",
                            (unsigned long)m, omp_get_thread_num());
                }
            }
            if ((m & 0x0FFFFFFFLL) == 0 && omp_get_thread_num() == 0) {
                fprintf(stderr, "  progress m=0x%08lx (~%.0f%%)\n",
                        (unsigned long)m, 100.0 * m / (double)0x100000000LL);
            }
        }
        n_eligible = local_eligible;
    }

    printf("FINAL: bit=%d fill=0x%08x trials=2^32 eligible=%lld\n", bit, fill, n_eligible);
    /* Σ1/σ1 alignment hypothesis from registry/notes/20260425_covered_bits_pattern.md
     * predicts 0 eligible at σ0-aligned bits {3, 7, 18}. Print verdict ONLY for
     * those bits where the hypothesis makes a prediction. */
    int sigma0_aligned = (bit == 3 || bit == 7 || bit == 18);
    if (sigma0_aligned) {
        if (n_eligible == 0) {
            printf("HYPOTHESIS HOLDS: bit=%d (σ0-aligned, predicted 0) → 0 eligible.\n", bit);
        } else {
            printf("HYPOTHESIS FALSIFIED: bit=%d (σ0-aligned, predicted 0) → %lld eligible.\n",
                   bit, n_eligible);
        }
    } else {
        printf("(bit=%d not in σ0-aligned prediction set; result is informational only.)\n", bit);
    }
    return 0;
}
