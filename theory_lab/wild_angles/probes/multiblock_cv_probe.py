#!/usr/bin/env python3
"""
multiblock_cv_probe.py  —  the NEXT link after the single-block de58-overflow theorem.

THE ESTABLISHED RESULT (single-block, take as given; SR61_WORKAROUND.md + tunnel_RESULT.md +
coincidence_variety/RESULT_sr61_is_2minus2N.md):
  sr=60 -> sr=61 single-block is 2^-2N and PROVABLY de58-bounded.  sr=61 needs TWO
  independent N-bit conditions:
      g1 = w60 - sched1[60] = 0   (per-MESSAGE absolute schedule match)
      h  = casoff - (sched2[60]-sched1[60]) = 0   (inter-MESSAGE differential compatibility)
  g1 _|_ h (independence ratio ~1.005 over 1B samples).  Any lever on g1's absolute target
  sched1[60] injects a FULL-WIDTH MULTI-REGISTER disturbance at r63, while the only repair
  channel de58 is hw(db56)<=N bits => single-block cannot decouple g1 from h.

THE HOPE (what this probe tests — MULTI-BLOCK):
  Block-1's message (~16N bits) -> chaining value CV (8N-bit state, all 8 registers) via
  Davies-Meyer feed-forward  CV = IV + state_block1[64]  (see repo
  headline_hunt/bets/block2_wang/encoders/absorber_pinned.py:block1_outputs).  CV becomes
  block-2's INITIAL STATE.  KEY structural difference: in block-2 the STATE (CV, from
  block-1) and the SCHEDULE (block-2's message -> sched1[60]) are SEPARATE inputs.  So CV
  is a candidate multi-register-width (8N-bit) uncoupled repair budget.  THE DECISIVE TEST:
  can CV steer h=0 INDEPENDENTLY of g1 / the collision?  If yes -> block-1 pre-sets h=0
  (free), block-2's w60 sets g1=0 => sr=61 = 2^-N.  If the SAME coupling re-appears =>
  multi-block faces the SAME wall and the de58-overflow is intrinsic to the round function.

FAITHFULNESS TO THE REPO (block2_wang, READ-ONLY):
  Block-2's input chaining value is CV = IV + state_block1[64] (Davies-Meyer).  CV1,CV2
  differ by the block-1 RESIDUAL = CV1^CV2 (the repo measured post-FF HW>=66 at N=32; the
  N=8 analog here is HW 25-35).  In block-2 the cascade re-runs from CV (NOT from IV): we
  feed CV as the initial state and re-solve block-2's message for cascade-eligibility
  (da56=0), exactly the role block-1's M0 plays single-block.  ADVERSARIAL: a real sr=61
  lever must move/zero h EXACTLY (full width), not the weak de61 filter, AND the block-2
  collision (de61=de62=de63=0) must hold simultaneously.

ENGINE: reuses the VALIDATED _w5co_engine (N=4 -> 49 colls; N=8 hint colls verified
bit-for-bit vs the repo C enumerator).  READ-ONLY toward the repo.  No SAT.  Throttled.

KEY STRUCTURAL LEMMA (verified, T0 below): within a fixed block-2 cascade, h is INDEPENDENT
of the last free word w60, while g1 = w60 - sched1 ranges over ALL values as w60 varies.
=> sr=61  <=>  EXISTS prefix (w57,w58,w59) with [ h=0  AND  the full collision closes at
w60=sched1 (g1=0) ].  So the WHOLE question is whether block-1's CV can make h=0 coincide
with a block-2 collision more often than 2^-2N.  This lemma lets every test below avoid
finding sparse collisions blindly — it measures the (g1,h,collision) coupling directly.
"""
import sys, time, itertools, random
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes')
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards')
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import _w5co_engine as eng
import shabridge as sb  # noqa: F401  (pins ground truth; primitives re-exported)


# ============================================================================ #
#  GF(2) rank over integers-as-bitmasks.                                        #
# ============================================================================ #
def gf2_rank_vals(vals, N):
    basis = []
    for v in vals:
        v &= (1 << N) - 1
        for b in basis:
            v = min(v, v ^ b)
        if v:
            basis.append(v); basis.sort(reverse=True)
    return len(basis)


# ============================================================================ #
#  MULTI-BLOCK CORE: feed CV (block-1's chaining value) as block-2's INITIAL    #
#  STATE.  Mirrors eng.precompute EXACTLY but seeds round-0 with CV (not IVN).   #
# ============================================================================ #
def precompute_from_cv(M, Mmsg, CV):
    MASK = M['MASK']
    W = [Mmsg[i] & MASK for i in range(16)] + [0] * 41
    for i in range(16, 57):
        W[i] = (M['s1'](W[i-2]) + W[i-7] + M['s0'](W[i-15]) + W[i-16]) & MASK
    a, b, c, d, e, f, g, h = [x & MASK for x in CV]
    for i in range(57):
        T1 = (h + M['S1'](e) + M['Ch'](e, f, g) + M['KN'][i] + W[i]) & MASK
        T2 = (M['S0'](a) + M['Mj'](a, b, c)) & MASK
        h = g; g = f; f = e; e = (d + T1) & MASK
        d = c; c = b; b = a; a = (T1 + T2) & MASK
    return (a, b, c, d, e, f, g, h), W


def block2_tail(M, CV1, CV2, M1, M2, w57, w58, w59, w60):
    """Block-2's sr=60 cascade + (g1,h,de61) with initial state (CV1,CV2) and message
    (M1,M2).  Mirrors neutral_bit_probe.evaluate / _w5co_engine.run_tail, precompute from
    CV.  Returns da56, sched1, h, g1, casoff, collide, de61."""
    MASK = M['MASK']; KN = M['KN']; s0 = M['s0']; s1f = M['s1']
    st1, W1p = precompute_from_cv(M, M1, CV1)
    st2, W2p = precompute_from_cv(M, M2, CV2)
    da56 = (st1[0] - st2[0]) & MASK
    s1, s2 = st1, st2
    w57b = eng.find_w2(s1, s2, 57, w57, M)
    s1 = eng.sha_round(s1, KN[57], w57, M); s2 = eng.sha_round(s2, KN[57], w57b, M)
    w58b = eng.find_w2(s1, s2, 58, w58, M)
    s1 = eng.sha_round(s1, KN[58], w58, M); s2 = eng.sha_round(s2, KN[58], w58b, M)
    w59b = eng.find_w2(s1, s2, 59, w59, M)
    s59a = eng.sha_round(s1, KN[59], w59, M); s59b = eng.sha_round(s2, KN[59], w59b, M)
    casoff = eng.find_w2(s59a, s59b, 60, 0, M)
    w60b = (w60 + casoff) & MASK
    sched1 = (s1f(w58)  + W1p[53] + s0(W1p[45]) + W1p[44]) & MASK
    sched2 = (s1f(w58b) + W2p[53] + s0(W2p[45]) + W2p[44]) & MASK
    h  = (casoff - ((sched2 - sched1) & MASK)) & MASK
    g1 = (w60 - sched1) & MASK
    a = eng.sha_round(s59a, KN[60], w60,  M)
    b = eng.sha_round(s59b, KN[60], w60b, M)
    W1_61 = (s1f(w59)  + W1p[54] + s0(W1p[46]) + W1p[45]) & MASK
    W2_61 = (s1f(w59b) + W2p[54] + s0(W2p[46]) + W2p[45]) & MASK
    W1_62 = (s1f(w60)  + W1p[55] + s0(W1p[47]) + W1p[46]) & MASK
    W2_62 = (s1f(w60b) + W2p[55] + s0(W2p[47]) + W2p[46]) & MASK
    W1_63 = (s1f(W1_61) + W1p[56] + s0(W1p[48]) + W1p[47]) & MASK
    W2_63 = (s1f(W2_61) + W2p[56] + s0(W2p[48]) + W2p[47]) & MASK
    a = eng.sha_round(a, KN[61], W1_61, M); b = eng.sha_round(b, KN[61], W2_61, M)
    de61 = (a[4] - b[4]) & MASK
    a = eng.sha_round(a, KN[62], W1_62, M); b = eng.sha_round(b, KN[62], W2_62, M)
    a = eng.sha_round(a, KN[63], W1_63, M); b = eng.sha_round(b, KN[63], W2_63, M)
    collide = (a == b)
    return dict(da56=da56, sched1=sched1, h=h, g1=g1, casoff=casoff,
                collide=collide, de61=de61)


# ============================================================================ #
#  Real block-1 Davies-Meyer chaining value (mirrors absorber_pinned at width N).#
#  Block-1 = 64 rounds + feed-forward CV = IVN + state[64].  Free tail comes from #
#  a block-1 cascade (da56=0); CV1,CV2 differ by the genuine post-FF residual.    #
# ============================================================================ #
def block1_cv(M, setup, free4):
    """Run block-1 (64 rounds, both messages, IVN start), feed-forward to CV.
    Returns (CV1, CV2, residual=CV1^CV2, post_ff_HW)."""
    MASK = M['MASK']; IVN = M['IVN']; KN = M['KN']
    W1p, W2p = setup['W1'], setup['W2']
    w57, w58, w59, w60 = free4
    s1, s2 = setup['st1'], setup['st2']
    w57b = eng.find_w2(s1, s2, 57, w57, M)
    A1 = eng.sha_round(s1, KN[57], w57, M);  A2 = eng.sha_round(s2, KN[57], w57b, M)
    w58b = eng.find_w2(A1, A2, 58, w58, M)
    B1 = eng.sha_round(A1, KN[58], w58, M);  B2 = eng.sha_round(A2, KN[58], w58b, M)
    w59b = eng.find_w2(B1, B2, 59, w59, M)
    C1 = eng.sha_round(B1, KN[59], w59, M);  C2 = eng.sha_round(B2, KN[59], w59b, M)
    co = eng.find_w2(C1, C2, 60, 0, M)
    w60b = (w60 + co) & MASK

    def cv(Wp, fp):
        W = list(Wp) + list(fp)
        W.append((M['s1'](W[59]) + Wp[54] + M['s0'](Wp[46]) + Wp[45]) & MASK)
        W.append((M['s1'](W[60]) + Wp[55] + M['s0'](Wp[47]) + Wp[46]) & MASK)
        W.append((M['s1'](W[61]) + Wp[56] + M['s0'](Wp[48]) + Wp[47]) & MASK)
        a, b, c, d, e, f, g, h = IVN
        for t in range(64):
            T1 = (h + M['S1'](e) + M['Ch'](e, f, g) + KN[t] + W[t]) & MASK
            T2 = (M['S0'](a) + M['Mj'](a, b, c)) & MASK
            h = g; g = f; f = e; e = (d + T1) & MASK
            d = c; c = b; b = a; a = (T1 + T2) & MASK
        fs = (a, b, c, d, e, f, g, h)
        return tuple((IVN[j] + fs[j]) & MASK for j in range(8))

    CV1 = cv(W1p, (w57, w58, w59, w60))
    CV2 = cv(W2p, (w57b, w58b, w59b, w60b))
    residual = tuple(CV1[j] ^ CV2[j] for j in range(8))
    return CV1, CV2, residual, sum(bin(r).count('1') for r in residual)


def block2_setup_from_cv(M, CV1, CV2, fill=None):
    """Re-solve block-2's message word-0 (fill = MASK) so block-2 is cascade-eligible
    (da56=0) — the block-2 analog of block-1's find_M0.  Returns the precompute states
    + schedule words, or None if no fill m0 works for this CV."""
    MASK = M['MASK']
    fill = MASK if fill is None else fill
    for m0 in range(MASK + 1):
        Mb = [m0] + [fill] * 15
        st1, W1p = precompute_from_cv(M, Mb, CV1)
        st2, W2p = precompute_from_cv(M, Mb, CV2)
        if (st1[0] - st2[0]) & MASK == 0:
            return dict(m0=m0, Mb=Mb, st1=st1, st2=st2, W1p=W1p, W2p=W2p)
    return None


# ============================================================================ #
#  Low-level tail evaluator on explicit (states, schedule words) — used by the   #
#  collision/coverage scans (avoids re-running precompute per tail).             #
# ============================================================================ #
def tail_gh(M, ST1, ST2, W1p, W2p, w57, w58, w59, w60, full=True):
    MASK = M['MASK']; KN = M['KN']; s0 = M['s0']; s1f = M['s1']
    w57b = eng.find_w2(ST1, ST2, 57, w57, M)
    P1 = eng.sha_round(ST1, KN[57], w57, M); P2 = eng.sha_round(ST2, KN[57], w57b, M)
    w58b = eng.find_w2(P1, P2, 58, w58, M)
    Q1 = eng.sha_round(P1, KN[58], w58, M);  Q2 = eng.sha_round(P2, KN[58], w58b, M)
    w59b = eng.find_w2(Q1, Q2, 59, w59, M)
    R1 = eng.sha_round(Q1, KN[59], w59, M);  R2 = eng.sha_round(Q2, KN[59], w59b, M)
    co = eng.find_w2(R1, R2, 60, 0, M)
    sched1 = (s1f(w58)  + W1p[53] + s0(W1p[45]) + W1p[44]) & MASK
    sched2 = (s1f(w58b) + W2p[53] + s0(W2p[45]) + W2p[44]) & MASK
    h = (co - ((sched2 - sched1) & MASK)) & MASK
    g1 = (w60 - sched1) & MASK
    w60b = (w60 + co) & MASK
    a = eng.sha_round(R1, KN[60], w60, M); b = eng.sha_round(R2, KN[60], w60b, M)
    W1_61 = (s1f(w59)  + W1p[54] + s0(W1p[46]) + W1p[45]) & MASK
    W2_61 = (s1f(w59b) + W2p[54] + s0(W2p[46]) + W2p[45]) & MASK
    a = eng.sha_round(a, KN[61], W1_61, M); b = eng.sha_round(b, KN[61], W2_61, M)
    de61 = (a[4] - b[4]) & MASK
    if not full:
        return g1, h, de61, None
    W1_62 = (s1f(w60)  + W1p[55] + s0(W1p[47]) + W1p[46]) & MASK
    W2_62 = (s1f(w60b) + W2p[55] + s0(W2p[47]) + W2p[46]) & MASK
    a = eng.sha_round(a, KN[62], W1_62, M); b = eng.sha_round(b, KN[62], W2_62, M)
    W1_63 = (s1f(W1_61) + W1p[56] + s0(W1p[48]) + W1p[47]) & MASK
    W2_63 = (s1f(W2_61) + W2p[56] + s0(W2p[48]) + W2p[47]) & MASK
    a = eng.sha_round(a, KN[63], W1_63, M); b = eng.sha_round(b, KN[63], W2_63, M)
    return g1, h, de61, (a == b)


KNOWN_COLLISIONS = {8: [(131, 70, 82, 92), (131, 140, 71, 87)],
                    10: [(309, 594, 54, 698), (310, 477, 913, 139)]}


# ============================================================================ #
#  T0 — STRUCTURAL LEMMA + GROUNDING.                                            #
# ============================================================================ #
def t0_grounding(M, setup, free):
    MASK = M['MASK']; IVN = M['IVN']
    # grounding: multi-block(CV=IVN) reproduces the validated single-block engine
    sb_ref = eng.run_tail(M, setup, *free)
    mb = block2_tail(M, IVN, IVN, setup['M1'], setup['M2'], *free)
    ground = (mb['collide'] == sb_ref['collide'] and mb['de61'] == sb_ref['de61'])
    # lemma: h independent of w60; g1 spans
    hs = set(); g1s = set()
    for w60 in range(MASK + 1):
        r = block2_tail(M, IVN, IVN, setup['M1'], setup['M2'], free[0], free[1], free[2], w60)
        hs.add(r['h']); g1s.add(r['g1'])
    print(f"  [T0] grounding multiblock(CV=IVN)==single-block: {ground} "
          f"(collide {mb['collide']}, g1 {mb['g1']}, h {mb['h']})")
    print(f"       LEMMA: distinct h over all w60 = {len(hs)} (expect 1) | "
          f"distinct g1 over all w60 = {len(g1s)} (expect {MASK+1})")
    return ground and len(hs) == 1 and len(g1s) == MASK + 1


# ============================================================================ #
#  T1 — CV reachability over block-1 message freedom (rank, registers touched).  #
# ============================================================================ #
def t1_cv_reachability(M, setup, free):
    MASK = M['MASK']; N = M['N']; IVN = M['IVN']; KN = M['KN']
    M1base = setup['M1']
    CV1_0, _, _, _ = block1_cv(M, setup, free)

    def cv1_single(M1msg):
        st1, W1p = eng.precompute(M, M1msg)
        W = list(W1p) + list(free)
        W.append((M['s1'](W[59]) + W1p[54] + M['s0'](W1p[46]) + W1p[45]) & MASK)
        W.append((M['s1'](W[60]) + W1p[55] + M['s0'](W1p[47]) + W1p[46]) & MASK)
        W.append((M['s1'](W[61]) + W1p[56] + M['s0'](W1p[48]) + W1p[47]) & MASK)
        a, b, c, d, e, f, g, h = IVN
        for t in range(64):
            T1 = (h + M['S1'](e) + M['Ch'](e, f, g) + KN[t] + W[t]) & MASK
            T2 = (M['S0'](a) + M['Mj'](a, b, c)) & MASK
            h = g; g = f; f = e; e = (d + T1) & MASK
            d = c; c = b; b = a; a = (T1 + T2) & MASK
        fs = (a, b, c, d, e, f, g, h)
        return tuple((IVN[j] + fs[j]) & MASK for j in range(8))

    rows = []; touch = [0] * 8
    for word in range(16):
        for j in range(N):
            Mp = list(M1base); Mp[word] ^= (1 << j)
            CVp = cv1_single(Mp)
            dcv = 0
            for r in range(8):
                d = (CV1_0[r] ^ CVp[r]) & MASK
                if d:
                    touch[r] = 1
                dcv |= (d << (r * N))
            if dcv:
                rows.append(dcv)
    rank = gf2_rank_vals(rows, 8 * N)
    print(f"  [T1] CV reachability over block-1 msg: GF(2) rank = {rank}/{8*N} | "
          f"registers touched = {sum(touch)}/8")
    return dict(rank=rank, regs=sum(touch), n8=8 * N)


# ============================================================================ #
#  T2/T3 — CV's lever on h and the DECOUPLING from g1 / the collision.           #
#  Faithful frame: vary block-1's CV over a family; for each re-solve block-2's   #
#  message (da56=0); at a FIXED block-2 tail prefix, measure h (and de61).        #
#  THE DECISIVE QUANTITIES:                                                       #
#   - rank{h wrt CV}                    (is h steerable by CV at all?)            #
#   - rank{Dg1 wrt CV}                  (g1's target is CV-independent => 0)      #
#   - decoupling: is CV's control of h=0 INDEPENDENT of the collision-onset       #
#     (de61=0)?  measured as the joint count #(h=0 & de61=0) vs expected-if-indep. #
# ============================================================================ #
def build_cv_family(M, setup, size=200, seed=1, max_tries=8000):
    """Family of valid block-1 outputs (each: near-collision tail -> CV -> re-solved
    block-2 message giving da56=0).  Bounded random sampling (the candidate space is
    2^{4N}; a full strided comprehension is infeasible at N>=10)."""
    MASK = M['MASK']
    rng = random.Random(seed)
    fam = []; tries = 0
    while len(fam) < size and tries < max_tries:
        tries += 1
        bt = tuple(rng.randrange(MASK + 1) for _ in range(4))
        CV1, CV2, _, ffhw = block1_cv(M, setup, bt)
        B = block2_setup_from_cv(M, CV1, CV2)
        if B is not None:
            B['ffhw'] = ffhw
            fam.append(B)
    return fam


def t23_cv_lever(M, setup, fam, prefix=(5, 9, 17), w60=33):
    N = M['N']; MASK = M['MASK']; IVN = M['IVN']
    # (a) sched1 CV-independence (=> g1's absolute target cannot be moved by CV)
    base = block2_tail(M, IVN, IVN, setup['M1'], setup['M2'], prefix[0], prefix[1], prefix[2], w60)
    sched_moves = 0
    for r in range(8):
        for j in range(N):
            CV = list(IVN); CV[r] ^= (1 << j)
            res = block2_tail(M, tuple(CV), tuple(CV), setup['M1'], setup['M2'],
                              prefix[0], prefix[1], prefix[2], w60)
            if res['sched1'] != base['sched1']:
                sched_moves += 1
    # (b) h-steerability + h/de61 independence over the CV-family at the fixed tail
    recs = [tail_gh(M, B['st1'], B['st2'], B['W1p'], B['W2p'],
                    prefix[0], prefix[1], prefix[2], w60, full=True) for B in fam]
    hs = {r[1] for r in recs}
    rank_h = gf2_rank_vals([h ^ min(hs) for h in hs], N) if hs else 0
    nh0 = sum(1 for r in recs if r[1] == 0)
    nd0 = sum(1 for r in recs if r[2] == 0)
    nboth = sum(1 for r in recs if r[1] == 0 and r[2] == 0)
    exp_indep = nh0 * nd0 / len(fam) if fam else 0.0
    h_at_de0 = sorted({r[1] for r in recs if r[2] == 0})
    print(f"  [T2] sched1[60] (g1's target) moves under CV: {sched_moves}/{8*N}  "
          f"=> g1 is {'CV-INDEPENDENT' if sched_moves == 0 else 'CV-dependent'}")
    print(f"  [T2] CV->h steerability over family of {len(fam)} CV-setups @tail "
          f"{prefix+(w60,)}: distinct h = {len(hs)}, GF(2) rank{{h}} = {rank_h}/{N}")
    print(f"  [T3] DECOUPLING — is CV's h=0 control independent of the collision (de61=0)?")
    print(f"       #(h=0)={nh0}  #(de61=0)={nd0}  #(both)={nboth}  expected-if-indep="
          f"{exp_indep:.3f}")
    print(f"       at de61=0 onset, h takes {h_at_de0} (h=0 among them: {0 in h_at_de0})")
    decoupled = (nboth > 0 and 0 in h_at_de0)
    print(f"       >>> CV decouples h from the collision: {decoupled}  "
          f"(h=0 and de61=0 must CO-OCCUR via CV; observed {nboth}, expected {exp_indep:.2f})")
    return dict(sched_moves=sched_moves, rank_h=rank_h, distinct_h=len(hs),
                nh0=nh0, nd0=nd0, nboth=nboth, exp_indep=exp_indep,
                h_at_de0=h_at_de0, decoupled=decoupled)


# ============================================================================ #
#  T4 — (g1,h) COVERAGE over block-2 collisions: RESIDUAL kernel vs MSB kernel.   #
#  Direct test of whether the residual-kernel block-2 reaches (0,0) steerably or  #
#  shows the SAME 2^-2N joint structure as single-block.  Uses the lemma: per     #
#  prefix, h is fixed; sweep w60 for the collision; record (g1,h).                #
# ============================================================================ #
def t4_coverage(M, ST1, ST2, W1p, W2p, grid, label):
    MASK = M['MASK']; KN = M['KN']; s0 = M['s0']; s1f = M['s1']
    joint = []; n_pref = 0; n_h0 = 0; t0 = time.time()
    for w57 in range(grid):
        for w58 in range(grid):
            for w59 in range(grid):
                w57b = eng.find_w2(ST1, ST2, 57, w57, M)
                P1 = eng.sha_round(ST1, KN[57], w57, M); P2 = eng.sha_round(ST2, KN[57], w57b, M)
                w58b = eng.find_w2(P1, P2, 58, w58, M)
                Q1 = eng.sha_round(P1, KN[58], w58, M);  Q2 = eng.sha_round(P2, KN[58], w58b, M)
                w59b = eng.find_w2(Q1, Q2, 59, w59, M)
                R1 = eng.sha_round(Q1, KN[59], w59, M);  R2 = eng.sha_round(Q2, KN[59], w59b, M)
                co = eng.find_w2(R1, R2, 60, 0, M)
                sched1 = (s1f(w58)  + W1p[53] + s0(W1p[45]) + W1p[44]) & MASK
                sched2 = (s1f(w58b) + W2p[53] + s0(W2p[45]) + W2p[44]) & MASK
                h = (co - ((sched2 - sched1) & MASK)) & MASK
                n_pref += 1
                if h == 0:
                    n_h0 += 1
                W1_61 = (s1f(w59)  + W1p[54] + s0(W1p[46]) + W1p[45]) & MASK
                W2_61 = (s1f(w59b) + W2p[54] + s0(W2p[46]) + W2p[45]) & MASK
                for w60 in range(MASK + 1):
                    w60b = (w60 + co) & MASK
                    a = eng.sha_round(R1, KN[60], w60, M); b = eng.sha_round(R2, KN[60], w60b, M)
                    a = eng.sha_round(a, KN[61], W1_61, M); b = eng.sha_round(b, KN[61], W2_61, M)
                    if (a[4] - b[4]) & MASK != 0:
                        continue
                    W1_62 = (s1f(w60)  + W1p[55] + s0(W1p[47]) + W1p[46]) & MASK
                    W2_62 = (s1f(w60b) + W2p[55] + s0(W2p[47]) + W2p[46]) & MASK
                    a2 = eng.sha_round(a, KN[62], W1_62, M); b2 = eng.sha_round(b, KN[62], W2_62, M)
                    W1_63 = (s1f(W1_61) + W1p[56] + s0(W1p[48]) + W1p[47]) & MASK
                    W2_63 = (s1f(W2_61) + W2p[56] + s0(W2p[48]) + W2p[47]) & MASK
                    a2 = eng.sha_round(a2, KN[63], W1_63, M); b2 = eng.sha_round(b2, KN[63], W2_63, M)
                    if a2 == b2:
                        joint.append(((w60 - sched1) & MASK, h))
    h0g = sorted({g for g, hh in joint if hh == 0})
    sr61 = sum(1 for g, hh in joint if g == 0 and hh == 0)
    print(f"  [T4] {label} (grid {grid}^3, {n_pref} prefixes): block-2 colls={len(joint)} "
          f"[{time.time()-t0:.0f}s]")
    print(f"       P(h=0 per prefix) = {n_h0}/{n_pref} = {n_h0/n_pref:.2e} "
          f"(2^-N = {2.0**-M['N']:.2e}) | distinct (g1,h) = {len(set(joint))}")
    print(f"       h=0 at coll: g1 in {h0g} | sr=61 (0,0) = {sr61} | "
          f"steerable h=0 w/ g1 free: {len(h0g) > 1}")
    return dict(label=label, n_coll=len(joint), n_pref=n_pref, n_h0=n_h0,
                sr61=sr61, h0g=h0g, steerable=len(h0g) > 1)


def _find_near_collision_tail(M, setup, seed=0):
    """A block-1 NEAR-collision tail: cascade-eligible (da56=0 automatic) but NOT a full
    r63 collision, so the post-FF residual CV1^CV2 is nonzero (block-2's real input)."""
    MASK = M['MASK']
    rng = random.Random(seed)
    for _ in range(10000):
        t = tuple(rng.randrange(MASK + 1) for _ in range(4))
        _, _, _, hw = block1_cv(M, setup, t)
        if hw > 0:
            return t
    return (50, 77, 30, 11)  # fallback (known nonzero-residual tail at N=8)


def run(N, fam_size=200, cov_grid=40, do_coverage=True):
    print(f"\n{'='*76}\nMULTI-BLOCK CV PROBE   N={N}\n{'='*76}")
    t0 = time.time()
    M = eng.make_model(N); setup = eng.find_M0(M)
    if setup is None:
        print(f"  no cascade-eligible M0 at N={N}; skip"); return None
    MASK = M['MASK']
    print(f"  model: M0=0x{setup['M0']:x}  fill=0x{MASK:x}  (MSB kernel)  IVN[0]=0x{M['IVN'][0]:x}")

    free = None
    for tup in KNOWN_COLLISIONS.get(N, []):
        if eng.run_tail(M, setup, *tup)['collide']:
            free = tup; break
    if free is None and N <= 4:
        for w57 in range(MASK + 1):
            for w58 in range(MASK + 1):
                for w59 in range(MASK + 1):
                    for w60 in range(MASK + 1):
                        if eng.run_tail(M, setup, w57, w58, w59, w60)['collide']:
                            free = (w57, w58, w59, w60); break
                    if free: break
                if free: break
            if free: break
    if free is None:
        print("  no anchor collision; skip"); return None
    print(f"  anchor block-1 sr=60 collision (free tail): {free}")

    ground = t0_grounding(M, setup, free)
    assert ground, "grounding/lemma failed"
    # NOTE: the ANCHOR `free` is a FULL block-1 collision => post-FF residual = 0 (CV1==CV2):
    # that IS a real reduced-hash collision, the degenerate "block-2 trivial" case. For the
    # faithful 2-block test we need a block-1 NEAR-collision (cascade-eligible da56=0 but NOT
    # a full r63 collision) so CV1 != CV2 differ by a genuine residual (analog of repo HW>=66).
    CV1f, CV2f, residf, ff_hw_full = block1_cv(M, setup, free)
    print(f"  [block-1 DM] FULL-collision anchor => post-FF residual HW = {ff_hw_full}/{8*N}  "
          f"(0 == already a reduced-hash collision; NOT block-2's input)")
    near = _find_near_collision_tail(M, setup)
    CV1, CV2, residual, ff_hw = block1_cv(M, setup, near)
    print(f"  [block-1 DM] NEAR-collision tail {near} => post-FF residual HW = {ff_hw}/{8*N}  "
          f"(repo measured >=66 at N=32; THIS is block-2's input)")

    t1 = t1_cv_reachability(M, setup, free)

    print(f"  building CV-steering family (block-1 outputs re-solved for block-2 da56=0)...")
    fam = build_cv_family(M, setup, size=fam_size)
    print(f"       family size {len(fam)}  (post-FF HW range "
          f"{min(b['ffhw'] for b in fam)}-{max(b['ffhw'] for b in fam)})")
    t23 = t23_cv_lever(M, setup, fam)

    t4 = None
    if do_coverage:
        assert ff_hw > 0, "residual-kernel test needs a NEAR-collision (residual>0)"
        # MSB kernel (single-block) vs residual kernel (block-2), matched grids
        t4_msb = t4_coverage(M, setup['st1'], setup['st2'], setup['W1'], setup['W2'],
                             cov_grid, "MSB-kernel (single-block)")
        B = block2_setup_from_cv(M, CV1, CV2)
        t4_res = t4_coverage(M, B['st1'], B['st2'], B['W1p'], B['W2p'],
                             cov_grid, f"residual-kernel HW{ff_hw} (block-2)")
        t4 = dict(msb=t4_msb, res=t4_res)

    # decoupling requires EITHER the family-level h/collision independence to break
    # (T3) OR the residual-kernel coverage to reach steerable sr=61 with a NONZERO residual.
    decouples = t23['decoupled'] or (t4 and ff_hw > 0 and t4['res']['steerable']
                                     and t4['res']['sr61'] < t4['res']['n_coll'])
    print(f"\n  >>> SUMMARY N={N}  [{time.time()-t0:.0f}s]")
    print(f"      CV reachability {t1['rank']}/{t1['n8']} ({t1['regs']}/8 regs) | "
          f"CV->h rank {t23['rank_h']}/{N} | g1 CV-moves {t23['sched_moves']}/{8*N}")
    print(f"      h/collision independence: #(h=0&de61=0)={t23['nboth']} vs "
          f"expected {t23['exp_indep']:.2f} | CV-DECOUPLES h from collision: {decouples}")
    print(f"      VERDICT(N={N}): multi-block {'CAN reach 2^-N' if decouples else 'faces the SAME WALL (2^-2N)'}")
    return dict(N=N, t1=t1, t23=t23, t4=t4, ff_hw=ff_hw, decouples=decouples, free=free)


if __name__ == '__main__':
    results = {}
    # N=8 primary (full + coverage). N=10 cross-check (lever only; coverage too slow).
    results[8] = run(8, fam_size=200, cov_grid=40, do_coverage=True)
    results[10] = run(10, fam_size=120, cov_grid=24, do_coverage=False)

    print(f"\n{'='*76}\nCROSS-N SUMMARY\n{'='*76}")
    for N, r in results.items():
        if r:
            print(f"  N={N}: CV->h rank {r['t23']['rank_h']}/{N} | g1-CV-moves "
                  f"{r['t23']['sched_moves']} | #(h=0&de61=0)={r['t23']['nboth']}/"
                  f"exp{r['t23']['exp_indep']:.2f} | -> "
                  f"{'DECOUPLES (2^-N)' if r['decouples'] else 'SAME WALL (2^-2N)'}")
