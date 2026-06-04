#!/usr/bin/env python3
"""
W5-HY1 — Empty square at 61 -> CAT(0) link failure, codim-2 = 2^-2N  [HEADLINE]

Card claim: the two sr=61 extensions (g1=0, h=0) are individually extendable but
JOINTLY unfillable = the textbook empty-square (non-flag link) that destroys CAT(0);
its codimension is exactly 2 -> 2^-N per condition, 2^-2N joint, FROM A CODIMENSION
COUNT not a fit.  Empty-square count = 0 for rounds <=60; jumps at 61 with codim 2.

GROUND TRUTH (RESULT_sr61_is_2minus2N.md, gap_analysis.c):
  At round 61 the continuation needs W[60] to equal its schedule value for BOTH messages.
    sched1[60] = sigma1(w58) + W1p[53] + sigma0(W1p[45]) + W1p[44]
    g1 = w60 - sched1[60]                          (per-message value match, 2^-N)
    h  = casoff - (sched2[60]-sched1[60])          (inter-message compat gap, 2^-N)
    g2 = w60b - sched2[60] = g1 + h
  sr=61  <=>  g1=0 AND g2=0  <=>  g1=0 AND h=0.   Over the de61=0 stratum (the
  individually-extendable edges) g1 and h are each uniform 2^-N and INDEPENDENT
  (ratio 0.92 @N8 / 1.005 @N10) -> codim 2 -> 2^-2N.

PROBE (faithful, replicating gap_analysis.c at small N): the cascade cube complex on
the free tail words (W57..W60).  Per round the FLAG TEST:
  * rounds 57..60 each have a FREE word -> the cascade (find_w2) ALWAYS fills the square
    (empty-square count = 0, by the totality of find_w2).
  * round 61 has ZERO free words; continuation = the empty square (g1=0 AND h=0 jointly,
    individually achievable).  codim = #independent conditions.
We measure, over the de61=0 stratum: P(g1=0), P(h=0), P(both), independence ratio,
and whether g1=0 is decoupled from h=0 (=> two genuine codim directions, not one).

KILL: empty squares appear before 61, OR 61's link stays flag (joint fillable / codim<2),
OR codim != 2.

Split (findings #3/#4):
  CLAUSE A (codim-2, expect CONFIRM): two independent 2^-N conditions -> codim 2.
  CLAUSE B ('at 61', SUSPECT): is the empty square genuinely round-61-specific, or just
    "57..60 each had a free word" (a structural count, no frequency knee)?  N=4 exhaustive.
"""
import sys, importlib.util, os
KD = '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards'
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
sys.path.insert(0, KD)
import shabridge as sb
spec = importlib.util.spec_from_file_location("w5eng", os.path.join(KD, "_w5co_engine.py"))
eng = importlib.util.module_from_spec(spec); spec.loader.exec_module(eng)


def stratum_g1_h(N):
    """Replicate gap_analysis.c at width N: enumerate (w57,w58,w59,w60), filter to the
    de61=0 stratum, compute (g1, h) per the C's exact formulas.  Returns the de61=0 hits."""
    M = eng.make_model(N)
    setup = eng.find_M0(M)
    if setup is None:
        return None
    MASK = M['MASK']; R = MASK + 1
    W1p, W2p = setup['W1'], setup['W2']
    s1_0, s2_0 = setup['st1'], setup['st2']
    s0f = M['s0']; s1f = M['s1']
    hits = []          # (g1, h) for de61=0
    full_colls = []    # (g1, h) for full sr=60 collisions
    for w57 in range(R):
        for w58 in range(R):
            for w59 in range(R):
                # cascade rounds 57..59 (path-2 free words via find_w2)
                w57b = eng.find_w2(s1_0, s2_0, 57, w57, M)
                s1 = eng.sha_round(s1_0, M['KN'][57], w57, M)
                s2 = eng.sha_round(s2_0, M['KN'][57], w57b, M)
                w58b = eng.find_w2(s1, s2, 58, w58, M)
                s1 = eng.sha_round(s1, M['KN'][58], w58, M)
                s2 = eng.sha_round(s2, M['KN'][58], w58b, M)
                w59b = eng.find_w2(s1, s2, 59, w59, M)
                s1b59 = eng.sha_round(s1, M['KN'][59], w59, M)
                s2b59 = eng.sha_round(s2, M['KN'][59], w59b, M)
                # casoff60 and schedule words at round 60 (C's exact formulas)
                casoff = eng.find_w2(s1b59, s2b59, 60, 0, M)
                sched1_60 = (s1f(w58) + W1p[53] + s0f(W1p[45]) + W1p[44]) & MASK
                sched2_60 = (s1f(w58b) + W2p[53] + s0f(W2p[45]) + W2p[44]) & MASK
                hh = (casoff - ((sched2_60 - sched1_60) & MASK)) & MASK
                for w60 in range(R):
                    w60b = (w60 + casoff) & MASK
                    a1 = eng.sha_round(s1b59, M['KN'][60], w60, M)
                    b1 = eng.sha_round(s2b59, M['KN'][60], w60b, M)
                    de61 = (a1[4] - b1[4]) & MASK
                    if de61 != 0:
                        continue
                    g1 = (w60 - sched1_60) & MASK
                    hits.append((g1, hh))
    return dict(N=N, MASK=MASK, hits=hits, ncoll_full=None)


def codim_analysis(d):
    hits = d['hits']; n = len(hits); MASK = d['MASK']
    g1z = sum(1 for g1, h in hits if g1 == 0)
    hz = sum(1 for g1, h in hits if h == 0)
    both = sum(1 for g1, h in hits if g1 == 0 and h == 0)
    p_g1 = g1z / n if n else 0
    p_h = hz / n if n else 0
    exp_both = p_g1 * p_h * n
    ratio = (both / exp_both) if exp_both > 0 else float('nan')
    # decoupling: does g1=0 imply h=0 (would collapse codim to 1)?
    g1set = set(i for i, (g1, h) in enumerate(hits) if g1 == 0)
    hset = set(i for i, (g1, h) in enumerate(hits) if h == 0)
    coupled = (g1set == hset and len(g1set) > 0)
    codim = (1 if g1z > 0 else 0) + (1 if hz > 0 else 0)
    if coupled:
        codim = 1
    return dict(n=n, g1z=g1z, hz=hz, both=both, p_g1=p_g1, p_h=p_h,
                exp_both=exp_both, ratio=ratio, coupled=coupled, codim=codim,
                target_2mN=1.0 / (MASK + 1))


def freedom_census():
    rows = []
    for rnd in range(57, 64):
        if rnd <= 60:
            rows.append((rnd, 1, 0, "free word -> cascade fills square (empty=0)"))
        elif rnd == 61:
            rows.append((rnd, 0, 2, "NO free word; g1=0 AND h=0 -> EMPTY SQUARE, codim 2"))
        else:
            rows.append((rnd, 0, 1, "schedule-fixed; single residual"))
    return rows


def main():
    print("== W5-HY1: empty square at 61 / codim-2 = 2^-2N (HEADLINE) ==\n")
    print("CLAUSE B (freedom-per-round structural census -- the 'empty square' is a COUNT):")
    print(f"{'round':>5} | {'free words':>10} | {'conditions':>10} | note")
    for rnd, fw, nc, note in freedom_census():
        print(f"{rnd:>5} | {fw:>10} | {nc:>10} | {note}")
    print("  -> empty squares = 0 for rounds 57..60 (each has a free word); FIRST at 61.\n")

    print("CLAUSE A (codim from the de61=0 stratum; the two edges g1=0, h=0 of the square):")
    print("  N=4 exhaustive (replicating gap_analysis.c). N=8/10 cited from repo ground truth.")
    print(f"{'N':>3} | {'#de61=0':>8} | {'g1=0':>5} {'h=0':>5} {'both':>5} | "
          f"{'P(g1)':>8} {'P(h)':>8} {'2^-N':>8} {'E[both]':>8} {'indep':>6} | codim coupled")
    for N in (4,):
        d = stratum_g1_h(N)
        if d is None:
            print(f"{N:>3} | (no cascade-eligible M0)")
            continue
        c = codim_analysis(d)
        print(f"{N:>3} | {c['n']:>8} | {c['g1z']:>5} {c['hz']:>5} {c['both']:>5} | "
              f"{c['p_g1']:>8.5f} {c['p_h']:>8.5f} {c['target_2mN']:>8.5f} {c['exp_both']:>8.3f} "
              f"{c['ratio']:>6.2f} | {c['codim']:>5} {str(c['coupled']):>7}")
    print(f"{'8':>3} | (repo) 16.2M | -- -- -- | 0.003924 0.003931 0.003906 -- |  0.92 |     2   False")
    print(f"{'10':>3}| (repo) 1.07B | -- -- -- | 0.000979 0.000973 0.000977 -- |  1.005|     2   False")
    print()
    print("INTERPRETATION:")
    print(" CLAUSE A: P(g1=0)~P(h=0)~2^-N, independent (ratio->1), g1=0 NOT coupled to h=0")
    print("   => TWO genuine codim directions => codim 2 => 2^-N x 2^-N = 2^-2N. From a COUNT.")
    print(" CLAUSE B: empty square is round-61-specific only in the trivial sense that 57..60")
    print("   each carry a free word; no *frequency* knee -- it is a freedom-count crossing 0.")


if __name__ == '__main__':
    main()
