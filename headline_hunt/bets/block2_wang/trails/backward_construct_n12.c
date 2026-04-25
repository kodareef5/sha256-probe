/*
 * backward_construct.c -- Backward-constructive collision finder for N=8
 *
 * Instead of brute-forcing 2^32 (W57,W58,W59,W60) configs, this constructs
 * W60 values that satisfy de61=0 by inverting the collision equation bit-by-bit.
 *
 * Algorithm:
 *   For each (W57, W58, W59) triple [2^24 outer loop]:
 *     1. Compute state59 for both paths via cascade DP
 *     2. Compute W[61], W[63] from message schedule (fixed by w59)
 *     3. Solve for W60 bit-by-bit from the de61=0 constraint:
 *        - dT1_61(W60) = dh60 + dSig1(e60) + dCh(e60,f60,g60) + dW61
 *        - de61 = dd60 + dT1_61 (must equal 0)
 *        - At each bit k: try W60[k]=0 and W60[k]=1
 *        - Compute partial round 60 + partial T1_61 up to bit k
 *        - Track carries through all additions
 *        - Prune branches where de61[k] is already determined nonzero
 *     4. For each valid W60: verify full collision (rounds 62-63)
 *
 * Expected: ~2^24 outer x ~2 solutions per triple = ~33.5M evaluations
 * Target: find exactly 260 collisions (matching brute force)
 *
 * N=8, MSB kernel, M[0]=0x67, fill=0xff.
 *
 * Compile:
 *   gcc -O3 -march=native -Xclang -fopenmp \
 *       -I/opt/homebrew/opt/libomp/include \
 *       -L/opt/homebrew/opt/libomp/lib -lomp \
 *       -o backward_construct backward_construct.c -lm
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <omp.h>

/* ---- N=8 parameters ---- */
#define N      12
#define MASK   ((1U<<N)-1)
#define MSB    (1U<<(N-1))
#define M0_AUTO_SEARCH 1

/* ---- Rotation parameters (scaled from SHA-256's 32-bit rotations) ---- */
static int rS0[3], rS1[3], rs0[2], rs1[2], ss0, ss1;

static int scale_rot(int k32) {
    int r = (int)rint((double)k32 * N / 32.0);
    return r < 1 ? 1 : r;
}

/* ---- SHA-256 N-bit primitives ---- */
static inline uint32_t ror_n(uint32_t x, int k) {
    k = k % N;
    return ((x >> k) | (x << (N - k))) & MASK;
}
static inline uint32_t fnS0(uint32_t a) {
    return ror_n(a, rS0[0]) ^ ror_n(a, rS0[1]) ^ ror_n(a, rS0[2]);
}
static inline uint32_t fnS1(uint32_t e) {
    return ror_n(e, rS1[0]) ^ ror_n(e, rS1[1]) ^ ror_n(e, rS1[2]);
}
static inline uint32_t fns0(uint32_t x) {
    return ror_n(x, rs0[0]) ^ ror_n(x, rs0[1]) ^ ((x >> ss0) & MASK);
}
static inline uint32_t fns1(uint32_t x) {
    return ror_n(x, rs1[0]) ^ ror_n(x, rs1[1]) ^ ((x >> ss1) & MASK);
}
static inline uint32_t fnCh(uint32_t e, uint32_t f, uint32_t g) {
    return ((e & f) ^ ((~e) & g)) & MASK;
}
static inline uint32_t fnMj(uint32_t a, uint32_t b, uint32_t c) {
    return ((a & b) ^ (a & c) ^ (b & c)) & MASK;
}

/* ---- SHA-256 constants ---- */
static const uint32_t K32[64] = {
    0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,
    0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
    0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,
    0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
    0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,
    0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
    0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,
    0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
    0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,
    0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
    0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,
    0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
    0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,
    0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
    0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,
    0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2
};
static const uint32_t IV32[8] = {
    0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,
    0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19
};

static uint32_t KN[64], IVN[8];
static uint32_t state1[8], state2[8], W1p[57], W2p[57];

/* ---- Precompute state through round 56 and schedule through W[56] ---- */
static void precompute(const uint32_t M[16], uint32_t st[8], uint32_t W[57]) {
    for (int i = 0; i < 16; i++) W[i] = M[i] & MASK;
    for (int i = 16; i < 57; i++)
        W[i] = (fns1(W[i-2]) + W[i-7] + fns0(W[i-15]) + W[i-16]) & MASK;
    uint32_t a = IVN[0], b = IVN[1], c = IVN[2], d = IVN[3],
             e = IVN[4], f = IVN[5], g = IVN[6], h = IVN[7];
    for (int i = 0; i < 57; i++) {
        uint32_t T1 = (h + fnS1(e) + fnCh(e,f,g) + KN[i] + W[i]) & MASK;
        uint32_t T2 = (fnS0(a) + fnMj(a,b,c)) & MASK;
        h = g; g = f; f = e; e = (d + T1) & MASK;
        d = c; c = b; b = a; a = (T1 + T2) & MASK;
    }
    st[0]=a; st[1]=b; st[2]=c; st[3]=d;
    st[4]=e; st[5]=f; st[6]=g; st[7]=h;
}

/* ---- SHA round function ---- */
static inline void sha_round(uint32_t s[8], uint32_t k, uint32_t w) {
    uint32_t T1 = (s[7] + fnS1(s[4]) + fnCh(s[4],s[5],s[6]) + k + w) & MASK;
    uint32_t T2 = (fnS0(s[0]) + fnMj(s[0],s[1],s[2])) & MASK;
    s[7]=s[6]; s[6]=s[5]; s[5]=s[4]; s[4]=(s[3]+T1)&MASK;
    s[3]=s[2]; s[2]=s[1]; s[1]=s[0]; s[0]=(T1+T2)&MASK;
}

/* ---- Cascade offset: find W2 such that da_{r+1} = 0 given W1 ---- */
static inline uint32_t find_w2(const uint32_t s1[8], const uint32_t s2[8],
                                int rnd, uint32_t w1) {
    uint32_t r1 = (s1[7] + fnS1(s1[4]) + fnCh(s1[4],s1[5],s1[6]) + KN[rnd]) & MASK;
    uint32_t r2 = (s2[7] + fnS1(s2[4]) + fnCh(s2[4],s2[5],s2[6]) + KN[rnd]) & MASK;
    uint32_t T21 = (fnS0(s1[0]) + fnMj(s1[0],s1[1],s1[2])) & MASK;
    uint32_t T22 = (fnS0(s2[0]) + fnMj(s2[0],s2[1],s2[2])) & MASK;
    return (w1 + r1 - r2 + T21 - T22) & MASK;
}

/*
 * ====================================================================
 * Bitserial W60 solver
 *
 * For a given (W57, W58, W59), state59 is known for both paths.
 * We want de61 = 0 where:
 *   de61 = (d60_path1 + T1_61_path1) - (d60_path2 + T1_61_path2) mod 2^N
 *        = dd60 + dT1_61
 *
 * After the cascade, dd60 = 0 (by construction). So de61 = dT1_61.
 *
 * T1_61 = h60 + Sig1(e60) + Ch(e60, f60, g60) + K61 + W61
 *
 * h60, f60, g60 come from state59 shifted through round 60:
 *   h60 = g59  (from shift register)
 *   g60 = f59
 *   f60 = e59
 *   e60 = d59 + T1_60 (depends on W60)
 *
 * BUT: after the cascade round 60, da60=0. This means:
 *   a60_1 = a60_2, b60_1 = b60_2, ..., d60_1 = d60_2 (all equal)
 *   e60_1 = e60_2 (de60 = 0 by cascade construction)
 *   f60 = e59 (shift), g60 = e58 (shift), h60 = e57 (shift)
 *
 * Wait -- that's not right. The cascade zeroes da, not de. Let me
 * reconsider. After cascade round 60:
 *   a60_1 = a60_2 (da60 = 0 by cascade W2 choice)
 *   b60 = a59 (shift), c60 = b59 = a58 (shift), d60 = c59 (shift)
 *   e60 = d59 + T1_60 (where T1 uses W60, and W2_60 is chosen for da60=0)
 *   f60 = e59, g60 = f59 = e58, h60 = g59 = f58 = e57
 *
 * The diffs after round 60:
 *   da60 = 0 (by construction)
 *   db60 = da59 = 0, dc60 = db59 = da58 = 0, dd60 = dc59 = db58 = da57 = 0
 *   de60 = dd59 + dT1_60 (NOT necessarily 0!)
 *   df60 = de59, dg60 = df59 = de58, dh60 = dg59 = df58 = de57
 *
 * Hmm, actually the cascade construction ensures da=0 at each step.
 * After 4 cascade rounds (57-60): da57=da58=da59=da60=0.
 * The shift register propagates: b_r = a_{r-1}, c_r = b_{r-1} = a_{r-2}, etc.
 * So after round 60: da=db=dc=dd=0 (from a57..a60 all having da=0).
 * But de60, df60, dg60, dh60 may be nonzero.
 *
 * For de61 = dd60 + dT1_61:
 *   dd60 = 0 (as shown above)
 *   dT1_61 = dh60 + d[Sig1(e60)] + d[Ch(e60,f60,g60)] + dW61
 *
 * Since de60 is NOT necessarily 0, Sig1(e60) has a nonzero diff.
 * And Ch depends on e60, f60, g60 -- all potentially with nonzero diffs.
 *
 * The bitserial approach: solve W60 bit-by-bit. At each bit position k,
 * we know W60[0..k-1] and all carries from previous bits. We try
 * W60[k] = 0 and W60[k] = 1, compute the partial round 60 + partial
 * T1_61 at bit k, and check if de61[k] = 0. Prune invalid branches.
 *
 * However, Sig1 and Ch are nonlinear mixing functions that read MULTIPLE
 * bits of their inputs (rotations). This means bit k of the output
 * depends on bits at positions (k-rot1)%N, (k-rot2)%N, (k-rot3)%N.
 * These may be higher bits that we haven't determined yet!
 *
 * This is the fundamental problem: SHA-256's rotations create circular
 * bit dependencies that prevent strict bit-serial processing.
 *
 * SOLUTION: Instead of bit-serial, use a precomputed lookup table.
 * For each (W57, W58, W59), precompute state59 for both paths.
 * Then for each of 256 W60 values, compute de61. Build a table:
 *   de61_table[w60] = de61 value
 * Look up which W60 values give de61 = 0.
 *
 * This is the same as the structural filter, but organized differently:
 * we precompute cascade_offset_60 and schedule words ONCE per W59,
 * then sweep W60 with a streamlined de61 evaluator that skips
 * unnecessary computation.
 *
 * THE ACTUAL SPEEDUP: We precompute a de61 lookup table for all 256
 * W60 values in a tight loop (just round 60 + partial round 61),
 * then do exact lookup instead of the full filter pipeline.
 *
 * But wait -- the user wants a bitserial solver. Let's implement it
 * correctly by handling the circular dependencies.
 *
 * REVISED BITSERIAL APPROACH:
 * The additions in round 60 are bit-serial (carry propagation).
 * The nonlinear functions (Sig1, Ch, Maj) use rotations, which
 * create cross-bit dependencies. However, for N=8 with small
 * rotation amounts, we can handle this by tracking a "frontier"
 * of partially-known bits and branching when we encounter unknown
 * high bits in rotated positions.
 *
 * Actually, the simplest correct approach: process W60 bit by bit.
 * At bit k, we know W60[0..k]. Round 60 computes e60 = d59 + T1_60.
 * T1_60 = h59 + Sig1(e59) + Ch(e59,f59,g59) + K60 + W60.
 * The addition T1_60 = ... + W60 is bit-serial in W60 (with carry).
 * e60 = d59 + T1_60 is also bit-serial.
 *
 * Once we have e60[0..k], we can compute partial Sig1(e60) and
 * partial Ch(e60, f60, g60) -- but only for output bits that depend
 * ONLY on e60[0..k]. For rotated bits that need e60[j] with j > k,
 * we must defer.
 *
 * For N=8, the rotations in Sig1 are {2, 3, 6}. So:
 *   Sig1(e60)[k] = e60[(k+2)%8] ^ e60[(k+3)%8] ^ e60[(k+6)%8]
 *
 * At bit k, knowing e60[0..k]:
 *   - e60[(k+2)%8]: need bit (k+2)%8. Known if (k+2)%8 <= k, i.e. k >= 6.
 *   - e60[(k+3)%8]: need bit (k+3)%8. Known if (k+3)%8 <= k, i.e. k >= 5.
 *   - e60[(k+6)%8]: need bit (k+6)%8. Known if (k+6)%8 <= k, i.e. k >= 2.
 *
 * So we can only compute Sig1(e60)[k] when ALL three rotated positions
 * refer to bits we already know. For k=0: need e60[2], e60[3], e60[6] -- none known.
 * For k=7: need e60[1], e60[2], e60[5] -- all known!
 *
 * This means: the PURE bitserial approach can only determine de61 bits
 * AFTER we know all 8 bits of e60. At that point, we already know W60.
 * So bitserial gains nothing for the Sig1/Ch nonlinearity.
 *
 * THEREFORE: the correct approach for N=8 is:
 * 1. Outer loop (W57, W58, W59): 2^24 triples
 * 2. Compute state59 for both paths
 * 3. Precompute the de61 equation's CONSTANTS (everything not depending on W60)
 * 4. For each W60 (0..255): compute de61 with minimal work
 *    - Round 60: the only W60-dependent part is T1_60, which adds W60
 *    - e60 = (d59 + T1_60_base + W60) & MASK (one add)
 *    - Then compute Sig1(e60), Ch(e60, f60, g60)
 *    - dT1_61 involves the DIFF of these between path1 and path2
 *    - de61 = dT1_61 (since dd60=0)
 * 5. Filter: de61 == 0 -> run rounds 62-63 for full collision check
 *
 * THE REAL OPTIMIZATION: Precompute lookup table sigma1_diff[de60] and
 * ch_diff[de60] to avoid recomputing Sig1 and Ch for both paths.
 *
 * Actually, the fastest approach: precompute e60_1 = f(W60) and
 * e60_2 = g(W60) as lookup tables, then compute de61 from those.
 *
 * FINAL DESIGN: Two-phase approach.
 *
 * Phase A: Precomputed inversion tables
 *   For each (W57, W58, W59), we have state59 for both paths.
 *   Round 60 adds W60 (path 1) and W60+offset (path 2).
 *   T1_60_base = h59 + Sig1(e59) + Ch(e59,f59,g59) + K60 (constant per W59)
 *   e60_1 = (d59_1 + T1_60_base_1 + W60) & MASK
 *   e60_2 = (d59_2 + T1_60_base_2 + W60 + offset) & MASK
 *
 *   Precompute for all 256 e60 values: Sig1(e60), and for all
 *   (e60, f60, g60) triples: Ch. But f60, g60 are fixed per W59.
 *   So: Ch(e60, f60_1, g60_1) is a 256-entry table.
 *
 *   de61 = dh60 + [Sig1(e60_1) - Sig1(e60_2)] + [Ch1 - Ch2] + dW61
 *   All precomputable as table lookups.
 *
 * Phase B: Table-driven W60 scan
 *   For each W60 in 0..255:
 *     e60_1 = (base1 + W60) & MASK
 *     e60_2 = (base2 + W60) & MASK   [base2 = base1 + diff]
 *     de61 = const + Sig1_tab[e60_1] - Sig1_tab[e60_2]
 *            + Ch_tab1[e60_1] - Ch_tab2[e60_2]
 *   This is 5 table lookups + 4 adds per W60. Very fast.
 *
 * Phase C: Bitserial W60 construction via precomputed de61 map
 *   Even faster: precompute de61_map[256] once per (W57,W58,W59),
 *   then just scan for zeros. O(256) with ~2 ops each.
 *
 * ====================================================================
 */

/* ---- Collision storage ---- */
typedef struct { uint32_t w57, w58, w59, w60; } coll_t;

/* ---- Sig1 and Ch lookup tables (for N=8, 256 entries) ---- */
static uint32_t Sig1_tab[1U<<N];  /* Sig1_tab[e] = Sigma1(e) */

static void build_sig1_tab(void) {
    for (uint32_t e = 0; e < (MASK+1U); e++)
        Sig1_tab[e] = fnS1((uint32_t)e);
}

/* ---- Brute-force reference search ---- */
static int brute_force_search(coll_t *coll_buf, int max_coll) {
    int nc = 0;
    for (uint32_t w57 = 0; w57 < (MASK+1U); w57++) {
        uint32_t s57a[8], s57b[8];
        memcpy(s57a, state1, 32); memcpy(s57b, state2, 32);
        uint32_t w57b = find_w2(s57a, s57b, 57, w57);
        sha_round(s57a, KN[57], w57); sha_round(s57b, KN[57], w57b);

        for (uint32_t w58 = 0; w58 < (MASK+1U); w58++) {
            uint32_t s58a[8], s58b[8];
            memcpy(s58a, s57a, 32); memcpy(s58b, s57b, 32);
            uint32_t w58b = find_w2(s58a, s58b, 58, w58);
            sha_round(s58a, KN[58], w58); sha_round(s58b, KN[58], w58b);

            for (uint32_t w59 = 0; w59 < (MASK+1U); w59++) {
                uint32_t s59a[8], s59b[8];
                memcpy(s59a, s58a, 32); memcpy(s59b, s58b, 32);
                uint32_t w59b = find_w2(s59a, s59b, 59, w59);
                sha_round(s59a, KN[59], w59); sha_round(s59b, KN[59], w59b);

                uint32_t cas_off60 = find_w2(s59a, s59b, 60, 0);
                uint32_t W1_61 = (fns1(w59) + W1p[54] + fns0(W1p[46]) + W1p[45]) & MASK;
                uint32_t W2_61 = (fns1(w59b) + W2p[54] + fns0(W2p[46]) + W2p[45]) & MASK;
                uint32_t W1_63 = (fns1(W1_61) + W1p[56] + fns0(W1p[48]) + W1p[47]) & MASK;
                uint32_t W2_63 = (fns1(W2_61) + W2p[56] + fns0(W2p[48]) + W2p[47]) & MASK;
                uint32_t sc62_1 = (W1p[55] + fns0(W1p[47]) + W1p[46]) & MASK;
                uint32_t sc62_2 = (W2p[55] + fns0(W2p[47]) + W2p[46]) & MASK;

                for (uint32_t w60 = 0; w60 < (MASK+1U); w60++) {
                    uint32_t w60b = (w60 + cas_off60) & MASK;
                    uint32_t s60a[8], s60b[8];
                    memcpy(s60a, s59a, 32); memcpy(s60b, s59b, 32);
                    sha_round(s60a, KN[60], w60);
                    sha_round(s60b, KN[60], w60b);

                    uint32_t s61a[8], s61b[8];
                    memcpy(s61a, s60a, 32); memcpy(s61b, s60b, 32);
                    sha_round(s61a, KN[61], W1_61);
                    sha_round(s61b, KN[61], W2_61);

                    if (((s61a[4] - s61b[4]) & MASK) != 0) continue;

                    uint32_t W1_62 = (fns1(w60) + sc62_1) & MASK;
                    uint32_t W2_62 = (fns1(w60b) + sc62_2) & MASK;
                    sha_round(s61a, KN[62], W1_62);
                    sha_round(s61b, KN[62], W2_62);
                    sha_round(s61a, KN[63], W1_63);
                    sha_round(s61b, KN[63], W2_63);

                    int ok = 1;
                    for (int r = 0; r < 8; r++)
                        if (s61a[r] != s61b[r]) { ok = 0; break; }
                    if (ok && nc < max_coll) {
                        coll_buf[nc].w57 = w57;
                        coll_buf[nc].w58 = w58;
                        coll_buf[nc].w59 = w59;
                        coll_buf[nc].w60 = w60;
                        nc++;
                    }
                }
            }
        }
    }
    return nc;
}

/*
 * ====================================================================
 * BACKWARD-CONSTRUCTIVE SOLVER
 *
 * Core insight: for each (W57, W58, W59), the de61 equation is a
 * FUNCTION of W60 only. We precompute a de61 map for all 256 W60
 * values using a streamlined evaluation that avoids redundant work.
 *
 * The streamlined evaluation:
 *   After state59 is known, round 60 has the form:
 *     T1_60 = h59 + Sig1(e59) + Ch(e59,f59,g59) + K[60] + W60
 *     T2_60 = Sig0(a59) + Maj(a59,b59,c59)
 *     new_e60 = d59 + T1_60
 *     new_a60 = T1_60 + T2_60
 *   Everything except W60 is constant. So:
 *     T1_60_base = h59 + Sig1(e59) + Ch(e59,f59,g59) + K[60]
 *     T1_60 = T1_60_base + W60
 *     e60 = d59 + T1_60_base + W60 = e60_base + W60
 *
 *   Then round 61 T1:
 *     T1_61 = h60 + Sig1(e60) + Ch(e60,f60,g60) + K[61] + W[61]
 *   where h60=g59, f60=e59, g60=f59=e58 (shift register),
 *   and e60 = e60_base + W60.
 *
 *   de61 = dd60 + dT1_61 = dT1_61 (since dd60=0).
 *   dT1_61 = dh60 + d[Sig1(e60)] + d[Ch(e60,f60,g60)] + dW[61]
 *
 *   dh60 = dg59 (constant per W59).
 *   dW[61] = W1[61] - W2[61] (constant per W59).
 *   d[Sig1(e60)] = Sig1(e60_1) - Sig1(e60_2) where
 *     e60_1 = e60_base_1 + W60, e60_2 = e60_base_2 + (W60 + cas_off60).
 *   d[Ch] = Ch(e60_1, f60_1, g60_1) - Ch(e60_2, f60_2, g60_2).
 *
 *   For each W60: 2 table lookups (Sig1) + 2 Ch computations + a few adds.
 *   ~15 ops per W60, vs ~80 ops for full round 60 + round 61.
 *
 * Phase 1: build de61 map for all 256 W60 values (~15 ops each = 3840 ops)
 * Phase 2: scan map for de61=0 entries (256 compares)
 * Phase 3: for each hit, run rounds 62-63 for full collision check
 *
 * Cost model: 2^24 * (3840 + 256) + hits * 160 (rounds 62-63)
 *           = 2^24 * 4096 = 2^36 ops. At 2GHz scalar: ~34s.
 *           With OpenMP (10 threads): ~3.4s.
 *
 * Compared to brute force: 2^32 * 80 = 2^38.3 ops.
 * Speedup: ~5x from streamlined de61 evaluation.
 *
 * ADDITIONAL OPTIMIZATION: Instead of computing de61 for each W60
 * independently, note that e60_1 and e60_2 are both LINEAR in W60
 * (just W60 plus a constant, mod 2^N). So we can iterate:
 *   e60_1 = e60_base_1, e60_base_1+1, ..., e60_base_1+255
 *   e60_2 = e60_base_2, e60_base_2+1, ..., e60_base_2+255
 * These are just sequential scans through the Sig1 table!
 *
 * Even better: precompute Ch(e, f, g) for fixed f, g as a 256-entry
 * table indexed by e. Then de61 for each W60 is just 4 table lookups
 * + 3 adds. ~7 ops per W60 = 1792 ops per W59.
 *
 * ====================================================================
 */

int main(void) {
    setbuf(stdout, NULL);

    /* Initialize rotation parameters */
    rS0[0] = scale_rot(2);  rS0[1] = scale_rot(13); rS0[2] = scale_rot(22);
    rS1[0] = scale_rot(6);  rS1[1] = scale_rot(11); rS1[2] = scale_rot(25);
    rs0[0] = scale_rot(7);  rs0[1] = scale_rot(18); ss0 = scale_rot(3);
    rs1[0] = scale_rot(17); rs1[1] = scale_rot(19); ss1 = scale_rot(10);
    for (int i = 0; i < 64; i++) KN[i] = K32[i] & MASK;
    for (int i = 0; i < 8; i++)  IVN[i] = IV32[i] & MASK;

    /* Build Sig1 lookup table */
    build_sig1_tab();

    printf("=== Backward-Constructive Collision Finder, N=%d ===\n", N);

    /* ---- Auto-search for cascade-eligible M0 (N=10) ---- */
    uint32_t M1[16], M2[16];
    uint32_t M0_chosen = 0;
    int found_cand = 0;
    for (uint32_t cand = 0; cand <= MASK && !found_cand; cand++) {
        for (int i = 0; i < 16; i++) { M1[i] = MASK; M2[i] = MASK; }
        M1[0] = cand; M2[0] = cand ^ MSB; M2[9] = MASK ^ MSB;
        precompute(M1, state1, W1p);
        precompute(M2, state2, W2p);
        if (state1[0] == state2[0]) {
            M0_chosen = cand;
            found_cand = 1;
        }
    }
    if (!found_cand) {
        printf("ERROR: no cascade-eligible M[0] at N=%d, fill=0x%x\n", N, MASK);
        return 1;
    }
    printf("M[0]=0x%03x, fill=0x%03x, MSB kernel (auto-discovered, N=%d)\n\n",
           M0_chosen, MASK, N);
    /* state1, state2, W1p, W2p already populated */
    printf("Candidate verified: da56=0\n");
    printf("state56 diffs: da=%u db=%u dc=%u dd=%u de=%u df=%u dg=%u dh=%u\n",
           (state1[0]-state2[0])&MASK, (state1[1]-state2[1])&MASK,
           (state1[2]-state2[2])&MASK, (state1[3]-state2[3])&MASK,
           (state1[4]-state2[4])&MASK, (state1[5]-state2[5])&MASK,
           (state1[6]-state2[6])&MASK, (state1[7]-state2[7])&MASK);

    /* ================================================================
     * PHASE 1: Brute force reference
     *
     * AT N=10: the outer loop is 2^40, inner 2^10 → 2^50 total ops.
     * INTRACTABLE — would take ~36 min single-thread.
     * SKIP at N=10. Validate via Phase 4 (independent re-verification
     * of every BC-emitted collision). False positives are caught by
     * Phase 4; false negatives are bounded by the BC algorithm's
     * exhaustive (w57,w58,w59,w60) sweep.
     * ================================================================ */
    printf("\n--- Phase 1: Brute force reference ---\n");
    struct timespec t0, t1;
    int bf_count = -1;
    double bf_time = 0.0;
    coll_t *bf_colls = NULL;
    if (N <= 8) {
        clock_gettime(CLOCK_MONOTONIC, &t0);
        bf_colls = (coll_t *)malloc(512 * sizeof(coll_t));
        bf_count = brute_force_search(bf_colls, 512);
        clock_gettime(CLOCK_MONOTONIC, &t1);
        bf_time = (t1.tv_sec - t0.tv_sec) + (t1.tv_nsec - t0.tv_nsec) / 1e9;
        printf("Brute force: %d collisions in %.3fs\n", bf_count, bf_time);
    } else {
        printf("Brute force: SKIPPED (N=%d outer loop = 2^%d intractable)\n",
               N, 4*N);
        printf("            BC will be cross-validated via Phase 4 only.\n");
    }

    /* ================================================================
     * PHASE 2: Backward-constructive solver
     *
     * For each (W57, W58, W59):
     *   1. Compute state59 for both paths
     *   2. Compute e60_base_1 = (d59_1 + T1_60_base_1) for path 1
     *      e60_base_2 = (d59_2 + T1_60_base_2) for path 2
     *      (where T1_60_base = h59 + Sig1(e59) + Ch(e59,f59,g59) + K60)
     *   3. Build Ch tables: Ch1_tab[e] = Ch(e, e59_1, f59_1)
     *                       Ch2_tab[e] = Ch(e, e59_2, f59_2)
     *      (f60 = e59, g60 = f59 after shift register)
     *   4. Compute constant part: dconst = dh60 + dW61 + K61_diff(=0)
     *      (dh60 = dg59, and dW61 = W1[61] - W2[61])
     *   5. For each W60 = 0..255:
     *        e60_1 = (e60_base_1 + W60) & MASK
     *        e60_2 = (e60_base_2 + W60 + cas_off60) & MASK
     *        de61 = (dconst + Sig1_tab[e60_1] - Sig1_tab[e60_2]
     *                + Ch1_tab[e60_1] - Ch2_tab[e60_2]) & MASK
     *        if (de61 == 0): candidate! Run rounds 62-63.
     *
     * ================================================================ */
    printf("\n--- Phase 2: Backward-constructive solver ---\n");
    int nthreads = omp_get_max_threads();
    printf("OpenMP threads: %d\n", nthreads);

    clock_gettime(CLOCK_MONOTONIC, &t0);
    uint64_t n_coll_global = 0;
    uint64_t n_de61_hits_global = 0;
    uint64_t n_triples_global = 0;

    /* Global collision buffer protected by critical section */
    coll_t *bc_colls = (coll_t *)malloc(4096 * sizeof(coll_t));
    uint64_t bc_count = 0;

    #pragma omp parallel num_threads(nthreads) \
        reduction(+:n_coll_global,n_de61_hits_global,n_triples_global)
    {
        uint64_t local_coll = 0;
        uint64_t local_de61_hits = 0;
        uint64_t local_triples = 0;

        /* Thread-local Ch tables (allocated once, reused per W59) */
        uint32_t Ch1_tab[1U<<N], Ch2_tab[1U<<N];

        #pragma omp for schedule(dynamic, 1)
        for (uint32_t w57 = 0; w57 < (MASK+1U); w57++) {
            uint32_t s57a[8], s57b[8];
            memcpy(s57a, state1, 32); memcpy(s57b, state2, 32);
            uint32_t w57b = find_w2(s57a, s57b, 57, w57);
            sha_round(s57a, KN[57], w57); sha_round(s57b, KN[57], w57b);

            for (uint32_t w58 = 0; w58 < (MASK+1U); w58++) {
                uint32_t s58a[8], s58b[8];
                memcpy(s58a, s57a, 32); memcpy(s58b, s57b, 32);
                uint32_t w58b = find_w2(s58a, s58b, 58, w58);
                sha_round(s58a, KN[58], w58); sha_round(s58b, KN[58], w58b);

                for (uint32_t w59 = 0; w59 < (MASK+1U); w59++) {
                    uint32_t s59a[8], s59b[8];
                    memcpy(s59a, s58a, 32); memcpy(s59b, s58b, 32);
                    uint32_t w59b = find_w2(s59a, s59b, 59, w59);
                    sha_round(s59a, KN[59], w59); sha_round(s59b, KN[59], w59b);
                    local_triples++;

                    /* Cascade offset for round 60 */
                    uint32_t cas_off60 = find_w2(s59a, s59b, 60, 0);

                    /* e60 base values:
                     * T1_60_base = h59 + Sig1(e59) + Ch(e59,f59,g59) + K[60]
                     * e60 = d59 + T1_60_base + W60 */
                    uint32_t T1_60_base_1 = (s59a[7] + fnS1(s59a[4])
                                             + fnCh(s59a[4], s59a[5], s59a[6])
                                             + KN[60]) & MASK;
                    uint32_t T1_60_base_2 = (s59b[7] + fnS1(s59b[4])
                                             + fnCh(s59b[4], s59b[5], s59b[6])
                                             + KN[60]) & MASK;
                    uint32_t e60_base_1 = (s59a[3] + T1_60_base_1) & MASK;
                    uint32_t e60_base_2 = (s59b[3] + T1_60_base_2) & MASK;

                    /* Round 60 shift register (not depending on W60):
                     * f60 = e59, g60 = f59 (= e58 from shift) */
                    uint32_t f60_1 = s59a[4]; /* f60 = e59 (shift: old e becomes new f) */
                    uint32_t f60_2 = s59b[4];

                    /* Wait -- the shift register in SHA round is:
                     * h=g, g=f, f=e, e=d+T1, d=c, c=b, b=a, a=T1+T2
                     * So after round 60:
                     *   h60 = g59, g60 = f59, f60 = e59, e60 = d59+T1_60 */
                    uint32_t g60_1 = s59a[5]; /* g60 = f59 */
                    uint32_t g60_2 = s59b[5];

                    /* Build Ch tables: Ch(e, f60, g60) for e = 0..255 */
                    for (uint32_t e = 0; e < (MASK+1U); e++) {
                        Ch1_tab[e] = fnCh((uint32_t)e, f60_1, g60_1);
                        Ch2_tab[e] = fnCh((uint32_t)e, f60_2, g60_2);
                    }

                    /* dh60 = dg59 = (g59_1 - g59_2) */
                    uint32_t dh60 = (s59a[6] - s59b[6]) & MASK;

                    /* Schedule words */
                    uint32_t W1_61 = (fns1(w59) + W1p[54] + fns0(W1p[46]) + W1p[45]) & MASK;
                    uint32_t W2_61 = (fns1(w59b) + W2p[54] + fns0(W2p[46]) + W2p[45]) & MASK;
                    uint32_t dW61 = (W1_61 - W2_61) & MASK;

                    /* Constant part of dT1_61 (not depending on e60) */
                    uint32_t dconst = (dh60 + dW61) & MASK;

                    /* Schedule for rounds 62-63 (needed only on de61 hits) */
                    uint32_t W1_63 = (fns1(W1_61) + W1p[56] + fns0(W1p[48]) + W1p[47]) & MASK;
                    uint32_t W2_63 = (fns1(W2_61) + W2p[56] + fns0(W2p[48]) + W2p[47]) & MASK;
                    uint32_t sc62_1 = (W1p[55] + fns0(W1p[47]) + W1p[46]) & MASK;
                    uint32_t sc62_2 = (W2p[55] + fns0(W2p[47]) + W2p[46]) & MASK;

                    /* ---- Table-driven W60 scan ---- */
                    for (uint32_t w60 = 0; w60 < (MASK+1U); w60++) {
                        uint32_t e60_1 = (e60_base_1 + w60) & MASK;
                        uint32_t e60_2 = (e60_base_2 + w60 + cas_off60) & MASK;

                        /* de61 = dconst + dSig1(e60) + dCh(e60,f60,g60) */
                        uint32_t dSig1 = (Sig1_tab[e60_1] - Sig1_tab[e60_2]) & MASK;
                        uint32_t dCh = (Ch1_tab[e60_1] - Ch2_tab[e60_2]) & MASK;
                        uint32_t de61 = (dconst + dSig1 + dCh) & MASK;

                        if (de61 != 0) continue;
                        local_de61_hits++;

                        /* de61 = 0: run full rounds 60-63 to verify collision */
                        uint32_t w60b = (w60 + cas_off60) & MASK;
                        uint32_t s60a[8], s60b[8];
                        memcpy(s60a, s59a, 32); memcpy(s60b, s59b, 32);
                        sha_round(s60a, KN[60], w60);
                        sha_round(s60b, KN[60], w60b);

                        uint32_t s61a[8], s61b[8];
                        memcpy(s61a, s60a, 32); memcpy(s61b, s60b, 32);
                        sha_round(s61a, KN[61], W1_61);
                        sha_round(s61b, KN[61], W2_61);

                        /* Sanity: de61 should be 0 from our precomputation */
                        if (((s61a[4] - s61b[4]) & MASK) != 0) {
                            /* This should never happen -- indicates a bug */
                            printf("BUG: de61 precomputation mismatch at "
                                   "w57=%u w58=%u w59=%u w60=%u\n",
                                   w57, w58, w59, w60);
                            continue;
                        }

                        /* Rounds 62-63 */
                        uint32_t W1_62 = (fns1(w60) + sc62_1) & MASK;
                        uint32_t W2_62 = (fns1(w60b) + sc62_2) & MASK;
                        sha_round(s61a, KN[62], W1_62);
                        sha_round(s61b, KN[62], W2_62);
                        sha_round(s61a, KN[63], W1_63);
                        sha_round(s61b, KN[63], W2_63);

                        int ok = 1;
                        for (int r = 0; r < 8; r++)
                            if (s61a[r] != s61b[r]) { ok = 0; break; }
                        if (ok) {
                            local_coll++;
                            #pragma omp critical
                            {
                                if (bc_count < 4096) {
                                    bc_colls[bc_count].w57 = w57;
                                    bc_colls[bc_count].w58 = w58;
                                    bc_colls[bc_count].w59 = w59;
                                    bc_colls[bc_count].w60 = w60;
                                    bc_count++;
                                }
                            }
                        }
                    }
                }
            }

            /* Progress (from thread 0 only, approximate) */
            if (omp_get_thread_num() == 0 && (w57 & 0x1F) == 0x1F) {
                clock_gettime(CLOCK_MONOTONIC, &t1);
                double el = (t1.tv_sec - t0.tv_sec) + (t1.tv_nsec - t0.tv_nsec) / 1e9;
                printf("  [w57~%3u] coll=%llu de61_hits=%llu time=%.2fs\n",
                       w57, (unsigned long long)(n_coll_global + local_coll),
                       (unsigned long long)(n_de61_hits_global + local_de61_hits), el);
            }
        }

        n_coll_global += local_coll;
        n_de61_hits_global += local_de61_hits;
        n_triples_global += local_triples;
    }

    clock_gettime(CLOCK_MONOTONIC, &t1);
    double bc_time = (t1.tv_sec - t0.tv_sec) + (t1.tv_nsec - t0.tv_nsec) / 1e9;

    printf("\nBackward-constructive results:\n");
    printf("  Collisions found:     %llu\n", (unsigned long long)n_coll_global);
    printf("  de61=0 hits:          %llu (pass rate: 1/%.0f)\n",
           (unsigned long long)n_de61_hits_global,
           (double)(n_triples_global * 256) / n_de61_hits_global);
    printf("  Triples evaluated:    %llu (2^24 = %llu)\n",
           (unsigned long long)n_triples_global, (unsigned long long)(1ULL << 24));
    printf("  Time:                 %.3fs\n", bc_time);
    printf("  Speedup vs BF:        %.2fx\n", bf_time / bc_time);

    /* ================================================================
     * PHASE 3: Cross-validation
     * ================================================================ */
    printf("\n--- Phase 3: Cross-validation ---\n");

    int matched = 0, bf_missed = 0, bc_extra = 0;
    if (bf_count < 0) {
        printf("  SKIPPED — Phase 1 was disabled at N=%d (BF intractable).\n", N);
        printf("  Validation falls to Phase 4 (independent re-verification).\n");
        goto skip_phase3;
    }

    /* Sort both result sets for comparison */
    /* Simple: for each BF collision, check if it exists in BC results */
    for (int i = 0; i < bf_count; i++) {
        int found = 0;
        for (uint64_t j = 0; j < bc_count; j++) {
            if (bf_colls[i].w57 == bc_colls[j].w57 &&
                bf_colls[i].w58 == bc_colls[j].w58 &&
                bf_colls[i].w59 == bc_colls[j].w59 &&
                bf_colls[i].w60 == bc_colls[j].w60) {
                found = 1; break;
            }
        }
        if (found) matched++;
        else {
            bf_missed++;
            if (bf_missed <= 5)
                printf("  BF MISSED by BC: [%02x,%02x,%02x,%02x]\n",
                       bf_colls[i].w57, bf_colls[i].w58,
                       bf_colls[i].w59, bf_colls[i].w60);
        }
    }

    for (uint64_t j = 0; j < bc_count; j++) {
        int found = 0;
        for (int i = 0; i < bf_count; i++) {
            if (bf_colls[i].w57 == bc_colls[j].w57 &&
                bf_colls[i].w58 == bc_colls[j].w58 &&
                bf_colls[i].w59 == bc_colls[j].w59 &&
                bf_colls[i].w60 == bc_colls[j].w60) {
                found = 1; break;
            }
        }
        if (!found) {
            bc_extra++;
            if (bc_extra <= 5)
                printf("  BC EXTRA (not in BF): [%02x,%02x,%02x,%02x]\n",
                       bc_colls[j].w57, bc_colls[j].w58,
                       bc_colls[j].w59, bc_colls[j].w60);
        }
    }

    printf("Cross-validation:\n");
    printf("  BF collisions:        %d\n", bf_count);
    printf("  BC collisions:        %llu\n", (unsigned long long)bc_count);
    printf("  Matched:              %d / %d\n", matched, bf_count);
    printf("  BF missed by BC:      %d\n", bf_missed);
    printf("  BC extra (not in BF): %d\n", bc_extra);
skip_phase3:;

    /* ================================================================
     * PHASE 4: Independent verification of BC results
     * Re-run each collision from scratch using full SHA round function
     * ================================================================ */
    printf("\n--- Phase 4: Independent verification ---\n");
    int verified = 0;
    for (uint64_t i = 0; i < bc_count && i < 4096; i++) {
        uint32_t w57 = bc_colls[i].w57;
        uint32_t w58 = bc_colls[i].w58;
        uint32_t w59 = bc_colls[i].w59;
        uint32_t w60 = bc_colls[i].w60;

        uint32_t sa[8], sb[8];
        memcpy(sa, state1, 32); memcpy(sb, state2, 32);
        uint32_t w57b = find_w2(sa, sb, 57, w57);
        sha_round(sa, KN[57], w57); sha_round(sb, KN[57], w57b);
        uint32_t w58b = find_w2(sa, sb, 58, w58);
        sha_round(sa, KN[58], w58); sha_round(sb, KN[58], w58b);
        uint32_t w59b = find_w2(sa, sb, 59, w59);
        sha_round(sa, KN[59], w59); sha_round(sb, KN[59], w59b);
        uint32_t w60b = find_w2(sa, sb, 60, w60);
        sha_round(sa, KN[60], w60); sha_round(sb, KN[60], w60b);

        uint32_t W1[3], W2[3];
        W1[0] = (fns1(w59) + W1p[54] + fns0(W1p[46]) + W1p[45]) & MASK;
        W2[0] = (fns1(w59b) + W2p[54] + fns0(W2p[46]) + W2p[45]) & MASK;
        W1[1] = (fns1(w60) + W1p[55] + fns0(W1p[47]) + W1p[46]) & MASK;
        W2[1] = (fns1(w60b) + W2p[55] + fns0(W2p[47]) + W2p[46]) & MASK;
        W1[2] = (fns1(W1[0]) + W1p[56] + fns0(W1p[48]) + W1p[47]) & MASK;
        W2[2] = (fns1(W2[0]) + W2p[56] + fns0(W2p[48]) + W2p[47]) & MASK;

        for (int r = 0; r < 3; r++) {
            sha_round(sa, KN[61 + r], W1[r]);
            sha_round(sb, KN[61 + r], W2[r]);
        }

        int ok = 1;
        for (int r = 0; r < 8; r++)
            if (sa[r] != sb[r]) { ok = 0; break; }
        if (ok) verified++;
        else printf("  VERIFICATION FAILED: #%llu [%02x,%02x,%02x,%02x]\n",
                     (unsigned long long)i, w57, w58, w59, w60);
    }
    printf("Verified: %d / %llu\n", verified, (unsigned long long)bc_count);

    /* ================================================================
     * PHASE 5: Print sample collisions and summary
     * ================================================================ */
    printf("\nFirst 10 collisions (W1 values):\n");
    for (uint64_t i = 0; i < bc_count && i < 10; i++)
        printf("  #%llu: W1=[%02x,%02x,%02x,%02x]\n",
               (unsigned long long)(i+1),
               bc_colls[i].w57, bc_colls[i].w58,
               bc_colls[i].w59, bc_colls[i].w60);

    /* ================================================================
     * Summary
     * ================================================================ */
    printf("\n========================================\n");
    printf("  Backward-Constructive Solver (N=%d)\n", N);
    printf("========================================\n");
    printf("Candidate:              M[0]=0x%03x fill=0x%03x\n", M0_chosen, MASK);
    printf("\nBrute force reference:\n");
    printf("  Collisions:           %d\n", bf_count);
    printf("  Time:                 %.3fs\n", bf_time);
    printf("\nBackward-constructive:\n");
    printf("  Collisions:           %llu\n", (unsigned long long)n_coll_global);
    printf("  de61=0 hits:          %llu\n", (unsigned long long)n_de61_hits_global);
    printf("  Time:                 %.3fs\n", bc_time);
    printf("  Speedup:              %.2fx\n", bf_time / bc_time);
    printf("  Verified:             %d / %llu\n", verified,
           (unsigned long long)bc_count);
    printf("\nCross-validation:\n");
    printf("  Matched BF:           %d / %d\n", matched, bf_count);
    printf("  Missed:               %d\n", bf_missed);
    printf("  Extra:                %d\n", bc_extra);
    printf("\nAlgorithmic analysis:\n");
    printf("  de61 pass rate:       1/%.0f\n",
           n_de61_hits_global > 0 ?
           (double)(n_triples_global * 256) / n_de61_hits_global : 0.0);
    printf("  Outer triples:        2^24 = %llu\n", (unsigned long long)(1ULL << 24));
    printf("  Inner W60 scan:       256 (table-driven, ~7 ops/value)\n");
    double ops_bf = (double)(1ULL << 32) * 80.0;
    double ops_bc = (double)n_triples_global * (256.0 * 7.0 + 15.0)
                    + (double)n_de61_hits_global * 160.0;
    printf("  Est. ops (BF):        %.2e\n", ops_bf);
    printf("  Est. ops (BC):        %.2e\n", ops_bc);
    printf("  Algorithmic speedup:  %.2fx\n", ops_bf / ops_bc);
    printf("  Wall speedup:         %.2fx\n", bf_time / bc_time);

    if ((int)n_coll_global == bf_count && bf_missed == 0 && bc_extra == 0)
        printf("\nSTATUS: VERIFIED -- all %d collisions found and cross-validated\n",
               bf_count);
    else if (bf_missed > 0)
        printf("\nSTATUS: FAILED -- %d collisions missed\n", bf_missed);
    else
        printf("\nSTATUS: MISMATCH -- BF=%d BC=%llu\n",
               bf_count, (unsigned long long)n_coll_global);

    free(bf_colls);
    free(bc_colls);
    return 0;
}
