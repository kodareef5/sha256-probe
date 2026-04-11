/*
 * round61_family_structure.c — Analyze the structure of the 8192 round-61 matches.
 *
 * For multiple prefixes, find ALL W1[60] values passing round-61 closure
 * and analyze their common bit patterns.
 *
 * Question: do all 8192 matches share specific fixed bits?
 *           are these fixed bits the SAME across different prefixes?
 *
 * If yes -> precomputable filter for round-61 (no enumeration needed)
 *
 * Compile: gcc -O3 -march=native -fopenmp -o /tmp/r61fam q4_mitm_geometry/round61_family_structure.c
 */

#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#ifdef _OPENMP
#include <omp.h>
#endif

#define MASK 0xFFFFFFFFU

static inline uint32_t ROR(uint32_t x, int n) { return (x >> n) | (x << (32 - n)); }
static inline uint32_t Ch(uint32_t e, uint32_t f, uint32_t g) { return (e & f) ^ (~e & g); }
static inline uint32_t Maj(uint32_t a, uint32_t b, uint32_t c) { return (a & b) ^ (a & c) ^ (b & c); }
static inline uint32_t Sigma0(uint32_t a) { return ROR(a, 2) ^ ROR(a, 13) ^ ROR(a, 22); }
static inline uint32_t Sigma1(uint32_t e) { return ROR(e, 6) ^ ROR(e, 11) ^ ROR(e, 25); }
static inline uint32_t sigma0(uint32_t x) { return ROR(x, 7) ^ ROR(x, 18) ^ (x >> 3); }
static inline uint32_t sigma1(uint32_t x) { return ROR(x, 17) ^ ROR(x, 19) ^ (x >> 10); }
static inline int hw(uint32_t x) { return __builtin_popcount(x); }

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
    0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,
    0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19
};

static void compute_state(const uint32_t M[16], uint32_t state[8], uint32_t W[64]) {
    for (int i = 0; i < 16; i++) W[i] = M[i];
    for (int i = 16; i < 57; i++)
        W[i] = sigma1(W[i-2]) + W[i-7] + sigma0(W[i-15]) + W[i-16];
    uint32_t a=IV[0],b=IV[1],c=IV[2],d=IV[3],e=IV[4],f=IV[5],g=IV[6],h=IV[7];
    for (int i = 0; i < 57; i++) {
        uint32_t T1 = h + Sigma1(e) + Ch(e,f,g) + K[i] + W[i];
        uint32_t T2 = Sigma0(a) + Maj(a,b,c);
        h=g; g=f; f=e; e=d+T1; d=c; c=b; b=a; a=T1+T2;
    }
    state[0]=a; state[1]=b; state[2]=c; state[3]=d;
    state[4]=e; state[5]=f; state[6]=g; state[7]=h;
}

static uint32_t cascade_dw(const uint32_t s1[8], const uint32_t s2[8]) {
    uint32_t dh = s1[7] - s2[7];
    uint32_t dSig1 = Sigma1(s1[4]) - Sigma1(s2[4]);
    uint32_t dCh = Ch(s1[4],s1[5],s1[6]) - Ch(s2[4],s2[5],s2[6]);
    uint32_t T2_1 = Sigma0(s1[0]) + Maj(s1[0],s1[1],s1[2]);
    uint32_t T2_2 = Sigma0(s2[0]) + Maj(s2[0],s2[1],s2[2]);
    return dh + dSig1 + dCh + T2_1 - T2_2;
}

static void one_round(uint32_t out[8], const uint32_t in[8], uint32_t w, int round_idx) {
    uint32_t T1 = in[7] + Sigma1(in[4]) + Ch(in[4],in[5],in[6]) + K[round_idx] + w;
    uint32_t T2 = Sigma0(in[0]) + Maj(in[0],in[1],in[2]);
    out[0] = T1 + T2; out[1] = in[0]; out[2] = in[1]; out[3] = in[2];
    out[4] = in[3] + T1; out[5] = in[4]; out[6] = in[5]; out[7] = in[6];
}

static uint64_t xorshift(uint64_t *s) {
    *s ^= *s << 13;
    *s ^= *s >> 7;
    *s ^= *s << 17;
    return *s;
}

/* For a given prefix, find ALL W1[60] passing round-61 and analyze structure. */
static void analyze_prefix(uint32_t w1_57, uint32_t w1_58, uint32_t w1_59,
                           const uint32_t s1c[8], const uint32_t s2c[8],
                           uint32_t C60, uint32_t target_dW61,
                           uint32_t *and_mask_out, uint32_t *or_mask_out, long *count_out) {
    /* and_mask = AND of all matches (which bits are always 1)
     * or_mask  = OR of all matches  (which bits are sometimes 1)
     * fixed_bits = ~and_mask AND ~or_mask | and_mask  (bits that are constant) */
    uint32_t and_mask = MASK;
    uint32_t or_mask = 0;
    long count = 0;

    #pragma omp parallel
    {
        uint32_t local_and = MASK, local_or = 0;
        long local_count = 0;

        #pragma omp for
        for (long w1_60_l = 0; w1_60_l < (1L << 32); w1_60_l++) {
            uint32_t w1_60 = (uint32_t)w1_60_l;
            uint32_t w2_60 = w1_60 + C60;

            uint32_t s1d[8], s2d[8];
            one_round(s1d, s1c, w1_60, 60);
            one_round(s2d, s2c, w2_60, 60);

            if (cascade_dw(s1d, s2d) == target_dW61) {
                local_and &= w1_60;
                local_or |= w1_60;
                local_count++;
            }
        }

        #pragma omp critical
        {
            and_mask &= local_and;
            or_mask |= local_or;
            count += local_count;
        }
    }

    *and_mask_out = and_mask;
    *or_mask_out = or_mask;
    *count_out = count;
}

int main(int argc, char **argv) {
    int n_prefixes = argc > 1 ? atoi(argv[1]) : 5;

    uint32_t M1[16] = {0x17149975,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff};
    uint32_t M2[16];
    memcpy(M2, M1, sizeof(M2));
    M2[0] ^= 0x80000000; M2[9] ^= 0x80000000;

    uint32_t s1[8], s2[8], W1_pre[64], W2_pre[64];
    compute_state(M1, s1, W1_pre);
    compute_state(M2, s2, W2_pre);
    uint32_t C57 = cascade_dw(s1, s2);

    uint32_t sched_const1_61 = W1_pre[54] + sigma0(W1_pre[46]) + W1_pre[45];
    uint32_t sched_const2_61 = W2_pre[54] + sigma0(W2_pre[46]) + W2_pre[45];

    /* Use the cert as the first prefix, then random ones */
    uint32_t cert_w1_57 = 0x9ccfa55e;
    uint32_t cert_w1_58 = 0xd9d64416;
    uint32_t cert_w1_59 = 0x9e3ffb08;

    uint64_t rng = (uint64_t)time(NULL) | 1;
    uint32_t common_and = MASK;  /* bits that are 1 in ALL matches across ALL prefixes */
    uint32_t common_zero = MASK; /* bits that are 0 in ALL matches across ALL prefixes */

    fprintf(stderr, "Round-61 family structure analysis\n");
    fprintf(stderr, "Will analyze %d prefixes (first = cert)\n\n", n_prefixes);

    for (int p = 0; p < n_prefixes; p++) {
        uint32_t w1_57, w1_58, w1_59;
        if (p == 0) {
            w1_57 = cert_w1_57;
            w1_58 = cert_w1_58;
            w1_59 = cert_w1_59;
        } else {
            w1_57 = (uint32_t)xorshift(&rng);
            w1_58 = (uint32_t)xorshift(&rng);
            w1_59 = (uint32_t)xorshift(&rng);
        }

        uint32_t w2_57 = w1_57 + C57;
        uint32_t s1a[8], s2a[8];
        one_round(s1a, s1, w1_57, 57);
        one_round(s2a, s2, w2_57, 57);
        uint32_t C58 = cascade_dw(s1a, s2a);

        uint32_t w2_58 = w1_58 + C58;
        uint32_t s1b[8], s2b[8];
        one_round(s1b, s1a, w1_58, 58);
        one_round(s2b, s2a, w2_58, 58);
        uint32_t C59 = cascade_dw(s1b, s2b);

        uint32_t w2_59 = w1_59 + C59;
        uint32_t s1c[8], s2c[8];
        one_round(s1c, s1b, w1_59, 59);
        one_round(s2c, s2b, w2_59, 59);
        uint32_t C60 = cascade_dw(s1c, s2c);

        uint32_t target_dW61 = sigma1(w2_59) - sigma1(w1_59) + sched_const2_61 - sched_const1_61;

        uint32_t and_mask, or_mask;
        long count;
        time_t pt0 = time(NULL);
        analyze_prefix(w1_57, w1_58, w1_59, s1c, s2c, C60, target_dW61, &and_mask, &or_mask, &count);
        time_t pt1 = time(NULL);

        /* Bits that are constant across this family:
         * fixed_to_1 = and_mask (these are always 1)
         * fixed_to_0 = ~or_mask (these are always 0)
         * variable = or_mask & ~and_mask (these can be either)
         */
        uint32_t fixed_to_1 = and_mask;
        uint32_t fixed_to_0 = ~or_mask & MASK;
        uint32_t variable = or_mask & ~and_mask & MASK;
        int n_fixed = hw(fixed_to_1) + hw(fixed_to_0);
        int n_var = hw(variable);

        fprintf(stderr, "[prefix %d, %lds] W1[57..59]=0x%08x 0x%08x 0x%08x\n",
                p, (long)(pt1-pt0), w1_57, w1_58, w1_59);
        fprintf(stderr, "  Round-61 matches: %ld\n", count);
        fprintf(stderr, "  AND_mask:    0x%08x  (bits always 1)\n", fixed_to_1);
        fprintf(stderr, "  ~OR_mask:    0x%08x  (bits always 0)\n", fixed_to_0);
        fprintf(stderr, "  variable:    0x%08x  (free bits)\n", variable);
        fprintf(stderr, "  fixed bits: %d, variable bits: %d\n", n_fixed, n_var);
        fprintf(stderr, "\n");

        /* Track bits common across all prefixes */
        if (count > 0) {
            common_and &= and_mask;
            common_zero &= ~or_mask & MASK;
        }
    }

    fprintf(stderr, "=== Common across all %d prefixes ===\n", n_prefixes);
    fprintf(stderr, "Bits always 1 (across all prefixes): 0x%08x (%d bits)\n", common_and, hw(common_and));
    fprintf(stderr, "Bits always 0 (across all prefixes): 0x%08x (%d bits)\n", common_zero, hw(common_zero));
    fprintf(stderr, "Bits SOMETIMES 1 SOMETIMES 0: %d bits\n", 32 - hw(common_and) - hw(common_zero));

    return 0;
}
