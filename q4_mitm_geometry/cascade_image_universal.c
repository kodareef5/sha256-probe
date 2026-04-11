/* Compute cascade_dw at round 61 (the FULL function — not the Ch-only
 * approximation) for multiple prefixes. For each, compute the F_2 affine
 * basis. Compare across prefixes to test universality.
 *
 * If the bases span the same subspace → universal precomputable filter.
 * If different → per-prefix structure.
 */
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <math.h>
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
static const uint32_t K[64] = {0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
static const uint32_t IV[8] = {0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};

static void compute_state(const uint32_t M[16], uint32_t state[8]) {
    uint32_t W[64];
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

typedef struct {
    const char *name;
    uint32_t w1_57, w1_58, w1_59;
    uint32_t basis[33];
    int rank;
    uint32_t v0;
    long count;
    /* round-60 state for this prefix */
    uint32_t s1c[8], s2c[8];
    uint32_t C60;
} prefix_t;

static void build_prefix(prefix_t *p, const uint32_t s1[8], const uint32_t s2[8], uint32_t C57) {
    uint32_t s1a[8], s2a[8];
    one_round(s1a, s1, p->w1_57, 57);
    one_round(s2a, s2, p->w1_57 + C57, 57);
    uint32_t C58 = cascade_dw(s1a, s2a);
    uint32_t s1b[8], s2b[8];
    one_round(s1b, s1a, p->w1_58, 58);
    one_round(s2b, s2a, p->w1_58 + C58, 58);
    uint32_t C59 = cascade_dw(s1b, s2b);
    one_round(p->s1c, s1b, p->w1_59, 59);
    one_round(p->s2c, s2b, p->w1_59 + C59, 59);
    p->C60 = cascade_dw(p->s1c, p->s2c);
}

static void compute_image(prefix_t *p, uint8_t *seen) {
    memset(seen, 0, (1L << 32) / 8);
    #pragma omp parallel for schedule(static)
    for (long w_l = 0; w_l < (1L << 32); w_l++) {
        uint32_t w1_60 = (uint32_t)w_l;
        uint32_t s1d[8], s2d[8];
        one_round(s1d, p->s1c, w1_60, 60);
        one_round(s2d, p->s2c, w1_60 + p->C60, 60);
        uint32_t v = cascade_dw(s1d, s2d);
        long idx = (long)v >> 3;
        uint8_t bit = 1 << (v & 7);
        #pragma omp atomic
        seen[idx] |= bit;
    }

    /* Find first value */
    uint32_t v0 = 0;
    int found = 0;
    for (long i = 0; i < (1L << 32); i++) {
        long idx = i >> 3;
        uint8_t bit = 1 << (i & 7);
        if (seen[idx] & bit) { v0 = (uint32_t)i; found = 1; break; }
    }
    p->v0 = v0;
    if (!found) { p->rank = 0; p->count = 0; return; }

    /* Compute basis */
    memset(p->basis, 0, sizeof(p->basis));
    int rank = 0;
    long count = 0;
    for (long i = 0; i < (1L << 32); i++) {
        long idx = i >> 3;
        uint8_t bit = 1 << (i & 7);
        if (seen[idx] & bit) {
            count++;
            uint32_t v = (uint32_t)i ^ v0;
            if (v == 0) continue;
            uint32_t r = v;
            for (int b = 31; b >= 0; b--) {
                if ((r >> b) & 1) {
                    if (p->basis[b] == 0) {
                        p->basis[b] = r;
                        rank++;
                        break;
                    }
                    r ^= p->basis[b];
                }
            }
        }
    }
    p->rank = rank;
    p->count = count;
}

static int in_span(const uint32_t *basis, uint32_t v) {
    uint32_t r = v;
    for (int b = 31; b >= 0; b--) {
        if ((r >> b) & 1) {
            if (basis[b] == 0) return 0;
            r ^= basis[b];
        }
    }
    return r == 0;
}

static int basis_overlap(const uint32_t *A, const uint32_t *B) {
    int overlap = 0;
    for (int b = 0; b < 32; b++) {
        if (B[b] != 0 && in_span(A, B[b])) overlap++;
    }
    return overlap;
}

static int union_rank(const uint32_t *A, const uint32_t *B) {
    uint32_t U[33];
    memcpy(U, A, sizeof(U));
    int n = 0;
    for (int b = 0; b < 32; b++) if (U[b]) n++;
    for (int b = 0; b < 32; b++) {
        if (B[b] == 0) continue;
        uint32_t r = B[b];
        for (int bb = 31; bb >= 0; bb--) {
            if ((r >> bb) & 1) {
                if (U[bb] == 0) { U[bb] = r; n++; break; }
                r ^= U[bb];
            }
        }
    }
    return n;
}

int main() {
    uint32_t M1[16] = {0x17149975,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff};
    uint32_t M2[16];
    memcpy(M2, M1, sizeof(M2));
    M2[0] ^= 0x80000000; M2[9] ^= 0x80000000;
    uint32_t s1[8], s2[8];
    compute_state(M1, s1);
    compute_state(M2, s2);
    uint32_t C57 = cascade_dw(s1, s2);

    /* Cert + 4 random prefixes */
    prefix_t prefs[5];
    prefs[0] = (prefix_t){.name = "CERT", .w1_57 = 0x9ccfa55e, .w1_58 = 0xd9d64416, .w1_59 = 0x9e3ffb08};

    uint64_t rng = 0x123456789abcULL;
    char *names[] = {"RAND1", "RAND2", "RAND3", "RAND4"};
    for (int p = 1; p <= 4; p++) {
        prefs[p].name = names[p-1];
        prefs[p].w1_57 = (uint32_t)xs(&rng);
        prefs[p].w1_58 = (uint32_t)xs(&rng);
        prefs[p].w1_59 = (uint32_t)xs(&rng);
    }

    for (int p = 0; p < 5; p++) {
        build_prefix(&prefs[p], s1, s2, C57);
    }

    uint8_t *seen = calloc((1L << 32) / 8, 1);
    if (!seen) { fprintf(stderr, "alloc failed\n"); return 1; }

    fprintf(stderr, "=== Computing FULL cascade_dw at round 61 image for 5 prefixes ===\n\n");
    for (int p = 0; p < 5; p++) {
        time_t t0 = time(NULL);
        fprintf(stderr, "[%s] W[57..59]=0x%08x 0x%08x 0x%08x C60=0x%08x\n",
                prefs[p].name, prefs[p].w1_57, prefs[p].w1_58, prefs[p].w1_59, prefs[p].C60);
        compute_image(&prefs[p], seen);
        fprintf(stderr, "  image=%ld (2^%.2f), rank=%d, v0=0x%08x  [%lds]\n\n",
                prefs[p].count, log2((double)prefs[p].count), prefs[p].rank, prefs[p].v0,
                (long)(time(NULL) - t0));
    }

    fprintf(stderr, "=== Pairwise comparison vs CERT (full cascade_dw) ===\n\n");
    for (int p = 1; p < 5; p++) {
        int ovl_AB = basis_overlap(prefs[0].basis, prefs[p].basis);
        int ovl_BA = basis_overlap(prefs[p].basis, prefs[0].basis);
        int u_rank = union_rank(prefs[0].basis, prefs[p].basis);
        fprintf(stderr, "CERT vs %s:\n", prefs[p].name);
        fprintf(stderr, "  CERT-rank=%d, %s-rank=%d, union-rank=%d, intersection=%d\n",
                prefs[0].rank, prefs[p].name, prefs[p].rank, u_rank,
                prefs[0].rank + prefs[p].rank - u_rank);
        fprintf(stderr, "  %s basis in span(CERT): %d/%d\n",
                prefs[p].name, ovl_AB, prefs[p].rank);
        fprintf(stderr, "  CERT basis in span(%s): %d/%d\n",
                prefs[p].name, ovl_BA, prefs[0].rank);
        if (u_rank == prefs[0].rank && u_rank == prefs[p].rank) {
            fprintf(stderr, "  *** SAME SUBSPACE ***\n");
        }
        int v0_in = in_span(prefs[0].basis, prefs[0].v0 ^ prefs[p].v0);
        fprintf(stderr, "  v0_diff=0x%08x in span(CERT): %s\n\n",
                prefs[0].v0 ^ prefs[p].v0, v0_in ? "YES (same coset)" : "no");
    }

    /* Global union */
    uint32_t global_union[33];
    memcpy(global_union, prefs[0].basis, sizeof(global_union));
    for (int p = 1; p < 5; p++) {
        for (int b = 0; b < 32; b++) {
            if (prefs[p].basis[b] == 0) continue;
            uint32_t r = prefs[p].basis[b];
            for (int bb = 31; bb >= 0; bb--) {
                if ((r >> bb) & 1) {
                    if (global_union[bb] == 0) { global_union[bb] = r; break; }
                    r ^= global_union[bb];
                }
            }
        }
    }
    int gu = 0;
    for (int b = 0; b < 32; b++) if (global_union[b]) gu++;
    fprintf(stderr, "=== Global union of all 5 prefix bases ===\n");
    fprintf(stderr, "Union dimension: %d\n", gu);
    if (gu == prefs[0].rank) {
        fprintf(stderr, "*** ALL SHARE THE %d-DIM SUBSPACE ***\n", gu);
    }

    /* Print cert basis (first row) */
    fprintf(stderr, "\n=== CERT basis (echelon form) ===\n");
    for (int b = 31; b >= 0; b--) {
        if (prefs[0].basis[b]) fprintf(stderr, "  pivot %2d: 0x%08x  hw=%d\n",
                                        b, prefs[0].basis[b], hw(prefs[0].basis[b]));
    }

    free(seen);
    return 0;
}
