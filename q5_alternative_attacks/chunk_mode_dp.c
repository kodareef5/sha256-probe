/*
 * chunk_mode_dp.c — Chunk-mode DP boundary-state deduplication measurement
 *
 * GPT-5.4 prescribed algorithm (measurement prototype):
 * At N=8 with B=4 bit chunks, measure whether projecting to boundary
 * carry states at bit 4 yields effective deduplication.
 *
 * For each of 2^32 (W57,W58,W59,W60) configs (via cascade DP):
 * 1. Compute both paths through all 7 rounds, extracting carries inline
 * 2. At the chunk boundary (bit 4): record carry-out at bit 3 from
 *    every addition in every round, for both paths
 * 3. Pack into a boundary StateKey = (carries_path1, carries_path2)
 * 4. Hash-cons and count unique StateKeys
 *
 * Also: for each collision, record its boundary state.
 * Verify all 260 collisions have unique boundary states.
 *
 * N=8, MSB kernel, M[0]=0x67, fill=0xff.
 * Compile: gcc -O3 -march=native -o chunk_mode_dp chunk_mode_dp.c -lm
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <time.h>

#define N 8
#define MASK ((1U << N) - 1)
#define MSB (1U << (N - 1))
#define ROUNDS 7
#define ADDS_PER_ROUND 7
#define TOTAL_ADDS (ROUNDS * ADDS_PER_ROUND)  /* 49 additions total */
#define BOUNDARY_BIT 4  /* chunk boundary between bits 0-3 and 4-7 */

/* Mask for low BOUNDARY_BIT bits */
#define LOW_MASK ((1U << BOUNDARY_BIT) - 1)  /* 0xF */

/* --- SHA-256 mini primitives (N-bit) --- */
static int rS0[3], rS1[3], rs0[2], rs1[2], ss0, ss1;
static int SR(int k) { int r = (int)rint((double)k * N / 32.0); return r < 1 ? 1 : r; }
static inline uint32_t ror_n(uint32_t x, int k) { k %= N; return ((x >> k) | (x << (N - k))) & MASK; }
static inline uint32_t fnS0(uint32_t a) { return ror_n(a, rS0[0]) ^ ror_n(a, rS0[1]) ^ ror_n(a, rS0[2]); }
static inline uint32_t fnS1(uint32_t e) { return ror_n(e, rS1[0]) ^ ror_n(e, rS1[1]) ^ ror_n(e, rS1[2]); }
static inline uint32_t fns0(uint32_t x) { return ror_n(x, rs0[0]) ^ ror_n(x, rs0[1]) ^ ((x >> ss0) & MASK); }
static inline uint32_t fns1(uint32_t x) { return ror_n(x, rs1[0]) ^ ror_n(x, rs1[1]) ^ ((x >> ss1) & MASK); }
static inline uint32_t fnCh(uint32_t e, uint32_t f, uint32_t g) { return ((e & f) ^ ((~e) & g)) & MASK; }
static inline uint32_t fnMj(uint32_t a, uint32_t b, uint32_t c) { return ((a & b) ^ (a & c) ^ (b & c)) & MASK; }

static const uint32_t K32[64] = {
    0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
    0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
    0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
    0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
    0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
    0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
    0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
    0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2
};
static const uint32_t IV32[8] = {
    0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19
};
static uint32_t KN[64], IVN[8];
static uint32_t state1[8], state2[8], W1p[57], W2p[57];

static void precompute(const uint32_t M[16], uint32_t st[8], uint32_t W[57]) {
    for (int i = 0; i < 16; i++) W[i] = M[i] & MASK;
    for (int i = 16; i < 57; i++)
        W[i] = (fns1(W[i-2]) + W[i-7] + fns0(W[i-15]) + W[i-16]) & MASK;
    uint32_t a=IVN[0],b=IVN[1],c=IVN[2],d=IVN[3],
             e=IVN[4],f=IVN[5],g=IVN[6],h=IVN[7];
    for (int i = 0; i < 57; i++) {
        uint32_t T1 = (h + fnS1(e) + fnCh(e,f,g) + KN[i] + W[i]) & MASK;
        uint32_t T2 = (fnS0(a) + fnMj(a,b,c)) & MASK;
        h=g; g=f; f=e; e=(d+T1)&MASK; d=c; c=b; b=a; a=(T1+T2)&MASK;
    }
    st[0]=a; st[1]=b; st[2]=c; st[3]=d;
    st[4]=e; st[5]=f; st[6]=g; st[7]=h;
}

static inline void sha_round(uint32_t s[8], uint32_t k, uint32_t w) {
    uint32_t T1 = (s[7]+fnS1(s[4])+fnCh(s[4],s[5],s[6])+k+w) & MASK;
    uint32_t T2 = (fnS0(s[0])+fnMj(s[0],s[1],s[2])) & MASK;
    s[7]=s[6]; s[6]=s[5]; s[5]=s[4]; s[4]=(s[3]+T1)&MASK;
    s[3]=s[2]; s[2]=s[1]; s[1]=s[0]; s[0]=(T1+T2)&MASK;
}

static uint32_t find_w2(uint32_t s1[8], uint32_t s2[8], int rnd, uint32_t w1) {
    uint32_t r1 = (s1[7]+fnS1(s1[4])+fnCh(s1[4],s1[5],s1[6])+KN[rnd]) & MASK;
    uint32_t r2 = (s2[7]+fnS1(s2[4])+fnCh(s2[4],s2[5],s2[6])+KN[rnd]) & MASK;
    uint32_t T21 = (fnS0(s1[0])+fnMj(s1[0],s1[1],s1[2])) & MASK;
    uint32_t T22 = (fnS0(s2[0])+fnMj(s2[0],s2[1],s2[2])) & MASK;
    return (w1 + r1 - r2 + T21 - T22) & MASK;
}

/*
 * SHA round with carry extraction at the chunk boundary.
 * Performs the round AND returns the 7 carry bits (one per addition)
 * packed into bits [base..base+6] of the carry accumulator.
 *
 * carry_out at bit (B-1) from a+b = bit B of (a_low + b_low)
 * where a_low = a & LOW_MASK (the bottom B bits).
 */
static inline uint64_t sha_round_carries(uint32_t s[8], uint32_t k, uint32_t w,
                                          int base) {
    uint32_t sig1_e = fnS1(s[4]);
    uint32_t ch_efg = fnCh(s[4], s[5], s[6]);
    uint32_t sig0_a = fnS0(s[0]);
    uint32_t maj_abc = fnMj(s[0], s[1], s[2]);

    uint32_t t0 = (s[7] + sig1_e) & MASK;
    uint32_t t1 = (t0 + ch_efg) & MASK;
    uint32_t t2 = (t1 + k) & MASK;
    uint32_t T1 = (t2 + w) & MASK;
    uint32_t T2 = (sig0_a + maj_abc) & MASK;

    /* Extract carry-out at bit 3 from each of the 7 additions */
    uint64_t carries = 0;
    carries |= (uint64_t)(((s[7] & LOW_MASK) + (sig1_e & LOW_MASK)) >> BOUNDARY_BIT & 1) << (base + 0);
    carries |= (uint64_t)(((t0 & LOW_MASK) + (ch_efg & LOW_MASK)) >> BOUNDARY_BIT & 1) << (base + 1);
    carries |= (uint64_t)(((t1 & LOW_MASK) + (k & LOW_MASK)) >> BOUNDARY_BIT & 1) << (base + 2);
    carries |= (uint64_t)(((t2 & LOW_MASK) + (w & LOW_MASK)) >> BOUNDARY_BIT & 1) << (base + 3);
    carries |= (uint64_t)(((sig0_a & LOW_MASK) + (maj_abc & LOW_MASK)) >> BOUNDARY_BIT & 1) << (base + 4);
    carries |= (uint64_t)(((s[3] & LOW_MASK) + (T1 & LOW_MASK)) >> BOUNDARY_BIT & 1) << (base + 5);
    carries |= (uint64_t)(((T1 & LOW_MASK) + (T2 & LOW_MASK)) >> BOUNDARY_BIT & 1) << (base + 6);

    /* Advance state */
    s[7]=s[6]; s[6]=s[5]; s[5]=s[4]; s[4]=(s[3]+T1)&MASK;
    s[3]=s[2]; s[2]=s[1]; s[1]=s[0]; s[0]=(T1+T2)&MASK;

    return carries;
}

/* ========== Boundary state type ========== */
typedef struct {
    uint64_t carries_p1;  /* carry-out at bit 3 for path 1, 49 bits */
    uint64_t carries_p2;  /* carry-out at bit 3 for path 2, 49 bits */
} BoundaryState;

/* ========== Hash table for boundary state deduplication ========== */

#define HT_BITS 26          /* 64M entries — handles high unique-state counts */
#define HT_SIZE (1U << HT_BITS)
#define HT_MASK (HT_SIZE - 1)

typedef struct {
    BoundaryState key;
    uint32_t count;
    uint32_t coll_count;
    int occupied;
} HTEntry;

static HTEntry *ht;
static uint64_t ht_entries = 0;

static inline uint32_t ht_hash(BoundaryState bs) {
    uint64_t h = 14695981039346656037ULL;
    h ^= bs.carries_p1; h *= 1099511628211ULL;
    h ^= bs.carries_p2; h *= 1099511628211ULL;
    h ^= (bs.carries_p1 >> 32); h *= 1099511628211ULL;
    h ^= (bs.carries_p2 >> 32); h *= 1099511628211ULL;
    return (uint32_t)(h & HT_MASK);
}

static inline int bs_eq(BoundaryState a, BoundaryState b) {
    return a.carries_p1 == b.carries_p1 && a.carries_p2 == b.carries_p2;
}

static int ht_insert(BoundaryState bs, int is_collision) {
    uint32_t idx = ht_hash(bs);
    for (;;) {
        if (!ht[idx].occupied) {
            ht[idx].key = bs;
            ht[idx].count = 1;
            ht[idx].coll_count = is_collision ? 1 : 0;
            ht[idx].occupied = 1;
            ht_entries++;
            return 1;
        }
        if (bs_eq(ht[idx].key, bs)) {
            ht[idx].count++;
            if (is_collision) ht[idx].coll_count++;
            return 0;
        }
        idx = (idx + 1) & HT_MASK;
    }
}

/* ========== Collision storage ========== */
#define MAX_COLL 4096
static int n_coll = 0;
static uint32_t coll_w1[MAX_COLL][4];
static BoundaryState coll_bs[MAX_COLL];

/* ========== Main ========== */
int main() {
    setbuf(stdout, NULL);

    /* Init SHA params */
    rS0[0]=SR(2); rS0[1]=SR(13); rS0[2]=SR(22);
    rS1[0]=SR(6); rS1[1]=SR(11); rS1[2]=SR(25);
    rs0[0]=SR(7); rs0[1]=SR(18); ss0=SR(3);
    rs1[0]=SR(17); rs1[1]=SR(19); ss1=SR(10);
    for (int i = 0; i < 64; i++) KN[i] = K32[i] & MASK;
    for (int i = 0; i < 8; i++) IVN[i] = IV32[i] & MASK;

    /* Find candidate: M[0]=0x67, fill=0xff */
    int found = 0;
    for (uint32_t m0 = 0; m0 <= MASK && !found; m0++) {
        uint32_t M1[16], M2[16];
        for (int i = 0; i < 16; i++) { M1[i] = MASK; M2[i] = MASK; }
        M1[0] = m0; M2[0] = m0 ^ MSB; M2[9] = MASK ^ MSB;
        precompute(M1, state1, W1p);
        precompute(M2, state2, W2p);
        if (state1[0] == state2[0]) {
            printf("Candidate: N=%d M[0]=0x%02x fill=0xff\n", N, m0);
            found = 1;
        }
    }
    if (!found) { printf("No candidate found at N=%d\n", N); return 1; }

    printf("\nChunk-Mode DP Boundary State Measurement\n");
    printf("=========================================\n");
    printf("N=%d, B=%d (chunk size), 2 chunks\n", N, BOUNDARY_BIT);
    printf("Boundary at bit %d: carry-out at bit %d from all %d additions x 2 paths\n",
           BOUNDARY_BIT, BOUNDARY_BIT - 1, TOTAL_ADDS);
    printf("Boundary state = (carries_p1[49 bits], carries_p2[49 bits])\n");
    printf("Search space: 2^%d = %llu configs (cascade DP over W1[57..60])\n\n",
           4*N, (unsigned long long)1ULL << (4*N));

    /* Allocate hash table */
    ht = calloc(HT_SIZE, sizeof(HTEntry));
    if (!ht) { printf("OOM for hash table\n"); return 1; }

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    uint64_t n_tested = 0;

    for (uint32_t w57 = 0; w57 < (1U << N); w57++) {
        uint32_t s57a[8], s57b[8];
        memcpy(s57a, state1, 32); memcpy(s57b, state2, 32);
        uint32_t w57b = find_w2(s57a, s57b, 57, w57);

        /* Round 57 with carry extraction */
        uint64_t c57a = sha_round_carries(s57a, KN[57], w57, 0);
        uint64_t c57b = sha_round_carries(s57b, KN[57], w57b, 0);

        for (uint32_t w58 = 0; w58 < (1U << N); w58++) {
            uint32_t s58a[8], s58b[8];
            memcpy(s58a, s57a, 32); memcpy(s58b, s57b, 32);
            uint32_t w58b = find_w2(s58a, s58b, 58, w58);

            uint64_t c58a = c57a | sha_round_carries(s58a, KN[58], w58, ADDS_PER_ROUND);
            uint64_t c58b = c57b | sha_round_carries(s58b, KN[58], w58b, ADDS_PER_ROUND);

            for (uint32_t w59 = 0; w59 < (1U << N); w59++) {
                uint32_t s59a[8], s59b[8];
                memcpy(s59a, s58a, 32); memcpy(s59b, s58b, 32);
                uint32_t w59b = find_w2(s59a, s59b, 59, w59);

                uint64_t c59a = c58a | sha_round_carries(s59a, KN[59], w59, 2*ADDS_PER_ROUND);
                uint64_t c59b = c58b | sha_round_carries(s59b, KN[59], w59b, 2*ADDS_PER_ROUND);

                for (uint32_t w60 = 0; w60 < (1U << N); w60++) {
                    uint32_t s60a[8], s60b[8];
                    memcpy(s60a, s59a, 32); memcpy(s60b, s59b, 32);
                    uint32_t w60b = find_w2(s60a, s60b, 60, w60);

                    uint64_t ca = c59a | sha_round_carries(s60a, KN[60], w60, 3*ADDS_PER_ROUND);
                    uint64_t cb = c59b | sha_round_carries(s60b, KN[60], w60b, 3*ADDS_PER_ROUND);

                    /* Schedule-determined rounds 61-63 */
                    uint32_t Wa[7]={w57, w58, w59, w60, 0, 0, 0};
                    uint32_t Wb[7]={w57b, w58b, w59b, w60b, 0, 0, 0};
                    Wa[4]=(fns1(Wa[2])+W1p[54]+fns0(W1p[46])+W1p[45])&MASK;
                    Wb[4]=(fns1(Wb[2])+W2p[54]+fns0(W2p[46])+W2p[45])&MASK;
                    Wa[5]=(fns1(Wa[3])+W1p[55]+fns0(W1p[47])+W1p[46])&MASK;
                    Wb[5]=(fns1(Wb[3])+W2p[55]+fns0(W2p[47])+W2p[46])&MASK;
                    Wa[6]=(fns1(Wa[4])+W1p[56]+fns0(W1p[48])+W1p[47])&MASK;
                    Wb[6]=(fns1(Wb[4])+W2p[56]+fns0(W2p[48])+W2p[47])&MASK;

                    /* Rounds 61-63 with carry extraction */
                    uint32_t fa[8], fb[8];
                    memcpy(fa, s60a, 32); memcpy(fb, s60b, 32);
                    for (int r = 4; r < 7; r++) {
                        ca |= sha_round_carries(fa, KN[57+r], Wa[r], r*ADDS_PER_ROUND);
                        cb |= sha_round_carries(fb, KN[57+r], Wb[r], r*ADDS_PER_ROUND);
                    }

                    /* Check collision */
                    int is_coll = 1;
                    for (int r = 0; r < 8; r++) {
                        if (fa[r] != fb[r]) { is_coll = 0; break; }
                    }

                    /* Build boundary state */
                    BoundaryState bs;
                    bs.carries_p1 = ca;
                    bs.carries_p2 = cb;

                    /* Insert into hash table */
                    ht_insert(bs, is_coll);

                    /* Record collision */
                    if (is_coll && n_coll < MAX_COLL) {
                        coll_w1[n_coll][0] = w57;
                        coll_w1[n_coll][1] = w58;
                        coll_w1[n_coll][2] = w59;
                        coll_w1[n_coll][3] = w60;
                        coll_bs[n_coll] = bs;
                        n_coll++;
                    }

                    n_tested++;
                }
            }
        }

        if ((w57 & 0x3) == 0x3) {
            clock_gettime(CLOCK_MONOTONIC, &t1);
            double el = (t1.tv_sec - t0.tv_sec) + (t1.tv_nsec - t0.tv_nsec) / 1e9;
            double pct = 100.0 * (w57 + 1) / (1 << N);
            double rate = n_tested / el / 1e6;
            printf("  [%5.1f%%] w57=0x%02x | tested=%llu coll=%d unique_bs=%llu | %.1fs ETA %.0fs | %.1fM/s\n",
                   pct, w57,
                   (unsigned long long)n_tested, n_coll,
                   (unsigned long long)ht_entries,
                   el, el / pct * 100 - el, rate);
            if (ht_entries > HT_SIZE * 3 / 4) {
                printf("  WARNING: hash table >75%% full (%llu / %u), results may have collisions\n",
                       (unsigned long long)ht_entries, HT_SIZE);
            }
        }
    }

    clock_gettime(CLOCK_MONOTONIC, &t1);
    double elapsed = (t1.tv_sec - t0.tv_sec) + (t1.tv_nsec - t0.tv_nsec) / 1e9;

    /* ========== Analysis ========== */
    printf("\n");
    printf("=============================================================\n");
    printf("  Chunk-Mode DP Boundary State Results (N=%d, B=%d)\n", N, BOUNDARY_BIT);
    printf("=============================================================\n\n");

    printf("--- Search ---\n");
    printf("Total configs tested:           %llu (2^%d)\n",
           (unsigned long long)n_tested, 4*N);
    printf("Collisions found:               %d\n", n_coll);
    printf("Time:                           %.2f s\n\n", elapsed);

    printf("--- Boundary State Deduplication ---\n");
    printf("Unique boundary states (all):   %llu\n", (unsigned long long)ht_entries);
    printf("Deduplication ratio:            %.1fx  (%.4g / %.4g)\n",
           (double)n_tested / ht_entries,
           (double)n_tested, (double)ht_entries);
    printf("log2(unique):                   %.2f  (vs log2(total)=%d)\n",
           log2((double)ht_entries), 4*N);
    printf("Bits saved by dedup:            %.1f\n\n",
           4.0*N - log2((double)ht_entries));

    /* Count collision boundary states */
    printf("--- Collision Boundary States ---\n");
    int unique_coll_bs = 0;
    for (int i = 0; i < n_coll; i++) {
        int dup = 0;
        for (int j = 0; j < i; j++) {
            if (bs_eq(coll_bs[i], coll_bs[j])) { dup = 1; break; }
        }
        if (!dup) unique_coll_bs++;
    }
    printf("Unique collision boundary states: %d / %d\n",
           unique_coll_bs, n_coll);
    printf("All collision BS unique?          %s\n",
           unique_coll_bs == n_coll ? "YES (perfect permutation)" : "NO (merging)");
    printf("Collision BS subset of full set?  YES (by construction)\n\n");

    /* Distribution analysis */
    printf("--- Configs-per-Boundary-State Distribution ---\n");
    uint64_t max_count = 0, min_count = UINT64_MAX;
    uint64_t count_1 = 0, count_le10 = 0, count_le100 = 0;
    uint64_t coll_bearing = 0;
    for (uint32_t i = 0; i < HT_SIZE; i++) {
        if (!ht[i].occupied) continue;
        uint32_t c = ht[i].count;
        if (c > max_count) max_count = c;
        if (c < min_count) min_count = c;
        if (c == 1) count_1++;
        if (c <= 10) count_le10++;
        if (c <= 100) count_le100++;
        if (ht[i].coll_count > 0) coll_bearing++;
    }
    printf("Min configs/BS:     %llu\n", (unsigned long long)min_count);
    printf("Max configs/BS:     %llu\n", (unsigned long long)max_count);
    printf("BS with count=1:    %llu (%.1f%%)\n",
           (unsigned long long)count_1, 100.0 * count_1 / ht_entries);
    printf("BS with count<=10:  %llu (%.1f%%)\n",
           (unsigned long long)count_le10, 100.0 * count_le10 / ht_entries);
    printf("BS with count<=100: %llu (%.1f%%)\n",
           (unsigned long long)count_le100, 100.0 * count_le100 / ht_entries);
    printf("Collision-bearing:  %llu (BS entries with >=1 collision)\n\n",
           (unsigned long long)coll_bearing);

    /* Collision BS sharing details */
    printf("--- Collision BS Sharing (first 10) ---\n");
    int shown = 0;
    for (int i = 0; i < n_coll && shown < 10; i++) {
        uint32_t idx = ht_hash(coll_bs[i]);
        while (!bs_eq(ht[idx].key, coll_bs[i])) idx = (idx + 1) & HT_MASK;
        printf("  Coll #%3d: W1=[%02x,%02x,%02x,%02x] BS=(0x%012llx,0x%012llx) "
               "share=%u coll_in_bs=%u\n",
               i + 1,
               coll_w1[i][0], coll_w1[i][1], coll_w1[i][2], coll_w1[i][3],
               (unsigned long long)coll_bs[i].carries_p1,
               (unsigned long long)coll_bs[i].carries_p2,
               ht[idx].count, ht[idx].coll_count);
        shown++;
    }

    /* Carry-diff analysis */
    printf("\n--- Carry-Diff at Boundary (P1 XOR P2) ---\n");
    int unique_diffs = 0;
    uint64_t diff_seen[MAX_COLL];
    for (int i = 0; i < n_coll; i++) {
        uint64_t d = coll_bs[i].carries_p1 ^ coll_bs[i].carries_p2;
        int dup = 0;
        for (int j = 0; j < unique_diffs; j++) {
            if (diff_seen[j] == d) { dup = 1; break; }
        }
        if (!dup) diff_seen[unique_diffs++] = d;
    }
    printf("Unique carry-diffs among collisions: %d\n", unique_diffs);
    if (unique_diffs <= 5) {
        for (int i = 0; i < unique_diffs; i++)
            printf("  diff[%d] = 0x%012llx  (%d bits set)\n",
                   i, (unsigned long long)diff_seen[i],
                   __builtin_popcountll(diff_seen[i]));
    }

    /* Invariant carry analysis */
    printf("\n--- Invariant Carries at Boundary (across all collisions) ---\n");
    if (n_coll > 0) {
        uint64_t all_same_p1 = ~0ULL, all_same_p2 = ~0ULL;
        uint64_t ref_p1 = coll_bs[0].carries_p1;
        uint64_t ref_p2 = coll_bs[0].carries_p2;
        for (int i = 1; i < n_coll; i++) {
            all_same_p1 &= ~(coll_bs[i].carries_p1 ^ ref_p1);
            all_same_p2 &= ~(coll_bs[i].carries_p2 ^ ref_p2);
        }
        uint64_t active_mask = (1ULL << TOTAL_ADDS) - 1;
        int inv_p1 = __builtin_popcountll(all_same_p1 & active_mask);
        int inv_p2 = __builtin_popcountll(all_same_p2 & active_mask);
        printf("Path 1: %d/%d carries invariant\n", inv_p1, TOTAL_ADDS);
        printf("Path 2: %d/%d carries invariant\n", inv_p2, TOTAL_ADDS);
        printf("Variable carries: %d (p1) + %d (p2) = %d total DOF\n",
               TOTAL_ADDS - inv_p1, TOTAL_ADDS - inv_p2,
               2 * TOTAL_ADDS - inv_p1 - inv_p2);

        /* Per-addition breakdown */
        printf("\nPer-addition invariance (across %d collisions):\n", n_coll);
        const char *add_names[ADDS_PER_ROUND] = {
            "h+Sig1(e)", "+Ch(efg)", "+K[r]", "+W[r]",
            "Sig0+Maj", "d+T1=e'", "T1+T2=a'"
        };
        printf("Round  Addition       P1-inv  P2-inv\n");
        for (int r = 0; r < ROUNDS; r++) {
            for (int a = 0; a < ADDS_PER_ROUND; a++) {
                int bit = r * ADDS_PER_ROUND + a;
                int p1_inv = (all_same_p1 >> bit) & 1;
                int p2_inv = (all_same_p2 >> bit) & 1;
                printf("  r%d   %-14s   %s      %s\n",
                       57 + r, add_names[a],
                       p1_inv ? "INV" : "var",
                       p2_inv ? "INV" : "var");
            }
        }
    }

    printf("\n=== Summary ===\n");
    printf("Deduplication effective? ");
    if (ht_entries < n_tested / 2)
        printf("YES (%.1fx compression)\n", (double)n_tested / ht_entries);
    else
        printf("MARGINAL (%.1fx compression)\n", (double)n_tested / ht_entries);
    printf("Collision BS unique?    %s\n",
           unique_coll_bs == n_coll ? "YES" : "NO");
    printf("Carry automaton width:  %d collision states in %llu total BS\n",
           n_coll, (unsigned long long)ht_entries);
    if (coll_bearing > 0)
        printf("Fraction coll-bearing:  %.6f (1 in %.0f)\n",
               (double)coll_bearing / ht_entries,
               (double)ht_entries / coll_bearing);

    free(ht);
    printf("\nDone.\n");
    return 0;
}
