/*
 * uncond_indep.c — INTRINSIC per-round independence of (g1(r), h(r)), measured
 * UNCONDITIONALLY over the free-word domain (NO de61=0 filter).
 *
 * relax_gap.c measured the independence ratio over the de61=0 hit set (the natural
 * conditioning for the W[60] step). For rounds 57/58/59 that conditioning depends on
 * later free words (w59,w60) and could INDUCE spurious correlation. The honest
 * intrinsic question — "if we put the sr-boundary at round r, are its two conditions
 * g1=0 and h=0 independent?" — is answered UNCONDITIONALLY:
 *   P(g1(r)=0), P(h(r)=0), P(both), ratio = P(both)/[P(g1=0)P(h=0)] over the FULL
 *   domain of the words r's gap depends on.
 *
 * Domain per round (the words sched/casoff actually depend on):
 *   r=57: casoff(57),schdiff(57) are CONSTANTS => h(57) const; g1(57)=w57-const ranges
 *         over w57 (2^N). h(57) takes ONE value. -> report that value + P(h=0)in{0,1}.
 *   r=58: casoff(58),schdiff(58) depend on w57 (via state after r57) ; g1(58) on w58.
 *         domain = (w57,w58) = 2^{2N}.
 *   r=59: depends on (w57,w58,w59) = 2^{3N}.
 *   r=60: gap_analysis already did de61=0; here we ALSO give the unconditional
 *         version over (w57,w58,w59,w60)=2^{4N} for r=60 (h(60) over triples, g1 over w60).
 *
 * If a round shows ratio >> 1 unconditionally (g1=0 => h=0), THAT is a genuine soft
 * seam (cost 2^-N). If all ratios ~1 (or the step is impossible like r57), the
 * per-step 2^-2N is intrinsic.
 *
 * Compile: gcc -O3 -march=native -Xclang -fopenmp -I/opt/homebrew/opt/libomp/include \
 *   -L/opt/homebrew/opt/libomp/lib -lomp -DN=8 -o /tmp/uncond8 /tmp/uncond_indep.c -lm
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
#ifndef KERNBIT
#define KERNBIT (N-1)
#endif

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
static uint32_t KN[64],IVN[8],state1[8],state2[8],W1p[57],W2p[57];

static void precompute(const uint32_t M[16],uint32_t st[8],uint32_t W[57]){
    for(int i=0;i<16;i++)W[i]=M[i]&MASK;
    for(int i=16;i<57;i++)W[i]=(fns1(W[i-2])+W[i-7]+fns0(W[i-15])+W[i-16])&MASK;
    uint32_t a=IVN[0],b=IVN[1],c=IVN[2],d=IVN[3],e=IVN[4],f=IVN[5],g=IVN[6],h=IVN[7];
    for(int i=0;i<57;i++){
        uint32_t T1=(h+fnS1(e)+fnCh(e,f,g)+KN[i]+W[i])&MASK,T2=(fnS0(a)+fnMj(a,b,c))&MASK;
        h=g;g=f;f=e;e=(d+T1)&MASK;d=c;c=b;b=a;a=(T1+T2)&MASK;}
    st[0]=a;st[1]=b;st[2]=c;st[3]=d;st[4]=e;st[5]=f;st[6]=g;st[7]=h;
}
static inline void sha_round(uint32_t s[8],uint32_t k,uint32_t w){
    uint32_t T1=(s[7]+fnS1(s[4])+fnCh(s[4],s[5],s[6])+k+w)&MASK,T2=(fnS0(s[0])+fnMj(s[0],s[1],s[2]))&MASK;
    s[7]=s[6];s[6]=s[5];s[5]=s[4];s[4]=(s[3]+T1)&MASK;s[3]=s[2];s[2]=s[1];s[1]=s[0];s[0]=(T1+T2)&MASK;
}
static inline uint32_t find_w2(const uint32_t s1[8],const uint32_t s2[8],int rnd,uint32_t w1){
    uint32_t r1=(s1[7]+fnS1(s1[4])+fnCh(s1[4],s1[5],s1[6])+KN[rnd])&MASK;
    uint32_t r2=(s2[7]+fnS1(s2[4])+fnCh(s2[4],s2[5],s2[6])+KN[rnd])&MASK;
    uint32_t T21=(fnS0(s1[0])+fnMj(s1[0],s1[1],s1[2]))&MASK;
    uint32_t T22=(fnS0(s2[0])+fnMj(s2[0],s2[1],s2[2]))&MASK;
    return (w1+r1-r2+T21-T22)&MASK;
}

int main(void){
    setbuf(stdout,NULL);
    rS0[0]=scale_rot(2);rS0[1]=scale_rot(13);rS0[2]=scale_rot(22);
    rS1[0]=scale_rot(6);rS1[1]=scale_rot(11);rS1[2]=scale_rot(25);
    rs0[0]=scale_rot(7);rs0[1]=scale_rot(18);ss0=scale_rot(3);
    rs1[0]=scale_rot(17);rs1[1]=scale_rot(19);ss1=scale_rot(10);
    for(int i=0;i<64;i++)KN[i]=K32[i]&MASK;
    for(int i=0;i<8;i++)IVN[i]=IV32[i]&MASK;
    uint32_t kbit=(1U<<KERNBIT)&MASK;
    uint32_t M1[16],M2[16],M0=0;int found=0;
    for(uint32_t cand=0;cand<=MASK&&!found;cand++){
        for(int i=0;i<16;i++){M1[i]=MASK;M2[i]=MASK;}
        M1[0]=cand;M2[0]=cand^kbit;M2[9]=MASK^kbit;
        precompute(M1,state1,W1p);precompute(M2,state2,W2p);
        if(state1[0]==state2[0]){M0=cand;found=1;}
    }
    if(!found){printf("no M0 N=%d k=%d\n",N,KERNBIT);return 1;}
    printf("=== uncond_indep N=%d kernbit=%d M0=0x%x : INTRINSIC g1(r)_|_h(r), NO de61 filter ===\n",N,KERNBIT,M0);

    /* round-57 schedule constants */
    uint32_t casoff57=find_w2(state1,state2,57,0);
    uint32_t sc1_57=(fns1(W1p[55])+W1p[50]+fns0(W1p[42])+W1p[41])&MASK;
    uint32_t sc2_57=(fns1(W2p[55])+W2p[50]+fns0(W2p[42])+W2p[41])&MASK;
    uint32_t h57=(casoff57-((sc2_57-sc1_57)&MASK))&MASK;
    printf("\nW[57] (sr63->64): h(57) is the CONSTANT 0x%x (=%u). g1(57)=w57-0x%x ranges fully over w57.\n",
        h57,h57,sc1_57);
    printf("   => g2=g1+h57; step needs g1=0 AND g1=-h57. h57==0? %s -> step is %s.\n",
        (h57==0)?"YES":"NO", (h57==0)?"2^-N (g1=0 alone)":"IMPOSSIBLE (no w57 gives g1=0 & g2=0)");

    /* round 58: domain (w57,w58)=2^{2N}. h(58) depends on w57 (state after r57); g1(58) on w58. */
    {
      uint64_t ng1=0,nh=0,nboth=0,tot=0;
      uint64_t *hh=calloc(MASK+1,sizeof(uint64_t)),*hg=calloc(MASK+1,sizeof(uint64_t));
      uint32_t sc1=(fns1(W1p[56])+W1p[51]+fns0(W1p[43])+W1p[42])&MASK;
      uint32_t sc2=(fns1(W2p[56])+W2p[51]+fns0(W2p[43])+W2p[42])&MASK;
      #pragma omp parallel
      { uint64_t l1=0,lh=0,lb=0,lt=0; uint64_t *lhh=calloc(MASK+1,sizeof(uint64_t)),*lhg=calloc(MASK+1,sizeof(uint64_t));
        #pragma omp for schedule(dynamic,1)
        for(uint32_t w57=0;w57<(MASK+1U);w57++){
          uint32_t sa[8],sb[8];memcpy(sa,state1,32);memcpy(sb,state2,32);
          uint32_t w57b=find_w2(sa,sb,57,w57);sha_round(sa,KN[57],w57);sha_round(sb,KN[57],w57b);
          uint32_t casoff58=find_w2(sa,sb,58,0);
          uint32_t h58=(casoff58-((sc2-sc1)&MASK))&MASK; lhh[h58]++; /* per w57 (counts once; scaled below) */
          for(uint32_t w58=0;w58<(MASK+1U);w58++){
            uint32_t w58b=(w58+casoff58)&MASK;
            uint32_t g1=(w58-sc1)&MASK, g2=(w58b-sc2)&MASK; lhg[g1]++;
            lt++; if(g1==0)l1++; if(h58==0)lh++; if(g1==0&&h58==0)lb++;
            (void)g2;
          }
        }
        #pragma omp critical
        { ng1+=l1;nh+=lh;nboth+=lb;tot+=lt; for(uint32_t v=0;v<=MASK;v++){hh[v]+=lhh[v];hg[v]+=lhg[v];} }
        free(lhh);free(lhg);
      }
      double pg=(double)ng1/tot,ph=(double)nh/tot,pb=(double)nboth/tot;
      uint64_t mh=0,mg=0; for(uint32_t v=0;v<=MASK;v++){if(hh[v]>mh)mh=hh[v];if(hg[v]>mg)mg=hg[v];}
      /* hh was counted once per w57 (MASK+1 samples), hg once per (w57,w58) */
      printf("\nW[58] (sr62->63): domain (w57,w58)=%llu | P(g1=0)=%.6f P(h=0)=%.6f P(both)=%.8f ratio=%.4f\n",
        (unsigned long long)tot,pg,ph,pb,(pg*ph>0)?pb/(pg*ph):0.0);
      printf("   h(58) uniformity over w57: max/mean=%.2f (image peak)   g1 uniform max/mean=%.2f\n",
        (double)mh/((double)(MASK+1)/(MASK+1)), (double)mg/((double)tot/(MASK+1)));
      free(hh);free(hg);
    }

    /* round 59: domain (w57,w58,w59)=2^{3N}. */
    {
      uint64_t ng1=0,nh=0,nboth=0,tot=0;
      #pragma omp parallel
      { uint64_t l1=0,lh=0,lb=0,lt=0;
        #pragma omp for schedule(dynamic,1)
        for(uint32_t w57=0;w57<(MASK+1U);w57++){
          uint32_t sa[8],sb[8];memcpy(sa,state1,32);memcpy(sb,state2,32);
          uint32_t w57b=find_w2(sa,sb,57,w57);sha_round(sa,KN[57],w57);sha_round(sb,KN[57],w57b);
          uint32_t sc1=(fns1(w57)+W1p[52]+fns0(W1p[44])+W1p[43])&MASK;    /* sched59 uses w57 */
          uint32_t sc2=(fns1(w57b)+W2p[52]+fns0(W2p[44])+W2p[43])&MASK;
          for(uint32_t w58=0;w58<(MASK+1U);w58++){
            uint32_t sb2a[8],sb2b[8];memcpy(sb2a,sa,32);memcpy(sb2b,sb,32);
            uint32_t w58b=find_w2(sb2a,sb2b,58,w58);sha_round(sb2a,KN[58],w58);sha_round(sb2b,KN[58],w58b);
            uint32_t casoff59=find_w2(sb2a,sb2b,59,0);
            uint32_t h59=(casoff59-((sc2-sc1)&MASK))&MASK;
            for(uint32_t w59=0;w59<(MASK+1U);w59++){
              uint32_t w59b=(w59+casoff59)&MASK;
              uint32_t g1=(w59-sc1)&MASK;
              lt++; if(g1==0)l1++; if(h59==0)lh++; if(g1==0&&h59==0)lb++;
              (void)w59b;
            }
          }
        }
        #pragma omp critical
        { ng1+=l1;nh+=lh;nboth+=lb;tot+=lt; }
      }
      double pg=(double)ng1/tot,ph=(double)nh/tot,pb=(double)nboth/tot;
      printf("\nW[59] (sr61->62): domain (w57,w58,w59)=%llu | P(g1=0)=%.6f P(h=0)=%.6f P(both)=%.8f ratio=%.4f\n",
        (unsigned long long)tot,pg,ph,pb,(pg*ph>0)?pb/(pg*ph):0.0);
    }

    /* round 60 unconditional: domain (w57,w58,w59,w60)=2^{4N}; h(60) per (w57,w58,w59)
       (depends on casoff60 = function of w57,w58,w59), g1(60)=w60-sched60. */
    {
      uint64_t ng1=0,nh=0,nboth=0,tot=0;
      #pragma omp parallel
      { uint64_t l1=0,lh=0,lb=0,lt=0;
        #pragma omp for schedule(dynamic,1)
        for(uint32_t w57=0;w57<(MASK+1U);w57++){
          uint32_t sa[8],sb[8];memcpy(sa,state1,32);memcpy(sb,state2,32);
          uint32_t w57b=find_w2(sa,sb,57,w57);sha_round(sa,KN[57],w57);sha_round(sb,KN[57],w57b);
          for(uint32_t w58=0;w58<(MASK+1U);w58++){
            uint32_t s2a[8],s2b[8];memcpy(s2a,sa,32);memcpy(s2b,sb,32);
            uint32_t w58b=find_w2(s2a,s2b,58,w58);sha_round(s2a,KN[58],w58);sha_round(s2b,KN[58],w58b);
            uint32_t sc1=(fns1(w58)+W1p[53]+fns0(W1p[45])+W1p[44])&MASK;   /* sched60 uses w58 */
            uint32_t sc2=(fns1(w58b)+W2p[53]+fns0(W2p[45])+W2p[44])&MASK;
            for(uint32_t w59=0;w59<(MASK+1U);w59++){
              uint32_t s3a[8],s3b[8];memcpy(s3a,s2a,32);memcpy(s3b,s2b,32);
              uint32_t w59b=find_w2(s3a,s3b,59,w59);sha_round(s3a,KN[59],w59);sha_round(s3b,KN[59],w59b);
              uint32_t casoff60=find_w2(s3a,s3b,60,0);
              uint32_t h60=(casoff60-((sc2-sc1)&MASK))&MASK;
              /* collapse the w60 loop analytically: g1(60)=w60-sc1 is uniform over the
                 2^N values of w60 (free word), independent of h60 (a function of
                 w57,w58,w59). So over each triple: #g1=0 is exactly 1, #h60=0 is 2^N*[h60==0],
                 #both is exactly [h60==0]. ratio is then provably 1; we just tally h60=0. */
              lt++; if(h60==0)lh++;
            }
          }
        }
        #pragma omp critical
        { nh+=lh;tot+=lt; }
      }
      /* tot = #triples; P(g1=0)=2^-N exactly; P(h60=0)=nh/tot; P(both)=P(h60=0)*2^-N exactly. */
      double pg=1.0/(MASK+1), ph=(double)nh/tot, pb=ph*pg;
      printf("\nW[60] (sr60->61): triples (w57,w58,w59)=%llu | P(g1=0)=%.6f(exact 2^-N) P(h=0)=%.6f P(both)=%.8f ratio=%.4f\n",
        (unsigned long long)tot,pg,ph,pb,(pg*ph>0)?pb/(pg*ph):0.0);
      printf("   [W[60] g1=0 is exactly uniform in the free word w60 => ratio is provably 1; only h60=0 tallied]\n");
      (void)ng1;(void)nboth;
    }
    printf("\n(unconditional ratio ~1 => g1,h INTRINSICALLY independent at that round => step is genuinely 2^-2N;\n");
    printf(" ratio >> 1 would mean g1=0 => h=0, a 2^-N soft seam; r57 special: h is a nonzero const => impossible.)\n");
    return 0;
}
