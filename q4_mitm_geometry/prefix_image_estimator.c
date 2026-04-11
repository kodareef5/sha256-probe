/* CHEAP image size estimator: sample N random W[60] values and count
 * distinct cascade_dw outputs. Time: O(N) per prefix instead of O(2^32).
 *
 * For N=1024:
 *   - Image >> N: distinct ≈ N (all unique)
 *   - Image << N: distinct ≈ image_size (saturated)
 *   - In between: birthday estimate
 *
 * Use this to RANK many prefixes cheaply, then full-test the top candidates.
 *
 * Validation: cert image is 1,179,648 (>> 1024), so cert sample should give
 * distinct ≈ 1024 (all unique).
 *
 * Speed target: 100K prefixes/sec on 24 cores.
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

/* Estimate image size by sampling N values of W[60]. Returns number of
 * distinct cascade_dw outputs. Also returns 1 if any sample matches target. */
static int estimate_image(uint32_t w1_57, uint32_t w1_58, uint32_t w1_59,
                           const uint32_t s1[8], const uint32_t s2[8],
                           uint32_t C57, const uint32_t W1_pre[64], const uint32_t W2_pre[64],
                           int N_samples, uint64_t *rng,
                           int *distinct_out, int *target_match_out) {
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

    /* Sample N W[60] values, store cascade_dw results, sort and count distinct */
    uint32_t *vals = malloc(N_samples * sizeof(uint32_t));
    int target_matched = 0;
    for (int i = 0; i < N_samples; i++) {
        uint32_t w1_60 = (uint32_t)xs(rng);
        uint32_t s1d[8], s2d[8];
        one_round(s1d, s1c, w1_60, 60);
        one_round(s2d, s2c, w1_60 + C60, 60);
        uint32_t v = cascade_dw(s1d, s2d);
        vals[i] = v;
        if (v == target) target_matched = 1;
    }
    /* Count distinct via sort */
    /* Simple O(N log N) sort */
    for (int i = 1; i < N_samples; i++) {
        uint32_t k = vals[i];
        int j = i - 1;
        while (j >= 0 && vals[j] > k) { vals[j+1] = vals[j]; j--; }
        vals[j+1] = k;
    }
    int distinct = 1;
    for (int i = 1; i < N_samples; i++) {
        if (vals[i] != vals[i-1]) distinct++;
    }
    free(vals);
    *distinct_out = distinct;
    *target_match_out = target_matched;
    return 0;
}

int main(int argc, char **argv) {
    int n_prefixes = argc > 1 ? atoi(argv[1]) : 10000;
    int n_samples = argc > 2 ? atoi(argv[2]) : 1024;
    uint64_t seed_base = argc > 3 ? strtoull(argv[3], NULL, 0) : 0xdeadbeef;
    int min_distinct = argc > 4 ? atoi(argv[4]) : 1000;  /* threshold for "interesting" */

    uint32_t M1[16] = {0x17149975,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff};
    uint32_t M2[16];
    memcpy(M2, M1, sizeof(M2));
    M2[0] ^= 0x80000000; M2[9] ^= 0x80000000;
    uint32_t s1[8], s2[8], W1_pre[64], W2_pre[64];
    compute_state(M1, s1, W1_pre);
    compute_state(M2, s2, W2_pre);
    uint32_t C57 = cascade_dw(s1, s2);

    /* Verify cert */
    fprintf(stderr, "=== Verifying CERT ===\n");
    uint64_t test_rng = 0xc0ffee;
    int d, m;
    estimate_image(0x9ccfa55e, 0xd9d64416, 0x9e3ffb08, s1, s2, C57, W1_pre, W2_pre,
                   n_samples, &test_rng, &d, &m);
    fprintf(stderr, "CERT: distinct=%d/%d  target_in_sample=%d  (expected: ~all unique, target rare)\n\n",
            d, n_samples, m);

    fprintf(stderr, "=== Sampling %d prefixes (N=%d samples each) ===\n", n_prefixes, n_samples);
    fprintf(stderr, "Reporting prefixes with distinct >= %d (large image) and any with target hit\n\n",
            min_distinct);

    time_t t0 = time(NULL);
    int n_interesting = 0, n_target = 0;

    /* Parallelize over prefixes */
    int chunk = 64;
    long n_done = 0;
    #pragma omp parallel
    {
        uint64_t rng = seed_base ^ ((uint64_t)omp_get_thread_num() << 32);
        rng = rng * 0x100000001b3ULL + 0xcbf29ce484222325ULL;  /* FNV-init mix */

        #pragma omp for schedule(dynamic, 64)
        for (int p = 0; p < n_prefixes; p++) {
            uint32_t w57 = (uint32_t)xs(&rng);
            uint32_t w58 = (uint32_t)xs(&rng);
            uint32_t w59 = (uint32_t)xs(&rng);
            int distinct, matched;
            uint64_t local_rng = rng;
            estimate_image(w57, w58, w59, s1, s2, C57, W1_pre, W2_pre,
                           n_samples, &local_rng, &distinct, &matched);
            #pragma omp atomic
            n_done++;
            if (distinct >= min_distinct || matched) {
                #pragma omp critical
                {
                    if (distinct >= min_distinct) n_interesting++;
                    if (matched) n_target++;
                    fprintf(stderr, "[%d] W=0x%08x,0x%08x,0x%08x  distinct=%d  %s\n",
                            p, w57, w58, w59, distinct, matched ? "*** TARGET HIT ***" : "");
                }
            }
        }
    }

    time_t t1 = time(NULL);
    fprintf(stderr, "\n=== Summary ===\n");
    fprintf(stderr, "Scanned: %d prefixes in %lds (%.0f prefix/sec)\n",
            n_prefixes, (long)(t1 - t0), (double)n_prefixes / (t1 - t0 + 1));
    fprintf(stderr, "Interesting (distinct >= %d): %d (%.2f%%)\n",
            min_distinct, n_interesting, 100.0 * n_interesting / n_prefixes);
    fprintf(stderr, "Target hits in sample: %d\n", n_target);
    fprintf(stderr, "(Note: target hit in 1024 samples doesn't mean viable. Full test those.)\n");
    return 0;
}
