/*
 * bdd_parametric.c — Parametric truth-table BDD for N=2..8
 *
 * Generates truth table via cascade DP, builds BDD bottom-up.
 * Generalizes bdd_n8.c to arbitrary N.
 *
 * Truth table size: 2^{4N} bits = 2^{4N-3} bytes
 *   N=4: 8KB,  N=5: 4MB,  N=6: 2MB(!),  N=7: 512MB,  N=8: 512MB
 *   Wait: N=5: 2^20 bits = 128KB. N=6: 2^24 = 2MB. N=7: 2^28 = 32MB.
 *
 * Compile: gcc -O3 -march=native -o bdd_param bdd_parametric.c -lm
 * Usage: ./bdd_param [N]
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <time.h>

static int N;
static uint32_t MASK, MSB_BIT;
static int NVARS;

/* ---- BDD core (index-based chains) ---- */

typedef struct { int var, lo, hi; } BDDNode;
#define BDD_FALSE 0
#define BDD_TRUE  1

static BDDNode *bdd_nodes; static int bdd_count, bdd_cap;

typedef struct { int var,lo,hi,node_id,next; } UEntry;
#define UHASH_BITS 22
#define UHASH_SIZE (1<<UHASH_BITS)
#define UHASH_MASK (UHASH_SIZE-1)
static int *uhash_table; static UEntry *uentry_pool; static int uentry_count, uentry_cap;

static void bdd_init(void) {
    bdd_cap=1<<20; bdd_nodes=malloc(bdd_cap*sizeof(BDDNode));
    bdd_nodes[0]=(BDDNode){-1,0,0}; bdd_nodes[1]=(BDDNode){-1,1,1}; bdd_count=2;
    uhash_table=malloc(UHASH_SIZE*sizeof(int));
    for(int i=0;i<UHASH_SIZE;i++) uhash_table[i]=-1;
    uentry_cap=1<<20; uentry_pool=malloc(uentry_cap*sizeof(UEntry)); uentry_count=0;
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

/* ---- SHA-256 concrete primitives ---- */
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

static inline void sha_round(uint32_t s[8],uint32_t k,uint32_t w) {
    uint32_t T1=(s[7]+fnS1(s[4])+fnCh(s[4],s[5],s[6])+k+w)&MASK;
    uint32_t T2=(fnS0(s[0])+fnMj(s[0],s[1],s[2]))&MASK;
    s[7]=s[6];s[6]=s[5];s[5]=s[4];s[4]=(s[3]+T1)&MASK;
    s[3]=s[2];s[2]=s[1];s[1]=s[0];s[0]=(T1+T2)&MASK;
}

static inline uint32_t find_w2(const uint32_t s1[8],const uint32_t s2[8],int rnd,uint32_t w1) {
    uint32_t r1=(s1[7]+fnS1(s1[4])+fnCh(s1[4],s1[5],s1[6])+KN[rnd])&MASK;
    uint32_t r2=(s2[7]+fnS1(s2[4])+fnCh(s2[4],s2[5],s2[6])+KN[rnd])&MASK;
    uint32_t T21=(fnS0(s1[0])+fnMj(s1[0],s1[1],s1[2]))&MASK;
    uint32_t T22=(fnS0(s2[0])+fnMj(s2[0],s2[1],s2[2]))&MASK;
    return(w1+r1-r2+T21-T22)&MASK;
}

/* ---- Interleaved index conversion ---- */
static uint32_t to_interleaved(uint32_t w57,uint32_t w58,uint32_t w59,uint32_t w60) {
    uint32_t idx=0;
    for(int b=0;b<N;b++){
        idx|=((w57>>b)&1)<<(4*b+0);
        idx|=((w58>>b)&1)<<(4*b+1);
        idx|=((w59>>b)&1)<<(4*b+2);
        idx|=((w60>>b)&1)<<(4*b+3);
    }
    return idx;
}

/* ---- Build k-variable BDD from 2^k truth table bits ---- */
static int build_bdd_kvars(const uint8_t *bits, int kvars, const int vars[]) {
    int maxn = 1<<kvars;
    int *layer = malloc(maxn*sizeof(int));
    for(int i=0;i<maxn;i++) layer[i]=bits[i]?BDD_TRUE:BDD_FALSE;
    int count=maxn;
    for(int d=kvars-1;d>=0;d--) {
        int var=vars[d], half=count/2, stride=1<<d, block=stride*2;
        int *nl=malloc(half*sizeof(int));
        int out=0;
        for(int base=0;base<count;base+=block)
            for(int j=0;j<stride;j++)
                nl[out++]=bdd_make(var,layer[base+j],layer[base+j+stride]);
        free(layer); layer=nl; count=half;
    }
    int root=layer[0]; free(layer); return root;
}

/* ---- Merge layer: given 2^kvars node IDs, build kvars-variable BDD ---- */
static int merge_layer(const int *nodes, int kvars, const int vars[]) {
    int maxn=1<<kvars;
    int *layer=malloc(maxn*sizeof(int));
    memcpy(layer,nodes,maxn*sizeof(int));
    int count=maxn;
    for(int d=kvars-1;d>=0;d--) {
        int var=vars[d], half=count/2, stride=1<<d, block=stride*2;
        int *nl=malloc(half*sizeof(int));
        int out=0;
        for(int base=0;base<count;base+=block)
            for(int j=0;j<stride;j++)
                nl[out++]=bdd_make(var,layer[base+j],layer[base+j+stride]);
        free(layer); layer=nl; count=half;
    }
    int root=layer[0]; free(layer); return root;
}

/* ---- BDD node counting ---- */
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

/* ---- SAT count ---- */
static double satcount(int node,int level) {
    if(node==BDD_FALSE)return 0.0;
    if(node==BDD_TRUE)return ldexp(1.0,NVARS-level);
    int v=bdd_nodes[node].var;
    return ldexp(1.0,v-level)*(satcount(bdd_nodes[node].lo,v+1)+satcount(bdd_nodes[node].hi,v+1));
}

/* ================================================================ */

int main(int argc,char**argv) {
    setbuf(stdout,NULL);
    struct timespec t0,t1,t2;
    clock_gettime(CLOCK_MONOTONIC,&t0);

    N=(argc>1)?atoi(argv[1]):4;
    if(N<2||N>8){printf("N must be 2..8\n");return 1;}
    MASK=(1U<<N)-1; MSB_BIT=1U<<(N-1); NVARS=4*N;

    rS0[0]=scale_rot(2);rS0[1]=scale_rot(13);rS0[2]=scale_rot(22);
    rS1[0]=scale_rot(6);rS1[1]=scale_rot(11);rS1[2]=scale_rot(25);
    rs0[0]=scale_rot(7);rs0[1]=scale_rot(18);ss0=scale_rot(3);
    rs1[0]=scale_rot(17);rs1[1]=scale_rot(19);ss1=scale_rot(10);
    for(int i=0;i<64;i++)KN[i]=K32[i]&MASK;
    for(int i=0;i<8;i++)IVN[i]=IV32[i]&MASK;

    printf("=== Parametric BDD for N=%d (NVARS=%d) ===\n\n",N,NVARS);

    /* Find first valid candidate: try kernel bits + fills, find one with da56=0.
     * Use known good candidates where available, otherwise search.
     * Fills: 0xff (all ones), 0x55 (alternating), 0x00 (all zeros) */
    uint32_t best_m0=0; int best_kbit=-1;
    uint32_t best_KMSB=0, best_fill=MASK;
    uint32_t SIZE=1U<<N;

    printf("Searching for valid candidate...\n");
    uint32_t fills[] = {MASK, MASK/3, 0, MASK/2, (MASK+1)/2};  /* various fills */
    int nfills = 5;
    int found_cand = 0;

    for(int fi=0;fi<nfills&&!found_cand;fi++) {
        uint32_t fill = fills[fi] & MASK;
        for(int kbit=N-1;kbit>=0&&!found_cand;kbit--) {
            uint32_t kb=1U<<kbit;
            for(uint32_t m0=0;m0<SIZE&&!found_cand;m0++) {
                uint32_t M1t[16],M2t[16],st1[8],st2[8],W1t[57],W2t[57];
                for(int i=0;i<16;i++){M1t[i]=fill;M2t[i]=fill;}
                M1t[0]=m0;M2t[0]=m0^kb;M2t[9]=fill^kb;
                precompute(M1t,st1,W1t); precompute(M2t,st2,W2t);
                if(((st1[0]-st2[0])&MASK)!=0) continue;

                /* Quick check: sample a few w57 values for collisions */
                int has_coll = 0;
                for(uint32_t w57=0;w57<SIZE&&!has_coll;w57++) {
                    uint32_t sa[8],sb[8]; memcpy(sa,st1,32);memcpy(sb,st2,32);
                    uint32_t w57b=find_w2(sa,sb,57,w57);
                    sha_round(sa,KN[57],w57);sha_round(sb,KN[57],w57b);
                    for(uint32_t w58=0;w58<SIZE&&!has_coll;w58++) {
                        uint32_t s58a[8],s58b[8]; memcpy(s58a,sa,32);memcpy(s58b,sb,32);
                        uint32_t w58b=find_w2(s58a,s58b,58,w58);
                        sha_round(s58a,KN[58],w58);sha_round(s58b,KN[58],w58b);
                        for(uint32_t w59=0;w59<SIZE&&!has_coll;w59++) {
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
                            for(uint32_t w60=0;w60<SIZE&&!has_coll;w60++) {
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
                                for(int r=0;r<8;r++) if(s61a[r]!=s61b[r]){coll=0;break;}
                                if(coll) has_coll=1;
                            }
                        }
                    }
                }
                if(has_coll) {
                    best_m0=m0;best_kbit=kbit;best_KMSB=kb;best_fill=fill;
                    found_cand=1;
                }
            }
        }
    }

    if(!found_cand){printf("No collisions found for any candidate at N=%d\n",N);return 1;}

    printf("Found: M[0]=0x%x, fill=0x%x, kernel bit %d\n\n",best_m0,best_fill,best_kbit);

    /* Setup the found candidate */
    uint32_t M1[16],M2[16],state1[8],state2[8],W1p[57],W2p[57];
    for(int i=0;i<16;i++){M1[i]=best_fill;M2[i]=best_fill;}
    M1[0]=best_m0;M2[0]=best_m0^best_KMSB;M2[9]=best_fill^best_KMSB;
    precompute(M1,state1,W1p); precompute(M2,state2,W2p);

    clock_gettime(CLOCK_MONOTONIC,&t1);
    double search_time=(t1.tv_sec-t0.tv_sec)+(t1.tv_nsec-t0.tv_nsec)/1e9;
    printf("Candidate search: %.2fs\n",search_time);

    /* ---- Generate truth table (interleaved bit order) ---- */
    uint64_t tt_size = 1ULL<<NVARS;  /* number of entries */
    uint64_t tt_bytes = tt_size/8;
    printf("Truth table: 2^%d = %llu entries (%llu bytes = %.1f MB)\n",
           NVARS,(unsigned long long)tt_size,(unsigned long long)tt_bytes,
           (double)tt_bytes/(1<<20));

    uint8_t *tt = calloc(tt_bytes,1);
    if(!tt){printf("OOM for truth table\n");return 1;}

    uint64_t ncoll=0;
    for(uint32_t w57=0;w57<SIZE;w57++) {
        uint32_t sa[8],sb[8]; memcpy(sa,state1,32);memcpy(sb,state2,32);
        uint32_t w57b=find_w2(sa,sb,57,w57);
        sha_round(sa,KN[57],w57);sha_round(sb,KN[57],w57b);
        for(uint32_t w58=0;w58<SIZE;w58++) {
            uint32_t s58a[8],s58b[8]; memcpy(s58a,sa,32);memcpy(s58b,sb,32);
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
                    for(int r=0;r<8;r++) if(s61a[r]!=s61b[r]){coll=0;break;}
                    if(coll) {
                        uint32_t idx=to_interleaved(w57,w58,w59,w60);
                        tt[idx>>3]|=(1U<<(idx&7));
                        ncoll++;
                    }
                }
            }
        }
    }

    clock_gettime(CLOCK_MONOTONIC,&t1);
    double tt_time=(t1.tv_sec-t0.tv_sec)+(t1.tv_nsec-t0.tv_nsec)/1e9-search_time;
    printf("Truth table generated: %llu collisions in %.2fs\n\n",(unsigned long long)ncoll,tt_time);

    /* ---- Build BDD bottom-up ---- */
    /* Process variables in groups of min(4, remaining).
     * Start from the deepest variables (NVARS-1 downward). */
    bdd_init();

    int group_size = 4;  /* variables per group */
    int n_groups = (NVARS + group_size - 1) / group_size;

    printf("Building BDD: %d groups of %d variables\n",n_groups,group_size);

    /* Layer 0 (deepest): process the top group_size variables */
    int first_var = NVARS - group_size;  /* e.g., NVARS=16, first_var=12 */
    int g0_count = 1 << first_var;  /* number of prefixes */
    int g0_chunk = 1 << group_size; /* 16 entries per chunk */

    int *layer = malloc(g0_count * sizeof(int));
    int vars_g[32];

    /* Group 0: variables [first_var .. NVARS-1] */
    for(int i=0;i<group_size;i++) vars_g[i] = first_var + i;

    for(int prefix=0;prefix<g0_count;prefix++) {
        uint8_t bits[16]; /* max 2^4 = 16 */
        for(int s=0;s<g0_chunk;s++) {
            uint32_t idx = prefix | ((uint32_t)s << first_var);
            bits[s] = (tt[idx>>3]>>(idx&7))&1;
        }
        layer[prefix] = build_bdd_kvars(bits, group_size, vars_g);
    }
    int layer_count = g0_count;
    printf("  Group 0 (vars %d-%d): %d -> %d entries, BDD nodes: %d\n",
           first_var, NVARS-1, g0_count, layer_count, bdd_count-2);

    /* Subsequent groups */
    for(int g=1; g<n_groups; g++) {
        int base_var = first_var - g * group_size;
        if(base_var < 0) base_var = 0;
        int gvars = first_var - g * group_size >= 0 ? group_size :
                    (first_var - (g-1) * group_size);
        base_var = NVARS - (g+1)*group_size;
        if(base_var < 0) { gvars = NVARS - g*group_size; base_var = 0; }

        for(int i=0;i<gvars;i++) vars_g[i] = base_var + i;
        int new_count = layer_count >> gvars;
        int chunk_size = 1 << gvars;
        int *new_layer = malloc(new_count * sizeof(int));

        for(int prefix=0;prefix<new_count;prefix++) {
            int chunk[16]; /* max 2^4 = 16 */
            for(int s=0;s<chunk_size;s++) {
                int old_idx = prefix | (s << (base_var > 0 ? base_var : 0));
                /* Need to map correctly: old layer index is bits 0..base_var+gvars-1,
                 * new prefix is bits 0..base_var-1,
                 * s provides bits base_var..base_var+gvars-1 */
                old_idx = prefix | (s << (base_var > 0 ? (int)log2(new_count) : 0));
                /* Simpler: layer index bits 0..layer_bits-1 where layer_bits = log2(layer_count).
                 * We split into prefix (lower bits) and suffix (upper gvars bits).
                 * prefix bits = layer_bits - gvars, suffix bits = gvars. */
                int layer_bits = 0; { int lc=layer_count; while(lc>1){layer_bits++;lc>>=1;} }
                int prefix_bits = layer_bits - gvars;
                old_idx = prefix | (s << prefix_bits);
                chunk[s] = layer[old_idx];
            }
            new_layer[prefix] = merge_layer(chunk, gvars, vars_g);
        }

        free(layer); layer = new_layer; layer_count = new_count;
        printf("  Group %d (vars %d-%d): -> %d entries, BDD nodes: %d\n",
               g, base_var, base_var+gvars-1, layer_count, bdd_count-2);
    }

    int root = layer[0];
    free(layer); free(tt);

    clock_gettime(CLOCK_MONOTONIC,&t2);
    double bdd_time=(t2.tv_sec-t1.tv_sec)+(t2.tv_nsec-t1.tv_nsec)/1e9;
    double total=(t2.tv_sec-t0.tv_sec)+(t2.tv_nsec-t0.tv_nsec)/1e9;

    int final_nodes = count_nodes(root);
    double sat = satcount(root, 0);

    printf("\n=== RESULTS ===\n\n");
    printf("| N | BDD nodes | Variables | Collisions | TT density | Time |\n");
    printf("|---|-----------|-----------|------------|------------|------|\n");
    printf("| %d | %d | %d | %.0f | %.2e | %.2fs |\n",
           N, final_nodes, NVARS, sat, sat/ldexp(1.0,NVARS), total);

    printf("\nBDD nodes: %d\n", final_nodes);
    printf("Collisions: %.0f (truth table: %llu)\n", sat, (unsigned long long)ncoll);
    printf("Match: %s\n", ((uint64_t)sat==ncoll)?"YES":"NO");
    printf("BDD build time: %.2fs\n", bdd_time);
    printf("Total time: %.2fs\n", total);

    /* Per-variable level node counts */
    printf("\nNodes per variable:\n");
    int var_cnt[64]; memset(var_cnt,0,sizeof(var_cnt));
    for(int i=2;i<bdd_count;i++)
        if(bdd_nodes[i].var>=0&&bdd_nodes[i].var<NVARS) var_cnt[bdd_nodes[i].var]++;
    for(int v=0;v<NVARS;v++) {
        const char *wn; int bit;
        switch(v%4){case 0:wn="W57";break;case 1:wn="W58";break;case 2:wn="W59";break;default:wn="W60";}
        bit=v/4;
        if(var_cnt[v]>0) printf("  var %2d (%s[%d]): %d\n",v,wn,bit,var_cnt[v]);
    }

    free(bdd_nodes);free(uentry_pool);free(uhash_table);free(vis);
    return 0;
}
