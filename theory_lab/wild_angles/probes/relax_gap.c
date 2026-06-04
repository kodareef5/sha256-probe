/*
 * relax_gap.c — RELAXATION-POINT sweep: generalize gap_analysis.c to EVERY free
 * word W[r], r in {57,58,59,60}, of the cascade-DP sr=60 construction.
 *
 * The sr-ladder forces the free words one at a time, backward:
 *     W[60]  <-> sr60 -> 61    (this is the ONLY round gap_analysis.c measured)
 *     W[59]  <-> sr61 -> 62
 *     W[58]  <-> sr62 -> 63
 *     W[57]  <-> sr63 -> 64
 * For a given full sr=60 collision, "additionally force W[r] schedule-compliant
 * for BOTH messages" costs, by the same algebra as round 60:
 *     sched1[r] = sigma1(W1[r-2]) + W1[r-7] + sigma0(W1[r-15]) + W1[r-16]
 *     sched2[r] = sigma1(W2[r-2]) + W2[r-7] + sigma0(W2[r-15]) + W2[r-16]
 *     g1(r) = W1[r] - sched1[r]                         (per-message-1 value match)
 *     g2(r) = W2[r] - sched2[r]                         (per-message-2 value match)
 *     h(r)  = (W2[r]-W1[r]) - (sched2[r]-sched1[r])     (inter-message compat gap)
 *   identity: g2(r) = g1(r) + h(r)  (mod 2^N).
 *   marginal sr-step <=> g1(r)==0 AND g2(r)==0 <=> g1(r)==0 AND h(r)==0.
 *
 * QUESTION: is round 60 the CHEAPEST place for the sr-boundary, or does some r
 *   have g1,h COUPLED (cost 2^-N) or one AUTO-SATISFIED (cost 2^-N or free)?
 *
 * We measure, per round r:
 *   (A) uniformity of g1(r),h(r) over the free-word domain (huge stats);
 *   (B) the independence ratio P(g1=0 & h=0)/[P(g1=0)P(h=0)] over de61=0 hits;
 *   (C) the marginal counts over the genuine sr=60 collision set;
 *   plus de57..de60 instrumentation and a de58-coupling test for r=58.
 *
 * READ-ONLY toward the repo. Mirrors lib.sha256 at width N (scaled rotations,
 * MSB kernel, auto-M0). Reuses gap_analysis.c's validated enumeration verbatim;
 * the ONLY additions are the per-round (g1,g2,h) accumulators in the same loops.
 *
 * Kernel selection: -DKERNBIT=b forces M2[0]=M0^(1<<b), M2[9]=MASK^(1<<b)
 *   (default b=N-1 = MSB). Lets us test an exotic high-hw(db56) kernel.
 *
 * Compile (lab-side, /tmp):
 *   gcc -O3 -march=native -Xclang -fopenmp \
 *     -I/opt/homebrew/opt/libomp/include -L/opt/homebrew/opt/libomp/lib -lomp \
 *     -DN=8 -o /tmp/relax_gap8 /tmp/relax_gap.c -lm
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

/* schedule target for free word r, message side using precompute words Wp[] and
   the free words it may depend on. r in {57,58,59,60}:
     r=57: sigma1(Wp[55]) + Wp[50] + sigma0(Wp[42]) + Wp[41]      (NO free word)
     r=58: sigma1(Wp[56]) + Wp[51] + sigma0(Wp[43]) + Wp[42]      (NO free word)
     r=59: sigma1(w57)    + Wp[52] + sigma0(Wp[44]) + Wp[43]      (free: w57)
     r=60: sigma1(w58)    + Wp[53] + sigma0(Wp[45]) + Wp[44]      (free: w58)
   The r-2 term is the only one that can be a free word (55,56 are NOT free; 57,58 ARE). */
static inline uint32_t sched_r(int r,const uint32_t Wp[57],uint32_t wm2){
    /* wm2 = the W[r-2] value (free word for r>=59, else Wp[r-2]) */
    return (fns1(wm2)+Wp[r-7]+fns0(Wp[r-15])+Wp[r-16])&MASK;
}

typedef struct{uint32_t w57,w58,w59,w60,w57b,w58b,w59b,w60b,casoff;} coll_t;

/* per-round accumulators */
typedef struct{
    uint64_t ng1, nh, ng2, nboth, n_g2id_fail;  /* over de61=0 hits */
    uint64_t *hg1, *hh;                          /* histograms over de61=0 hits */
} racc_t;

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
    if(!found){printf("no cascade-eligible M0 at N=%d kernbit=%d\n",N,KERNBIT);return 1;}
    /* db56 = b-register difference at round 56 (precompute output index 1). hw used only as a label. */
    uint32_t db56=(state1[1]-state2[1])&MASK; int hwdb=0; for(int b=0;b<N;b++) if((db56>>b)&1) hwdb++;
    printf("=== relax_gap N=%d kernbit=%d  M0=0x%x fill=0x%x  db56=0x%x(hw=%d) ===\n",
           N,KERNBIT,M0,MASK,db56,hwdb);

    /* round set we instrument: free words 57..60 */
    int RND[4]={57,58,59,60}; const int NR=4;

    coll_t *colls=malloc((size_t)4000000*sizeof(coll_t));
    uint64_t nc=0, ntrip=0, nde61=0;
    /* de-image accumulators (do de57..de60 vary? memo: only de58 varies) */
    uint64_t *de_img[4]; for(int i=0;i<4;i++) de_img[i]=calloc(MASK+1,sizeof(uint64_t));
    /* per-round global accumulators */
    racc_t G[4];
    for(int k=0;k<NR;k++){ G[k].ng1=G[k].nh=G[k].ng2=G[k].nboth=G[k].n_g2id_fail=0;
        G[k].hg1=calloc(MASK+1,sizeof(uint64_t)); G[k].hh=calloc(MASK+1,sizeof(uint64_t)); }
    /* de58-coupling for r=58: joint count of (g1(58)==0) x (de58 bucket) — does forcing
       W[58] interact with the de58 freedom? We test: is P(g1(58)=0 | de58=v) flat in v? */
    /* We instead test coupling via independence ratio per round (below). de58 logged separately. */

    #pragma omp parallel
    {
      uint64_t lnc=0,lt=0,lh=0;
      uint64_t *lde[4]; for(int i=0;i<4;i++) lde[i]=calloc(MASK+1,sizeof(uint64_t));
      racc_t L[4];
      for(int k=0;k<NR;k++){ L[k].ng1=L[k].nh=L[k].ng2=L[k].nboth=L[k].n_g2id_fail=0;
          L[k].hg1=calloc(MASK+1,sizeof(uint64_t)); L[k].hh=calloc(MASK+1,sizeof(uint64_t)); }
      coll_t *lc=malloc((size_t)400000*sizeof(coll_t)); uint64_t lci=0;

      #pragma omp for schedule(dynamic,1)
      for(uint32_t w57=0;w57<(MASK+1U);w57++){
        uint32_t s57a[8],s57b[8];memcpy(s57a,state1,32);memcpy(s57b,state2,32);
        uint32_t w57b=find_w2(s57a,s57b,57,w57);
        /* de57 (e-diff entering round 57's output, i.e. after the round) */
        sha_round(s57a,KN[57],w57);sha_round(s57b,KN[57],w57b);
        lde[0][(s57a[4]-s57b[4])&MASK]++;
        for(uint32_t w58=0;w58<(MASK+1U);w58++){
          uint32_t s58a[8],s58b[8];memcpy(s58a,s57a,32);memcpy(s58b,s57b,32);
          uint32_t w58b=find_w2(s58a,s58b,58,w58);
          sha_round(s58a,KN[58],w58);sha_round(s58b,KN[58],w58b);
          lde[1][(s58a[4]-s58b[4])&MASK]++;
          for(uint32_t w59=0;w59<(MASK+1U);w59++){
            uint32_t s59a[8],s59b[8];memcpy(s59a,s58a,32);memcpy(s59b,s58b,32);
            uint32_t w59b=find_w2(s59a,s59b,59,w59);
            sha_round(s59a,KN[59],w59);sha_round(s59b,KN[59],w59b);
            lde[2][(s59a[4]-s59b[4])&MASK]++;
            lt++;
            uint32_t casoff=find_w2(s59a,s59b,60,0);

            /* ---- per-round schedule targets and gaps (independent of w60) ---- */
            /* r=57 */
            uint32_t sc1_57=sched_r(57,W1p,W1p[55]);
            uint32_t sc2_57=sched_r(57,W2p,W2p[55]);
            uint32_t g1_57=(w57 - sc1_57)&MASK, g2_57=(w57b - sc2_57)&MASK;
            uint32_t h_57=(((w57b-w57)&MASK) - ((sc2_57-sc1_57)&MASK))&MASK;
            /* r=58 */
            uint32_t sc1_58=sched_r(58,W1p,W1p[56]);
            uint32_t sc2_58=sched_r(58,W2p,W2p[56]);
            uint32_t g1_58=(w58 - sc1_58)&MASK, g2_58=(w58b - sc2_58)&MASK;
            uint32_t h_58=(((w58b-w58)&MASK) - ((sc2_58-sc1_58)&MASK))&MASK;
            /* r=59 (sched uses free word w57 / w57b for r-2) */
            uint32_t sc1_59=sched_r(59,W1p,w57);
            uint32_t sc2_59=sched_r(59,W2p,w57b);
            uint32_t g1_59=(w59 - sc1_59)&MASK, g2_59=(w59b - sc2_59)&MASK;
            uint32_t h_59=(((w59b-w59)&MASK) - ((sc2_59-sc1_59)&MASK))&MASK;
            /* r=60 (sched uses free word w58 / w58b for r-2) — gap_analysis.c's quantity */
            uint32_t sc1_60=sched_r(60,W1p,w58);
            uint32_t sc2_60=sched_r(60,W2p,w58b);
            uint32_t h_60=(casoff - ((sc2_60-sc1_60)&MASK))&MASK;

            /* schedule-fixed words for the de61 filter (same as gap_analysis.c) */
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
                if(w60==0){ lde[3][(a[4]-b[4])&MASK]++; } /* de60 sample (memo: ==0 always) */
                uint32_t a1[8],b1[8];memcpy(a1,a,32);memcpy(b1,b,32);
                sha_round(a1,KN[61],W1_61);sha_round(b1,KN[61],W2_61);
                if(((a1[4]-b1[4])&MASK)!=0)continue;  /* de61=0 filter */
                lh++;
                /* ---- per-round (g1,h) accumulation over de61=0 hits ----
                   r=57,58,59 gaps are INDEPENDENT of w60 (functions of w57,w58,w59);
                   r=60 gap g1 depends on w60. We accumulate all four here so the
                   de61=0 conditioning is identical across rounds (apples-to-apples). */
                uint32_t g1_60=(w60 - sc1_60)&MASK, g2_60=(w60b - sc2_60)&MASK;
                /* round 57 */
                if(g1_57==0)L[0].ng1++; if(h_57==0)L[0].nh++; if(g2_57==0)L[0].ng2++;
                if(g1_57==0&&h_57==0)L[0].nboth++; if(((g1_57+h_57)&MASK)!=g2_57)L[0].n_g2id_fail++;
                L[0].hg1[g1_57]++; L[0].hh[h_57]++;
                /* round 58 */
                if(g1_58==0)L[1].ng1++; if(h_58==0)L[1].nh++; if(g2_58==0)L[1].ng2++;
                if(g1_58==0&&h_58==0)L[1].nboth++; if(((g1_58+h_58)&MASK)!=g2_58)L[1].n_g2id_fail++;
                L[1].hg1[g1_58]++; L[1].hh[h_58]++;
                /* round 59 */
                if(g1_59==0)L[2].ng1++; if(h_59==0)L[2].nh++; if(g2_59==0)L[2].ng2++;
                if(g1_59==0&&h_59==0)L[2].nboth++; if(((g1_59+h_59)&MASK)!=g2_59)L[2].n_g2id_fail++;
                L[2].hg1[g1_59]++; L[2].hh[h_59]++;
                /* round 60 */
                if(g1_60==0)L[3].ng1++; if(h_60==0)L[3].nh++; if(g2_60==0)L[3].ng2++;
                if(g1_60==0&&h_60==0)L[3].nboth++; if(((g1_60+h_60)&MASK)!=g2_60)L[3].n_g2id_fail++;
                L[3].hg1[g1_60]++; L[3].hh[h_60]++;

                uint32_t W1_62=(fns1(w60)+sc62_1)&MASK,W2_62=(fns1(w60b)+sc62_2)&MASK;
                sha_round(a1,KN[62],W1_62);sha_round(b1,KN[62],W2_62);
                sha_round(a1,KN[63],W1_63);sha_round(b1,KN[63],W2_63);
                int ok=1;for(int r=0;r<8;r++)if(a1[r]!=b1[r]){ok=0;break;}
                if(ok&&lci<400000){lc[lci].w57=w57;lc[lci].w58=w58;lc[lci].w59=w59;lc[lci].w60=w60;
                    lc[lci].w57b=w57b;lc[lci].w58b=w58b;lc[lci].w59b=w59b;lc[lci].w60b=w60b;
                    lc[lci].casoff=casoff;lci++;lnc++;}
            }
          }
        }
      }
      #pragma omp critical
      {
        for(uint64_t i=0;i<lci&&nc<4000000;i++)colls[nc++]=lc[i];
        ntrip+=lt;nde61+=lh;
        for(int i=0;i<4;i++) for(uint32_t v=0;v<=MASK;v++) de_img[i][v]+=lde[i][v];
        for(int k=0;k<NR;k++){ G[k].ng1+=L[k].ng1;G[k].nh+=L[k].nh;G[k].ng2+=L[k].ng2;
            G[k].nboth+=L[k].nboth;G[k].n_g2id_fail+=L[k].n_g2id_fail;
            for(uint32_t v=0;v<=MASK;v++){G[k].hg1[v]+=L[k].hg1[v];G[k].hh[v]+=L[k].hh[v];} }
      }
      free(lc);for(int i=0;i<4;i++)free(lde[i]);
      for(int k=0;k<NR;k++){free(L[k].hg1);free(L[k].hh);}
    }

    /* ---- de-image report (which de_r vary?) ---- */
    printf("\n--- de-image sizes over the free-word sweep (memo: only de58 varies) ---\n");
    const char*den[4]={"de57","de58","de59","de60"};
    for(int i=0;i<4;i++){ uint64_t nz=0,mx=0; uint32_t arg=0;
        for(uint32_t v=0;v<=MASK;v++){ if(de_img[i][v]){nz++; if(de_img[i][v]>mx){mx=de_img[i][v];arg=v;}} }
        printf("  %s: image-size=%llu  (most common diff=0x%x)\n",den[i],(unsigned long long)nz,arg);
    }

    /* ---- per-round marginal-step report over de61=0 hits (HUGE stats) ---- */
    printf("\n--- PER-ROUND marginal sr-step cost over %llu de61=0 hits ---\n",(unsigned long long)nde61);
    printf("  round | sr-step      | P(g1=0)   | P(h=0)    | P(both)    | indep ratio | g2=g1+h fails\n");
    printf("  ------|--------------|-----------|-----------|------------|-------------|--------------\n");
    const char*step[4]={"sr63->64","sr62->63","sr61->62","sr60->61"};
    double uni=1.0/(MASK+1);
    for(int k=0;k<NR;k++){
        double pg1=(double)G[k].ng1/nde61, ph=(double)G[k].nh/nde61, pb=(double)G[k].nboth/nde61;
        double ratio=(pg1*ph>0)?pb/(pg1*ph):0.0;
        printf("  W[%d] | %-12s | %.6f | %.6f | %.8f | %11.4f | %llu\n",
            RND[k],step[k],pg1,ph,pb,ratio,(unsigned long long)G[k].n_g2id_fail);
    }
    printf("  (uniform 2^-N = %.6f;  2^-2N = %.8f;  ratio~1 => g1,h INDEPENDENT => step is 2^-2N)\n",
        uni, uni*uni);

    /* ---- per-round histogram peak (non-uniformity gauge) ---- */
    printf("\n--- per-round uniformity of g1,h over de61=0 hits (max-bin/mean; ~1 => uniform) ---\n");
    for(int k=0;k<NR;k++){
        uint64_t mg=0,mh=0; for(uint32_t v=0;v<=MASK;v++){if(G[k].hg1[v]>mg)mg=G[k].hg1[v];if(G[k].hh[v]>mh)mh=G[k].hh[v];}
        double mean=(double)nde61/(MASK+1);
        printf("  W[%d]: g1 max/mean=%.2f   h max/mean=%.2f\n",RND[k],(double)mg/mean,(double)mh/mean);
    }

    /* ---- per-round marginal counts over the GENUINE sr=60 collision set ---- */
    printf("\n--- PER-ROUND marginal step over the %llu genuine sr=60 collisions ---\n",(unsigned long long)nc);
    printf("  round | g1=0 | h=0 | g2=0 | BOTH(=sr-step) | exp@2^-N | exp@2^-2N\n");
    for(int k=0;k<NR;k++){
        uint64_t cg1=0,ch=0,cg2=0,cb=0;
        for(uint64_t i=0;i<nc;i++){
            coll_t*c=&colls[i];
            uint32_t W1r,W2r,sc1,sc2,casr;
            if(RND[k]==57){W1r=c->w57;W2r=c->w57b;sc1=sched_r(57,W1p,W1p[55]);sc2=sched_r(57,W2p,W2p[55]);}
            else if(RND[k]==58){W1r=c->w58;W2r=c->w58b;sc1=sched_r(58,W1p,W1p[56]);sc2=sched_r(58,W2p,W2p[56]);}
            else if(RND[k]==59){W1r=c->w59;W2r=c->w59b;sc1=sched_r(59,W1p,c->w57);sc2=sched_r(59,W2p,c->w57b);}
            else {W1r=c->w60;W2r=c->w60b;sc1=sched_r(60,W1p,c->w58);sc2=sched_r(60,W2p,c->w58b);}
            casr=(W2r-W1r)&MASK;
            uint32_t g1=(W1r-sc1)&MASK,g2=(W2r-sc2)&MASK,hh=(casr-((sc2-sc1)&MASK))&MASK;
            if(g1==0)cg1++; if(hh==0)ch++; if(g2==0)cg2++; if(g1==0&&hh==0)cb++;
        }
        double e1=(double)nc/(MASK+1), e2=(double)nc/((double)(MASK+1)*(MASK+1));
        printf("  W[%d] | %4llu | %3llu | %4llu | %14llu | %8.4f | %.6f\n",
            RND[k],(unsigned long long)cg1,(unsigned long long)ch,(unsigned long long)cg2,
            (unsigned long long)cb,e1,e2);
    }

    /* ---- de58-coupling test for r=58: is P(g1(58)=0) independent of the de58 bucket? ----
       We recompute over the collision set: stratify g1(58)==0 by de58 value of each collision. */
    printf("\n--- ROUND-58 / de58 coupling: does forcing W[58] interact with the de58 freedom? ---\n");
    {
        /* over the collision set, compute de58 per collision and stratify g1(58),h(58). */
        /* de58 for a collision = e-diff after round 58 given its (w57,w58). recompute. */
        uint64_t *byde_n=calloc(MASK+1,sizeof(uint64_t));
        uint64_t *byde_g1=calloc(MASK+1,sizeof(uint64_t));
        uint64_t *byde_h=calloc(MASK+1,sizeof(uint64_t));
        uint32_t sc1=sched_r(58,W1p,W1p[56]), sc2=sched_r(58,W2p,W2p[56]);
        for(uint64_t i=0;i<nc;i++){
            coll_t*c=&colls[i];
            uint32_t sa[8],sb[8];memcpy(sa,state1,32);memcpy(sb,state2,32);
            sha_round(sa,KN[57],c->w57);sha_round(sb,KN[57],c->w57b);
            sha_round(sa,KN[58],c->w58);sha_round(sb,KN[58],c->w58b);
            uint32_t de58=(sa[4]-sb[4])&MASK;
            uint32_t g1=(c->w58-sc1)&MASK, hh=(((c->w58b-c->w58)&MASK)-((sc2-sc1)&MASK))&MASK;
            byde_n[de58]++; if(g1==0)byde_g1[de58]++; if(hh==0)byde_h[de58]++;
        }
        int nb=0; for(uint32_t v=0;v<=MASK;v++) if(byde_n[v]) nb++;
        printf("  de58 takes %d distinct values over the collisions; per-bucket g1(58)=0 / h(58)=0 counts:\n",nb);
        int shown=0;
        for(uint32_t v=0;v<=MASK&&shown<16;v++) if(byde_n[v]){
            printf("    de58=0x%-4x : n=%-5llu  g1=0:%-4llu  h=0:%-4llu\n",
                v,(unsigned long long)byde_n[v],(unsigned long long)byde_g1[v],(unsigned long long)byde_h[v]);
            shown++;
        }
        free(byde_n);free(byde_g1);free(byde_h);
    }

    printf("\ntriples=%llu  de61=0 hits=%llu  sr60 collisions=%llu\n",
        (unsigned long long)ntrip,(unsigned long long)nde61,(unsigned long long)nc);

    for(int i=0;i<4;i++)free(de_img[i]);
    for(int k=0;k<NR;k++){free(G[k].hg1);free(G[k].hh);}
    free(colls);
    return 0;
}
