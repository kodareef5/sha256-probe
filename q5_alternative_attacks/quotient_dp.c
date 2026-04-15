/*
 * quotient_dp.c — Quotient-State Chunk DP Solver for N=8 mini-SHA
 *
 * GPT-5.4 prescribed algorithm: the automaton state at a chunk boundary
 * is carries + residual GF(2) linear context. We measure whether
 * projecting to this quotient state gives meaningful deduplication.
 *
 * Architecture:
 *   Outer: concrete W1[57] x W1[58] (2^16)
 *   Inner: symbolic round 59 (both messages) with 8 vars
 *   Measurement: at EACH pool state after round 59, extract the
 *     quotient key = (GF(2) RREF hash, register diff hash)
 *   Then: concrete rounds 60-63 for collision search
 *
 * The quotient measures equivalence classes: two post-R59 pool states
 * that produce the SAME collision set for ALL possible (W1[60],...)
 * values. This is determined by the GF(2) system (which constrains
 * how variables interact) plus the register state differential.
 *
 * Additionally: measures LOCAL dedup (within each w57,w58 pair) and
 * GLOBAL dedup (across all pairs).
 *
 * Verification: must find exactly 260 collisions for N=8, MSB kernel,
 * M[0]=0x67, fill=0xff.
 *
 * Compile: gcc -O3 -march=native -o quotient_dp quotient_dp.c -lm
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <time.h>

/* ================================================================ */
#define N 8
#define MASK ((1U << N) - 1)
#define MSB (1U << (N - 1))
#define M0_VAL 0x67U
#define FILL_VAL 0xFFU
#define NV 8     /* 8 variables: W1[59] bits 0-7 */
#define MAXPOOL (1 << 18)

typedef struct { uint8_t m; uint8_t c; } AF;
static inline AF af_c(int v)      { return (AF){0, (uint8_t)(v & 1)}; }
static inline AF af_v(int i)      { return (AF){(uint8_t)(1U << i), 0}; }
static inline AF af_x(AF a, AF b) { return (AF){(uint8_t)(a.m ^ b.m), (uint8_t)(a.c ^ b.c)}; }
static inline int af_ic(AF f)     { return f.m == 0; }
static inline int af_cv(AF f)     { return f.c; }

typedef struct {
    uint8_t rm[NV], rc[NV], has[NV];
    int rank;
} G2;

static void g2_init(G2 *s) { memset(s, 0, sizeof(G2)); }

static int g2_add(G2 *s, AF f) {
    for (int i = NV - 1; i >= 0; i--) {
        if (!((f.m >> i) & 1)) continue;
        if (s->has[i]) { f.m ^= s->rm[i]; f.c ^= s->rc[i]; }
        else {
            s->rm[i] = f.m; s->rc[i] = f.c; s->has[i] = 1; s->rank++;
            for (int j = 0; j < NV; j++)
                if (j != i && s->has[j] && ((s->rm[j] >> i) & 1)) {
                    s->rm[j] ^= f.m; s->rc[j] ^= f.c;
                }
            return 1;
        }
    }
    return (f.c == 0);
}

static AF g2_r(const G2 *s, AF f) {
    for (int i = NV - 1; i >= 0; i--)
        if (((f.m >> i) & 1) && s->has[i]) { f.m ^= s->rm[i]; f.c ^= s->rc[i]; }
    return f;
}

/* ================================================================ */
typedef struct {
    G2 sys;
    AF r1[8][N], r2[8][N];
    AF ax[N], ay[N], az[N]; int ac;
    AF ch[N], maj[N], t1[N], t2[N], w[N];
} ST;

static ST *PA, *PB;
static uint64_t stat_br = 0, stat_cx = 0;

/* ================================================================ */
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
static uint32_t KN[64], IVN[8], s1c[8], s2c[8], W1p[57], W2p[57];

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

static void bf_round(uint32_t s[8], uint32_t k, uint32_t w) {
    uint32_t T1 = (s[7] + fnS1(s[4]) + fnCh(s[4],s[5],s[6]) + k + w) & MASK;
    uint32_t T2 = (fnS0(s[0]) + fnMj(s[0],s[1],s[2])) & MASK;
    s[7]=s[6]; s[6]=s[5]; s[5]=s[4]; s[4]=(s[3]+T1)&MASK;
    s[3]=s[2]; s[2]=s[1]; s[1]=s[0]; s[0]=(T1+T2)&MASK;
}

static uint32_t cas_off(const uint32_t st1[8], const uint32_t st2[8], int rr) {
    return ((st1[7]+fnS1(st1[4])+fnCh(st1[4],st1[5],st1[6])+KN[rr])
           -(st2[7]+fnS1(st2[4])+fnCh(st2[4],st2[5],st2[6])+KN[rr])
           +(fnS0(st1[0])+fnMj(st1[0],st1[1],st1[2]))
           -(fnS0(st2[0])+fnMj(st2[0],st2[1],st2[2]))) & MASK;
}

static void sched_w1(const uint32_t w[4], uint32_t o[7]) {
    o[0]=w[0]; o[1]=w[1]; o[2]=w[2]; o[3]=w[3];
    o[4] = (fns1(w[2]) + W1p[54] + fns0(W1p[46]) + W1p[45]) & MASK;
    o[5] = (fns1(w[3]) + W1p[55] + fns0(W1p[47]) + W1p[46]) & MASK;
    o[6] = (fns1(o[4]) + W1p[56] + fns0(W1p[48]) + W1p[47]) & MASK;
}
static void sched_w2(const uint32_t w[4], uint32_t o[7]) {
    o[0]=w[0]; o[1]=w[1]; o[2]=w[2]; o[3]=w[3];
    o[4] = (fns1(w[2]) + W2p[54] + fns0(W2p[46]) + W2p[45]) & MASK;
    o[5] = (fns1(w[3]) + W2p[55] + fns0(W2p[47]) + W2p[46]) & MASK;
    o[6] = (fns1(o[4]) + W2p[56] + fns0(W2p[48]) + W2p[47]) & MASK;
}

static void aS0(AF o[N], const AF a[N]) {
    for (int i = 0; i < N; i++)
        o[i] = af_x(af_x(a[(i+rS0[0])%N], a[(i+rS0[1])%N]), a[(i+rS0[2])%N]);
}
static void aS1(AF o[N], const AF e[N]) {
    for (int i = 0; i < N; i++)
        o[i] = af_x(af_x(e[(i+rS1[0])%N], e[(i+rS1[1])%N]), e[(i+rS1[2])%N]);
}

/* ================================================================
 * Pool operations (FACE-proven)
 * ================================================================ */

static int p_add(int n) {
    for (int bit = 0; bit < N; bit++) {
        int no = 0;
        for (int i = 0; i < n && no < MAXPOOL - 3; i++) {
            AF xf = g2_r(&PA[i].sys, PA[i].ax[bit]);
            AF yf = g2_r(&PA[i].sys, PA[i].ay[bit]);
            int cin = PA[i].ac, xc = af_ic(xf), yc = af_ic(yf);
            if (xc && yc) {
                int xv = af_cv(xf), yv = af_cv(yf);
                PB[no] = PA[i]; PB[no].az[bit] = af_c(xv^yv^cin);
                PB[no].ac = (xv&yv)|(xv&cin)|(yv&cin); no++; continue;
            }
            { PB[no] = PA[i]; int ok = 1;
              if (!xc) ok = g2_add(&PB[no].sys, xf); else if (af_cv(xf)) ok = 0;
              if (ok) { AF yr = g2_r(&PB[no].sys, PA[i].ay[bit]);
                        if (!af_ic(yr)) ok = g2_add(&PB[no].sys, yr); else if (af_cv(yr)) ok = 0; }
              if (ok) { stat_br++; PB[no].az[bit] = af_c(cin); PB[no].ac = 0; no++; } else stat_cx++;
            }
            { PB[no] = PA[i]; AF d = af_x(xf, yf); d.c ^= 1;
              int ok = af_ic(d) ? (af_cv(d) == 0) : g2_add(&PB[no].sys, d);
              if (ok) { stat_br++; PB[no].az[bit] = af_c(cin^1); PB[no].ac = cin; no++; } else stat_cx++;
            }
            { PB[no] = PA[i]; int ok = 1;
              if (!xc) { AF cx = xf; cx.c ^= 1; ok = g2_add(&PB[no].sys, cx); } else if (!af_cv(xf)) ok = 0;
              if (ok) { AF yr = g2_r(&PB[no].sys, PA[i].ay[bit]); AF cy = yr; cy.c ^= 1;
                        if (!af_ic(yr)) ok = g2_add(&PB[no].sys, cy); else if (!af_cv(yr)) ok = 0; }
              if (ok) { stat_br++; PB[no].az[bit] = af_c(cin); PB[no].ac = 1; no++; } else stat_cx++;
            }
        }
        ST *t = PA; PA = PB; PB = t; n = no;
    }
    return n;
}

static int p_ch(int n, int m2) {
    for (int bit = 0; bit < N; bit++) {
        int no = 0;
        for (int i = 0; i < n && no < MAXPOOL - 2; i++) {
            AF ef = g2_r(&PA[i].sys, PA[i].ax[bit]);
            AF ff = PA[i].ay[bit];
            AF gf = m2 ? PA[i].r2[6][bit] : PA[i].r1[6][bit];
            if (af_ic(ef)) {
                PB[no] = PA[i];
                PB[no].az[bit] = af_cv(ef) ? g2_r(&PB[no].sys, ff) : g2_r(&PB[no].sys, gf);
                no++;
            } else {
                PB[no] = PA[i];
                if (g2_add(&PB[no].sys, ef)) { stat_br++; PB[no].az[bit] = g2_r(&PB[no].sys, gf); no++; } else stat_cx++;
                PB[no] = PA[i];
                { AF c = ef; c.c ^= 1;
                  if (g2_add(&PB[no].sys, c)) { stat_br++; PB[no].az[bit] = g2_r(&PB[no].sys, ff); no++; } else stat_cx++; }
            }
        }
        ST *t = PA; PA = PB; PB = t; n = no;
    }
    return n;
}

static int p_maj(int n, int m2) {
    for (int bit = 0; bit < N; bit++) {
        int no = 0;
        for (int i = 0; i < n && no < MAXPOOL - 4; i++) {
            AF a = g2_r(&PA[i].sys, PA[i].ax[bit]);
            AF b = g2_r(&PA[i].sys, PA[i].ay[bit]);
            AF c = g2_r(&PA[i].sys, m2 ? PA[i].r2[2][bit] : PA[i].r1[2][bit]);
            int ac_ = af_ic(a), bc_ = af_ic(b), cc_ = af_ic(c);
            if (ac_ && bc_ && cc_) {
                int av = af_cv(a), bv = af_cv(b), cv = af_cv(c);
                PB[no] = PA[i]; PB[no].az[bit] = af_c((av&bv)^(av&cv)^(bv&cv)); no++;
            } else if (bc_ && cc_) {
                int bv = af_cv(b), cv = af_cv(c);
                PB[no] = PA[i]; PB[no].az[bit] = (bv == cv) ? af_c(bv) : a; no++;
            } else if (ac_ && cc_) {
                int av = af_cv(a), cv = af_cv(c);
                PB[no] = PA[i]; PB[no].az[bit] = (av == cv) ? af_c(av) : b; no++;
            } else if (ac_ && bc_) {
                int av = af_cv(a), bv = af_cv(b);
                PB[no] = PA[i]; PB[no].az[bit] = (av == bv) ? af_c(av) :
                    g2_r(&PB[no].sys, m2 ? PA[i].r2[2][bit] : PA[i].r1[2][bit]); no++;
            } else {
                for (int av = 0; av <= 1; av++) {
                    if (no >= MAXPOOL) break;
                    PB[no] = PA[i]; int ok = 1;
                    if (!ac_) { AF cn = a; cn.c ^= av; ok = g2_add(&PB[no].sys, cn); }
                    else if (af_cv(a) != av) ok = 0;
                    if (!ok) { stat_cx++; continue; } stat_br++;
                    AF br = g2_r(&PB[no].sys, PA[i].ay[bit]);
                    AF cr = g2_r(&PB[no].sys, m2 ? PA[i].r2[2][bit] : PA[i].r1[2][bit]);
                    if (af_ic(br) && af_ic(cr)) {
                        int bvv = af_cv(br), cvv = af_cv(cr);
                        PB[no].az[bit] = af_c((av&bvv)^(av&cvv)^(bvv&cvv)); no++;
                    } else if (af_ic(br)) {
                        PB[no].az[bit] = (af_cv(br) == av) ? af_c(av) : cr; no++;
                    } else if (af_ic(cr)) {
                        PB[no].az[bit] = (af_cv(cr) == av) ? af_c(av) : br; no++;
                    } else {
                        ST sv = PB[no]; int ad = 0;
                        for (int bv = 0; bv <= 1 && no < MAXPOOL; bv++) {
                            if (ad) PB[no] = sv;
                            AF bc2 = br; bc2.c ^= bv;
                            if (!g2_add(&PB[no].sys, bc2)) { stat_cx++; ad = 1; continue; } stat_br++;
                            AF cr2 = g2_r(&PB[no].sys, m2 ? PA[i].r2[2][bit] : PA[i].r1[2][bit]);
                            if (af_ic(cr2)) { int cv2 = af_cv(cr2); PB[no].az[bit] = af_c((av&bv)^(av&cv2)^(bv&cv2)); }
                            else PB[no].az[bit] = (av == bv) ? af_c(av) : cr2;
                            no++; ad = 1;
                        }
                    }
                }
            }
        }
        ST *t = PA; PA = PB; PB = t; n = no;
    }
    return n;
}

/* ================================================================
 * Round function (FACE architecture)
 * ================================================================ */
static int do_rnd(int n, int rnd, int m2) {
    #define R(s, r) (m2 ? (s)->r2[r] : (s)->r1[r])

    for (int i = 0; i < n; i++) { memcpy(PA[i].ax, R(&PA[i],4), N*sizeof(AF));
        memcpy(PA[i].ay, R(&PA[i],5), N*sizeof(AF)); }
    n = p_ch(n, m2); if (!n) return 0;
    for (int i = 0; i < n; i++) memcpy(PA[i].ch, PA[i].az, N*sizeof(AF));

    for (int i = 0; i < n; i++) { memcpy(PA[i].ax, R(&PA[i],7), N*sizeof(AF));
        aS1(PA[i].ay, R(&PA[i],4)); PA[i].ac = 0; }
    n = p_add(n); if (!n) return 0;
    for (int i = 0; i < n; i++) memcpy(PA[i].t1, PA[i].az, N*sizeof(AF));

    for (int i = 0; i < n; i++) { memcpy(PA[i].ax, PA[i].t1, N*sizeof(AF));
        memcpy(PA[i].ay, PA[i].ch, N*sizeof(AF)); PA[i].ac = 0; }
    n = p_add(n); if (!n) return 0;
    for (int i = 0; i < n; i++) memcpy(PA[i].t1, PA[i].az, N*sizeof(AF));

    { int rr = 57 + rnd;
      for (int i = 0; i < n; i++) { for (int b = 0; b < N; b++) PA[i].ax[b] = af_c((KN[rr]>>b)&1);
          memcpy(PA[i].ay, PA[i].w, N*sizeof(AF)); PA[i].ac = 0; } }
    n = p_add(n); if (!n) return 0;
    for (int i = 0; i < n; i++) memcpy(PA[i].t2, PA[i].az, N*sizeof(AF));

    for (int i = 0; i < n; i++) { memcpy(PA[i].ax, PA[i].t1, N*sizeof(AF));
        memcpy(PA[i].ay, PA[i].t2, N*sizeof(AF)); PA[i].ac = 0; }
    n = p_add(n); if (!n) return 0;
    for (int i = 0; i < n; i++) memcpy(PA[i].t1, PA[i].az, N*sizeof(AF));

    for (int i = 0; i < n; i++) { memcpy(PA[i].ax, R(&PA[i],0), N*sizeof(AF));
        memcpy(PA[i].ay, R(&PA[i],1), N*sizeof(AF)); }
    n = p_maj(n, m2); if (!n) return 0;
    for (int i = 0; i < n; i++) memcpy(PA[i].maj, PA[i].az, N*sizeof(AF));

    for (int i = 0; i < n; i++) { aS0(PA[i].ax, R(&PA[i],0));
        memcpy(PA[i].ay, PA[i].maj, N*sizeof(AF)); PA[i].ac = 0; }
    n = p_add(n); if (!n) return 0;
    for (int i = 0; i < n; i++) memcpy(PA[i].t2, PA[i].az, N*sizeof(AF));

    for (int i = 0; i < n; i++) { memcpy(PA[i].ax, R(&PA[i],3), N*sizeof(AF));
        memcpy(PA[i].ay, PA[i].t1, N*sizeof(AF)); PA[i].ac = 0; }
    n = p_add(n); if (!n) return 0;
    for (int i = 0; i < n; i++) memcpy(PA[i].ch, PA[i].az, N*sizeof(AF));

    for (int i = 0; i < n; i++) { memcpy(PA[i].ax, PA[i].t1, N*sizeof(AF));
        memcpy(PA[i].ay, PA[i].t2, N*sizeof(AF)); PA[i].ac = 0; }
    n = p_add(n); if (!n) return 0;

    for (int i = 0; i < n; i++) {
        AF na[N], ne[N]; memcpy(na, PA[i].az, N*sizeof(AF));
        memcpy(ne, PA[i].ch, N*sizeof(AF));
        AF (*RR)[N] = m2 ? PA[i].r2 : PA[i].r1;
        memcpy(RR[7],RR[6],N*sizeof(AF)); memcpy(RR[6],RR[5],N*sizeof(AF));
        memcpy(RR[5],RR[4],N*sizeof(AF)); memcpy(RR[4],ne,N*sizeof(AF));
        memcpy(RR[3],RR[2],N*sizeof(AF)); memcpy(RR[2],RR[1],N*sizeof(AF));
        memcpy(RR[1],RR[0],N*sizeof(AF)); memcpy(RR[0],na,N*sizeof(AF));
    }
    return n;
    #undef R
}

/* ================================================================
 * Quotient state hashing
 *
 * The quotient key for a post-R59 pool state captures everything
 * that determines which W1[60] values produce collisions:
 * 1. Concrete register state for msg1 (all 8 vars resolved)
 * 2. Concrete register state for msg2 (derived from msg1 via constraints)
 * 3. GF(2) rank (how many vars are assigned)
 *
 * Since all 8 W1[59] variables are resolved after round 59 (the pool
 * branching explores all 256 values), the register states should be
 * FULLY CONCRETE. The quotient key is then just the two register states.
 *
 * But two different (w57,w58) pairs can produce the SAME pair of
 * register states after round 59. THAT is the dedup we measure.
 * ================================================================ */

typedef struct {
    uint32_t s1[8], s2[8];  /* concrete register states */
} QuotKey;

static uint64_t qkey_hash(const QuotKey *k) {
    uint64_t h = 14695981039346656037ULL;
    for (int i = 0; i < 8; i++) {
        h ^= k->s1[i]; h *= 1099511628211ULL;
        h ^= k->s2[i]; h *= 1099511628211ULL;
    }
    return h;
}

static int qkey_eq(const QuotKey *a, const QuotKey *b) {
    return memcmp(a, b, sizeof(QuotKey)) == 0;
}

/* Lightweight hash table for QuotKeys */
#define QTAB_BITS 22
#define QTAB_SIZE (1U << QTAB_BITS)
#define QTAB_MASK (QTAB_SIZE - 1)

typedef struct {
    uint64_t hash;
    QuotKey key;
    int count;
    int occupied;
} QEntry;

static QEntry *qtab;
static int n_unique_q;
static int n_total_q;

static void qtab_init(void) {
    qtab = calloc(QTAB_SIZE, sizeof(QEntry));
    n_unique_q = 0; n_total_q = 0;
}
static void qtab_free(void) { free(qtab); }

/* Returns 1 if new, 0 if merged */
static int qtab_insert(const QuotKey *k) {
    uint64_t h = qkey_hash(k);
    uint32_t slot = (uint32_t)(h & QTAB_MASK);
    n_total_q++;
    for (int probe = 0; probe < 4096; probe++) {
        uint32_t idx = (slot + probe) & QTAB_MASK;
        if (!qtab[idx].occupied) {
            qtab[idx].hash = h;
            qtab[idx].key = *k;
            qtab[idx].count = 1;
            qtab[idx].occupied = 1;
            n_unique_q++;
            return 1;
        }
        if (qtab[idx].hash == h && qkey_eq(k, &qtab[idx].key)) {
            qtab[idx].count++;
            return 0;
        }
    }
    return 1; /* probe limit — conservative */
}

/* Extract concrete state from a pool entry */
static QuotKey extract_qkey(const ST *st) {
    QuotKey k;
    for (int r = 0; r < 8; r++) {
        uint32_t v1 = 0, v2 = 0;
        for (int b = 0; b < N; b++) {
            AF f1 = g2_r(&st->sys, st->r1[r][b]);
            AF f2 = g2_r(&st->sys, st->r2[r][b]);
            if (af_ic(f1)) v1 |= (af_cv(f1) << b);
            if (af_ic(f2)) v2 |= (af_cv(f2) << b);
        }
        k.s1[r] = v1;
        k.s2[r] = v2;
    }
    return k;
}

/* ================================================================
 * ALSO measure: GF(2) RREF quotient (the lin_id from the spec)
 * This captures constraints between variables that survive to chunk 1.
 * Since all 8 vars are resolved, the RREF is rank-8 (fully determined).
 * The lin_id is just the 8 RHS values = the concrete W1[59] assignment.
 *
 * So the RREF quotient = concrete W1[59] value.
 * And the register state quotient = f(w57, w58, w59).
 *
 * Real dedup question: do different (w57,w58,w59) triples produce
 * the same register state at round 59? If so, they yield the same
 * collision set for all W1[60] values.
 * ================================================================ */

/* ================================================================ */
int main(int argc, char **argv) {
    setbuf(stdout, NULL);
    int skip_bf = (argc > 1 && !strcmp(argv[1], "--skip-bf"));

    rS0[0]=SR(2);  rS0[1]=SR(13); rS0[2]=SR(22);
    rS1[0]=SR(6);  rS1[1]=SR(11); rS1[2]=SR(25);
    rs0[0]=SR(7);  rs0[1]=SR(18); ss0=SR(3);
    rs1[0]=SR(17); rs1[1]=SR(19); ss1=SR(10);
    for (int i = 0; i < 64; i++) KN[i] = K32[i] & MASK;
    for (int i = 0; i < 8; i++) IVN[i] = IV32[i] & MASK;

    printf("=== Quotient-State Chunk DP Solver (N=%d) ===\n", N);
    printf("Candidate: M[0]=0x%02x fill=0x%02x MSB kernel\n\n", M0_VAL, FILL_VAL);

    uint32_t M1[16], M2[16];
    for (int i = 0; i < 16; i++) { M1[i] = FILL_VAL; M2[i] = FILL_VAL; }
    M1[0] = M0_VAL; M2[0] = M0_VAL ^ MSB; M2[9] = FILL_VAL ^ MSB;
    precompute(M1, s1c, W1p); precompute(M2, s2c, W2p);
    if (s1c[0] != s2c[0]) { printf("FAIL: da56 != 0\n"); return 1; }
    printf("da56=0 confirmed.\n");
    printf("st1:"); for (int i=0;i<8;i++) printf(" %02x",s1c[i]); printf("\n");
    printf("st2:"); for (int i=0;i<8;i++) printf(" %02x",s2c[i]); printf("\n\n");

    /* ============================================================
     * Brute-force
     * ============================================================ */
    int bf_count = 0;
    uint32_t (*bf_sols)[4] = malloc(512 * sizeof(uint32_t[4]));
    double bf_time = 0;

    if (!skip_bf) {
        printf("--- Brute force ---\n");
        struct timespec t0, t1; clock_gettime(CLOCK_MONOTONIC, &t0);
        for (uint64_t x = 0; x < (1ULL << (4*N)); x++) {
            uint32_t w1[4] = {(uint32_t)(x&MASK),(uint32_t)((x>>N)&MASK),
                              (uint32_t)((x>>(2*N))&MASK),(uint32_t)((x>>(3*N))&MASK)};
            uint32_t sa[8], sb[8]; memcpy(sa,s1c,32); memcpy(sb,s2c,32);
            uint32_t W1f[7], W2f[7]; sched_w1(w1,W1f);
            for (int r = 0; r < 4; r++) { uint32_t off = cas_off(sa,sb,57+r);
                W2f[r] = (W1f[r]+off)&MASK; bf_round(sa,KN[57+r],W1f[r]); bf_round(sb,KN[57+r],W2f[r]); }
            sched_w2(W2f,W2f);
            for (int r = 4; r < 7; r++) { bf_round(sa,KN[57+r],W1f[r]); bf_round(sb,KN[57+r],W2f[r]); }
            int ok = 1; for (int r = 0; r < 8; r++) if (sa[r] != sb[r]) { ok = 0; break; }
            if (ok && bf_count < 512) { memcpy(bf_sols[bf_count],w1,16); bf_count++; }
        }
        clock_gettime(CLOCK_MONOTONIC, &t1);
        bf_time = (t1.tv_sec-t0.tv_sec) + (t1.tv_nsec-t0.tv_nsec)/1e9;
        printf("BF: %d collisions, %.3fs\n\n", bf_count, bf_time);
    } else { bf_count = 260; printf("BF skipped (expected %d).\n\n", bf_count); }

    /* ============================================================
     * Quotient DP
     * ============================================================ */
    printf("--- Quotient DP ---\n");
    printf("Outer: W1[57] x W1[58] (2^%d)\n", 2*N);
    printf("Inner: symbolic R59 (8 vars), concrete R60-63\n");
    printf("Measures: register-state quotient at R59 boundary\n\n");

    PA = calloc(MAXPOOL, sizeof(ST));
    PB = calloc(MAXPOOL, sizeof(ST));
    if (!PA || !PB) { printf("OOM\n"); return 1; }
    qtab_init();

    struct timespec ts0, ts1; clock_gettime(CLOCK_MONOTONIC, &ts0);

    int total_coll = 0;
    uint32_t (*dp_sols)[4] = malloc(512 * sizeof(uint32_t[4]));
    uint64_t total_r59_states = 0;
    uint64_t tot_br = 0, tot_cx = 0;

    /* Also measure dedup via concrete state hashing:
     * For each (w57,w58,w59) triple, compute register state at R59
     * concretely, and hash-cons the (s1_59, s2_59) pair. */
    uint64_t n_triples = 0;

    for (uint32_t w57 = 0; w57 < (1U << N); w57++) {
        uint32_t w2_57 = (w57 + cas_off(s1c, s2c, 57)) & MASK;
        uint32_t st57_1[8], st57_2[8];
        memcpy(st57_1, s1c, 32); memcpy(st57_2, s2c, 32);
        bf_round(st57_1, KN[57], w57); bf_round(st57_2, KN[57], w2_57);

        for (uint32_t w58 = 0; w58 < (1U << N); w58++) {
            uint32_t w2_58 = (w58 + cas_off(st57_1, st57_2, 58)) & MASK;
            uint32_t st58_1[8], st58_2[8];
            memcpy(st58_1, st57_1, 32); memcpy(st58_2, st57_2, 32);
            bf_round(st58_1, KN[58], w58); bf_round(st58_2, KN[58], w2_58);

            stat_br = 0; stat_cx = 0;
            uint32_t cas59 = cas_off(st58_1, st58_2, 59);

            /* Symbolic round 59 */
            int sn = 1;
            g2_init(&PA[0].sys);
            for (int r = 0; r < 8; r++)
                for (int b = 0; b < N; b++) {
                    PA[0].r1[r][b] = af_c((st58_1[r] >> b) & 1);
                    PA[0].r2[r][b] = af_c((st58_2[r] >> b) & 1);
                }

            for (int i = 0; i < sn; i++)
                for (int b = 0; b < N; b++) PA[i].w[b] = af_v(b);
            sn = do_rnd(sn, 2, 0); /* R59 msg1 */
            if (sn == 0) goto next;

            for (int i = 0; i < sn; i++) {
                for (int b = 0; b < N; b++) {
                    PA[i].ax[b] = af_v(b);
                    PA[i].ay[b] = af_c((cas59 >> b) & 1);
                }
                PA[i].ac = 0;
            }
            sn = p_add(sn);
            if (sn == 0) goto next;
            for (int i = 0; i < sn; i++) memcpy(PA[i].w, PA[i].az, N*sizeof(AF));
            sn = do_rnd(sn, 2, 1); /* R59 msg2 */
            if (sn == 0) goto next;

            total_r59_states += sn;

            /* Insert each state into quotient hash table */
            for (int i = 0; i < sn; i++) {
                QuotKey qk = extract_qkey(&PA[i]);
                qtab_insert(&qk);
            }

            /* Collision search (concrete R60-63) */
            for (int si = 0; si < sn; si++) {
                uint32_t w59v = 0;
                for (int b = 0; b < N; b++) {
                    AF f = g2_r(&PA[si].sys, af_v(b));
                    if (af_ic(f)) w59v |= (af_cv(f) << b);
                }

                uint32_t s59_1[8], s59_2[8];
                memcpy(s59_1, st58_1, 32); memcpy(s59_2, st58_2, 32);
                uint32_t w2_59 = (w59v + cas59) & MASK;
                bf_round(s59_1, KN[59], w59v); bf_round(s59_2, KN[59], w2_59);

                uint32_t c60 = cas_off(s59_1, s59_2, 60);
                uint32_t W1_61 = (fns1(w59v) + W1p[54] + fns0(W1p[46]) + W1p[45]) & MASK;
                uint32_t W2_61 = (fns1(w2_59) + W2p[54] + fns0(W2p[46]) + W2p[45]) & MASK;
                uint32_t W1_63 = (fns1(W1_61) + W1p[56] + fns0(W1p[48]) + W1p[47]) & MASK;
                uint32_t W2_63 = (fns1(W2_61) + W2p[56] + fns0(W2p[48]) + W2p[47]) & MASK;

                n_triples++;

                for (uint32_t w60 = 0; w60 < (1U << N); w60++) {
                    uint32_t w2_60 = (w60 + c60) & MASK;
                    uint32_t s60_1[8], s60_2[8];
                    memcpy(s60_1, s59_1, 32); memcpy(s60_2, s59_2, 32);
                    bf_round(s60_1, KN[60], w60); bf_round(s60_2, KN[60], w2_60);

                    uint32_t s61_1[8], s61_2[8];
                    memcpy(s61_1, s60_1, 32); memcpy(s61_2, s60_2, 32);
                    bf_round(s61_1, KN[61], W1_61); bf_round(s61_2, KN[61], W2_61);

                    if (((s61_1[4] - s61_2[4]) & MASK) != 0) continue;

                    uint32_t W1_62 = (fns1(w60) + W1p[55] + fns0(W1p[47]) + W1p[46]) & MASK;
                    uint32_t W2_62 = (fns1(w2_60) + W2p[55] + fns0(W2p[47]) + W2p[46]) & MASK;

                    bf_round(s61_1, KN[62], W1_62); bf_round(s61_2, KN[62], W2_62);
                    bf_round(s61_1, KN[63], W1_63); bf_round(s61_2, KN[63], W2_63);

                    int ok = 1;
                    for (int r = 0; r < 8; r++) if (s61_1[r] != s61_2[r]) { ok = 0; break; }
                    if (ok) {
                        uint32_t ww[4] = {w57, w58, w59v, w60};
                        if (total_coll < 512) memcpy(dp_sols[total_coll], ww, 16);
                        total_coll++;
                    }
                }
            }

            tot_br += stat_br; tot_cx += stat_cx;
            next:;
        }

        if ((w57 & 0x3) == 0x3 || w57 == (1U << N) - 1) {
            clock_gettime(CLOCK_MONOTONIC, &ts1);
            double el = (ts1.tv_sec-ts0.tv_sec) + (ts1.tv_nsec-ts0.tv_nsec)/1e9;
            double dedup = n_total_q > 0 ?
                100.0*(1.0 - (double)n_unique_q / n_total_q) : 0.0;
            printf("  [%3.0f%%] w57=%3u coll=%d tot_r59=%llu uniq=%d/%d (%.1f%% dedup) %.1fs\n",
                   100.0*(w57+1)/(1U<<N), w57, total_coll,
                   (unsigned long long)total_r59_states,
                   n_unique_q, n_total_q, dedup, el);
        }
    }
    clock_gettime(CLOCK_MONOTONIC, &ts1);
    double dp_time = (ts1.tv_sec-ts0.tv_sec) + (ts1.tv_nsec-ts0.tv_nsec)/1e9;

    /* ============================================================
     * Results
     * ============================================================ */
    printf("\n========================================\n");
    printf("  Quotient-State Chunk DP Results (N=%d)\n", N);
    printf("========================================\n");
    printf("Candidate: M[0]=0x%02x fill=0x%02x MSB kernel\n\n", M0_VAL, FILL_VAL);
    if (!skip_bf) printf("Brute force:     %d collisions (%.3fs)\n", bf_count, bf_time);
    printf("DP solver:       %d collisions (%.3fs)\n\n", total_coll, dp_time);

    printf("=== Register-State Quotient at R59 Boundary ===\n");
    printf("Total (w57,w58,w59) triples:   %llu\n", (unsigned long long)n_triples);
    printf("Total post-R59 pool states:    %llu\n", (unsigned long long)total_r59_states);
    printf("Unique register-state pairs:   %d\n", n_unique_q);
    if (n_total_q > 0 && n_unique_q > 0) {
        double dedup = 100.0 * (1.0 - (double)n_unique_q / n_total_q);
        double ratio = (double)n_total_q / n_unique_q;
        printf("Deduplication ratio:           %.4fx (%.2f%% reduction)\n", ratio, dedup);
        printf("\nInterpretation:\n");
        if (dedup > 1.0)
            printf("  %.2f%% of (w57,w58,w59) triples share a register state with\n"
                   "  another triple. These produce identical collision behavior for\n"
                   "  all W1[60] values, enabling %.2fx compression.\n", dedup, ratio);
        else
            printf("  Negligible dedup: almost every (w57,w58,w59) triple produces\n"
                   "  a unique register state. The quotient gives no compression.\n");
    }

    /* Multiplicity distribution */
    printf("\n=== Multiplicity Distribution ===\n");
    int mult_max = 0;
    for (uint32_t i = 0; i < QTAB_SIZE; i++)
        if (qtab[i].occupied && qtab[i].count > mult_max) mult_max = qtab[i].count;

    int *mhist = calloc(mult_max + 2, sizeof(int));
    for (uint32_t i = 0; i < QTAB_SIZE; i++)
        if (qtab[i].occupied) mhist[qtab[i].count]++;
    for (int c = 1; c <= mult_max && c <= 20; c++)
        if (mhist[c] > 0) printf("  count=%d: %d states\n", c, mhist[c]);
    if (mult_max > 20) {
        int above20 = 0;
        for (int c = 21; c <= mult_max; c++) above20 += mhist[c];
        if (above20 > 0) printf("  count>20: %d states (max %d)\n", above20, mult_max);
    }
    free(mhist);

    /* Branches and contradictions */
    printf("\nTotal branches:       %llu\n", (unsigned long long)tot_br);
    printf("Total contradictions: %llu\n\n", (unsigned long long)tot_cx);

    /* Cross-validation */
    if (!skip_bf) {
        printf("=== Cross-Validation ===\n");
        int matched = 0, missed = 0;
        for (int i = 0; i < total_coll && i < 512; i++)
            for (int j = 0; j < bf_count; j++)
                if (!memcmp(dp_sols[i], bf_sols[j], 16)) { matched++; break; }
        for (int j = 0; j < bf_count; j++) {
            int f = 0;
            for (int i = 0; i < total_coll && i < 512; i++)
                if (!memcmp(dp_sols[i], bf_sols[j], 16)) { f = 1; break; }
            if (!f) { if (missed < 5) printf("  MISSED: [%02x,%02x,%02x,%02x]\n",
                        bf_sols[j][0],bf_sols[j][1],bf_sols[j][2],bf_sols[j][3]); missed++; }
        }
        printf("DP matched BF: %d / %d\n", matched, bf_count);
        printf("BF missed:     %d\n", missed);
        if (matched == bf_count && missed == 0 && total_coll == bf_count)
            printf("PERFECT MATCH -- all %d collisions verified.\n", bf_count);
        else
            printf("Status: BF=%d, DP=%d\n", bf_count, total_coll);
    }

    printf("\nFirst 10 solutions:\n");
    for (int i = 0; i < total_coll && i < 10 && i < 512; i++)
        printf("  #%d: W1=[%02x,%02x,%02x,%02x]\n", i+1,
               dp_sols[i][0],dp_sols[i][1],dp_sols[i][2],dp_sols[i][3]);

    free(PA); free(PB); free(bf_sols); free(dp_sols);
    qtab_free();
    return 0;
}
