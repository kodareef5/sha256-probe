/*
 * bitserial_quotient_dp.c — Bit-serial DP with GF(2) state canonicalization
 *
 * Process variables in BDD interleaved order: W57[0], W58[0], W59[0], W60[0],
 * W57[1], W58[1], ... This matches the BDD variable ordering where the
 * completion quotient has width = #collisions.
 *
 * At each variable, branch on its value (0 or 1). Add GF(2) constraint.
 * After processing 4 variables (one "slice" = all 4 words at one bit position),
 * run the SHA-256 round computations for that bit and track carry states.
 *
 * The state after each slice is: (concrete carry-outs, GF(2) system canonical form)
 * Count distinct states → this is the quotient width at that depth.
 *
 * Key: register bits at OTHER positions (needed for Sigma rotations) are kept
 * as SYMBOLIC affine forms. They're resolved when their bit position is processed.
 *
 * Compile: gcc -O3 -march=native -o bsq_dp bitserial_quotient_dp.c -lm
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>

#define N 4
#define MASK ((1U<<N)-1)
#define MSB (1U<<(N-1))
#define NV (4*N)  /* Only W1[57..60] variables — W2 derived from cascade */
#define MAXPOOL (1<<22)  /* 4M states max */

/* ---- Affine Form: val = popcount(m & vars) % 2 XOR c ---- */
typedef struct { uint32_t m; uint8_t c; } AF;
static inline AF af_xor(AF a, AF b) { return (AF){a.m^b.m, (uint8_t)(a.c^b.c)}; }
static inline AF af_const(int v) { return (AF){0, (uint8_t)(v&1)}; }
static inline AF af_var(int i) { return (AF){1U<<i, 0}; }
static inline int af_is_const(AF f) { return f.m==0; }
static inline int af_val(AF f) { return f.c; }

/* ---- GF(2) RREF System ---- */
typedef struct { AF rows[NV]; uint8_t has[NV]; } G2;

static void g2_init(G2 *s) { memset(s, 0, sizeof(G2)); }
static int g2_add(G2 *s, AF f) {
    for (int i = NV-1; i >= 0; i--)
        if ((f.m >> i) & 1 && s->has[i]) f = af_xor(f, s->rows[i]);
    if (f.m == 0) return f.c ? 0 : 1;
    int p = 31 - __builtin_clz(f.m);
    s->rows[p] = f; s->has[p] = 1;
    for (int i = 0; i < NV; i++)
        if (i != p && s->has[i] && ((s->rows[i].m >> p) & 1))
            s->rows[i] = af_xor(s->rows[i], f);
    return 1;
}
static AF g2_res(const G2 *s, AF f) {
    for (int i = NV-1; i >= 0; i--)
        if ((f.m >> i) & 1 && s->has[i]) f = af_xor(f, s->rows[i]);
    return f;
}

/* Canonicalize GF(2) system → hash for deduplication */
static uint64_t g2_hash(const G2 *s) {
    uint64_t h = 0xcbf29ce484222325ULL;
    for (int i = 0; i < NV; i++) {
        if (s->has[i]) {
            h ^= (uint64_t)s->rows[i].m * 0x100000001b3ULL;
            h ^= (uint64_t)s->rows[i].c * 0x517cc1b727220a95ULL;
        }
        h = (h << 7) | (h >> 57);
    }
    return h;
}

/* ---- State: registers (as AF per bit) + GF(2) system ---- */
typedef struct {
    G2 sys;
    AF r1[8][N];  /* msg1 registers */
    AF r2[8][N];  /* msg2 registers */
    /* Carry state: for each addition being tracked, carry-in for next bit */
    /* 7 adds per round × 7 rounds × 2 msgs = 98 carries */
    int carries[98];
} ST;

static ST *PA, *PB;
static int nA;

/* SHA constants */
static int rS0[3], rS1[3];
static uint32_t KN[64], s1c[8], s2c[8], W1p[57], W2p[57];
static int SR(int k) { int r=(int)rint((double)k*N/32.0); return r<1?1:r; }
static uint32_t ror_n(uint32_t x, int k) { k%=N; return ((x>>k)|(x<<(N-k)))&MASK; }
static uint32_t bfS1(uint32_t e) { return ror_n(e,rS1[0])^ror_n(e,rS1[1])^ror_n(e,rS1[2]); }
static uint32_t bfS0(uint32_t a) { return ror_n(a,rS0[0])^ror_n(a,rS0[1])^ror_n(a,rS0[2]); }
static uint32_t bfCh(uint32_t e,uint32_t f,uint32_t g){return((e&f)^((~e)&g))&MASK;}
static uint32_t bfMj(uint32_t a,uint32_t b,uint32_t c){return((a&b)^(a&c)^(b&c))&MASK;}
static uint32_t bfs0(uint32_t x){return ror_n(x,SR(7))^ror_n(x,SR(18))^((x>>SR(3))&MASK);}
static uint32_t bfs1(uint32_t x){return ror_n(x,SR(17))^ror_n(x,SR(19))^((x>>SR(10))&MASK);}

/* af_Sigma: XOR of rotated forms (free, no branching) */
static AF af_Sigma1_bit(const AF e[N], int bit) {
    return af_xor(af_xor(e[(bit+rS1[0])%N], e[(bit+rS1[1])%N]), e[(bit+rS1[2])%N]);
}
static AF af_Sigma0_bit(const AF a[N], int bit) {
    return af_xor(af_xor(a[(bit+rS0[0])%N], a[(bit+rS0[1])%N]), a[(bit+rS0[2])%N]);
}

/* ---- Process one SHA round at a SINGLE bit position ---- */
/* This is the heart: process bit k of round r for one message.
 * Requires: register AFs (may be symbolic at other bit positions).
 * Produces: carry-outs for the 7 additions, new register values at bit k.
 * Branches on symbolic operands in Ch, Maj, and addition carries. */

static int process_round_bit(int n_in, int round, int bit, int is_msg2) {
    int n = n_in;

    for (int i = 0; i < n; i++) {
        AF (*R)[N] = is_msg2 ? PA[i].r2 : PA[i].r1;
        int carry_base = (round * 7 + (is_msg2 ? 49 : 0));

        /* 1. Sigma1(e)[bit] — XOR of rotated bits (free, symbolic OK) */
        AF sig1k = af_Sigma1_bit(R[4], bit);

        /* 2. Ch(e,f,g)[bit] — NONLINEAR: branch if e[bit] is symbolic */
        AF ek = g2_res(&PA[i].sys, R[4][bit]);
        AF fk = R[5][bit], gk = R[6][bit];
        AF chk;

        if (af_is_const(ek)) {
            chk = af_val(ek) ? fk : gk;
        } else {
            /* Need to branch on ek — but we're in a loop over states.
             * For this first version, we'll handle branching by expanding
             * the pool. Branch e=0 and e=1. */
            /* TODO: implement pool expansion for Ch branching */
            /* For now, just use a heuristic: resolve against GF(2) system */
            chk = af_const(0); /* placeholder — need proper branching */
        }

        /* 3. T1 chain: h + Sig1 + Ch + K + W (4 additions at bit k) */
        AF hk = R[7][bit];
        int Kbit = (KN[57 + round] >> bit) & 1;

        /* For free rounds (0-3): W is a variable. For schedule rounds (4-6): computed */
        AF wk;
        if (round < 4) {
            /* W1[57+round] bit k is variable # (round*N + bit) */
            wk = af_var(round * N + bit);
        } else {
            /* Schedule-determined: need sigma1(W[59+round-4]) etc.
             * This requires full N-bit words, not just bit k. Complex. */
            wk = af_const(0); /* placeholder */
        }

        /* Sequential additions with carry tracking */
        /* add1: h + Sig1 */
        int ci = PA[i].carries[carry_base + 0];
        AF h_res = g2_res(&PA[i].sys, hk);
        AF s1_res = g2_res(&PA[i].sys, sig1k);

        if (af_is_const(h_res) && af_is_const(s1_res)) {
            int hv = af_val(h_res), sv = af_val(s1_res);
            int sum1 = hv ^ sv ^ ci;
            int co1 = (hv & sv) | (hv & ci) | (sv & ci);
            PA[i].carries[carry_base + 0] = co1;
            /* Continue with sum1... */
            (void)sum1; /* suppress warning */
        }
        /* ... this is getting very complex for inline code ... */
    }

    return n; /* placeholder */
}

int main() {
    setbuf(stdout, NULL);
    rS0[0]=SR(2);rS0[1]=SR(13);rS0[2]=SR(22);
    rS1[0]=SR(6);rS1[1]=SR(11);rS1[2]=SR(25);
    for(int i=0;i<64;i++)KN[i]=((uint32_t[]){0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2}[i])&MASK;

    s1c[0]=0x9;s1c[1]=0x8;s1c[2]=0xd;s1c[3]=0x5;s1c[4]=0x6;s1c[5]=0xe;s1c[6]=0xb;s1c[7]=0xf;
    s2c[0]=0x9;s2c[1]=0xa;s2c[2]=0xd;s2c[3]=0x8;s2c[4]=0x5;s2c[5]=0x0;s2c[6]=0xc;s2c[7]=0x1;

    {uint32_t M1[16],M2[16];
     for(int i=0;i<16;i++){M1[i]=MASK;M2[i]=MASK;}
     M1[0]=0;M2[0]=MSB;M2[9]=MASK^MSB;
     for(int i=0;i<16;i++)W1p[i]=M1[i]&MASK;
     for(int i=16;i<57;i++)W1p[i]=(bfs1(W1p[i-2])+W1p[i-7]+bfs0(W1p[i-15])+W1p[i-16])&MASK;
     for(int i=0;i<16;i++)W2p[i]=M2[i]&MASK;
     for(int i=16;i<57;i++)W2p[i]=(bfs1(W2p[i-2])+W2p[i-7]+bfs0(W2p[i-15])+W2p[i-16])&MASK;
    }

    PA = calloc(MAXPOOL, sizeof(ST));
    PB = calloc(MAXPOOL, sizeof(ST));

    printf("=== Bit-Serial Quotient DP, N=%d ===\n\n", N);
    printf("Processing in BDD interleaved order (bit-first).\n");
    printf("Measuring GF(2) quotient width at each depth.\n\n");

    /* Initialize: one state with all register AFs from state56 */
    nA = 1;
    g2_init(&PA[0].sys);
    for (int r = 0; r < 8; r++)
        for (int b = 0; b < N; b++) {
            PA[0].r1[r][b] = af_const((s1c[r] >> b) & 1);
            PA[0].r2[r][b] = af_const((s2c[r] >> b) & 1);
        }
    memset(PA[0].carries, 0, sizeof(PA[0].carries));

    /* ---- Main DP loop: process variable by variable ---- */
    /* BDD order: var 0 = W57[0], var 1 = W58[0], var 2 = W59[0], var 3 = W60[0],
     *            var 4 = W57[1], var 5 = W58[1], ...
     * At each variable, branch on its value (0 or 1). */

    for (int depth = 0; depth < NV; depth++) {
        int word_idx = depth % 4;   /* 0=W57, 1=W58, 2=W59, 3=W60 */
        int bit_idx = depth / 4;

        /* For each state in pool: branch on this variable */
        int nout = 0;
        for (int i = 0; i < nA; i++) {
            for (int val = 0; val <= 1; val++) {
                if (nout >= MAXPOOL) goto pool_full;
                PB[nout] = PA[i];
                /* Add constraint: var = val */
                AF var_af = af_var(depth);
                AF con = var_af; con.c ^= val;
                if (!g2_add(&PB[nout].sys, con)) continue;
                nout++;
            }
        }
        pool_full:;

        /* Swap pools */
        ST *tmp = PA; PA = PB; PB = tmp;
        nA = nout;

        /* After processing all 4 words at one bit position (depth % 4 == 3),
         * we have a "slice boundary." At this point, all 4 W bits at this
         * bit position are determined, and we could run the round function.
         * But Sigma rotations need OTHER bit positions...
         *
         * For now: just measure pool size (= simple branching quotient) */

        /* Deduplicate by GF(2) canonical form */
        /* Simple: hash each state's GF(2) system and count unique hashes */
        /* (Full dedup would merge states — for measurement, counting suffices) */
        uint64_t *hashes = malloc(nA * sizeof(uint64_t));
        for (int i = 0; i < nA; i++) hashes[i] = g2_hash(&PA[i].sys);

        /* Count distinct hashes (simple sort + unique) */
        for (int i = 0; i < nA - 1; i++)
            for (int j = i+1; j < nA; j++)
                if (hashes[i] > hashes[j]) { uint64_t t = hashes[i]; hashes[i] = hashes[j]; hashes[j] = t; }
        int distinct = (nA > 0) ? 1 : 0;
        for (int i = 1; i < nA; i++) if (hashes[i] != hashes[i-1]) distinct++;
        free(hashes);

        const char *wn[] = {"W57","W58","W59","W60"};
        printf("Depth %2d (%s[%d]): pool=%6d, distinct_g2=%6d\n",
               depth, wn[word_idx], bit_idx, nA, distinct);
    }

    printf("\n=== Collision check ===\n");
    /* After all NV variables are fixed, each state has ALL variables determined.
     * Run the round function concretely and check collision. */
    int collisions = 0;
    for (int i = 0; i < nA; i++) {
        /* Extract W1 values from the GF(2) system */
        uint32_t W1[4] = {0,0,0,0};
        int ok = 1;
        for (int v = 0; v < NV; v++) {
            AF f = g2_res(&PA[i].sys, af_var(v));
            if (!af_is_const(f)) { ok = 0; break; }
            int word = v % 4, bit = v / 4;
            W1[word] |= (af_val(f) << bit);
        }
        if (!ok) continue;

        /* Run brute-force check */
        uint32_t st1[8], st2[8];
        for (int j = 0; j < 8; j++) { st1[j] = s1c[j]; st2[j] = s2c[j]; }

        /* Cascade W2 + 7 rounds */
        uint32_t W2[4];
        uint32_t stA[8], stB[8];
        memcpy(stA, s1c, 32); memcpy(stB, s2c, 32);
        for (int r = 0; r < 4; r++) {
            uint32_t t1nw1 = (stA[7]+bfS1(stA[4])+bfCh(stA[4],stA[5],stA[6])+KN[57+r])&MASK;
            uint32_t t1nw2 = (stB[7]+bfS1(stB[4])+bfCh(stB[4],stB[5],stB[6])+KN[57+r])&MASK;
            uint32_t t2_1 = (bfS0(stA[0])+bfMj(stA[0],stA[1],stA[2]))&MASK;
            uint32_t t2_2 = (bfS0(stB[0])+bfMj(stB[0],stB[1],stB[2]))&MASK;
            W2[r] = (W1[r] + ((t1nw1+t2_1)-(t1nw2+t2_2)))&MASK;
            uint32_t t1_1=(t1nw1+W1[r])&MASK, t1_2=(t1nw2+W2[r])&MASK;
            uint32_t nA1=(t1_1+t2_1)&MASK, nA2=(t1_2+t2_2)&MASK;
            stA[7]=stA[6];stA[6]=stA[5];stA[5]=stA[4];stA[4]=(stA[3]+t1_1)&MASK;
            stA[3]=stA[2];stA[2]=stA[1];stA[1]=stA[0];stA[0]=nA1;
            stB[7]=stB[6];stB[6]=stB[5];stB[5]=stB[4];stB[4]=(stB[3]+t1_2)&MASK;
            stB[3]=stB[2];stB[2]=stB[1];stB[1]=stB[0];stB[0]=nA2;
        }
        /* Schedule + remaining rounds */
        uint32_t Wf1[64], Wf2[64];
        memcpy(Wf1, W1p, 57*4); memcpy(Wf2, W2p, 57*4);
        for(int j=0;j<4;j++){Wf1[57+j]=W1[j];Wf2[57+j]=W2[j];}
        for(int t=61;t<64;t++){
            Wf1[t]=(bfs1(Wf1[t-2])+Wf1[t-7]+bfs0(Wf1[t-15])+Wf1[t-16])&MASK;
            Wf2[t]=(bfs1(Wf2[t-2])+Wf2[t-7]+bfs0(Wf2[t-15])+Wf2[t-16])&MASK;
        }
        memcpy(stA,s1c,32);memcpy(stB,s2c,32);
        for(int r=0;r<7;r++){
            uint32_t T1a=(stA[7]+bfS1(stA[4])+bfCh(stA[4],stA[5],stA[6])+KN[57+r]+Wf1[57+r])&MASK;
            uint32_t T2a=(bfS0(stA[0])+bfMj(stA[0],stA[1],stA[2]))&MASK;
            stA[7]=stA[6];stA[6]=stA[5];stA[5]=stA[4];stA[4]=(stA[3]+T1a)&MASK;
            stA[3]=stA[2];stA[2]=stA[1];stA[1]=stA[0];stA[0]=(T1a+T2a)&MASK;
            uint32_t T1b=(stB[7]+bfS1(stB[4])+bfCh(stB[4],stB[5],stB[6])+KN[57+r]+Wf2[57+r])&MASK;
            uint32_t T2b=(bfS0(stB[0])+bfMj(stB[0],stB[1],stB[2]))&MASK;
            stB[7]=stB[6];stB[6]=stB[5];stB[5]=stB[4];stB[4]=(stB[3]+T1b)&MASK;
            stB[3]=stB[2];stB[2]=stB[1];stB[1]=stB[0];stB[0]=(T1b+T2b)&MASK;
        }
        int coll = 1;
        for(int j=0;j<8;j++) if(stA[j]!=stB[j]){coll=0;break;}
        if (coll) collisions++;
    }

    printf("Collisions found: %d (expected 49)\n", collisions);
    free(PA); free(PB);
    return 0;
}
