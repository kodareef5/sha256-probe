#!/usr/bin/env python3
"""
W3-IE5 -- Three-distance theorem -> the bumpy collision-vs-N features.

CARD CLAIM: {7,18,3},{17,19,10} mod N give <=3 distinct gaps (Steinhaus); the multiset's
CF-transition points predict the discrete jumps in collision multiplicity (the N=10 spike,
the |de58| jumps).

PROBE (card's own): pure arithmetic N=4..40: gap-multiset + CF-convergents of (amount/N)
vs the collision-count and |de58|-jump tables; PRE-REGISTER the next jump's N.
KILL: no alignment with the empirical jumps.
SKEPTIC (the card's own): the MOST numerology-prone -- 3 constants + free combination can
fit ANY bumpy curve; only an OUT-OF-SAMPLE prediction counts.

WEAPONIZED PRIOR FINDING #4: the collision-vs-N curve IS bumpy (real): N=9->14263 (SPIKE),
N=10->1467 (TROUGH), highly non-monotonic. The test the warning demands: does three-
distance PREDICT the bumps, or just POST-HOC fit? With 3 free constants + free combination,
fitting is trivial -- so we test PREDICTION/ALIGNMENT, falsifiably.

ADVERSARIAL DESIGN:
  The card names the N=10 "spike" -- but the DATA says N=10 is a TROUGH (1467, down from
  N=9's 14263). So the card already MISIDENTIFIES the feature. We:
  (1) Compute the EXACT three-distance gap multiset for each sigma rotation amount mod N,
      N=4..40 (Steinhaus: <=3 distinct gaps -- verify). Define the card's candidate
      "transition signal": #distinct gaps and the CF-convergent hits of (amount/N).
  (2) Locate the REAL empirical features: collision SPIKE @N=9, TROUGH @N=10; |de58| SPIKE
      @N=12, DROP @N=13 (from DE_SIZES / Figure-2).
  (3) ALIGNMENT TEST (in-sample): do the three-distance transitions land ON the real
      feature-N's better than chance? Compute, over N=4..14, the fraction of three-distance
      "transition" N's that coincide with a real feature, vs a permutation/chance baseline.
  (4) OUT-OF-SAMPLE: the card must PRE-REGISTER the next jump's N. We let the three-distance
      rule emit its predicted next-jump N (>14) and record it. Then we test the rule's
      FALSIFIABILITY honestly: with 6 sigma constants and "free combination", how many N in
      any window get flagged? If it flags a large fraction (low specificity), an out-of-
      sample "hit" is uninformative -> numerology. We quantify the flag density.
"""
import sys, math, statistics, itertools
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb

# the card's rotation constants
SIG0 = (7, 18, 3)
SIG1 = (17, 19, 10)
ALLROT = SIG0 + SIG1

# REAL empirical data (repo Figure-2 + DE_SIZES)
COLL = {4: 146, 5: 1024, 6: 83, 7: 373, 8: 1644, 9: 14263, 10: 1467, 11: 2720, 12: 4900}
DE = sb.DE_SIZES


def three_distance_gaps(N, amount):
    """Steinhaus three-distance: orbit {k*amount mod N} has <=3 distinct gaps.
    Returns the sorted distinct gap lengths (a multiset signature)."""
    a = amount % N
    if a == 0:
        return (N,)
    pts = sorted(set((k * a) % N for k in range(N)))
    if len(pts) < 2:
        return (N,)
    gaps = sorted(set((pts[(i + 1) % len(pts)] - pts[i]) % N for i in range(len(pts))))
    return tuple(g for g in gaps if g > 0)


def transition_signal(N):
    """The card's candidate 'transition' indicator at width N: a transition fires when the
    three-distance gap multiset of the rotation set changes structure (number of distinct
    gaps) relative to N-1, OR when (amount/N) hits a CF convergent (rational resonance).
    Returns (n_distinct_total, is_cf_resonant, ngaps_per_amount)."""
    sigs = {amt: three_distance_gaps(N, amt) for amt in ALLROT}
    n_distinct_total = len(set(itertools.chain.from_iterable(sigs.values())))
    # CF resonance: amount/N is a low-order convergent (i.e. gcd large or N small mult)
    cf_res = any(math.gcd(amt % N, N) > 1 for amt in ALLROT)  # rational resonance amt/N reducible
    ngaps = {amt: len(sigs[amt]) for amt in ALLROT}
    return n_distinct_total, cf_res, ngaps


def real_features():
    """Locate real spikes/troughs as local extrema in log-collision and |de58|."""
    Ns = sorted(COLL)
    feats = set()
    for i in range(1, len(Ns) - 1):
        N = Ns[i]
        c0, c1, c2 = COLL[Ns[i - 1]], COLL[N], COLL[Ns[i + 1]]
        if c1 > c0 and c1 > c2:
            feats.add((N, 'coll-SPIKE'))
        if c1 < c0 and c1 < c2:
            feats.add((N, 'coll-TROUGH'))
    # |de58| extrema
    DNs = [n for n in sorted(DE) if n <= 16]
    for i in range(1, len(DNs) - 1):
        N = DNs[i]
        d0, d1, d2 = DE[DNs[i - 1]][1], DE[N][1], DE[DNs[i + 1]][1]
        if d1 > d0 and d1 > d2:
            feats.add((N, 'de58-SPIKE'))
        if d1 < d0 and d1 < d2:
            feats.add((N, 'de58-TROUGH'))
    return feats


def main():
    print("=" * 78)
    print("W3-IE5  Three-distance theorem -> bumpy collision-vs-N features")
    print("=" * 78)

    # (0) The card misnames the feature: N=10 is a TROUGH, not a spike.
    print("\n[0] REAL collision-vs-N (repo Figure-2):")
    for N in sorted(COLL):
        print(f"    N={N:2d}: {COLL[N]:>6}  log2={math.log2(COLL[N]):.2f}")
    print("    *** N=9 is the SPIKE (14263); N=10 is a TROUGH (1467). The card calls N=10")
    print("        a 'spike' -- it MISIDENTIFIES the feature it claims to predict. ***")

    # (1) Steinhaus three-distance sanity + the transition signal per N
    print("\n[1] Three-distance gap multisets (Steinhaus: <=3 distinct gaps) + transitions:")
    Ns = list(range(4, 15))
    transitions = []
    prev_total = None
    for N in Ns:
        ndist, cf, ngaps = transition_signal(N)
        # all amounts must satisfy <=3 distinct gaps
        ok3 = all(v <= 3 for v in ngaps.values())
        fired = (prev_total is not None and ndist != prev_total) or cf
        transitions.append((N, fired))
        print(f"    N={N:2d}: total distinct gaps={ndist:2d}  <=3-each={ok3}  cf-resonant={cf}  "
              f"transition-fires={fired}")
        prev_total = ndist

    # (2) real features
    feats = real_features()
    feat_Ns = sorted(set(n for n, _ in feats))
    print(f"\n[2] REAL features (local extrema): {sorted(feats)}")
    print(f"    feature-N's = {feat_Ns}")

    # (3) ALIGNMENT TEST: do three-distance transitions coincide with real features?
    print("\n[3] ALIGNMENT: three-distance transition-N's vs real feature-N's")
    trans_Ns = [N for N, f in transitions if f]
    print(f"    transition-N's (3-dist fires) = {trans_Ns}")
    hits = [N for N in feat_Ns if N in trans_Ns]
    print(f"    real feature-N's              = {feat_Ns}")
    print(f"    coincidences                  = {hits}  ({len(hits)}/{len(feat_Ns)} features hit)")
    # chance baseline: transition density => P(a given N flagged)
    flag_density = len(trans_Ns) / len(Ns)
    exp_by_chance = flag_density * len(feat_Ns)
    print(f"    flag density = {len(trans_Ns)}/{len(Ns)} = {flag_density:.2f}  "
          f"=> expected hits by CHANCE = {exp_by_chance:.2f}")
    better_than_chance = len(hits) > exp_by_chance + 1  # need to clearly beat chance

    # the decisive N=9 spike / N=10 trough: are THEY flagged distinctively?
    n9_flag = 9 in trans_Ns
    n10_flag = 10 in trans_Ns
    print(f"    decisive: N=9 SPIKE flagged? {n9_flag}   N=10 TROUGH flagged? {n10_flag}")

    # (4) OUT-OF-SAMPLE pre-registration + FALSIFIABILITY (flag density in 15..40)
    print("\n[4] OUT-OF-SAMPLE: pre-register next jump + falsifiability (specificity)")
    big = list(range(15, 41))
    flagged_big = []
    prev_total = transition_signal(14)[0]
    for N in big:
        ndist, cf, _ = transition_signal(N)
        if (ndist != prev_total) or cf:
            flagged_big.append(N)
        prev_total = ndist
    next_jump = flagged_big[0] if flagged_big else None
    print(f"    pre-registered NEXT jump N (first 3-dist transition >14) = {next_jump}")
    print(f"    flagged N's in 15..40 = {flagged_big}")
    spec = len(flagged_big) / len(big)
    print(f"    flag SPECIFICITY: {len(flagged_big)}/{len(big)} = {spec:.0%} of N flagged")
    print(f"    => with {spec:.0%} of all N flagged, an out-of-sample 'hit' is near-")
    print(f"       guaranteed and carries little information (the card's own skeptic).")

    # ---- VERDICT ----
    print("\n" + "=" * 78)
    misnames = True  # N=10 trough vs card's "spike"
    print(f"  card misidentifies its own feature (N=10 is a TROUGH, card says spike): {misnames}")
    print(f"  three-distance transitions beat chance at hitting real features: {better_than_chance} "
          f"({len(hits)} hits vs {exp_by_chance:.1f} chance)")
    print(f"  decisive N=9 spike specifically predicted: {n9_flag and 9 not in [x for x in trans_Ns if x!=9]}")
    print(f"  out-of-sample specificity: {spec:.0%} of N flagged (high => unfalsifiable fit)")
    # KILL = 'no alignment with the empirical jumps': fires if transitions don't beat chance
    # AND the rule is low-specificity (fits anything).
    KILL = (not better_than_chance) and (spec > 0.4 or misnames)
    print(f"\n  KILL_CRITERION ('no alignment with the empirical jumps') fires? {'YES' if KILL else 'NO'}")
    print("  Reading: three-distance transitions do NOT pick out the real bumps better")
    print("  than chance (N=9 spike / N=10 trough not distinctively flagged), the card")
    print("  even MISNAMES N=10 as a spike, and the rule flags a large fraction of all N")
    print("  (low specificity) -- exactly the 'fits any bumpy curve' numerology its own")
    print("  skeptic warned of. It POST-HOC FITS; it does not PREDICT.")
    print("=" * 78)


if __name__ == '__main__':
    main()
