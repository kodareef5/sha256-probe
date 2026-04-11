/* Fast viability check: skip bitmap, just count W[60] matches against target.
 * No memset, no atomic OR, no bitmap walk. Pure compute loop.
 * Target: ~2-3x speedup over prefix_viability_scan.c.
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
static const uint32_t K[64] = {0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
static const uint32_t IV[8] = {0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};

static void compute_state(const uint32_t M[16], uint32_t state[8], uint32_t W[64]) {
    for (int i = 0; i < 16; i++) W[i] = M[i];
    for (int i = 16; i < 57; i++) W[i] = sigma1(W[i-2]) + W[i-7] + sigma0(W[i-15]) + W[i-16];
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

static uint64_t xs(uint64_t *s) { *s ^= *s << 13; *s ^= *s >> 7; *s ^= *s << 17; return *s; }

/* Returns number of W[60] giving cascade_dw == target. */
static long fast_viability(uint32_t w1_57, uint32_t w1_58, uint32_t w1_59,
                            const uint32_t s1[8], const uint32_t s2[8],
                            uint32_t C57, const uint32_t W1_pre[64], const uint32_t W2_pre[64],
                            uint32_t *first_w60) {
    uint32_t sched_const1_61 = W1_pre[54] + sigma0(W1_pre[46]) + W1_pre[45];
    uint32_t sched_const2_61 = W2_pre[54] + sigma0(W2_pre[46]) + W2_pre[45];

    uint32_t s1a[8], s2a[8];
    one_round(s1a, s1, w1_57, 57);
    one_round(s2a, s2, w1_57 + C57, 57);
    uint32_t C58 = cascade_dw(s1a, s2a);
    uint32_t s1b[8], s2b[8];
    one_round(s1b, s1a, w1_58, 58);
    one_round(s2b, s2a, w1_58 + C58, 58);
    uint32_t C59 = cascade_dw(s1b, s2b);
    uint32_t s1c[8], s2c[8];
    one_round(s1c, s1b, w1_59, 59);
    one_round(s2c, s2b, w1_59 + C59, 59);
    uint32_t C60 = cascade_dw(s1c, s2c);
    uint32_t target = sigma1(w1_59 + C59) - sigma1(w1_59) + sched_const2_61 - sched_const1_61;

    long matches = 0;
    uint32_t found_w60 = 0xffffffff;
    /* Inline cascade_dw at round 61 for speed */
    uint32_t s1c4 = s1c[4], s1c5 = s1c[5], s1c6 = s1c[6], s1c7 = s1c[7];
    uint32_t s2c4 = s2c[4], s2c5 = s2c[5], s2c6 = s2c[6], s2c7 = s2c[7];
    uint32_t s1c0 = s1c[0], s1c1 = s1c[1], s1c2 = s1c[2], s1c3 = s1c[3];
    uint32_t s2c0 = s2c[0], s2c1 = s2c[1], s2c2 = s2c[2], s2c3 = s2c[3];
    /* Pre-compute round-60 T1 base values (no W[60] contribution) */
    uint32_t T1_base_M1 = s1c7 + Sigma1(s1c4) + Ch(s1c4, s1c5, s1c6) + K[60];
    uint32_t T1_base_M2 = s2c7 + Sigma1(s2c4) + Ch(s2c4, s2c5, s2c6) + K[60];
    uint32_t T2_60_M1 = Sigma0(s1c0) + Maj(s1c0, s1c1, s1c2);
    uint32_t T2_60_M2 = Sigma0(s2c0) + Maj(s2c0, s2c1, s2c2);

    #pragma omp parallel for schedule(static) reduction(+:matches)
    for (long w_l = 0; w_l < (1L << 32); w_l++) {
        uint32_t w1_60 = (uint32_t)w_l;
        /* Round 60 update: a' = T1+T2, e' = d + T1, f' = e, g' = f, h' = g */
        uint32_t T1_M1 = T1_base_M1 + w1_60;
        uint32_t T1_M2 = T1_base_M2 + (w1_60 + C60);
        uint32_t a_M1_61 = T1_M1 + T2_60_M1;
        uint32_t a_M2_61 = T1_M2 + T2_60_M2;
        uint32_t e_M1_61 = s1c3 + T1_M1;
        uint32_t e_M2_61 = s2c3 + T1_M2;
        /* round 61 state: e=e_61, f=s1c4 (was e_60), g=s1c5 (was f_60), h=s1c6 (was g_60) */
        uint32_t dh_61 = s1c6 - s2c6;
        uint32_t dSig1_61 = Sigma1(e_M1_61) - Sigma1(e_M2_61);
        uint32_t dCh_61 = Ch(e_M1_61, s1c4, s1c5) - Ch(e_M2_61, s2c4, s2c5);
        /* T2 at round 61: a_61 above */
        uint32_t T2_M1_61 = Sigma0(a_M1_61) + Maj(a_M1_61, s1c0, s1c1);
        uint32_t T2_M2_61 = Sigma0(a_M2_61) + Maj(a_M2_61, s2c0, s2c1);
        uint32_t v = dh_61 + dSig1_61 + dCh_61 + T2_M1_61 - T2_M2_61;
        if (v == target) {
            matches++;
            if (found_w60 == 0xffffffff) {
                #pragma omp critical
                if (found_w60 == 0xffffffff) found_w60 = w1_60;
            }
        }
    }
    *first_w60 = found_w60;
    return matches;
}

int main(int argc, char **argv) {
    int n_prefixes = argc > 1 ? atoi(argv[1]) : 32;
    uint64_t seed_base = argc > 2 ? strtoull(argv[2], NULL, 0) : 0xc0ffee;

    uint32_t M1[16] = {0x17149975,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff};
    uint32_t M2[16];
    memcpy(M2, M1, sizeof(M2));
    M2[0] ^= 0x80000000; M2[9] ^= 0x80000000;
    uint32_t s1[8], s2[8], W1_pre[64], W2_pre[64];
    compute_state(M1, s1, W1_pre);
    compute_state(M2, s2, W2_pre);
    uint32_t C57 = cascade_dw(s1, s2);

    /* Verify cert first */
    fprintf(stderr, "=== Verifying CERT prefix ===\n");
    uint32_t found;
    long c_matches = fast_viability(0x9ccfa55e, 0xd9d64416, 0x9e3ffb08,
                                     s1, s2, C57, W1_pre, W2_pre, &found);
    fprintf(stderr, "CERT: matches=%ld first_w60=0x%08x  expected: 8192, 0xb6befe82-ish\n\n",
            c_matches, found);
    if (c_matches == 0) {
        fprintf(stderr, "ERROR: cert should be viable\n");
        return 1;
    }

    fprintf(stderr, "=== Scanning %d random prefixes (seed=0x%lx) ===\n\n", n_prefixes, (long)seed_base);
    uint64_t rng = seed_base;
    int n_viable = 0;
    time_t t0 = time(NULL);

    for (int p = 0; p < n_prefixes; p++) {
        uint32_t w57 = (uint32_t)xs(&rng);
        uint32_t w58 = (uint32_t)xs(&rng);
        uint32_t w59 = (uint32_t)xs(&rng);
        long matches = fast_viability(w57, w58, w59, s1, s2, C57, W1_pre, W2_pre, &found);
        time_t now = time(NULL);
        if (matches > 0) {
            fprintf(stderr, "[%4d] *** VIABLE *** W=0x%08x,0x%08x,0x%08x  matches=%ld w60=0x%08x  [%lds]\n",
                    p, w57, w58, w59, matches, found, (long)(now - t0));
            n_viable++;
        } else if (p % 8 == 0) {
            fprintf(stderr, "[%4d] W=0x%08x,0x%08x,0x%08x  no viable (running %lds, viable so far: %d)\n",
                    p, w57, w58, w59, (long)(now - t0), n_viable);
        }
    }

    time_t t1 = time(NULL);
    fprintf(stderr, "\n=== Summary ===\n");
    fprintf(stderr, "Viable: %d / %d  (%.4f%%)  [%lds total, %.1fs/prefix]\n",
            n_viable, n_prefixes, 100.0 * n_viable / n_prefixes,
            (long)(t1 - t0), (double)(t1 - t0) / n_prefixes);
    return 0;
}
