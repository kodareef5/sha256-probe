/*
 * bdd_incremental.c — Incremental BDD construction for collision function
 *
 * Builds the collision-function BDD WITHOUT a truth table by composing
 * SHA-256 round operations symbolically as BDD operations.
 *
 * This is the potentially polynomial-time collision finder:
 * if intermediate BDD sizes stay polynomial in N, the entire
 * construction runs in polynomial time.
 *
 * Strategy:
 *   - 4N BDD input variables (bits of W57, W58, W59, W60)
 *   - State after round 56 is concrete (precomputed)
 *   - Round function applied symbolically using BDD Apply operations
 *   - Cascade W2[r] computed symbolically via BDD addition
 *   - Collision check: AND of XNOR for all 8×N output register bits
 *
 * Validation targets:
 *   N=4:  183 nodes, 49 collisions
 *   N=6:  615 nodes
 *   N=8: 4322 nodes, 260 collisions
 *
 * Variable ordering (interleaved, bit-first):
 *   var 4*b+0 = W57[b], var 4*b+1 = W58[b],
 *   var 4*b+2 = W59[b], var 4*b+3 = W60[b]
 *   for b = 0, 1, ..., N-1
 *
 * Compile: gcc -O3 -march=native -o bdd_inc bdd_incremental.c -lm
 * Usage:   ./bdd_inc [N]    (default N=4)
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <time.h>

/* ================================================================
 * CONFIGURABLE PARAMETERS
 * ================================================================ */

static int N;           /* word width (set from argv or default 4) */
static uint32_t MASK;   /* (1 << N) - 1 */
static uint32_t MSB_BIT;/* 1 << (N-1) */
static int NVARS;       /* 4 * N */

/* ================================================================
 * BDD CORE DATA STRUCTURES
 * ================================================================ */

typedef struct {
    int var;    /* variable index [0..NVARS-1], or -1 for terminals */
    int lo;     /* child when var = 0 */
    int hi;     /* child when var = 1 */
} BDDNode;

#define BDD_FALSE 0
#define BDD_TRUE  1

static BDDNode *bdd_nodes = NULL;
static int bdd_count = 0;
static int bdd_cap = 0;
static int bdd_peak = 0;  /* track peak node count */

/* ---- Unique table ---- */
#define UHASH_BITS 22
#define UHASH_SIZE (1 << UHASH_BITS)
#define UHASH_MASK (UHASH_SIZE - 1)

typedef struct {
    int var, lo, hi, node_id;
    int next;  /* index into uentry_pool, -1 = end of chain */
} UEntry;

static int *uhash_table = NULL;  /* indices into uentry_pool, -1 = empty */
static UEntry *uentry_pool = NULL;
static int uentry_count = 0;
static int uentry_cap = 0;

/* ---- Computed table (for Apply memoization) ---- */
#define CHASH_BITS 22
#define CHASH_SIZE (1 << CHASH_BITS)
#define CHASH_MASK (CHASH_SIZE - 1)

typedef struct {
    int op, f, g, result;
} CacheEntry;

static CacheEntry *comp_table = NULL;
static uint64_t cache_hits = 0, cache_misses = 0;

/* ================================================================
 * BDD INITIALIZATION
 * ================================================================ */

static void bdd_init(void) {
    bdd_cap = 1 << 20;  /* 1M initial */
    bdd_nodes = (BDDNode *)malloc(bdd_cap * sizeof(BDDNode));
    bdd_nodes[0] = (BDDNode){-1, 0, 0};  /* FALSE */
    bdd_nodes[1] = (BDDNode){-1, 1, 1};  /* TRUE */
    bdd_count = 2;

    uhash_table = (int *)malloc(UHASH_SIZE * sizeof(int));
    for (int i = 0; i < UHASH_SIZE; i++) uhash_table[i] = -1;
    uentry_cap = 1 << 20;
    uentry_pool = (UEntry *)malloc(uentry_cap * sizeof(UEntry));
    uentry_count = 0;

    comp_table = (CacheEntry *)calloc(CHASH_SIZE, sizeof(CacheEntry));
    for (int i = 0; i < CHASH_SIZE; i++)
        comp_table[i].op = -1;
}

/* ================================================================
 * BDD MAKE (unique table lookup + creation)
 * ================================================================ */

static inline uint32_t uhash_fn(int var, int lo, int hi) {
    uint32_t h = (uint32_t)var * 7919u + (uint32_t)lo * 104729u + (uint32_t)hi * 1000003u;
    return h & UHASH_MASK;
}

static int bdd_make(int var, int lo, int hi) {
    if (lo == hi) return lo;  /* reduction rule */

    uint32_t h = uhash_fn(var, lo, hi);
    for (int ei = uhash_table[h]; ei >= 0; ei = uentry_pool[ei].next) {
        UEntry *e = &uentry_pool[ei];
        if (e->var == var && e->lo == lo && e->hi == hi)
            return e->node_id;
    }

    if (bdd_count >= bdd_cap) {
        bdd_cap *= 2;
        bdd_nodes = (BDDNode *)realloc(bdd_nodes, bdd_cap * sizeof(BDDNode));
    }
    int id = bdd_count++;
    bdd_nodes[id] = (BDDNode){var, lo, hi};
    if (bdd_count > bdd_peak) bdd_peak = bdd_count;

    if (uentry_count >= uentry_cap) {
        uentry_cap *= 2;
        uentry_pool = (UEntry *)realloc(uentry_pool, uentry_cap * sizeof(UEntry));
    }
    int nei = uentry_count++;
    uentry_pool[nei].var = var;
    uentry_pool[nei].lo = lo;
    uentry_pool[nei].hi = hi;
    uentry_pool[nei].node_id = id;
    uentry_pool[nei].next = uhash_table[h];
    uhash_table[h] = nei;

    return id;
}

/* ================================================================
 * BDD VARIABLE
 * ================================================================ */

static int bdd_var(int v) {
    return bdd_make(v, BDD_FALSE, BDD_TRUE);
}

static int bdd_not(int f) {
    /* NOT via recursive structural negation */
    if (f == BDD_FALSE) return BDD_TRUE;
    if (f == BDD_TRUE) return BDD_FALSE;
    int lo = bdd_not(bdd_nodes[f].lo);
    int hi = bdd_not(bdd_nodes[f].hi);
    return bdd_make(bdd_nodes[f].var, lo, hi);
}

/* ================================================================
 * BDD APPLY (the core operation)
 *
 * Operations: 0=AND, 1=OR, 2=XOR, 3=XNOR
 * ================================================================ */

enum { OP_AND=0, OP_OR=1, OP_XOR=2, OP_XNOR=3 };

static inline int apply_op(int op, int a, int b) {
    switch (op) {
        case OP_AND:  return a & b;
        case OP_OR:   return a | b;
        case OP_XOR:  return a ^ b;
        case OP_XNOR: return !(a ^ b);
        default: return 0;
    }
}

static inline uint32_t chash_fn(int op, int f, int g) {
    uint32_t h = (uint32_t)op * 314159u + (uint32_t)f * 271828u + (uint32_t)g * 161803u;
    return h & CHASH_MASK;
}

static int bdd_apply(int op, int f, int g) {
    /* Terminal cases */
    if (f <= 1 && g <= 1)
        return apply_op(op, f, g) ? BDD_TRUE : BDD_FALSE;

    /* Symmetry: for commutative ops, normalize order */
    if ((op == OP_AND || op == OP_OR || op == OP_XOR || op == OP_XNOR) && f > g) {
        int tmp = f; f = g; g = tmp;
    }

    /* Short-circuit for AND/OR */
    if (op == OP_AND) {
        if (f == BDD_FALSE || g == BDD_FALSE) return BDD_FALSE;
        if (f == BDD_TRUE) return g;
        if (g == BDD_TRUE) return f;
        if (f == g) return f;
    } else if (op == OP_OR) {
        if (f == BDD_TRUE || g == BDD_TRUE) return BDD_TRUE;
        if (f == BDD_FALSE) return g;
        if (g == BDD_FALSE) return f;
        if (f == g) return f;
    } else if (op == OP_XOR) {
        if (f == BDD_FALSE) return g;
        if (g == BDD_FALSE) return f;
        if (f == g) return BDD_FALSE;
    } else if (op == OP_XNOR) {
        if (f == g) return BDD_TRUE;
    }

    /* Computed table lookup */
    uint32_t ch = chash_fn(op, f, g);
    CacheEntry *ce = &comp_table[ch];
    if (ce->op == op && ce->f == f && ce->g == g) {
        cache_hits++;
        return ce->result;
    }
    cache_misses++;

    /* Get top variable */
    int vf = (f <= 1) ? NVARS : bdd_nodes[f].var;
    int vg = (g <= 1) ? NVARS : bdd_nodes[g].var;
    int v = (vf < vg) ? vf : vg;

    /* Cofactors */
    int f_lo = f, f_hi = f;
    int g_lo = g, g_hi = g;
    if (vf == v) { f_lo = bdd_nodes[f].lo; f_hi = bdd_nodes[f].hi; }
    if (vg == v) { g_lo = bdd_nodes[g].lo; g_hi = bdd_nodes[g].hi; }

    /* Recurse */
    int lo = bdd_apply(op, f_lo, g_lo);
    int hi = bdd_apply(op, f_hi, g_hi);
    int result = bdd_make(v, lo, hi);

    /* Cache result */
    ce->op = op; ce->f = f; ce->g = g; ce->result = result;
    return result;
}

/* Convenience wrappers */
static inline int bdd_and(int f, int g) { return bdd_apply(OP_AND, f, g); }
static inline int bdd_or(int f, int g)  { return bdd_apply(OP_OR, f, g); }
static inline int bdd_xor(int f, int g) { return bdd_apply(OP_XOR, f, g); }
static inline int bdd_xnor(int f, int g){ return bdd_apply(OP_XNOR, f, g); }

/* ================================================================
 * N-BIT ARITHMETIC OVER BDD VECTORS
 *
 * A "bdd_word" is an array of N ints, each a BDD node ID.
 * word[0] = LSB, word[N-1] = MSB.
 * ================================================================ */

/* Convert concrete value to BDD word */
static void bdd_const(int *out, uint32_t val) {
    for (int i = 0; i < N; i++)
        out[i] = ((val >> i) & 1) ? BDD_TRUE : BDD_FALSE;
}

/* N-bit XOR */
static void bdd_word_xor(int *out, const int *a, const int *b) {
    for (int i = 0; i < N; i++)
        out[i] = bdd_xor(a[i], b[i]);
}

/* N-bit AND */
static void bdd_word_and(int *out, const int *a, const int *b) {
    for (int i = 0; i < N; i++)
        out[i] = bdd_and(a[i], b[i]);
}

/* N-bit OR */
static void bdd_word_or(int *out, const int *a, const int *b) {
    for (int i = 0; i < N; i++)
        out[i] = bdd_or(a[i], b[i]);
}

/* N-bit NOT */
static void bdd_word_not(int *out, const int *a) {
    for (int i = 0; i < N; i++)
        out[i] = bdd_not(a[i]);
}

/* N-bit addition (mod 2^N) with ripple carry */
static void bdd_word_add(int *out, const int *a, const int *b) {
    int carry = BDD_FALSE;
    for (int i = 0; i < N; i++) {
        /* sum[i] = a[i] XOR b[i] XOR carry */
        int axb = bdd_xor(a[i], b[i]);
        out[i] = bdd_xor(axb, carry);
        /* carry[i+1] = MAJ(a[i], b[i], carry) */
        if (i < N - 1) {
            int ab = bdd_and(a[i], b[i]);
            int ac = bdd_and(a[i], carry);
            int bc = bdd_and(b[i], carry);
            carry = bdd_or(bdd_or(ab, ac), bc);
        }
    }
}

/* N-bit subtraction: out = a - b (mod 2^N) */
static void bdd_word_sub(int *out, const int *a, const int *b) {
    /* a - b = a + (~b) + 1 = a + (~b + 1) */
    int neg_b[32];
    for (int i = 0; i < N; i++) neg_b[i] = bdd_not(b[i]);
    /* Add 1: ripple through */
    int one[32];
    bdd_const(one, 1);
    int twos_comp[32];
    bdd_word_add(twos_comp, neg_b, one);
    bdd_word_add(out, a, twos_comp);
}

/* Copy BDD word */
static void bdd_word_copy(int *dst, const int *src) {
    memcpy(dst, src, N * sizeof(int));
}

/* Right rotation by k bits */
static void bdd_word_ror(int *out, const int *a, int k) {
    k = k % N;
    for (int i = 0; i < N; i++)
        out[i] = a[(i + k) % N];
}

/* Right shift by k bits (logical) */
static void bdd_word_shr(int *out, const int *a, int k) {
    for (int i = 0; i < N; i++)
        out[i] = (i + k < N) ? a[i + k] : BDD_FALSE;
}

/* ================================================================
 * SHA-256 PRIMITIVES OVER BDD WORDS
 * ================================================================ */

static int rS0[3], rS1[3], rs0[2], rs1[2], ss0, ss1;

static int scale_rot(int k32) {
    int r = (int)rint((double)k32 * N / 32.0);
    return r < 1 ? 1 : r;
}

/* Sigma0(a) = ROR(a,2) XOR ROR(a,13) XOR ROR(a,22) */
static void bdd_Sigma0(int *out, const int *a) {
    int t1[32], t2[32], t3[32];
    bdd_word_ror(t1, a, rS0[0]);
    bdd_word_ror(t2, a, rS0[1]);
    bdd_word_ror(t3, a, rS0[2]);
    int t4[32];
    bdd_word_xor(t4, t1, t2);
    bdd_word_xor(out, t4, t3);
}

/* Sigma1(e) = ROR(e,6) XOR ROR(e,11) XOR ROR(e,25) */
static void bdd_Sigma1(int *out, const int *e) {
    int t1[32], t2[32], t3[32];
    bdd_word_ror(t1, e, rS1[0]);
    bdd_word_ror(t2, e, rS1[1]);
    bdd_word_ror(t3, e, rS1[2]);
    int t4[32];
    bdd_word_xor(t4, t1, t2);
    bdd_word_xor(out, t4, t3);
}

/* sigma0(x) = ROR(x,7) XOR ROR(x,18) XOR SHR(x,3) */
static void bdd_sigma0(int *out, const int *x) {
    int t1[32], t2[32], t3[32];
    bdd_word_ror(t1, x, rs0[0]);
    bdd_word_ror(t2, x, rs0[1]);
    bdd_word_shr(t3, x, ss0);
    int t4[32];
    bdd_word_xor(t4, t1, t2);
    bdd_word_xor(out, t4, t3);
}

/* sigma1(x) = ROR(x,17) XOR ROR(x,19) XOR SHR(x,10) */
static void bdd_sigma1(int *out, const int *x) {
    int t1[32], t2[32], t3[32];
    bdd_word_ror(t1, x, rs1[0]);
    bdd_word_ror(t2, x, rs1[1]);
    bdd_word_shr(t3, x, ss1);
    int t4[32];
    bdd_word_xor(t4, t1, t2);
    bdd_word_xor(out, t4, t3);
}

/* Ch(e,f,g) = (e AND f) XOR (NOT(e) AND g) */
static void bdd_Ch(int *out, const int *e, const int *f, const int *g) {
    int ef[32], neg[32], ng[32];
    bdd_word_and(ef, e, f);
    bdd_word_not(neg, e);
    bdd_word_and(ng, neg, g);
    bdd_word_xor(out, ef, ng);
}

/* Maj(a,b,c) = (a AND b) XOR (a AND c) XOR (b AND c) */
static void bdd_Maj(int *out, const int *a, const int *b, const int *c) {
    int ab[32], ac[32], bc[32], t[32];
    bdd_word_and(ab, a, b);
    bdd_word_and(ac, a, c);
    bdd_word_and(bc, b, c);
    bdd_word_xor(t, ab, ac);
    bdd_word_xor(out, t, bc);
}

/* ================================================================
 * SHA-256 STATE: 8 registers, each an N-bit BDD word
 * ================================================================ */

typedef struct {
    int reg[8][32];  /* reg[0]=a, reg[1]=b, ..., reg[7]=h; each is N BDD nodes */
} BDDState;

/* Concrete SHA-256 round function (for precomputation) */
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

/* Concrete rotation/shift for precomputation */
static inline uint32_t ror_n(uint32_t x, int k) {
    k = k % N; return ((x >> k) | (x << (N - k))) & MASK;
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

/* Precompute through round 56 */
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

/* ================================================================
 * BDD ROUND FUNCTION
 *
 * Apply one SHA-256 round symbolically on a BDD state.
 * K_bdd and W_bdd are the round constant and message word as BDD words.
 * ================================================================ */

static void bdd_sha_round(BDDState *s, const int *K_bdd, const int *W_bdd) {
    int sig1[32], ch[32], T1_partial[32], T1[32], sig0[32], maj[32], T2[32];
    int new_a[32], new_e[32];

    /* T1 = h + Sigma1(e) + Ch(e,f,g) + K + W */
    bdd_Sigma1(sig1, s->reg[4]);                   /* Sigma1(e) */
    bdd_Ch(ch, s->reg[4], s->reg[5], s->reg[6]);   /* Ch(e,f,g) */

    bdd_word_add(T1_partial, s->reg[7], sig1);      /* h + Sigma1(e) */
    int t2[32];
    bdd_word_add(t2, T1_partial, ch);                /* + Ch */
    int t3[32];
    bdd_word_add(t3, t2, K_bdd);                    /* + K */
    bdd_word_add(T1, t3, W_bdd);                    /* + W */

    /* T2 = Sigma0(a) + Maj(a,b,c) */
    bdd_Sigma0(sig0, s->reg[0]);
    bdd_Maj(maj, s->reg[0], s->reg[1], s->reg[2]);
    bdd_word_add(T2, sig0, maj);

    /* new_e = d + T1 */
    bdd_word_add(new_e, s->reg[3], T1);

    /* new_a = T1 + T2 */
    bdd_word_add(new_a, T1, T2);

    /* Shift register: h=g, g=f, f=e, e=new_e, d=c, c=b, b=a, a=new_a */
    bdd_word_copy(s->reg[7], s->reg[6]);  /* h = g */
    bdd_word_copy(s->reg[6], s->reg[5]);  /* g = f */
    bdd_word_copy(s->reg[5], s->reg[4]);  /* f = e */
    bdd_word_copy(s->reg[4], new_e);      /* e = new_e */
    bdd_word_copy(s->reg[3], s->reg[2]);  /* d = c */
    bdd_word_copy(s->reg[2], s->reg[1]);  /* c = b */
    bdd_word_copy(s->reg[1], s->reg[0]);  /* b = a */
    bdd_word_copy(s->reg[0], new_a);      /* a = new_a */
}

/* ================================================================
 * CASCADE: compute W2 as BDD word given W1 BDD word + states
 *
 * W2 = W1 + (r1 - r2) + (T21 - T22)
 * where r_i = h_i + Sigma1(e_i) + Ch(e_i,f_i,g_i) + K
 *       T2_i = Sigma0(a_i) + Maj(a_i,b_i,c_i)
 * ================================================================ */

static void bdd_cascade_w2(int *W2_bdd, const int *W1_bdd,
                           const BDDState *s1, const BDDState *s2,
                           const int *K_bdd) {
    /* r1 = h1 + Sigma1(e1) + Ch(e1,f1,g1) + K */
    int sig1_1[32], ch_1[32], r1[32];
    bdd_Sigma1(sig1_1, s1->reg[4]);
    bdd_Ch(ch_1, s1->reg[4], s1->reg[5], s1->reg[6]);
    int t1[32], t2[32];
    bdd_word_add(t1, s1->reg[7], sig1_1);
    bdd_word_add(t2, t1, ch_1);
    bdd_word_add(r1, t2, K_bdd);

    /* r2 = h2 + Sigma1(e2) + Ch(e2,f2,g2) + K */
    int sig1_2[32], ch_2[32], r2[32];
    bdd_Sigma1(sig1_2, s2->reg[4]);
    bdd_Ch(ch_2, s2->reg[4], s2->reg[5], s2->reg[6]);
    int t3[32], t4[32];
    bdd_word_add(t3, s2->reg[7], sig1_2);
    bdd_word_add(t4, t3, ch_2);
    bdd_word_add(r2, t4, K_bdd);

    /* T21 = Sigma0(a1) + Maj(a1,b1,c1) */
    int sig0_1[32], maj_1[32], T21[32];
    bdd_Sigma0(sig0_1, s1->reg[0]);
    bdd_Maj(maj_1, s1->reg[0], s1->reg[1], s1->reg[2]);
    bdd_word_add(T21, sig0_1, maj_1);

    /* T22 = Sigma0(a2) + Maj(a2,b2,c2) */
    int sig0_2[32], maj_2[32], T22[32];
    bdd_Sigma0(sig0_2, s2->reg[0]);
    bdd_Maj(maj_2, s2->reg[0], s2->reg[1], s2->reg[2]);
    bdd_word_add(T22, sig0_2, maj_2);

    /* offset = (r1 - r2) + (T21 - T22) */
    int diff_r[32], diff_T[32], offset[32];
    bdd_word_sub(diff_r, r1, r2);
    bdd_word_sub(diff_T, T21, T22);
    bdd_word_add(offset, diff_r, diff_T);

    /* W2 = W1 + offset */
    bdd_word_add(W2_bdd, W1_bdd, offset);
}

/* ================================================================
 * BDD NODE COUNTING (count unique reachable nodes from a root)
 * ================================================================ */

static int *visited = NULL;
static int visited_cap = 0;

static int count_nodes_rec(int node) {
    if (node <= 1) return 0;
    if (node >= visited_cap) {
        int new_cap = node + 1;
        visited = (int *)realloc(visited, new_cap * sizeof(int));
        memset(visited + visited_cap, 0, (new_cap - visited_cap) * sizeof(int));
        visited_cap = new_cap;
    }
    if (visited[node]) return 0;
    visited[node] = 1;
    return 1 + count_nodes_rec(bdd_nodes[node].lo)
             + count_nodes_rec(bdd_nodes[node].hi);
}

static int count_bdd_nodes(int root) {
    if (visited_cap < bdd_count) {
        visited = (int *)realloc(visited, bdd_count * sizeof(int));
        visited_cap = bdd_count;
    }
    memset(visited, 0, visited_cap * sizeof(int));
    return count_nodes_rec(root);
}

/* Count nodes reachable from a collision BDD (for the final result) */
/* Also count reachable from the state BDDs (for intermediate tracking) */
static int count_state_nodes(const BDDState *s) {
    if (visited_cap < bdd_count) {
        visited = (int *)realloc(visited, bdd_count * sizeof(int));
        visited_cap = bdd_count;
    }
    memset(visited, 0, visited_cap * sizeof(int));
    int total = 0;
    for (int r = 0; r < 8; r++)
        for (int b = 0; b < N; b++)
            total += count_nodes_rec(s->reg[r][b]);
    return total;
}

/* ================================================================
 * EVALUATE BDD (for verification)
 * ================================================================ */

static int bdd_eval(int node, const int *assignment) {
    while (bdd_nodes[node].var >= 0) {
        int v = bdd_nodes[node].var;
        node = assignment[v] ? bdd_nodes[node].hi : bdd_nodes[node].lo;
    }
    return node;  /* BDD_TRUE or BDD_FALSE */
}

/* ================================================================
 * COUNT SAT ASSIGNMENTS (count solutions in BDD)
 * ================================================================ */

static double count_sat_rec(int node, int var_level) {
    if (node == BDD_FALSE) return 0.0;
    if (node == BDD_TRUE) {
        /* All remaining variables are free */
        return ldexp(1.0, NVARS - var_level);
    }
    int node_var = bdd_nodes[node].var;
    /* Skip variables between var_level and node_var (they're "don't care") */
    double skip_factor = ldexp(1.0, node_var - var_level);
    double lo_count = count_sat_rec(bdd_nodes[node].lo, node_var + 1);
    double hi_count = count_sat_rec(bdd_nodes[node].hi, node_var + 1);
    return skip_factor * (lo_count + hi_count);
    /* Wait, this isn't right. For each skipped variable, both branches are possible,
       so we multiply by 2^(skipped vars). But each branch of the BDD node
       also corresponds to one assignment of the node's variable. */
    /* Actually: for skipped vars, multiply by 2^(#skipped) for each child */
}

/* Corrected SAT count */
static double count_sat(int root) {
    /* Use a recursive approach with memoization */
    /* For simplicity, just use the direct recursive formula */
    if (root == BDD_FALSE) return 0.0;
    if (root == BDD_TRUE) return ldexp(1.0, NVARS);

    /* Simple recursive: for node with variable v,
       count = 2^(v - parent_level) * (count(lo, v+1) + count(hi, v+1))
       But we call from level 0. */
    return count_sat_rec(root, 0);
}

/* Actually fix count_sat_rec properly */
/* The formula: if the current node is at variable v and we're at var_level,
   there are (v - var_level) "don't care" variables above this node.
   Each doubles the count. Then we branch on variable v:
   lo_count handles var_level = v+1, hi_count handles var_level = v+1.
   Total = 2^(v - var_level) * (lo_count + hi_count) / 2
         = 2^(v - var_level - 1) * (lo_count + hi_count)
   Wait no. Let me think again.

   count(node, level) = number of assignments to variables [level..NVARS-1]
                        that make the BDD evaluate to TRUE when we're at 'node'.

   If node is TRUE: return 2^(NVARS - level)
   If node is FALSE: return 0
   If node has variable v >= level:
     Variables level..v-1 are "don't care" (not tested by any node above).
     Each can be 0 or 1: factor of 2^(v - level).
     Then variable v splits into lo (v=0) and hi (v=1):
     count = 2^(v - level) * (count(lo, v+1) + count(hi, v+1))
     Wait, that overcounts. The 2^(v-level) accounts for the don't-care
     variables, and then for variable v itself, we sum lo and hi (one
     assignment each). So:
     count = 2^(v - level) * (count(lo, v+1) + count(hi, v+1))
     Hmm, but that means variable v is counted twice in 2^(v-level)?
     No: 2^(v-level) counts variables level, level+1, ..., v-1 (that's v-level vars).
     Variable v itself is handled by the branching (lo + hi).
     So total vars accounted for: (v - level) + 1 + remaining from recursion.
     This looks correct. Let me redo the function.
*/

/* OK I'll just rewrite it cleanly */

static double bdd_satcount(int node, int level) {
    if (node == BDD_FALSE) return 0.0;
    if (node == BDD_TRUE) return ldexp(1.0, NVARS - level);
    int v = bdd_nodes[node].var;
    double factor = ldexp(1.0, v - level);  /* 2^(#don't-care vars above) */
    double lo_c = bdd_satcount(bdd_nodes[node].lo, v + 1);
    double hi_c = bdd_satcount(bdd_nodes[node].hi, v + 1);
    return factor * (lo_c + hi_c);
}

/* ================================================================
 * MAIN
 * ================================================================ */

int main(int argc, char **argv) {
    setbuf(stdout, NULL);
    struct timespec t_start, t_now;
    clock_gettime(CLOCK_MONOTONIC, &t_start);

    N = (argc > 1) ? atoi(argv[1]) : 4;
    if (N < 2 || N > 32) { printf("N must be 2..32\n"); return 1; }
    MASK = (1U << N) - 1;
    MSB_BIT = 1U << (N - 1);
    NVARS = 4 * N;

    printf("=== Incremental BDD Construction for N=%d ===\n", N);
    printf("Variables: %d (4 words x %d bits)\n", NVARS, N);
    printf("Brute-force truth table would need 2^%d = %.0f entries\n\n",
           NVARS, ldexp(1.0, NVARS));

    /* ---- Initialize rotation parameters ---- */
    rS0[0]=scale_rot(2);  rS0[1]=scale_rot(13); rS0[2]=scale_rot(22);
    rS1[0]=scale_rot(6);  rS1[1]=scale_rot(11); rS1[2]=scale_rot(25);
    rs0[0]=scale_rot(7);  rs0[1]=scale_rot(18);  ss0=scale_rot(3);
    rs1[0]=scale_rot(17); rs1[1]=scale_rot(19);  ss1=scale_rot(10);
    for (int i = 0; i < 64; i++) KN[i] = K32[i] & MASK;
    for (int i = 0; i < 8; i++)  IVN[i] = IV32[i] & MASK;

    printf("Rotations: S0(%d,%d,%d) S1(%d,%d,%d) s0(%d,%d,>>%d) s1(%d,%d,>>%d)\n",
           rS0[0],rS0[1],rS0[2], rS1[0],rS1[1],rS1[2],
           rs0[0],rs0[1],ss0, rs1[0],rs1[1],ss1);

    /* ---- Search for valid candidate: try all kernel bits, fill=0xff ---- */
    uint32_t M0 = 0;
    int kernel_bit = -1;
    uint32_t M1[16], M2[16];
    uint32_t state1[8], state2[8], W1p[57], W2p[57];
    int found = 0;
    int best_colls = 0;
    uint32_t best_m0 = 0;
    int best_kbit = -1;

    for (int kbit = N-1; kbit >= 0 && !found; kbit--) {
        uint32_t kmsb = 1U << kbit;
        for (uint32_t m0 = 0; m0 < (1U << N); m0++) {
            for (int i = 0; i < 16; i++) { M1[i] = MASK; M2[i] = MASK; }
            M1[0] = m0; M2[0] = m0 ^ kmsb; M2[9] = MASK ^ kmsb;
            precompute(M1, state1, W1p);
            precompute(M2, state2, W2p);
            if (((state1[0] - state2[0]) & MASK) == 0) {
                /* Found valid candidate — use the first one for this kernel bit */
                if (!found) {
                    best_m0 = m0;
                    best_kbit = kbit;
                    found = 1;
                    break;
                }
            }
        }
    }
    if (!found) {
        printf("ERROR: no valid candidate found for N=%d\n", N);
        return 1;
    }
    M0 = best_m0;
    kernel_bit = best_kbit;
    uint32_t KMSB = 1U << kernel_bit;

    /* Finalize candidate */
    for (int i = 0; i < 16; i++) { M1[i] = MASK; M2[i] = MASK; }
    M1[0] = M0; M2[0] = M0 ^ KMSB; M2[9] = MASK ^ KMSB;
    precompute(M1, state1, W1p);
    precompute(M2, state2, W2p);

    printf("Candidate: M[0]=0x%x, fill=0x%x, kernel bit %d\n",
           M0, MASK, kernel_bit);
    printf("da56 = %u (verified = 0)\n\n", (state1[0] - state2[0]) & MASK);

    /* ---- Initialize BDD ---- */
    bdd_init();

    /* ---- Create BDD input variables ----
     * Interleaved ordering: var 4*b+w = word w, bit b
     * w=0: W57, w=1: W58, w=2: W59, w=3: W60
     */
    int W57_bdd[32], W58_bdd[32], W59_bdd[32], W60_bdd[32];
    for (int b = 0; b < N; b++) {
        W57_bdd[b] = bdd_var(4*b + 0);
        W58_bdd[b] = bdd_var(4*b + 1);
        W59_bdd[b] = bdd_var(4*b + 2);
        W60_bdd[b] = bdd_var(4*b + 3);
    }
    printf("Created %d BDD variables\n", NVARS);
    printf("BDD nodes after variable creation: %d\n\n", bdd_count - 2);

    /* ---- Initialize BDD states with concrete values from precomputation ---- */
    BDDState bs1, bs2;
    for (int r = 0; r < 8; r++) {
        bdd_const(bs1.reg[r], state1[r]);
        bdd_const(bs2.reg[r], state2[r]);
    }

    /* ---- Round constants as BDD words ---- */
    int K57_bdd[32], K58_bdd[32], K59_bdd[32], K60_bdd[32],
        K61_bdd[32], K62_bdd[32], K63_bdd[32];
    bdd_const(K57_bdd, KN[57]); bdd_const(K58_bdd, KN[58]);
    bdd_const(K59_bdd, KN[59]); bdd_const(K60_bdd, KN[60]);
    bdd_const(K61_bdd, KN[61]); bdd_const(K62_bdd, KN[62]);
    bdd_const(K63_bdd, KN[63]);

    /* ================================================================
     * ROUND 57: W1[57] = BDD vars, W2[57] = cascade
     * ================================================================ */
    printf("--- Round 57 ---\n");
    int W2_57[32];
    bdd_cascade_w2(W2_57, W57_bdd, &bs1, &bs2, K57_bdd);
    bdd_sha_round(&bs1, K57_bdd, W57_bdd);
    bdd_sha_round(&bs2, K57_bdd, W2_57);

    clock_gettime(CLOCK_MONOTONIC, &t_now);
    double el = (t_now.tv_sec-t_start.tv_sec)+(t_now.tv_nsec-t_start.tv_nsec)/1e9;
    int sn1 = count_state_nodes(&bs1);
    int sn2 = count_state_nodes(&bs2);
    printf("  BDD total nodes: %d, state1: %d, state2: %d (%.2fs)\n",
           bdd_count-2, sn1, sn2, el);

    /* ================================================================
     * ROUND 58: W1[58] = BDD vars, W2[58] = cascade
     * ================================================================ */
    printf("--- Round 58 ---\n");
    int W2_58[32];
    bdd_cascade_w2(W2_58, W58_bdd, &bs1, &bs2, K58_bdd);
    bdd_sha_round(&bs1, K58_bdd, W58_bdd);
    bdd_sha_round(&bs2, K58_bdd, W2_58);

    clock_gettime(CLOCK_MONOTONIC, &t_now);
    el = (t_now.tv_sec-t_start.tv_sec)+(t_now.tv_nsec-t_start.tv_nsec)/1e9;
    sn1 = count_state_nodes(&bs1);
    sn2 = count_state_nodes(&bs2);
    printf("  BDD total nodes: %d, state1: %d, state2: %d (%.2fs)\n",
           bdd_count-2, sn1, sn2, el);

    /* ================================================================
     * ROUND 59: W1[59] = BDD vars, W2[59] = cascade
     * ================================================================ */
    printf("--- Round 59 ---\n");
    int W2_59[32];
    bdd_cascade_w2(W2_59, W59_bdd, &bs1, &bs2, K59_bdd);
    bdd_sha_round(&bs1, K59_bdd, W59_bdd);
    bdd_sha_round(&bs2, K59_bdd, W2_59);

    clock_gettime(CLOCK_MONOTONIC, &t_now);
    el = (t_now.tv_sec-t_start.tv_sec)+(t_now.tv_nsec-t_start.tv_nsec)/1e9;
    sn1 = count_state_nodes(&bs1);
    sn2 = count_state_nodes(&bs2);
    printf("  BDD total nodes: %d, state1: %d, state2: %d (%.2fs)\n",
           bdd_count-2, sn1, sn2, el);

    /* ================================================================
     * ROUND 60: W1[60] = BDD vars, W2[60] = cascade
     * ================================================================ */
    printf("--- Round 60 ---\n");
    int W2_60[32];
    bdd_cascade_w2(W2_60, W60_bdd, &bs1, &bs2, K60_bdd);
    bdd_sha_round(&bs1, K60_bdd, W60_bdd);
    bdd_sha_round(&bs2, K60_bdd, W2_60);

    clock_gettime(CLOCK_MONOTONIC, &t_now);
    el = (t_now.tv_sec-t_start.tv_sec)+(t_now.tv_nsec-t_start.tv_nsec)/1e9;
    sn1 = count_state_nodes(&bs1);
    sn2 = count_state_nodes(&bs2);
    printf("  BDD total nodes: %d, state1: %d, state2: %d (%.2fs)\n",
           bdd_count-2, sn1, sn2, el);

    /* ================================================================
     * ROUNDS 61-63: schedule-determined message words
     * W[61] = sigma1(W[59]) + W[54] + sigma0(W[46]) + W[45]
     * W[62] = sigma1(W[60]) + W[55] + sigma0(W[47]) + W[46]
     * W[63] = sigma1(W[61]) + W[56] + sigma0(W[48]) + W[47]
     *
     * For path 1: W59 and W60 are BDD variables.
     * W[54], W[46], W[45], etc. are from precomputed schedule.
     * For path 2: W59b and W60b are BDD, plus precomputed schedule.
     * ================================================================ */

    /* W1[61] = sigma1(W59) + const */
    printf("--- Round 61 (schedule-determined) ---\n");
    int sig1_w59[32], W1_61[32];
    bdd_sigma1(sig1_w59, W59_bdd);
    int c61_1[32];
    bdd_const(c61_1, (W1p[54] + fns0(W1p[46]) + W1p[45]) & MASK);
    bdd_word_add(W1_61, sig1_w59, c61_1);

    /* W2[61] = sigma1(W2_59) + const2 */
    int sig1_w59b[32], W2_61[32];
    bdd_sigma1(sig1_w59b, W2_59);
    int c61_2[32];
    bdd_const(c61_2, (W2p[54] + fns0(W2p[46]) + W2p[45]) & MASK);
    bdd_word_add(W2_61, sig1_w59b, c61_2);

    bdd_sha_round(&bs1, K61_bdd, W1_61);
    bdd_sha_round(&bs2, K61_bdd, W2_61);

    clock_gettime(CLOCK_MONOTONIC, &t_now);
    el = (t_now.tv_sec-t_start.tv_sec)+(t_now.tv_nsec-t_start.tv_nsec)/1e9;
    sn1 = count_state_nodes(&bs1);
    sn2 = count_state_nodes(&bs2);
    printf("  BDD total nodes: %d, state1: %d, state2: %d (%.2fs)\n",
           bdd_count-2, sn1, sn2, el);

    /* W1[62] = sigma1(W60) + const */
    printf("--- Round 62 (schedule-determined) ---\n");
    int sig1_w60[32], W1_62[32];
    bdd_sigma1(sig1_w60, W60_bdd);
    int c62_1[32];
    bdd_const(c62_1, (W1p[55] + fns0(W1p[47]) + W1p[46]) & MASK);
    bdd_word_add(W1_62, sig1_w60, c62_1);

    int sig1_w60b[32], W2_62[32];
    bdd_sigma1(sig1_w60b, W2_60);
    int c62_2[32];
    bdd_const(c62_2, (W2p[55] + fns0(W2p[47]) + W2p[46]) & MASK);
    bdd_word_add(W2_62, sig1_w60b, c62_2);

    bdd_sha_round(&bs1, K62_bdd, W1_62);
    bdd_sha_round(&bs2, K62_bdd, W2_62);

    clock_gettime(CLOCK_MONOTONIC, &t_now);
    el = (t_now.tv_sec-t_start.tv_sec)+(t_now.tv_nsec-t_start.tv_nsec)/1e9;
    sn1 = count_state_nodes(&bs1);
    sn2 = count_state_nodes(&bs2);
    printf("  BDD total nodes: %d, state1: %d, state2: %d (%.2fs)\n",
           bdd_count-2, sn1, sn2, el);

    /* W1[63] = sigma1(W1_61) + const */
    printf("--- Round 63 (schedule-determined) ---\n");
    int sig1_w61_1[32], W1_63[32];
    bdd_sigma1(sig1_w61_1, W1_61);
    int c63_1[32];
    bdd_const(c63_1, (W1p[56] + fns0(W1p[48]) + W1p[47]) & MASK);
    bdd_word_add(W1_63, sig1_w61_1, c63_1);

    int sig1_w61_2[32], W2_63[32];
    bdd_sigma1(sig1_w61_2, W2_61);
    int c63_2[32];
    bdd_const(c63_2, (W2p[56] + fns0(W2p[48]) + W2p[47]) & MASK);
    bdd_word_add(W2_63, sig1_w61_2, c63_2);

    bdd_sha_round(&bs1, K63_bdd, W1_63);
    bdd_sha_round(&bs2, K63_bdd, W2_63);

    clock_gettime(CLOCK_MONOTONIC, &t_now);
    el = (t_now.tv_sec-t_start.tv_sec)+(t_now.tv_nsec-t_start.tv_nsec)/1e9;
    sn1 = count_state_nodes(&bs1);
    sn2 = count_state_nodes(&bs2);
    printf("  BDD total nodes: %d, state1: %d, state2: %d (%.2fs)\n",
           bdd_count-2, sn1, sn2, el);

    /* ================================================================
     * COLLISION CHECK: all 8 registers must match
     * collision = AND over all r,b of XNOR(s1.reg[r][b], s2.reg[r][b])
     * ================================================================ */
    printf("\n--- Collision BDD construction ---\n");
    int collision_bdd = BDD_TRUE;
    for (int r = 0; r < 8; r++) {
        for (int b = 0; b < N; b++) {
            int eq = bdd_xnor(bs1.reg[r][b], bs2.reg[r][b]);
            collision_bdd = bdd_and(collision_bdd, eq);
        }
        /* Report after each register */
        int cn = count_bdd_nodes(collision_bdd);
        printf("  After register %d (%c): collision BDD has %d nodes\n",
               r, "abcdefgh"[r], cn);
    }

    clock_gettime(CLOCK_MONOTONIC, &t_now);
    el = (t_now.tv_sec-t_start.tv_sec)+(t_now.tv_nsec-t_start.tv_nsec)/1e9;

    int final_nodes = count_bdd_nodes(collision_bdd);
    double sat_count = bdd_satcount(collision_bdd, 0);

    printf("\n=== RESULTS ===\n\n");
    printf("N = %d\n", N);
    printf("Collision BDD nodes: %d\n", final_nodes);
    printf("Collision count (SAT assignments): %.0f\n", sat_count);
    printf("Total BDD nodes allocated: %d\n", bdd_count - 2);
    printf("Peak BDD nodes: %d\n", bdd_peak - 2);
    printf("Cache hits: %llu, misses: %llu (%.1f%% hit rate)\n",
           (unsigned long long)cache_hits, (unsigned long long)cache_misses,
           100.0 * cache_hits / (cache_hits + cache_misses + 1));
    printf("Construction time: %.2fs\n", el);
    printf("NO TRUTH TABLE USED.\n\n");

    /* Validation */
    int expected_nodes = -1, expected_coll = -1;
    if (N == 4) { expected_nodes = 183; expected_coll = 49; }
    else if (N == 6) { expected_nodes = 615; }
    else if (N == 8) { expected_nodes = 4322; expected_coll = 260; }

    if (expected_nodes >= 0) {
        printf("Expected nodes: %d, got: %d — %s\n",
               expected_nodes, final_nodes,
               (final_nodes == expected_nodes) ? "MATCH" : "MISMATCH");
    }
    if (expected_coll >= 0) {
        printf("Expected collisions: %d, got: %.0f — %s\n",
               expected_coll, sat_count,
               ((int)sat_count == expected_coll) ? "MATCH" : "MISMATCH");
    }

    /* ---- Spot-check verification against concrete computation ---- */
    if (N <= 8) {
        printf("\n--- Spot-check verification ---\n");
        int checked = 0, verified = 0;
        uint32_t size = 1U << N;
        for (uint32_t w57 = 0; w57 < size && checked < 30; w57++) {
            for (uint32_t w58 = 0; w58 < size && checked < 30; w58++) {
                for (uint32_t w59 = 0; w59 < size && checked < 30; w59++) {
                    for (uint32_t w60 = 0; w60 < size && checked < 30; w60++) {
                        /* Build assignment */
                        int assign[128];
                        memset(assign, 0, sizeof(assign));
                        for (int b = 0; b < N; b++) {
                            assign[4*b+0] = (w57 >> b) & 1;
                            assign[4*b+1] = (w58 >> b) & 1;
                            assign[4*b+2] = (w59 >> b) & 1;
                            assign[4*b+3] = (w60 >> b) & 1;
                        }
                        int bdd_result = bdd_eval(collision_bdd, assign);

                        /* Concrete check */
                        uint32_t sa[8], sb[8];
                        memcpy(sa, state1, 32); memcpy(sb, state2, 32);

                        /* Round 57 */
                        uint32_t r1_h = (sa[7]+fnS1(sa[4])+fnCh(sa[4],sa[5],sa[6])+KN[57])&MASK;
                        uint32_t r2_h = (sb[7]+fnS1(sb[4])+fnCh(sb[4],sb[5],sb[6])+KN[57])&MASK;
                        uint32_t T21_h = (fnS0(sa[0])+fnMj(sa[0],sa[1],sa[2]))&MASK;
                        uint32_t T22_h = (fnS0(sb[0])+fnMj(sb[0],sb[1],sb[2]))&MASK;
                        uint32_t w57b = (w57 + r1_h - r2_h + T21_h - T22_h) & MASK;

                        uint32_t T1a = (sa[7]+fnS1(sa[4])+fnCh(sa[4],sa[5],sa[6])+KN[57]+w57)&MASK;
                        uint32_t T2a = (fnS0(sa[0])+fnMj(sa[0],sa[1],sa[2]))&MASK;
                        uint32_t T1b = (sb[7]+fnS1(sb[4])+fnCh(sb[4],sb[5],sb[6])+KN[57]+w57b)&MASK;
                        uint32_t T2b = (fnS0(sb[0])+fnMj(sb[0],sb[1],sb[2]))&MASK;
                        sa[7]=sa[6];sa[6]=sa[5];sa[5]=sa[4];sa[4]=(sa[3]+T1a)&MASK;
                        sa[3]=sa[2];sa[2]=sa[1];sa[1]=sa[0];sa[0]=(T1a+T2a)&MASK;
                        sb[7]=sb[6];sb[6]=sb[5];sb[5]=sb[4];sb[4]=(sb[3]+T1b)&MASK;
                        sb[3]=sb[2];sb[2]=sb[1];sb[1]=sb[0];sb[0]=(T1b+T2b)&MASK;

                        /* Round 58 */
                        r1_h=(sa[7]+fnS1(sa[4])+fnCh(sa[4],sa[5],sa[6])+KN[58])&MASK;
                        r2_h=(sb[7]+fnS1(sb[4])+fnCh(sb[4],sb[5],sb[6])+KN[58])&MASK;
                        T21_h=(fnS0(sa[0])+fnMj(sa[0],sa[1],sa[2]))&MASK;
                        T22_h=(fnS0(sb[0])+fnMj(sb[0],sb[1],sb[2]))&MASK;
                        uint32_t w58b=(w58+r1_h-r2_h+T21_h-T22_h)&MASK;
                        T1a=(sa[7]+fnS1(sa[4])+fnCh(sa[4],sa[5],sa[6])+KN[58]+w58)&MASK;
                        T2a=(fnS0(sa[0])+fnMj(sa[0],sa[1],sa[2]))&MASK;
                        T1b=(sb[7]+fnS1(sb[4])+fnCh(sb[4],sb[5],sb[6])+KN[58]+w58b)&MASK;
                        T2b=(fnS0(sb[0])+fnMj(sb[0],sb[1],sb[2]))&MASK;
                        sa[7]=sa[6];sa[6]=sa[5];sa[5]=sa[4];sa[4]=(sa[3]+T1a)&MASK;
                        sa[3]=sa[2];sa[2]=sa[1];sa[1]=sa[0];sa[0]=(T1a+T2a)&MASK;
                        sb[7]=sb[6];sb[6]=sb[5];sb[5]=sb[4];sb[4]=(sb[3]+T1b)&MASK;
                        sb[3]=sb[2];sb[2]=sb[1];sb[1]=sb[0];sb[0]=(T1b+T2b)&MASK;

                        /* Round 59 */
                        r1_h=(sa[7]+fnS1(sa[4])+fnCh(sa[4],sa[5],sa[6])+KN[59])&MASK;
                        r2_h=(sb[7]+fnS1(sb[4])+fnCh(sb[4],sb[5],sb[6])+KN[59])&MASK;
                        T21_h=(fnS0(sa[0])+fnMj(sa[0],sa[1],sa[2]))&MASK;
                        T22_h=(fnS0(sb[0])+fnMj(sb[0],sb[1],sb[2]))&MASK;
                        uint32_t w59b=(w59+r1_h-r2_h+T21_h-T22_h)&MASK;
                        T1a=(sa[7]+fnS1(sa[4])+fnCh(sa[4],sa[5],sa[6])+KN[59]+w59)&MASK;
                        T2a=(fnS0(sa[0])+fnMj(sa[0],sa[1],sa[2]))&MASK;
                        T1b=(sb[7]+fnS1(sb[4])+fnCh(sb[4],sb[5],sb[6])+KN[59]+w59b)&MASK;
                        T2b=(fnS0(sb[0])+fnMj(sb[0],sb[1],sb[2]))&MASK;
                        sa[7]=sa[6];sa[6]=sa[5];sa[5]=sa[4];sa[4]=(sa[3]+T1a)&MASK;
                        sa[3]=sa[2];sa[2]=sa[1];sa[1]=sa[0];sa[0]=(T1a+T2a)&MASK;
                        sb[7]=sb[6];sb[6]=sb[5];sb[5]=sb[4];sb[4]=(sb[3]+T1b)&MASK;
                        sb[3]=sb[2];sb[2]=sb[1];sb[1]=sb[0];sb[0]=(T1b+T2b)&MASK;

                        /* Round 60 */
                        r1_h=(sa[7]+fnS1(sa[4])+fnCh(sa[4],sa[5],sa[6])+KN[60])&MASK;
                        r2_h=(sb[7]+fnS1(sb[4])+fnCh(sb[4],sb[5],sb[6])+KN[60])&MASK;
                        T21_h=(fnS0(sa[0])+fnMj(sa[0],sa[1],sa[2]))&MASK;
                        T22_h=(fnS0(sb[0])+fnMj(sb[0],sb[1],sb[2]))&MASK;
                        uint32_t w60b=(w60+r1_h-r2_h+T21_h-T22_h)&MASK;
                        T1a=(sa[7]+fnS1(sa[4])+fnCh(sa[4],sa[5],sa[6])+KN[60]+w60)&MASK;
                        T2a=(fnS0(sa[0])+fnMj(sa[0],sa[1],sa[2]))&MASK;
                        T1b=(sb[7]+fnS1(sb[4])+fnCh(sb[4],sb[5],sb[6])+KN[60]+w60b)&MASK;
                        T2b=(fnS0(sb[0])+fnMj(sb[0],sb[1],sb[2]))&MASK;
                        sa[7]=sa[6];sa[6]=sa[5];sa[5]=sa[4];sa[4]=(sa[3]+T1a)&MASK;
                        sa[3]=sa[2];sa[2]=sa[1];sa[1]=sa[0];sa[0]=(T1a+T2a)&MASK;
                        sb[7]=sb[6];sb[6]=sb[5];sb[5]=sb[4];sb[4]=(sb[3]+T1b)&MASK;
                        sb[3]=sb[2];sb[2]=sb[1];sb[1]=sb[0];sb[0]=(T1b+T2b)&MASK;

                        /* Rounds 61-63 */
                        uint32_t cw61a=(fns1(w59)+W1p[54]+fns0(W1p[46])+W1p[45])&MASK;
                        uint32_t cw61b=(fns1(w59b)+W2p[54]+fns0(W2p[46])+W2p[45])&MASK;
                        T1a=(sa[7]+fnS1(sa[4])+fnCh(sa[4],sa[5],sa[6])+KN[61]+cw61a)&MASK;
                        T2a=(fnS0(sa[0])+fnMj(sa[0],sa[1],sa[2]))&MASK;
                        T1b=(sb[7]+fnS1(sb[4])+fnCh(sb[4],sb[5],sb[6])+KN[61]+cw61b)&MASK;
                        T2b=(fnS0(sb[0])+fnMj(sb[0],sb[1],sb[2]))&MASK;
                        sa[7]=sa[6];sa[6]=sa[5];sa[5]=sa[4];sa[4]=(sa[3]+T1a)&MASK;
                        sa[3]=sa[2];sa[2]=sa[1];sa[1]=sa[0];sa[0]=(T1a+T2a)&MASK;
                        sb[7]=sb[6];sb[6]=sb[5];sb[5]=sb[4];sb[4]=(sb[3]+T1b)&MASK;
                        sb[3]=sb[2];sb[2]=sb[1];sb[1]=sb[0];sb[0]=(T1b+T2b)&MASK;

                        uint32_t cw62a=(fns1(w60)+W1p[55]+fns0(W1p[47])+W1p[46])&MASK;
                        uint32_t cw62b=(fns1(w60b)+W2p[55]+fns0(W2p[47])+W2p[46])&MASK;
                        T1a=(sa[7]+fnS1(sa[4])+fnCh(sa[4],sa[5],sa[6])+KN[62]+cw62a)&MASK;
                        T2a=(fnS0(sa[0])+fnMj(sa[0],sa[1],sa[2]))&MASK;
                        T1b=(sb[7]+fnS1(sb[4])+fnCh(sb[4],sb[5],sb[6])+KN[62]+cw62b)&MASK;
                        T2b=(fnS0(sb[0])+fnMj(sb[0],sb[1],sb[2]))&MASK;
                        sa[7]=sa[6];sa[6]=sa[5];sa[5]=sa[4];sa[4]=(sa[3]+T1a)&MASK;
                        sa[3]=sa[2];sa[2]=sa[1];sa[1]=sa[0];sa[0]=(T1a+T2a)&MASK;
                        sb[7]=sb[6];sb[6]=sb[5];sb[5]=sb[4];sb[4]=(sb[3]+T1b)&MASK;
                        sb[3]=sb[2];sb[2]=sb[1];sb[1]=sb[0];sb[0]=(T1b+T2b)&MASK;

                        uint32_t cw63a=(fns1(cw61a)+W1p[56]+fns0(W1p[48])+W1p[47])&MASK;
                        uint32_t cw63b=(fns1(cw61b)+W2p[56]+fns0(W2p[48])+W2p[47])&MASK;
                        T1a=(sa[7]+fnS1(sa[4])+fnCh(sa[4],sa[5],sa[6])+KN[63]+cw63a)&MASK;
                        T2a=(fnS0(sa[0])+fnMj(sa[0],sa[1],sa[2]))&MASK;
                        T1b=(sb[7]+fnS1(sb[4])+fnCh(sb[4],sb[5],sb[6])+KN[63]+cw63b)&MASK;
                        T2b=(fnS0(sb[0])+fnMj(sb[0],sb[1],sb[2]))&MASK;
                        sa[7]=sa[6];sa[6]=sa[5];sa[5]=sa[4];sa[4]=(sa[3]+T1a)&MASK;
                        sa[3]=sa[2];sa[2]=sa[1];sa[1]=sa[0];sa[0]=(T1a+T2a)&MASK;
                        sb[7]=sb[6];sb[6]=sb[5];sb[5]=sb[4];sb[4]=(sb[3]+T1b)&MASK;
                        sb[3]=sb[2];sb[2]=sb[1];sb[1]=sb[0];sb[0]=(T1b+T2b)&MASK;

                        int coll = 1;
                        for (int r = 0; r < 8; r++)
                            if (sa[r] != sb[r]) { coll = 0; break; }

                        if (bdd_result != coll) {
                            printf("  MISMATCH w57=%u w58=%u w59=%u w60=%u: "
                                   "BDD=%d concrete=%d\n",
                                   w57, w58, w59, w60, bdd_result, coll);
                        } else {
                            verified++;
                        }
                        checked++;
                    }
                }
            }
        }
        printf("Verified %d/%d spot-checks PASS\n", verified, checked);
    }

    /* Scaling analysis */
    printf("\n--- Scaling Analysis ---\n");
    printf("N=%d: %d BDD nodes (incremental, no truth table)\n", N, final_nodes);
    if (N == 4 || N == 6 || N == 8) {
        printf("\nKnown data points:\n");
        printf("  N=4:  183 nodes\n");
        printf("  N=6:  615 nodes\n");
        printf("  N=8: 4322 nodes\n");
        printf("\nScaling: nodes = c * N^alpha\n");
        printf("  N=4->6: alpha = %.3f\n", log(615.0/183.0) / log(6.0/4.0));
        printf("  N=4->8: alpha = %.3f\n", log(4322.0/183.0) / log(8.0/4.0));
        printf("  N=6->8: alpha = %.3f\n", log(4322.0/615.0) / log(8.0/6.0));
    }

    printf("\nEvidence level: %s\n",
           (expected_nodes >= 0 && final_nodes == expected_nodes) ?
           "VERIFIED (matches truth-table BDD)" :
           "NEW (no truth-table reference available)");

    /* Memory stats */
    printf("\nMemory: BDD nodes %.1f MB, unique table %.1f MB, computed table %.1f MB\n",
           (double)bdd_count * sizeof(BDDNode) / (1 << 20),
           (double)uentry_count * sizeof(UEntry) / (1 << 20),
           (double)CHASH_SIZE * sizeof(CacheEntry) / (1 << 20));

    free(bdd_nodes); free(uentry_pool); free(uhash_table);
    free(comp_table); free(visited);
    return 0;
}
