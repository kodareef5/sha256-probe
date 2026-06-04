/*
 * coincidence_scan.c — scan candidates x kernels for the g1 _|_ h independence ratio.
 *
 * For each (M0, kernel-bit), exhaustively enumerate cascade-DP sr=60 collisions at
 * width N and measure, over the de61=0 hits, the independence ratio
 *   R = P(g1=0 & h=0) / [P(g1=0) * P(h=0)].
 * R~1  => g1 _|_ h  => sr=61 rate = 2^-2N (universal wall).
 * R>>1 (toward 1/P) => g1=0 IMPLIES h=0 => sr=61 reverts to 2^-N for that candidate
 *        (a reachability lead worth chasing).
 * Also reports sr=61 (both g1=g2=0) count.
 *
 * Compile: gcc -O3 -march=native -Xclang -fopenmp \
 *   -I/opt/homebrew/opt/libomp/include -L/opt/homebrew/opt/libomp/lib -lomp \
 *   -DN=8 -o coincidence_scan coincidence_scan.c -lm
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <omp.h>

#ifndef N
#define N 8
#endif
#define MASK ((1U<<N)-1)

static int rS0[3],rS1[3],rs0[2],rs1[2],ss0,ss1;
static int scale_rot(int k){int r=(int)rint((double)k*N/32.0);return r<1?1:r;}
static inline uint32_t ror_n(uint32_t x,int k){k%=N;return ((x>>k)|(x<<(N-k)))&MASK;}
static inline uint32_t fnS0(uint32_t a){return ror_n(a,rS0[0])^ror_n(a,rS0[1])^ror_n(a,rS0[2]);}
static inline uint32_t fnS1(uint32_t e){return ror_n(e,rS1[0])^ror_n(e,rS1[1])^ror_n(e,rS1[2]);}
static inline uint32_t fns0(uint32_t x){return ror_n(x,rs0[0])^ror_n(x,rs0[1])^((x>>ss0)&MASK);}
static inline uint32_t fns1(uint32_t x){return ror_n(x,rs1[0])^ror_n(x,rs1[1])^((x>>ss1)&MASK);}
static inline uint32_t fnCh(uint32_t e,uint32_t f,uint32_t g){return ((e&f)^((~e)&g))&MASK;}
static inline uint32_t fnMj(uint32_t a,uint32_t b,uint32_t c){return ((a&b)^(a&c)^(b&c))&MASK;}
static const uint32_t K32[64]={
0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
static const uint32_t IV32[8]={0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};
static uint32_t KN[64],IVN[8];
/* per-candidate globals (set before each parallel enumeration) */
static uint32_t g_state1[8],g_state2[8],g_W1p[57],g_W2p[57];

static void precompute(const uint32_t M[16],uint32_t st[8],uint32_t W[57]){
    for(int i=0;i<16;i++)W[i]=M[i]&MASK;
    for(int i=16;i<57;i++)W[i]=(fns1(W[i-2])+W[i-7]+fns0(W[i-15])+W[i-16])&MASK;
    uint32_t a=IVN[0],b=IVN[1],c=IVN[2],d=IVN[3],e=IVN[4],f=IVN[5],g=IVN[6],h=IVN[7];
    for(int i=0;i<57;i++){uint32_t T1=(h+fnS1(e)+fnCh(e,f,g)+KN[i]+W[i])&MASK,T2=(fnS0(a)+fnMj(a,b,c))&MASK;
        h=g;g=f;f=e;e=(d+T1)&MASK;d=c;c=b;b=a;a=(T1+T2)&MASK;}
    st[0]=a;st[1]=b;st[2]=c;st[3]=d;st[4]=e;st[5]=f;st[6]=g;st[7]=h;
}
static inline void sha_round(uint32_t s[8],uint32_t k,uint32_t w){
    uint32_t T1=(s[7]+fnS1(s[4])+fnCh(s[4],s[5],s[6])+k+w)&MASK,T2=(fnS0(s[0])+fnMj(s[0],s[1],s[2]))&MASK;
    s[7]=s[6];s[6]=s[5];s[5]=s[4];s[4]=(s[3]+T1)&MASK;s[3]=s[2];s[2]=s[1];s[1]=s[0];s[0]=(T1+T2)&MASK;}
static inline uint32_t find_w2(const uint32_t s1[8],const uint32_t s2[8],int rnd,uint32_t w1){
    uint32_t r1=(s1[7]+fnS1(s1[4])+fnCh(s1[4],s1[5],s1[6])+KN[rnd])&MASK;
    uint32_t r2=(s2[7]+fnS1(s2[4])+fnCh(s2[4],s2[5],s2[6])+KN[rnd])&MASK;
    uint32_t T21=(fnS0(s1[0])+fnMj(s1[0],s1[1],s1[2]))&MASK,T22=(fnS0(s2[0])+fnMj(s2[0],s2[1],s2[2]))&MASK;
    return (w1+r1-r2+T21-T22)&MASK;}

/* Returns 1 if cascade-eligible (da56=0); fills out-metrics. */
static int analyze(uint32_t M0,int kbit,uint64_t *o_nde61,uint64_t *o_ncoll,
                   uint64_t *o_ng1,uint64_t *o_nh,uint64_t *o_nboth,uint64_t *o_sr61){
    uint32_t M1[16],M2[16];
    for(int i=0;i<16;i++){M1[i]=MASK;M2[i]=MASK;}
    M1[0]=M0&MASK; M2[0]=(M0^(1U<<kbit))&MASK; M2[9]=(MASK^(1U<<kbit))&MASK;
    precompute(M1,g_state1,g_W1p); precompute(M2,g_state2,g_W2p);
    if(g_state1[0]!=g_state2[0]) return 0;  /* not cascade-eligible */

    uint64_t nde61=0,ncoll=0,ng1=0,nh=0,nboth=0,sr61=0;
    #pragma omp parallel reduction(+:nde61,ncoll,ng1,nh,nboth,sr61)
    {
      #pragma omp for schedule(dynamic,1)
      for(uint32_t w57=0;w57<(MASK+1U);w57++){
        uint32_t s57a[8],s57b[8];memcpy(s57a,g_state1,32);memcpy(s57b,g_state2,32);
        uint32_t w57b=find_w2(s57a,s57b,57,w57);sha_round(s57a,KN[57],w57);sha_round(s57b,KN[57],w57b);
        for(uint32_t w58=0;w58<(MASK+1U);w58++){
          uint32_t s58a[8],s58b[8];memcpy(s58a,s57a,32);memcpy(s58b,s57b,32);
          uint32_t w58b=find_w2(s58a,s58b,58,w58);sha_round(s58a,KN[58],w58);sha_round(s58b,KN[58],w58b);
          for(uint32_t w59=0;w59<(MASK+1U);w59++){
            uint32_t s59a[8],s59b[8];memcpy(s59a,s58a,32);memcpy(s59b,s58b,32);
            uint32_t w59b=find_w2(s59a,s59b,59,w59);sha_round(s59a,KN[59],w59);sha_round(s59b,KN[59],w59b);
            uint32_t casoff=find_w2(s59a,s59b,60,0);
            uint32_t sd1=(fns1(w58)+g_W1p[53]+fns0(g_W1p[45])+g_W1p[44])&MASK;
            uint32_t sd2=(fns1(w58b)+g_W2p[53]+fns0(g_W2p[45])+g_W2p[44])&MASK;
            uint32_t hh=(casoff-((sd2-sd1)&MASK))&MASK;
            uint32_t W1_61=(fns1(w59)+g_W1p[54]+fns0(g_W1p[46])+g_W1p[45])&MASK;
            uint32_t W2_61=(fns1(w59b)+g_W2p[54]+fns0(g_W2p[46])+g_W2p[45])&MASK;
            uint32_t W1_63=(fns1(W1_61)+g_W1p[56]+fns0(g_W1p[48])+g_W1p[47])&MASK;
            uint32_t W2_63=(fns1(W2_61)+g_W2p[56]+fns0(g_W2p[48])+g_W2p[47])&MASK;
            uint32_t sc62_1=(g_W1p[55]+fns0(g_W1p[47])+g_W1p[46])&MASK;
            uint32_t sc62_2=(g_W2p[55]+fns0(g_W2p[47])+g_W2p[46])&MASK;
            for(uint32_t w60=0;w60<(MASK+1U);w60++){
              uint32_t w60b=(w60+casoff)&MASK;
              uint32_t a[8],b[8];memcpy(a,s59a,32);memcpy(b,s59b,32);
              sha_round(a,KN[60],w60);sha_round(b,KN[60],w60b);
              uint32_t a1[8],b1[8];memcpy(a1,a,32);memcpy(b1,b,32);
              sha_round(a1,KN[61],W1_61);sha_round(b1,KN[61],W2_61);
              if(((a1[4]-b1[4])&MASK)!=0)continue;
              nde61++;
              uint32_t g1=(w60-sd1)&MASK;
              if(g1==0)ng1++; if(hh==0)nh++; if(g1==0&&hh==0)nboth++;
              uint32_t W1_62=(fns1(w60)+sc62_1)&MASK,W2_62=(fns1(w60b)+sc62_2)&MASK;
              sha_round(a1,KN[62],W1_62);sha_round(b1,KN[62],W2_62);
              sha_round(a1,KN[63],W1_63);sha_round(b1,KN[63],W2_63);
              int ok=1;for(int r=0;r<8;r++)if(a1[r]!=b1[r]){ok=0;break;}
              if(ok){ncoll++; uint32_t g2=(w60b-sd2)&MASK; if(g1==0&&g2==0)sr61++;}
            }
          }
        }
      }
    }
    *o_nde61=nde61;*o_ncoll=ncoll;*o_ng1=ng1;*o_nh=nh;*o_nboth=nboth;*o_sr61=sr61;
    return 1;
}

int main(int argc,char**argv){
    setbuf(stdout,NULL);
    rS0[0]=scale_rot(2);rS0[1]=scale_rot(13);rS0[2]=scale_rot(22);
    rS1[0]=scale_rot(6);rS1[1]=scale_rot(11);rS1[2]=scale_rot(25);
    rs0[0]=scale_rot(7);rs0[1]=scale_rot(18);ss0=scale_rot(3);
    rs1[0]=scale_rot(17);rs1[1]=scale_rot(19);ss1=scale_rot(10);
    for(int i=0;i<64;i++)KN[i]=K32[i]&MASK;
    for(int i=0;i<8;i++)IVN[i]=IV32[i]&MASK;
    int max_cands = (argc>1)?atoi(argv[1]):8;   /* cascade-eligible candidates per kernel */

    printf("=== coincidence_scan N=%d : g1 _|_ h independence across candidates x kernels ===\n",N);
    printf("(ratio R = P(g1=0 & h=0)/[P(g1=0)P(h=0)];  R~1 => 2^-2N wall;  R>>1 => sr=61 reverts to 2^-N)\n");
    int kernels[4]={N-1, 0, 1, N/2};
    for(int ki=0;ki<4;ki++){
        int kbit=kernels[ki];
        printf("\n--- kernel bit %d ---\n",kbit);
        printf("  %-10s %-12s %-10s %-10s %-8s %-8s %s\n","M0","de61hits","P(g1=0)","P(h=0)","ratio","sr60","sr61");
        int found=0;
        for(uint32_t m0=0;m0<=MASK&&found<max_cands;m0++){
            uint64_t nde61,ncoll,ng1,nh,nboth,sr61;
            if(!analyze(m0,kbit,&nde61,&ncoll,&ng1,&nh,&nboth,&sr61))continue;
            found++;
            double pg1=(double)ng1/nde61,ph=(double)nh/nde61,pboth=(double)nboth/nde61;
            double ratio=(pg1*ph>0)?pboth/(pg1*ph):0.0;
            printf("  0x%-8x %-12llu %-10.6f %-10.6f %-8.3f %-8llu %llu\n",
                m0,(unsigned long long)nde61,pg1,ph,ratio,(unsigned long long)ncoll,(unsigned long long)sr61);
        }
        if(!found)printf("  (no cascade-eligible M0 for this kernel)\n");
    }
    return 0;
}
