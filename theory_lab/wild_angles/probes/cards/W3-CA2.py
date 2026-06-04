#!/usr/bin/env python3
"""
W3-CA2 -- Delta-lens -> why de58 is the lone non-trivial fibre.

CARD CLAIM (CATALOG): a delta-lens acts on DIFFERENCES. de57/de59/de60 constant (=1)
= identity deltas (the functor sends them to identities); de58 = the unique non-identity
image. Functoriality predicts |de58| is the lone DOF.

PROBE (per the card): N=8..12, take message TRIANGLES M1->M2->M3, check the delta
COMPOSITION law  de_r(1->3) = de_r(1->2) (+) de_r(2->3)  (modular for de58, identity for
the constants); count de58's fibre = 2^hw(db56)?

KILL: constants don't compose, OR de58 fibre != 2^hw(db56).

THE OPEN QUESTION (lead finding #5): two prior partials -- QI3 localized ALL freedom to
de58 (30/30 chambers) but did NOT quantify it; NT3 found |de58| = 2^hw(db56) is a Maj/AND
image count. The CONFIRMED bar here: does the delta-lens *fibre structure* DERIVE the
2^hw(db56) growth law, or merely restate de58 is the lone non-trivial fibre?

So we test THREE things, escalating:
  (A) COMPOSITION (functoriality): for triangles M1->M2->M3, does
      de_r(1->3) = de_r(1->2) +/xor de_r(2->3)?  constants must compose to identity;
      de58 must compose ADDITIVELY (mod 2^N). This is the delta-lens's defining law.
  (B) FIBRE SIZE: |de58 image set over the cascade tail freedom| =? 2^hw(db56).
  (C) DERIVATION (the prize): does the delta-lens give an INDEPENDENT reason the fibre
      has size 2^hw(db56) -- i.e. does additivity + a rank argument PREDICT hw(db56),
      or is 2^hw(db56) injected from the Maj-image count (NT3) and merely *consistent*
      with additivity?  We test whether the de58 fibre is a SUBGROUP (closed under +)
      of order 2^hw(db56): if the delta-lens functor structure forces de58 to be an
      additive subgroup whose rank we can read off from db56, that is a derivation;
      if the fibre is NOT a clean subgroup (just a set of size 2^hw), additivity does
      not explain the EXPONENT and the card only restates the lone-fibre fact.

Reuses the QI3 cascade builder (exact repo de58_enum.c recipe).
"""
import sys, math, collections
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
import transfer_operator as to

# ============================================================================
# CANONICAL de-set measurement -- mirrors W2-NT3.py EXACTLY (which reproduces the
# pinned sb.DE_SIZES ground truth). KEY: db56 = b-register XOR diff (s[1]) at round 56,
# and de_r is swept over a free w1 per round with w2 forced to hold da=0 (so de58 ranges
# over the (w57,w58) cascade tail, not just w57). This is the recipe the growth law
# 2^hw(db56) is defined against -- using anything else strawmans the card.
# ============================================================================
K32 = sb.s.K; IV32 = sb.s.IV

def mini(N):
    m = (1 << N) - 1
    rp = to._rot_params(N)
    S0r, S1r, s0r, s1r = rp['S0'], rp['S1'], rp['s0'], rp['s1']
    def ror(x, k): k %= N; return ((x >> k) | (x << (N - k))) & m
    S0 = lambda a: ror(a,S0r[0])^ror(a,S0r[1])^ror(a,S0r[2])
    S1 = lambda e: ror(e,S1r[0])^ror(e,S1r[1])^ror(e,S1r[2])
    sig0 = lambda x: ror(x,s0r[0])^ror(x,s0r[1])^((x>>s0r[2])&m)
    sig1 = lambda x: ror(x,s1r[0])^ror(x,s1r[1])^((x>>s1r[2])&m)
    Ch = lambda e,f,g: ((e&f)^((~e&m)&g))&m
    Maj = lambda a,b,c: ((a&b)^(a&c)^(b&c))&m
    KN = [k&m for k in K32]; IVN=[v&m for v in IV32]
    return dict(m=m,S0=S0,S1=S1,sig0=sig0,sig1=sig1,Ch=Ch,Maj=Maj,KN=KN,IVN=IVN,N=N)

def precompute(P, M):
    m,sig0,sig1=P['m'],P['sig0'],P['sig1']; S0,S1,Ch,Maj,KN,IVN=P['S0'],P['S1'],P['Ch'],P['Maj'],P['KN'],P['IVN']
    W=[M[i]&m for i in range(16)]+[0]*41
    for i in range(16,57): W[i]=(sig1(W[i-2])+W[i-7]+sig0(W[i-15])+W[i-16])&m
    a,b,c,d,e,f,g,h=IVN
    for i in range(57):
        T1=(h+S1(e)+Ch(e,f,g)+KN[i]+W[i])&m; T2=(S0(a)+Maj(a,b,c))&m
        h,g,f,e,d,c,b,a=g,f,e,(d+T1)&m,c,b,a,(T1+T2)&m
    return (a,b,c,d,e,f,g,h), W

def rnd(P, st, k, w):
    m,S0,S1,Ch,Maj=P['m'],P['S0'],P['S1'],P['Ch'],P['Maj']
    a,b,c,d,e,f,g,h=st
    T1=(h+S1(e)+Ch(e,f,g)+k+w)&m; T2=(S0(a)+Maj(a,b,c))&m
    return ((T1+T2)&m,a,b,c,(d+T1)&m,e,f,g)

def step(P, s1, s2, k, w1):
    """advance both paths one round; w2 forced so da stays 0 (find_w2 trick, exact NT3)."""
    m=P['m']; S1,Ch,S0,Maj=P['S1'],P['Ch'],P['S0'],P['Maj']
    T1_1=(s1[7]+S1(s1[4])+Ch(s1[4],s1[5],s1[6])+k+w1)&m; T2_1=(S0(s1[0])+Maj(s1[0],s1[1],s1[2]))&m
    a1n=(T1_1+T2_1)&m
    r2=(s2[7]+S1(s2[4])+Ch(s2[4],s2[5],s2[6])+k)&m; T22=(S0(s2[0])+Maj(s2[0],s2[1],s2[2]))&m
    w2=(a1n-T22-r2)&m
    return rnd(P,s1,k,w1), rnd(P,s2,k,w2)

def de_sets_canon(N, M1, M2):
    """EXACT NT3 de-set measurement. Returns (sizes dict, db56=b-XOR diff, de58 set)."""
    P=mini(N); m=P['m']; KN=P['KN']
    st1_56,_=precompute(P,M1); st2_56,_=precompute(P,M2)
    held=(st1_56[0]==st2_56[0])
    db56=(st1_56[1]^st2_56[1])  # b-register XOR diff at round 56 -- the growth-law seed
    de={57:set(),58:set(),59:set(),60:set()}
    for w57 in (range(m+1) if (m+1)<=65536 else range(0,m+1,max(1,(m+1)//65536))):
        s1a,s2a=step(P,st1_56,st2_56,KN[57],w57)
        de[57].add((s1a[4]-s2a[4])&m)
        for w58 in (range(m+1) if (m+1)<=2048 else range(0,m+1,max(1,(m+1)//2048))):
            s1b,s2b=step(P,s1a,s2a,KN[58],w58)
            de[58].add((s1b[4]-s2b[4])&m)
            if w58<8:
                for w59 in range(min(m+1,64)):
                    s1c,s2c=step(P,s1b,s2b,KN[59],w59)
                    de[59].add((s1c[4]-s2c[4])&m)
                    s1d,s2d=step(P,s1c,s2c,KN[60],0)
                    de[60].add((s1d[4]-s2d[4])&m)
    return {r:len(de[r]) for r in de}, db56, de[58]

def de58_ground(N, M1, M2):
    """The single de_r 'delta' at the cascade GROUND ray (all free words 0), for the
    composition (functoriality) test."""
    P=mini(N); KN=P['KN']
    st1,_=precompute(P,M1); st2,_=precompute(P,M2)
    s1=list(st1); s2=list(st2); val={}
    for k in (57,58,59,60):
        s1,s2=step(P,s1,s2,KN[k],0)
        val[k]=(s1[4]-s2[4])&P['m']
    return val

def find_M0_canon(N):
    """Canonical auto-M0 (all-ones fill, MSB kernel) -- the chamber DE_SIZES is defined on."""
    P=mini(N); m=P['m']; MSB=1<<(N-1)
    for cand in range(m+1):
        M1=[m]*16; M2=[m]*16; M1[0]=cand; M2[0]=cand^MSB; M2[9]=m^MSB
        st1,_=precompute(P,M1); st2,_=precompute(P,M2)
        if st1[0]==st2[0]: return cand,M1,M2
    return None,None,None

# ---- legacy random-chamber builder kept for the composition triangle scan ----
def make_ops(N):
    MASK = (1 << N) - 1
    def ror(x, r): r %= N; return ((x >> r) | (x << (N - r))) & MASK
    def shr(x, r): return (x >> r) & MASK
    base = dict(S0=(2,13,22), S1=(6,11,25), s0=(7,18,3), s1=(17,19,10))
    sc = {k: tuple(max(0, min(N-1, round(a*N/32))) for a in t) for k,t in base.items()}
    Sig0 = lambda a: (lambda r: ror(a,r[0])^ror(a,r[1])^ror(a,r[2]))(sc['S0'])
    Sig1 = lambda e: (lambda r: ror(e,r[0])^ror(e,r[1])^ror(e,r[2]))(sc['S1'])
    sig0 = lambda x: (lambda r: ror(x,r[0])^ror(x,r[1])^shr(x,r[2]))(sc['s0'])
    sig1 = lambda x: (lambda r: ror(x,r[0])^ror(x,r[1])^shr(x,r[2]))(sc['s1'])
    Ch  = lambda e,f,g: (e & f) ^ ((~e & MASK) & g)
    Maj = lambda a,b,c: (a & b) ^ (a & c) ^ (b & c)
    def add(*xs):
        s = 0
        for x in xs: s = (s + x) & MASK
        return s
    sub = lambda a,b: (a - b) & MASK
    return MASK, ror, shr, Sig0, Sig1, sig0, sig1, Ch, Maj, add, sub

def builder(N):
    MASK, ror, shr, Sig0, Sig1, sig0, sig1, Ch, Maj, add, sub = make_ops(N)
    Kw = [k & MASK for k in sb.K]
    def sha_round(s, r, w):
        a,b,c,d,e,f,g,h = s
        T1 = add(h, Sig1(e), Ch(e,f,g), Kw[r], w)
        T2 = add(Sig0(a), Maj(a,b,c))
        return [add(T1,T2), a, b, c, add(d,T1), e, f, g]
    def precompute(M, kt):
        W = list(M) + [0]*(64-len(M))
        for i in range(16, 64):
            W[i] = add(sig1(W[i-2]), W[i-7], sig0(W[i-15]), W[i-16])
        s = [v & MASK for v in sb.IV]
        for r in range(kt): s = sha_round(s, r, W[r])
        return s, W
    def cas_off(s1, s2):  # path-2 correction that holds da=0
        dh = sub(s1[7], s2[7])
        dSig1 = sub(Sig1(s1[4]), Sig1(s2[4]))
        dCh = sub(Ch(s1[4],s1[5],s1[6]), Ch(s2[4],s2[5],s2[6]))
        T2_1 = add(Sig0(s1[0]), Maj(s1[0],s1[1],s1[2]))
        T2_2 = add(Sig0(s2[0]), Maj(s2[0],s2[1],s2[2]))
        return add(dh, dSig1, dCh, sub(T2_1, T2_2))
    return MASK, sha_round, precompute, cas_off, sub

def de_sets(N, M1, M2, full_cap=1<<13):
    """de_k = (s1[4]-s2[4]) after cascade round k, over W57; the exact repo measurement.
    Also returns db56 = e-reg diff at round-57 input (seeds the growth law)."""
    MASK, sha_round, precompute, cas_off, sub = builder(N)
    s1_56,_ = precompute(M1, 57); s2_56,_ = precompute(M2, 57)
    held = (s1_56[0] == s2_56[0])
    db56 = sub(s1_56[4], s2_56[4]); hw_db56 = bin(db56).count('1')
    de = {57:set(),58:set(),59:set(),60:set()}
    total = 1<<N; step = 1 if total<=full_cap else max(1,total//full_cap)
    for w57 in range(0, total, step):
        s1=list(s1_56); s2=list(s2_56)
        for k,(w_a) in zip((57,58,59,60),(w57,0,0,0)):
            cw = cas_off(s1,s2)
            s1 = sha_round(s1,k,w_a); s2 = sha_round(s2,k,(w_a+cw)&MASK)
            de[k].add(sub(s1[4],s2[4]))
    return de, db56, hw_db56, held

def de58_value(N, M1, M2):
    """The single de58 'delta' for a triangle leg at the cascade ground point (w57=0):
    the realized e-register modular difference after round 58. Used for composition."""
    MASK, sha_round, precompute, cas_off, sub = builder(N)
    s1_56,_ = precompute(M1,57); s2_56,_ = precompute(M2,57)
    s1=list(s1_56); s2=list(s2_56)
    val = {}
    for k,(w_a) in zip((57,58,59,60),(0,0,0,0)):
        cw = cas_off(s1,s2)
        s1 = sha_round(s1,k,w_a); s2 = sha_round(s2,k,(w_a+cw)&MASK)
        val[k] = sub(s1[4],s2[4])
    return val

def find_chambers(N, n_want=6, seed=2027):
    """Find (m0,fill,bit) chambers where cascade-1 holds (da=0) with hw(db56)>0."""
    MASK, sha_round, precompute, cas_off, sub = builder(N)
    found=[]; st=seed&0xffffffff
    def nxt():
        nonlocal st
        st^=(st<<13)&0xffffffff; st^=st>>17; st^=(st<<5)&0xffffffff; return st
    t=0
    while len(found)<n_want and t<400000:
        t+=1; m0=nxt()&MASK; fill=nxt()&MASK; bit=nxt()%N
        M1=[m0]+[fill]*15; M2=list(M1); M2[0]^=(1<<bit)&MASK; M2[9]^=(1<<bit)&MASK
        s1,_=precompute(M1,57); s2,_=precompute(M2,57)
        if s1[0]==s2[0] and sub(s1[4],s2[4])!=0: found.append((m0,fill,bit))
    return found

def is_subgroup(S, N):
    """Is the set S (of N-bit ints) an additive subgroup of Z/2^N (closed under +, has 0)?
    Returns (closed, has0, order)."""
    M=(1<<N)-1
    has0 = 0 in S
    closed = all(((a+b)&M) in S for a in S for b in S) if len(S)<=512 else None
    return closed, has0, len(S)

def cascade_holds_set(N):
    """Which single message differences (kernel-bit flips in words 0&9) keep da=0 at M0?
    FINDING: exactly ONE (the kernel MSB) -- the cascade category over a base point has a
    SINGLE non-identity morphism, so there is no nontrivial composition TRIANGLE to test;
    the only composition is self-inverse (MSB then MSB = identity)."""
    P=mini(N); MSB=1<<(N-1)
    cand,M1,_=find_M0_canon(N)
    holds=[]
    for b in range(N):
        M2=list(M1); M2[0]^=(1<<b); M2[9]^=(1<<b)
        s1,_=precompute(P,M1); s2,_=precompute(P,M2)
        if s1[0]==s2[0]: holds.append(b)
    return cand, M1, holds

if __name__ == '__main__':
    print("=== W3-CA2: delta-lens fibre structure -> de58 growth law 2^hw(db56)? ===")
    print("    Ground truth: de57=de59=de60=1 (identity deltas); de58 = 2^hw(db56) (NT3 Maj-image).")
    print("    Using EXACT NT3/DE_SIZES recipe (db56 = b-XOR diff; de58 swept over (w57,w58)).")
    print("    CONFIRMED bar (#5): does the delta-lens DERIVE 2^hw(db56), or restate the lone fibre?\n")

    print("### Part B/C: growth law + fibre algebraic structure (canonical chamber) ###")
    for N in (8, 10, 12):
        cand,M1,M2=find_M0_canon(N)
        if cand is None: print(f"N={N}: no canonical M0"); continue
        sizes, db56, de58 = de_sets_canon(N, M1, M2)
        hw_db56=sb.hw(db56); MASK=(1<<N)-1
        gt = sb.DE_SIZES.get(N)
        growth = (sizes[58]==2**hw_db56)
        # subgroup / coset structure of the de58 fibre
        closed,has0,order = is_subgroup(de58,N)
        d0=sorted(de58)[0]; shifted={(x-d0)&MASK for x in de58}
        c2,h2,o2 = is_subgroup(shifted,N)
        xorclosed = all(((a^b)&MASK) in de58 for a in de58 for b in de58) if len(de58)<=512 else None
        print(f"  N={N}: |de|={sizes} (repo {gt})  db56={db56:#0{(N+3)//4+2}x} hw={hw_db56}"
              f" 2^hw={2**hw_db56} | de58==2^hw? {growth}")
        print(f"        de58 additive subgroup? closed={closed} has0={has0} | coset(de58-min)? closed={c2}"
              f" | XOR-closed? {xorclosed}")

    print("\n### Part A: composition / functoriality of the delta-lens ###")
    for N in (8, 10, 12):
        cand, M1, holds = cascade_holds_set(N)
        MASK=(1<<N)-1
        print(f"  --- N={N}  M0={cand:#x}: single-bit diffs holding da=0 = {holds} "
              f"(=> {len(holds)} non-identity morphism) ---")
        # The one available composition: self-inverse. M1 --MSB--> M2 --MSB--> M1.
        b=holds[0]
        M2=list(M1); M2[0]^=(1<<b); M2[9]^=(1<<b)
        v12=de58_ground(N,M1,M2); v21=de58_ground(N,M2,M1); v11=de58_ground(N,M1,M1)
        # identity composition: de(1->1) must be 0 (identity delta); de(1->2)+de(2->1) =? 0
        for k in (57,58,59,60):
            inv_ok=( (v12[k]+v21[k])&MASK == v11[k] )
            ident = (v11[k]==0)
            tag = "identity-leg(de57/59/60)" if k in (57,59,60) else "de58 (the lone fibre)"
            print(f"    round {k} [{tag}]: de(1->2)={v12[k]} de(2->1)={v21[k]} "
                  f"sum={ (v12[k]+v21[k])&MASK } de(1->1)={v11[k]} | inverse-composes?{inv_ok} id?{ident}")
        print(f"    NOTE: only 1 non-identity morphism exists -> no 3-vertex triangle; the")
        print(f"          additive composition law is tested via self-inverse only (near-vacuous).")

    print("\n=== DERIVATION verdict input ===")
    print("  Composition (functoriality) + constants->identity = the delta-lens DEFINING laws.")
    print("  2^hw(db56) is DERIVED by the delta-lens ONLY IF the de58 fibre is an additive")
    print("  SUBGROUP/coset whose rank = hw(db56) (then group structure forces the exponent).")
    print("  If de58 is a size-2^hw SET that is NOT a coset, additivity is consistent but does")
    print("  NOT predict the EXPONENT -> the card restates the lone fibre (QI3/#5), not derives it.")
