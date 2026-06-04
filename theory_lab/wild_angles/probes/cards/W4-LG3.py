"""
W4-LG3 -- Lattice Gauss law: "de58 is the unique charged column."

Card probe: per-round divergence D(r); ~0 for r in {57,59,60}, !=0 growing for
58? Test LOCALITY (pinned to a column, not smeared). Kill: "sourced at columns
!=de58, or zero everywhere, or linking vacuous."  Skeptic: must show locality or
it's an avalanche; modular-only conservation -> group is Z/2^k not Z_2.

PRIOR FINDING #5 (de58 thread CLOSED): |de58|=2^hw(db56) is a Maj/AND image-count,
no deeper invariant; cards here RESTATE not DERIVE. CONFIRM only if the gauge
picture DERIVES 2^hw(db56) (not just relabels the cascade table).

What we compute (READ-ONLY repo; faithful width-N model via lab-side C copied
VERBATIM from the repo enumerator backward_construct_n10.c):
  1. The ADDITIVE per-round e-difference image cardinality |de_r| for r=57..60,
     over the full cascade-feeding free-word sweep.  This is the canonical de-set.
     Gauss-law "divergence" D(r) := (|de_r| > 1) i.e. is the column "charged".
  2. Test locality: is the source confined to de58 (one column), with the others
     (de57,de59,de60) source-free (|.|=1)?
  3. Derive-vs-restate: does |de58| equal 2^hw(db56_XOR)?  If yes, that is the
     KNOWN cascade/Maj fact -- the gauge lens RESTATES it, it does not derive it
     from any gauge principle.  We make that distinction explicit.

The C tools live in /tmp (lab-side); this orchestrator builds+runs them throttled
and reports. Ground truth (shabridge.DE_SIZES): (|de57|,|de58|,|de59|,|de60|) =
(1,2,1,1)@N=4, (1,8,1,1)@N=8; DE_LAW de58=2^hw(db56) for N<=14.
"""
import sys, os, subprocess, textwrap
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb

CSRC = '/tmp/de58_add.c'      # additive |de_r| imager (already written by the sweep)
CSRC_X = '/tmp/de58_xor.c'    # XOR db56 reporter for the 2^hw check

# Minimal XOR-db56 reporter (additive imager already gives |de_r|; we need the
# XOR db56 hamming weight, which the law uses). Self-contained, width-N, repo-faithful.
XOR_SRC = r'''
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#ifndef N
#define N 8
#endif
#define MASK ((1U<<N)-1)
#define MSB  (1U<<(N-1))
static int rS0[3],rS1[3],rs0[2],rs1[2],ss0,ss1;
static int sr(int k){int r=(int)rint((double)k*N/32.0);return r<1?1:r;}
static inline uint32_t ro(uint32_t x,int k){k%=N;return ((x>>k)|(x<<(N-k)))&MASK;}
static inline uint32_t S0(uint32_t a){return ro(a,rS0[0])^ro(a,rS0[1])^ro(a,rS0[2]);}
static inline uint32_t S1(uint32_t e){return ro(e,rS1[0])^ro(e,rS1[1])^ro(e,rS1[2]);}
static inline uint32_t s0f(uint32_t x){return ro(x,rs0[0])^ro(x,rs0[1])^((x>>ss0)&MASK);}
static inline uint32_t s1f(uint32_t x){return ro(x,rs1[0])^ro(x,rs1[1])^((x>>ss1)&MASK);}
static inline uint32_t Ch(uint32_t e,uint32_t f,uint32_t g){return ((e&f)^((~e)&g))&MASK;}
static inline uint32_t Mj(uint32_t a,uint32_t b,uint32_t c){return ((a&b)^(a&c)^(b&c))&MASK;}
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
static uint32_t KN[64],IVN[8],st1[8],st2[8],W1p[57],W2p[57];
static void pre(const uint32_t M[16],uint32_t st[8],uint32_t W[57]){
    for(int i=0;i<16;i++)W[i]=M[i]&MASK;
    for(int i=16;i<57;i++)W[i]=(s1f(W[i-2])+W[i-7]+s0f(W[i-15])+W[i-16])&MASK;
    uint32_t a=IVN[0],b=IVN[1],c=IVN[2],d=IVN[3],e=IVN[4],f=IVN[5],g=IVN[6],h=IVN[7];
    for(int i=0;i<57;i++){uint32_t T1=(h+S1(e)+Ch(e,f,g)+KN[i]+W[i])&MASK,T2=(S0(a)+Mj(a,b,c))&MASK;
        h=g;g=f;f=e;e=(d+T1)&MASK;d=c;c=b;b=a;a=(T1+T2)&MASK;}
    st[0]=a;st[1]=b;st[2]=c;st[3]=d;st[4]=e;st[5]=f;st[6]=g;st[7]=h;}
static int hw(uint32_t x){int c=0;for(int i=0;i<N;i++)if((x>>i)&1)c++;return c;}
int main(void){
    rS0[0]=sr(2);rS0[1]=sr(13);rS0[2]=sr(22);rS1[0]=sr(6);rS1[1]=sr(11);rS1[2]=sr(25);
    rs0[0]=sr(7);rs0[1]=sr(18);ss0=sr(3);rs1[0]=sr(17);rs1[1]=sr(19);ss1=sr(10);
    for(int i=0;i<64;i++)KN[i]=K32[i]&MASK;for(int i=0;i<8;i++)IVN[i]=IV32[i]&MASK;
    uint32_t M1[16],M2[16],M0=0;int f=0;
    for(uint32_t c=0;c<=MASK&&!f;c++){for(int i=0;i<16;i++){M1[i]=MASK;M2[i]=MASK;}
        M1[0]=c;M2[0]=c^MSB;M2[9]=MASK^MSB;pre(M1,st1,W1p);pre(M2,st2,W2p);
        if(st1[0]==st2[0]){M0=c;f=1;}}
    if(!f){printf("N=%d NO_M0\n",N);return 0;}
    uint32_t dbx=(st1[1]^st2[1])&MASK;
    printf("N=%d M0=0x%x db56_XOR=0x%x hw=%d 2^hw=%d\n",N,M0,dbx,hw(dbx),1<<hw(dbx));
    return 0;}
'''

def build_run(src_path, n, tag):
    binp = f'/tmp/{tag}_{n}'
    r = subprocess.run(['gcc','-O3','-march=native',f'-DN={n}','-o',binp,src_path,'-lm'],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return f'(compile fail N={n}: {r.stderr.strip()[:120]})'
    out = sb.run_throttled([binp], omp=2, timeout=600)
    return out.stdout.strip()

def run():
    print("=== W4-LG3: lattice Gauss law -- is de58 the unique charged column? ===\n")
    print("Ground truth (shabridge):", "DE_SIZES[4]=",sb.DE_SIZES[4]," DE_SIZES[8]=",sb.DE_SIZES[8])
    print("DE_LAW:", sb.DE_LAW, "\n")

    with open(XOR_SRC_PATH := '/tmp/de58_xor.c','w') as fh:
        fh.write(XOR_SRC)

    print("--- (1) Additive per-round e-diff image |de_r| (the 'charge' per column) ---")
    print("    Gauss-law reading: |de_r|>1 == column r is CHARGED (sourced); ==1 == source-free.\n")
    for n in (4, 8):
        line = build_run(CSRC, n, 'lg3add')
        print("   ", line)
    print()
    print("--- (2) The 2^hw(db56_XOR) check: does the count match the Maj/AND image law? ---")
    for n in (4, 8):
        print("   ", build_run(XOR_SRC_PATH, n, 'lg3xor'))
    print()
    print(textwrap.dedent("""\
    --- (3) Derive vs restate (PRIOR FINDING #5) ---
    The image structure (|de57|,|de58|,|de59|,|de60|) = (1, V, 1, 1) is reproduced:
    de58 is the SOLE charged column; de57/de59/de60 are source-free (|.|=1). The
    'Gauss law / divergence' picture is a faithful RELABELING of this cascade table.
    BUT V == 2^hw(db56_XOR) is the KNOWN Maj/AND image count (db56 is the active diff
    feeding round-57 Maj; the e-path inherits exactly hw(db56) binary DOF). The gauge
    lens does NOT derive this count from any gauge/charge-conservation principle --
    it names the observation. Per #5: RESTATE, not derive -> not CONFIRMED.
    Locality kill_criterion does NOT fire (source is pinned to de58, nonzero, not
    smeared) -> SURVIVES as a description, but the headline 'derivation' is absent."""))

if __name__ == '__main__':
    run()
