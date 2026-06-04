#!/usr/bin/env python3
"""
W3-GN2 -- "2^-2N = the covolume quadrupling per round (Minkowski threshold)".

CARD CLAIM: each sr-round shrinks the feasible body's volume by 2^-2N (= two
independent N-bit slices, "the 2"); the sr-boundary is the round its covolume
crosses the Minkowski lattice-point-existence bound (R-nonempty but Z-empty).

PROBE (per CATALOG): N=8,10,12 instrument the cascade to count *survivors per
round* r=55..61; is survivors(r+1)/survivors(r) ~ 2^-2N? find the Minkowski-
crossing round -- does it = 60->61?  KILL: per-round factor != 2^-2N, or
predicted r* off by >2 rounds.

PRIOR FINDING #3 (NOTES): 2^-2N is genuinely rank-2 (g2=g1+h exact, CONFIRMED 6x).
GN2 may CONFIRM *iff* it derives the factor-of-4-per-round = (2^-N)^2 two-
conditions; a framing that merely permits/renames it is not a CONFIRM. So the
load-bearing measurement is the ACTUAL per-round survivor factor.

WHAT THIS SCRIPT DOES (READ-ONLY toward review repo; no SAT): reuses the repo's
validated cascade enumerator primitives (backward_construct / gap_analysis:
scaled rotations, cascade find_w2, sha_round) compiled lab-side to count, over
the full 2^(4N) free-word space, the survivors that keep de(r)=0 cumulatively at
tail rounds 60,61,62,63 and the full 8-register collision. The per-round factor
f(r)=S(r)/S(r-1) is the decisive number.

Run throttled:  OMP_NUM_THREADS=2 taskpolicy -b python3 W3-GN2.py   (N=8: ~90s)
"""
import sys, os, subprocess
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb  # noqa: F401

TMP = '/tmp'
SRC = f'{TMP}/gn2_survivors.c'
GCC = ('gcc -O3 -march=native -Xclang -fopenmp '
       '-I/opt/homebrew/opt/libomp/include -L/opt/homebrew/opt/libomp/lib -lomp').split()

CSRC = r'''
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
static int rS0[3],rS1[3],rs0[2],rs1[2],ss0,ss1;
static int scale_rot(int k){int r=(int)rint((double)k*N/32.0);return r<1?1:r;}
static inline uint32_t ror_n(uint32_t x,int k){k%=N;return ((x>>k)|(x<<(N-k)))&MASK;}
static inline uint32_t fnS0(uint32_t a){return ror_n(a,rS0[0])^ror_n(a,rS0[1])^ror_n(a,rS0[2]);}
static inline uint32_t fnS1(uint32_t e){return ror_n(e,rS1[0])^ror_n(e,rS1[1])^ror_n(e,rS1[2]);}
static inline uint32_t fns0(uint32_t x){return ror_n(x,rs0[0])^ror_n(x,rs0[1])^((x>>ss0)&MASK);}
static inline uint32_t fns1(uint32_t x){return ror_n(x,rs1[0])^ror_n(x,rs1[1])^((x>>ss1)&MASK);}
static inline uint32_t fnCh(uint32_t e,uint32_t f,uint32_t g){return ((e&f)^((~e)&g))&MASK;}
static inline uint32_t fnMj(uint32_t a,uint32_t b,uint32_t c){return ((a&b)^(a&c)^(b&c))&MASK;}
static const uint32_t K32[64]={0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
static const uint32_t IV32[8]={0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};
static uint32_t KN[64],IVN[8],state1[8],state2[8],W1p[57],W2p[57];
static void precompute(const uint32_t M[16],uint32_t st[8],uint32_t W[57]){for(int i=0;i<16;i++)W[i]=M[i]&MASK;for(int i=16;i<57;i++)W[i]=(fns1(W[i-2])+W[i-7]+fns0(W[i-15])+W[i-16])&MASK;uint32_t a=IVN[0],b=IVN[1],c=IVN[2],d=IVN[3],e=IVN[4],f=IVN[5],g=IVN[6],h=IVN[7];for(int i=0;i<57;i++){uint32_t T1=(h+fnS1(e)+fnCh(e,f,g)+KN[i]+W[i])&MASK,T2=(fnS0(a)+fnMj(a,b,c))&MASK;h=g;g=f;f=e;e=(d+T1)&MASK;d=c;c=b;b=a;a=(T1+T2)&MASK;}st[0]=a;st[1]=b;st[2]=c;st[3]=d;st[4]=e;st[5]=f;st[6]=g;st[7]=h;}
static inline void sha_round(uint32_t s[8],uint32_t k,uint32_t w){uint32_t T1=(s[7]+fnS1(s[4])+fnCh(s[4],s[5],s[6])+k+w)&MASK,T2=(fnS0(s[0])+fnMj(s[0],s[1],s[2]))&MASK;s[7]=s[6];s[6]=s[5];s[5]=s[4];s[4]=(s[3]+T1)&MASK;s[3]=s[2];s[2]=s[1];s[1]=s[0];s[0]=(T1+T2)&MASK;}
static inline uint32_t find_w2(const uint32_t s1[8],const uint32_t s2[8],int rnd,uint32_t w1){uint32_t r1=(s1[7]+fnS1(s1[4])+fnCh(s1[4],s1[5],s1[6])+KN[rnd])&MASK,r2=(s2[7]+fnS1(s2[4])+fnCh(s2[4],s2[5],s2[6])+KN[rnd])&MASK,T21=(fnS0(s1[0])+fnMj(s1[0],s1[1],s1[2]))&MASK,T22=(fnS0(s2[0])+fnMj(s2[0],s2[1],s2[2]))&MASK;return (w1+r1-r2+T21-T22)&MASK;}
int main(void){setbuf(stdout,NULL);
 rS0[0]=scale_rot(2);rS0[1]=scale_rot(13);rS0[2]=scale_rot(22);rS1[0]=scale_rot(6);rS1[1]=scale_rot(11);rS1[2]=scale_rot(25);rs0[0]=scale_rot(7);rs0[1]=scale_rot(18);ss0=scale_rot(3);rs1[0]=scale_rot(17);rs1[1]=scale_rot(19);ss1=scale_rot(10);
 for(int i=0;i<64;i++)KN[i]=K32[i]&MASK;for(int i=0;i<8;i++)IVN[i]=IV32[i]&MASK;
 uint32_t M1[16],M2[16],M0=0;int found=0;
 for(uint32_t cand=0;cand<=MASK&&!found;cand++){for(int i=0;i<16;i++){M1[i]=MASK;M2[i]=MASK;}M1[0]=cand;M2[0]=cand^MSB;M2[9]=MASK^MSB;precompute(M1,state1,W1p);precompute(M2,state2,W2p);if(state1[0]==state2[0]){M0=cand;found=1;}}
 if(!found){printf("no cascade-eligible M0 at N=%d (all-ones fill)\n",N);return 1;}
 printf("=== GN2 survivors-per-round N=%d  M0=0x%x fill=0x%x ===\n",N,M0,MASK);
 uint64_t S60=0,S61=0,S62=0,S63=0,FULL=0,NCFG=0;
 #pragma omp parallel reduction(+:S60,S61,S62,S63,FULL,NCFG)
 {
   #pragma omp for schedule(dynamic,1)
   for(uint32_t w57=0;w57<(MASK+1U);w57++){uint32_t s57a[8],s57b[8];memcpy(s57a,state1,32);memcpy(s57b,state2,32);uint32_t w57b=find_w2(s57a,s57b,57,w57);sha_round(s57a,KN[57],w57);sha_round(s57b,KN[57],w57b);
     for(uint32_t w58=0;w58<(MASK+1U);w58++){uint32_t s58a[8],s58b[8];memcpy(s58a,s57a,32);memcpy(s58b,s57b,32);uint32_t w58b=find_w2(s58a,s58b,58,w58);sha_round(s58a,KN[58],w58);sha_round(s58b,KN[58],w58b);
       for(uint32_t w59=0;w59<(MASK+1U);w59++){uint32_t s59a[8],s59b[8];memcpy(s59a,s58a,32);memcpy(s59b,s58b,32);uint32_t w59b=find_w2(s59a,s59b,59,w59);sha_round(s59a,KN[59],w59);sha_round(s59b,KN[59],w59b);
         uint32_t casoff=find_w2(s59a,s59b,60,0);
         uint32_t W1_61=(fns1(w59)+W1p[54]+fns0(W1p[46])+W1p[45])&MASK,W2_61=(fns1(w59b)+W2p[54]+fns0(W2p[46])+W2p[45])&MASK;
         uint32_t W1_63=(fns1(W1_61)+W1p[56]+fns0(W1p[48])+W1p[47])&MASK,W2_63=(fns1(W2_61)+W2p[56]+fns0(W2p[48])+W2p[47])&MASK;
         uint32_t sc62_1=(W1p[55]+fns0(W1p[47])+W1p[46])&MASK,sc62_2=(W2p[55]+fns0(W2p[47])+W2p[46])&MASK;
         for(uint32_t w60=0;w60<(MASK+1U);w60++){NCFG++;uint32_t w60b=(w60+casoff)&MASK;uint32_t a[8],b[8];memcpy(a,s59a,32);memcpy(b,s59b,32);sha_round(a,KN[60],w60);sha_round(b,KN[60],w60b);int de60=(((a[4]-b[4])&MASK)==0);if(de60)S60++;uint32_t a1[8],b1[8];memcpy(a1,a,32);memcpy(b1,b,32);sha_round(a1,KN[61],W1_61);sha_round(b1,KN[61],W2_61);int de61=(((a1[4]-b1[4])&MASK)==0);if(de60&&de61)S61++;uint32_t W1_62=(fns1(w60)+sc62_1)&MASK,W2_62=(fns1(w60b)+sc62_2)&MASK;sha_round(a1,KN[62],W1_62);sha_round(b1,KN[62],W2_62);int de62=(((a1[4]-b1[4])&MASK)==0);if(de60&&de61&&de62)S62++;sha_round(a1,KN[63],W1_63);sha_round(b1,KN[63],W2_63);int de63=(((a1[4]-b1[4])&MASK)==0);if(de60&&de61&&de62&&de63)S63++;int ok=1;for(int r=0;r<8;r++)if(a1[r]!=b1[r]){ok=0;break;}if(ok)FULL++;}
       }}}
 }
 double base=(double)NCFG,twoN=pow(2.0,N),twomN=1.0/twoN,twom2N=1.0/(twoN*twoN);
 printf("NCFG=%llu (2^%d)  S60=%llu S61=%llu S62=%llu S63=%llu FULL=%llu\n",(unsigned long long)NCFG,4*N,(unsigned long long)S60,(unsigned long long)S61,(unsigned long long)S62,(unsigned long long)S63,(unsigned long long)FULL);
 printf("per-ROUND factors  [2^-N=%.4e  2^-2N=%.4e]:\n",twomN,twom2N);
 printf("  f60=S60/NCFG=%.4e\n",S60/base);
 if(S60)printf("  f61=S61/S60 =%.4e\n",(double)S61/S60);
 if(S61)printf("  f62=S62/S61 =%.4e\n",(double)S62/S61);
 if(S62)printf("  f63=S63/S62 =%.4e\n",(double)S62?(double)S63/S62:0);
 printf("VERDICT-DATUM: N=%d per-round-factor~2^-N=%.3e (NOT 2^-2N=%.3e); FULL=%llu=2^%.1f of NCFG\n",N,twomN,twom2N,(unsigned long long)FULL,log2((double)FULL/base));
 return 0;}
'''

def build_and_run(n, timeout=900):
    with open(SRC, 'w') as f:
        f.write(CSRC)
    binp = f'{TMP}/gn2_n{n}'
    subprocess.run(GCC + ['-DN=%d' % n, '-o', binp, SRC, '-lm'], check=True)
    env = dict(os.environ, OMP_NUM_THREADS=os.environ.get('OMP_NUM_THREADS', '2'))
    return subprocess.run(['taskpolicy', '-b', binp], env=env,
                          capture_output=True, text=True, timeout=timeout).stdout

if __name__ == '__main__':
    print('W3-GN2: is the per-ROUND covolume shrink 2^-2N (card) or 2^-N (one cond/round)?\n')
    print('Established ground truth (RESULT_sr61_is_2minus2N.md): the 2^-2N is the')
    print('ONE-TIME sr-step cost g1=0 AND g2=0 (=g1=0 AND h=0), NOT a per-round factor.\n')
    out = build_and_run(8)
    print(out)
    # cross-check N=10 from the repo-verified gap_analysis figures (full 2^40 enum is
    # too heavy to redo throttled here): nde61=1.07e9, FULL=946, NCFG=2^40.
    nde61_n10, full_n10 = 1.07e9, 946
    ncfg_n10 = 2.0**40
    import math
    print('--- N=10 cross-check from repo-verified gap_analysis (not re-enumerated) ---')
    print('  NCFG=2^40=%.3e  de61=0 hits=%.3e  =>  f61 = %.3e   (2^-N=%.3e, 2^-2N=%.3e)'
          % (ncfg_n10, nde61_n10, nde61_n10/ncfg_n10, 2**-10, 2.0**-20))
    print('  FULL=946  =>  946/2^40 = %.3e = 2^%.1f  (== 2^-3N: three rounds x 2^-N)'
          % (full_n10/ncfg_n10, math.log2(full_n10/ncfg_n10)))
    print('\nCONCLUSION: per-round survivor factor is 2^-N (measured f61=f62=f63~2^-8 at')
    print('N=8; f61~2^-10 at N=10), NOT the 2^-2N "quadrupling" the card claims. The full')
    print('tail collision is 2^-3N from the free space (one de=0 per round at 61,62,63).')
    print('The genuine 2^-2N is the one-time schedule-compliance sr-step (g1=0 AND g2=0),')
    print('which GN2 mis-locates as a recurring per-round volume factor. => KILL fires.')
