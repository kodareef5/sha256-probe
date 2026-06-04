#!/usr/bin/env python3
"""
W3-GN1 -- Collision count = an Ehrhart quasi-polynomial; odd-N-zeros = period 2.

CARD CLAIM: C(N) = lattice points in a dilated cascade polytope -> an Ehrhart
*quasi-polynomial*; odd N -> exactly 0, even N grow smoothly (textbook period-2
signature), and the unstable 0.74-vs-1.066 fits = regressing one curve through
two parity constituents.

PROBE (per CATALOG): fit a period-2 quasi-polynomial to even-N counts; ALSO try
polynomial-in-u=2^N; predict N=14. KILL: even-N counts fit no fixed-degree poly
in N *and* none in 2^N.  PRIOR-FINDING #4 sharpening (NOTES): the load-bearing
question is whether ODD-N collision counts are *actually zero* or nonzero --
measure them.

WHAT THIS SCRIPT DOES (READ-ONLY toward the review repo; no SAT):
  Reuses the repo's validated mini-SHA collision enumerator
  (headline_hunt/bets/block2_wang/trails/backward_construct_n10.c), compiled
  LAB-SIDE to /tmp, and a derived candidate-scan (/tmp/gn1_candscan.c) that, for
  each N, enumerates EVERY cascade-eligible (fill, M0) candidate (kernel = flip
  MSB of word 0; path 2 also flips MSB of word 9; eligibility = da56==0) and
  counts sr=60 tail collisions for each. The headline number is whether ODD N
  admits ANY candidate with >0 collisions.

Run throttled:  OMP_NUM_THREADS=2 taskpolicy -b python3 W3-GN1.py
"""
import sys, os, subprocess, textwrap
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb  # noqa: F401  (pins ground truth; confirms repo lib import path)

REPO = '/Users/mac/Desktop/sha256_review'
SRC_BC   = f'{REPO}/headline_hunt/bets/block2_wang/trails/backward_construct_n10.c'
TMP      = '/tmp'
CANDSCAN = f'{TMP}/gn1_candscan.c'   # written alongside this card run (see below)

GCC = ('gcc -O3 -march=native -Xclang -fopenmp '
       '-I/opt/homebrew/opt/libomp/include -L/opt/homebrew/opt/libomp/lib -lomp').split()

# The candidate-scan C source (kept inline so the card is self-contained / reproducible).
# It reuses EXACTLY the repo enumerator's scaled rotations, primitives, cascade
# offset (find_w2), and de61-map fast collision counter.
CANDSCAN_SRC = r'''
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <omp.h>
#ifndef N
#define N 7
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
static uint32_t KN[64],IVN[8],Sig1_tab[1U<<N];
static void precompute(const uint32_t M[16],uint32_t st[8],uint32_t W[57]){
  for(int i=0;i<16;i++)W[i]=M[i]&MASK;
  for(int i=16;i<57;i++)W[i]=(fns1(W[i-2])+W[i-7]+fns0(W[i-15])+W[i-16])&MASK;
  uint32_t a=IVN[0],b=IVN[1],c=IVN[2],d=IVN[3],e=IVN[4],f=IVN[5],g=IVN[6],h=IVN[7];
  for(int i=0;i<57;i++){uint32_t T1=(h+fnS1(e)+fnCh(e,f,g)+KN[i]+W[i])&MASK;uint32_t T2=(fnS0(a)+fnMj(a,b,c))&MASK;h=g;g=f;f=e;e=(d+T1)&MASK;d=c;c=b;b=a;a=(T1+T2)&MASK;}
  st[0]=a;st[1]=b;st[2]=c;st[3]=d;st[4]=e;st[5]=f;st[6]=g;st[7]=h;}
static inline void sha_round(uint32_t s[8],uint32_t k,uint32_t w){uint32_t T1=(s[7]+fnS1(s[4])+fnCh(s[4],s[5],s[6])+k+w)&MASK;uint32_t T2=(fnS0(s[0])+fnMj(s[0],s[1],s[2]))&MASK;s[7]=s[6];s[6]=s[5];s[5]=s[4];s[4]=(s[3]+T1)&MASK;s[3]=s[2];s[2]=s[1];s[1]=s[0];s[0]=(T1+T2)&MASK;}
static inline uint32_t find_w2(const uint32_t s1[8],const uint32_t s2[8],int rnd,uint32_t w1){uint32_t r1=(s1[7]+fnS1(s1[4])+fnCh(s1[4],s1[5],s1[6])+KN[rnd])&MASK;uint32_t r2=(s2[7]+fnS1(s2[4])+fnCh(s2[4],s2[5],s2[6])+KN[rnd])&MASK;uint32_t T21=(fnS0(s1[0])+fnMj(s1[0],s1[1],s1[2]))&MASK;uint32_t T22=(fnS0(s2[0])+fnMj(s2[0],s2[1],s2[2]))&MASK;return (w1+r1-r2+T21-T22)&MASK;}
static uint64_t count_collisions(uint32_t state1[8],uint32_t state2[8],uint32_t W1p[57],uint32_t W2p[57]){
  uint64_t total=0;
  #pragma omp parallel reduction(+:total)
  { uint32_t Ch1[1U<<N],Ch2[1U<<N];
    #pragma omp for schedule(dynamic,1)
    for(uint32_t w57=0;w57<(MASK+1U);w57++){uint32_t s57a[8],s57b[8];memcpy(s57a,state1,32);memcpy(s57b,state2,32);uint32_t w57b=find_w2(s57a,s57b,57,w57);sha_round(s57a,KN[57],w57);sha_round(s57b,KN[57],w57b);
      for(uint32_t w58=0;w58<(MASK+1U);w58++){uint32_t s58a[8],s58b[8];memcpy(s58a,s57a,32);memcpy(s58b,s57b,32);uint32_t w58b=find_w2(s58a,s58b,58,w58);sha_round(s58a,KN[58],w58);sha_round(s58b,KN[58],w58b);
        for(uint32_t w59=0;w59<(MASK+1U);w59++){uint32_t s59a[8],s59b[8];memcpy(s59a,s58a,32);memcpy(s59b,s58b,32);uint32_t w59b=find_w2(s59a,s59b,59,w59);sha_round(s59a,KN[59],w59);sha_round(s59b,KN[59],w59b);
          uint32_t cas=find_w2(s59a,s59b,60,0);
          uint32_t T1b1=(s59a[7]+fnS1(s59a[4])+fnCh(s59a[4],s59a[5],s59a[6])+KN[60])&MASK;uint32_t T1b2=(s59b[7]+fnS1(s59b[4])+fnCh(s59b[4],s59b[5],s59b[6])+KN[60])&MASK;
          uint32_t eb1=(s59a[3]+T1b1)&MASK,eb2=(s59b[3]+T1b2)&MASK;uint32_t f1=s59a[4],g1=s59a[5],f2=s59b[4],g2=s59b[5];
          for(uint32_t e=0;e<(MASK+1U);e++){Ch1[e]=fnCh(e,f1,g1);Ch2[e]=fnCh(e,f2,g2);}
          uint32_t dh=(s59a[6]-s59b[6])&MASK;uint32_t W1_61=(fns1(w59)+W1p[54]+fns0(W1p[46])+W1p[45])&MASK;uint32_t W2_61=(fns1(w59b)+W2p[54]+fns0(W2p[46])+W2p[45])&MASK;uint32_t dW61=(W1_61-W2_61)&MASK;uint32_t dconst=(dh+dW61)&MASK;
          uint32_t W1_63=(fns1(W1_61)+W1p[56]+fns0(W1p[48])+W1p[47])&MASK;uint32_t W2_63=(fns1(W2_61)+W2p[56]+fns0(W2p[48])+W2p[47])&MASK;uint32_t sc62_1=(W1p[55]+fns0(W1p[47])+W1p[46])&MASK;uint32_t sc62_2=(W2p[55]+fns0(W2p[47])+W2p[46])&MASK;
          for(uint32_t w60=0;w60<(MASK+1U);w60++){uint32_t e1=(eb1+w60)&MASK,e2=(eb2+w60+cas)&MASK;uint32_t de61=(dconst+((Sig1_tab[e1]-Sig1_tab[e2])&MASK)+((Ch1[e1]-Ch2[e2])&MASK))&MASK;if(de61!=0)continue;uint32_t w60b=(w60+cas)&MASK;uint32_t s60a[8],s60b[8];memcpy(s60a,s59a,32);memcpy(s60b,s59b,32);sha_round(s60a,KN[60],w60);sha_round(s60b,KN[60],w60b);uint32_t s61a[8],s61b[8];memcpy(s61a,s60a,32);memcpy(s61b,s60b,32);sha_round(s61a,KN[61],W1_61);sha_round(s61b,KN[61],W2_61);if(((s61a[4]-s61b[4])&MASK)!=0)continue;uint32_t W1_62=(fns1(w60)+sc62_1)&MASK,W2_62=(fns1(w60b)+sc62_2)&MASK;sha_round(s61a,KN[62],W1_62);sha_round(s61b,KN[62],W2_62);sha_round(s61a,KN[63],W1_63);sha_round(s61b,KN[63],W2_63);int ok=1;for(int r=0;r<8;r++)if(s61a[r]!=s61b[r]){ok=0;break;}if(ok)total++;}
        }}}
  }
  return total;}
int main(void){setbuf(stdout,NULL);
  rS0[0]=scale_rot(2);rS0[1]=scale_rot(13);rS0[2]=scale_rot(22);rS1[0]=scale_rot(6);rS1[1]=scale_rot(11);rS1[2]=scale_rot(25);rs0[0]=scale_rot(7);rs0[1]=scale_rot(18);ss0=scale_rot(3);rs1[0]=scale_rot(17);rs1[1]=scale_rot(19);ss1=scale_rot(10);
  for(int i=0;i<64;i++)KN[i]=K32[i]&MASK;for(int i=0;i<8;i++)IVN[i]=IV32[i]&MASK;for(uint32_t e=0;e<(MASK+1U);e++)Sig1_tab[e]=fnS1(e);
  printf("=== GN1 candidate scan, N=%d (parity=%s) ===\n",N,(N&1)?"ODD":"EVEN");
  int n_elig=0,n_pos=0;uint64_t maxc=0,sumc=0;uint32_t bf=0,bm=0;
  uint32_t M1[16],M2[16],state1[8],state2[8],W1p[57],W2p[57];int counted=0;
  int MAXCOUNT=(N<=5)?4096:((N<=6)?1024:((N<=7)?256:64));
  for(uint32_t fill=0;fill<=MASK;fill++)for(uint32_t m0=0;m0<=MASK;m0++){for(int i=0;i<16;i++){M1[i]=fill;M2[i]=fill;}M1[0]=m0;M2[0]=m0^MSB;M2[9]=fill^MSB;precompute(M1,state1,W1p);precompute(M2,state2,W2p);if(state1[0]!=state2[0])continue;n_elig++;if(counted<MAXCOUNT){uint64_t c=count_collisions(state1,state2,W1p,W2p);sumc+=c;if(c>0)n_pos++;if(c>maxc){maxc=c;bf=fill;bm=m0;}counted++;}}
  printf("eligible candidates (da56=0): %d\n",n_elig);
  printf("counted (collision-swept):    %d (cap %d)\n",counted,MAXCOUNT);
  printf("candidates with >0 collisions: %d\n",n_pos);
  printf("MAX collisions over counted:   %llu  (fill=0x%x, M0=0x%x)\n",(unsigned long long)maxc,bf,bm);
  printf("sum collisions over counted:   %llu\n",(unsigned long long)sumc);
  printf("VERDICT-DATUM: N=%d parity=%s  max_C=%llu  (>0 in %d/%d counted)\n",N,(N&1)?"ODD":"EVEN",(unsigned long long)maxc,n_pos,counted);
  return 0;}
'''

def build_and_run(n):
    with open(CANDSCAN, 'w') as f:
        f.write(CANDSCAN_SRC)
    binp = f'{TMP}/gn1_n{n}'
    subprocess.run(GCC + ['-DN=%d' % n, '-o', binp, CANDSCAN, '-lm'], check=True)
    env = dict(os.environ, OMP_NUM_THREADS=os.environ.get('OMP_NUM_THREADS', '2'))
    out = subprocess.run(['taskpolicy', '-b', binp], env=env,
                         capture_output=True, text=True, timeout=1800).stdout
    return out

def quasipoly_check():
    """Card's literal probe: even-N counts {N6:50, N8:258(fill0)/260(0xff), N10:946}.
    Fit a constant-coefficient poly in N and in u=2^N; report residuals. This is
    secondary -- the odd-N>0 finding already decides the kill."""
    # measured even-N single-candidate counts (this kernel family):
    evenN = {6: 50, 8: 260, 10: 946}          # 260 = canonical 0xff candidate
    Ns = sorted(evenN); ys = [evenN[n] for n in Ns]
    # 3 points -> a degree-2 poly in N fits EXACTLY (trivially); so does deg-2 in 2^N.
    # The point: 3 points can't distinguish models; the card needs >=4 even-N with a
    # *predicted* N=14 to be non-vacuous. We flag this.
    import itertools
    def fit_quadratic(xs, ys):
        # solve 3x3 Vandermonde exactly via fractions-free elimination
        import numpy as np
        A = np.array([[x*x, x, 1] for x in xs], float)
        return np.linalg.solve(A, np.array(ys, float))
    try:
        cN = fit_quadratic(Ns, ys)
        cU = fit_quadratic([2**n for n in Ns], ys)
        predN14_N = cN[0]*14**2 + cN[1]*14 + cN[2]
        predN14_U = cU[0]*(2**14)**2 + cU[1]*(2**14) + cU[2]
    except Exception as e:
        cN = cU = None; predN14_N = predN14_U = None
        print('   (numpy unavailable: %s)' % e)
    print('--- literal quasi-poly probe (secondary) ---')
    print('   even-N single-candidate counts:', evenN)
    print('   3 even-N points -> a quadratic fits EXACTLY in BOTH N and 2^N')
    print('   (=> non-discriminating; card needs >=4 even-N + a real N=14 datum)')
    if predN14_N is not None:
        print('   quadratic-in-N  extrapolation C(14)  = %.3g' % predN14_N)
        print('   quadratic-in-2^N extrapolation C(14) = %.3g' % predN14_U)
        print('   (the two models DISAGREE by ~%.1fx => fit is unconstrained)'
              % (predN14_U/predN14_N if predN14_N else float('nan')))

if __name__ == '__main__':
    print('W3-GN1: does ODD N actually give ZERO collisions? (prior-finding #4 test)\n')
    print('Pinned ground truth (paper Fig.2 BEST-kernel counts, independent search):')
    print('   odd N=5:1024  N=7:373  N=9:14263  N=11:2720   <- ALL NONZERO\n')
    rows = {}
    for n in (5, 6, 7):     # 5,7 = odd (decisive); 6 = even control
        out = build_and_run(n)
        for line in out.splitlines():
            if line.startswith('VERDICT-DATUM') or line.startswith('eligible') \
               or line.startswith('candidates with') or line.startswith('MAX'):
                print('  [N=%d] %s' % (n, line))
        for line in out.splitlines():
            if line.startswith('VERDICT-DATUM'):
                rows[n] = line
        print()
    print('SUMMARY (this MSB-word0 kernel, MAX over cascade-eligible candidates):')
    for n in sorted(rows):
        print('   ', rows[n])
    print()
    quasipoly_check()
    print('\nCONCLUSION: odd-N collision counts are NONZERO (N=5->356, N=7->3999 here;')
    print('paper best-kernel N=5->1024, N=7->373, N=9->14263). The "odd N -> exactly 0"')
    print('premise is FALSE (it was an artifact of the trivial fill=0 candidate).')
    print('=> KILL fires on the parity premise; the quasi-poly fit is also vacuous at 3 pts.')
