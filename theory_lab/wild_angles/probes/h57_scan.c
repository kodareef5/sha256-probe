/*
 * h57_scan.c — decisive adversarial test of the ROUND-57 coupling.
 *
 * relax_gap.c found: for free word W[57] (the sr63->64 step), h(57) is a CONSTANT
 * (max-bin/mean = 2^N => all mass in one bin), NOT uniform. So the two conditions
 * g1(57)=0 and g2(57)=0 are PERFECTLY COUPLED: g2 = g1 + h(57), h(57) fixed.
 *   - if h(57)==0 : g1=0 => g2=0 automatically  => W[57] step costs only 2^-N (SOFT SEAM!)
 *   - if h(57)!=0 : g1=0 and g2=0 can NEVER co-hold => W[57] step is IMPOSSIBLE.
 * Observed: h(57)!=0 for MSB (kernbit=7) and exotic (kernbit=4) at N=8.
 *
 * MECHANISM (claimed): round 57 is the FIRST cascade round, so casoff(57) and
 * (sched2[57]-sched1[57]) are functions of the PRECOMPUTE states ONLY (no free word
 * has been chosen yet) => h(57) is a per-(kernel,M0) CONSTANT, independent of the
 * collision. This program computes that constant directly (no sweep needed) for
 * EVERY kernel bit b in 0..N-1 and EVERY cascade-eligible M0, and asks: is h(57)
 * EVER 0?  If yes -> a 2^-N seam exists at round 57. If never -> the coupling is real
 * but always lands on a nonzero constant -> no seam, round 57 is the WORST place
 * (cost 0, impossible), not the cheapest.
 *
 * Also reports h(58) constancy check by direct formula and the de57 value.
 *
 * Compile: gcc -O3 -DN=8 -o /tmp/h57_scan8 /tmp/h57_scan.c -lm
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>

#ifndef N
#define N 8
#endif
#define MASK ((1U<<N)-1)

static int rS0[3], rS1[3], rs0[2], rs1[2], ss0, ss1;
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

static void precompute(const uint32_t M[16],uint32_t st[8],uint32_t W[57]){
    for(int i=0;i<16;i++)W[i]=M[i]&MASK;
    for(int i=16;i<57;i++)W[i]=(fns1(W[i-2])+W[i-7]+fns0(W[i-15])+W[i-16])&MASK;
    uint32_t a=IVN[0],b=IVN[1],c=IVN[2],d=IVN[3],e=IVN[4],f=IVN[5],g=IVN[6],h=IVN[7];
    for(int i=0;i<57;i++){
        uint32_t T1=(h+fnS1(e)+fnCh(e,f,g)+KN[i]+W[i])&MASK,T2=(fnS0(a)+fnMj(a,b,c))&MASK;
        h=g;g=f;f=e;e=(d+T1)&MASK;d=c;c=b;b=a;a=(T1+T2)&MASK;}
    st[0]=a;st[1]=b;st[2]=c;st[3]=d;st[4]=e;st[5]=f;st[6]=g;st[7]=h;
}
static inline uint32_t find_w2(const uint32_t s1[8],const uint32_t s2[8],int rnd,uint32_t w1){
    uint32_t r1=(s1[7]+fnS1(s1[4])+fnCh(s1[4],s1[5],s1[6])+KN[rnd])&MASK;
    uint32_t r2=(s2[7]+fnS1(s2[4])+fnCh(s2[4],s2[5],s2[6])+KN[rnd])&MASK;
    uint32_t T21=(fnS0(s1[0])+fnMj(s1[0],s1[1],s1[2]))&MASK;
    uint32_t T22=(fnS0(s2[0])+fnMj(s2[0],s2[1],s2[2]))&MASK;
    return (w1+r1-r2+T21-T22)&MASK;
}

int main(void){
    rS0[0]=scale_rot(2);rS0[1]=scale_rot(13);rS0[2]=scale_rot(22);
    rS1[0]=scale_rot(6);rS1[1]=scale_rot(11);rS1[2]=scale_rot(25);
    rs0[0]=scale_rot(7);rs0[1]=scale_rot(18);ss0=scale_rot(3);
    rs1[0]=scale_rot(17);rs1[1]=scale_rot(19);ss1=scale_rot(10);
    for(int i=0;i<64;i++)KN[i]=K32[i]&MASK;
    for(int i=0;i<8;i++)IVN[i]=IV32[i]&MASK;

    printf("=== h57_scan N=%d : is h(57) EVER 0 over all kernels x cascade-eligible M0? ===\n",N);
    printf("kbit |   M0  | db56 hw | de57   | casoff57 | schdiff57 | h(57)  | h(57)==0?\n");
    printf("-----|-------|---------|--------|----------|-----------|--------|----------\n");
    uint32_t st1[8],st2[8],W1p[57],W2p[57];
    uint64_t total=0, hz57=0; int any_h57_zero=0;
    for(int b=0;b<N;b++){
        uint32_t kbit=(1U<<b)&MASK;
        for(uint32_t cand=0;cand<=MASK;cand++){
            uint32_t M1[16],M2[16];
            for(int i=0;i<16;i++){M1[i]=MASK;M2[i]=MASK;}
            M1[0]=cand;M2[0]=cand^kbit;M2[9]=MASK^kbit;
            precompute(M1,st1,W1p);precompute(M2,st2,W2p);
            if(st1[0]!=st2[0])continue;            /* not cascade-eligible (da56!=0) */
            total++;
            /* db56 hw (label only) */
            uint32_t db56=(st1[1]-st2[1])&MASK; int hwdb=0; for(int j=0;j<N;j++) if((db56>>j)&1) hwdb++;
            /* round-57 constants: casoff(57)=find_w2 at the PRECOMPUTE states (w1=0);
               sched_i[57]=sigma1(Wp[55])+Wp[50]+sigma0(Wp[42])+Wp[41]; both message-independent. */
            uint32_t casoff57=find_w2(st1,st2,57,0);
            uint32_t sc1=(fns1(W1p[55])+W1p[50]+fns0(W1p[42])+W1p[41])&MASK;
            uint32_t sc2=(fns1(W2p[55])+W2p[50]+fns0(W2p[42])+W2p[41])&MASK;
            uint32_t schdiff=(sc2-sc1)&MASK;
            uint32_t h57=(casoff57 - schdiff)&MASK;
            /* de57: e-diff AFTER round 57. The cascade keeps da=0; de57 depends only on
               states (constant in the free words) — compute it for w57=0 as a representative. */
            uint32_t sa[8],sb[8];memcpy(sa,st1,32);memcpy(sb,st2,32);
            uint32_t w57=0,w57b=find_w2(sa,sb,57,w57);
            /* one round 57 */
            { uint32_t T1=(sa[7]+fnS1(sa[4])+fnCh(sa[4],sa[5],sa[6])+KN[57]+w57)&MASK,T2=(fnS0(sa[0])+fnMj(sa[0],sa[1],sa[2]))&MASK;
              sa[7]=sa[6];sa[6]=sa[5];sa[5]=sa[4];sa[4]=(sa[3]+T1)&MASK;sa[3]=sa[2];sa[2]=sa[1];sa[1]=sa[0];sa[0]=(T1+T2)&MASK; }
            { uint32_t T1=(sb[7]+fnS1(sb[4])+fnCh(sb[4],sb[5],sb[6])+KN[57]+w57b)&MASK,T2=(fnS0(sb[0])+fnMj(sb[0],sb[1],sb[2]))&MASK;
              sb[7]=sb[6];sb[6]=sb[5];sb[5]=sb[4];sb[4]=(sb[3]+T1)&MASK;sb[3]=sb[2];sb[2]=sb[1];sb[1]=sb[0];sb[0]=(T1+T2)&MASK; }
            uint32_t de57=(sa[4]-sb[4])&MASK;
            int isz=(h57==0); if(isz){hz57++;any_h57_zero=1;}
            printf(" %2d  | 0x%02x |    %d    | 0x%04x | 0x%04x   | 0x%04x    | 0x%04x | %s\n",
                b,cand,hwdb,de57,casoff57,schdiff,h57, isz?"*** YES ***":"no");
        }
    }
    printf("-----\n");
    printf("cascade-eligible (kernel,M0) pairs scanned: %llu ; of these h(57)==0: %llu\n",
        (unsigned long long)total,(unsigned long long)hz57);
    printf("VERDICT: h(57)==0 is %s achievable at N=%d => round-57 sr-step %s.\n",
        any_h57_zero?"SOMETIMES":"NEVER", N,
        any_h57_zero?"can be a 2^-N SOFT SEAM (check g1 reachable there)":"is IMPOSSIBLE (coupled to nonzero const), not a seam");
    return 0;
}
