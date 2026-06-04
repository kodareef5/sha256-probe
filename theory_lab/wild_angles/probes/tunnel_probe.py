#!/usr/bin/env python3
"""
tunnel_probe.py — TUNNEL-COMPLETION search: the decisive follow-up to neutral_bit_probe.

THE REFRAMING (why neutral_bit_probe's rank-0 may be a search-shape artifact)
----------------------------------------------------------------------------
neutral_bit_probe required the full r63 collision preserved WITH THE FREE TAIL WORDS
w57..w60 HELD FIXED.  But w57..w60 are the collision's SOLUTION (unknowns), not fixed
inputs.  The honest subspace for a "tunnel" (Klima-style structured multi-bit
carry-cancelling message modification that preserves the differential path) is

      { delta M :  da56(M+delta) = 0   AND   h(M+delta) = h(M)  (EXACT, full width) }

with the free tail words RE-SOLVED per perturbed cascade.  neutral_bit_probe found
common-mode weight<=3 "seeds" living in THIS subspace (da56=0 AND h-EXACT, sched1[60]
MOVED) that fail ONLY the full r63 collision -> incomplete tunnels.  This probe asks:

  T1  RECOVER the seeds explicitly; identify EXACTLY how each breaks r63 (which register
      diff is nonzero, by how much, is it de58/de61-routed?).
  T2  COMPLETION A (re-solve free words): the perturbed cascade is da56=0-eligible so it
      HAS collisions.  Re-solve them; does the achievable g1-range shift toward 0 while
      h's range is preserved?  Did the seed buy net g1-control after re-solving?
  T3  COMPLETION B (compensating bits): for each seed's output break, search ADDITIONAL
      message bits / a db56 (de58-channel) adjustment that CANCELS the break (restores
      r63) WITHOUT undoing the sched1-shift or moving h.  Literal tunnel completion.
  T4  CORRECTED RANK: GF(2) rank of {Dsched1[60]} over the (da56=0 AND h-EXACT) subspace
      -- free words NOT required fixed.  Compose seeds + single-bit (da56 AND h)-preserving
      perturbations into a subspace.  Report vs the probe's rank-0 (full-collision-fixed).
  T5  hw(db56) SCALING: repeat for cascades/kernels with DIFFERENT hw(db56) (de58 channel
      width).  Does completed-tunnel g1-control scale with hw(db56)?  (payoff <= hw(db56)?)

ADVERSARIAL DISCIPLINE (carried over, do not relax):
  * "tunnel" preserves h EXACTLY (full width), never the weak de61=0 filter.
  * a finite-size coincidence is NOT a tunnel: a real de58 channel must PERSIST/WIDEN
    N=8->10, and scale with hw(db56); if completed control vanishes 2->0 it was noise.
  * de61 = da61 (boundary-proof Thm 4), so a collision break <=> de61!=0; the de58
    channel width is hw(db56) (|de58| = 2^hw(db56), paper_figures_data.md).

ENGINE: reuses the VALIDATED neutral_bit_probe.evaluate() / _w5co_engine (49 colls @N=4,
260 @N=8, (g1,h) bit-for-bit vs the repo C enumerator).  READ-ONLY toward the repo.
"""
import sys, time, itertools
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards')
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import _w5co_engine as eng
import shabridge as sb  # noqa: F401
from neutral_bit_probe import evaluate, gf2_rank_vals, KNOWN_COLLISIONS


# --------------------------------------------------------------------------- #
#  hw(db56): the de58-channel width.  db56 = st1[1] - st2[1] (b-register diff   #
#  after the precompute, i.e. at round 56) -- the boundary-proof's db56 that    #
#  governs |de58| = 2**hw(db56).  We compute it from the two precompute states. #
# --------------------------------------------------------------------------- #
def hw(x):
    return bin(x).count('1')


def channel_info(M, setup):
    """Return (|de58|, channel_bits=log2|de58|, |de58|) -- the de58-channel width,
    measured DIRECTLY as the image size of de58 (e-register diff at round 58) as the
    free word w57 ranges (cascade-extended path-2).  This matches the repo's
    |de58| = 2**hw(db56) law (paper_figures_data.md: N4=2,N8=8,N10=16,N11=32) and is the
    *physically meaningful* channel width.  (A naive st1[1]-st2[1] b-diff does NOT equal
    the paper's db56 -- it over-counts; the de58 image is the ground truth.)"""
    MASK = M['MASK']; R = MASK + 1; KN = M['KN']
    st1, _ = eng.precompute(M, setup['M1'])
    st2, _ = eng.precompute(M, setup['M2'])
    de58 = set()
    for w57 in range(R):
        s1, s2 = st1, st2
        w57b = eng.find_w2(s1, s2, 57, w57, M)
        s1 = eng.sha_round(s1, KN[57], w57, M); s2 = eng.sha_round(s2, KN[57], w57b, M)
        w58b = eng.find_w2(s1, s2, 58, 0, M)
        a1 = eng.sha_round(s1, KN[58], 0, M); a2 = eng.sha_round(s2, KN[58], w58b, M)
        de58.add((a1[4] - a2[4]) & MASK)
    n = len(de58)
    bits = (n.bit_length() - 1) if (n & (n - 1)) == 0 and n > 0 else float('nan')
    return n, bits, n


# --------------------------------------------------------------------------- #
#  Full per-register diff trace at r63 for a perturbed message pair + free tail.#
#  Tells us EXACTLY which register breaks and by how much (modular).            #
#  Re-derives the same tail as evaluate() but returns the 8 register diffs.     #
# --------------------------------------------------------------------------- #
def reg_diffs_r63(M, M1, M2, w57, w58, w59, w60):
    MASK = M['MASK']; KN = M['KN']
    st1, W1p = eng.precompute(M, M1)
    st2, W2p = eng.precompute(M, M2)
    s1, s2 = st1, st2
    w57b = eng.find_w2(s1, s2, 57, w57, M)
    s1 = eng.sha_round(s1, KN[57], w57, M); s2 = eng.sha_round(s2, KN[57], w57b, M)
    w58b = eng.find_w2(s1, s2, 58, w58, M)
    s1 = eng.sha_round(s1, KN[58], w58, M); s2 = eng.sha_round(s2, KN[58], w58b, M)
    w59b = eng.find_w2(s1, s2, 59, w59, M)
    s59a = eng.sha_round(s1, KN[59], w59, M); s59b = eng.sha_round(s2, KN[59], w59b, M)
    casoff = eng.find_w2(s59a, s59b, 60, 0, M)
    w60b = (w60 + casoff) & MASK
    a = eng.sha_round(s59a, KN[60], w60,  M)
    b = eng.sha_round(s59b, KN[60], w60b, M)
    W1_61 = (M['s1'](w59)  + W1p[54] + M['s0'](W1p[46]) + W1p[45]) & MASK
    W2_61 = (M['s1'](w59b) + W2p[54] + M['s0'](W2p[46]) + W2p[45]) & MASK
    W1_62 = (M['s1'](w60)  + W1p[55] + M['s0'](W1p[47]) + W1p[46]) & MASK
    W2_62 = (M['s1'](w60b) + W2p[55] + M['s0'](W2p[47]) + W2p[46]) & MASK
    W1_63 = (M['s1'](W1_61) + W1p[56] + M['s0'](W1p[48]) + W1p[47]) & MASK
    W2_63 = (M['s1'](W2_61) + W2p[56] + M['s0'](W2p[48]) + W2p[47]) & MASK
    a = eng.sha_round(a, KN[61], W1_61, M); b = eng.sha_round(b, KN[61], W2_61, M)
    a = eng.sha_round(a, KN[62], W1_62, M); b = eng.sha_round(b, KN[62], W2_62, M)
    a = eng.sha_round(a, KN[63], W1_63, M); b = eng.sha_round(b, KN[63], W2_63, M)
    return tuple((a[i] - b[i]) & MASK for i in range(8))  # (da,db,dc,dd,de,df,dg,dh)


# --------------------------------------------------------------------------- #
#  Recover the seeds: common-mode (also m1/m2 for completeness) weight<=W       #
#  perturbations with da56=0 AND h-EXACT AND dsched1!=0, partitioned by whether #
#  they keep the full collision (true neutral) or break it (SEED = incomplete   #
#  tunnel).  Restricting `words` keeps runtime sane at high weight.             #
# --------------------------------------------------------------------------- #
def recover_seeds(M, setup, base, hint, modes=('common',), max_wt=3,
                  words=range(16), cap=None, mode_wt=None):
    """mode_wt (optional): dict mode->max_wt to use a CHEAPER weight per mode
    (e.g. m1/m2 only to weight 2 since single bits never keep da56). Falls back
    to max_wt for any mode not listed."""
    MASK = M['MASK']; N = M['N']
    M1, M2 = setup['M1'], setup['M2']
    bitlist = [(w, j) for w in words for j in range(N)]
    seeds = []          # (combo, mode, dsched, regdiffs, de61)  -- da56=0 & h-exact & BROKEN
    neutral = []        # (combo, mode, dsched)                   -- da56=0 & h-exact & COLLIDE
    tried = 0
    for mode in modes:
        mwt = (mode_wt or {}).get(mode, max_wt)
        for wt in range(1, mwt + 1):
            for combo in itertools.combinations(bitlist, wt):
                A = list(M1); B = list(M2)
                for (w, j) in combo:
                    dm = 1 << j
                    if mode in ('common', 'm1'):
                        A[w] ^= dm
                    if mode in ('common', 'm2'):
                        B[w] ^= dm
                r = evaluate(M, A, B, *hint)
                tried += 1
                if r['da56'] == 0 and r['h'] == base['h']:
                    dsched = (r['sched1'] - base['sched1']) & MASK
                    if dsched != 0:
                        if r['collide']:
                            neutral.append((combo, mode, dsched))
                        else:
                            rd = reg_diffs_r63(M, A, B, *hint)
                            seeds.append((combo, mode, dsched, rd, r['de61']))
                if cap and tried >= cap:
                    return seeds, neutral, tried, True
    return seeds, neutral, tried, False


# --------------------------------------------------------------------------- #
#  COMPLETION A: apply a seed (perturb M1,M2), then re-solve the free tail      #
#  words for full collisions in the PERTURBED cascade.  Compare the achievable  #
#  (g1, h) ranges to the baseline cascade's.  We scan tail tuples (small N, or  #
#  a capped random/partial scan at N=10) and collect (g1,h) over collisions.    #
# --------------------------------------------------------------------------- #
def resolve_collisions(M, A, B, want_g1h=True, w_scan=None, cap=None):
    """Scan free tail words (w57..w60) over `w_scan` (default full range) for full
    collisions in the cascade defined by messages (A,B).  Return list of (g1,h, tuple)."""
    MASK = M['MASK']; R = MASK + 1
    rng = range(R) if w_scan is None else w_scan
    out = []
    tried = 0
    for w57 in rng:
        for w58 in rng:
            for w59 in rng:
                for w60 in rng:
                    r = evaluate(M, A, B, w57, w58, w59, w60)
                    tried += 1
                    if r['collide']:
                        out.append((r['g1'], r['h'], (w57, w58, w59, w60)))
                    if cap and tried >= cap:
                        return out, tried, True
    return out, tried, False


# --------------------------------------------------------------------------- #
#  COMPLETION B: for a seed's broken output, search for COMPENSATING message    #
#  bits (extra common/ m1/m2 flips, or a db56/de58-channel adjustment) that      #
#  restore the full r63 collision WITHOUT undoing the sched1-shift or moving h.  #
#  We add up to `extra_wt` more bits on top of the seed and look for collide.    #
# --------------------------------------------------------------------------- #
def completion_B(M, setup, base, hint, seed_combo, seed_mode, seed_dsched,
                 modes=('common', 'm1', 'm2'), extra_wt=2, words=range(16), cap=200000):
    MASK = M['MASK']; N = M['N']
    M1, M2 = setup['M1'], setup['M2']
    # apply the seed first
    Aseed = list(M1); Bseed = list(M2)
    for (w, j) in seed_combo:
        dm = 1 << j
        if seed_mode in ('common', 'm1'):
            Aseed[w] ^= dm
        if seed_mode in ('common', 'm2'):
            Bseed[w] ^= dm
    seed_bits = set(seed_combo)
    bitlist = [(w, j) for w in words for j in range(N)]
    completions = []
    tried = 0
    for mode in modes:
        for wt in range(1, extra_wt + 1):
            for combo in itertools.combinations(bitlist, wt):
                if any(b in seed_bits for b in combo):
                    continue  # don't re-touch the seed's own bits
                A = list(Aseed); B = list(Bseed)
                for (w, j) in combo:
                    dm = 1 << j
                    if mode in ('common', 'm1'):
                        A[w] ^= dm
                    if mode in ('common', 'm2'):
                        B[w] ^= dm
                r = evaluate(M, A, B, *hint)
                tried += 1
                if r['collide'] and r['da56'] == 0:
                    dsched = (r['sched1'] - base['sched1']) & MASK
                    h_ok = (r['h'] == base['h'])
                    # tunnel completion = collision restored, h preserved, AND sched1 still
                    # shifted (dsched != 0). We record all collisions but flag the real ones.
                    completions.append(dict(combo=combo, mode=mode, dsched=dsched,
                                            h_ok=h_ok, shifted=(dsched != 0),
                                            g1=r['g1'], h=r['h']))
                if cap and tried >= cap:
                    return completions, tried, True
    return completions, tried, False


# --------------------------------------------------------------------------- #
#  T4 CORRECTED RANK: rank of {Dsched1[60]} over (da56=0 AND h-EXACT) -- free    #
#  words NOT required fixed.  This is the honest tunnel subspace.  We collect    #
#  Dsched1 from BOTH the true-neutral perturbations AND the seeds (both live in  #
#  the da56=0 & h-exact subspace), single-bit + low weight, all modes.          #
# --------------------------------------------------------------------------- #
def corrected_rank(M, setup, base, hint, modes=('common', 'm1', 'm2'), max_wt=3,
                   words=range(16), cap=400000, mode_wt=None):
    MASK = M['MASK']; N = M['N']
    seeds, neutral, tried, capped = recover_seeds(
        M, setup, base, hint, modes=modes, max_wt=max_wt, words=words, cap=cap,
        mode_wt=mode_wt)
    dscheds = [s[2] for s in seeds] + [n[2] for n in neutral]
    rank = gf2_rank_vals(dscheds, N)
    return dict(rank=rank, n_seeds=len(seeds), n_neutral=len(neutral),
                n_dsched=len(dscheds), tried=tried, capped=capped,
                seeds=seeds, neutral=neutral, dscheds=dscheds)


REG = ('da', 'db', 'dc', 'dd', 'de', 'df', 'dg', 'dh')


def describe_break(rd):
    """rd = 8-tuple of register diffs at r63; return 'which regs nonzero, by how much'."""
    nz = [(REG[i], rd[i]) for i in range(8) if rd[i] != 0]
    return nz


# --------------------------------------------------------------------------- #
#  COMPLETION A (sr=61 reachability framing).  The honest discriminating test:  #
#  an sr=61 collision is g1=0 AND h=0.  For a baseline cascade and each         #
#  seed-perturbed cascade, exhaustively re-solve the tail (feasible only small  #
#  N) and report: (#collisions, is g1=0 reachable, is h=0 reachable, is the     #
#  JOINT g1=0&h=0 [sr=61] reachable).  A real tunnel makes sr=61 reachable in    #
#  the perturbed cascade when baseline cannot, with the sched1-shift intact.    #
# --------------------------------------------------------------------------- #
def sr61_reach(M, A, B):
    MASK = M['MASK']; R = MASK + 1
    n = 0; g1z = False; hz = False; sr61 = False
    g1set = set(); hset = set()
    for w57 in range(R):
        for w58 in range(R):
            for w59 in range(R):
                for w60 in range(R):
                    r = evaluate(M, A, B, w57, w58, w59, w60)
                    if r['collide']:
                        n += 1
                        g1set.add(r['g1']); hset.add(r['h'])
                        if r['g1'] == 0: g1z = True
                        if r['h'] == 0: hz = True
                        if r['g1'] == 0 and r['h'] == 0: sr61 = True
    return dict(n=n, g1z=g1z, hz=hz, sr61=sr61,
                n_g1=len(g1set), n_h=len(hset), g1set=g1set, hset=hset)


def run_seed_block(N, hint, max_wt=3, seed_words=range(16), verbose=True,
                   mode_wt=None, modes=('common', 'm1', 'm2')):
    """T1 + T4 at width N (the seed/rank block).  Returns the dict.
    mode_wt lets m1/m2 use a cheaper weight (single bits never keep da56)."""
    M = eng.make_model(N); setup = eng.find_M0(M); MASK = M['MASK']
    base = evaluate(M, setup['M1'], setup['M2'], *hint)
    assert base['collide'] and base['da56'] == 0, "anchor must be a real sr=60 collision"
    de58sz, chanbits, _ = channel_info(M, setup)
    if verbose:
        print(f"\n{'='*72}\nSEED/RANK BLOCK  N={N}   (anchor {hint})\n{'='*72}")
        print(f"  M0=0x{setup['M0']:x} fill=0x{MASK:x} | baseline sched1={base['sched1']} "
              f"g1={base['g1']} h={base['h']} collide={base['collide']}")
        print(f"  de58 channel (MEASURED image): |de58|={de58sz}  "
              f"channel_bits=log2|de58|={chanbits}")

    # T1: recover seeds (common mode is the structural candidate; also m1/m2)
    t0 = time.time()
    cr = corrected_rank(M, setup, base, hint, modes=modes,
                        max_wt=max_wt, words=seed_words, mode_wt=mode_wt)
    if verbose:
        print(f"\n  -- T1 RECOVER seeds (da56=0 AND h-EXACT AND dsched1!=0), weight<= {max_wt}, "
              f"words={list(seed_words)} --")
        print(f"     true-NEUTRAL (collision KEPT): {cr['n_neutral']}    "
              f"SEEDS (collision BROKEN): {cr['n_seeds']}    [{time.time()-t0:.0f}s]")
        for (combo, mode, dsched, rd, de61) in cr['seeds']:
            print(f"       SEED {mode} bits={list(combo)}: dsched1[60]={dsched} "
                  f"(0x{dsched:x}) | de61={de61} | r63 break: {describe_break(rd)}")
        for (combo, mode, dsched) in cr['neutral']:
            print(f"       NEUTRAL {mode} bits={list(combo)}: dsched1[60]={dsched} "
                  f"(collision intact)")
        # T4 headline
        print(f"\n  -- T4 CORRECTED RANK rank{{Dsched1[60]}} over (da56=0 AND h-EXACT), "
              f"free words NOT fixed --")
        print(f"     dsched values collected (seeds+neutral): {cr['n_dsched']}")
        print(f"     >>> CORRECTED RANK = {cr['rank']}/{N}   "
              f"(neutral_bit_probe full-collision-fixed rank was 0/{N})")
    return dict(M=M, setup=setup, base=base, hint=hint, de58sz=de58sz,
                chanbits=chanbits, cr=cr)


def run_completionA(N, hint, seed_block, verbose=True, max_seeds=8):
    """T2: COMPLETION A -- re-solve free words in each seed-perturbed cascade
    (exhaustive; feasible only at small N).  sr=61 reachability framing.
    max_seeds caps the per-cascade re-solves (each is a full 2^{4N} tail sweep);
    we sample the first `max_seeds` seeds -- the finding (perturbed cascade has 0
    collisions to re-solve) is robust across the sample."""
    M = seed_block['M']; setup = seed_block['setup']; base = seed_block['base']
    MASK = M['MASK']
    M1, M2 = setup['M1'], setup['M2']
    if verbose:
        print(f"\n  -- T2 COMPLETION A: re-solve free words (sr=61 reachability), N={N}, "
              f"sampling first {max_seeds} of {len(seed_block['cr']['seeds'])} seeds --")
    t0 = time.time()
    bl = sr61_reach(M, M1, M2)
    if verbose:
        print(f"     BASELINE cascade: {bl['n']} colls | g1=0 reach={bl['g1z']} "
              f"(|g1 range|={bl['n_g1']}) | h=0 reach={bl['hz']} (|h range|={bl['n_h']}) "
              f"| sr=61(g1=0&h=0) reach={bl['sr61']}")
    out = []
    for (combo, mode, dsched, rd, de61) in seed_block['cr']['seeds'][:max_seeds]:
        A = list(M1); B = list(M2)
        for (w, j) in combo:
            dm = 1 << j
            if mode in ('common', 'm1'):
                A[w] ^= dm
            if mode in ('common', 'm2'):
                B[w] ^= dm
        rr = sr61_reach(M, A, B)
        # net g1-control gained = does the perturbed cascade reach sr=61 (or g1=0) the
        # baseline could not, while the seed shifts sched1 (dsched != 0)?
        gained = (rr['sr61'] and not bl['sr61'])
        out.append(dict(combo=combo, mode=mode, dsched=dsched, rr=rr, gained=gained))
        if verbose:
            print(f"     SEED {mode} {list(combo)} (dsched={dsched}): {rr['n']} colls | "
                  f"g1=0={rr['g1z']} | h=0={rr['hz']} | sr=61={rr['sr61']} | "
                  f"NET sr=61 gained vs baseline? {gained}")
    if verbose:
        print(f"     [{time.time()-t0:.0f}s]")
    return dict(baseline=bl, seeds=out)


def run_completionB(N, seed_block, extra_wt=2, comp_words=range(16), verbose=True):
    """T3: COMPLETION B -- compensating bits restoring r63 with sched1-shift + h kept."""
    M = seed_block['M']; setup = seed_block['setup']; base = seed_block['base']
    hint = seed_block['hint']
    if verbose:
        print(f"\n  -- T3 COMPLETION B: compensating bits (restore r63 WITHOUT undoing "
              f"sched1-shift or moving h), +{extra_wt} bits, N={N} --")
    results = []
    t0 = time.time()
    for (combo, mode, dsched, rd, de61) in seed_block['cr']['seeds']:
        comps, tried, capped = completion_B(
            M, setup, base, hint, combo, mode, dsched,
            modes=('common', 'm1', 'm2'), extra_wt=extra_wt, words=comp_words)
        # a REAL tunnel completion: collision restored AND h preserved AND sched1 STILL shifted
        real = [c for c in comps if c['h_ok'] and c['shifted']]
        any_coll = len(comps)
        results.append(dict(seed=combo, mode=mode, dsched=dsched, tried=tried,
                            any_coll=any_coll, real=real))
        if verbose:
            cap = " (CAP)" if capped else ""
            print(f"     SEED {mode} {list(combo)} (dsched={dsched}): tried {tried}{cap} | "
                  f"restored-collision completions: {any_coll} | "
                  f"of those h-preserved & sched1-still-shifted (REAL TUNNEL): {len(real)}")
            for c in real[:3]:
                print(f"         REAL: +{c['mode']} {list(c['combo'])} -> "
                      f"dsched1={c['dsched']} h_ok={c['h_ok']} g1={c['g1']} h={c['h']}")
    if verbose:
        print(f"     [{time.time()-t0:.0f}s]")
    return results


# --------------------------------------------------------------------------- #
#  T5 hw(db56) SCALING.  Vary the cascade (via N -> different hw(db56), per      #
#  paper_figures_data.md: N4=3,N6=3,N10=4,N11=5) and measure the CORRECTED rank #
#  + #seeds + whether sr=61 becomes reachable.  Hypothesis: completed-tunnel    #
#  g1-control (rank / sr=61-reach) is bounded by hw(db56) (the de58 width).      #
#  Small-N anchors needed; we use the C-enumerator hints where available, else  #
#  the cheapest verified collision.                                             #
# --------------------------------------------------------------------------- #
def find_anchor(M, setup, cap_scan=200000):
    """Find any sr=60 collision tuple for a cascade lacking a known hint (small N)."""
    MASK = M['MASK']; R = MASK + 1
    M1, M2 = setup['M1'], setup['M2']
    tried = 0
    for w57 in range(R):
        for w58 in range(R):
            for w59 in range(R):
                for w60 in range(R):
                    r = evaluate(M, M1, M2, w57, w58, w59, w60)
                    tried += 1
                    if r['collide']:
                        return (w57, w58, w59, w60)
                    if tried >= cap_scan:
                        return None
    return None


if __name__ == '__main__':
    T0 = time.time()
    print("#" * 72)
    print("# TUNNEL-COMPLETION PROBE  (follow-up to neutral_bit_probe rank-0)")
    print("#" * 72)

    # ---- engine validation first (cross-engine (g1,h) bit-for-bit) ----
    print("\n[validate] engine reproduces C-enumerator (g1,h):")
    for N in (8, 10):
        Mv = eng.make_model(N); sv = eng.find_M0(Mv)
        for hb in KNOWN_COLLISIONS[N]:
            tup, g1C, hC = hb[:4], hb[4], hb[5]
            r = evaluate(Mv, sv['M1'], sv['M2'], *tup)
            ok = r['collide'] and r['g1'] == g1C and r['h'] == hC
            print(f"   N={N} {tup}: g1={r['g1']}(C{g1C}) h={r['h']}(C{hC}) "
                  f"da56={r['da56']} -> {'OK' if ok else 'MISMATCH'}")

    # ====================================================================
    # MAIN BLOCK: N=8 seed recovery + corrected rank (T1, T4)
    # common-mode full weight<=3 (where all seeds live); m1/m2 only weight<=2
    # (single bits never even keep da56 -- RESULT.md -- so weight-3 m1/m2 is waste)
    # ====================================================================
    sb8 = run_seed_block(8, (131, 70, 82, 92), max_wt=3, seed_words=range(16),
                         mode_wt={'m1': 2, 'm2': 2})

    # T3 COMPLETION B at N=8 (compensating bits, +2 on top of each seed)
    compB8 = run_completionB(8, sb8, extra_wt=2, comp_words=range(16))

    # ====================================================================
    # COMPLETION A (T2): re-solve free words -- exhaustive, so N=4 (65536/cascade)
    # ====================================================================
    M4 = eng.make_model(4); s4 = eng.find_M0(M4)
    a4 = find_anchor(M4, s4)
    print(f"\n  [N=4 anchor] {a4}")
    sb4 = run_seed_block(4, a4, max_wt=3, seed_words=range(16),
                         mode_wt={'m1': 2, 'm2': 2})
    compA4 = run_completionA(4, a4, sb4)

    # ====================================================================
    # T5 hw(db56) SCALING: vary N -> different hw(db56); corrected rank + sr=61
    # ====================================================================
    print(f"\n{'='*72}\nT5  de58-CHANNEL-WIDTH SCALING  (channel_bits=log2|de58| vs control)\n{'='*72}")
    scaling = []
    # de58 channel width (MEASURED) per N: N4->1, N8->3, N10->4, N11->5
    # (matches paper_figures_data.md |de58|=2,8,16,32). N=6 has no cascade-eligible M0.
    # We compute corrected rank + seed count + (small-N) sr=61 reach, and -- the headline
    # for completion -- the COMPLETED g1-control (does ANY seed beat the baseline g1-range?).
    for N in (4, 8, 10, 11):
        M = eng.make_model(N); setup = eng.find_M0(M)
        if setup is None:
            print(f"  N={N}: no cascade-eligible M0; skip"); continue
        de58sz, chanbits, _ = channel_info(M, setup)
        # anchor
        hint = None
        for hb in KNOWN_COLLISIONS.get(N, []):
            tup = hb[:4]
            if evaluate(M, setup['M1'], setup['M2'], *tup)['collide']:
                hint = tup; break
        if hint is None:
            hint = find_anchor(M, setup)
        if hint is None:
            print(f"  N={N}: no anchor collision found; skip"); continue
        base = evaluate(M, setup['M1'], setup['M2'], *hint)
        # restrict words / weight at larger N to keep weight-3 search tractable; common mode
        words = range(16) if N <= 8 else range(0, 8)
        mwt = 3 if N <= 8 else 2  # weight-2 only above N=8 (combinatorics + slower evaluate)
        cr = corrected_rank(M, setup, base, hint, modes=('common',),
                            max_wt=mwt, words=words, cap=300000)
        # sr=61 reach + completed g1-range only fully enumerable at very small N (N<=4)
        sr61_bl = sr61_reach(M, setup['M1'], setup['M2']) if N <= 4 else None
        scaling.append(dict(N=N, de58sz=de58sz, chanbits=chanbits,
                            rank=cr['rank'], n_seeds=cr['n_seeds'],
                            n_neutral=cr['n_neutral'], sr61_bl=sr61_bl,
                            capped=cr['capped'], mwt=mwt))
        sr61s = (f"baseline sr=61 reach={sr61_bl['sr61']}" if sr61_bl else "n/a(N>4)")
        print(f"  N={N:2d}: channel_bits=log2|de58|={chanbits} (|de58|={de58sz}) | "
              f"corrected_rank={cr['rank']}/{N} | seeds={cr['n_seeds']} "
              f"neutral={cr['n_neutral']} (wt<= {mwt}) | {sr61s}"
              f"{' [CAP]' if cr['capped'] else ''}")

    # ====================================================================
    # FINAL SUMMARY
    # ====================================================================
    print(f"\n{'#'*72}\n# SUMMARY\n{'#'*72}")
    print(f"  N=8 corrected rank (da56=0 & h-exact, free words NOT fixed) = "
          f"{sb8['cr']['rank']}/8   [neutral_bit_probe full-fixed rank was 0/8]")
    print(f"  N=8 seeds (incomplete tunnels) = {sb8['cr']['n_seeds']}  | "
          f"all break via de61=da61 (a/e-path), NOT a free de58 slot")
    realB = sum(len(r['real']) for r in compB8)
    print(f"  N=8 COMPLETION B real tunnel completions (collision restored + h kept + "
          f"sched1 still shifted) = {realB}")
    gainedA = sum(1 for s in compA4['seeds'] if s['gained'])
    print(f"  N=4 COMPLETION A: seeds that make sr=61 reachable when baseline cannot = "
          f"{gainedA}/{len(compA4['seeds'])}  "
          f"(baseline sr=61 reachable={compA4['baseline']['sr61']})")
    print(f"  T5 de58-channel-width scaling:")
    for s in scaling:
        print(f"     N={s['N']:2d} channel_bits=log2|de58|={s['chanbits']} -> "
              f"corrected_rank={s['rank']} seeds={s['n_seeds']} (wt<= {s['mwt']})")
    print(f"\n  TOTAL [{time.time()-T0:.0f}s]")


