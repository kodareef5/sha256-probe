/*
 * gap_analysis.c — measure the sr=60 -> sr=61 coincidence-gap distribution.
 *
 * Enumerates ALL sr=60 cascade collisions at width N (MSB kernel, auto M0),
 * and for each collision computes the sr=61 W[60]-schedule gaps:
 *   sched1[60] = sigma1(w58)  + W1p[53] + sigma0(W1p[45]) + W1p[44]
 *   sched2[60] = sigma1(w58b) + W2p[53] + sigma0(W2p[45]) + W2p[44]
 *   g1 = w60  - sched1[60]   (mod 2^N)
 *   g2 = w60b - sched2[60]   (mod 2^N)
 *   h  = cas_off60 - (sched2[60] - sched1[60])     (the "compatibility gap")
 * sr=61 (W[60] level) <=> g1==0 AND g2==0.
 *
 * Outputs: collision count, marginal histograms of g1/g2, joint (g1=0,g2=0)
 * counts, and whether sr=61 rate looks like 2^-N (g1=0 => g2=0, i.e. h==0
 * structurally) or 2^-2N (g1,g2 independent). Dumps per-collision rows to CSV.
 *
 * Reuses the validated backward_construct enumeration (q5/block2_wang).
 * Compile: gcc -O3 -march=native -Xclang -fopenmp \
 *   -I/opt/homebrew/opt/libomp/include -L/opt/homebrew/opt/libomp/lib -lomp \
 *   -o gap_analysis gap_analysis.c -lm
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
#define MSB  (1U<<(N-1))

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

typedef struct{uint32_t w57,w58,w59,w60,w58b,w60b,casoff;} coll_t;

int main(void){
    setbuf(stdout,NULL);
    rS0[0]=scale_rot(2);rS0[1]=scale_rot(13);rS0[2]=scale_rot(22);
    rS1[0]=scale_rot(6);rS1[1]=scale_rot(11);rS1[2]=scale_rot(25);
    rs0[0]=scale_rot(7);rs0[1]=scale_rot(18);ss0=scale_rot(3);
    rs1[0]=scale_rot(17);rs1[1]=scale_rot(19);ss1=scale_rot(10);
    for(int i=0;i<64;i++)KN[i]=K32[i]&MASK;
    for(int i=0;i<8;i++)IVN[i]=IV32[i]&MASK;

    uint32_t M1[16],M2[16],M0=0;int found=0;
    for(uint32_t cand=0;cand<=MASK&&!found;cand++){
        for(int i=0;i<16;i++){M1[i]=MASK;M2[i]=MASK;}
        M1[0]=cand;M2[0]=cand^MSB;M2[9]=MASK^MSB;
        precompute(M1,state1,W1p);precompute(M2,state2,W2p);
        if(state1[0]==state2[0]){M0=cand;found=1;}
    }
    if(!found){printf("no cascade-eligible M0 at N=%d\n",N);return 1;}
    printf("=== gap_analysis N=%d  M0=0x%x fill=0x%x ===\n",N,M0,MASK);

    coll_t *colls=malloc((size_t)2000000*sizeof(coll_t));
    uint64_t nc=0, ntrip=0, nde61=0, ng1=0, nh=0, nboth=0;
    /* h = casoff - (sched2[60]-sched1[60]) is a per-TRIPLE quantity (w57,w58,w59).
       Histogram it over ALL 2^3N triples to test uniformity with huge stats. */
    uint64_t *htrip=calloc(MASK+1,sizeof(uint64_t));

    #pragma omp parallel
    {
      uint64_t lnc=0,lt=0,lh=0,l_ng1=0,l_nh=0,l_nboth=0;
      uint64_t *lhtrip=calloc(MASK+1,sizeof(uint64_t));
      coll_t *lc=malloc((size_t)200000*sizeof(coll_t)); uint64_t lci=0;
      #pragma omp for schedule(dynamic,1)
      for(uint32_t w57=0;w57<(MASK+1U);w57++){
        uint32_t s57a[8],s57b[8];memcpy(s57a,state1,32);memcpy(s57b,state2,32);
        uint32_t w57b=find_w2(s57a,s57b,57,w57);sha_round(s57a,KN[57],w57);sha_round(s57b,KN[57],w57b);
        for(uint32_t w58=0;w58<(MASK+1U);w58++){
          uint32_t s58a[8],s58b[8];memcpy(s58a,s57a,32);memcpy(s58b,s57b,32);
          uint32_t w58b=find_w2(s58a,s58b,58,w58);sha_round(s58a,KN[58],w58);sha_round(s58b,KN[58],w58b);
          for(uint32_t w59=0;w59<(MASK+1U);w59++){
            uint32_t s59a[8],s59b[8];memcpy(s59a,s58a,32);memcpy(s59b,s58b,32);
            uint32_t w59b=find_w2(s59a,s59b,59,w59);sha_round(s59a,KN[59],w59);sha_round(s59b,KN[59],w59b);
            lt++;
            uint32_t casoff=find_w2(s59a,s59b,60,0);
            /* per-triple gaps (hoisted so the w60 loop can use them) */
            uint32_t sched1_60=(fns1(w58)+W1p[53]+fns0(W1p[45])+W1p[44])&MASK;
            uint32_t sched2_60=(fns1(w58b)+W2p[53]+fns0(W2p[45])+W2p[44])&MASK;
            uint32_t hh=(casoff-((sched2_60-sched1_60)&MASK))&MASK; lhtrip[hh]++;
            uint32_t W1_61=(fns1(w59)+W1p[54]+fns0(W1p[46])+W1p[45])&MASK;
            uint32_t W2_61=(fns1(w59b)+W2p[54]+fns0(W2p[46])+W2p[45])&MASK;
            uint32_t W1_63=(fns1(W1_61)+W1p[56]+fns0(W1p[48])+W1p[47])&MASK;
            uint32_t W2_63=(fns1(W2_61)+W2p[56]+fns0(W2p[48])+W2p[47])&MASK;
            uint32_t sc62_1=(W1p[55]+fns0(W1p[47])+W1p[46])&MASK;
            uint32_t sc62_2=(W2p[55]+fns0(W2p[47])+W2p[46])&MASK;
            for(uint32_t w60=0;w60<(MASK+1U);w60++){
                uint32_t w60b=(w60+casoff)&MASK;
                uint32_t a[8],b[8];memcpy(a,s59a,32);memcpy(b,s59b,32);
                sha_round(a,KN[60],w60);sha_round(b,KN[60],w60b);
                uint32_t a1[8],b1[8];memcpy(a1,a,32);memcpy(b1,b,32);
                sha_round(a1,KN[61],W1_61);sha_round(b1,KN[61],W2_61);
                if(((a1[4]-b1[4])&MASK)!=0)continue;  /* de61=0 filter */
                lh++;
                /* independence test over de61=0 hits: is (g1==0) ind. of (h==0)? */
                { uint32_t g1=(w60-sched1_60)&MASK;
                  if(g1==0)l_ng1++; if(hh==0)l_nh++; if(g1==0&&hh==0)l_nboth++; }
                uint32_t W1_62=(fns1(w60)+sc62_1)&MASK,W2_62=(fns1(w60b)+sc62_2)&MASK;
                sha_round(a1,KN[62],W1_62);sha_round(b1,KN[62],W2_62);
                sha_round(a1,KN[63],W1_63);sha_round(b1,KN[63],W2_63);
                int ok=1;for(int r=0;r<8;r++)if(a1[r]!=b1[r]){ok=0;break;}
                if(ok&&lci<200000){lc[lci].w57=w57;lc[lci].w58=w58;lc[lci].w59=w59;
                    lc[lci].w60=w60;lc[lci].w58b=w58b;lc[lci].w60b=w60b;lc[lci].casoff=casoff;lci++;lnc++;}
            }
          }
        }
      }
      #pragma omp critical
      {
        for(uint64_t i=0;i<lci&&nc<2000000;i++)colls[nc++]=lc[i];
        ntrip+=lt;nde61+=lh;ng1+=l_ng1;nh+=l_nh;nboth+=l_nboth;
        for(uint32_t v=0;v<=MASK;v++)htrip[v]+=lhtrip[v];
      }
      free(lc);free(lhtrip);
    }
    /* h-over-all-triples uniformity (the decisive 2^-N vs 2^-2N test) */
    uint64_t hmax=0,hzt=htrip[0]; double hmean=(double)ntrip/(MASK+1);
    for(uint32_t v=0;v<=MASK;v++)if(htrip[v]>hmax)hmax=htrip[v];
    printf("\n--- h (compatibility gap) over ALL %llu triples ---\n",(unsigned long long)ntrip);
    printf("P(h==0): %llu / %llu = %.6f   (uniform 2^-N = %.6f)\n",
        (unsigned long long)hzt,(unsigned long long)ntrip,(double)hzt/ntrip,1.0/(MASK+1));
    printf("h-hist: mean/bin=%.1f  max-bin=%llu  (max/mean=%.2f; ~1 => uniform)\n",
        hmean,(unsigned long long)hmax,(double)hmax/hmean);
    free(htrip);
    /* INDEPENDENCE TEST over de61=0 hits: P(g1=0 & h=0) vs P(g1=0)*P(h=0).
       If independent => sr=61 ~ 2^-2N (TWO conditions), contradicting 2^-N. */
    double pg1=(double)ng1/nde61, ph=(double)nh/nde61, pboth=(double)nboth/nde61;
    printf("\n--- INDEPENDENCE TEST (g1=0 vs h=0) over %llu de61=0 hits ---\n",(unsigned long long)nde61);
    printf("P(g1=0)=%.6f (2^-N=%.6f)  P(h=0)=%.6f\n",pg1,1.0/(MASK+1),ph);
    printf("P(g1=0 & h=0)=%.8f   P(g1=0)*P(h=0)=%.8f   ratio=%.3f\n",
        pboth,pg1*ph,(pg1*ph>0)?pboth/(pg1*ph):0.0);
    printf("=> sr=61 needs g1=0 AND h=0; if ratio~1 they are INDEPENDENT => rate ~2^-2N.\n");
    printf("triples=%llu  de61=0 hits=%llu  sr60 collisions=%llu\n",
        (unsigned long long)ntrip,(unsigned long long)nde61,(unsigned long long)nc);

    /* ---- gap analysis over the sr=60 collisions ---- */
    uint64_t g1zero=0,g2zero=0,both=0,hzero=0;
    uint32_t *hist1=calloc(MASK+1,sizeof(uint32_t));
    uint32_t *hist2=calloc(MASK+1,sizeof(uint32_t));
    uint32_t *histh=calloc(MASK+1,sizeof(uint32_t));
    FILE *f=fopen("gap_rows.csv","w");
    fprintf(f,"w57,w58,w59,w60,g1,g2,h\n");
    for(uint64_t i=0;i<nc;i++){
        coll_t *c=&colls[i];
        uint32_t sched1=(fns1(c->w58)+W1p[53]+fns0(W1p[45])+W1p[44])&MASK;
        uint32_t sched2=(fns1(c->w58b)+W2p[53]+fns0(W2p[45])+W2p[44])&MASK;
        uint32_t g1=(c->w60 - sched1)&MASK;
        uint32_t g2=(c->w60b - sched2)&MASK;
        uint32_t h =(c->casoff - ((sched2 - sched1)&MASK))&MASK;
        hist1[g1]++;hist2[g2]++;histh[h]++;
        if(g1==0)g1zero++; if(g2==0)g2zero++; if(g1==0&&g2==0)both++; if(h==0)hzero++;
        fprintf(f,"%u,%u,%u,%u,%u,%u,%u\n",c->w57,c->w58,c->w59,c->w60,g1,g2,h);
    }
    fclose(f);
    /* max histogram bin (peak) to gauge non-uniformity */
    uint32_t mx1=0,mx2=0,mxh=0;
    for(uint32_t v=0;v<=MASK;v++){if(hist1[v]>mx1)mx1=hist1[v];if(hist2[v]>mx2)mx2=hist2[v];if(histh[v]>mxh)mxh=histh[v];}
    double exp_uni=(double)nc/(MASK+1);
    printf("\n--- sr=61 (W[60]) coincidence gap analysis (%llu collisions) ---\n",(unsigned long long)nc);
    printf("g1==0 : %llu  (expected if uniform: %.3f)\n",(unsigned long long)g1zero,exp_uni);
    printf("g2==0 : %llu  (expected if uniform: %.3f)\n",(unsigned long long)g2zero,exp_uni);
    printf("h==0  : %llu  (compatibility gap; h==0 => g1=0 <=> g2=0)\n",(unsigned long long)hzero);
    printf("BOTH g1==0 & g2==0  (= sr=61) : %llu\n",(unsigned long long)both);
    printf("  expected if 2^-N  (g1=0 => g2=0): %.4f\n",exp_uni);
    printf("  expected if 2^-2N (g1,g2 indep) : %.6f\n",(double)nc/((double)(MASK+1)*(MASK+1)));
    printf("histogram peaks: g1 max-bin=%u g2 max-bin=%u h max-bin=%u (uniform~%.2f)\n",mx1,mx2,mxh,exp_uni);
    printf("wrote gap_rows.csv\n");
    free(hist1);free(hist2);free(histh);free(colls);
    return 0;
}
