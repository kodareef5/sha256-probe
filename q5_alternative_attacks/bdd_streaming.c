/*
 * bdd_streaming.c — Streaming BDD construction for N=9..12
 *
 * For N>8, the full truth table (2^{4N} bits) doesn't fit in memory.
 * This tool partitions over W57 (2^N outer loop), generating a partial
 * truth table of 2^{3N} bits per iteration. Each partial truth table
 * is converted to a BDD, then merged into the full collision BDD.
 *
 * Memory: O(2^{3N}) for the partial truth table + O(BDD size) for the BDD.
 *   N=9: 2^27 = 128MB per partial TT, 512 outer iterations
 *   N=10: 2^30 = 128MB per partial TT, 1024 outer iterations
 *   N=11: 2^33 = 1GB per partial TT — needs sub-partitioning
 *   N=12: 2^36 = 8GB per partial TT — needs sub-partitioning
 *
 * For N=11+, we partition over (W57,W58): 2^{2N} outer, 2^{2N} inner TT.
 *
 * Compile: gcc -O3 -march=native -o bdd_stream bdd_streaming.c -lm
 * Usage: ./bdd_stream [N]
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <time.h>

static int N;
static uint32_t MASK;
static int NVARS;

/* ---- BDD core ---- */
typedef struct { int var,lo,hi; } BDDNode;
#define BDD_FALSE 0
#define BDD_TRUE  1

static BDDNode *bdd_nodes; static int bdd_count, bdd_cap;
typedef struct { int var,lo,hi,node_id,next; } UEntry;

#define UHASH_BITS 24
#define UHASH_SIZE (1<<UHASH_BITS)
#define UHASH_MASK (UHASH_SIZE-1)
static int *uhash_table; static UEntry *uentry_pool; static int uentry_count, uentry_cap;

/* Computed table for Apply */
#define CHASH_BITS 24
#define CHASH_SIZE (1<<CHASH_BITS)
#define CHASH_MASK (CHASH_SIZE-1)
typedef struct { int op,f,g,result; } CEntry;
static CEntry *comp_table;

static void bdd_init(void) {
    bdd_cap=1<<22; bdd_nodes=malloc(bdd_cap*sizeof(BDDNode));
    bdd_nodes[0]=(BDDNode){-1,0,0}; bdd_nodes[1]=(BDDNode){-1,1,1}; bdd_count=2;
    uhash_table=malloc(UHASH_SIZE*sizeof(int));
    for(int i=0;i<UHASH_SIZE;i++) uhash_table[i]=-1;
    uentry_cap=1<<22; uentry_pool=malloc(uentry_cap*sizeof(UEntry)); uentry_count=0;
    comp_table=calloc(CHASH_SIZE,sizeof(CEntry));
    for(int i=0;i<CHASH_SIZE;i++) comp_table[i].op=-1;
}

static int bdd_make(int var, int lo, int hi) {
    if(lo==hi) return lo;
    uint32_t h=((uint32_t)var*7919u+(uint32_t)lo*104729u+(uint32_t)hi*1000003u)&UHASH_MASK;
    for(int ei=uhash_table[h];ei>=0;ei=uentry_pool[ei].next) {
        UEntry*e=&uentry_pool[ei];
        if(e->var==var&&e->lo==lo&&e->hi==hi) return e->node_id;
    }
    if(bdd_count>=bdd_cap){bdd_cap*=2;bdd_nodes=realloc(bdd_nodes,bdd_cap*sizeof(BDDNode));}
    int id=bdd_count++; bdd_nodes[id]=(BDDNode){var,lo,hi};
    if(uentry_count>=uentry_cap){uentry_cap*=2;uentry_pool=realloc(uentry_pool,uentry_cap*sizeof(UEntry));}
    int nei=uentry_count++;
    uentry_pool[nei]=(UEntry){var,lo,hi,id,uhash_table[h]}; uhash_table[h]=nei;
    return id;
}

/* Apply (for OR-ing partial BDDs together) */
enum { OP_AND=0, OP_OR=1 };

static int bdd_apply(int op, int f, int g) {
    if(f<=1&&g<=1) return (op==OP_AND?(f&g):(f|g))?BDD_TRUE:BDD_FALSE;
    if(op==OP_AND){
        if(f==BDD_FALSE||g==BDD_FALSE) return BDD_FALSE;
        if(f==BDD_TRUE) return g; if(g==BDD_TRUE) return f;
        if(f==g) return f;
    } else {
        if(f==BDD_TRUE||g==BDD_TRUE) return BDD_TRUE;
        if(f==BDD_FALSE) return g; if(g==BDD_FALSE) return f;
        if(f==g) return f;
    }
    if(f>g){int t=f;f=g;g=t;}
    uint32_t ch=((uint32_t)op*314159u+(uint32_t)f*271828u+(uint32_t)g*161803u)&CHASH_MASK;
    CEntry*ce=&comp_table[ch];
    if(ce->op==op&&ce->f==f&&ce->g==g) return ce->result;
    int vf=(f<=1)?NVARS:bdd_nodes[f].var, vg=(g<=1)?NVARS:bdd_nodes[g].var;
    int v=(vf<vg)?vf:vg;
    int flo=f,fhi=f,glo=g,ghi=g;
    if(vf==v){flo=bdd_nodes[f].lo;fhi=bdd_nodes[f].hi;}
    if(vg==v){glo=bdd_nodes[g].lo;ghi=bdd_nodes[g].hi;}
    int lo=bdd_apply(op,flo,glo), hi=bdd_apply(op,fhi,ghi);
    int result=bdd_make(v,lo,hi);
    ce->op=op;ce->f=f;ce->g=g;ce->result=result;
    return result;
}

/* ---- SHA-256 concrete ---- */
static int rS0[3],rS1[3],rs0[2],rs1[2],ss0,ss1;
static int scale_rot(int k32){int r=(int)rint((double)k32*N/32.0);return r<1?1:r;}
static inline uint32_t ror_n(uint32_t x,int k){k%=N;return((x>>k)|(x<<(N-k)))&MASK;}
static inline uint32_t fnS0(uint32_t a){return ror_n(a,rS0[0])^ror_n(a,rS0[1])^ror_n(a,rS0[2]);}
static inline uint32_t fnS1(uint32_t e){return ror_n(e,rS1[0])^ror_n(e,rS1[1])^ror_n(e,rS1[2]);}
static inline uint32_t fns0(uint32_t x){return ror_n(x,rs0[0])^ror_n(x,rs0[1])^((x>>ss0)&MASK);}
static inline uint32_t fns1(uint32_t x){return ror_n(x,rs1[0])^ror_n(x,rs1[1])^((x>>ss1)&MASK);}
static inline uint32_t fnCh(uint32_t e,uint32_t f,uint32_t g){return((e&f)^((~e)&g))&MASK;}
static inline uint32_t fnMj(uint32_t a,uint32_t b,uint32_t c){return((a&b)^(a&c)^(b&c))&MASK;}
static const uint32_t K32[64]={
    0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
    0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
    0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
    0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
    0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
    0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
    0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
    0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
static const uint32_t IV32[8]={
    0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,
    0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};
static uint32_t KN[64],IVN[8];

static void precompute(const uint32_t M[16],uint32_t st[8],uint32_t W[57]) {
    for(int i=0;i<16;i++)W[i]=M[i]&MASK;
    for(int i=16;i<57;i++)W[i]=(fns1(W[i-2])+W[i-7]+fns0(W[i-15])+W[i-16])&MASK;
    uint32_t a=IVN[0],b=IVN[1],c=IVN[2],d=IVN[3],e=IVN[4],f=IVN[5],g=IVN[6],h=IVN[7];
    for(int i=0;i<57;i++){
        uint32_t T1=(h+fnS1(e)+fnCh(e,f,g)+KN[i]+W[i])&MASK;
        uint32_t T2=(fnS0(a)+fnMj(a,b,c))&MASK;
        h=g;g=f;f=e;e=(d+T1)&MASK;d=c;c=b;b=a;a=(T1+T2)&MASK;
    }
    st[0]=a;st[1]=b;st[2]=c;st[3]=d;st[4]=e;st[5]=f;st[6]=g;st[7]=h;
}
static inline void sha_round(uint32_t s[8],uint32_t k,uint32_t w){
    uint32_t T1=(s[7]+fnS1(s[4])+fnCh(s[4],s[5],s[6])+k+w)&MASK;
    uint32_t T2=(fnS0(s[0])+fnMj(s[0],s[1],s[2]))&MASK;
    s[7]=s[6];s[6]=s[5];s[5]=s[4];s[4]=(s[3]+T1)&MASK;
    s[3]=s[2];s[2]=s[1];s[1]=s[0];s[0]=(T1+T2)&MASK;
}
static inline uint32_t find_w2(const uint32_t s1[8],const uint32_t s2[8],int rnd,uint32_t w1){
    uint32_t r1=(s1[7]+fnS1(s1[4])+fnCh(s1[4],s1[5],s1[6])+KN[rnd])&MASK;
    uint32_t r2=(s2[7]+fnS1(s2[4])+fnCh(s2[4],s2[5],s2[6])+KN[rnd])&MASK;
    uint32_t T21=(fnS0(s1[0])+fnMj(s1[0],s1[1],s1[2]))&MASK;
    uint32_t T22=(fnS0(s2[0])+fnMj(s2[0],s2[1],s2[2]))&MASK;
    return(w1+r1-r2+T21-T22)&MASK;
}

/* ---- Interleaved index for inner variables (W58, W59, W60) ---- */
/* For the partial truth table (W57 fixed): 3N variables
 * Variable mapping: use the FULL BDD variable numbering
 *   Full: var 4*b+0=W57[b], var 4*b+1=W58[b], var 4*b+2=W59[b], var 4*b+3=W60[b]
 *
 * The partial TT over (W58,W59,W60) is indexed by 3N bits.
 * We use the interleaved ordering within the inner words:
 *   inner_idx bit 3*b+0 = W58[b], bit 3*b+1 = W59[b], bit 3*b+2 = W60[b]
 *
 * But the BDD variables follow the FULL ordering (gap at W57 vars).
 */

/* Build BDD from partial truth table (3N variables: W58, W59, W60).
 * The BDD variable indices are from the full ordering (with gaps for W57).
 * Process in groups of 3 variables (one bit position at a time). */
static int build_inner_bdd(const uint8_t *tt, int inner_nvars) {
    /* Bottom-up: start with 2^{3N} terminals, reduce 3 variables at a time.
     * Process from bit N-1 (deepest) to bit 0 (shallowest).
     * At each bit position b, the 3 variables are:
     *   var 4*b+1 (W58[b]), var 4*b+2 (W59[b]), var 4*b+3 (W60[b])
     */
    uint64_t count = 1ULL << inner_nvars;  /* 2^{3N} */
    int *layer = malloc(count * sizeof(int));
    if(!layer) { fprintf(stderr, "OOM for layer (%llu entries)\n", (unsigned long long)count); exit(1); }

    for(uint64_t i=0;i<count;i++)
        layer[i] = tt[i] ? BDD_TRUE : BDD_FALSE;

    /* Process from deepest bit to shallowest */
    for(int b = N-1; b >= 0; b--) {
        /* 3 variables at this bit position (deepest first):
         * var 4*b+3 (W60[b]), var 4*b+2 (W59[b]), var 4*b+1 (W58[b]) */
        int vars[3] = {4*b+1, 4*b+2, 4*b+3};

        /* Process var 4*b+3 (W60[b]) — deepest */
        {
            uint64_t half = count/2;
            /* In the inner index, bit 3*b+2 = W60[b].
             * Entries with bit=0 are lo, bit=1 are hi. */
            int bit_pos = 3*b + 2;
            int *nl = malloc(half * sizeof(int));
            uint64_t stride = 1ULL << bit_pos;
            uint64_t block = stride * 2;
            uint64_t out = 0;
            for(uint64_t base=0; base<count; base+=block)
                for(uint64_t j=0; j<stride; j++)
                    nl[out++] = bdd_make(vars[2], layer[base+j], layer[base+j+stride]);
            free(layer); layer=nl; count=half;
        }

        /* Process var 4*b+2 (W59[b]) */
        {
            uint64_t half = count/2;
            int bit_pos = 3*b + 1;
            int *nl = malloc(half * sizeof(int));
            uint64_t stride = 1ULL << bit_pos;
            uint64_t block = stride * 2;
            uint64_t out = 0;
            for(uint64_t base=0; base<count; base+=block)
                for(uint64_t j=0; j<stride; j++)
                    nl[out++] = bdd_make(vars[1], layer[base+j], layer[base+j+stride]);
            free(layer); layer=nl; count=half;
        }

        /* Process var 4*b+1 (W58[b]) */
        {
            uint64_t half = count/2;
            int bit_pos = 3*b;
            int *nl = malloc(half * sizeof(int));
            uint64_t stride = 1ULL << bit_pos;
            uint64_t block = stride * 2;
            uint64_t out = 0;
            for(uint64_t base=0; base<count; base+=block)
                for(uint64_t j=0; j<stride; j++)
                    nl[out++] = bdd_make(vars[0], layer[base+j], layer[base+j+stride]);
            free(layer); layer=nl; count=half;
        }
    }

    int root = layer[0];
    free(layer);
    return root;
}

/* Count BDD nodes reachable from root */
static int *vis; static int vis_cap;
static int cnt_rec(int n) {
    if(n<=1)return 0;
    if(n>=vis_cap){int nc=n+1;vis=realloc(vis,nc*sizeof(int));
        memset(vis+vis_cap,0,(nc-vis_cap)*sizeof(int));vis_cap=nc;}
    if(vis[n])return 0; vis[n]=1;
    return 1+cnt_rec(bdd_nodes[n].lo)+cnt_rec(bdd_nodes[n].hi);
}
static int count_nodes(int root) {
    if(vis_cap<bdd_count){vis=realloc(vis,bdd_count*sizeof(int));vis_cap=bdd_count;}
    memset(vis,0,vis_cap*sizeof(int)); return cnt_rec(root);
}

static double satcount(int node,int level) {
    if(node==BDD_FALSE)return 0.0;
    if(node==BDD_TRUE)return ldexp(1.0,NVARS-level);
    int v=bdd_nodes[node].var;
    return ldexp(1.0,v-level)*(satcount(bdd_nodes[node].lo,v+1)+satcount(bdd_nodes[node].hi,v+1));
}

/* ================================================================ */

int main(int argc, char **argv) {
    setbuf(stdout, NULL);
    struct timespec t0, t_now;
    clock_gettime(CLOCK_MONOTONIC, &t0);

    N = (argc>1) ? atoi(argv[1]) : 9;
    if(N<4||N>12){printf("N must be 4..12\n");return 1;}
    MASK=(1U<<N)-1;
    NVARS=4*N;
    int INNER_NVARS = 3*N;
    uint32_t SIZE = 1U<<N;

    printf("=== Streaming BDD for N=%d ===\n", N);
    printf("Outer: W57 (2^%d = %u values)\n", N, SIZE);
    printf("Inner: W58,W59,W60 (2^%d = %llu TT entries per slice)\n",
           INNER_NVARS, 1ULL<<INNER_NVARS);
    printf("Memory per slice: %.0f MB\n", (double)(1ULL<<INNER_NVARS)/(1<<20));
    printf("Total BDD vars: %d\n\n", NVARS);

    /* Init */
    rS0[0]=scale_rot(2);rS0[1]=scale_rot(13);rS0[2]=scale_rot(22);
    rS1[0]=scale_rot(6);rS1[1]=scale_rot(11);rS1[2]=scale_rot(25);
    rs0[0]=scale_rot(7);rs0[1]=scale_rot(18);ss0=scale_rot(3);
    rs1[0]=scale_rot(17);rs1[1]=scale_rot(19);ss1=scale_rot(10);
    for(int i=0;i<64;i++)KN[i]=K32[i]&MASK;
    for(int i=0;i<8;i++)IVN[i]=IV32[i]&MASK;

    /* Find first valid candidate */
    uint32_t M0=0, KMSB=0, best_fill=MASK;
    int kbit=-1, found=0;
    uint32_t fills[]={MASK, 0x55555555&MASK, 0xAAAAAAAA&MASK, 0, MASK/2, (MASK+1)/2};
    int nfills=6;
    for(int fi=0;fi<nfills&&!found;fi++){
        uint32_t fill=fills[fi]&MASK;
        for(int kb=N-1;kb>=0&&!found;kb--){
            uint32_t kbm=1U<<kb;
            for(uint32_t m0=0;m0<SIZE&&!found;m0++){
                uint32_t M1[16],M2[16],st1[8],st2[8],W1t[57],W2t[57];
                for(int i=0;i<16;i++){M1[i]=fill;M2[i]=fill;}
                M1[0]=m0;M2[0]=m0^kbm;M2[9]=fill^kbm;
                precompute(M1,st1,W1t);precompute(M2,st2,W2t);
                if(((st1[0]-st2[0])&MASK)==0){
                    /* Quick collision check: try a few w57 values */
                    int has=0;
                    for(uint32_t tw57=0;tw57<SIZE&&!has;tw57+=SIZE/8+(tw57==0?0:1)){
                    uint32_t sa[8],sb[8]; memcpy(sa,st1,32);memcpy(sb,st2,32);
                    uint32_t w57b=find_w2(sa,sb,57,tw57);
                    sha_round(sa,KN[57],tw57);sha_round(sb,KN[57],w57b);
                    for(uint32_t w58=0;w58<SIZE&&!has;w58++){
                        uint32_t s58a[8],s58b[8]; memcpy(s58a,sa,32);memcpy(s58b,sb,32);
                        uint32_t w58b=find_w2(s58a,s58b,58,w58);
                        sha_round(s58a,KN[58],w58);sha_round(s58b,KN[58],w58b);
                        for(uint32_t w59=0;w59<SIZE&&!has;w59++){
                            uint32_t s59a[8],s59b[8]; memcpy(s59a,s58a,32);memcpy(s59b,s58b,32);
                            uint32_t w59b=find_w2(s59a,s59b,59,w59);
                            sha_round(s59a,KN[59],w59);sha_round(s59b,KN[59],w59b);
                            uint32_t co60=find_w2(s59a,s59b,60,0);
                            uint32_t cw61a=(fns1(w59)+W1t[54]+fns0(W1t[46])+W1t[45])&MASK;
                            uint32_t cw61b=(fns1(w59b)+W2t[54]+fns0(W2t[46])+W2t[45])&MASK;
                            uint32_t sc62a=(W1t[55]+fns0(W1t[47])+W1t[46])&MASK;
                            uint32_t sc62b=(W2t[55]+fns0(W2t[47])+W2t[46])&MASK;
                            uint32_t cw63a=(fns1(cw61a)+W1t[56]+fns0(W1t[48])+W1t[47])&MASK;
                            uint32_t cw63b=(fns1(cw61b)+W2t[56]+fns0(W2t[48])+W2t[47])&MASK;
                            for(uint32_t w60=0;w60<SIZE&&!has;w60++){
                                uint32_t w60b=(w60+co60)&MASK;
                                uint32_t s60a[8],s60b[8]; memcpy(s60a,s59a,32);memcpy(s60b,s59b,32);
                                sha_round(s60a,KN[60],w60);sha_round(s60b,KN[60],w60b);
                                uint32_t s61a[8],s61b[8]; memcpy(s61a,s60a,32);memcpy(s61b,s60b,32);
                                sha_round(s61a,KN[61],cw61a);sha_round(s61b,KN[61],cw61b);
                                uint32_t cw62a=(fns1(w60)+sc62a)&MASK;
                                uint32_t cw62b=(fns1(w60b)+sc62b)&MASK;
                                sha_round(s61a,KN[62],cw62a);sha_round(s61b,KN[62],cw62b);
                                sha_round(s61a,KN[63],cw63a);sha_round(s61b,KN[63],cw63b);
                                int coll=1;
                                for(int r=0;r<8;r++)if(s61a[r]!=s61b[r]){coll=0;break;}
                                if(coll) has=1;
                            }
                        }
                    }
                    } /* close tw57 loop */
                    if(has){M0=m0;kbit=kb;KMSB=kbm;best_fill=fill;found=1;}
                }
            }
        }
    }
    if(!found){printf("No candidate found\n");return 1;}

    uint32_t M1[16],M2[16],state1[8],state2[8],W1p[57],W2p[57];
    for(int i=0;i<16;i++){M1[i]=best_fill;M2[i]=best_fill;}
    M1[0]=M0;M2[0]=M0^KMSB;M2[9]=best_fill^KMSB;
    precompute(M1,state1,W1p);precompute(M2,state2,W2p);

    clock_gettime(CLOCK_MONOTONIC, &t_now);
    double el=(t_now.tv_sec-t0.tv_sec)+(t_now.tv_nsec-t0.tv_nsec)/1e9;
    printf("Candidate: M[0]=0x%x, fill=0x%x, kernel bit %d (%.1fs)\n\n",
           M0,best_fill,kbit,el);

    /* Init BDD */
    bdd_init();

    /* Allocate partial truth table */
    uint64_t inner_size = 1ULL << INNER_NVARS;
    uint8_t *ptt = calloc(inner_size, 1);
    if(!ptt){printf("OOM for partial TT (%llu bytes)\n",(unsigned long long)inner_size);return 1;}

    /* Main streaming loop */
    uint64_t total_coll = 0;
    int collision_bdd = BDD_FALSE;  /* running OR of all slice BDDs */

    printf("--- Streaming %u slices ---\n", SIZE);

    for(uint32_t w57 = 0; w57 < SIZE; w57++) {
        /* Run round 57 concretely */
        uint32_t s57a[8],s57b[8]; memcpy(s57a,state1,32);memcpy(s57b,state2,32);
        uint32_t w57b = find_w2(s57a,s57b,57,w57);
        sha_round(s57a,KN[57],w57); sha_round(s57b,KN[57],w57b);

        /* Generate partial truth table over (W58,W59,W60) */
        memset(ptt, 0, inner_size);
        uint64_t slice_coll = 0;

        for(uint32_t w58=0;w58<SIZE;w58++) {
            uint32_t s58a[8],s58b[8]; memcpy(s58a,s57a,32);memcpy(s58b,s57b,32);
            uint32_t w58b=find_w2(s58a,s58b,58,w58);
            sha_round(s58a,KN[58],w58);sha_round(s58b,KN[58],w58b);
            for(uint32_t w59=0;w59<SIZE;w59++) {
                uint32_t s59a[8],s59b[8]; memcpy(s59a,s58a,32);memcpy(s59b,s58b,32);
                uint32_t w59b=find_w2(s59a,s59b,59,w59);
                sha_round(s59a,KN[59],w59);sha_round(s59b,KN[59],w59b);
                uint32_t co60=find_w2(s59a,s59b,60,0);
                uint32_t cw61a=(fns1(w59)+W1p[54]+fns0(W1p[46])+W1p[45])&MASK;
                uint32_t cw61b=(fns1(w59b)+W2p[54]+fns0(W2p[46])+W2p[45])&MASK;
                uint32_t sc62a=(W1p[55]+fns0(W1p[47])+W1p[46])&MASK;
                uint32_t sc62b=(W2p[55]+fns0(W2p[47])+W2p[46])&MASK;
                uint32_t cw63a=(fns1(cw61a)+W1p[56]+fns0(W1p[48])+W1p[47])&MASK;
                uint32_t cw63b=(fns1(cw61b)+W2p[56]+fns0(W2p[48])+W2p[47])&MASK;
                for(uint32_t w60=0;w60<SIZE;w60++) {
                    uint32_t w60b=(w60+co60)&MASK;
                    uint32_t s60a[8],s60b[8]; memcpy(s60a,s59a,32);memcpy(s60b,s59b,32);
                    sha_round(s60a,KN[60],w60);sha_round(s60b,KN[60],w60b);
                    uint32_t s61a[8],s61b[8]; memcpy(s61a,s60a,32);memcpy(s61b,s60b,32);
                    sha_round(s61a,KN[61],cw61a);sha_round(s61b,KN[61],cw61b);
                    uint32_t cw62a=(fns1(w60)+sc62a)&MASK;
                    uint32_t cw62b=(fns1(w60b)+sc62b)&MASK;
                    sha_round(s61a,KN[62],cw62a);sha_round(s61b,KN[62],cw62b);
                    sha_round(s61a,KN[63],cw63a);sha_round(s61b,KN[63],cw63b);
                    int coll=1;
                    for(int r=0;r<8;r++)if(s61a[r]!=s61b[r]){coll=0;break;}
                    if(coll) {
                        /* Interleaved inner index: bit 3*b+0=W58[b], 3*b+1=W59[b], 3*b+2=W60[b] */
                        uint32_t idx=0;
                        for(int b=0;b<N;b++){
                            idx|=((w58>>b)&1)<<(3*b+0);
                            idx|=((w59>>b)&1)<<(3*b+1);
                            idx|=((w60>>b)&1)<<(3*b+2);
                        }
                        ptt[idx] = 1;
                        slice_coll++;
                    }
                }
            }
        }

        total_coll += slice_coll;

        if(slice_coll > 0) {
            /* Build inner BDD from partial truth table */
            int inner_root = build_inner_bdd(ptt, INNER_NVARS);

            /* Wrap with W57 constraint: AND with (W57 == w57) */
            /* W57[b] = variable 4*b+0 */
            int w57_constraint = BDD_TRUE;
            for(int b=N-1; b>=0; b--) {
                int var = 4*b;
                int bit = (w57>>b)&1;
                int var_bdd = bdd_make(var, BDD_FALSE, BDD_TRUE);
                int lit = bit ? var_bdd : bdd_make(var, BDD_TRUE, BDD_FALSE);
                w57_constraint = bdd_apply(OP_AND, w57_constraint, lit);
            }
            int slice_bdd = bdd_apply(OP_AND, w57_constraint, inner_root);

            /* OR into running collision BDD */
            collision_bdd = bdd_apply(OP_OR, collision_bdd, slice_bdd);
        }

        /* Progress */
        if((w57 & (SIZE/8 > 0 ? SIZE/8-1 : 0)) == 0 || w57 == SIZE-1) {
            clock_gettime(CLOCK_MONOTONIC, &t_now);
            el=(t_now.tv_sec-t0.tv_sec)+(t_now.tv_nsec-t0.tv_nsec)/1e9;
            int cn = count_nodes(collision_bdd);
            printf("  w57=%u/%u coll=%llu running_bdd=%d total_nodes=%d (%.1fs)\n",
                   w57+1,SIZE,(unsigned long long)total_coll,cn,bdd_count-2,el);
        }
    }

    free(ptt);

    clock_gettime(CLOCK_MONOTONIC, &t_now);
    el=(t_now.tv_sec-t0.tv_sec)+(t_now.tv_nsec-t0.tv_nsec)/1e9;

    int final_nodes = count_nodes(collision_bdd);
    double sat = satcount(collision_bdd, 0);

    printf("\n=== RESULTS ===\n\n");
    printf("N = %d\n", N);
    printf("BDD nodes: %d\n", final_nodes);
    printf("Collisions: %.0f (enumerated: %llu)\n", sat, (unsigned long long)total_coll);
    printf("Match: %s\n", ((uint64_t)sat==total_coll)?"YES":"NO");
    printf("Total BDD nodes allocated: %d\n", bdd_count-2);
    printf("Total time: %.1fs\n", el);

    free(bdd_nodes);free(uentry_pool);free(uhash_table);free(comp_table);free(vis);
    return 0;
}
