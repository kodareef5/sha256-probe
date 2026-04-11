/* Cascade-Optimized DP: search W1 only (W2 determined by cascade offsets)
 * Search space: 2^(4N) instead of 2^(8N). At N=4: 65536 candidates.
 * Compile: gcc -O3 -march=native -o cascade_dp_fast cascade_dp_fast.c -lm
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#include <math.h>

#define N 6
#define MASK ((1U << N) - 1)
#define MSB (1U << (N - 1))

static int r_Sig0[3],r_Sig1[3],r_sig0[2],r_sig1[2],s_sig0,s_sig1;
static inline uint32_t ror_n(uint32_t x,int k){k=k%N;return((x>>k)|(x<<(N-k)))&MASK;}
static inline uint32_t fn_S0(uint32_t a){return ror_n(a,r_Sig0[0])^ror_n(a,r_Sig0[1])^ror_n(a,r_Sig0[2]);}
static inline uint32_t fn_S1(uint32_t e){return ror_n(e,r_Sig1[0])^ror_n(e,r_Sig1[1])^ror_n(e,r_Sig1[2]);}
static inline uint32_t fn_s0(uint32_t x){return ror_n(x,r_sig0[0])^ror_n(x,r_sig0[1])^((x>>s_sig0)&MASK);}
static inline uint32_t fn_s1(uint32_t x){return ror_n(x,r_sig1[0])^ror_n(x,r_sig1[1])^((x>>s_sig1)&MASK);}
static inline uint32_t fn_Ch(uint32_t e,uint32_t f,uint32_t g){return((e&f)^((~e)&g))&MASK;}
static inline uint32_t fn_Maj(uint32_t a,uint32_t b,uint32_t c){return((a&b)^(a&c)^(b&c))&MASK;}

static const uint32_t K32[64]={0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
static const uint32_t IV32[8]={0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};
static uint32_t KN[64],IVN[8],state1[8],state2[8],W1_pre[57],W2_pre[57];

static int scale_rot(int k32){int r=(int)rint((double)k32*N/32.0);return r<1?1:r;}
static void precompute(const uint32_t M[16],uint32_t st[8],uint32_t W[57]){
    for(int i=0;i<16;i++)W[i]=M[i]&MASK;
    for(int i=16;i<57;i++)W[i]=(fn_s1(W[i-2])+W[i-7]+fn_s0(W[i-15])+W[i-16])&MASK;
    uint32_t a=IVN[0],b=IVN[1],c=IVN[2],d=IVN[3],e=IVN[4],f=IVN[5],g=IVN[6],h=IVN[7];
    for(int i=0;i<57;i++){uint32_t T1=(h+fn_S1(e)+fn_Ch(e,f,g)+KN[i]+W[i])&MASK,T2=(fn_S0(a)+fn_Maj(a,b,c))&MASK;h=g;g=f;f=e;e=(d+T1)&MASK;d=c;c=b;b=a;a=(T1+T2)&MASK;}
    st[0]=a;st[1]=b;st[2]=c;st[3]=d;st[4]=e;st[5]=f;st[6]=g;st[7]=h;
}

static inline void sha_round(uint32_t s[8],uint32_t k,uint32_t w){
    uint32_t T1=(s[7]+fn_S1(s[4])+fn_Ch(s[4],s[5],s[6])+k+w)&MASK;
    uint32_t T2=(fn_S0(s[0])+fn_Maj(s[0],s[1],s[2]))&MASK;
    s[7]=s[6];s[6]=s[5];s[5]=s[4];s[4]=(s[3]+T1)&MASK;s[3]=s[2];s[2]=s[1];s[1]=s[0];s[0]=(T1+T2)&MASK;
}

/* Compute the cascade offset: given state57 for both msgs, find the unique
   W2[k] that makes da_{57+k}=0 given W1[k] */
static uint32_t find_w2_offset(uint32_t s1[8],uint32_t s2[8],uint32_t round,uint32_t w1_k){
    /* a_{r+1} = T1+T2. For da=0: T1_1+T2_1 = T1_2+T2_2.
       T1 = h+Sig1(e)+Ch(e,f,g)+K+W. T2 = Sig0(a)+Maj(a,b,c).
       da=0 ⟹ W2 = W1 + (T2_1-T2_2) - (rest_1-rest_2) where rest excludes W */
    uint32_t rest1 = (s1[7]+fn_S1(s1[4])+fn_Ch(s1[4],s1[5],s1[6])+KN[round])&MASK;
    uint32_t rest2 = (s2[7]+fn_S1(s2[4])+fn_Ch(s2[4],s2[5],s2[6])+KN[round])&MASK;
    uint32_t T2_1 = (fn_S0(s1[0])+fn_Maj(s1[0],s1[1],s1[2]))&MASK;
    uint32_t T2_2 = (fn_S0(s2[0])+fn_Maj(s2[0],s2[1],s2[2]))&MASK;
    /* For T1_1+T2_1 = T1_2+T2_2:
       (rest1+W1)+T2_1 = (rest2+W2)+T2_2
       W2 = W1 + rest1-rest2 + T2_1-T2_2 */
    return (w1_k + rest1 - rest2 + T2_1 - T2_2) & MASK;
}

int main(){
    setbuf(stdout,NULL);
    r_Sig0[0]=scale_rot(2);r_Sig0[1]=scale_rot(13);r_Sig0[2]=scale_rot(22);
    r_Sig1[0]=scale_rot(6);r_Sig1[1]=scale_rot(11);r_Sig1[2]=scale_rot(25);
    r_sig0[0]=scale_rot(7);r_sig0[1]=scale_rot(18);s_sig0=scale_rot(3);
    r_sig1[0]=scale_rot(17);r_sig1[1]=scale_rot(19);s_sig1=scale_rot(10);
    for(int i=0;i<64;i++)KN[i]=K32[i]&MASK;
    for(int i=0;i<8;i++)IVN[i]=IV32[i]&MASK;

    int found=0;
    for(uint32_t m0=0;m0<=MASK&&!found;m0++){
        uint32_t M1[16],M2[16];
        for(int i=0;i<16;i++){M1[i]=0;M2[i]=0;}
        M1[0]=m0;M2[0]=m0^MSB;M2[9]=0^MSB;
        precompute(M1,state1,W1_pre);precompute(M2,state2,W2_pre);
        if(state1[0]==state2[0]){printf("Candidate: M[0]=0x%x\n",m0);found=1;}
    }

    printf("Cascade-Optimized DP at N=%d\n",N);
    printf("Search W1 only — W2 determined by cascade offsets\n");
    printf("Search space: 2^%d = %llu (vs brute force 2^%d = %llu)\n\n",
           4*N,(unsigned long long)(1ULL<<(4*N)),8*N,(unsigned long long)(1ULL<<(8*N)));

    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0);
    uint64_t n_tested=0, n_collisions=0;

    for(uint32_t w1_57=0; w1_57<(1U<<N); w1_57++){
        uint32_t s1_57[8],s2_57[8];
        memcpy(s1_57,state1,32);memcpy(s2_57,state2,32);
        uint32_t w2_57=find_w2_offset(s1_57,s2_57,57,w1_57);
        sha_round(s1_57,KN[57],w1_57);sha_round(s2_57,KN[57],w2_57);

        for(uint32_t w1_58=0; w1_58<(1U<<N); w1_58++){
            uint32_t s1_58[8],s2_58[8];
            memcpy(s1_58,s1_57,32);memcpy(s2_58,s2_57,32);
            uint32_t w2_58=find_w2_offset(s1_58,s2_58,58,w1_58);
            sha_round(s1_58,KN[58],w1_58);sha_round(s2_58,KN[58],w2_58);

            for(uint32_t w1_59=0; w1_59<(1U<<N); w1_59++){
                uint32_t s1_59[8],s2_59[8];
                memcpy(s1_59,s1_58,32);memcpy(s2_59,s2_58,32);
                uint32_t w2_59=find_w2_offset(s1_59,s2_59,59,w1_59);
                sha_round(s1_59,KN[59],w1_59);sha_round(s2_59,KN[59],w2_59);

                for(uint32_t w1_60=0; w1_60<(1U<<N); w1_60++){
                    uint32_t s1_60[8],s2_60[8];
                    memcpy(s1_60,s1_59,32);memcpy(s2_60,s2_59,32);
                    uint32_t w2_60=find_w2_offset(s1_60,s2_60,60,w1_60);
                    sha_round(s1_60,KN[60],w1_60);sha_round(s2_60,KN[60],w2_60);

                    /* Schedule-determined rounds 61-63 */
                    uint32_t W1f[7]={w1_57,w1_58,w1_59,w1_60,0,0,0};
                    uint32_t W2f[7]={w2_57,w2_58,w2_59,w2_60,0,0,0};
                    W1f[4]=(fn_s1(W1f[2])+W1_pre[54]+fn_s0(W1_pre[46])+W1_pre[45])&MASK;
                    W2f[4]=(fn_s1(W2f[2])+W2_pre[54]+fn_s0(W2_pre[46])+W2_pre[45])&MASK;
                    W1f[5]=(fn_s1(W1f[3])+W1_pre[55]+fn_s0(W1_pre[47])+W1_pre[46])&MASK;
                    W2f[5]=(fn_s1(W2f[3])+W2_pre[55]+fn_s0(W2_pre[47])+W2_pre[46])&MASK;
                    W1f[6]=(fn_s1(W1f[4])+W1_pre[56]+fn_s0(W1_pre[48])+W1_pre[47])&MASK;
                    W2f[6]=(fn_s1(W2f[4])+W2_pre[56]+fn_s0(W2_pre[48])+W2_pre[47])&MASK;

                    uint32_t fs1[8],fs2[8];
                    memcpy(fs1,s1_60,32);memcpy(fs2,s2_60,32);
                    for(int r=4;r<7;r++){sha_round(fs1,KN[57+r],W1f[r]);sha_round(fs2,KN[57+r],W2f[r]);}

                    n_tested++;
                    int ok=1;
                    for(int r=0;r<8;r++) if(fs1[r]!=fs2[r]){ok=0;break;}
                    if(ok){
                        n_collisions++;
                        if(n_collisions<=5)
                            printf("  #%llu: W1=[%x,%x,%x,%x] W2=[%x,%x,%x,%x]\n",
                                   (unsigned long long)n_collisions,
                                   w1_57,w1_58,w1_59,w1_60,w2_57,w2_58,w2_59,w2_60);
                    }
                }
            }
        }
    }

    clock_gettime(CLOCK_MONOTONIC,&t1);
    double elapsed=(t1.tv_sec-t0.tv_sec)+(t1.tv_nsec-t0.tv_nsec)/1e9;
    printf("\n=== Results ===\n");
    printf("Tested: %llu (out of 2^%d = %llu)\n",(unsigned long long)n_tested,4*N,(unsigned long long)(1ULL<<(4*N)));
    printf("Collisions: %llu\n",(unsigned long long)n_collisions);
    printf("Time: %.6f seconds\n",elapsed);
    printf("Speedup vs brute force (157s): %.0fx\n",157.0/elapsed);
    if(n_collisions==49) printf("\n*** ALL 49 COLLISIONS FOUND ***\n");
    printf("Done.\n");
    return 0;
}
