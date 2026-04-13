/*
 * de_pruned_search.c — Forward search with e-path diff pruning
 *
 * At each round, prune message words that don't produce valid de values.
 * This reduces 2^{4N} to ~product(|valid_de_sets|) evaluations.
 *
 * Phase 1: Brute-force find all collisions and extract valid de sets
 * Phase 2: Re-search with de pruning, count evaluations
 * Phase 3: Report speedup
 *
 * This proves the de-pruning concept. A practical implementation would
 * predict valid de sets from cascade structure rather than pre-computing them.
 *
 * Compile: gcc -O3 -march=native -o de_pruned_search de_pruned_search.c -lm
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <time.h>

static int gN;
static uint32_t gMASK;
static int rS0[3],rS1[3],rs0[2],rs1[2],ss0,ss1;
static uint32_t KN[64],IVN[8];
static inline uint32_t ror_n(uint32_t x,int k){k%=gN;return((x>>k)|(x<<(gN-k)))&gMASK;}
static inline uint32_t fnS0(uint32_t a){return ror_n(a,rS0[0])^ror_n(a,rS0[1])^ror_n(a,rS0[2]);}
static inline uint32_t fnS1(uint32_t e){return ror_n(e,rS1[0])^ror_n(e,rS1[1])^ror_n(e,rS1[2]);}
static inline uint32_t fns0(uint32_t x){return ror_n(x,rs0[0])^ror_n(x,rs0[1])^((x>>ss0)&gMASK);}
static inline uint32_t fns1(uint32_t x){return ror_n(x,rs1[0])^ror_n(x,rs1[1])^((x>>ss1)&gMASK);}
static inline uint32_t fnCh(uint32_t e,uint32_t f,uint32_t g){return((e&f)^((~e)&g))&gMASK;}
static inline uint32_t fnMj(uint32_t a,uint32_t b,uint32_t c){return((a&b)^(a&c)^(b&c))&gMASK;}
static const uint32_t K32[64]={0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
static const uint32_t IV32[8]={0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};
static int scale_rot(int k32){int r=(int)rint((double)k32*gN/32.0);return r<1?1:r;}
static uint32_t W1pre[57],W2pre[57],state1[8],state2[8];

static void precompute(const uint32_t M[16],uint32_t st[8],uint32_t W[57]){
    for(int i=0;i<16;i++)W[i]=M[i]&gMASK;
    for(int i=16;i<57;i++)W[i]=(fns1(W[i-2])+W[i-7]+fns0(W[i-15])+W[i-16])&gMASK;
    uint32_t a=IVN[0],b=IVN[1],c=IVN[2],d=IVN[3],e=IVN[4],f=IVN[5],g=IVN[6],h=IVN[7];
    for(int i=0;i<57;i++){uint32_t T1=(h+fnS1(e)+fnCh(e,f,g)+KN[i]+W[i])&gMASK,T2=(fnS0(a)+fnMj(a,b,c))&gMASK;h=g;g=f;f=e;e=(d+T1)&gMASK;d=c;c=b;b=a;a=(T1+T2)&gMASK;}
    st[0]=a;st[1]=b;st[2]=c;st[3]=d;st[4]=e;st[5]=f;st[6]=g;st[7]=h;
}
static inline void sha_round(uint32_t s[8],uint32_t k,uint32_t w){
    uint32_t T1=(s[7]+fnS1(s[4])+fnCh(s[4],s[5],s[6])+k+w)&gMASK,T2=(fnS0(s[0])+fnMj(s[0],s[1],s[2]))&gMASK;
    s[7]=s[6];s[6]=s[5];s[5]=s[4];s[4]=(s[3]+T1)&gMASK;s[3]=s[2];s[2]=s[1];s[1]=s[0];s[0]=(T1+T2)&gMASK;
}
static inline uint32_t find_w2(const uint32_t s1[8],const uint32_t s2[8],int rnd,uint32_t w1){
    uint32_t r1=(s1[7]+fnS1(s1[4])+fnCh(s1[4],s1[5],s1[6])+KN[rnd])&gMASK;
    uint32_t r2=(s2[7]+fnS1(s2[4])+fnCh(s2[4],s2[5],s2[6])+KN[rnd])&gMASK;
    uint32_t T21=(fnS0(s1[0])+fnMj(s1[0],s1[1],s1[2]))&gMASK;
    uint32_t T22=(fnS0(s2[0])+fnMj(s2[0],s2[1],s2[2]))&gMASK;
    return(w1+r1-r2+T21-T22)&gMASK;
}

/* Valid de sets — bitmap for fast lookup */
static uint8_t valid_de[4][65536]; /* valid_de[round_offset][value] */

int main(int argc, char *argv[]){
    setbuf(stdout,NULL);
    gN = argc > 1 ? atoi(argv[1]) : 4;
    if(gN > 16){printf("N<=16\n");return 1;}
    gMASK = (1U<<gN)-1;
    rS0[0]=scale_rot(2);rS0[1]=scale_rot(13);rS0[2]=scale_rot(22);
    rS1[0]=scale_rot(6);rS1[1]=scale_rot(11);rS1[2]=scale_rot(25);
    rs0[0]=scale_rot(7);rs0[1]=scale_rot(18);ss0=scale_rot(3);
    rs1[0]=scale_rot(17);rs1[1]=scale_rot(19);ss1=scale_rot(10);
    for(int i=0;i<64;i++)KN[i]=K32[i]&gMASK;
    for(int i=0;i<8;i++)IVN[i]=IV32[i]&gMASK;

    uint32_t MSB=1U<<(gN-1);
    uint32_t fills[]={gMASK,0};int found=0;
    for(int fi=0;fi<2&&!found;fi++){
        for(uint32_t m0=0;m0<=gMASK&&!found;m0++){
            uint32_t M1[16],M2[16];
            for(int i=0;i<16;i++){M1[i]=fills[fi];M2[i]=fills[fi];}
            M1[0]=m0;M2[0]=m0^MSB;M2[9]=fills[fi]^MSB;
            precompute(M1,state1,W1pre);precompute(M2,state2,W2pre);
            if(state1[0]==state2[0]){printf("Candidate: M[0]=0x%x fill=0x%x\n",m0,fills[fi]);found=1;}
        }
    }
    if(!found){printf("No candidate\n");return 1;}

    printf("\n=== Phase 1: Brute force to find valid de sets ===\n");
    struct timespec t0; clock_gettime(CLOCK_MONOTONIC,&t0);

    memset(valid_de,0,sizeof(valid_de));
    int n_coll_bf = 0;
    uint64_t n_eval_bf = 0;

    for(uint32_t w57=0;w57<(1U<<gN);w57++){
        uint32_t s57a[8],s57b[8];memcpy(s57a,state1,32);memcpy(s57b,state2,32);
        uint32_t w57b=find_w2(s57a,s57b,57,w57);
        sha_round(s57a,KN[57],w57);sha_round(s57b,KN[57],w57b);
        for(uint32_t w58=0;w58<(1U<<gN);w58++){
            uint32_t s58a[8],s58b[8];memcpy(s58a,s57a,32);memcpy(s58b,s57b,32);
            uint32_t w58b=find_w2(s58a,s58b,58,w58);
            sha_round(s58a,KN[58],w58);sha_round(s58b,KN[58],w58b);
            for(uint32_t w59=0;w59<(1U<<gN);w59++){
                uint32_t s59a[8],s59b[8];memcpy(s59a,s58a,32);memcpy(s59b,s58b,32);
                uint32_t w59b=find_w2(s59a,s59b,59,w59);
                sha_round(s59a,KN[59],w59);sha_round(s59b,KN[59],w59b);
                for(uint32_t w60=0;w60<(1U<<gN);w60++){
                    uint32_t fa[8],fb[8];memcpy(fa,s59a,32);memcpy(fb,s59b,32);
                    uint32_t w60b=find_w2(fa,fb,60,w60);
                    sha_round(fa,KN[60],w60);sha_round(fb,KN[60],w60b);
                    uint32_t W1[7]={w57,w58,w59,w60,0,0,0},W2[7]={w57b,w58b,w59b,w60b,0,0,0};
                    W1[4]=(fns1(W1[2])+W1pre[54]+fns0(W1pre[46])+W1pre[45])&gMASK;
                    W2[4]=(fns1(W2[2])+W2pre[54]+fns0(W2pre[46])+W2pre[45])&gMASK;
                    W1[5]=(fns1(W1[3])+W1pre[55]+fns0(W1pre[47])+W1pre[46])&gMASK;
                    W2[5]=(fns1(W2[3])+W2pre[55]+fns0(W2pre[47])+W2pre[46])&gMASK;
                    W1[6]=(fns1(W1[4])+W1pre[56]+fns0(W1pre[48])+W1pre[47])&gMASK;
                    W2[6]=(fns1(W2[4])+W2pre[56]+fns0(W2pre[48])+W2pre[47])&gMASK;
                    for(int r=4;r<7;r++){sha_round(fa,KN[57+r],W1[r]);sha_round(fb,KN[57+r],W2[r]);}
                    n_eval_bf++;
                    int ok=1;for(int r=0;r<8;r++)if(fa[r]!=fb[r]){ok=0;break;}
                    if(ok){
                        n_coll_bf++;
                        /* Record de values at each round */
                        uint32_t sa[8],sb[8];
                        memcpy(sa,state1,32);memcpy(sb,state2,32);
                        sha_round(sa,KN[57],w57);sha_round(sb,KN[57],w57b);
                        valid_de[0][sa[4]^sb[4]]=1;
                        sha_round(sa,KN[58],w58);sha_round(sb,KN[58],w58b);
                        valid_de[1][sa[4]^sb[4]]=1;
                        sha_round(sa,KN[59],w59);sha_round(sb,KN[59],w59b);
                        valid_de[2][sa[4]^sb[4]]=1;
                        sha_round(sa,KN[60],w60);sha_round(sb,KN[60],w60b);
                        valid_de[3][sa[4]^sb[4]]=1;
                    }
                }
            }
        }
    }

    struct timespec t1;clock_gettime(CLOCK_MONOTONIC,&t1);
    double bf_time=(t1.tv_sec-t0.tv_sec)+(t1.tv_nsec-t0.tv_nsec)/1e9;

    int de_counts[4]={0,0,0,0};
    for(int r=0;r<4;r++)for(uint32_t v=0;v<=gMASK;v++)if(valid_de[r][v])de_counts[r]++;
    printf("  Collisions: %d (brute force: %llu evals, %.3fs)\n",n_coll_bf,(unsigned long long)n_eval_bf,bf_time);
    for(int r=0;r<4;r++)printf("  de%d: %d/%d (%.1f%%)\n",57+r,de_counts[r],1<<gN,100.0*de_counts[r]/(1<<gN));

    printf("\n=== Phase 2: de-pruned search ===\n");
    clock_gettime(CLOCK_MONOTONIC,&t0);

    int n_coll_pruned=0;
    uint64_t n_eval_pruned=0, n_skip[4]={0,0,0,0};

    for(uint32_t w57=0;w57<(1U<<gN);w57++){
        uint32_t s57a[8],s57b[8];memcpy(s57a,state1,32);memcpy(s57b,state2,32);
        uint32_t w57b=find_w2(s57a,s57b,57,w57);
        sha_round(s57a,KN[57],w57);sha_round(s57b,KN[57],w57b);
        uint32_t de57=s57a[4]^s57b[4];
        if(!valid_de[0][de57]){n_skip[0]+=(uint64_t)(1U<<gN)*(1U<<gN)*(1U<<gN);continue;}

        for(uint32_t w58=0;w58<(1U<<gN);w58++){
            uint32_t s58a[8],s58b[8];memcpy(s58a,s57a,32);memcpy(s58b,s57b,32);
            uint32_t w58b=find_w2(s58a,s58b,58,w58);
            sha_round(s58a,KN[58],w58);sha_round(s58b,KN[58],w58b);
            uint32_t de58=s58a[4]^s58b[4];
            if(!valid_de[1][de58]){n_skip[1]+=(uint64_t)(1U<<gN)*(1U<<gN);continue;}

            for(uint32_t w59=0;w59<(1U<<gN);w59++){
                uint32_t s59a[8],s59b[8];memcpy(s59a,s58a,32);memcpy(s59b,s58b,32);
                uint32_t w59b=find_w2(s59a,s59b,59,w59);
                sha_round(s59a,KN[59],w59);sha_round(s59b,KN[59],w59b);
                uint32_t de59=s59a[4]^s59b[4];
                if(!valid_de[2][de59]){n_skip[2]+=(uint64_t)(1U<<gN);continue;}

                for(uint32_t w60=0;w60<(1U<<gN);w60++){
                    uint32_t fa[8],fb[8];memcpy(fa,s59a,32);memcpy(fb,s59b,32);
                    uint32_t w60b=find_w2(fa,fb,60,w60);
                    sha_round(fa,KN[60],w60);sha_round(fb,KN[60],w60b);
                    uint32_t de60=fa[4]^fb[4];
                    if(!valid_de[3][de60]){n_skip[3]++;continue;}

                    /* Full collision check */
                    uint32_t W1[7]={w57,w58,w59,w60,0,0,0},W2[7]={w57b,w58b,w59b,w60b,0,0,0};
                    W1[4]=(fns1(W1[2])+W1pre[54]+fns0(W1pre[46])+W1pre[45])&gMASK;
                    W2[4]=(fns1(W2[2])+W2pre[54]+fns0(W2pre[46])+W2pre[45])&gMASK;
                    W1[5]=(fns1(W1[3])+W1pre[55]+fns0(W1pre[47])+W1pre[46])&gMASK;
                    W2[5]=(fns1(W2[3])+W2pre[55]+fns0(W2pre[47])+W2pre[46])&gMASK;
                    W1[6]=(fns1(W1[4])+W1pre[56]+fns0(W1pre[48])+W1pre[47])&gMASK;
                    W2[6]=(fns1(W2[4])+W2pre[56]+fns0(W2pre[48])+W2pre[47])&gMASK;
                    for(int r=4;r<7;r++){sha_round(fa,KN[57+r],W1[r]);sha_round(fb,KN[57+r],W2[r]);}
                    n_eval_pruned++;
                    int ok=1;for(int r=0;r<8;r++)if(fa[r]!=fb[r]){ok=0;break;}
                    if(ok)n_coll_pruned++;
                }
            }
        }
    }

    clock_gettime(CLOCK_MONOTONIC,&t1);
    double pr_time=(t1.tv_sec-t0.tv_sec)+(t1.tv_nsec-t0.tv_nsec)/1e9;

    printf("  Collisions: %d (pruned: %llu evals, %.3fs)\n",n_coll_pruned,(unsigned long long)n_eval_pruned,pr_time);
    printf("  Skipped at de57: %llu\n",(unsigned long long)n_skip[0]);
    printf("  Skipped at de58: %llu\n",(unsigned long long)n_skip[1]);
    printf("  Skipped at de59: %llu\n",(unsigned long long)n_skip[2]);
    printf("  Skipped at de60: %llu\n",(unsigned long long)n_skip[3]);

    printf("\n=== Comparison ===\n");
    printf("  Brute force: %llu evals in %.3fs\n",(unsigned long long)n_eval_bf,bf_time);
    printf("  de-pruned:   %llu evals in %.3fs\n",(unsigned long long)n_eval_pruned,pr_time);
    printf("  Speedup:     %.1fx fewer evals\n",(double)n_eval_bf/n_eval_pruned);
    printf("  Time speedup: %.1fx\n",bf_time/pr_time);
    printf("  Both found:  %d == %d collisions? %s\n",
           n_coll_bf,n_coll_pruned,n_coll_bf==n_coll_pruned?"YES":"NO");

    return 0;
}
