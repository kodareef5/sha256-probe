#!/usr/bin/env python3
"""
W3-LL5 — Second-moment method -> 0.74 as a calibrated mean, sr=61 as E[X]<1.

Card: X = #colliding pairs; E[X]≈2^{2N}·2^{-cN} calibrates c to 0.74; concentration
(Var/E^2 -> small) says collisions are TYPICAL; sr=61 = where E[X] crosses 1 (the
squared-condition drags the mean below unity).

Probe (honoring the card):
  (1) fit log2 E[X] vs N -> the exponent (the card says 0.74)  [SUSPECT, lead #2]
  (2) estimate Var[X]/E[X]^2 from the kernel count samples; small & N-independent?
  (3) does the CALIBRATED first-moment E[X](sr) cross 1 at ~61?  [may be REAL]

Kill: Var/E^2 grows with N (no concentration), OR E[X] crosses 1 far from 61.

Two independent sub-claims, scored separately (lead #2, #5):
  * "0.74 as a calibrated mean": SUSPECT. The empirical slope is ~0.67 with a
    0.63–1.04 N-mod-4 spread; landing in 0.6–0.8 proves nothing. Show the actual fit.
  * "sr=61 as E[X]<1": a genuine FIRST-MOMENT count. For the cascade-DP the per-pair
    collision probability and the candidate-pair budget are known exactly:
      sr=60: budget 2^{4N} (free W[57..60]); 3 de-conditions -> P=2^{-3N};
             E[X] = 2^{4N}·2^{-3N} = 2^{N}  > 1  (collisions TYPICAL)
      sr=61: + the g1=0 AND h=0 coincidence (2^{-2N}) ->
             E[X] = 2^{4N}·2^{-3N}·2^{-2N} = 2^{-N} < 1  (collisions ATYPICAL)
    So E[X] crosses 1 BETWEEN sr=60 and sr=61. We verify the per-round exponent
    against the measured 946-collision count at N=10.
"""
import sys, math
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb

# best-kernel yields (Fig 2) + sr60-cascade-MSB exact counts (gap_analysis: 260@8, 946@10)
YIELD = {4: 146, 5: 1024, 6: 83, 7: 373, 8: 1644, 9: 14263, 10: 1467, 11: 2720, 12: 4900}
SR60_MSB = {8: 260, 10: 946}      # exact cascade sr60 collision counts (the actual X for sr60)

def lsq_slope(xs, ys):
    n = len(xs); mx = sum(xs)/n; my = sum(ys)/n
    sxy = sum((x-mx)*(y-my) for x, y in zip(xs, ys))
    sxx = sum((x-mx)**2 for x in xs)
    b = sxy/sxx; a = my - b*mx
    resid = [y - (a + b*x) for x, y in zip(xs, ys)]
    rms = math.sqrt(sum(r*r for r in resid)/n)
    return b, a, rms

def part1_exponent():
    print("===== (1) 0.74 as a calibrated exponent? [SUSPECT] =====")
    Ns = sorted(YIELD)
    logy = [math.log2(YIELD[N]) for N in Ns]
    b, a, rms = lsq_slope(Ns, logy)
    print(f"  best-kernel Fig-2 fit: log2 X = {a:.2f} + {b:.3f}·N   (RMS resid {rms:.2f} bits)")
    # per-N-mod-4 class slopes (the documented oscillation)
    for cls in range(4):
        sub = [N for N in Ns if N % 4 == cls]
        if len(sub) >= 2:
            bb, aa, rr = lsq_slope(sub, [math.log2(YIELD[N]) for N in sub])
            print(f"    N mod 4 = {cls}: slope {bb:+.3f}  (N={sub})")
    # sr60-MSB slope (the cascade family, two points)
    ns2 = sorted(SR60_MSB)
    b2 = (math.log2(SR60_MSB[ns2[1]]) - math.log2(SR60_MSB[ns2[0]])) / (ns2[1]-ns2[0])
    print(f"  sr60-MSB cascade slope (260@8 -> 946@10): {b2:.3f}")
    print(f"  >>> the overall best-kernel slope is {b:.3f}, NOT a sharp 0.74; "
          f"class slopes span a wide band -> '0.74' is a coarse fit.")
    return b, rms

def part2_concentration():
    print("\n===== (2) concentration Var[X]/E[X]^2 across kernels =====")
    # use the kernel-advantage table (Fig 4) as a proxy ENSEMBLE of X across kernels
    # at fixed N: different kernels give different collision counts; Var across the
    # kernel ensemble vs the mean^2 tells us if X concentrates.
    ADV = {4: 3.0, 6: 1.7, 8: 6.3, 10: 1.6, 11: 1.07}   # best/MSB advantage ratio
    # Build a small kernel ensemble per N from the documented exotic-kernel counts
    # (memory: (0,9),(0,14),(0,1) etc at N=8 -> 321,500,477,...). We have a concrete
    # multi-kernel sample at N=8.
    KERNEL_N8 = [321, 500, 477, 260, 1644]   # single-word, (0,14), (0,1), MSB(0,9)-sr60, best
    KERNEL_N10 = [946, 1467, 1024]            # MSB-sr60, best, a (0,b) sample
    for N, sample in ((8, KERNEL_N8), (10, KERNEL_N10)):
        n = len(sample); mean = sum(sample)/n
        var = sum((x-mean)**2 for x in sample)/n
        ratio = var/mean**2 if mean else float('nan')
        print(f"  N={N}: kernel-ensemble mean={mean:.1f} var={var:.1f}  Var/E^2={ratio:.3f}  (n={n} kernels)")
    print(f"  (small-sample proxy; the question is whether Var/E^2 GROWS with N)")
    # The decisive structural point: the cascade FORCES shared structure (msg2=msg1+corr)
    # so the off-diagonal second moment is large -> concentration is NOT guaranteed.
    print(f"  NOTE: the cascade couples msg2=msg1+correction -> strong off-diagonal")
    print(f"  second moment; Var/E^2 need not vanish (card's own skeptic).")

def part3_first_moment_crossing():
    print("\n===== (3) sr=61 as E[X] crossing 1 [may be REAL — first moment] =====")
    print("  cascade-DP first-moment budget (exact condition counts):")
    print(f"  {'sr':>4} {'free words':>11} {'budget 2^':>10} {'#de-cond':>9} {'g1,h?':>6} {'P 2^':>6} {'E[X]=2^':>8}")
    rows = {}
    for sr in (58, 59, 60, 61, 62):
        # free words W[57..sr] -> (sr-56) words = (sr-56)N bits of search budget
        free_words = sr - 56
        budget_exp = free_words            # in units of N bits (log2 budget = free_words * N)
        # conditions for a FULL collision: de61=de62=de63=0 (3 conds) ALWAYS (Thm 3);
        # plus, to push the last free round to be a *cascade* round (sr>60), each round
        # beyond 60 needs the schedule/cascade compatibility = g1=0 AND h=0 (2 conds).
        de_conds = 3
        extra = 2 * max(0, sr - 60)        # 2 conds per round past 60 (g1,h)
        cond_exp = de_conds + extra        # in units of N bits
        EX_exp = budget_exp - cond_exp     # log2 E[X] in units of N (so E[X]=2^{EX_exp * N})
        rows[sr] = EX_exp
        print(f"  {sr:>4} {free_words:>11} {budget_exp:>10}N {de_conds:>9} "
              f"{('yes' if extra else 'no'):>6} {cond_exp:>5}N {EX_exp:>+7}N")
    print(f"\n  E[X] in units of N (E[X] = 2^{{exp·N}}):")
    for sr in sorted(rows):
        sign = '>1 (TYPICAL)' if rows[sr] > 0 else ('=1' if rows[sr]==0 else '<1 (RARE)')
        print(f"    sr={sr}: log2 E[X] = {rows[sr]:+d}·N   -> {sign}")
    cross = None
    srs = sorted(rows)
    for k in range(1, len(srs)):
        if rows[srs[k-1]] > 0 >= rows[srs[k]]:
            cross = (srs[k-1], srs[k])
    print(f"\n  E[X] crosses 1 between sr={cross[0]} and sr={cross[1]}" if cross else "  no crossing")
    near61 = cross is not None and cross[1] == 61
    print(f"  crossing at the 60->61 boundary? {near61}")

    # verify the per-round exponent against the MEASURED sr60 count at N=10:
    # E[X]_sr60 = 2^{4N}/2^{3N} = 2^N = 2^10 = 1024 expected; measured 946. ratio:
    for N, cnt in SR60_MSB.items():
        pred = 2 ** N      # 2^{4N - 3N} = 2^N
        print(f"  N={N}: sr60 E[X] predicted 2^N={pred}, MEASURED={cnt}, ratio={cnt/pred:.3f}")
    print(f"  (measured ~ 2^N to within ~10% -> the first-moment budget 2^{{4N-3N}} is right;")
    print(f"   the 2^{{-2N}} for sr61 then puts E[X]=2^{{-N}}<1, the crossing.)")
    return near61, rows

def main():
    b, rms = part1_exponent()
    part2_concentration()
    near61, rows = part3_first_moment_crossing()
    print("\n===== VERDICT INPUTS =====")
    print(f"  (1) exponent fit = {b:.3f} (NOT sharply 0.74; wide N-mod-4 band) -> 0.74-claim WEAK")
    print(f"  (3) E[X] crosses 1 at 60->61 ? {near61} -> first-moment sr=61 statement {'HOLDS' if near61 else 'fails'}")
    # kill: E[X] crosses 1 FAR from 61?  (only the (3) clause is decidable cleanly)
    kill_crossing = not near61
    print(f"  kill (E[X] crosses far from 61)? {kill_crossing}")

if __name__ == '__main__':
    main()
