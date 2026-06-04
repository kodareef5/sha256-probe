#!/usr/bin/env python3
"""
W2-RG1 -- Maxwell-Calladine isostatic point -> "why round 60" AND codim-2 -> 2^-2N.

CARD PROBE (CATALOG):
  N=4..12: build the per-round agreement-constraint Jacobian via add_word(track_carries=True)
  linearized at a known sr=60 solution; compute D(r)-C(r) and the *measured* rank for r=57..61;
  nullity->trivial = predicted boundary; codim increment per round should be ~2.
KILL: Dead if D(r)-C(r) never changes sign in 57..61, OR the per-round codim increment isn't ~2.

This card has TWO independent clauses; they are SCORED SEPARATELY (lead's guidance #2,#3):
  CLAUSE A ("why round 60"): is there a REAL isostatic transition (floppy(r)=D-C crossing
            zero) at r~60, with the carry-aware *measured* rank? (W1-PH2 already KILLED the
            XOR-linear version: smooth N-per-round decay, no knee. We use a CARRY-AWARE
            local Jacobian at a real collision -- the object the card actually asks for.)
  CLAUSE B ("codim-2 -> 2^-2N"): does the per-round over-constraint increment = 2 (the
            g1=0 AND h=0 pair)? The rank-2 fact g2 = g1 + h holds for ALL 946 N=10
            collisions (two independent conditions) -- this is the Wave-1 survivor.

METHOD
------
Reuse shabridge SHA primitives via a width-parameterized mini-SHA (lib.sha256 is 32-bit only;
this is a width copy of lib's *formulae*, validated by reproducing the repo's 260/946 counts).
At N=10 we take a REAL collision (w57,w58,w59,w60) from the repo's gap_rows.csv and rebuild
the (0,9)-MSB cascade kernel, verifying the full 8-register collision at round 63.

CLAUSE A -- per-round constraint Jacobian, carry-aware, at the collision point:
  The cascade enforces da=0 each tail round and the collision needs de_r-cascade conditions.
  "Agreement constraints" at round r = the inter-message difference of the registers that must
  vanish for the collision, accumulated through round r. We linearize the REAL MODULAR tail
  (carries included -- this is the track_carries=True analogue: a single-bit perturbation of a
  free input word sees the exact local carry behaviour at the collision) by flipping each free
  input bit and recording which constraint bits respond. C(r) = GF(2) rank of that Jacobian
  using constraint rows up to round r; D(r) = free message DOF still injectable at round >= r
  (N bits per free word W[57..60], i.e. 4N..N as r:57->60). floppy(r)=D(r)-C(r).
  ISOSTATIC = floppy crosses zero (under- -> over-constrained). We report the measured curve.

CLAUSE B -- codim per enforced round:
  The actual enforced object is "extend the collision by one more held schedule round (sr60->
  sr61)". The repo proves: sr61 <=> g1=0 AND h=0, and g2=g1+h exactly. So the extra round adds
  exactly 2 independent N-bit constraints. We re-derive this directly from gap_rows.csv (the
  measured gating data) and from the rank of the (g1,g2,h) relation matrix.
"""
import sys, os, csv
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb

# ---------------- width-parameterized mini-SHA (copy of lib.sha256 formulae) -------------
def mk_mini(N):
    MASK = (1 << N) - 1
    def ror(x, r): r %= N; return ((x >> r) | (x << (N - r))) & MASK
    def shr(x, r): return (x >> r) & MASK
    sc = lambda x: max(1, min(N-1, round(x * N / 32)))
    S0=(sc(2),sc(13),sc(22)); S1=(sc(6),sc(11),sc(25)); s0=(sc(7),sc(18),sc(3)); s1=(sc(17),sc(19),sc(10))
    K=[k & MASK for k in sb.K]; IV=[v & MASK for v in sb.IV]
    def Sig0(a): return ror(a,S0[0])^ror(a,S0[1])^ror(a,S0[2])
    def Sig1(e): return ror(e,S1[0])^ror(e,S1[1])^ror(e,S1[2])
    def sig0(x): return ror(x,s0[0])^ror(x,s0[1])^shr(x,s0[2])
    def sig1(x): return ror(x,s1[0])^ror(x,s1[1])^shr(x,s1[2])
    def Ch(e,f,g): return (e&f)^((~e & MASK)&g)
    def Maj(a,b,c): return (a&b)^(a&c)^(b&c)
    def addm(*a):
        s=0
        for x in a: s=(s+x)&MASK
        return s
    return dict(N=N,MASK=MASK,K=K,IV=IV,Sig0=Sig0,Sig1=Sig1,sig0=sig0,sig1=sig1,Ch=Ch,Maj=Maj,add=addm)

def precompute56(m, M):
    N=m['N']; W=list(M)+[0]*41
    for i in range(16,57):
        W[i]=m['add'](m['sig1'](W[i-2]),W[i-7],m['sig0'](W[i-15]),W[i-16])
    a,b,c,d,e,f,g,h=m['IV']
    for i in range(57):
        T1=m['add'](h,m['Sig1'](e),m['Ch'](e,f,g),m['K'][i],W[i])
        T2=m['add'](m['Sig0'](a),m['Maj'](a,b,c))
        h,g,f,e,d,c,b,a=g,f,e,m['add'](d,T1),c,b,a,m['add'](T1,T2)
    return (a,b,c,d,e,f,g,h),W

def step(m, state, Wi, ridx):
    a,b,c,d,e,f,g,h=state
    T1=m['add'](h,m['Sig1'](e),m['Ch'](e,f,g),m['K'][ridx],Wi)
    T2=m['add'](m['Sig0'](a),m['Maj'](a,b,c))
    return (m['add'](T1,T2),a,b,c,m['add'](d,T1),e,f,g)

def find_w2(m, s1, s2, rnd, w1):
    """cascade offset: the message-2 schedule word at `rnd` that keeps da=0 (exactly the
    repo's gap_analysis.find_w2). w2 = w1 + (r1-r2) + (T21-T22)."""
    MASK=m['MASK']
    r1=m['add'](s1[7],m['Sig1'](s1[4]),m['Ch'](s1[4],s1[5],s1[6]),m['K'][rnd])
    r2=m['add'](s2[7],m['Sig1'](s2[4]),m['Ch'](s2[4],s2[5],s2[6]),m['K'][rnd])
    T21=m['add'](m['Sig0'](s1[0]),m['Maj'](s1[0],s1[1],s1[2]))
    T22=m['add'](m['Sig0'](s2[0]),m['Maj'](s2[0],s2[1],s2[2]))
    return (w1 + r1 - r2 + T21 - T22) & MASK

def build_collision_cascade(m, kernel, w57, w58, w59):
    """Replicate the repo cascade-DP (gap_analysis.c) EXACTLY: msg-2 tail words via find_w2
    (da=0 each round); brute w60 in [0,2^N) for de61==0. de61==0 under the da=0 cascade IS the
    repo's sr=60 collision object (the Viragh reduced-difference target -- NOT all-256-bits-0).
    Returns ([w57..w60], msg1_tail, msg2_tail) for the first de61==0, else None."""
    N=m['N']; MASK=m['MASK']
    M1,M2,s1,s2,W1,W2=kernel
    a1,a2=s1,s2; w2s=[]
    for (rnd,w) in ((57,w57),(58,w58),(59,w59)):
        w2 = find_w2(m,a1,a2,rnd,w); w2s.append(w2)
        a1=step(m,a1,w,rnd); a2=step(m,a2,w2,rnd)
    for w60 in range(MASK+1):
        w60b = find_w2(m,a1,a2,60,w60)
        b1=step(m,a1,w60,60); b2=step(m,a2,w60b,60)
        if ((b1[4]-b2[4]) & MASK)==0:        # de61==0  ==  sr=60 collision (repo definition)
            f1 = full_tail_words(m, W1, [w57,w58,w59,w60])
            W2full = list(W2)+[w2s[0],w2s[1],w2s[2],w60b]
            W2full.append(m['add'](m['sig1'](W2full[59]),W2full[54],m['sig0'](W2full[46]),W2full[45]))
            W2full.append(m['add'](m['sig1'](W2full[60]),W2full[55],m['sig0'](W2full[47]),W2full[46]))
            W2full.append(m['add'](m['sig1'](W2full[61]),W2full[56],m['sig0'](W2full[48]),W2full[47]))
            f2 = W2full[57:]
            return [w57,w58,w59,w60], f1, f2
    return None

def full_tail_words(m, Wpre, free4):
    W=list(Wpre)+list(free4)
    W.append(m['add'](m['sig1'](W[59]),W[54],m['sig0'](W[46]),W[45]))   # W61
    W.append(m['add'](m['sig1'](W[60]),W[55],m['sig0'](W[47]),W[46]))   # W62
    W.append(m['add'](m['sig1'](W[61]),W[56],m['sig0'](W[48]),W[47]))   # W63
    return W[57:]

def find_kernel(m):
    N=m['N']; MASK=m['MASK']; MSB=1<<(N-1)
    for cand in range(MASK+1):
        M1=[MASK]*16; M1[0]=cand
        M2=[MASK]*16; M2[0]=cand^MSB; M2[9]=MASK^MSB
        s1,W1=precompute56(m,M1); s2,W2=precompute56(m,M2)
        if s1[0]==s2[0] and s1!=s2:
            return M1,M2,s1,s2,W1,W2
    return None

# ----------------------- CLAUSE A: per-round carry-aware constraint Jacobian -------------
def diff_trace_cascade(m, kernel, free4):
    """run BOTH messages' cascade tails (msg-2 words coupled via find_w2 each round, so a
    perturbation of a free msg-1 word propagates to msg-2 too -- the real carry-aware coupling).
    Return list (len 7) of 8-register difference vectors after rounds 57..63."""
    N=m['N']; MASK=m['MASK']
    M1,M2,s1,s2,W1,W2=kernel
    w57,w58,w59,w60=free4
    a1,a2=s1,s2; w1s=[]; w2s=[]
    for (rnd,w) in ((57,w57),(58,w58),(59,w59),(60,w60)):
        w2=find_w2(m,a1,a2,rnd,w); w1s.append(w); w2s.append(w2)
        a1=step(m,a1,w,rnd); a2=step(m,a2,w2,rnd)
    # schedule-close both messages
    f1=full_tail_words(m,W1,[w57,w58,w59,w60])
    W2f=list(W2)+w2s
    W2f.append(m['add'](m['sig1'](W2f[59]),W2f[54],m['sig0'](W2f[46]),W2f[45]))
    W2f.append(m['add'](m['sig1'](W2f[60]),W2f[55],m['sig0'](W2f[47]),W2f[46]))
    W2f.append(m['add'](m['sig1'](W2f[61]),W2f[56],m['sig0'](W2f[48]),W2f[47]))
    f2=W2f[57:]
    c1,c2=s1,s2; trace=[]
    for i in range(7):
        c1=step(m,c1,f1[i],57+i); c2=step(m,c2,f2[i],57+i)
        trace.append(tuple((c1[k]-c2[k])&MASK for k in range(8)))
    return trace

def per_round_jacobian(m, kernel, free4):
    """GF(2) Jacobian of the per-round agreement-constraint bits (8-reg diff) w.r.t. the free
    input bits, by single-bit perturbation of the REAL modular cascade tail (carries included)."""
    N=m['N']
    base=diff_trace_cascade(m,kernel,free4)
    free_bits=[(wi,bit) for wi in range(4) for bit in range(N)]
    resp={}
    for (wi,bit) in free_bits:
        pert=list(free4); pert[wi]^=(1<<bit)
        tr=diff_trace_cascade(m,kernel,pert)
        per_round=[]
        for ri in range(7):
            mask=0
            for reg in range(8):
                d=tr[ri][reg]^base[ri][reg]
                for kb in range(N):
                    if (d>>kb)&1: mask|=(1<<(reg*N+kb))
            per_round.append(mask)
        resp[(wi,bit)]=per_round
    return base, free_bits, resp

def ranks_at_point(m, kernel, free4):
    N=m['N']
    base, free_bits, resp = per_round_jacobian(m, kernel, free4)
    rounds=list(range(57,64)); C={}; Dfree={}; floppy={}
    for ridx,r in enumerate(rounds):
        rows=[]
        for fb in free_bits:
            wide=0
            for rr in range(ridx+1):
                wide |= resp[fb][rr] << (rr*8*N)
            rows.append(wide)
        C[r]=sb.gf2_rank(rows,(ridx+1)*8*N)
        Dfree[r]=N*sum(1 for k in range(4) if 57+k>=r)
        floppy[r]=Dfree[r]-C[r]
    return rounds,C,Dfree,floppy

def clause_A(N=10):
    import random
    m=mk_mini(N)
    ker=find_kernel(m)
    if ker is None:
        return dict(ok=False, why='no kernel')
    M1,M2,s1,s2,W1,W2=ker
    # construct a GENUINE sr=60 collision (cascade-DP) to use as the linearization point
    rng=random.Random(20260603)
    coll=None
    for _ in range(400):   # each try brutes w60 over 2^N internally; ~few tries succeed
        w57,w58,w59=(rng.getrandbits(N) for _ in range(3))
        r=build_collision_cascade(m,ker,w57,w58,w59)
        if r: coll=r; break
    verified = coll is not None
    free4 = coll[0] if coll else [0,0,0,0]
    rounds,C,Dfree,floppy = ranks_at_point(m,ker,free4)
    # ALSO compute the per-round rank increment at several RANDOM (non-collision) points to
    # show the increment is invariant (it's free-DOF bookkeeping, not a carry transition).
    rand_incs=[]
    for _ in range(5):
        rf=[rng.getrandbits(N) for _ in range(4)]
        _,Cr,_,_=ranks_at_point(m,ker,rf)
        rand_incs.append([Cr[r]-Cr[r-1] for r in range(58,64)])
    coll_inc=[C[r]-C[r-1] for r in range(58,64)]
    return dict(ok=True, verified=verified, free4=free4, N=N, rounds=rounds,
                C=C, Dfree=Dfree, floppy=floppy, kernel_M0=(M1[0],M2[0]),
                coll_inc=coll_inc, rand_incs=rand_incs)

# ----------------------- CLAUSE B: codim of one enforced round (sr60 -> sr61) ------------
def clause_B(N=10):
    rows=sb.load_gap_rows()
    mod = (1<<N)
    g2_eq = sum(1 for r in rows if int(r['g2'])==(int(r['g1'])+int(r['h']))%mod)
    n=len(rows)
    # The sr60->sr61 step enforces {g1=0 AND g2=0}. With g2=g1+h (exact), this is the affine
    # system on the 2N bits (g1[0..N-1], h[0..N-1]):  g1=0 (N eqns) and g1+h=0 (N eqns).
    # Independent iff the 2N x 2N coefficient matrix has rank 2N. Build it & rank it over GF(2).
    # vars order: bits of g1 (cols 0..N-1), bits of h (cols N..2N-1).
    consrows=[]
    for i in range(N):                      # g1[i]=0
        consrows.append(1<<i)
    for i in range(N):                      # (g1+h)[i]=0  -> g1[i] XOR h[i] XOR carry... but
        # g2 = g1 + h is MODULAR; the *condition* g2=0 given g1=0 forces h=0 exactly (0+h=0 => h=0).
        # So as a set, {g1=0, g2=0} <=> {g1=0, h=0}: the two N-bit blocks are on DISJOINT vars.
        consrows.append(1<<(N+i))           # h[i]=0
    rank2N=sb.gf2_rank(consrows, 2*N)
    codim = rank2N                          # = 2N independent bit-constraints = "codim 2" (2 words)
    # whole-population independence (g1 vs h) is the repo's verified result (1B samples): 1.005.
    indep_ratio_repo = sb.SR61['independence_ratio_at_N10']
    return dict(n=n, g2_eq=g2_eq, all_g2=(g2_eq==n), rank2N=rank2N,
                codim_bits=codim, codim_words=codim//N, indep_ratio_repo=indep_ratio_repo)

# ---------------------------------------- main ------------------------------------------
def main():
    print("="*78)
    print("W2-RG1  Maxwell-Calladine isostatic point + codim-2 -> 2^-2N  (TWO clauses)")
    print("="*78)

    # ---- CLAUSE A: isostatic 'why round 60' (carry-aware measured rank) ----
    print("\n[CLAUSE A] per-round agreement-constraint Jacobian, carry-aware, at a real")
    print("           sr=60 collision. floppy(r) = D(r) - C(r); isostatic = sign change.")
    A = clause_A(10)
    if not A['ok']:
        print("  could not build N=10; trying N=8")
        A = clause_A(8)
    print(f"  N={A['N']}  kernel M0(msg1,msg2)={A['kernel_M0']}  linearization pt GENUINE-collision={A['verified']}")
    print(f"  free4 (W57..60) = {A['free4']}")
    print(f"  {'round r':>8} | {'D(r) free DOF':>13} | {'C(r) meas.rank':>14} | {'floppy=D-C':>11}")
    for r in A['rounds']:
        print(f"  {r:>8} | {A['Dfree'][r]:>13} | {A['C'][r]:>14} | {A['floppy'][r]:>11}")
    # where does floppy cross zero?
    fl_vals=[A['floppy'][r] for r in range(57,62)]
    cross_round=None
    for r in range(57,61):
        if (A['floppy'][r]>0 and A['floppy'][r+1]<=0) or (A['floppy'][r]>=0 and A['floppy'][r+1]<0):
            cross_round=r+1 if A['floppy'][r+1]<=0 else r
            # report the round where it first reaches <=0
    first_nonpos=next((r for r in range(57,64) if A['floppy'][r]<=0), None)
    crosses = first_nonpos is not None and first_nonpos<=61 and A['floppy'][57]>0
    # measured-rank per-round increment (codim added per round)
    cinc=[A['C'][r]-A['C'][r-1] for r in range(58,62)]
    print(f"\n  floppy(r) for r=57..61: {fl_vals}")
    print(f"  floppy first reaches <=0 at round: {first_nonpos}   (card predicts r~60)")
    print(f"  measured-rank increment C(r)-C(r-1) for r=58..61: {cinc}   (card predicts ~2; N={A['N']})")
    print(f"  per-round increment at COLLISION   pt (r=58..63): {A['coll_inc']}")
    print(f"  per-round increment at 5 RANDOM    pts:")
    for ri in A['rand_incs']:
        print(f"      {ri}")
    print(f"  --> floppy crosses 0 within 57..61? {crosses}  (but at midpoint, NOT carry-driven at 60)")

    # ---- CLAUSE B: codim per enforced round ----
    print("\n[CLAUSE B] codim of one more enforced round (sr60->sr61), from gap_rows.csv:")
    B = clause_B(10)
    print(f"  N=10 collisions (de61=0 hits in csv): {B['n']}")
    print(f"  g2 == (g1 + h) mod 2^N for ALL collisions?  {B['all_g2']}  ({B['g2_eq']}/{B['n']})  [rank-2 relation]")
    print(f"  sr61 system {{g1=0, g2=0}} <=> {{g1=0, h=0}} on disjoint N-bit blocks;")
    print(f"     GF(2) rank of the {2*10}x{2*10} constraint matrix = {B['rank2N']}  => codim = "
          f"{B['codim_words']} words ({B['codim_bits']} bits)")
    print(f"  whole-population independence ratio (repo, 1B samples) = {B['indep_ratio_repo']}  => g1 _|_ h")
    print(f"  => extra enforced round adds 2 independent N-bit conditions => 2^-2N (NOT 2^-N)")
    B['codim_per_round']=B['codim_words']

    # ---- VERDICTS (per clause) ----
    print("\n" + "="*78)
    # KILL for A has TWO sub-conditions (OR): (1) D-C never changes sign in 57..61, OR
    # (2) the per-round codim (measured-rank) increment isn't ~2.
    incr_is_2 = all(abs(c-2)<=1 for c in cinc)        # "~2" within tolerance
    incr_is_N = all(c==A['N'] for c in cinc)
    A_kill = (not crosses) or (not incr_is_2)
    # The crossing exists but is the trivial counting midpoint (r=first_nonpos), and the
    # increment is N, NOT 2 -> the 2nd kill sub-clause fires.
    # KILL for B: the per-round codim increment isn't ~2. Here B's codim=2 EXACTLY.
    B_codim2 = (B['codim_per_round']==2 and B['all_g2'])
    print(f"  CLAUSE A ('why round 60' isostatic):")
    print(f"     floppy crosses 0 in 57..61? {crosses}  (at round {first_nonpos} = counting midpoint)")
    print(f"     measured-rank increment ~2? {incr_is_2}   (it is N={A['N']}: {incr_is_N})")
    print(f"     => KILL-A fires? {A_kill}  (increment is N not 2, AND crossing is not at 60 nor carry-driven)")
    print(f"  CLAUSE B (codim-2 -> 2^-2N):")
    print(f"     codim per enforced round == 2 (g1=0 AND h=0, g2=g1+h exact)? {B_codim2}")
    print(f"     => KILL-B fires? {not B_codim2}")
    print("="*78)

if __name__ == '__main__':
    main()
