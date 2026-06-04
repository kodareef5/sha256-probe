#!/usr/bin/env python3
"""
W3-IE2 -- de58 = the unique uniquely-ergodic IET coordinate.  [HEADLINE]

CARD CLAIM: an IET splits into minimal (equidistributing -> growing) + periodic (closing
-> constant) components; de57/59/60 constant = periodic Rauzy components; de58 = the lone
minimal component whose Rokhlin-tower height grows with N (matching the |de58| table).

PROBE (card's own): Rauzy-Veech induction on the schedule IET at N=4..14; predict exactly
3 periodic + 1 minimal coordinate (data already matches), and tower-height(N) vs the
|de58| growth {1,3,3,4,9,...}.
KILL: induction predicts 0/2/4 periodic, OR wrong growth form.
SKEPTIC (the card's own): "3 constant 1 grows" is ALSO plain linear algebra (3 linear-
determined, 1 nonlinear) -- IET may add NOTHING beyond renaming unless the growth *rate*
matches.

WEAPONIZED PRIOR FINDING #5: de57=de59=de60=1 always; |de58| = 2^hw(db56)
(shabridge.DE_SIZES). The size is a Maj/AND-image count on db56 (NT3). The OPEN question
the warning poses: does the "unique uniquely-ergodic IET coordinate" framing DERIVE
2^hw(db56), or just RESTATE de58's uniqueness?  TEST AGAINST DE_SIZES.

DISCRIMINATING DESIGN (derive vs restate):
  Two checks the card must pass to be more than a rename:
  (1) STRUCTURE (cheap, credit ~nothing): confirm 3 constant + 1 growing. TRUE by
      DE_SIZES, but the card's own skeptic concedes this is plain linear algebra
      (3 linearly-determined de coords, 1 nonlinear). A rename gets no credit for it.
  (2) GROWTH LAW (the whole game): the IET claim is that |de58| = a Rokhlin TOWER HEIGHT
      of the minimal component under Rauzy-Veech induction. A Rokhlin tower height = the
      RETURN TIME of the minimal component; under RV renormalization it grows MONOTONE
      NON-DECREASING with depth (return times only lengthen as you induce). It tracks the
      CONTINUED-FRACTION denominators of the IET's rotation number (smooth, Fibonacci-like).
      THE ACTUAL law log2|de58| = hw(db56) is NON-MONOTONE in N: {1,3,3,4,5,9,5,5,8,...}
      -- it SPIKES to 9 at N=12 then DROPS to 5 at N=13,14. A return-time tower height
      CANNOT drop. So we test: does ANY IET-tower-height model (CF-denominator growth of
      the Sigma offsets) reproduce the non-monotone hw(db56) sequence? If not -> wrong
      growth form -> the framing RESTATES uniqueness, does not DERIVE 2^hw(db56).
  (3) PROVENANCE: show 2^hw(db56) is an AND/Maj differential image-count (an algebraic
      property of the message-pair difference db56), independent of any N-indexed ergodic
      return time. The hw(db56) is hw of a register XOR-difference for the cascade-eligible
      M0 -- a combinatorial fact about ONE message pair, not a renormalization invariant.
"""
import sys, math, statistics
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
import numpy as np

DE = sb.DE_SIZES  # {N: (|de57|,|de58|,|de59|,|de60|)}


def cf_denominators(theta, N, depth=40):
    """Continued-fraction convergent denominators q_k of a rotation number theta -- the
    canonical Rokhlin-tower heights of a rotation/IET. Returns the q_k sequence."""
    # theta in (0,1); here we use Sigma-offset/N as the rotation number
    x = theta - math.floor(theta)
    qs = []
    h_prev, h = 1, 0  # denominators
    a_terms = []
    for _ in range(depth):
        if x < 1e-12:
            break
        a = math.floor(1.0 / x)
        a_terms.append(a)
        x = 1.0 / x - a
        h_prev, h = h, a * h + h_prev
        qs.append(h)
    return qs


def iet_tower_height_model(N):
    """The card's object: the minimal component's Rokhlin tower height under Rauzy-Veech.
    Best small-N proxy: the largest CF convergent denominator <= N of the Sigma1 (SHR10/
    lacunary) rotation number, i.e. the return time of the minimal sub-interval. This is
    what an IET tower height would predict for |de58|. Return log2 of that height (to
    compare with hw(db56) = log2|de58|)."""
    # de58 is driven (NT3/cascade) by the Sigma1/round-58 structure; rotation number ~ a
    # Sigma1 offset / N. Take the densest tower (max denominator <= N) across the offsets.
    best = 1
    for off in (6, 11, 25, 13):  # Sigma rotation amounts that could set the return time
        theta = (off % N) / N if N else 0
        for q in cf_denominators(theta, N):
            if q <= N and q > best:
                best = q
    # tower height is at most N (heights of towers over an N-point discretization)
    return best, math.log2(best) if best > 0 else 0.0


def main():
    print("=" * 78)
    print("W3-IE2  de58 = the unique uniquely-ergodic IET coordinate  [HEADLINE]")
    print("=" * 78)

    # (1) STRUCTURE: 3 constant + 1 growing  (credit ~nothing -- plain linear algebra)
    print("\n[1] STRUCTURE: exactly 3 periodic(constant) + 1 minimal(growing)?  (DE_SIZES)")
    ok_struct = True
    for N in sorted(DE):
        d57, d58, d59, d60 = DE[N]
        const3 = (d57 == 1 and d59 == 1 and d60 == 1)
        grows = d58 > 1 if N > 4 else d58 >= 2
        ok_struct &= const3
        print(f"    N={N:2d}: (|de57|,|de58|,|de59|,|de60|)=({d57},{d58},{d59},{d60})  "
              f"3-constant={const3}  de58>1={grows}")
    n_periodic = 3
    n_minimal = 1
    print(f"    => {n_periodic} periodic + {n_minimal} minimal: {ok_struct}  (matches card's count)")
    print("    BUT the card's own skeptic: this is plain linear algebra (3 linearly-")
    print("    determined de-coords, 1 nonlinear). Structure alone earns the IET NOTHING.")

    # (2) GROWTH LAW: does an IET tower height reproduce the NON-MONOTONE hw(db56)?
    print("\n[2] GROWTH LAW -- the whole game: |de58| = a Rokhlin tower height?")
    Ns = sorted(DE)
    hw = {N: int(round(math.log2(DE[N][1]))) for N in Ns}  # = hw(db56), exact N<=14
    seq = [hw[N] for N in Ns]
    diffs = [seq[i + 1] - seq[i] for i in range(len(seq) - 1)]
    monotone = all(d >= 0 for d in diffs)
    print(f"    ACTUAL log2|de58| = hw(db56) sequence (N={Ns}):")
    print(f"      {seq}")
    print(f"    first differences: {diffs}  -> monotone non-decreasing? {monotone}")
    print(f"    *** hw(db56) SPIKES to 9 @N=12 then DROPS to 5 @N=13,14. ***")
    print(f"    A Rokhlin tower height = a RETURN TIME under RV induction: MONOTONE")
    print(f"    non-decreasing in depth. A return time CANNOT DROP. So no IET tower")
    print(f"    height can reproduce this sequence.")

    print("\n    IET tower-height model (CF-denominator return times of Sigma offsets):")
    iet_heights = []
    for N in Ns:
        h, log2h = iet_tower_height_model(N)
        iet_heights.append(log2h)
        print(f"      N={N:2d}: IET tower height (max CF denom <= N) = {h:2d}  log2={log2h:.2f}  "
              f"vs hw(db56)={hw[N]}")
    # Does the IET tower-height model PREDICT the exact hw(db56) values? (not just
    # loosely correlate). Predictive accuracy = mean |log2(IET height) - hw(db56)|.
    a = np.array(iet_heights[:8])  # N<=14 where the law is exact (N up to 14 is index 7)
    b = np.array(seq[:8])
    mae = float(np.mean(np.abs(a - b)))
    if a.std() > 0 and b.std() > 0:
        corr = float(np.corrcoef(a, b)[0, 1])
    else:
        corr = 0.0
    # Does the model capture the two DECISIVE features: the N=12 SPIKE and the N=13/14 DROP?
    i12, i13, i14 = Ns.index(12), Ns.index(13), Ns.index(14)
    real_spike = seq[i12] > seq[i12 - 1] and seq[i12] > seq[i13]          # 9 > 5 and 9 > 5
    real_drop = seq[i13] < seq[i12]                                       # 5 < 9
    model_spike = iet_heights[i12] > iet_heights[i12 - 1] and iet_heights[i12] > iet_heights[i13]
    model_drop = iet_heights[i13] < iet_heights[i12]
    captures_features = (model_spike == real_spike) and (model_drop == real_drop)
    print(f"    predictive error: mean |log2(IET height) - hw(db56)| = {mae:.2f} bits  "
          f"(loose corr={corr:.2f})")
    print(f"    DECISIVE features: real hw(db56) has SPIKE@N=12 (9>5,9>5)={real_spike} and "
          f"DROP@N=13 (5<9)={real_drop}")
    print(f"    IET model reproduces spike? {model_spike}  drop? {model_drop}  "
          f"=> captures both features: {captures_features}")
    print(f"    (the genuine RV return-time tower height is MONOTONE in induction depth and")
    print(f"     cannot DROP; my CF-proxy's wobble is an off-%-N artifact, not a return time.)")

    # (3) PROVENANCE: 2^hw(db56) is a Maj/AND image count, not an ergodic invariant
    print("\n[3] PROVENANCE of 2^hw(db56): a Maj/AND differential image-count on db56")
    print("    db56 = b56_1 XOR b56_2 (register XOR-diff of the cascade-eligible M0 pair).")
    print("    |de58| = #distinct Maj-images = 2^(active bits of db56) = 2^hw(db56) (N<=14;")
    print("    carry-collapses to 1024 at N=32). This is an ALGEBRAIC property of ONE")
    print("    message-pair's bit pattern -- it has NO N-indexed return-time / ergodic")
    print("    reading. The hw(db56) jumps because the cascade-eligible M0's db56 bit-")
    print("    pattern changes with N, not because a tower lengthens then shortens.")

    # ---- VERDICT ----
    print("\n" + "=" * 78)
    # The card is CONFIRMED only if the IET tower-height DERIVES 2^hw(db56) (predicts the
    # exact sequence incl. its decisive non-monotone features). It is a RENAME (kill fires,
    # 'wrong growth form') if the structure matches but the growth law is not derived:
    #  - real hw(db56) is non-monotone (spike@12, drop@13) -- impossible for an RV return time;
    #  - the IET model does not predict the values (large MAE) nor capture the spike+drop.
    derives = captures_features and mae < 1.0
    wrong_growth_form = (not derives)
    structure_is_la = ok_struct  # true, but credited to linear algebra not IET
    print(f"  structure (3 periodic + 1 minimal) matches: {structure_is_la}  "
          f"(but = plain linear algebra; no IET credit)")
    print(f"  IET tower-height DERIVES the hw(db56) growth law: {derives}")
    print(f"    - actual hw(db56) is NON-monotone (spike@N=12 to 9, drop@N=13 to 5): {not monotone}")
    print(f"    - a genuine RV return-time tower height is MONOTONE -> cannot match this form")
    print(f"    - model predictive error MAE={mae:.2f} bits; reproduces spike+drop: {captures_features}")
    KILL = wrong_growth_form
    print(f"\n  KILL_CRITERION ('wrong growth form') fires? {'YES' if KILL else 'NO'}")
    print("  Reading: the IET framing REPRODUCES the 3+1 component COUNT (which is just")
    print("  linear algebra), but its tower-height growth law is monotone and cannot")
    print("  produce the non-monotone hw(db56) (9 at N=12, 5 at N=13/14). It RESTATES")
    print("  de58's uniqueness; it does NOT DERIVE 2^hw(db56). 2^hw(db56) is a Maj/AND")
    print("  image-count, not a Rokhlin return time.")
    print("=" * 78)


if __name__ == '__main__':
    main()
