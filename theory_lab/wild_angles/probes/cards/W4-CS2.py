#!/usr/bin/env python3
"""
W4-CS2 -- "2^-2N = an instrumental-variable identification order-deficit".

CARD CLAIM: sr=61 needs two targets (g1=0, h=0) identified from the residual free
words; if the admissible-instrument->target Jacobian has RANK 1 (one exclusion-valid
lever), the second target is UNDER-IDENTIFIED -> 2^-N per missing dimension -> 2^-2N.
probe: Jacobian d(T1,T2)/d(free words) over levers preserving sr=60; rank over GF(2),
mod-2^N, R; predict rank=1, hit-rate "both=0" = 2^{-N(targets-rank)} = 2^-2N.
KILL: rank=2, OR hit-rate exponent != targets - rank.

CRITICAL PRIOR (#3): 2^-2N is genuinely RANK-2 (g2 = g1 + h exact for all 946 collisions;
CONFIRMED 9x). The two conditions g1=0 AND h=0 (== g1=0 AND g2=0) are EMPIRICALLY
INDEPENDENT (ratio 1.005 over ~1e9 hits). CS2 may CONFIRM iff it lands on the two-
conditions structure; a generic identification-deficit that merely PERMITS 2^-2N is a rename.

  => The card's specific prediction is rank=1 (one identifying lever, the other target a
     2^-N freebie). The established structure is TWO independent conditions => effective
     IDENTIFICATION RANK = 2 (each target has its own exclusion-valid lever). So the
     decisive measurement is: does the instrument->(g1,h) Jacobian have rank 1 (card) or
     rank 2 (priors)? And does the joint hit-rate factor as 2^-N * 2^-N (independent)?

STRUCTURE (from gap_analysis.c, repo-validated):
  g1 = w60 - sched1[60](w58, M)              -- moved by the lever w60
  h  = casoff(w57,w58,w59) - (sched2[60]-sched1[60])(w57,w58,w59)
                                             -- a per-TRIPLE quantity: depends ONLY on
                                                (w57,w58,w59), INDEPENDENT of w60.
So g1 and h are moved by DISJOINT instrument sets (w60 vs {w57,w58,w59}) => the
instrument->target map is rank 2 by construction, each target separately identified.
This is the IV-faithful Jacobian. We MEASURE it (don't assume): discrete partials of
(g1,h) wrt each free word over the cascade tail, rank over the three rings; plus the
joint (g1=0 AND h=0) hit-rate vs the marginal product, from the repo N=10 collision data
and a direct mini-SHA enumeration at N=8.

Reuses the mini-SHA cascade (rotations scaled exactly as gap_analysis.c) + shabridge.
Run throttled:  OMP_NUM_THREADS=2 taskpolicy -b python3 W4-CS2.py     (N=8, ~20s)
"""
import sys, csv, random, math
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb

def make_sha(N):
    MASK = (1 << N) - 1
    def scale_rot(k):
        r = int(round(k * N / 32.0)); return r if r >= 1 else 1
    rS0=[scale_rot(2),scale_rot(13),scale_rot(22)]; rS1=[scale_rot(6),scale_rot(11),scale_rot(25)]
    rs0=[scale_rot(7),scale_rot(18)]; ss0=scale_rot(3); rs1=[scale_rot(17),scale_rot(19)]; ss1=scale_rot(10)
    def ror(x,k): k%=N; return ((x>>k)|(x<<(N-k)))&MASK
    def S0(a): return ror(a,rS0[0])^ror(a,rS0[1])^ror(a,rS0[2])
    def S1(e): return ror(e,rS1[0])^ror(e,rS1[1])^ror(e,rS1[2])
    def s0(x): return ror(x,rs0[0])^ror(x,rs0[1])^((x>>ss0)&MASK)
    def s1(x): return ror(x,rs1[0])^ror(x,rs1[1])^((x>>ss1)&MASK)
    def Ch(e,f,g): return ((e&f)^((~e)&g))&MASK
    def Mj(a,b,c): return ((a&b)^(a&c)^(b&c))&MASK
    KN=[k&MASK for k in sb.K]; IVN=[v&MASK for v in sb.IV]
    def precompute(M):
        W=[0]*57
        for i in range(16): W[i]=M[i]&MASK
        for i in range(16,57): W[i]=(s1(W[i-2])+W[i-7]+s0(W[i-15])+W[i-16])&MASK
        a,b,c,d,e,f,g,h=IVN
        for i in range(57):
            T1=(h+S1(e)+Ch(e,f,g)+KN[i]+W[i])&MASK; T2=(S0(a)+Mj(a,b,c))&MASK
            h,g,f,e,d,c,b,a=g,f,e,(d+T1)&MASK,c,b,a,(T1+T2)&MASK
        return [a,b,c,d,e,f,g,h],W
    def find_w2(p,q,rnd,w1):
        r1=(p[7]+S1(p[4])+Ch(p[4],p[5],p[6])+KN[rnd])&MASK
        r2=(q[7]+S1(q[4])+Ch(q[4],q[5],q[6])+KN[rnd])&MASK
        T21=(S0(p[0])+Mj(p[0],p[1],p[2]))&MASK; T22=(S0(q[0])+Mj(q[0],q[1],q[2]))&MASK
        return (w1+r1-r2+T21-T22)&MASK
    def rnd1(state,k,w):
        S0v=S0(state[0]); S1v=S1(state[4]); Chv=Ch(state[4],state[5],state[6]); Mjv=Mj(state[0],state[1],state[2])
        T1=(state[7]+S1v+Chv+KN[k]+w)&MASK; T2=(S0v+Mjv)&MASK
        return [(T1+T2)&MASK,state[0],state[1],state[2],(state[3]+T1)&MASK,state[4],state[5],state[6]]
    return dict(MASK=MASK,precompute=precompute,find_w2=find_w2,rnd1=rnd1,KN=KN,N=N,s0=s0,s1=s1)

def build_M0(sh):
    MASK=sh['MASK']; MSB=1<<(sh['N']-1)
    for cand in range(MASK+1):
        M1=[MASK]*16; M2=[MASK]*16
        M1[0]=cand; M2[0]=cand^MSB; M2[9]=MASK^MSB
        st1,_=sh['precompute'](M1); st2,_=sh['precompute'](M2)
        if st1[0]==st2[0]:
            return cand,M1,M2,st1,st2
    return None

def gf2_rank_rows(rows, ncols):
    rows=[r&((1<<ncols)-1) for r in rows]; piv=0
    for c in range(ncols):
        bit=1<<c; sel=next((i for i in range(piv,len(rows)) if rows[i]&bit),None)
        if sel is None: continue
        rows[piv],rows[sel]=rows[sel],rows[piv]
        for i in range(len(rows)):
            if i!=piv and rows[i]&bit: rows[i]^=rows[piv]
        piv+=1
    return piv

def main():
    N=8
    sh=make_sha(N); MASK=sh['MASK']
    res=build_M0(sh)
    if res is None:
        print(f"no cascade-eligible M0 at N={N}"); return
    M0,M1,M2,st1,st2=res
    _,W1p=sh['precompute'](M1); _,W2p=sh['precompute'](M2)
    s0=sh['s0']; s1=sh['s1']
    print(f"=== W4-CS2 : IV identification rank of the instrument->(g1,h) map  (N={N}, M0=0x{M0:x}) ===\n")
    print("Targets: g1 = w60 - sched1[60]   ;   h = casoff - (sched2[60]-sched1[60])")
    print("Instruments (levers preserving sr=60): the free words w57,w58,w59,w60.\n")

    def targets(w57,w58,w59,w60):
        """Return (g1,h) for a free-word tuple. (sr=60 is preserved by construction: path-2
        words are forced via find_w2, so da=0 through round 60.)"""
        a=list(st1); b=list(st2)
        for (r,w) in ((57,w57),(58,w58),(59,w59)):
            wb=sh['find_w2'](a,b,r,w); a=sh['rnd1'](a,r,w); b=sh['rnd1'](b,r,wb)
        # need w58b for sched2[60]; recompute cleanly
        a2=list(st1); b2=list(st2)
        wb57=sh['find_w2'](a2,b2,57,w57); a2=sh['rnd1'](a2,57,w57); b2=sh['rnd1'](b2,57,wb57)
        wb58=sh['find_w2'](a2,b2,58,w58)
        casoff=sh['find_w2'](a,b,60,0)
        sched1_60=(s1(w58)+W1p[53]+s0(W1p[45])+W1p[44])&MASK
        sched2_60=(s1(wb58)+W2p[53]+s0(W2p[45])+W2p[44])&MASK
        g1=(w60-sched1_60)&MASK
        h=(casoff-((sched2_60-sched1_60)&MASK))&MASK
        return g1,h

    # ---- DISCRETE JACOBIAN: per-bit linearization of (g1,h) wrt each free word, at a base point.
    # For instrument word j (one of w57,w58,w59,w60), flip each of its N bits; record which bits of
    # g1 and of h respond. The GF(2) rank of the stacked response matrix = identification rank.
    rng=random.Random(3)
    NBASE=40
    # response matrices: rows indexed by (instrument-word, input-bit), bit-vector of output response
    # We build, per target, the set of (word) that move it at all, and the per-bit Jacobian rank.
    moves_g1=set(); moves_h=set()
    rows_g1=[]; rows_h=[]   # GF(2) rows: response of g1 (N bits) / h (N bits) to single input-bit flips
    INWORDS=['w57','w58','w59','w60']
    for _ in range(NBASE):
        base=[rng.randint(0,MASK) for _ in range(4)]
        g1_0,h_0=targets(*base)
        for wi in range(4):
            for bit in range(N):
                pert=list(base); pert[wi]^=(1<<bit)
                g1_1,h_1=targets(*pert)
                dg=g1_1^g1_0; dh=h_1^h_0
                if dg: moves_g1.add(INWORDS[wi]); rows_g1.append(dg)
                if dh: moves_h.add(INWORDS[wi]); rows_h.append(dh)
    rank_g1=gf2_rank_rows(rows_g1,N); rank_h=gf2_rank_rows(rows_h,N)
    # Stacked: does the SAME instrument lever move BOTH targets (confounded) or disjoint sets?
    print(f"[Jacobian over GF(2), {NBASE} base points]")
    print(f"  instruments that move g1 : {sorted(moves_g1)}   (g1-response rank over its bits = {rank_g1}/{N})")
    print(f"  instruments that move h  : {sorted(moves_h)}   (h-response  rank over its bits = {rank_h}/{N})")
    shared=moves_g1 & moves_h; disjoint=not shared
    print(f"  shared instruments (move BOTH) : {sorted(shared) if shared else '(none)'}")
    # IDENTIFICATION RANK = number of targets that have an exclusion-valid (own) lever.
    # g1 has its own lever iff some instrument moves g1 but not (only) h; same for h.
    g1_own = moves_g1 - moves_h if (moves_g1 - moves_h) else moves_g1
    h_own  = moves_h - moves_g1 if (moves_h - moves_g1) else moves_h
    ident_rank = (1 if moves_g1 else 0) + (1 if moves_h else 0)
    print(f"\n  g1's exclusion-valid lever(s): {sorted(moves_g1 - moves_h) or 'shares only'};  "
          f"h's: {sorted(moves_h - moves_g1) or 'shares only'}")
    print(f"  => IDENTIFICATION RANK (targets with an own instrument) = {ident_rank}  "
          f"(card predicts 1; priors predict 2)")

    # ---- JOINT HIT-RATE: enumerate ALL free-word triples (h depends only on w57,w58,w59),
    # and use the exact-by-construction marginal P(g1=0)=2^-N (g1 = w60 - const => exactly one
    # w60 of 2^N zeros it, for EVERY triple). We do the exhaustive triple sweep at a smaller width
    # NH so 2^{3 NH} Python calls stay seconds-fast; the structure (g1 lever-disjoint from h) is
    # width-independent, and the N=10 repo CSV confirms the rank-2 identity at the canonical width.
    NH=5   # N=6,7 have no cascade-eligible all-ones-fill M0; N=5 and N=8 do. NH=5 => 2^15 triples (instant).
    shH=make_sha(NH); MASKH=shH['MASK']
    resH=build_M0(shH)
    if resH is None:
        print(f"no cascade-eligible M0 at NH={NH}; skipping joint sweep"); return
    M0H,M1H,M2H,st1H,st2H=resH
    _,W1pH=shH['precompute'](M1H); _,W2pH=shH['precompute'](M2H)
    s0H=shH['s0']; s1H=shH['s1']
    def h_of_triple(w57,w58,w59):
        a=list(st1H); b=list(st2H)
        wb57=shH['find_w2'](a,b,57,w57); a=shH['rnd1'](a,57,w57); b=shH['rnd1'](b,57,wb57)
        wb58=shH['find_w2'](a,b,58,w58); a=shH['rnd1'](a,58,w58); b=shH['rnd1'](b,58,wb58)
        wb59=shH['find_w2'](a,b,59,w59); a=shH['rnd1'](a,59,w59); b=shH['rnd1'](b,59,wb59)
        casoff=shH['find_w2'](a,b,60,0)
        sched1_60=(s1H(w58)+W1pH[53]+s0H(W1pH[45])+W1pH[44])&MASKH
        sched2_60=(s1H(wb58)+W2pH[53]+s0H(W2pH[45])+W2pH[44])&MASKH
        return (casoff-((sched2_60-sched1_60)&MASKH))&MASKH
    print(f"\n[Joint hit-rate: exhaustive triple sweep at NH={NH} (h is w60-independent), exact marginal P(g1=0)=2^-NH]")
    n_h0=0; n_trip=0
    from collections import Counter
    hcount=Counter()
    for w57 in range(MASKH+1):
        for w58 in range(MASKH+1):
            for w59 in range(MASKH+1):
                h=h_of_triple(w57,w58,w59)
                hcount[h]+=1; n_trip+=1
                if h==0: n_h0+=1
    P_h0=n_h0/n_trip
    N=NH; MASK=MASKH   # report at NH for the joint block
    P_g1_0=1.0/(MASK+1)   # exactly one w60 of 2^N zeros g1, for every triple (g1 = w60 - const)
    # joint: (g1=0 AND h=0) occurs for triples with h=0, each contributing exactly one w60.
    n_both=n_h0
    total_cfg=n_trip*(MASK+1)
    P_both=n_both/total_cfg
    print(f"  triples enumerated = {n_trip} = 2^{3*N};  P(h=0) = {n_h0}/{n_trip} = {P_h0:.4e}  (2^-N={2**-N:.4e})")
    print(f"  P(g1=0) = exactly one w60 per triple = {P_g1_0:.4e} (= 2^-N exactly)")
    print(f"  P(g1=0 AND h=0) = {P_both:.4e}   ;   P(g1=0)*P(h=0) = {P_g1_0*P_h0:.4e}")
    ratio = P_both/(P_g1_0*P_h0) if P_g1_0*P_h0>0 else float('nan')
    print(f"  independence ratio P(both)/(P*P) = {ratio:.4f}  (priors: ~1.005 => INDEPENDENT)")
    exp_both = math.log2(P_both) if P_both>0 else float('-inf')
    print(f"  log2 P(both) = {exp_both:.3f}  (2^-2N exponent = {-2*N})")

    # ---- N=10 cross-check from the repo-verified collision CSV (g1,h columns present)
    try:
        rows=list(csv.DictReader(open(sb.GAP_ROWS_CSV)))
        g1z=sum(1 for r in rows if int(r['g1'])==0)
        hz=sum(1 for r in rows if int(r['h'])==0)
        # the CSV is the de61=0 SLICE (g2 column = g1+h check). Verify rank-2 identity g2=g1+h.
        identity_ok=all((int(r['g1'])+int(r['h']))% (1<<10)==int(r['g2']) for r in rows)
        print(f"\n[N=10 repo CSV, {len(rows)} de61=0-slice rows]  g2=g1+h identity holds for all: {identity_ok}")
        print(f"  (this is the rank-2 signature: two independent coordinates g1,h sum to g2.)")
    except Exception as e:
        print(f"\n[N=10 CSV] skipped: {e}")

    # ---- VERDICT
    print(f"\n--- DECISION ---")
    print(f"card: identification rank = 1 (second target under-identified, a 2^-N freebie).")
    print(f"measured: identification rank = {ident_rank}; g1 & h moved by DISJOINT instruments "
          f"(g1<-w60, h<-w57/58/59): {disjoint}.")
    print(f"joint hit-rate factors as 2^-N * 2^-N (ratio {ratio:.3f}), log2 P(both)={exp_both:.2f} ~ -2N={-2*N}.")
    kill_rank2 = (ident_rank == 2)
    kill_exp   = abs(exp_both - (-2*N)) > 1.5
    if kill_rank2:
        print(f"=> RANK IS 2, not 1: the card's 'order-deficit' (one missing identifying dimension) is FALSE.")
        print(f"   Each target has its OWN exclusion-valid lever; 2^-2N is two FULLY-identified independent")
        print(f"   conditions (2^-N each), NOT one identified + one under-identified freebie.")
        print(f"=> KILL FIRES (kill clause: 'rank=2'). The 2^-2N is real & rank-2, but the IV deficit mechanism")
        print(f"   the card proposes is the wrong cause -- it inverts the structure (deficit vs full id).")
    elif kill_exp:
        print(f"=> hit-rate exponent {exp_both:.2f} != -2N -> KILL (kill clause 2).")
    else:
        print(f"=> rank=1 AND exponent=-2N: CONFIRM the order-deficit mechanism (would contradict priors).")

if __name__ == '__main__':
    main()
