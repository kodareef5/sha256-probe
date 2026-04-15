/*
 * bdd_hybrid.c — Hybrid concrete/BDD collision finder
 *
 * Outer loop: enumerate W57, W58 concretely (2^{2N} iterations).
 * Inner BDD: build collision BDD over W59, W60 (2N variables) with
 *            concrete state after round 58.
 * Combine: OR partial BDDs with W57/W58 constraints to get full BDD.
 *
 * This avoids the intermediate BDD blowup of the pure incremental approach
 * while still constructing the polynomial-sized collision BDD.
 *
 * Key advantage: inner BDD has only 2N variables, so intermediate BDDs
 * stay O(2^{2N}) at worst — much better than O(2^{4N}) of the truth table.
 *
 * Compile: gcc -O3 -march=native -Xclang -fopenmp \
 *          -I/opt/homebrew/opt/libomp/include \
 *          -L/opt/homebrew/opt/libomp/lib -lomp \
 *          -o bdd_hybrid bdd_hybrid.c -lm
 *
 * Usage: ./bdd_hybrid [N]   (default N=4)
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <time.h>

/* ================================================================
 * PARAMETERS
 * ================================================================ */

static int N;
static uint32_t MASK, MSB_BIT;
static int NVARS;       /* 4*N total BDD variables in the full BDD */
static int INNER_NVARS;  /* 2*N variables for the inner BDD (W59, W60) */

/* ================================================================
 * BDD CORE (same as bdd_incremental.c but with larger tables)
 * ================================================================ */

typedef struct {
    int var, lo, hi;
} BDDNode;

#define BDD_FALSE 0
#define BDD_TRUE  1

static BDDNode *bdd_nodes = NULL;
static int bdd_count = 0;
static int bdd_cap = 0;

/* Unique table: index-based chains (no dangling pointers on realloc) */
#define UHASH_BITS 22
#define UHASH_SIZE (1 << UHASH_BITS)
#define UHASH_MASK (UHASH_SIZE - 1)

typedef struct {
    int var, lo, hi, node_id;
    int next;
} UEntry;

static int *uhash_table = NULL;
static UEntry *uentry_pool = NULL;
static int uentry_count = 0;
static int uentry_cap = 0;

/* Computed table */
#define CHASH_BITS 22
#define CHASH_SIZE (1 << CHASH_BITS)
#define CHASH_MASK (CHASH_SIZE - 1)

typedef struct {
    int op, f, g, result;
} CacheEntry;

static CacheEntry *comp_table = NULL;

static void bdd_init(void) {
    bdd_cap = 1 << 20;
    bdd_nodes = (BDDNode *)malloc(bdd_cap * sizeof(BDDNode));
    bdd_nodes[0] = (BDDNode){-1, 0, 0};
    bdd_nodes[1] = (BDDNode){-1, 1, 1};
    bdd_count = 2;

    uhash_table = (int *)malloc(UHASH_SIZE * sizeof(int));
    for (int i = 0; i < UHASH_SIZE; i++) uhash_table[i] = -1;
    uentry_cap = 1 << 20;
    uentry_pool = (UEntry *)malloc(uentry_cap * sizeof(UEntry));
    uentry_count = 0;

    comp_table = (CacheEntry *)calloc(CHASH_SIZE, sizeof(CacheEntry));
    for (int i = 0; i < CHASH_SIZE; i++) comp_table[i].op = -1;
}

static inline uint32_t uhash_fn(int var, int lo, int hi) {
    return ((uint32_t)var * 7919u + (uint32_t)lo * 104729u + (uint32_t)hi * 1000003u) & UHASH_MASK;
}

static int bdd_make(int var, int lo, int hi) {
    if (lo == hi) return lo;
    uint32_t h = uhash_fn(var, lo, hi);
    for (int ei = uhash_table[h]; ei >= 0; ei = uentry_pool[ei].next) {
        UEntry *e = &uentry_pool[ei];
        if (e->var == var && e->lo == lo && e->hi == hi) return e->node_id;
    }
    if (bdd_count >= bdd_cap) {
        bdd_cap *= 2;
        bdd_nodes = (BDDNode *)realloc(bdd_nodes, bdd_cap * sizeof(BDDNode));
    }
    int id = bdd_count++;
    bdd_nodes[id] = (BDDNode){var, lo, hi};
    if (uentry_count >= uentry_cap) {
        uentry_cap *= 2;
        uentry_pool = (UEntry *)realloc(uentry_pool, uentry_cap * sizeof(UEntry));
    }
    int nei = uentry_count++;
    uentry_pool[nei] = (UEntry){var, lo, hi, id, uhash_table[h]};
    uhash_table[h] = nei;
    return id;
}

static int bdd_var(int v) { return bdd_make(v, BDD_FALSE, BDD_TRUE); }

enum { OP_AND=0, OP_OR=1, OP_XOR=2, OP_XNOR=3 };

static inline uint32_t chash_fn(int op, int f, int g) {
    return ((uint32_t)op * 314159u + (uint32_t)f * 271828u + (uint32_t)g * 161803u) & CHASH_MASK;
}

static int bdd_apply(int op, int f, int g) {
    if (f <= 1 && g <= 1) {
        int r;
        switch(op) {
            case OP_AND: r=f&g; break; case OP_OR: r=f|g; break;
            case OP_XOR: r=f^g; break; case OP_XNOR: r=!(f^g); break;
            default: r=0;
        }
        return r ? BDD_TRUE : BDD_FALSE;
    }
    if ((op==OP_AND||op==OP_OR||op==OP_XOR||op==OP_XNOR) && f > g) { int t=f; f=g; g=t; }
    if (op==OP_AND) {
        if (f==BDD_FALSE||g==BDD_FALSE) return BDD_FALSE;
        if (f==BDD_TRUE) return g; if (g==BDD_TRUE) return f;
        if (f==g) return f;
    } else if (op==OP_OR) {
        if (f==BDD_TRUE||g==BDD_TRUE) return BDD_TRUE;
        if (f==BDD_FALSE) return g; if (g==BDD_FALSE) return f;
        if (f==g) return f;
    } else if (op==OP_XOR) {
        if (f==BDD_FALSE) return g; if (g==BDD_FALSE) return f;
        if (f==g) return BDD_FALSE;
    } else if (op==OP_XNOR) {
        if (f==g) return BDD_TRUE;
    }
    uint32_t ch = chash_fn(op, f, g);
    CacheEntry *ce = &comp_table[ch];
    if (ce->op == op && ce->f == f && ce->g == g) return ce->result;
    int vf = (f<=1)?NVARS:bdd_nodes[f].var, vg = (g<=1)?NVARS:bdd_nodes[g].var;
    int v = (vf<vg)?vf:vg;
    int flo=f,fhi=f,glo=g,ghi=g;
    if(vf==v){flo=bdd_nodes[f].lo;fhi=bdd_nodes[f].hi;}
    if(vg==v){glo=bdd_nodes[g].lo;ghi=bdd_nodes[g].hi;}
    int lo=bdd_apply(op,flo,glo), hi=bdd_apply(op,fhi,ghi);
    int result=bdd_make(v,lo,hi);
    ce->op=op; ce->f=f; ce->g=g; ce->result=result;
    return result;
}

static inline int bdd_and(int f, int g) { return bdd_apply(OP_AND, f, g); }
static inline int bdd_or(int f, int g)  { return bdd_apply(OP_OR, f, g); }
static inline int bdd_xor(int f, int g) { return bdd_apply(OP_XOR, f, g); }
static inline int bdd_xnor(int f, int g){ return bdd_apply(OP_XNOR, f, g); }

static int bdd_not(int f) {
    if (f==BDD_FALSE) return BDD_TRUE;
    if (f==BDD_TRUE) return BDD_FALSE;
    return bdd_make(bdd_nodes[f].var, bdd_not(bdd_nodes[f].lo), bdd_not(bdd_nodes[f].hi));
}

/* ================================================================
 * BDD WORD ARITHMETIC (N-bit vectors of BDD nodes)
 * ================================================================ */

static void bdd_const(int *out, uint32_t val) {
    for (int i=0;i<N;i++) out[i]=((val>>i)&1)?BDD_TRUE:BDD_FALSE;
}
static void bdd_word_xor(int *out, const int *a, const int *b) {
    for (int i=0;i<N;i++) out[i]=bdd_xor(a[i],b[i]);
}
static void bdd_word_and(int *out, const int *a, const int *b) {
    for (int i=0;i<N;i++) out[i]=bdd_and(a[i],b[i]);
}
static void bdd_word_not(int *out, const int *a) {
    for (int i=0;i<N;i++) out[i]=bdd_not(a[i]);
}
static void bdd_word_add(int *out, const int *a, const int *b) {
    int carry = BDD_FALSE;
    for (int i=0;i<N;i++) {
        int axb=bdd_xor(a[i],b[i]);
        out[i]=bdd_xor(axb,carry);
        if (i<N-1) {
            int ab=bdd_and(a[i],b[i]);
            int ac=bdd_and(a[i],carry);
            int bc=bdd_and(b[i],carry);
            carry=bdd_or(bdd_or(ab,ac),bc);
        }
    }
}
static void bdd_word_sub(int *out, const int *a, const int *b) {
    int neg[32], one[32], tc[32];
    for (int i=0;i<N;i++) neg[i]=bdd_not(b[i]);
    bdd_const(one, 1); bdd_word_add(tc, neg, one);
    bdd_word_add(out, a, tc);
}
static void bdd_word_copy(int *d, const int *s) { memcpy(d,s,N*sizeof(int)); }
static void bdd_word_ror(int *out, const int *a, int k) {
    k=k%N; for(int i=0;i<N;i++) out[i]=a[(i+k)%N];
}
static void bdd_word_shr(int *out, const int *a, int k) {
    for(int i=0;i<N;i++) out[i]=(i+k<N)?a[i+k]:BDD_FALSE;
}

/* SHA-256 primitives over BDD words */
static int rS0[3],rS1[3],rs0[2],rs1[2],ss0,ss1;

static int scale_rot(int k32) {
    int r=(int)rint((double)k32*N/32.0); return r<1?1:r;
}

static void bdd_Sigma0(int *out, const int *a) {
    int t1[32],t2[32],t3[32],t4[32];
    bdd_word_ror(t1,a,rS0[0]); bdd_word_ror(t2,a,rS0[1]); bdd_word_ror(t3,a,rS0[2]);
    bdd_word_xor(t4,t1,t2); bdd_word_xor(out,t4,t3);
}
static void bdd_Sigma1(int *out, const int *e) {
    int t1[32],t2[32],t3[32],t4[32];
    bdd_word_ror(t1,e,rS1[0]); bdd_word_ror(t2,e,rS1[1]); bdd_word_ror(t3,e,rS1[2]);
    bdd_word_xor(t4,t1,t2); bdd_word_xor(out,t4,t3);
}
static void bdd_sigma0(int *out, const int *x) {
    int t1[32],t2[32],t3[32],t4[32];
    bdd_word_ror(t1,x,rs0[0]); bdd_word_ror(t2,x,rs0[1]); bdd_word_shr(t3,x,ss0);
    bdd_word_xor(t4,t1,t2); bdd_word_xor(out,t4,t3);
}
static void bdd_sigma1(int *out, const int *x) {
    int t1[32],t2[32],t3[32],t4[32];
    bdd_word_ror(t1,x,rs1[0]); bdd_word_ror(t2,x,rs1[1]); bdd_word_shr(t3,x,ss1);
    bdd_word_xor(t4,t1,t2); bdd_word_xor(out,t4,t3);
}
static void bdd_Ch(int *out, const int *e, const int *f, const int *g) {
    int ef[32],neg[32],ng[32];
    bdd_word_and(ef,e,f); bdd_word_not(neg,e); bdd_word_and(ng,neg,g);
    bdd_word_xor(out,ef,ng);
}
static void bdd_Maj(int *out, const int *a, const int *b, const int *c) {
    int ab[32],ac[32],bc[32],t[32];
    bdd_word_and(ab,a,b); bdd_word_and(ac,a,c); bdd_word_and(bc,b,c);
    bdd_word_xor(t,ab,ac); bdd_word_xor(out,t,bc);
}

/* BDD SHA round */
typedef struct { int reg[8][32]; } BDDState;

static void bdd_sha_round(BDDState *s, const int *K, const int *W) {
    int sig1[32],ch[32],t1[32],t2[32],t3[32],T1[32],sig0[32],maj[32],T2[32],na[32],ne[32];
    bdd_Sigma1(sig1, s->reg[4]);
    bdd_Ch(ch, s->reg[4], s->reg[5], s->reg[6]);
    bdd_word_add(t1, s->reg[7], sig1);
    bdd_word_add(t2, t1, ch);
    bdd_word_add(t3, t2, K);
    bdd_word_add(T1, t3, W);
    bdd_Sigma0(sig0, s->reg[0]);
    bdd_Maj(maj, s->reg[0], s->reg[1], s->reg[2]);
    bdd_word_add(T2, sig0, maj);
    bdd_word_add(ne, s->reg[3], T1);
    bdd_word_add(na, T1, T2);
    bdd_word_copy(s->reg[7], s->reg[6]);
    bdd_word_copy(s->reg[6], s->reg[5]);
    bdd_word_copy(s->reg[5], s->reg[4]);
    bdd_word_copy(s->reg[4], ne);
    bdd_word_copy(s->reg[3], s->reg[2]);
    bdd_word_copy(s->reg[2], s->reg[1]);
    bdd_word_copy(s->reg[1], s->reg[0]);
    bdd_word_copy(s->reg[0], na);
}

/* Cascade W2 computation */
static void bdd_cascade_w2(int *W2, const int *W1, const BDDState *s1,
                           const BDDState *s2, const int *K) {
    int sig1_1[32],ch_1[32],r1[32],sig1_2[32],ch_2[32],r2[32];
    int sig0_1[32],maj_1[32],T21[32],sig0_2[32],maj_2[32],T22[32];
    int dr[32],dT[32],off[32],t1[32],t2[32],t3[32],t4[32];
    bdd_Sigma1(sig1_1,s1->reg[4]); bdd_Ch(ch_1,s1->reg[4],s1->reg[5],s1->reg[6]);
    bdd_word_add(t1,s1->reg[7],sig1_1); bdd_word_add(t2,t1,ch_1); bdd_word_add(r1,t2,K);
    bdd_Sigma1(sig1_2,s2->reg[4]); bdd_Ch(ch_2,s2->reg[4],s2->reg[5],s2->reg[6]);
    bdd_word_add(t3,s2->reg[7],sig1_2); bdd_word_add(t4,t3,ch_2); bdd_word_add(r2,t4,K);
    bdd_Sigma0(sig0_1,s1->reg[0]); bdd_Maj(maj_1,s1->reg[0],s1->reg[1],s1->reg[2]);
    bdd_word_add(T21,sig0_1,maj_1);
    bdd_Sigma0(sig0_2,s2->reg[0]); bdd_Maj(maj_2,s2->reg[0],s2->reg[1],s2->reg[2]);
    bdd_word_add(T22,sig0_2,maj_2);
    bdd_word_sub(dr,r1,r2); bdd_word_sub(dT,T21,T22);
    bdd_word_add(off,dr,dT); bdd_word_add(W2,W1,off);
}

/* ================================================================
 * CONCRETE SHA-256 (for precomputation and outer-loop rounds)
 * ================================================================ */

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
    0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,
    0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19
};
static uint32_t KN[64], IVN[8];

static inline uint32_t ror_n(uint32_t x, int k) {
    k=k%N; return ((x>>k)|(x<<(N-k)))&MASK;
}
static inline uint32_t fnS0(uint32_t a){return ror_n(a,rS0[0])^ror_n(a,rS0[1])^ror_n(a,rS0[2]);}
static inline uint32_t fnS1(uint32_t e){return ror_n(e,rS1[0])^ror_n(e,rS1[1])^ror_n(e,rS1[2]);}
static inline uint32_t fns0(uint32_t x){return ror_n(x,rs0[0])^ror_n(x,rs0[1])^((x>>ss0)&MASK);}
static inline uint32_t fns1(uint32_t x){return ror_n(x,rs1[0])^ror_n(x,rs1[1])^((x>>ss1)&MASK);}
static inline uint32_t fnCh(uint32_t e,uint32_t f,uint32_t g){return((e&f)^((~e)&g))&MASK;}
static inline uint32_t fnMj(uint32_t a,uint32_t b,uint32_t c){return((a&b)^(a&c)^(b&c))&MASK;}

static void precompute(const uint32_t M[16], uint32_t st[8], uint32_t W[57]) {
    for (int i=0;i<16;i++) W[i]=M[i]&MASK;
    for (int i=16;i<57;i++) W[i]=(fns1(W[i-2])+W[i-7]+fns0(W[i-15])+W[i-16])&MASK;
    uint32_t a=IVN[0],b=IVN[1],c=IVN[2],d=IVN[3],e=IVN[4],f=IVN[5],g=IVN[6],h=IVN[7];
    for (int i=0;i<57;i++) {
        uint32_t T1=(h+fnS1(e)+fnCh(e,f,g)+KN[i]+W[i])&MASK;
        uint32_t T2=(fnS0(a)+fnMj(a,b,c))&MASK;
        h=g;g=f;f=e;e=(d+T1)&MASK;d=c;c=b;b=a;a=(T1+T2)&MASK;
    }
    st[0]=a;st[1]=b;st[2]=c;st[3]=d;st[4]=e;st[5]=f;st[6]=g;st[7]=h;
}

static inline void concrete_round(uint32_t s[8], uint32_t k, uint32_t w) {
    uint32_t T1=(s[7]+fnS1(s[4])+fnCh(s[4],s[5],s[6])+k+w)&MASK;
    uint32_t T2=(fnS0(s[0])+fnMj(s[0],s[1],s[2]))&MASK;
    s[7]=s[6];s[6]=s[5];s[5]=s[4];s[4]=(s[3]+T1)&MASK;
    s[3]=s[2];s[2]=s[1];s[1]=s[0];s[0]=(T1+T2)&MASK;
}

static inline uint32_t find_w2(const uint32_t s1[8], const uint32_t s2[8], int rnd, uint32_t w1) {
    uint32_t r1=(s1[7]+fnS1(s1[4])+fnCh(s1[4],s1[5],s1[6])+KN[rnd])&MASK;
    uint32_t r2=(s2[7]+fnS1(s2[4])+fnCh(s2[4],s2[5],s2[6])+KN[rnd])&MASK;
    uint32_t T21=(fnS0(s1[0])+fnMj(s1[0],s1[1],s1[2]))&MASK;
    uint32_t T22=(fnS0(s2[0])+fnMj(s2[0],s2[1],s2[2]))&MASK;
    return (w1+r1-r2+T21-T22)&MASK;
}

/* ================================================================
 * BDD NODE COUNTING AND EVALUATION
 * ================================================================ */

static int *visited = NULL;
static int visited_cap = 0;

static int count_nodes_rec(int node) {
    if (node<=1) return 0;
    if (node >= visited_cap) {
        int nc=node+1; visited=(int*)realloc(visited,nc*sizeof(int));
        memset(visited+visited_cap,0,(nc-visited_cap)*sizeof(int)); visited_cap=nc;
    }
    if (visited[node]) return 0;
    visited[node]=1;
    return 1+count_nodes_rec(bdd_nodes[node].lo)+count_nodes_rec(bdd_nodes[node].hi);
}

static int count_bdd_nodes(int root) {
    if (visited_cap<bdd_count) {
        visited=(int*)realloc(visited,bdd_count*sizeof(int)); visited_cap=bdd_count;
    }
    memset(visited,0,visited_cap*sizeof(int));
    return count_nodes_rec(root);
}

static double bdd_satcount(int node, int level) {
    if (node==BDD_FALSE) return 0.0;
    if (node==BDD_TRUE) return ldexp(1.0, NVARS-level);
    int v=bdd_nodes[node].var;
    double factor=ldexp(1.0, v-level);
    return factor*(bdd_satcount(bdd_nodes[node].lo,v+1)+bdd_satcount(bdd_nodes[node].hi,v+1));
}

static int bdd_eval(int node, const int *assign) {
    while (bdd_nodes[node].var >= 0) {
        int v=bdd_nodes[node].var;
        node=assign[v]?bdd_nodes[node].hi:bdd_nodes[node].lo;
    }
    return node;
}

/* ================================================================
 * MAIN: HYBRID CONCRETE + BDD
 * ================================================================ */

int main(int argc, char **argv) {
    setbuf(stdout, NULL);
    struct timespec t_start, t_now;
    clock_gettime(CLOCK_MONOTONIC, &t_start);

    N = (argc > 1) ? atoi(argv[1]) : 4;
    if (N<2||N>16) { printf("N must be 2..16\n"); return 1; }
    MASK=(1U<<N)-1; MSB_BIT=1U<<(N-1);
    NVARS = 4*N;
    INNER_NVARS = 2*N;

    printf("=== Hybrid BDD Construction for N=%d ===\n", N);
    printf("Outer loop: W57, W58 concrete (2^%d = %u iterations)\n", 2*N, 1U<<(2*N));
    printf("Inner BDD: W59, W60 symbolic (%d variables)\n", INNER_NVARS);
    printf("Full BDD variables: %d\n\n", NVARS);

    /* Init */
    rS0[0]=scale_rot(2);rS0[1]=scale_rot(13);rS0[2]=scale_rot(22);
    rS1[0]=scale_rot(6);rS1[1]=scale_rot(11);rS1[2]=scale_rot(25);
    rs0[0]=scale_rot(7);rs0[1]=scale_rot(18);ss0=scale_rot(3);
    rs1[0]=scale_rot(17);rs1[1]=scale_rot(19);ss1=scale_rot(10);
    for (int i=0;i<64;i++) KN[i]=K32[i]&MASK;
    for (int i=0;i<8;i++) IVN[i]=IV32[i]&MASK;

    /* Find valid candidate */
    uint32_t M0=0, KMSB=0;
    int kernel_bit=-1;
    uint32_t M1[16],M2[16],state1[8],state2[8],W1p[57],W2p[57];
    int found=0;
    for (int kbit=N-1;kbit>=0&&!found;kbit--) {
        uint32_t kb=1U<<kbit;
        for (uint32_t m0=0;m0<(1U<<N);m0++) {
            for(int i=0;i<16;i++){M1[i]=MASK;M2[i]=MASK;}
            M1[0]=m0;M2[0]=m0^kb;M2[9]=MASK^kb;
            precompute(M1,state1,W1p); precompute(M2,state2,W2p);
            if(((state1[0]-state2[0])&MASK)==0) {
                M0=m0; kernel_bit=kbit; KMSB=kb; found=1; break;
            }
        }
    }
    if (!found) { printf("ERROR: no valid candidate\n"); return 1; }
    for(int i=0;i<16;i++){M1[i]=MASK;M2[i]=MASK;}
    M1[0]=M0;M2[0]=M0^KMSB;M2[9]=MASK^KMSB;
    precompute(M1,state1,W1p); precompute(M2,state2,W2p);
    printf("Candidate: M[0]=0x%x, fill=0x%x, kernel bit %d\n", M0, MASK, kernel_bit);

    /* Init BDD */
    bdd_init();

    /* BDD variables for W59, W60 (inner BDD):
     * Use the SAME variable numbering as the full BDD.
     * Full BDD: var 4*b+w, w=0:W57, w=1:W58, w=2:W59, w=3:W60
     * Inner BDD variables are var 4*b+2 (W59[b]) and var 4*b+3 (W60[b]).
     */
    int W59_bdd[32], W60_bdd[32];
    for (int b=0;b<N;b++) {
        W59_bdd[b] = bdd_var(4*b+2);
        W60_bdd[b] = bdd_var(4*b+3);
    }

    /* Also need BDD variables for W57, W58 (for the final combined BDD) */
    /* We'll create constraint BDDs for W57=w57, W58=w58 using vars 4*b+0, 4*b+1 */
    /* Pre-create the variable nodes */
    int W57_vars[32], W58_vars[32];
    for (int b=0;b<N;b++) {
        W57_vars[b] = bdd_var(4*b+0);
        W58_vars[b] = bdd_var(4*b+1);
    }

    printf("BDD initialized: %d variables, %d nodes\n\n", NVARS, bdd_count-2);

    /* ================================================================
     * OUTER LOOP: enumerate W57, W58 concretely
     *
     * For each (w57, w58):
     *   1. Run rounds 57-58 concretely for both paths
     *   2. Build inner BDD over (W59, W60) for collision
     *   3. Create constraint BDD for "W57==w57 AND W58==w58"
     *   4. OR into running collision BDD: collision |= (constraint AND inner)
     * ================================================================ */

    int collision_bdd = BDD_FALSE;
    uint64_t total_collisions = 0;
    uint32_t SIZE = 1U << N;
    uint64_t outer_total = (uint64_t)SIZE * SIZE;
    uint64_t outer_done = 0;
    int max_inner_nodes = 0;

    printf("--- Processing %llu outer-loop iterations ---\n", (unsigned long long)outer_total);

    for (uint32_t w57 = 0; w57 < SIZE; w57++) {
        /* Round 57 concrete */
        uint32_t s57a[8], s57b[8];
        memcpy(s57a, state1, 32); memcpy(s57b, state2, 32);
        uint32_t w57b = find_w2(s57a, s57b, 57, w57);
        concrete_round(s57a, KN[57], w57);
        concrete_round(s57b, KN[57], w57b);

        for (uint32_t w58 = 0; w58 < SIZE; w58++) {
            /* Round 58 concrete */
            uint32_t s58a[8], s58b[8];
            memcpy(s58a, s57a, 32); memcpy(s58b, s57b, 32);
            uint32_t w58b = find_w2(s58a, s58b, 58, w58);
            concrete_round(s58a, KN[58], w58);
            concrete_round(s58b, KN[58], w58b);

            /* Now build inner BDD: state is concrete, W59 and W60 are symbolic */
            BDDState bs1, bs2;
            for (int r=0;r<8;r++) {
                bdd_const(bs1.reg[r], s58a[r]);
                bdd_const(bs2.reg[r], s58b[r]);
            }

            /* Round 59: W59 is BDD, cascade W2_59 */
            int K59_bdd[32]; bdd_const(K59_bdd, KN[59]);
            int W2_59[32];
            bdd_cascade_w2(W2_59, W59_bdd, &bs1, &bs2, K59_bdd);
            bdd_sha_round(&bs1, K59_bdd, W59_bdd);
            bdd_sha_round(&bs2, K59_bdd, W2_59);

            /* Round 60: W60 is BDD, cascade W2_60 */
            int K60_bdd[32]; bdd_const(K60_bdd, KN[60]);
            int W2_60[32];
            bdd_cascade_w2(W2_60, W60_bdd, &bs1, &bs2, K60_bdd);
            bdd_sha_round(&bs1, K60_bdd, W60_bdd);
            bdd_sha_round(&bs2, K60_bdd, W2_60);

            /* Rounds 61-63: schedule-determined */
            /* W1[61] = sigma1(W59) + W[54] + sigma0(W[46]) + W[45] */
            int sig1_59[32], W1_61[32], c61[32];
            bdd_sigma1(sig1_59, W59_bdd);
            bdd_const(c61, (W1p[54]+fns0(W1p[46])+W1p[45])&MASK);
            bdd_word_add(W1_61, sig1_59, c61);

            int sig1_59b[32], W2_61[32], c61b[32];
            bdd_sigma1(sig1_59b, W2_59);
            bdd_const(c61b, (W2p[54]+fns0(W2p[46])+W2p[45])&MASK);
            bdd_word_add(W2_61, sig1_59b, c61b);

            int K61_bdd[32]; bdd_const(K61_bdd, KN[61]);
            bdd_sha_round(&bs1, K61_bdd, W1_61);
            bdd_sha_round(&bs2, K61_bdd, W2_61);

            /* W1[62] = sigma1(W60) + const */
            int sig1_60[32], W1_62[32], c62[32];
            bdd_sigma1(sig1_60, W60_bdd);
            bdd_const(c62, (W1p[55]+fns0(W1p[47])+W1p[46])&MASK);
            bdd_word_add(W1_62, sig1_60, c62);

            int sig1_60b[32], W2_62[32], c62b[32];
            bdd_sigma1(sig1_60b, W2_60);
            bdd_const(c62b, (W2p[55]+fns0(W2p[47])+W2p[46])&MASK);
            bdd_word_add(W2_62, sig1_60b, c62b);

            int K62_bdd[32]; bdd_const(K62_bdd, KN[62]);
            bdd_sha_round(&bs1, K62_bdd, W1_62);
            bdd_sha_round(&bs2, K62_bdd, W2_62);

            /* W1[63] = sigma1(W1_61) + const */
            int sig1_61a[32], W1_63[32], c63[32];
            bdd_sigma1(sig1_61a, W1_61);
            bdd_const(c63, (W1p[56]+fns0(W1p[48])+W1p[47])&MASK);
            bdd_word_add(W1_63, sig1_61a, c63);

            int sig1_61b[32], W2_63[32], c63b[32];
            bdd_sigma1(sig1_61b, W2_61);
            bdd_const(c63b, (W2p[56]+fns0(W2p[48])+W2p[47])&MASK);
            bdd_word_add(W2_63, sig1_61b, c63b);

            int K63_bdd[32]; bdd_const(K63_bdd, KN[63]);
            bdd_sha_round(&bs1, K63_bdd, W1_63);
            bdd_sha_round(&bs2, K63_bdd, W2_63);

            /* Collision check: AND of XNOR for all register bits */
            int inner_coll = BDD_TRUE;
            for (int r=0;r<8;r++)
                for (int b=0;b<N;b++)
                    inner_coll = bdd_and(inner_coll, bdd_xnor(bs1.reg[r][b], bs2.reg[r][b]));

            if (inner_coll != BDD_FALSE) {
                /* Count collisions in this slice */
                double inner_sat = bdd_satcount(inner_coll, 0);
                /* inner_sat counts over ALL NVARS variables, but W57/W58 vars
                 * are free in the inner BDD → multiply by 2^{2N}.
                 * Divide by 2^{2N} to get actual count for this (w57,w58). */
                double actual_sat = inner_sat / ldexp(1.0, 2*N);
                total_collisions += (uint64_t)actual_sat;

                int cn = count_bdd_nodes(inner_coll);
                if (cn > max_inner_nodes) max_inner_nodes = cn;

                /* Build constraint: W57==w57 AND W58==w58 */
                int constraint = BDD_TRUE;
                for (int b=0;b<N;b++) {
                    int bit57 = (w57>>b)&1;
                    int v57 = bit57 ? W57_vars[b] : bdd_not(W57_vars[b]);
                    constraint = bdd_and(constraint, v57);

                    int bit58 = (w58>>b)&1;
                    int v58 = bit58 ? W58_vars[b] : bdd_not(W58_vars[b]);
                    constraint = bdd_and(constraint, v58);
                }

                /* Add to full collision BDD */
                int slice = bdd_and(constraint, inner_coll);
                collision_bdd = bdd_or(collision_bdd, slice);
            }

            outer_done++;
        }

        /* Progress */
        if ((w57 & ((SIZE/4 > 0 ? SIZE/4 : 1) - 1)) == 0 || w57 == SIZE-1) {
            clock_gettime(CLOCK_MONOTONIC, &t_now);
            double el = (t_now.tv_sec-t_start.tv_sec)+(t_now.tv_nsec-t_start.tv_nsec)/1e9;
            printf("  w57=%u/%u collisions=%llu BDD_total=%d max_inner=%d time=%.1fs\n",
                   w57+1, SIZE, (unsigned long long)total_collisions,
                   bdd_count-2, max_inner_nodes, el);
        }
    }

    clock_gettime(CLOCK_MONOTONIC, &t_now);
    double el = (t_now.tv_sec-t_start.tv_sec)+(t_now.tv_nsec-t_start.tv_nsec)/1e9;

    int final_nodes = count_bdd_nodes(collision_bdd);
    double sat = bdd_satcount(collision_bdd, 0);

    printf("\n=== RESULTS ===\n\n");
    printf("N = %d\n", N);
    printf("Collision BDD nodes: %d\n", final_nodes);
    printf("Collisions found: %llu (BDD satcount: %.0f)\n",
           (unsigned long long)total_collisions, sat);
    printf("Max inner BDD nodes: %d (over 2N=%d variables)\n", max_inner_nodes, 2*N);
    printf("Total BDD nodes allocated: %d\n", bdd_count-2);
    printf("Construction time: %.2fs\n", el);
    printf("NO TRUTH TABLE USED.\n");

    /* Validation */
    int expected_coll = -1;
    if (N==4) expected_coll = 49;
    else if (N==8) expected_coll = 260;
    if (expected_coll >= 0)
        printf("Expected collisions: %d — %s\n", expected_coll,
               ((int)sat==expected_coll)?"MATCH":"MISMATCH");

    /* Spot-check */
    if (N <= 8) {
        printf("\n--- Spot-check ---\n");
        int checked=0, verified=0;
        for (uint32_t w57=0;w57<SIZE&&checked<20;w57++)
         for (uint32_t w58=0;w58<SIZE&&checked<20;w58++)
          for (uint32_t w59=0;w59<SIZE&&checked<20;w59++)
           for (uint32_t w60=0;w60<SIZE&&checked<20;w60++) {
            int assign[128]; memset(assign,0,sizeof(assign));
            for(int b=0;b<N;b++){
                assign[4*b+0]=(w57>>b)&1; assign[4*b+1]=(w58>>b)&1;
                assign[4*b+2]=(w59>>b)&1; assign[4*b+3]=(w60>>b)&1;
            }
            int bdd_r = bdd_eval(collision_bdd, assign);

            /* Concrete */
            uint32_t sa[8],sb[8];
            memcpy(sa,state1,32); memcpy(sb,state2,32);
            uint32_t w57b=find_w2(sa,sb,57,w57);
            concrete_round(sa,KN[57],w57); concrete_round(sb,KN[57],w57b);
            uint32_t w58b=find_w2(sa,sb,58,w58);
            concrete_round(sa,KN[58],w58); concrete_round(sb,KN[58],w58b);
            uint32_t w59b=find_w2(sa,sb,59,w59);
            concrete_round(sa,KN[59],w59); concrete_round(sb,KN[59],w59b);
            uint32_t co60=find_w2(sa,sb,60,0);
            uint32_t w60b=(w60+co60)&MASK;
            concrete_round(sa,KN[60],w60); concrete_round(sb,KN[60],w60b);
            uint32_t cw61a=(fns1(w59)+W1p[54]+fns0(W1p[46])+W1p[45])&MASK;
            uint32_t cw61b=(fns1(w59b)+W2p[54]+fns0(W2p[46])+W2p[45])&MASK;
            concrete_round(sa,KN[61],cw61a); concrete_round(sb,KN[61],cw61b);
            uint32_t cw62a=(fns1(w60)+W1p[55]+fns0(W1p[47])+W1p[46])&MASK;
            uint32_t cw62b=(fns1(w60b)+W2p[55]+fns0(W2p[47])+W2p[46])&MASK;
            concrete_round(sa,KN[62],cw62a); concrete_round(sb,KN[62],cw62b);
            uint32_t cw63a=(fns1(cw61a)+W1p[56]+fns0(W1p[48])+W1p[47])&MASK;
            uint32_t cw63b=(fns1(cw61b)+W2p[56]+fns0(W2p[48])+W2p[47])&MASK;
            concrete_round(sa,KN[63],cw63a); concrete_round(sb,KN[63],cw63b);
            int coll=1;
            for(int r=0;r<8;r++) if(sa[r]!=sb[r]){coll=0;break;}

            if(bdd_r!=coll)
                printf("  MISMATCH w57=%u w58=%u w59=%u w60=%u: BDD=%d concrete=%d\n",
                       w57,w58,w59,w60,bdd_r,coll);
            else verified++;
            checked++;
           }
        printf("Verified %d/%d spot-checks PASS\n", verified, checked);
    }

    printf("\nMemory: BDD %.1f MB, unique %.1f MB, cache %.1f MB\n",
           (double)bdd_count*sizeof(BDDNode)/(1<<20),
           (double)uentry_count*sizeof(UEntry)/(1<<20),
           (double)CHASH_SIZE*sizeof(CacheEntry)/(1<<20));

    free(bdd_nodes); free(uentry_pool); free(uhash_table);
    free(comp_table); free(visited);
    return 0;
}
