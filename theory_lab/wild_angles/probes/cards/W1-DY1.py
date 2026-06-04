#!/usr/bin/env python3
"""
W1-DY1 — Differential transfer operator + Ruelle zeta -> collisions as a leading
eigenvalue.  HEADLINE probe.

Card claim: build a weighted Perron-Frobenius operator L on per-round modular
differentials; log2(lambda_max(L)) should be ~0.74 (the measured collision-growth
exponent) and N-stable; de58-low-rank predicts L is tiny.

Kill_criterion: "Dead if log2(lambda_max) isn't within ~10% of the measured
exponent at two N, or lambda_max drifts with N."

This probe is ADVERSARIAL by construction. Two things are checked that the card
glosses:
  (A) What IS the measured exponent? We refit it from the repo's own collision
      table (Figure 2, paper_figures_data.md) instead of trusting the rounded 0.74.
  (B) Is log2(lambda_max) a per-N slope (units: bits per unit word-width) or a
      per-round entropy rate (units: bits per round)?  These are different
      objects; the card conflates them.  We report log2(lambda_max) at several N
      and ask both (i) is it ~0.74 and (ii) does it drift with N.

Reuses kernels/transfer_operator.py (the Batch-C dependency).
"""
import sys, time
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
import transfer_operator as TO
import numpy as np

TARGET = sb.GROWTH_EXPONENT  # 0.74, pinned ground truth


def refit_measured_exponent():
    """Re-derive the collision-growth exponent from the repo's Figure-2 table.
    Returns (pooled_slope, per_class) so we know the real spread behind '0.74'."""
    # N, best collision count (mini-SHA sr=60, best kernel) — paper_figures_data.md
    data = [(4, 146), (5, 1024), (6, 83), (7, 373), (8, 1644),
            (9, 14263), (10, 1467), (11, 2720)]
    N = np.array([d[0] for d in data], float)
    log2C = np.log2([d[1] for d in data])
    A = np.vstack([N, np.ones_like(N)]).T
    pooled = np.linalg.lstsq(A, log2C, rcond=None)[0][0]
    per_class = {}
    for r in range(4):
        idx = [i for i in range(len(N)) if int(N[i]) % 4 == r]
        if len(idx) >= 2:
            Ni = N[idx]; Li = log2C[idx]
            Ai = np.vstack([Ni, np.ones_like(Ni)]).T
            per_class[r] = float(np.linalg.lstsq(Ai, Li, rcond=None)[0][0])
    return float(pooled), per_class


def measure_operator(Ns, msgdiff=0, samples=30000, seed=7):
    """Build the differential transfer operator at each N in BOTH the
    probability normalization (Markov) and the raw-count normalization (the
    card's literal L[d',d]=#realizations). Report the spectrum of each."""
    rows = []
    for N in Ns:
        t0 = time.time()
        states, L, C = TO.build_diff_operator_fast(
            N, msgdiff=msgdiff, samples=samples, seed=seed,
            max_heads=400, return_counts=True)
        info_p = TO.spectral_summary(L)        # probability operator (Markov)
        # Card's literal count operator: realizations per conditioning state.
        # With the message difference fixed there are exactly 2^N message words,
        # each mapping an incoming head to one out-head, so the meaningful raw
        # count operator is (2^N) * L  (sampling-budget divided out). Its Perron
        # is therefore 2^N * lam_p exactly; we form it so the number is the true
        # per-round realization multiplier, not the Monte-Carlo budget.
        Lcount = (2 ** N) * L
        info_c = TO.spectral_summary(Lcount)
        rows.append(dict(N=N, heads=len(states),
                         lam_p=info_p['lambda_max'], log2_p=info_p['log2_lambda'],
                         lam_c=info_c['lambda_max'], log2_c=info_c['log2_lambda'],
                         secs=time.time() - t0))
    return rows


def main():
    print("=" * 70)
    print("W1-DY1: differential transfer operator -> leading eigenvalue vs 0.74")
    print("=" * 70)

    pooled, per_class = refit_measured_exponent()
    print("\n[A] What is the 'measured exponent' really?")
    print(f"    pinned ground-truth GROWTH_EXPONENT = {TARGET}")
    print(f"    refit pooled slope (all N, best kernel) = {pooled:.4f}")
    print(f"    per-(N mod 4)-class slopes            = "
          + ", ".join(f"{k}:{v:.3f}" for k, v in per_class.items()))
    print(f"    -> '0.74' is a rough cross-class average; real spread "
          f"~{min(per_class.values()):.2f}-{max(per_class.values()):.2f}")

    print("\n[B] Leading eigenvalue of the per-round differential operator L")
    print("    (cascade regime: msgdiff=0, active differential injected)")
    print("    Two normalizations of the SAME operator:")
    print("      prob  : L[d',d]=P(d->d')  (Markov)  -> Perron is ALWAYS 1")
    print("      count : L[d',d]=#realizations (card's literal definition)")
    Ns = [4, 6, 8, 10]
    rows = measure_operator(Ns, msgdiff=0, samples=30000, seed=7)
    print(f"\n    {'N':>3} {'heads':>6} {'lam(prob)':>10} {'log2':>7} "
          f"{'lam(count)':>11} {'log2':>8} {'secs':>6}")
    for r in rows:
        print(f"    {r['N']:>3} {r['heads']:>6} {r['lam_p']:>10.4f} "
              f"{r['log2_p']:>7.3f} {r['lam_c']:>11.1f} {r['log2_c']:>8.3f} "
              f"{r['secs']:>6.1f}")

    # The card's verdict number is log2(lambda_max). Evaluate BOTH norms.
    log2_p = [r['log2_p'] for r in rows]
    log2_c = [r['log2_c'] for r in rows]
    lam_c = [r['lam_c'] for r in rows]

    print("\n[VERDICT INPUTS]")
    print(f"    log2(lam) PROB  across N = {[round(x,4) for x in log2_p]}"
          f"  (structurally pinned to 0: stochastic Perron)")
    print(f"    log2(lam) COUNT across N = {[round(x,4) for x in log2_c]}")
    near_p = [abs(x - TARGET) <= 0.10 * TARGET for x in log2_p]
    near_c = [abs(x - TARGET) <= 0.10 * TARGET for x in log2_c]
    print(f"    within 10% of {TARGET}:  prob={near_p} count={near_c}")
    # count-operator Perron drifts with N? (it grows with per-round freedom)
    drift_c = max(lam_c) - min(lam_c)
    print(f"    count-operator lam range = [{min(lam_c):.1f}, {max(lam_c):.1f}]"
          f"  drift={drift_c:.1f}  (grows with N => NOT N-stable)")

    print("\n[KILL CRITERION EVALUATION]")
    two_N_prob = sum(near_p) >= 2
    two_N_count = sum(near_c) >= 2
    drifts_count = drift_c > 0.10 * min(lam_c)
    print(f"    PROB  norm: log2(lam) within 10% of {TARGET} at >=2 N? "
          f"{two_N_prob}  (it is identically 0)")
    print(f"    COUNT norm: log2(lam) within 10% of {TARGET} at >=2 N? "
          f"{two_N_count};  lam drifts with N? {drifts_count}")
    fired = (not two_N_prob) and ((not two_N_count) or drifts_count)
    if fired:
        print("    => KILL CRITERION FIRES in BOTH natural normalizations:")
        print("       prob-norm log2(lam)=0 (never 0.74); count-norm not 0.74")
        print("       AND drifts with N.")
    else:
        print("    => kill criterion does NOT fire")

    # Charitable interpretation: maybe lam^64 = collision count C(N) ~ 2^(0.74N)?
    print("\n[CHARITABLE] back-solve lam from 'lam^64 = 2^(0.74 N)':")
    for N in Ns:
        need = 2 ** (TARGET * N / 64.0)
        print(f"    N={N}: lam would need to be 2^(0.74*{N}/64) = {need:.5f}"
              f"  (log2={TARGET*N/64.0:.4f})")
    print("    -> this REQUIRES lam to grow with N (2^(0.74N/64)), which")
    print("       directly contradicts the card's own 'N-stable' premise.")

    # Adversarial second look: is log2(lam) even a per-N slope at all?
    print("\n[SKEPTIC] per-round entropy rate vs per-N growth slope:")
    print("    log2(lambda_max) is bits/ROUND (a fixed-point property of L);")
    print("    0.74 is bits per unit WORD-WIDTH N (slope of log2 C vs N).")
    print("    These are different units; converging them would be a coincidence,")
    print("    not a structural identity, unless lam itself scaled like 2^0.74"
          " per N.")


if __name__ == '__main__':
    main()
