/* h58_scan.c — is h(58)=0 reachable? h(58)=casoff(58)-schdiff(58) where casoff(58)
 * depends on w57 (state after the FIRST cascade round). de57 is CONSTANT, so casoff(58)
 * ranges over a SMALL image as w57 varies. Question: is 0 in the h(58) image, per kernel/M0?
 * If not, the W[58] (sr62->63) step is IMPOSSIBLE for that kernel (like r57). */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#ifndef N
#define N 8
#endif
#define MASK ((1U<<N)-1)
static int rS0[3],rS1[3],rs0[2],rs1[2],ss0,ss1;
static int sr(int k){int r=(int)rint((double)k*N/32.0);return r<1?1:r;}
static inline uint32_t ror(uint32_t x,int k){k%=N;return ((x>>k)|(x<<(N-k)))&MASK;}
static inline uint32_t S0(uint32_t a){return ror(a,rS0[0])^ror(a,rS0[1])^ror(a,rS0[2]);}
static inline uint32_t S1(uint32_t e){return ror(e,rS1[0])^ror(e,rS1[1])^ror(e,rS1[2]);}
static inline uint32_t s0(uint32_t x){return ror(x,rs0[0])^ror(x,rs0[1])^((x>>ss0)&MASK);}
static inline uint32_t s1(uint32_t x){return ror(x,rs1[0])^ror(x,rs1[1])^((x>>ss1)&MASK);}
static inline uint32_t Ch(uint32_t e,uint32_t f,uint32_t g){return ((e&f)^((~e)&g))&MASK;}
static inline uint32_t Mj(uint32_t a,uint32_t b,uint32_t c){return ((a&b)^(a&c)^(b&c))&MASK;}
static const uint32_t K32[64]={0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
static const uint32_t IV32[8]={0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};
static uint32_t KN[64],IVN[8];
static void pre(const uint32_t M[16],uint32_t st[8],uint32_t W[57]){
  for(int i=0;i<16;i++)W[i]=M[i]&MASK; for(int i=16;i<57;i++)W[i]=(s1(W[i-2])+W[i-7]+s0(W[i-15])+W[i-16])&MASK;
  uint32_t a=IVN[0],b=IVN[1],c=IVN[2],d=IVN[3],e=IVN[4],f=IVN[5],g=IVN[6],h=IVN[7];
  for(int i=0;i<57;i++){uint32_t T1=(h+S1(e)+Ch(e,f,g)+KN[i]+W[i])&MASK,T2=(S0(a)+Mj(a,b,c))&MASK;h=g;g=f;f=e;e=(d+T1)&MASK;d=c;c=b;b=a;a=(T1+T2)&MASK;}
  st[0]=a;st[1]=b;st[2]=c;st[3]=d;st[4]=e;st[5]=f;st[6]=g;st[7]=h;}
static inline void rnd(uint32_t s[8],uint32_t k,uint32_t w){uint32_t T1=(s[7]+S1(s[4])+Ch(s[4],s[5],s[6])+k+w)&MASK,T2=(S0(s[0])+Mj(s[0],s[1],s[2]))&MASK;s[7]=s[6];s[6]=s[5];s[5]=s[4];s[4]=(s[3]+T1)&MASK;s[3]=s[2];s[2]=s[1];s[1]=s[0];s[0]=(T1+T2)&MASK;}
static inline uint32_t fw2(const uint32_t s1_[8],const uint32_t s2_[8],int r,uint32_t w1){uint32_t r1=(s1_[7]+S1(s1_[4])+Ch(s1_[4],s1_[5],s1_[6])+KN[r])&MASK;uint32_t r2=(s2_[7]+S1(s2_[4])+Ch(s2_[4],s2_[5],s2_[6])+KN[r])&MASK;uint32_t T21=(S0(s1_[0])+Mj(s1_[0],s1_[1],s1_[2]))&MASK;uint32_t T22=(S0(s2_[0])+Mj(s2_[0],s2_[1],s2_[2]))&MASK;return (w1+r1-r2+T21-T22)&MASK;}
int main(void){
  rS0[0]=sr(2);rS0[1]=sr(13);rS0[2]=sr(22);rS1[0]=sr(6);rS1[1]=sr(11);rS1[2]=sr(25);rs0[0]=sr(7);rs0[1]=sr(18);ss0=sr(3);rs1[0]=sr(17);rs1[1]=sr(19);ss1=sr(10);
  for(int i=0;i<64;i++)KN[i]=K32[i]&MASK;for(int i=0;i<8;i++)IVN[i]=IV32[i]&MASK;
  printf("=== h58_scan N=%d : is h(58)=0 reachable per kernel/M0? (W[58]=sr62->63 step) ===\n",N);
  printf("kbit |  M0  | |de57| | |h(58) image| | 0 in image? -> step\n");
  uint32_t st1[8],st2[8],W1p[57],W2p[57];
  int n_pairs=0,n_h58_reach=0;
  for(int b=0;b<N;b++){uint32_t kbit=(1U<<b)&MASK;
    for(uint32_t cand=0;cand<=MASK;cand++){uint32_t M1[16],M2[16];for(int i=0;i<16;i++){M1[i]=MASK;M2[i]=MASK;}M1[0]=cand;M2[0]=cand^kbit;M2[9]=MASK^kbit;
      pre(M1,st1,W1p);pre(M2,st2,W2p);if(st1[0]!=st2[0])continue;n_pairs++;
      uint32_t sc1=(s1(W1p[56])+W1p[51]+s0(W1p[43])+W1p[42])&MASK;
      uint32_t sc2=(s1(W2p[56])+W2p[51]+s0(W2p[43])+W2p[42])&MASK;
      uint32_t schd=(sc2-sc1)&MASK;
      char*seen=calloc(MASK+1,1); char*de57seen=calloc(MASK+1,1);
      int reach=0,himg=0,de57img=0;
      for(uint32_t w57=0;w57<(MASK+1U);w57++){uint32_t sa[8],sb[8];memcpy(sa,st1,32);memcpy(sb,st2,32);
        uint32_t w57b=fw2(sa,sb,57,w57);rnd(sa,KN[57],w57);rnd(sb,KN[57],w57b);
        uint32_t de57=(sa[4]-sb[4])&MASK; if(!de57seen[de57]){de57seen[de57]=1;de57img++;}
        uint32_t casoff58=fw2(sa,sb,58,0); uint32_t h58=(casoff58-schd)&MASK;
        if(!seen[h58]){seen[h58]=1;himg++;} if(h58==0)reach=1;}
      if(reach)n_h58_reach++;
      printf(" %2d  | 0x%02x |   %d    |     %2d        | %s\n",b,cand,de57img,himg, reach?"YES -> 2^-2N possible":"NO  -> IMPOSSIBLE");
      free(seen);free(de57seen);
    }}
  printf("-----\ncascade-eligible pairs: %d ; h(58)=0 reachable in: %d ; IMPOSSIBLE in: %d\n",n_pairs,n_h58_reach,n_pairs-n_h58_reach);
  return 0;}
