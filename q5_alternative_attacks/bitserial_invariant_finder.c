/*
 * Bitserial Invariant-Pruned Collision Finder
 *
 * Uses carry-diff invariants to prune the cascade DP search.
 * At each bit position k: enumerate message-bit-k choices,
 * compute carries, check invariant carry-diffs, prune.
 *
 * If invariant pruning keeps width bounded by #collisions,
 * total work is O(N × #solutions × branching_factor).
 *
 * Proof of concept at N=4 (should find 49 collisions).
 *
 * Compile: gcc -O3 -march=native -o /tmp/bsif bitserial_invariant_finder.c -lm
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#include <math.h>

#define N 4
#define MASK ((1U<<N)-1)
#define MSB (1U<<(N-1))
#define MAX_STATES 100000

/* SHA-256 mini functions */
static int rS0[3],rS1[3],rs0[2],rs1[2],ss0,ss1;
static inline uint32_t ror_n(uint32_t x,int k){k=k%N;return((x>>k)|(x<<(N-k)))&MASK;}
static inline uint32_t fn_S0(uint32_t a){return ror_n(a,rS0[0])^ror_n(a,rS0[1])^ror_n(a,rS0[2]);}
static inline uint32_t fn_S1(uint32_t e){return ror_n(e,rS1[0])^ror_n(e,rS1[1])^ror_n(e,rS1[2]);}
static inline uint32_t fn_Ch(uint32_t e,uint32_t f,uint32_t g){return((e&f)^((~e)&g))&MASK;}
static inline uint32_t fn_Maj(uint32_t a,uint32_t b,uint32_t c){return((a&b)^(a&c)^(b&c))&MASK;}
static inline uint32_t fn_s0(uint32_t x){return ror_n(x,rs0[0])^ror_n(x,rs0[1])^((x>>ss0)&MASK);}
static inline uint32_t fn_s1(uint32_t x){return ror_n(x,rs1[0])^ror_n(x,rs1[1])^((x>>ss1)&MASK);}
static const uint32_t K32[64]={0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
static const uint32_t IV32[8]={0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};
static uint32_t KN[64],IVN[8],state1[8],state2[8],W1_pre[57],W2_pre[57];
static int scale_rot(int k){int r=(int)rint((double)k*N/32.0);return r<1?1:r;}

static void precompute(const uint32_t M[16],uint32_t st[8],uint32_t W[57]){
    for(int i=0;i<16;i++)W[i]=M[i]&MASK;
    for(int i=16;i<57;i++)W[i]=(fn_s1(W[i-2])+W[i-7]+fn_s0(W[i-15])+W[i-16])&MASK;
    uint32_t a=IVN[0],b=IVN[1],c=IVN[2],d=IVN[3],e=IVN[4],f=IVN[5],g=IVN[6],h=IVN[7];
    for(int i=0;i<57;i++){uint32_t T1=(h+fn_S1(e)+fn_Ch(e,f,g)+KN[i]+W[i])&MASK,T2=(fn_S0(a)+fn_Maj(a,b,c))&MASK;h=g;g=f;f=e;e=(d+T1)&MASK;d=c;c=b;b=a;a=(T1+T2)&MASK;}
    st[0]=a;st[1]=b;st[2]=c;st[3]=d;st[4]=e;st[5]=f;st[6]=g;st[7]=h;
}

/*
 * State for the bitserial search:
 * - Partial message words W1[57..60] (bits 0..k assigned)
 * - Round-by-round state registers for M1 and M2 after processing bits 0..k
 *
 * For the proof-of-concept: just do the cascade DP normally but check
 * how many states survive at each bit position of W1[57].
 *
 * The REAL bitserial approach processes one BIT at a time across ALL words
 * and rounds. That requires restructuring the round function to work
 * bit-serially (process bit k of all additions before bit k+1).
 *
 * For now: validate the PRUNING POWER by checking how many W1[57] values
 * survive after checking each bit.
 */

int main(){
    setbuf(stdout,NULL);
    rS0[0]=scale_rot(2);rS0[1]=scale_rot(13);rS0[2]=scale_rot(22);
    rS1[0]=scale_rot(6);rS1[1]=scale_rot(11);rS1[2]=scale_rot(25);
    rs0[0]=scale_rot(7);rs0[1]=scale_rot(18);ss0=scale_rot(3);
    rs1[0]=scale_rot(17);rs1[1]=scale_rot(19);ss1=scale_rot(10);
    for(int i=0;i<64;i++)KN[i]=K32[i]&MASK;
    for(int i=0;i<8;i++)IVN[i]=IV32[i]&MASK;

    /* Find candidate */
    int found=0;
    for(uint32_t m0=0;m0<=MASK&&!found;m0++){
        uint32_t M1[16],M2[16];
        for(int i=0;i<16;i++){M1[i]=MASK;M2[i]=MASK;}
        M1[0]=m0;M2[0]=m0^MSB;M2[9]=MASK^MSB;
        precompute(M1,state1,W1_pre);precompute(M2,state2,W2_pre);
        if(state1[0]==state2[0]){printf("M[0]=0x%x\n",m0);found=1;}
    }

    printf("Bitserial Invariant-Pruned Finder at N=%d\n\n",N);

    /* Phase 1: Do the cascade DP and measure width at each W1[57] bit */
    printf("Phase 1: Cascade DP with per-bit width measurement\n");

    /* For each bit position of W1[57], count how many values lead to
       at least one collision when combined with optimal W1[58..60] */

    int total_collisions = 0;
    int w57_productive[1<<N];
    memset(w57_productive, 0, sizeof(w57_productive));

    /* Full cascade DP */
    for(uint32_t w57=0;w57<(1U<<N);w57++){
        uint32_t s1_57[8],s2_57[8];
        memcpy(s1_57,state1,32);memcpy(s2_57,state2,32);
        /* Cascade W2[57] */
        uint32_t rest1=(s1_57[7]+fn_S1(s1_57[4])+fn_Ch(s1_57[4],s1_57[5],s1_57[6])+KN[57])&MASK;
        uint32_t rest2=(s2_57[7]+fn_S1(s2_57[4])+fn_Ch(s2_57[4],s2_57[5],s2_57[6])+KN[57])&MASK;
        uint32_t T2_1=(fn_S0(s1_57[0])+fn_Maj(s1_57[0],s1_57[1],s1_57[2]))&MASK;
        uint32_t T2_2=(fn_S0(s2_57[0])+fn_Maj(s2_57[0],s2_57[1],s2_57[2]))&MASK;
        uint32_t w2_57=(w57+rest1-rest2+T2_1-T2_2)&MASK;

        /* Advance state */
        {uint32_t T1a=(s1_57[7]+fn_S1(s1_57[4])+fn_Ch(s1_57[4],s1_57[5],s1_57[6])+KN[57]+w57)&MASK;
        uint32_t T2a=(fn_S0(s1_57[0])+fn_Maj(s1_57[0],s1_57[1],s1_57[2]))&MASK;
        s1_57[7]=s1_57[6];s1_57[6]=s1_57[5];s1_57[5]=s1_57[4];s1_57[4]=(s1_57[3]+T1a)&MASK;s1_57[3]=s1_57[2];s1_57[2]=s1_57[1];s1_57[1]=s1_57[0];s1_57[0]=(T1a+T2a)&MASK;}
        {uint32_t T1b=(s2_57[7]+fn_S1(s2_57[4])+fn_Ch(s2_57[4],s2_57[5],s2_57[6])+KN[57]+w2_57)&MASK;
        uint32_t T2b=(fn_S0(s2_57[0])+fn_Maj(s2_57[0],s2_57[1],s2_57[2]))&MASK;
        s2_57[7]=s2_57[6];s2_57[6]=s2_57[5];s2_57[5]=s2_57[4];s2_57[4]=(s2_57[3]+T1b)&MASK;s2_57[3]=s2_57[2];s2_57[2]=s2_57[1];s2_57[1]=s2_57[0];s2_57[0]=(T1b+T2b)&MASK;}

        for(uint32_t w58=0;w58<(1U<<N);w58++){
            uint32_t s1_58[8],s2_58[8];
            memcpy(s1_58,s1_57,32);memcpy(s2_58,s2_57,32);
            uint32_t r1=(s1_58[7]+fn_S1(s1_58[4])+fn_Ch(s1_58[4],s1_58[5],s1_58[6])+KN[58])&MASK;
            uint32_t r2=(s2_58[7]+fn_S1(s2_58[4])+fn_Ch(s2_58[4],s2_58[5],s2_58[6])+KN[58])&MASK;
            uint32_t t1=(fn_S0(s1_58[0])+fn_Maj(s1_58[0],s1_58[1],s1_58[2]))&MASK;
            uint32_t t2=(fn_S0(s2_58[0])+fn_Maj(s2_58[0],s2_58[1],s2_58[2]))&MASK;
            uint32_t w2_58=(w58+r1-r2+t1-t2)&MASK;

            {uint32_t T1=(s1_58[7]+fn_S1(s1_58[4])+fn_Ch(s1_58[4],s1_58[5],s1_58[6])+KN[58]+w58)&MASK;uint32_t T2=(fn_S0(s1_58[0])+fn_Maj(s1_58[0],s1_58[1],s1_58[2]))&MASK;s1_58[7]=s1_58[6];s1_58[6]=s1_58[5];s1_58[5]=s1_58[4];s1_58[4]=(s1_58[3]+T1)&MASK;s1_58[3]=s1_58[2];s1_58[2]=s1_58[1];s1_58[1]=s1_58[0];s1_58[0]=(T1+T2)&MASK;}
            {uint32_t T1=(s2_58[7]+fn_S1(s2_58[4])+fn_Ch(s2_58[4],s2_58[5],s2_58[6])+KN[58]+w2_58)&MASK;uint32_t T2=(fn_S0(s2_58[0])+fn_Maj(s2_58[0],s2_58[1],s2_58[2]))&MASK;s2_58[7]=s2_58[6];s2_58[6]=s2_58[5];s2_58[5]=s2_58[4];s2_58[4]=(s2_58[3]+T1)&MASK;s2_58[3]=s2_58[2];s2_58[2]=s2_58[1];s2_58[1]=s2_58[0];s2_58[0]=(T1+T2)&MASK;}

            for(uint32_t w59=0;w59<(1U<<N);w59++){
                uint32_t s1_59[8],s2_59[8];
                memcpy(s1_59,s1_58,32);memcpy(s2_59,s2_58,32);
                r1=(s1_59[7]+fn_S1(s1_59[4])+fn_Ch(s1_59[4],s1_59[5],s1_59[6])+KN[59])&MASK;
                r2=(s2_59[7]+fn_S1(s2_59[4])+fn_Ch(s2_59[4],s2_59[5],s2_59[6])+KN[59])&MASK;
                t1=(fn_S0(s1_59[0])+fn_Maj(s1_59[0],s1_59[1],s1_59[2]))&MASK;
                t2=(fn_S0(s2_59[0])+fn_Maj(s2_59[0],s2_59[1],s2_59[2]))&MASK;
                uint32_t w2_59=(w59+r1-r2+t1-t2)&MASK;

                {uint32_t T1=(s1_59[7]+fn_S1(s1_59[4])+fn_Ch(s1_59[4],s1_59[5],s1_59[6])+KN[59]+w59)&MASK;uint32_t T2=(fn_S0(s1_59[0])+fn_Maj(s1_59[0],s1_59[1],s1_59[2]))&MASK;s1_59[7]=s1_59[6];s1_59[6]=s1_59[5];s1_59[5]=s1_59[4];s1_59[4]=(s1_59[3]+T1)&MASK;s1_59[3]=s1_59[2];s1_59[2]=s1_59[1];s1_59[1]=s1_59[0];s1_59[0]=(T1+T2)&MASK;}
                {uint32_t T1=(s2_59[7]+fn_S1(s2_59[4])+fn_Ch(s2_59[4],s2_59[5],s2_59[6])+KN[59]+w2_59)&MASK;uint32_t T2=(fn_S0(s2_59[0])+fn_Maj(s2_59[0],s2_59[1],s2_59[2]))&MASK;s2_59[7]=s2_59[6];s2_59[6]=s2_59[5];s2_59[5]=s2_59[4];s2_59[4]=(s2_59[3]+T1)&MASK;s2_59[3]=s2_59[2];s2_59[2]=s2_59[1];s2_59[1]=s2_59[0];s2_59[0]=(T1+T2)&MASK;}

                for(uint32_t w60=0;w60<(1U<<N);w60++){
                    uint32_t s1_60[8],s2_60[8];
                    memcpy(s1_60,s1_59,32);memcpy(s2_60,s2_59,32);
                    r1=(s1_60[7]+fn_S1(s1_60[4])+fn_Ch(s1_60[4],s1_60[5],s1_60[6])+KN[60])&MASK;
                    r2=(s2_60[7]+fn_S1(s2_60[4])+fn_Ch(s2_60[4],s2_60[5],s2_60[6])+KN[60])&MASK;
                    t1=(fn_S0(s1_60[0])+fn_Maj(s1_60[0],s1_60[1],s1_60[2]))&MASK;
                    t2=(fn_S0(s2_60[0])+fn_Maj(s2_60[0],s2_60[1],s2_60[2]))&MASK;
                    uint32_t w2_60=(w60+r1-r2+t1-t2)&MASK;

                    {uint32_t T1=(s1_60[7]+fn_S1(s1_60[4])+fn_Ch(s1_60[4],s1_60[5],s1_60[6])+KN[60]+w60)&MASK;uint32_t T2=(fn_S0(s1_60[0])+fn_Maj(s1_60[0],s1_60[1],s1_60[2]))&MASK;s1_60[7]=s1_60[6];s1_60[6]=s1_60[5];s1_60[5]=s1_60[4];s1_60[4]=(s1_60[3]+T1)&MASK;s1_60[3]=s1_60[2];s1_60[2]=s1_60[1];s1_60[1]=s1_60[0];s1_60[0]=(T1+T2)&MASK;}
                    {uint32_t T1=(s2_60[7]+fn_S1(s2_60[4])+fn_Ch(s2_60[4],s2_60[5],s2_60[6])+KN[60]+w2_60)&MASK;uint32_t T2=(fn_S0(s2_60[0])+fn_Maj(s2_60[0],s2_60[1],s2_60[2]))&MASK;s2_60[7]=s2_60[6];s2_60[6]=s2_60[5];s2_60[5]=s2_60[4];s2_60[4]=(s2_60[3]+T1)&MASK;s2_60[3]=s2_60[2];s2_60[2]=s2_60[1];s2_60[1]=s2_60[0];s2_60[0]=(T1+T2)&MASK;}

                    /* Schedule + rounds 61-63 */
                    uint32_t W1f[7]={w57,w58,w59,w60,0,0,0},W2f[7]={w2_57,w2_58,w2_59,w2_60,0,0,0};
                    W1f[4]=(fn_s1(W1f[2])+W1_pre[54]+fn_s0(W1_pre[46])+W1_pre[45])&MASK;
                    W2f[4]=(fn_s1(W2f[2])+W2_pre[54]+fn_s0(W2_pre[46])+W2_pre[45])&MASK;
                    W1f[5]=(fn_s1(W1f[3])+W1_pre[55]+fn_s0(W1_pre[47])+W1_pre[46])&MASK;
                    W2f[5]=(fn_s1(W2f[3])+W2_pre[55]+fn_s0(W2_pre[47])+W2_pre[46])&MASK;
                    W1f[6]=(fn_s1(W1f[4])+W1_pre[56]+fn_s0(W1_pre[48])+W1_pre[47])&MASK;
                    W2f[6]=(fn_s1(W2f[4])+W2_pre[56]+fn_s0(W2_pre[48])+W2_pre[47])&MASK;
                    uint32_t fs1[8],fs2[8];
                    memcpy(fs1,s1_60,32);memcpy(fs2,s2_60,32);
                    for(int r=4;r<7;r++){
                        uint32_t T1=(fs1[7]+fn_S1(fs1[4])+fn_Ch(fs1[4],fs1[5],fs1[6])+KN[57+r]+W1f[r])&MASK;
                        uint32_t T2=(fn_S0(fs1[0])+fn_Maj(fs1[0],fs1[1],fs1[2]))&MASK;
                        fs1[7]=fs1[6];fs1[6]=fs1[5];fs1[5]=fs1[4];fs1[4]=(fs1[3]+T1)&MASK;fs1[3]=fs1[2];fs1[2]=fs1[1];fs1[1]=fs1[0];fs1[0]=(T1+T2)&MASK;
                        T1=(fs2[7]+fn_S1(fs2[4])+fn_Ch(fs2[4],fs2[5],fs2[6])+KN[57+r]+W2f[r])&MASK;
                        T2=(fn_S0(fs2[0])+fn_Maj(fs2[0],fs2[1],fs2[2]))&MASK;
                        fs2[7]=fs2[6];fs2[6]=fs2[5];fs2[5]=fs2[4];fs2[4]=(fs2[3]+T1)&MASK;fs2[3]=fs2[2];fs2[2]=fs2[1];fs2[1]=fs2[0];fs2[0]=(T1+T2)&MASK;
                    }
                    int ok=1;
                    for(int r=0;r<8;r++) if(fs1[r]!=fs2[r]){ok=0;break;}
                    if(ok){
                        total_collisions++;
                        w57_productive[w57]++;
                    }
                }
            }
        }
    }

    printf("Total collisions: %d\n\n",total_collisions);

    /* Width analysis: how many W1[57] values produce collisions? */
    printf("Width analysis (W1[57] productivity):\n");
    int productive_count=0;
    for(int w=0;w<(1<<N);w++){
        if(w57_productive[w]>0){
            productive_count++;
            printf("  W1[57]=0x%x: %d collisions\n",w,w57_productive[w]);
        }
    }
    printf("\nProductive W1[57] values: %d/%d\n",productive_count,1<<N);
    printf("Width at W1[57] level: %d (vs %d search space)\n",productive_count,1<<N);
    printf("Pruning at W1[57]: %.1fx\n",(double)(1<<N)/productive_count);

    /* Per-bit width: how many distinct bit-k prefixes of W1[57] are productive? */
    printf("\nPer-bit prefix width of W1[57]:\n");
    for(int k=0;k<N;k++){
        int prefix_count=0;
        int prefix_mask=(1<<(k+1))-1;
        int seen[1<<N];
        memset(seen,0,sizeof(seen));
        for(int w=0;w<(1<<N);w++){
            if(w57_productive[w]>0){
                int prefix=w&prefix_mask;
                if(!seen[prefix]){seen[prefix]=1;prefix_count++;}
            }
        }
        printf("  After bit %d: %d/%d distinct productive prefixes (%.1fx pruning)\n",
               k, prefix_count, 1<<(k+1), (double)(1<<(k+1))/prefix_count);
    }

    printf("\nDone.\n");
    return 0;
}
