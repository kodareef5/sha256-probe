/*
 * m16_mitm_forward.c — N-parameterized forward enumerator for M16-MITM milestone.
 *
 * Stage 3 of bets/block2_wang/SCALING_PLAN.md.
 *
 * Algorithm:
 *   For each (W57, W58, W59) triple at N bits:
 *     Apply cascade-1 (force da57=da58=da59=0 modular).
 *     Compute state after round 59.
 *     Emit (state_59 signature, W57, W58, W59) record to stdout / output file.
 *
 *   Output format: binary records, packed.
 *     state_59:  8 × N bits (rounded to bytes)
 *     W57, W58, W59: 3 × N bits (rounded to bytes)
 *
 *   At N=16: state_59 = 16 bytes, W57/W58/W59 = 6 bytes total → 22 bytes/record
 *            × 2^48 records = 6.6 PB. NOT TRACTABLE.
 *
 *   So this enumerator must be RESTRICTED. Use cascade-extending W2 (already in
 *   backward_construct_n10.c) to force da57 = 0 modular. This REDUCES the search
 *   space: W57 fully free, but W58 must satisfy cw58 = cascade1_offset(state_57)
 *   which has 1 modular constraint. So W58's effective freedom is N bits minus
 *   ~N/3 from cascade — net ~2N/3 free.
 *
 *   At N=16: ~2^11 effective W58 freedom × 2^16 W57 = 2^27 records × 22 bytes =
 *   ~3 GB. TRACTABLE.
 *
 *   The match phase will join on state_59 against backward enumerator records.
 *
 * Compile:
 *   gcc -O3 -mcpu=apple-m4 -mtune=apple-m4 -Xclang -fopenmp \
 *       -I/opt/homebrew/opt/libomp/include \
 *       -L/opt/homebrew/opt/libomp/lib -lomp \
 *       -o m16_mitm_forward m16_mitm_forward.c -lm
 *
 * Run:
 *   ./m16_mitm_forward 16 forward.bin
 *
 * STATUS: SOURCE ONLY — not yet validated at any N. Foundation port from
 *         q5/mitm_cascade_sr60.py + backward_construct_n10.c scaffolding.
 *         Next implementer: review + validate at N=10 first (BC reference
 *         comparison), then run at N=16.
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <omp.h>

#ifndef N_BITS
#define N_BITS 10  /* override via -DN_BITS=16 etc */
#endif
#define N N_BITS
#define MASK ((1U<<N)-1)
#define MSB (1U<<(N-1))

static int rS0[3], rS1[3], rs0[2], rs1[2], ss0, ss1;
static int scale_rot(int k32) {
    int r = (int)rint((double)k32 * N / 32.0);
    return r < 1 ? 1 : r;
}
static inline uint32_t ror_n(uint32_t x, int k) {
    k = k % N;
    return ((x >> k) | (x << (N - k))) & MASK;
}
static inline uint32_t fnS0(uint32_t a){return ror_n(a,rS0[0])^ror_n(a,rS0[1])^ror_n(a,rS0[2]);}
static inline uint32_t fnS1(uint32_t e){return ror_n(e,rS1[0])^ror_n(e,rS1[1])^ror_n(e,rS1[2]);}
static inline uint32_t fns0(uint32_t x){return ror_n(x,rs0[0])^ror_n(x,rs0[1])^((x>>ss0)&MASK);}
static inline uint32_t fns1(uint32_t x){return ror_n(x,rs1[0])^ror_n(x,rs1[1])^((x>>ss1)&MASK);}
static inline uint32_t fnCh(uint32_t e,uint32_t f,uint32_t g){return((e&f)^((~e)&g))&MASK;}
static inline uint32_t fnMj(uint32_t a,uint32_t b,uint32_t c){return((a&b)^(a&c)^(b&c))&MASK;}

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
    uint32_t a=IVN[0],b=IVN[1],c=IVN[2],d=IVN[3],e=IVN[4],f=IVN[5],g=IVN[6],h=IVN[7];
    for (int i = 0; i < 57; i++) {
        uint32_t T1 = (h + fnS1(e) + fnCh(e,f,g) + KN[i] + W[i]) & MASK;
        uint32_t T2 = (fnS0(a) + fnMj(a,b,c)) & MASK;
        h=g; g=f; f=e; e=(d+T1)&MASK; d=c; c=b; b=a; a=(T1+T2)&MASK;
    }
    st[0]=a; st[1]=b; st[2]=c; st[3]=d;
    st[4]=e; st[5]=f; st[6]=g; st[7]=h;
}

static inline void sha_round(uint32_t s[8], uint32_t k, uint32_t w) {
    uint32_t T1 = (s[7] + fnS1(s[4]) + fnCh(s[4],s[5],s[6]) + k + w) & MASK;
    uint32_t T2 = (fnS0(s[0]) + fnMj(s[0],s[1],s[2])) & MASK;
    s[7]=s[6]; s[6]=s[5]; s[5]=s[4]; s[4]=(s[3]+T1)&MASK;
    s[3]=s[2]; s[2]=s[1]; s[1]=s[0]; s[0]=(T1+T2)&MASK;
}

static inline uint32_t find_w2(const uint32_t s1[8], const uint32_t s2[8], int rnd, uint32_t w1) {
    uint32_t r1 = (s1[7] + fnS1(s1[4]) + fnCh(s1[4],s1[5],s1[6]) + KN[rnd]) & MASK;
    uint32_t r2 = (s2[7] + fnS1(s2[4]) + fnCh(s2[4],s2[5],s2[6]) + KN[rnd]) & MASK;
    uint32_t T21 = (fnS0(s1[0]) + fnMj(s1[0],s1[1],s1[2])) & MASK;
    uint32_t T22 = (fnS0(s2[0]) + fnMj(s2[0],s2[1],s2[2])) & MASK;
    return (w1 + r1 - r2 + T21 - T22) & MASK;
}

/* Compact record format: pack into byte buffer.
 *   state_59 (8 registers × ceil(N/8) bytes each)
 *   W57, W58, W59 (3 × ceil(N/8) bytes)
 * For N=10: state 8×2=16 bytes, W's 3×2=6 bytes → 22 bytes/record
 * For N=16: state 8×2=16 bytes, W's 3×2=6 bytes → 22 bytes/record
 */
static inline int bytes_per_word(void) {
    return (N + 7) / 8;
}

static inline void pack_word(unsigned char *dst, uint32_t w) {
    int bw = bytes_per_word();
    for (int i = 0; i < bw; i++) {
        dst[i] = (w >> (8 * i)) & 0xff;
    }
}

int main(int argc, char *argv[]) {
    setbuf(stdout, NULL);
    rS0[0]=scale_rot(2); rS0[1]=scale_rot(13); rS0[2]=scale_rot(22);
    rS1[0]=scale_rot(6); rS1[1]=scale_rot(11); rS1[2]=scale_rot(25);
    rs0[0]=scale_rot(7); rs0[1]=scale_rot(18); ss0=scale_rot(3);
    rs1[0]=scale_rot(17); rs1[1]=scale_rot(19); ss1=scale_rot(10);
    for (int i = 0; i < 64; i++) KN[i] = K32[i] & MASK;
    for (int i = 0; i < 8; i++)  IVN[i] = IV32[i] & MASK;

    /* Find cascade-eligible (M0, fill) */
    uint32_t M1[16], M2[16];
    uint32_t M0_chosen = 0;
    int found = 0;
    for (uint32_t cand = 0; cand <= MASK && !found; cand++) {
        for (int i = 0; i < 16; i++) { M1[i] = MASK; M2[i] = MASK; }
        M1[0] = cand; M2[0] = cand ^ MSB; M2[9] = MASK ^ MSB;
        precompute(M1, state1, W1p);
        precompute(M2, state2, W2p);
        if (state1[0] == state2[0]) { M0_chosen = cand; found = 1; }
    }
    if (!found) { fprintf(stderr, "No cascade-eligible M0 at N=%d\n", N); return 1; }
    fprintf(stderr, "N=%d, M0=0x%x, fill=0x%x\n", N, M0_chosen, MASK);

    /* Output file */
    FILE *out = (argc >= 2) ? fopen(argv[1], "wb") : stdout;
    if (!out) { perror("fopen"); return 2; }

    int bw = bytes_per_word();
    /* Record: state_59[8 words] + W57 + W58 + W59 = 11 words */
    unsigned char rec[11 * 8];  /* enough for N up to 32 */
    uint64_t emitted = 0;

    /* Forward enumeration: W57 free, W58 free, W59 free; pair-2 W's via cascade-1 */
    for (uint32_t w57 = 0; w57 < (MASK + 1U); w57++) {
        uint32_t s57a[8], s57b[8];
        memcpy(s57a, state1, 32); memcpy(s57b, state2, 32);
        uint32_t w57b = find_w2(s57a, s57b, 57, w57);
        sha_round(s57a, KN[57], w57); sha_round(s57b, KN[57], w57b);

        for (uint32_t w58 = 0; w58 < (MASK + 1U); w58++) {
            uint32_t s58a[8], s58b[8];
            memcpy(s58a, s57a, 32); memcpy(s58b, s57b, 32);
            uint32_t w58b = find_w2(s58a, s58b, 58, w58);
            sha_round(s58a, KN[58], w58); sha_round(s58b, KN[58], w58b);

            for (uint32_t w59 = 0; w59 < (MASK + 1U); w59++) {
                uint32_t s59a[8], s59b[8];
                memcpy(s59a, s58a, 32); memcpy(s59b, s58b, 32);
                uint32_t w59b = find_w2(s59a, s59b, 59, w59);
                sha_round(s59a, KN[59], w59); sha_round(s59b, KN[59], w59b);

                /* Emit record: state_59 (s59a is the "pair-1" reference; pair-2
                 * is determined by cascade) + W57, W58, W59 */
                int p = 0;
                for (int r = 0; r < 8; r++) {
                    pack_word(rec + p, s59a[r]);
                    p += bw;
                }
                pack_word(rec + p, w57); p += bw;
                pack_word(rec + p, w58); p += bw;
                pack_word(rec + p, w59); p += bw;
                if (fwrite(rec, 1, p, out) != (size_t)p) {
                    fprintf(stderr, "fwrite short at record %llu\n",
                            (unsigned long long)emitted);
                    return 3;
                }
                emitted++;
            }
        }

        if ((w57 & 0xFF) == 0xFF) {
            fprintf(stderr, "  forward[w57=%u/%u] emitted=%llu\n",
                    w57, MASK, (unsigned long long)emitted);
        }
    }

    if (out != stdout) fclose(out);
    fprintf(stderr, "Forward enumeration complete: %llu records emitted.\n",
            (unsigned long long)emitted);
    return 0;
}
