/*
 * bdd_n10.c — BDD construction for N=10 collision function
 *
 * Double outer loop: enumerate (W57, W58) concretely (2^20 = 1M iterations)
 * Inner BDD: W59, W60 (20 variables, 2^20 = 1M truth table entries)
 *
 * This avoids the 1TB full truth table (2^40 bits).
 * Inner TT is only 1MB per iteration.
 *
 * Compile: gcc -O3 -march=native -o bdd_n10 bdd_n10.c -lm
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <time.h>

#define N 10
#define MASK ((1U<<N)-1)
#define NVARS (4*N)  /* 40 total BDD variables */
#define INNER_NVARS (2*N)  /* 20 inner variables (W59, W60) */

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
    for(int ei=uhash_table[h];ei>=0;ei=uentry_pool[ei].next){
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

enum { OP_AND=0, OP_OR=1 };
static int bdd_apply(int op, int f, int g) {
    if(f<=1&&g<=1) return (op==OP_AND?(f&g):(f|g))?BDD_TRUE:BDD_FALSE;
    if(op==OP_AND){
        if(f==BDD_FALSE||g==BDD_FALSE) return BDD_FALSE;
        if(f==BDD_TRUE) return g; if(g==BDD_TRUE) return f; if(f==g) return f;
    } else {
        if(f==BDD_TRUE||g==BDD_TRUE) return BDD_TRUE;
        if(f==BDD_FALSE) return g; if(g==BDD_FALSE) return f; if(f==g) return f;
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

/* ---- SHA-256 ---- */
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
static void precompute(const uint32_t M[16],uint32_t st[8],uint32_t W[57]){
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

/* Build inner BDD from 2^{2N} partial truth table (W59, W60 only).
 * Variable ordering: var 4*b+2 (W59[b]), var 4*b+3 (W60[b]).
 * TT index: bit 2*b+0 = W59[b], bit 2*b+1 = W60[b]. */
static int build_inner_bdd_2w(const uint8_t *tt) {
    uint32_t count = 1U << INNER_NVARS;
    int *layer = malloc(count * sizeof(int));
    for(uint32_t i=0;i<count;i++) layer[i]=tt[i]?BDD_TRUE:BDD_FALSE;

    for(int b=N-1; b>=0; b--) {
        /* Process var 4*b+3 (W60[b]) then var 4*b+2 (W59[b]) */
        /* W60[b] is at TT index bit 2*b+1 */
        {
            uint32_t half=count/2;
            uint32_t stride=1U<<(2*b+1), block=stride*2;
            int *nl=malloc(half*sizeof(int));
            uint32_t out=0;
            for(uint32_t base=0;base<count;base+=block)
                for(uint32_t j=0;j<stride;j++)
                    nl[out++]=bdd_make(4*b+3, layer[base+j], layer[base+j+stride]);
            free(layer); layer=nl; count=half;
        }
        /* W59[b] at TT index bit 2*b */
        {
            uint32_t half=count/2;
            uint32_t stride=1U<<(2*b), block=stride*2;
            int *nl=malloc(half*sizeof(int));
            uint32_t out=0;
            for(uint32_t base=0;base<count;base+=block)
                for(uint32_t j=0;j<stride;j++)
                    nl[out++]=bdd_make(4*b+2, layer[base+j], layer[base+j+stride]);
            free(layer); layer=nl; count=half;
        }
    }
    int root=layer[0]; free(layer); return root;
}

/* Node counting */
static int *vis; static int vis_cap;
static int cnt_rec(int n){
    if(n<=1)return 0;
    if(n>=vis_cap){int nc=n+1;vis=realloc(vis,nc*sizeof(int));
        memset(vis+vis_cap,0,(nc-vis_cap)*sizeof(int));vis_cap=nc;}
    if(vis[n])return 0; vis[n]=1;
    return 1+cnt_rec(bdd_nodes[n].lo)+cnt_rec(bdd_nodes[n].hi);
}
static int count_nodes(int root){
    if(vis_cap<bdd_count){vis=realloc(vis,bdd_count*sizeof(int));vis_cap=bdd_count;}
    memset(vis,0,vis_cap*sizeof(int)); return cnt_rec(root);
}
static double satcount(int node,int level){
    if(node==BDD_FALSE)return 0.0;
    if(node==BDD_TRUE)return ldexp(1.0,NVARS-level);
    int v=bdd_nodes[node].var;
    return ldexp(1.0,v-level)*(satcount(bdd_nodes[node].lo,v+1)+satcount(bdd_nodes[node].hi,v+1));
}

int main(int argc, char **argv) {
    setbuf(stdout,NULL);
    struct timespec t0,t_now;
    clock_gettime(CLOCK_MONOTONIC,&t0);

    rS0[0]=scale_rot(2);rS0[1]=scale_rot(13);rS0[2]=scale_rot(22);
    rS1[0]=scale_rot(6);rS1[1]=scale_rot(11);rS1[2]=scale_rot(25);
    rs0[0]=scale_rot(7);rs0[1]=scale_rot(18);ss0=scale_rot(3);
    rs1[0]=scale_rot(17);rs1[1]=scale_rot(19);ss1=scale_rot(10);
    for(int i=0;i<64;i++)KN[i]=K32[i]&MASK;
    for(int i=0;i<8;i++)IVN[i]=IV32[i]&MASK;

    uint32_t SIZE=1U<<N;
    printf("=== N=10 BDD Construction ===\n");
    printf("Outer: W57,W58 (2^%d = %u iterations)\n", 2*N, 1U<<(2*N));
    printf("Inner: W59,W60 (2^%d = %u TT entries, %d variables)\n",
           INNER_NVARS, 1U<<INNER_NVARS, INNER_NVARS);
    printf("Full BDD: %d variables\n\n", NVARS);

    /* Use known good candidate: bit 9 (MSB), fill=0x1ff */
    /* From cascade_structure_complete.md: N=10 best is bit 9, fill=0x1ff, 1833 coll */
    uint32_t M0 = 0; int kbit = 9;
    uint32_t KMSB = 1U<<kbit, fill = MASK;  /* fill = 0x3ff */

    /* Search for valid M[0] with this kernel */
    printf("Searching for valid candidate (kernel bit %d, fill=0x%x)...\n", kbit, fill);
    int found=0;
    uint32_t M1[16],M2[16],state1[8],state2[8],W1p[57],W2p[57];
    for(uint32_t m0=0;m0<SIZE&&!found;m0++){
        for(int i=0;i<16;i++){M1[i]=fill;M2[i]=fill;}
        M1[0]=m0;M2[0]=m0^KMSB;M2[9]=fill^KMSB;
        precompute(M1,state1,W1p);precompute(M2,state2,W2p);
        if(((state1[0]-state2[0])&MASK)==0){M0=m0;found=1;}
    }
    if(!found){
        /* Try other kernel bits */
        printf("MSB kernel failed, trying others...\n");
        uint32_t fills[]={MASK,0x55555555&MASK,0xAAAAAAAA&MASK,0,(MASK+1)/2};
        for(int fi=0;fi<5&&!found;fi++){
            fill=fills[fi];
            for(kbit=N-1;kbit>=0&&!found;kbit--){
                KMSB=1U<<kbit;
                for(uint32_t m0=0;m0<SIZE&&!found;m0++){
                    for(int i=0;i<16;i++){M1[i]=fill;M2[i]=fill;}
                    M1[0]=m0;M2[0]=m0^KMSB;M2[9]=fill^KMSB;
                    precompute(M1,state1,W1p);precompute(M2,state2,W2p);
                    if(((state1[0]-state2[0])&MASK)==0){M0=m0;found=1;}
                }
            }
        }
    }
    if(!found){printf("No candidate found!\n");return 1;}

    for(int i=0;i<16;i++){M1[i]=fill;M2[i]=fill;}
    M1[0]=M0;M2[0]=M0^KMSB;M2[9]=fill^KMSB;
    precompute(M1,state1,W1p);precompute(M2,state2,W2p);

    clock_gettime(CLOCK_MONOTONIC,&t_now);
    double el=(t_now.tv_sec-t0.tv_sec)+(t_now.tv_nsec-t0.tv_nsec)/1e9;
    printf("Candidate: M[0]=0x%x, fill=0x%x, kernel bit %d (%.1fs)\n\n",M0,fill,kbit,el);

    /* Init BDD */
    bdd_init();

    /* Allocate inner truth table */
    uint32_t inner_size = 1U << INNER_NVARS;
    uint8_t *ptt = calloc(inner_size, 1);
    if(!ptt){printf("OOM\n");return 1;}

    uint64_t total_coll=0;
    int collision_bdd = BDD_FALSE;
    uint64_t outer_total = (uint64_t)SIZE * SIZE;  /* 2^20 */
    uint64_t outer_done = 0;
    uint64_t report_interval = outer_total / 16;
    if(report_interval == 0) report_interval = 1;

    printf("--- Streaming %llu outer iterations ---\n", (unsigned long long)outer_total);

    for(uint32_t w57=0; w57<SIZE; w57++) {
        uint32_t s57a[8],s57b[8]; memcpy(s57a,state1,32);memcpy(s57b,state2,32);
        uint32_t w57b=find_w2(s57a,s57b,57,w57);
        sha_round(s57a,KN[57],w57);sha_round(s57b,KN[57],w57b);

        for(uint32_t w58=0; w58<SIZE; w58++) {
            uint32_t s58a[8],s58b[8]; memcpy(s58a,s57a,32);memcpy(s58b,s57b,32);
            uint32_t w58b=find_w2(s58a,s58b,58,w58);
            sha_round(s58a,KN[58],w58);sha_round(s58b,KN[58],w58b);

            /* Generate inner TT over (W59, W60) */
            memset(ptt, 0, inner_size);
            uint64_t slice_coll=0;

            for(uint32_t w59=0;w59<SIZE;w59++){
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
                for(uint32_t w60=0;w60<SIZE;w60++){
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
                    if(coll){
                        /* Inner TT index: interleaved W59,W60 */
                        uint32_t idx=0;
                        for(int b=0;b<N;b++){
                            idx|=((w59>>b)&1)<<(2*b);
                            idx|=((w60>>b)&1)<<(2*b+1);
                        }
                        ptt[idx]=1;
                        slice_coll++;
                    }
                }
            }

            total_coll += slice_coll;

            if(slice_coll > 0) {
                int inner_root = build_inner_bdd_2w(ptt);

                /* Wrap with W57==w57 AND W58==w58 constraints */
                int constraint = BDD_TRUE;
                for(int b=N-1;b>=0;b--){
                    int bit57=(w57>>b)&1, bit58=(w58>>b)&1;
                    int var57=4*b, var58=4*b+1;
                    int lit57 = bit57 ? bdd_make(var57,BDD_FALSE,BDD_TRUE) : bdd_make(var57,BDD_TRUE,BDD_FALSE);
                    int lit58 = bit58 ? bdd_make(var58,BDD_FALSE,BDD_TRUE) : bdd_make(var58,BDD_TRUE,BDD_FALSE);
                    constraint = bdd_apply(OP_AND, constraint, lit57);
                    constraint = bdd_apply(OP_AND, constraint, lit58);
                }
                int slice_bdd = bdd_apply(OP_AND, constraint, inner_root);
                collision_bdd = bdd_apply(OP_OR, collision_bdd, slice_bdd);
            }

            outer_done++;
            if(outer_done % report_interval == 0 || outer_done == outer_total) {
                clock_gettime(CLOCK_MONOTONIC,&t_now);
                el=(t_now.tv_sec-t0.tv_sec)+(t_now.tv_nsec-t0.tv_nsec)/1e9;
                int cn=count_nodes(collision_bdd);
                double pct=100.0*outer_done/outer_total;
                printf("  [%.0f%%] w57=%u w58=%u coll=%llu bdd=%d total_nodes=%d (%.0fs)\n",
                       pct,w57,w58,(unsigned long long)total_coll,cn,bdd_count-2,el);
            }
        }
    }

    free(ptt);

    clock_gettime(CLOCK_MONOTONIC,&t_now);
    el=(t_now.tv_sec-t0.tv_sec)+(t_now.tv_nsec-t0.tv_nsec)/1e9;

    int final_nodes=count_nodes(collision_bdd);
    double sat=satcount(collision_bdd,0);

    printf("\n=== RESULTS ===\n\n");
    printf("N = %d\n", N);
    printf("BDD nodes: %d\n", final_nodes);
    printf("Collisions: %.0f (enumerated: %llu)\n", sat, (unsigned long long)total_coll);
    printf("Match: %s\n", ((uint64_t)sat==total_coll)?"YES":"NO");
    printf("Total BDD nodes: %d\n", bdd_count-2);
    printf("Total time: %.1fs\n", el);

    free(bdd_nodes);free(uentry_pool);free(uhash_table);free(comp_table);free(vis);
    return 0;
}
