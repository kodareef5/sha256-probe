#!/usr/bin/env python3
"""Three twisted-constraint probes v2 (refined). Deterministic. Uses lib/sha256."""
import sys, random
sys.path.insert(0, "lib")
from sha256 import Sigma0, Sigma1, sigma0, sigma1, Ch, Maj, K as KCONST
M = 0xffffffff
def hw(x): return bin(x & M).count("1")
def fwd_round(s, w, k):
    a,b,c,d,e,f,g,h = s
    T1=(h+Sigma1(e)+Ch(e,f,g)+k+w)&M; T2=(Sigma0(a)+Maj(a,b,c))&M
    return ((T1+T2)&M,a,b,c,(d+T1)&M,e,f,g)
def inv_round(s, w, k):
    a2,b2,c2,d2,e2,f2,g2,h2=s
    a=b2;b=c2;c=d2;e=f2;f=g2;g=h2
    T2=(Sigma0(a)+Maj(a,b,c))&M; T1=(a2-T2)&M; d=(e2-T1)&M
    h=(T1-Sigma1(e)-Ch(e,f,g)-k-w)&M
    return (a,b,c,d,e,f,g,h)
def det_bits(diffs):
    e0=e1=0
    for d in diffs: e0|=(~d)&M; e1|=d&M
    return 32-hw(e0&e1)

# TWIST 1: per-round, which coordinate linearizes more — and the hybrid payoff
def twist1(R=16, Ksamp=3000, seed=1):
    rnd=random.Random(seed)
    def expand(W):
        W=list(W)
        for i in range(16,16+R): W.append((sigma1(W[i-2])+W[i-7]+sigma0(W[i-15])+W[i-16])&M)
        return W
    xor_tot=mod_tot=hyb_tot=0
    for i in range(16,16+R):
        ox=[]; om=[]
        for _ in range(Ksamp):
            base=[rnd.getrandbits(32) for _ in range(16)]
            p=1<<rnd.randrange(32)               # random single-bit perturbation of W[0]
            bx=list(base); bx[0]^=p
            bm=list(base); bm[0]=(bm[0]+p)&M
            Wb=expand(base); ox.append((Wb[i]^expand(bx)[i])&M); om.append((Wb[i]-expand(bm)[i])&M)
        dx=det_bits(ox); dm=det_bits(om)
        xor_tot+=dx; mod_tot+=dm; hyb_tot+=max(dx,dm)
    print(f"  Across {R} schedule rounds, total determined (linear) bits / {R*32}:")
    print(f"    XOR coords only : {xor_tot}")
    print(f"    MOD coords only : {mod_tot}")
    print(f"    HYBRID (best per round) : {hyb_tot}   <- the complementarity payoff")
    print(f"    hybrid beats best-single by: {hyb_tot-max(xor_tot,mod_tot)} bits ({100*(hyb_tot-max(xor_tot,mod_tot))/max(1,max(xor_tot,mod_tot)):.0f}%)")

# TWIST 2: carry-criticality at SHALLOW depth (before full diffusion)
def twist2(Ksamp=20000, seed=2):
    sites=["ALL_modular","T1(5op)","T2(2op)","a=T1+T2","e=d+T1"]
    def rv(s,w,k,lin):
        a,b,c,d,e,f,g,h=s
        def AD(*x):
            r=0
            for v in x: r=(r+v)&M
            return r
        def XO(*x):
            r=0
            for v in x: r^=v
            return r&M
        T1=(XO if lin=="T1(5op)" else AD)(h,Sigma1(e),Ch(e,f,g),k,w)
        T2=(XO if lin=="T2(2op)" else AD)(Sigma0(a),Maj(a,b,c))
        return ((XO if lin=="a=T1+T2" else AD)(T1,T2),a,b,c,(XO if lin=="e=d+T1" else AD)(d,T1),e,f,g)
    for R in (3,4):
        print(f"  R={R} rounds, 1-bit input diff in e | determined output-diff bits (higher=more LINEAR=that add was load-bearing)")
        for lin in sites:
            rnd=random.Random(seed)
            diffs=[]
            for _ in range(Ksamp):
                s1=tuple(rnd.getrandbits(32) for _ in range(8))
                s2=list(s1); s2[4]^=(1<<15); s2=tuple(s2)
                W=[rnd.getrandbits(32) for _ in range(R)]
                for r in range(R): s1=rv(s1,W[r],KCONST[r],lin); s2=rv(s2,W[r],KCONST[r],lin)
                diffs.append(tuple((x^y)&M for x,y in zip(s1,s2)))
            # determined bits across all 256 output bits
            det=sum(det_bits([d[reg] for d in diffs]) for reg in range(8))
            print(f"    {lin:12s} | {det:3d}/256")

# TWIST 3: forward vs backward diffusion + ratio
def twist3(R=10, Ksamp=4000, seed=3):
    rnd=random.Random(seed); fa=[0.0]*R; ba=[0.0]*R
    for _ in range(Ksamp):
        s1=tuple(rnd.getrandbits(32) for _ in range(8)); bt=rnd.randrange(256); rg,of=divmod(bt,32)
        s2=list(s1); s2[rg]^=(1<<of); s2=tuple(s2); W=[rnd.getrandbits(32) for _ in range(R)]
        a,b=s1,s2
        for r in range(R): a=fwd_round(a,W[r],KCONST[r]); b=fwd_round(b,W[r],KCONST[r]); fa[r]+=sum(hw(x^y) for x,y in zip(a,b))
        t1=tuple(rnd.getrandbits(32) for _ in range(8)); bt=rnd.randrange(256); rg,of=divmod(bt,32)
        t2=list(t1); t2[rg]^=(1<<of); t2=tuple(t2); Wb=[rnd.getrandbits(32) for _ in range(R)]
        a,b=t1,t2
        for r in range(R): a=inv_round(a,Wb[r],KCONST[R-1-r]); b=inv_round(b,Wb[r],KCONST[R-1-r]); ba[r]+=sum(hw(x^y) for x,y in zip(a,b))
    print("  round | fwd HW | bwd HW | fwd/bwd ratio")
    for r in range(R):
        f=fa[r]/Ksamp; bb=ba[r]/Ksamp
        print(f"    {r+1:2d}   | {f:6.1f} | {bb:6.1f} | {f/bb:4.2f}x")

if __name__=="__main__":
    print("=== TWIST 1: modular vs XOR coords + the HYBRID payoff (schedule) ==="); twist1()
    print("\n=== TWIST 2: carry-criticality at shallow depth ==="); twist2()
    print("\n=== TWIST 3: forward vs backward diffusion asymmetry ==="); twist3()
