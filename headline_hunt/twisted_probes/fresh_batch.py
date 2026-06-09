#!/usr/bin/env python3
"""Fresh batch of twists 4-6. Deterministic. lib/sha256 primitives."""
import sys, random
sys.path.insert(0,"lib")
from sha256 import Ch, Maj, K as KCONST
M=0xffffffff
def ROTR(x,n): return ((x>>n)|(x<<(32-n)))&M
def SHR(x,n): return (x>>n)&M
def hw(x): return bin(x&M).count("1")
def Sig0(x): return ROTR(x,2)^ROTR(x,13)^ROTR(x,22)
def Sig1(x): return ROTR(x,6)^ROTR(x,11)^ROTR(x,25)
def sig0(x): return ROTR(x,7)^ROTR(x,18)^SHR(x,3)
def sig1(x): return ROTR(x,17)^ROTR(x,19)^SHR(x,10)

def round_fn(s,w,k, S0=Sig0,S1=Sig1, ch=Ch, mj=Maj, lin_add=False):
    a,b,c,d,e,f,g,h=s
    def AD(*xs):
        if lin_add:
            r=0
            for x in xs: r^=x
            return r&M
        r=0
        for x in xs: r=(r+x)&M
        return r
    T1=AD(h,S1(e),ch(e,f,g),k,w); T2=AD(S0(a),mj(a,b,c))
    return (AD(T1,T2),a,b,c,AD(d,T1),e,f,g)

def avalanche(diff_setup, R=4, Ksamp=3000, seed=0, **kw):
    rnd=random.Random(seed); acc=0.0
    for _ in range(Ksamp):
        s1=tuple(rnd.getrandbits(32) for _ in range(8))
        s2=diff_setup(s1, rnd)
        W=[rnd.getrandbits(32) for _ in range(R)]
        a,b=s1,s2
        for r in range(R):
            a=round_fn(a,W[r],KCONST[r],**kw); b=round_fn(b,W[r],KCONST[r],**kw)
        acc+=sum(hw(x^y) for x,y in zip(a,b))
    return acc/Ksamp

# ---- TWIST 4: diffusion spectrum over all 256 single-bit input diffs ----
print("=== TWIST 4: diffusion spectrum (avalanche HW @R=4 per input-bit difference) ===")
names="a b c d e f g h".split()
spec=[]
for bit in range(256):
    reg,off=divmod(bit,32)
    def setup(s,rnd,reg=reg,off=off):
        x=list(s); x[reg]^=(1<<off); return tuple(x)
    spec.append((avalanche(setup,R=4,Ksamp=1500,seed=4), reg, off))
spec.sort()
print("  slowest-diffusing input bits (weakest directions):")
for hwv,reg,off in spec[:6]: print(f"    {names[reg]}[{off:2d}]: {hwv:5.1f}")
print("  fastest-diffusing:")
for hwv,reg,off in spec[-3:]: print(f"    {names[reg]}[{off:2d}]: {hwv:5.1f}")
print(f"  spread: slowest {spec[0][0]:.1f}  ..  fastest {spec[-1][0]:.1f}  ({spec[-1][0]/spec[0][0]:.1f}x)")

# ---- TWIST 5: carries vs booleans ----
print("\n=== TWIST 5: where does diffusion/resistance live? (avalanche @R=4) ===")
def setup_rand(s,rnd):
    bit=rnd.randrange(256); reg,off=divmod(bit,32); x=list(s); x[reg]^=(1<<off); return tuple(x)
base=avalanche(setup_rand,R=4,Ksamp=4000,seed=5)
no_bool=avalanche(setup_rand,R=4,Ksamp=4000,seed=5, ch=lambda e,f,g:0, mj=lambda a,b,c:0)
no_carry=avalanche(setup_rand,R=4,Ksamp=4000,seed=5, lin_add=True)
print(f"    baseline (full SHA)         : {base:5.1f}")
print(f"    Ch=Maj=0 (no boolean nonlin): {no_bool:5.1f}   (drop {base-no_bool:+.1f})")
print(f"    adds->XOR (no carries)      : {no_carry:5.1f}   (drop {base-no_carry:+.1f})")
print(f"    => resistance lives more in: {'CARRIES' if (base-no_carry)>(base-no_bool) else 'BOOLEANS (Ch/Maj)'}")

# ---- TWIST 6: rotation-constant sensitivity ----
print("\n=== TWIST 6: are SHA-256's rotations tuned for diffusion? (avalanche @R=4) ===")
def mk(r):  # custom Sigma/sigma from rotation tuples
    (a0,a1,a2),(b0,b1,b2),(c0,c1,c2),(d0,d1,d2)=r
    return (lambda x:ROTR(x,a0)^ROTR(x,a1)^ROTR(x,a2),
            lambda x:ROTR(x,b0)^ROTR(x,b1)^ROTR(x,b2),
            lambda x:ROTR(x,c0)^ROTR(x,c1)^SHR(x,c2),
            lambda x:ROTR(x,d0)^ROTR(x,d1)^SHR(x,d2))
sets={
 "SHA-256 actual": ((2,13,22),(6,11,25),(7,18,3),(17,19,10)),
 "tiny rots 1,2,3": ((1,2,3),(1,2,3),(1,2,3),(1,2,3)),
 "all same (7)":   ((7,7,7),(7,7,7),(7,7,7),(7,7,7)),
 "wide spread":    ((1,11,21),(3,13,27),(5,15,9),(2,16,28)),
}
for nm,r in sets.items():
    S0,S1,s0,s1=mk(r)
    av=avalanche(setup_rand,R=4,Ksamp=3000,seed=6,S0=S0,S1=S1)
    # note: only Sigma0/Sigma1 swapped in round_fn (state path); schedule sigmas not in this round-only test
    print(f"    {nm:16s}: {av:5.1f}")
