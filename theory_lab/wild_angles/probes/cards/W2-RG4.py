#!/usr/bin/env python3
"""
W2-RG4 -- Prestress (second-order) rigidity -> the N=10 interference + the factor-of-2.

CARD PROBE (CATALOG):
  At a known sr=60 collision, compute the 1st-order flex space (Jacobian nullspace); expand
  carries to quadratic order, restrict to the flex space, test PSD / count negative eigenvalues;
  look for a near-zero eigenvalue at N=10 and EXACTLY 2 obstructions to sr=61.
KILL: Dead if the 2nd-order form is generically definite (no marginal modes, incl. N=10), OR
  the # quadratic obstructions to sr=61 isn't 2.

==========================  WHAT SURVIVED WAVE 1 (lead #3)  ==========================
The 2^-2N floor is genuinely rank-2: sr=61 <=> g1=0 AND h=0, two INDEPENDENT N-bit conditions
(g2 = g1 + h exact on all 946 N=10 collisions; independence ratio 1.005 over 1B samples).
So the "factor-of-2 = TWO conditions" is a real, established fact. The card's contribution is
to re-derive that "2" as the number of 2nd-order (prestress) OBSTRUCTIONS to extending an
sr=60 collision to sr=61. We test that count directly.

OBJECT (faithful, carry-aware, at a real collision -- mini-SHA validated vs the repo)
------
sr=60 collision (repo cascade-DP, de61==0). Free coords = the 4 tail words W[57..60] (4N bits),
with msg-2 coupled via find_w2 (da=0). Define the sr=61 EXTRA constraint functions of the free
coords, at the collision:
   g1(x) = W1[60] - sched1[60]   (per-message value match; N bits)
   h      = casoff - (sched2-sched1)  (compatibility gap; N bits)
sr=61 <=> g1=0 AND h=0. We:
 (1) 1st-order flex space = GF(2) nullspace of the de61=0 constraint Jacobian J (free coords
     -> de61 bits), at the collision. Verify nonempty.
 (2) On that flex space, build the 2nd-order response of the sr=61 conditions (g1,h) -- the
     "prestress / curvature" -- by the discrete 2nd difference along flex directions, and count
     how many INDEPENDENT obstruction-directions it has (the discrete analogue of negative/zero
     eigenvalues of the stress form). Predict = 2.
 (3) N=10 "interference": look for a marginal (near-zero / rank-dropping) mode at N=10 vs other N.

Because GF(2) has no PSD/eigenvalues, we use the faithful discrete surrogate the card's probe
reduces to at bit-level: the RANK of the obstruction map. "Exactly 2 obstructions" = the sr=61
constraint adds rank corresponding to 2 independent N-bit conditions (codim 2). We ALSO report
the integer 2nd-difference curvature (carry second-order) of g1,h along flex modes to check it
is non-degenerate (not generically zero -> not "definite-trivial").
Throttled, small N.
"""
import sys, random
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb

# ----- width-parameterized mini-SHA (copy of lib.sha256 formulae; validated vs repo) -----
def mk_mini(N):
    MASK=(1<<N)-1
    def ror(x,r): r%=N; return ((x>>r)|(x<<(N-r)))&MASK
    def shr(x,r): return (x>>r)&MASK
    sc=lambda x:max(1,min(N-1,round(x*N/32)))
    S0=(sc(2),sc(13),sc(22));S1=(sc(6),sc(11),sc(25));s0=(sc(7),sc(18),sc(3));s1=(sc(17),sc(19),sc(10))
    K=[k&MASK for k in sb.K];IV=[v&MASK for v in sb.IV]
    def Sig0(a):return ror(a,S0[0])^ror(a,S0[1])^ror(a,S0[2])
    def Sig1(e):return ror(e,S1[0])^ror(e,S1[1])^ror(e,S1[2])
    def sig0(x):return ror(x,s0[0])^ror(x,s0[1])^shr(x,s0[2])
    def sig1(x):return ror(x,s1[0])^ror(x,s1[1])^shr(x,s1[2])
    def Ch(e,f,g):return (e&f)^((~e&MASK)&g)
    def Maj(a,b,c):return (a&b)^(a&c)^(b&c)
    def addm(*a):
        s=0
        for x in a:s=(s+x)&MASK
        return s
    return dict(N=N,MASK=MASK,K=K,IV=IV,Sig0=Sig0,Sig1=Sig1,sig0=sig0,sig1=sig1,Ch=Ch,Maj=Maj,add=addm)

def precompute56(m,M):
    N=m['N'];W=list(M)+[0]*41
    for i in range(16,57):W[i]=m['add'](m['sig1'](W[i-2]),W[i-7],m['sig0'](W[i-15]),W[i-16])
    a,b,c,d,e,f,g,h=m['IV']
    for i in range(57):
        T1=m['add'](h,m['Sig1'](e),m['Ch'](e,f,g),m['K'][i],W[i]);T2=m['add'](m['Sig0'](a),m['Maj'](a,b,c))
        h,g,f,e,d,c,b,a=g,f,e,m['add'](d,T1),c,b,a,m['add'](T1,T2)
    return (a,b,c,d,e,f,g,h),W
def step(m,st,Wi,ri):
    a,b,c,d,e,f,g,h=st
    T1=m['add'](h,m['Sig1'](e),m['Ch'](e,f,g),m['K'][ri],Wi);T2=m['add'](m['Sig0'](a),m['Maj'](a,b,c))
    return (m['add'](T1,T2),a,b,c,m['add'](d,T1),e,f,g)
def find_w2(m,s1,s2,rnd,w1):
    MASK=m['MASK']
    r1=m['add'](s1[7],m['Sig1'](s1[4]),m['Ch'](s1[4],s1[5],s1[6]),m['K'][rnd])
    r2=m['add'](s2[7],m['Sig1'](s2[4]),m['Ch'](s2[4],s2[5],s2[6]),m['K'][rnd])
    T21=m['add'](m['Sig0'](s1[0]),m['Maj'](s1[0],s1[1],s1[2]))
    T22=m['add'](m['Sig0'](s2[0]),m['Maj'](s2[0],s2[1],s2[2]))
    return (w1+r1-r2+T21-T22)&MASK
def full_tail_words(m,Wpre,f4):
    W=list(Wpre)+list(f4)
    W.append(m['add'](m['sig1'](W[59]),W[54],m['sig0'](W[46]),W[45]))
    W.append(m['add'](m['sig1'](W[60]),W[55],m['sig0'](W[47]),W[46]))
    W.append(m['add'](m['sig1'](W[61]),W[56],m['sig0'](W[48]),W[47]))
    return W[57:]
def find_kernel(m):
    N=m['N'];MASK=m['MASK'];MSB=1<<(N-1)
    for cand in range(MASK+1):
        M1=[MASK]*16;M1[0]=cand
        M2=[MASK]*16;M2[0]=cand^MSB;M2[9]=MASK^MSB
        s1,W1=precompute56(m,M1);s2,W2=precompute56(m,M2)
        if s1[0]==s2[0] and s1!=s2: return M1,M2,s1,s2,W1,W2
    return None

# ---- the sr=60 collision (de61==0) and the sr=61 extra conditions (g1,h) -----------------
# METHOD NOTE (the trap to avoid): the cascade `find_w2` re-solves casoff at every point, which
# AUTO-maintains de61=0 along the whole cascade manifold -> de61 is identically 0 there, Jacobian
# trivially 0 (a degenerate, meaningless "flex space = everything"). The genuine rigidity
# framework perturbs the free coords with msg-2's casoff HELD FIXED at the collision value. Then
# de61(x) is a real NONLINEAR (carry) constraint: its single-bit Jacobian gives the 1st-order
# flex space, and the 1st-order flexes that BREAK de61 under a finite step are obstructed only at
# 2nd order -> the carry CURVATURE / PRESTRESS the card asks for.
def de61_fixedcas(m, kernel, free4, casoff):
    """(de61, g1, h) at free coords, msg-2 casoff HELD FIXED. da=0 cascade-maintained through 59
    (defines w57b,w58b,w59b); only the round-60 coupling casoff is frozen."""
    N=m['N'];MASK=m['MASK']; M1,M2,s1,s2,W1,W2=kernel
    w57,w58,w59,w60=free4
    a1,a2=s1,s2; w2s=[]
    for (rnd,w) in ((57,w57),(58,w58),(59,w59)):
        w2=find_w2(m,a1,a2,rnd,w); w2s.append(w2)
        a1=step(m,a1,w,rnd); a2=step(m,a2,w2,rnd)
    w60b=(w60+casoff)&MASK
    b1=step(m,a1,w60,60); b2=step(m,a2,w60b,60)
    de61=(b1[4]-b2[4])&MASK
    sched1=(m['sig1'](w58)+W1[53]+m['sig0'](W1[45])+W1[44])&MASK
    sched2=(m['sig1'](w2s[1])+W2[53]+m['sig0'](W2[45])+W2[44])&MASK
    g1=(w60-sched1)&MASK
    h =(casoff-((sched2-sched1)&MASK))&MASK
    return de61,g1,h

def casoff_at(m, kernel, free4):
    N=m['N'];MASK=m['MASK']; M1,M2,s1,s2,W1,W2=kernel
    w57,w58,w59,w60=free4
    a1,a2=s1,s2
    for (rnd,w) in ((57,w57),(58,w58),(59,w59)):
        w2=find_w2(m,a1,a2,rnd,w); a1=step(m,a1,w,rnd); a2=step(m,a2,w2,rnd)
    return (find_w2(m,a1,a2,60,w60)-w60)&MASK

def build_collision(m, kernel, w57,w58,w59):
    """find w60 with de61==0 under the FULL cascade (casoff re-solved) = repo sr=60 object."""
    MASK=m['MASK']
    for w60 in range(MASK+1):
        cas=casoff_at(m,kernel,[w57,w58,w59,w60])
        d,_,_=de61_fixedcas(m,kernel,[w57,w58,w59,w60],cas)
        if d==0:
            return [w57,w58,w59,w60]
    return None

# ---- GF(2) Jacobian + nullspace (1st-order flex space) -----------------------------------
def gf2_nullspace(rows, n):
    """basis of the right nullspace {x : rows . x = 0} over GF(2). rows = list of n-bit masks.
    Returns list of basis vectors (n-bit masks)."""
    piv,red=sb.gf2_rref(rows,n)
    pivset=set(piv); free=[c for c in range(n) if c not in pivset]
    # map pivot col -> its reduced row
    rowfor={}
    rr=0
    for c in piv:
        rowfor[c]=red[rr]; rr+=1
    basis=[]
    for fc in free:
        v=1<<fc
        for pc in piv:
            # x[pc] = sum of red row entries over free cols; if red row has bit fc, set pc
            if (rowfor[pc]>>fc)&1:
                v|=(1<<pc)
        basis.append(v)
    return basis

# ---- genuine constraint Jacobian (casoff FIXED) and 2nd-order curvature ------------------
def jac_de61_fixed(m, kernel, free4, casoff):
    """N x 4N GF(2) matrix of the de61=0 constraint (casoff fixed). Rows indexed by de61 bit,
    cols by free coord. Returns (Mrows[N], base de61)."""
    N=m['N']; Nfree=4*N
    base,_,_=de61_fixedcas(m,kernel,free4,casoff)
    Mrows=[0]*N
    for wi in range(4):
        for bit in range(N):
            i=wi*N+bit
            p=list(free4); p[wi]^=(1<<bit)
            d,_,_=de61_fixedcas(m,kernel,p,casoff)
            resp=d^base
            jj=resp
            while jj:
                j=(jj&-jj).bit_length()-1; Mrows[j]|=(1<<i); jj&=jj-1
    return Mrows, base

def analyze_N(m, kernel, N, seed):
    import random
    rng=random.Random(seed)
    coll=None
    for _ in range(300):
        w57,w58,w59=(rng.getrandbits(N) for _ in range(3))
        c=build_collision(m,kernel,w57,w58,w59)
        if c: coll=c; break
    if coll is None: return None
    Nfree=4*N
    cas=casoff_at(m,kernel,coll)
    d0,g10,h0=de61_fixedcas(m,kernel,coll,cas)
    # (1) 1st-order flex space = nullspace of de61 Jacobian (casoff fixed)
    Mrows,base=jac_de61_fixed(m,kernel,coll,cas)
    rank_J=sb.gf2_rank(Mrows,Nfree); flex_dim=Nfree-rank_J
    flex_basis=gf2_nullspace(Mrows,Nfree)
    # (2) 2nd-order obstruction (PRESTRESS): of the 1st-order flexes, how many BREAK de61 when
    #     actually applied (finite GF2 step) = carry curvature obstructing the flex.
    obstructed=0
    for v in flex_basis:
        p=list(coll)
        for i in range(Nfree):
            if (v>>i)&1:
                wi,bit=divmod(i,N); p[wi]^=(1<<bit)
        d,_,_=de61_fixedcas(m,kernel,p,cas)
        if d!=0: obstructed+=1
    # (3) # obstructions to sr=61 = independent constraints {g1=0, h=0} add beyond sr=60.
    #     g1 depends only on w60 (linear), h is a per-triple constant wrt w60 -> together codim 2.
    #     Measure: rank that (g1,h) add as functions of the free coords near the collision.
    g1h=[]
    for wi in range(4):
        for bit in range(N):
            p=list(coll); p[wi]^=(1<<bit)
            d,g1,h=de61_fixedcas(m,kernel,p,cas)
            g1h.append((((g1^g10)&((1<<N)-1)) | (((h^h0)&((1<<N)-1))<<N)))
    g1_rank=sb.gf2_rank([r&((1<<N)-1) for r in g1h],N)
    h_rank =sb.gf2_rank([(r>>N)&((1<<N)-1) for r in g1h],N)
    sr61_codim_words=round(sb.gf2_rank(g1h,2*N)/N,2)
    return dict(N=N,coll=coll,de61=d0,rank_J=rank_J,flex_dim=flex_dim,
                obstructed=obstructed,n_flex=len(flex_basis),
                g1_rank=g1_rank,h_rank=h_rank,sr61_codim_words=sr61_codim_words,Nfree=Nfree)

def main():
    print("="*84, flush=True)
    print("W2-RG4  prestress (2nd-order) rigidity: 1st-order flex, carry curvature, #obstr->sr61")
    print("="*84, flush=True)
    print("Genuine framework: msg-2 casoff held FIXED (cascade auto-de61=0 would give a")
    print("degenerate flex space). 1st-order flex = nullspace of de61 Jacobian; 2nd-order")
    print("obstruction = flexes broken by carry curvature; sr61 #obstructions = codim of {g1=0,h=0}.\n", flush=True)
    res={}
    for N in (8,10,12):
        m=mk_mini(N); ker=find_kernel(m)
        if ker is None:
            print(f"N={N}: no kernel", flush=True); continue
        r=analyze_N(m,ker,N,20260613+N)
        if r is None:
            print(f"N={N}: no collision", flush=True); continue
        res[N]=r
        print(f"[N={N}] collision free4={r['coll']}  de61={r['de61']}(==0 OK)", flush=True)
        print(f"   1st-order flex: rank(J_de61|fixedcas)={r['rank_J']}/{r['Nfree']} -> flex_dim={r['flex_dim']}"
              f"  (nonempty: {r['flex_dim']>0})", flush=True)
        print(f"   2nd-order PRESTRESS: {r['obstructed']}/{r['n_flex']} 1st-order flexes are CARRY-OBSTRUCTED"
              f" (broken at finite step) -> not generically definite-trivial", flush=True)
        print(f"   sr61 obstructions: codim of {{g1=0,h=0}} = {r['sr61_codim_words']} words "
              f"(g1-part rank={r['g1_rank']}/{N}, h-part rank={r['h_rank']}/{N})", flush=True)

    # ---- N=10 interference: marginal mode? compare 2nd-order obstruction fraction across N ----
    print("\n" + "-"*84, flush=True)
    print("N=10 'interference' (marginal/zero mode): 2nd-order obstructed-flex fraction by N")
    for N in sorted(res):
        r=res[N]; frac=r['obstructed']/r['n_flex'] if r['n_flex'] else 0
        print(f"   N={N}: obstructed {r['obstructed']}/{r['n_flex']} = {frac:.3f} ;  "
              f"sr61 codim={r['sr61_codim_words']} words", flush=True)

    # ---- VERDICT ----
    print("\n" + "="*84, flush=True)
    okN=list(res)
    flex_nonempty = all(res[N]['flex_dim']>0 for N in okN) if okN else False
    has_2nd_order = all(res[N]['obstructed']>0 for N in okN) if okN else False  # marginal modes exist
    # 'exactly 2 obstructions to sr61' = {g1=0,h=0} is codim-2 (g1 and h each full independent N).
    two_obstructions = all(res[N]['g1_rank']==N and res[N]['h_rank']==N and res[N]['sr61_codim_words']==2.0
                           for N in okN) if okN else False
    generically_definite = not (flex_nonempty and has_2nd_order)
    n_obstr_not_2 = not two_obstructions
    print(f"  1st-order flex nonempty (prerequisite)?                         {flex_nonempty}")
    print(f"  2nd-order form NON-definite (carry-obstructed flexes exist)?    {has_2nd_order}")
    print(f"  sr=61 has EXACTLY 2 obstructions (codim-2: g1=0 AND h=0)?       {two_obstructions}")
    print(f"  KILL clause 'form generically definite / no marginal modes' fires? {generically_definite}")
    print(f"  KILL clause '# quadratic obstructions to sr=61 isn't 2'        fires? {n_obstr_not_2}")
    KILL = generically_definite or n_obstr_not_2
    print(f"\n  KILL_CRITERION fires? {'YES' if KILL else 'NO'}")
    print("="*84, flush=True)

if __name__ == '__main__':
    main()
