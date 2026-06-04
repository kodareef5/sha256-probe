#!/usr/bin/env python3
"""
neutral_bit_probe.py  —  decisive make-or-break test of the sr=60->61 DECOUPLE idea.

THE IDEA (lead follow-up, not a catalog card):
  sr=60 -> sr=61 costs 2^-2N = TWO independent N-bit conditions:
      g1 = 0   (a per-MESSAGE absolute value match: w60 == sched1[60])
      h  = 0   (an inter-MESSAGE differential compatibility gap)
  with g2 = g1 + h exactly.  OC2 already showed the last free TAIL word w60 moves g1
  but is structurally incapable of moving h ("two conditions, one control").

  This probe tests a DIFFERENT lever:  MESSAGE-bit perturbations ("neutral bits") that
  move g1's ABSOLUTE target

      sched1[60] = sigma1(w58) + W1p[53] + sigma0(W1p[45]) + W1p[44]

  via the PRECOMPUTE words W1p[44],W1p[45],W1p[53]  (functions of M[0..15]) WITHOUT
  disturbing the differential — i.e. keeping da56=0 (cascade-eligible), keeping the
  full 8-register collision at r63, and keeping h EXACTLY unchanged.
  If a rank-r subspace of such perturbations exists, g1 gains r free bits -> sr=61
  drops from 2^-2N to 2^-(2N-r).  rank==N => full decouple (2^-N); rank==0 => BLOCKED.

STRUCTURAL HYPOTHESIS to test (do NOT assume): sched1[60] is ABSOLUTE (message-1),
the cascade+h are DIFFERENTIAL (message-difference).  A COMMON-MODE delta added to BOTH
M1 and M2 leaves the difference unchanged to first order, so it "should" move sched1[60]
while preserving h.  BUT the carry/Ch/Maj nonlinearity in precompute couples
absolute<->differential, so common-mode delta will generally perturb the differential too.
Neutral bits = the perturbations where that coupling happens to vanish.  EMPIRICAL.

ENGINE: reuses the VALIDATED N-bit cascade engine _w5co_engine (49 colls @N=4, 260 @N=8,
cross-checked vs gap_analysis.c @N=8 -> 260, M0=0x67).  READ-ONLY toward the repo.

ADVERSARIAL DISCIPLINE:
  * h is checked EXACTLY (full-width equality), not "de61=0".  A perturbation that moves
    sched1[60] but shifts h even by 1 is NOT neutral.
  * we additionally require the full collision to survive (all 8 registers equal @r63),
    the STRONGEST filter — this dominates the weak de61=0 filter.
  * the "headline rank" is the GF(2) rank of {Delta sched1[60]} over the perturbation
    subspace that preserves (da56=0 AND h-exact AND full-collision).  We compute it two
    ways: (i) exact enumeration of a low-weight perturbation ball, (ii) a linear-image
    span over the single-bit responses restricted to the differential-preserving kernel.
"""
import sys, time, itertools
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards')
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import _w5co_engine as eng
import shabridge as sb  # noqa: F401  (ground-truth pins; primitives re-exported)


# ----------------------------------------------------------------------------- #
#  GF(2) rank over integers-as-bitmasks (each value is an N-bit column vector).  #
# ----------------------------------------------------------------------------- #
def gf2_rank_vals(vals, N):
    """rank over GF(2) of a set of N-bit vectors (given as ints). bit j = coord j."""
    basis = []
    for v in vals:
        v &= (1 << N) - 1
        for b in basis:
            v = min(v, v ^ b)
        if v:
            basis.append(v)
            basis.sort(reverse=True)
    return len(basis)


# ----------------------------------------------------------------------------- #
#  Recompute sched1[60], h, da56, and the FULL collision after perturbing M.     #
#  We perturb the message words (M1 and/or M2) by delta-masks, rebuild precompute #
#  (states + schedule words), then replay the SAME free tail words (w57..w60).    #
# ----------------------------------------------------------------------------- #
def evaluate(M, M1, M2, w57, w58, w59, w60):
    """Given (possibly perturbed) messages M1,M2 and fixed free tail words, return:
        da56   : st1[0]-st2[0]  (==0  <=> cascade-eligible)
        sched1 : sched1[60]  (g1's ABSOLUTE target, message-1)
        h      : differential compatibility gap (EXACT, full width)
        g1     : w60 - sched1[60]
        collide: full 8-register collision at r63 (strongest filter)
        de61   : weak filter, for contrast only
    Mirrors _w5co_engine.run_tail exactly; precompute via eng.precompute."""
    MASK = M['MASK']; KN = M['KN']; s0 = M['s0']; s1f = M['s1']
    st1, W1p = eng.precompute(M, M1)
    st2, W2p = eng.precompute(M, M2)
    da56 = (st1[0] - st2[0]) & MASK

    s1, s2 = st1, st2
    # rounds 57,58 cascade
    w57b = eng.find_w2(s1, s2, 57, w57, M)
    s1 = eng.sha_round(s1, KN[57], w57, M); s2 = eng.sha_round(s2, KN[57], w57b, M)
    w58b = eng.find_w2(s1, s2, 58, w58, M)
    s1 = eng.sha_round(s1, KN[58], w58, M); s2 = eng.sha_round(s2, KN[58], w58b, M)
    # round 59 cascade -> w59b (needed for path-2 schedule W[61])
    w59b = eng.find_w2(s1, s2, 59, w59, M)
    s59a = eng.sha_round(s1, KN[59], w59, M); s59b = eng.sha_round(s2, KN[59], w59b, M)
    # round 60 cascade offset
    casoff = eng.find_w2(s59a, s59b, 60, 0, M)
    w60b = (w60 + casoff) & MASK

    # sched1[60], sched2[60], h  (boundary-proof / gap_analysis.c formulae)
    sched1 = (s1f(w58)  + W1p[53] + s0(W1p[45]) + W1p[44]) & MASK
    sched2 = (s1f(w58b) + W2p[53] + s0(W2p[45]) + W2p[44]) & MASK
    h  = (casoff - ((sched2 - sched1) & MASK)) & MASK
    g1 = (w60 - sched1) & MASK

    # full tail r60..r63 for the collision check
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
    return dict(da56=da56, sched1=sched1, h=h, g1=g1, collide=collide, de61=de61)


# ----------------------------------------------------------------------------- #
#  Find a valid sr=60 collision (a free 4-tuple w57..w60) for the BASE messages.  #
#  We need at least one full collision to anchor the probe.                        #
# ----------------------------------------------------------------------------- #
def find_one_collision(M, setup, max_scan=None, hint=None):
    """Find a full sr=60 collision (free 4-tuple). If `hint` is given (a known tuple
    from the C enumerator gap_analysis.c), verify it and return immediately — collisions
    are 2^-? sparse so a blind scan is infeasible at N>=8. Otherwise scan (small N only)."""
    MASK = M['MASK']; R = MASK + 1
    M1, M2 = setup['M1'], setup['M2']
    if hint is not None:
        r = evaluate(M, M1, M2, *hint)
        if r['collide']:
            return tuple(hint), r, 0
        # hint failed — fall through to scan (shouldn't happen if engines agree)
        print(f"   [warn] hint {hint} is NOT a collision in this engine; scanning...")
    scanned = 0
    for w57 in range(R):
        for w58 in range(R):
            for w59 in range(R):
                for w60 in range(R):
                    r = evaluate(M, M1, M2, w57, w58, w59, w60)
                    scanned += 1
                    if r['collide']:
                        return (w57, w58, w59, w60), r, scanned
                    if max_scan and scanned >= max_scan:
                        return None, None, scanned
    return None, None, scanned


# ----------------------------------------------------------------------------- #
#  Perturbation generators. delta1 = mask XORed into M1 words; delta2 into M2.    #
#  We represent a perturbation as (which_word, delta_mask, mode) where mode in    #
#  {'common','m1','m2'}: common -> both messages get the same delta (preserves    #
#  the difference to first order); m1/m2 -> only one side.                         #
# ----------------------------------------------------------------------------- #
def apply_pert(M1, M2, word, dmask, mode):
    A = list(M1); B = list(M2)
    if mode in ('common', 'm1'):
        A[word] ^= dmask
    if mode in ('common', 'm2'):
        B[word] ^= dmask
    return A, B


def probe_single_bit(M, setup, free, base, mode, words):
    """For each single-bit message perturbation in `mode` over `words`, record:
        (Dsched1, h_changed?, da56_broken?, collide_kept?)
    Returns list of records and the collected Dsched1 over the differential-PRESERVING
    single-bit perturbations (those keeping da56=0, h exact, AND collision)."""
    MASK = M['MASK']; N = M['N']
    M1, M2 = setup['M1'], setup['M2']
    w57, w58, w59, w60 = free
    recs = []
    neutral_dsched = []      # Dsched1 for perturbations preserving da56,h,collision
    moved_sched_any = []     # any Dsched1 != 0 (regardless of differential)
    for word in words:
        for j in range(N):
            dmask = 1 << j
            A, B = apply_pert(M1, M2, word, dmask, mode)
            r = evaluate(M, A, B, w57, w58, w59, w60)
            dsched = (r['sched1'] - base['sched1']) & MASK
            da_ok = (r['da56'] == 0)
            h_ok = (r['h'] == base['h'])
            coll_ok = r['collide']
            recs.append(dict(word=word, bit=j, mode=mode, dsched=dsched,
                             da_ok=da_ok, h_ok=h_ok, coll_ok=coll_ok,
                             de61_ok=(r['de61'] == 0)))
            if dsched != 0:
                moved_sched_any.append(dsched)
            if da_ok and h_ok and coll_ok and dsched != 0:
                neutral_dsched.append(dsched)
    return recs, neutral_dsched, moved_sched_any


def probe_lowweight_ball(M, setup, free, base, mode, words, max_weight=2, cap=200000):
    """Exact enumeration of a low-weight perturbation ball (Hamming weight<=max_weight
    over the chosen words' bits). Collect Dsched1 over the EXACTLY-neutral subset
    (da56=0, h exact, full collision). This catches neutral DIRECTIONS that are not
    single-bit (e.g. a 2-bit combo that cancels the differential coupling)."""
    MASK = M['MASK']; N = M['N']
    M1, M2 = setup['M1'], setup['M2']
    w57, w58, w59, w60 = free
    bitlist = [(word, j) for word in words for j in range(N)]
    neutral = []      # Dsched1 over neutral perturbations
    tried = 0
    n_da = n_h = n_coll = n_neutral = 0
    for wt in range(1, max_weight + 1):
        for combo in itertools.combinations(bitlist, wt):
            A = list(M1); B = list(M2)
            for (word, j) in combo:
                dmask = 1 << j
                if mode in ('common', 'm1'):
                    A[word] ^= dmask
                if mode in ('common', 'm2'):
                    B[word] ^= dmask
            r = evaluate(M, A, B, w57, w58, w59, w60)
            tried += 1
            if r['da56'] == 0:
                n_da += 1
                if r['h'] == base['h']:
                    n_h += 1
                    if r['collide']:
                        n_coll += 1
                        dsched = (r['sched1'] - base['sched1']) & MASK
                        if dsched != 0:
                            n_neutral += 1
                            neutral.append(dsched)
            if tried >= cap:
                return neutral, dict(tried=tried, n_da=n_da, n_h=n_h,
                                     n_coll=n_coll, n_neutral=n_neutral, capped=True)
    return neutral, dict(tried=tried, n_da=n_da, n_h=n_h,
                         n_coll=n_coll, n_neutral=n_neutral, capped=False)


# Known sr=60 collisions from the C enumerator gap_analysis.c (M0 auto-discovered;
# fill=MASK). Format: N -> [(w57,w58,w59,w60, g1_C, h_C), ...]. We VALIDATE that the
# Python engine reproduces g1_C,h_C exactly before probing (cross-engine ground truth).
KNOWN_COLLISIONS = {
    8:  [(131, 70, 82, 92, 28, 249), (131, 140, 71, 87, 207, 89)],
    10: [(309, 594, 54, 698, 277, 609), (310, 477, 913, 139, 981, 452)],
}


def joint_coupling_analysis(N, hint, max_wt=3, cap=60000):
    """ADVERSARIAL deep-dive: the headline rank can be 0 simply because da56=0 (cascade
    eligibility) is so restrictive that few perturbations survive it. The decisive
    question is: AMONG the perturbations that DO preserve da56=0, is sched1[60]-movement
    ever DECOUPLED from h-movement?  If every da56=0 perturbation that moves sched1 also
    moves h, the absolute<->differential coupling is total -> decouple genuinely BLOCKED.
    We enumerate weight<=max_wt perturbations (all 3 modes), keep da56=0 survivors, and
    report the joint (Dsched1, Dh) structure + the rank of {Dsched1 : da56=0 AND Dh=0}."""
    M = eng.make_model(N); setup = eng.find_M0(M); MASK = M['MASK']
    base = evaluate(M, setup['M1'], setup['M2'], *hint)
    M1, M2 = setup['M1'], setup['M2']
    print(f"\n  --- ADVERSARIAL coupling deep-dive (N={N}, weight<= {max_wt}): is sched1 "
          f"movement EVER decoupled from h among da56=0 survivors? ---")
    bitlist = [(w, j) for w in range(16) for j in range(N)]
    overall_decouple_rank = 0
    for mode in ('common', 'm1', 'm2'):
        t0 = time.time(); tried = 0; capped = False
        surv = []   # (dsched, dh, collide)
        done = False
        for wt in range(1, max_wt + 1):
            if done:
                break
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
                if r['da56'] == 0:
                    dsched = (r['sched1'] - base['sched1']) & MASK
                    dh = (r['h'] - base['h']) & MASK
                    surv.append((dsched, dh, r['collide']))
                if tried >= cap:
                    capped = True; done = True; break
        move_s = [s for s in surv if s[0] != 0]
        decouple = [s for s in move_s if s[1] == 0]              # sched1 moves, h FIXED
        decouple_coll = [s for s in decouple if s[2]]           # ...AND full collision kept
        rk_weak = gf2_rank_vals([s[0] for s in decouple], N)        # da56=0 & dh=0 (no coll)
        rk_strict = gf2_rank_vals([s[0] for s in decouple_coll], N) # + FULL collision (NEUTRAL)
        overall_decouple_rank = max(overall_decouple_rank, rk_strict)
        both = sum(1 for s in move_s if s[1] != 0)
        capmark = " (CAP)" if capped else ""
        print(f"   mode={mode:6s}: tried {tried}{capmark} | da56=0 survivors {len(surv)} | "
              f"move sched1 {len(move_s)} | sched1-moves-h-FIXED {len(decouple)} (rank {rk_weak}) | "
              f"+FULL-collision {len(decouple_coll)} -> STRICT neutral rank={rk_strict}/{N}  "
              f"[{time.time()-t0:.1f}s]")
        if move_s:
            print(f"            coupling: {both}/{len(move_s)} da56=0 perts that move sched1 "
                  f"ALSO move h ({100*both/len(move_s):.0f}%); the few h-FIXED ones BREAK the "
                  f"collision (strict-neutral count {len(decouple_coll)})")
    print(f"   >>> deep-dive STRICT neutral rank (N={N}) = {overall_decouple_rank}/{N}  "
          f"(neutral = da56=0 & h-exact & FULL collision; 0 => decouple BLOCKED)")
    return overall_decouple_rank


def run(N, max_weight=2, verbose=True):
    print(f"\n{'='*70}\nNEUTRAL-BIT PROBE  N={N}\n{'='*70}")
    t0 = time.time()
    M = eng.make_model(N)
    setup = eng.find_M0(M)
    if setup is None:
        print(f"  no cascade-eligible M0 at N={N}; skip"); return None
    MASK = M['MASK']
    print(f"  model: M0=0x{setup['M0']:x}  fill=0x{MASK:x}  (MSB kernel)")

    # 1) anchor on a real sr=60 collision (hint from the C enumerator) and CROSS-VALIDATE
    #    that the Python engine reproduces the C-derived g1,h exactly.
    hints = KNOWN_COLLISIONS.get(N)
    free = base = None
    if hints:
        for hb in hints:
            tup, g1_C, h_C = hb[:4], hb[4], hb[5]
            cand = evaluate(M, setup['M1'], setup['M2'], *tup)
            ok = cand['collide'] and cand['g1'] == g1_C and cand['h'] == h_C
            print(f"   [xcheck] C tuple {tup}: collide={cand['collide']} "
                  f"g1(py)={cand['g1']} vs g1(C)={g1_C}  h(py)={cand['h']} vs h(C)={h_C}  "
                  f"-> {'MATCH' if ok else 'MISMATCH'}")
            if ok and free is None:
                free, base = tup, cand
        if free is None:
            print("   [warn] no hint matched the C enumerator; falling back to scan")
    if free is None:
        free, base, scanned = find_one_collision(M, setup)
        if free is None:
            print(f"  no full collision found; skip"); return None
    w57, w58, w59, w60 = free
    print(f"  anchor collision: (w57,w58,w59,w60)=({w57},{w58},{w59},{w60})")
    print(f"  baseline: sched1[60]={base['sched1']}  g1={base['g1']}  h={base['h']}  "
          f"collide={base['collide']}  de61={base['de61']}")
    assert base['collide'] and base['da56'] == 0, "anchor must be a real sr=60 collision"

    # the message words that actually feed sched1[60]'s precompute part:
    # W1p[44],W1p[45],W1p[53] depend on M[0..15]; word 0 carries the kernel difference.
    # We probe ALL 16 message words to be thorough (cheap), in three modes.
    words_all = list(range(16))

    print(f"\n  --- single-bit message perturbations (does sched1[60] move? is the "
          f"differential preserved?) ---")
    summary = {}
    for mode in ('common', 'm1', 'm2'):
        recs, neutral_dsched, moved_any = probe_single_bit(
            M, setup, free, base, mode, words_all)
        n_total = len(recs)
        n_moved = sum(1 for r in recs if r['dsched'] != 0)
        n_da_ok = sum(1 for r in recs if r['da_ok'])
        n_h_ok = sum(1 for r in recs if r['h_ok'])
        n_coll_ok = sum(1 for r in recs if r['coll_ok'])
        # perturbations that move sched1 AND keep da56=0 (necessary for neutral)
        n_move_da = sum(1 for r in recs if r['dsched'] != 0 and r['da_ok'])
        rank_moved = gf2_rank_vals(moved_any, N)            # raw reach of sched1 (no constraint)
        rank_neutral = gf2_rank_vals(neutral_dsched, N)     # constrained: da56,h,collision
        summary[mode] = dict(rank_neutral=rank_neutral, rank_moved=rank_moved,
                             n_neutral=len(neutral_dsched))
        print(f"   mode={mode:6s}: {n_total} single-bit perts | "
              f"move sched1: {n_moved} | da56=0 kept: {n_da_ok} | "
              f"h-exact kept: {n_h_ok} | collision kept: {n_coll_ok}")
        print(f"            move-sched1 AND da56=0: {n_move_da} | "
              f"NEUTRAL (move sched1 & da56=0 & h-exact & collide): {len(neutral_dsched)}")
        print(f"            rank{{Dsched1}} unconstrained = {rank_moved}/{N}  ||  "
              f"rank{{Dsched1}} over NEUTRAL subspace = {rank_neutral}/{N}")

    # 2) low-weight ball (catches multi-bit neutral directions single bits miss)
    print(f"\n  --- low-weight perturbation ball (weight<= {max_weight}), "
          f"exact neutrality (da56=0 & h-exact & full collision) ---")
    ball_summary = {}
    for mode in ('common', 'm1', 'm2'):
        neutral, stats = probe_lowweight_ball(
            M, setup, free, base, mode, words_all, max_weight=max_weight)
        rank = gf2_rank_vals(neutral, N)
        ball_summary[mode] = dict(rank=rank, **stats)
        cap = " (CAPPED)" if stats['capped'] else ""
        print(f"   mode={mode:6s}: tried {stats['tried']}{cap} | da56=0:{stats['n_da']} | "
              f"+h-exact:{stats['n_h']} | +full-collision:{stats['n_coll']} | "
              f"neutral&move:{stats['n_neutral']} | rank{{Dsched1|neutral}} = {rank}/{N}")

    # 3) HEADLINE rank = best neutral rank across modes & probes
    best_rank = max([s['rank_neutral'] for s in summary.values()] +
                    [b['rank'] for b in ball_summary.values()])
    best_unconstrained = max(s['rank_moved'] for s in summary.values())
    print(f"\n  >>> HEADLINE (N={N}): rank of FREE g1-control via neutral message bits = "
          f"{best_rank}/{N}")
    print(f"      (for contrast: rank of sched1[60] reachability with NO differential "
          f"constraint = {best_unconstrained}/{N})")
    if best_rank >= N:
        verdict = f"FULL DECOUPLE: g1 fully free -> sr=61 -> 2^-N"
    elif best_rank > 0:
        verdict = f"PARTIAL: sr=61 -> 2^-(2N-{best_rank}) = 2^-{2*N-best_rank}"
    else:
        verdict = f"BLOCKED: no neutral freedom -> sr=61 stays 2^-2N"
    print(f"      VERDICT: {verdict}   [{time.time()-t0:.1f}s]")
    return dict(N=N, best_rank=best_rank, best_unconstrained=best_unconstrained,
                verdict=verdict, single=summary, ball=ball_summary, free=free,
                base_h=base['h'], base_sched1=base['sched1'])


if __name__ == '__main__':
    results = {}
    # N=8: anchor from C-enumerator collision; single-bit (3 modes) + ball weight<=2.
    # N=10 as an independence cross-check.
    for N in (8, 10):
        results[N] = run(N, max_weight=2)

    # ADVERSARIAL coupling deep-dive (weight<=3) — is sched1-movement EVER decoupled
    # from h among da56=0 survivors? (rules out "rank 0 is just because da56=0 is rare")
    anchors = {8: (131, 70, 82, 92), 10: (309, 594, 54, 698)}
    deep = {}
    for N in (8, 10):
        if results[N]:
            deep[N] = joint_coupling_analysis(N, anchors[N], max_wt=3)

    print(f"\n{'='*70}\nCROSS-N SUMMARY\n{'='*70}")
    for N, r in results.items():
        if r:
            dd = deep.get(N, 'n/a')
            print(f"  N={N}: HEADLINE rank = {r['best_rank']}/{N}  "
                  f"(unconstrained {r['best_unconstrained']}/{N})  "
                  f"deep-dive decouple rank = {dd}/{N}  ->  {r['verdict']}")
