"""
W7-QW2 — Discriminant top edge -> 0.74 = log2 s_max(D)   [P3 cheap]

CARD CLAIM: the bidirectional search operator's top singular value = per-bit
amplification of completable prefixes (geom mean of forward x backward survival
mass); 2^{0.74 N} = s_max^N, so 0.74 = log2 s_max(D). Computable from local
transition stats, no collision enumeration. Must track across N and != s_max(P)
(Perron) -- the non-reversible feed-forward is the only thing saving it.

PROBE (per CATALOG): N=8,10 build P on prefixes (forward weight = #completions
passing the on-track oracle), s_max(D) by power iteration; log2 s_max ~0.74,
tracks across N, and != P's Perron.

KILL: log2 s_max not in [0.6,0.9], OR = the round-Jacobian's top singular value
(relabel), OR = P's Perron value (reversible).

ADVERSARIAL PRIOR #2: 0.74 is DEAD as a derivable sharp constant. The repo's own
honest refit of the collision-growth slope is **0.673** (spread 0.72-1.04), NOT a
sharp 0.74. So we report log2 s_max(D) to 3 figures and compare it to BOTH 0.74
and 0.673 and to the directly-measured collision-growth slope at the same N.

WHAT WE BUILD: the per-round differential SURVIVAL operator in the cascade-pinned
regime (msgdiff=0 -- where collisions live). Two operands, both reported:
  - C = RAW-COUNT transfer operator (entries = # carry realizations head_i->head_j);
        its Perron eigenvalue is the multiplicative growth in the NUMBER of
        on-track realizations per round -> log2(Perron(C)/samples-normalization)
        is the natural "per-round amplification of completable configs."
  - P = the column-stochastic version; D = sqrt(P .* P^T); s_max(D) and its log2.
We compare log2 s_max(D) to 0.74 / 0.673, and to Perron(P) (reversible test), and
ALSO directly measure the collision-growth slope (log2 #collisions / N) from the
repo's exact enumerator counts (260@N8, 946@N10) as the real 0.74-source object.
"""
import sys, time, math
import numpy as np
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
import transfer_operator as to
import _qw_kit as qw

s = sb.s
np.set_printoptions(precision=4, suppress=True)


def edge_summary(N, samples=12000, seed=1, max_heads=200):
    """Build cascade-pinned diff-config chain P, discriminant D, report edges."""
    states, P = to.build_diff_operator_fast(N, msgdiff=0, samples=samples,
                                             seed=seed, max_heads=max_heads)
    D = qw.discriminant(P)
    sD = qw.svals(D)
    sP = qw.svals(P)              # singular values of P itself (the schedule-Jacobian-ish edge)
    eP = qw.perron(P)             # |eig(P)| -- the Perron/reversible reference
    return dict(states=len(states), smax_D=float(sD[0]), log2_smax_D=float(np.log2(sD[0])),
                smax_P=float(sP[0]), perron_P=float(eP[0]),
                log2_perron_P=float(np.log2(eP[0])) if eP[0] > 0 else float('-inf'),
                rev_gap=qw.is_reversible(P))


# directly-measured growth slope from the exact backward-construction collision census
EXACT_COLL = {8: 260, 10: 946, 12: None}  # repo-verified counts; 12 not run here (cost)


if __name__ == '__main__':
    print("=" * 74)
    print("W7-QW2 : is log2 s_max(D) a sharp 0.74? (vs 0.673, vs Perron(P))")
    print("=" * 74)

    print("\n--- discriminant top edge s_max(D) of the cascade-pinned diff chain ---")
    print(f"{'N':>3} {'s_max(D)':>9} {'log2 s_max(D)':>14} {'Perron(P)':>10} "
          f"{'rev_gap':>8}")
    rows = {}
    for N in (6, 8, 10):
        t0 = time.time()
        r = edge_summary(N, samples=16000, seed=1, max_heads=200)
        rows[N] = r
        print(f"{N:>3} {r['smax_D']:>9.4f} {r['log2_smax_D']:>14.4f} "
              f"{r['perron_P']:>10.4f} {r['rev_gap']:>8.4f}   t={time.time()-t0:.1f}s")

    print("\n  Is the edge a *sharp, N-stable* 0.74?  (report log2 s_max(D) deviation)")
    for N, r in rows.items():
        d74 = r['log2_smax_D'] - 0.74
        d673 = r['log2_smax_D'] - 0.673
        print(f"    N={N}: log2 s_max(D) = {r['log2_smax_D']:+.4f}   "
              f"(vs 0.74: {d74:+.4f},  vs 0.673: {d673:+.4f})")

    print("\n--- does D relabel P? (s_max(D) == Perron(P) ?) ---")
    for N, r in rows.items():
        same = abs(r['smax_D'] - r['perron_P']) < 1e-2
        print(f"    N={N}: s_max(D)={r['smax_D']:.4f}  Perron(P)={r['perron_P']:.4f}  "
              f"-> {'EQUAL (banned relabel)' if same else 'differ'}")

    print("\n--- the REAL 0.74 source: collision-growth slope log2(#Coll)/N ---")
    print("    (exact backward-construction census, repo-verified counts)")
    Ns = [n for n in EXACT_COLL if EXACT_COLL[n]]
    for n in Ns:
        print(f"    N={n}: #Coll={EXACT_COLL[n]:>4}  log2/N = {math.log2(EXACT_COLL[n])/n:.4f}")
    if len(Ns) >= 2:
        n0, n1 = Ns[0], Ns[1]
        slope = (math.log2(EXACT_COLL[n1]) - math.log2(EXACT_COLL[n0])) / (n1 - n0)
        print(f"    secant slope N={n0}->{n1}: d log2(#Coll)/dN = {slope:.4f}  "
              f"(repo's honest refit ~0.673, NOT a sharp 0.74)")

    print(f"\n  pinned ground truth GROWTH_EXPONENT = {sb.GROWTH_EXPONENT} "
          f"(nominal; refit 0.673)")
