"""
W1-GE6 -- Configuration-space braid: multi-block = added generators.

Card probe: "N=4: record the 43-adder carry pattern of collision vs non-collision
pairs as a crossing sequence; compute writhe (signed carry count) + underlying
permutation; do collisions cluster at a distinguished class? escalate to Burau if
writhe alone separates."
Kill: "Dead if the braid invariant is the same on collision/non-collision pairs
or is a deterministic function of HW."

We reconstruct the repo's REDUCED-WIDTH-N cascade SHA (scaled rotations, MSB
kernel, fill=MASK, W2=W1+casoff for da=0) -- EXACTLY gap_analysis.c -- so genuine
sr=60 cascade collisions exist and can be enumerated.  For each tail round we read
the SIGNED CARRY-DIFFERENCE pattern across the round's adders (the 'crossings');
braid invariants = writhe (signed carry count) and the (n+,n-) crossing type.
COLLISION = sr=60 cascade collision (tail diff through round 60 == 0);
NON-COLLISION = cascade-valid pair (W2=W1+casoff) that does NOT collide.
Then: do collisions cluster at a distinguished writhe class, beyond a function of HW?
"""
import sys, math, random
from collections import Counter, defaultdict
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
import adder_diff as ad

# ---- reduced-width-N SHA, matching headline_hunt/.../gap_analysis.c ----------
def scale_rot(k, N):
    r = round(k * N / 32.0); return r if r >= 1 else 1

class RSHA:
    def __init__(self, N):
        self.N = N; self.M = (1 << N) - 1
        self.rS0 = [scale_rot(k,N) for k in (2,13,22)]
        self.rS1 = [scale_rot(k,N) for k in (6,11,25)]
        self.rs0 = [scale_rot(k,N) for k in (7,18)]; self.ss0 = scale_rot(3,N)
        self.rs1 = [scale_rot(k,N) for k in (17,19)]; self.ss1 = scale_rot(10,N)
        self.K = [k & self.M for k in sb.K]
        self.IV = [v & self.M for v in sb.IV]
    def ror(self, x, k):
        N=self.N; k%=N; return ((x>>k)|(x<<(N-k))) & self.M
    def S0(self,a): return self.ror(a,self.rS0[0])^self.ror(a,self.rS0[1])^self.ror(a,self.rS0[2])
    def S1(self,e): return self.ror(e,self.rS1[0])^self.ror(e,self.rS1[1])^self.ror(e,self.rS1[2])
    def s0(self,x): return self.ror(x,self.rs0[0])^self.ror(x,self.rs0[1])^((x>>self.ss0)&self.M)
    def s1(self,x): return self.ror(x,self.rs1[0])^self.ror(x,self.rs1[1])^((x>>self.ss1)&self.M)
    def Ch(self,e,f,g): return (e&f)^((~e&self.M)&g)
    def Maj(self,a,b,c): return (a&b)^(a&c)^(b&c)
    def expand(self, M):
        N=self.N; W=list(M)+[0]*41
        for i in range(16,57):
            W[i]=(self.s1(W[i-2])+W[i-7]+self.s0(W[i-15])+W[i-16])&self.M
        return W
    def round(self, st, k, w):
        a,b,c,d,e,f,g,h = st
        T1=(h+self.S1(e)+self.Ch(e,f,g)+k+w)&self.M
        T2=(self.S0(a)+self.Maj(a,b,c))&self.M
        return ((T1+T2)&self.M, a,b,c, (d+T1)&self.M, e,f,g)
    def precompute57(self, M):
        W=self.expand(M); st=tuple(self.IV)
        for i in range(57): st=self.round(st,self.K[i],W[i])
        return st, W
    def find_w2(self, s1, s2, rnd, w1):
        """w2 s.t. round keeps da=0: cw = (a-contribution diff); w2 = w1 + cw."""
        N=self.N; M=self.M
        # da_next=0 needs T1A+T2A == T1B+T2B (the a' update). Solve w2.
        cwA=(s1[7]+self.S1(s1[4])+self.Ch(s1[4],s1[5],s1[6])+self.S0(s1[0])+self.Maj(s1[0],s1[1],s1[2]))&M
        cwB=(s2[7]+self.S1(s2[4])+self.Ch(s2[4],s2[5],s2[6])+self.S0(s2[0])+self.Maj(s2[0],s2[1],s2[2]))&M
        cw=(cwA-cwB)&M
        return (w1+cw)&M

def carry_trace(x,y,N):
    m=(1<<N)-1; x&=m; y&=m; c=[0]*(N+1)
    for i in range(N):
        sm=((x>>i)&1)+((y>>i)&1)+c[i]; c[i+1]=sm>>1
    return c

def find_cascade_M0(rs):
    """find an M0 with the cascade property (state1[0]==state2[0]) like the C tool."""
    N=rs.N; M=rs.M; MSB=1<<(N-1)
    for cand in range(1<<N):
        M1=[cand]+[M]*15
        M2=list(M1); M2[0]=cand^MSB; M2[9]=M^MSB
        s1,_=rs.precompute57(M1); s2,_=rs.precompute57(M2)
        if s1[0]==s2[0]:
            return cand, M1, M2
    return None, None, None

def tail_braid(rs, s1_0, s2_0, freeW1):
    """Run rounds 57..60 cascade (W2=W1+casoff each round) from pre-states; collect
    per-round signed carry crossings (a'-chain carry diff); return (de_after60, braid).
    de_after60 = full 8-reg diff after round 60 (cascade collision iff small/zero)."""
    s1=list(s1_0); s2=list(s2_0); braid=[]
    N=rs.N; M=rs.M
    for t in range(4):           # rounds 57,58,59,60
        r=57+t; k=rs.K[r]; w1=freeW1[t]
        w2=rs.find_w2(s1,s2,r,w1)
        # crossings = signed carry diff in the a'=T1+T2 adder
        a1,b1,c1,d1,e1,f1,g1,h1=s1; a2,b2,c2,d2,e2,f2,g2,h2=s2
        T1a=(h1+rs.S1(e1)+rs.Ch(e1,f1,g1)+k+w1)&M; T2a=(rs.S0(a1)+rs.Maj(a1,b1,c1))&M
        T1b=(h2+rs.S1(e2)+rs.Ch(e2,f2,g2)+k+w2)&M; T2b=(rs.S0(a2)+rs.Maj(a2,b2,c2))&M
        cA=carry_trace(T1a,T2a,N); cB=carry_trace(T1b,T2b,N)
        braid.append([cB[i]-cA[i] for i in range(1,N+1)])
        s1=list(rs.round(tuple(s1),k,w1)); s2=list(rs.round(tuple(s2),k,w2))
    de=tuple((s1[i]^s2[i]) & M for i in range(8))
    return de, braid

def writhe(braid): return sum(sum(r) for r in braid)
def crossing_type(braid):
    seq=[x for r in braid for x in r]
    return (sum(1 for x in seq if x>0), sum(1 for x in seq if x<0))

def run():
    print("=== W1-GE6: configuration-space braid (writhe + permutation) ===\n")
    # Use the GENUINE N=10 sr=60 collisions in gap_rows.csv (946 real collisions,
    # cols w57,w58,w59,w60) and compare their carry-braids to random cascade-valid
    # NON-collision tuples at the same N.
    N=10
    rs=RSHA(N)
    print(f"reduced SHA N={N}: rS0={rs.rS0} rS1={rs.rS1}")
    m0, M1, M2 = find_cascade_M0(rs)
    print(f"cascade M0=0x{m0:x} fill=0x{rs.M:x} (MSB kernel)")
    s1_0,_=rs.precompute57(M1); s2_0,_=rs.precompute57(M2)

    # define collision by the gap-data criterion: a (w57..w60) cascade pair whose
    # post-round-60 cascade difference is minimal (the sr=60 collision set).  We
    # read braid + post-60 HW for the REAL gap_rows tuples and for random tuples.
    gap = sb.load_gap_rows()    # 946 real N=10 collisions
    coll=[]
    for row in gap:
        w57,w58,w59,w60 = (int(row['w57']),int(row['w58']),int(row['w59']),int(row['w60']))
        de, braid = tail_braid(rs, s1_0, s2_0, [w57,w58,w59,w60])
        hw=sum(bin(x).count('1') for x in de)
        coll.append((hw, writhe(braid), crossing_type(braid)))
    # random NON-collision cascade tuples (same N), matched count
    rng=random.Random(2026); noncoll=[]
    for _ in range(len(coll)):
        w=[rng.getrandbits(N) for _ in range(4)]
        de, braid = tail_braid(rs, s1_0, s2_0, w)
        hw=sum(bin(x).count('1') for x in de)
        noncoll.append((hw, writhe(braid), crossing_type(braid)))
    samples = coll + noncoll
    coll_hw = sum(s[0] for s in coll)/len(coll)
    nc_hw = sum(s[0] for s in noncoll)/len(noncoll)
    print(f"\nreal gap_rows collisions: n={len(coll)} (mean post-60 HW={coll_hw:.1f})")
    print(f"random non-collisions:    n={len(noncoll)} (mean post-60 HW={nc_hw:.1f})")
    band="rand"

    def summ(name, grp):
        wr=[s[1] for s in grp]
        ct=Counter(s[2] for s in grp).most_common(3)
        print(f"  {name}: n={len(grp)}  writhe mean={sum(wr)/len(wr):+.2f} sd="
              f"{(sum((x-sum(wr)/len(wr))**2 for x in wr)/len(wr))**0.5:.2f} "
              f"range=[{min(wr)},{max(wr)}]  type-modes={ct}")
    print("\n[writhe / crossing-type separation]:")
    summ("collision   ", coll)
    summ(f"noncoll HW={band}", noncoll)

    # KILL test 1: invariant identical on collision vs non-collision?
    wc=[s[1] for s in coll]; wn=[s[1] for s in noncoll]
    mc=sum(wc)/len(wc); mn=sum(wn)/len(wn)
    sdc=(sum((x-mc)**2 for x in wc)/len(wc))**0.5
    sep = abs(mc-mn)/(sdc+1e-9)   # separation in collision-sd units
    print(f"\n[KILL tests]")
    print(f"  (1) writhe mean coll={mc:+.2f} vs noncoll={mn:+.2f}; separation={sep:.2f} sd")
    print(f"      collision type-set == noncoll type-set? "
          f"{set(s[2] for s in coll)==set(s[2] for s in noncoll)}")
    # KILL test 2: writhe a (deterministic) function of HW?
    def pear(a,b):
        n=len(a); ma=sum(a)/n; mb=sum(b)/n
        num=sum((a[i]-ma)*(b[i]-mb) for i in range(n))
        da=(sum((x-ma)**2 for x in a))**0.5; db=(sum((x-mb)**2 for x in b))**0.5
        return num/(da*db) if da*db else 0.0
    H=[s[0] for s in samples]; Wr=[s[1] for s in samples]
    byhw=defaultdict(set)
    for hw,wr,_ in samples: byhw[hw].add(wr)
    print(f"  (2a) corr(writhe, HW) over all {len(samples)} pairs = {pear(Wr,H):+.3f}")
    print(f"  (2b) writhe deterministic in HW? {all(len(v)==1 for v in byhw.values())} "
          f"(max distinct writhes at one HW = {max(len(v) for v in byhw.values())})")

    print("\n[interpretation] KILL if invariant same on coll/non-coll OR writhe is a")
    print("deterministic function of HW.  CONFIRMED if collisions cluster at a distinct")
    print("writhe/type class with clear separation, not explained by HW.")

if __name__ == '__main__':
    run()
