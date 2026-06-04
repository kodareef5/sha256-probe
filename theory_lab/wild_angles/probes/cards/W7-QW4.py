"""
W7-QW4 — Interference fringe -> the N=10 bump as a singular-value coalescence  [P3 cheap, fragile]

CARD CLAIM: constructive interference = two eigenphases coalescing (a singular-value
crossing in D); conjecture the rotations make D's top-two singular values cross at N=10
(the unique two-branching-bit N), splitting at 9,11. Predicts the next anomalous N.

PROBE (cheapest, per CATALOG): N=8..14 top-two singular-value gap s1-s2 of D(N) (two
power iterations); a pronounced DIP at N=10 coinciding with the collision bump? predict
& test a second dip.

KILL: no local minimum at N=10, OR the bump fails to replicate under alternating-fill
corrections.

ADVERSARIAL PRIOR #4: there is NO N=10 bump. N=10 is a yield TROUGH, not a bump (killed
4x); N=9 PEAKS. Repo census: collision yields N=8..12 = (4322, 52821, 19677, --, 92975)
[bdd_scaling memory] and kernel-sweep N=9=14263 (peak). So the "bump at N=10" premise is
empirically FALSE before we even build D. We still build s1-s2(D) across N to check
whether the discriminant manufactures a spurious dip at N=10 (which would itself be the
artifact the kill names).
"""
import sys, time, math
import numpy as np
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
import transfer_operator as to
import _qw_kit as qw

s = sb.s
np.set_printoptions(precision=5, suppress=True)

# Repo-verified per-N collision yields (the object the 'bump' would live in).
# From MEMORY project_bdd_scaling (collision-list builder counts) + kernel-sweep peak.
YIELDS = {8: 4322, 9: 52821, 10: 19677, 12: 92975}     # note N=9 >> N=10 -> N=10 is a TROUGH


def top2_gap(N, samples=14000, seed=1, max_heads=160):
    """s1 - s2 of the discriminant D of the cascade-pinned diff chain at width N."""
    states, P = to.build_diff_operator_fast(N, msgdiff=0, samples=samples,
                                             seed=seed, max_heads=max_heads)
    D = qw.discriminant(P)
    sv = qw.svals(D)
    s1 = float(sv[0]); s2 = float(sv[1]) if len(sv) > 1 else 0.0
    # average over a few seeds to de-noise the sampled operator
    return s1, s2, s1 - s2, len(states)


def top2_gap_avg(N, seeds=(1, 2, 3), samples=14000, max_heads=160):
    g = []
    s1s = []; s2s = []
    for sd in seeds:
        s1, s2, gap, n = top2_gap(N, samples=samples, seed=sd, max_heads=max_heads)
        g.append(gap); s1s.append(s1); s2s.append(s2)
    return float(np.mean(s1s)), float(np.mean(s2s)), float(np.mean(g)), float(np.std(g))


if __name__ == '__main__':
    print("=" * 74)
    print("W7-QW4 : is there a top-two singular-value DIP at N=10 (a coalescence)?")
    print("=" * 74)

    print("\n--- (0) PREMISE CHECK: is N=10 even a collision bump? (repo census) ---")
    print(f"    yields  N=8:{YIELDS[8]}  N=9:{YIELDS[9]}  N=10:{YIELDS[10]}  N=12:{YIELDS[12]}")
    print(f"    N=9/N=10 ratio = {YIELDS[9]/YIELDS[10]:.2f}  ->  N=10 is a "
          f"{'TROUGH (N=9 peaks)' if YIELDS[9] > YIELDS[10] else 'BUMP'}, not a bump.")

    print("\n--- (1) discriminant top-two gap s1-s2(D) vs N (look for a dip at N=10) ---")
    print(f"{'N':>3} {'s1':>8} {'s2':>8} {'s1-s2':>9} {'std':>7} {'dim':>5}")
    gaps = {}
    for N in (8, 9, 10, 11, 12):
        t0 = time.time()
        s1, s2, gap, std = top2_gap_avg(N, seeds=(1, 2, 3), samples=14000, max_heads=160)
        gaps[N] = gap
        # one extra call just to print dim
        _, _, _, dim = top2_gap(N, samples=8000, seed=1, max_heads=160)
        print(f"{N:>3} {s1:>8.5f} {s2:>8.5f} {gap:>9.5f} {std:>7.5f} {dim:>5}"
              f"   t={time.time()-t0:.1f}s")

    print("\n--- (2) is N=10 a LOCAL MINIMUM of s1-s2(D)? ---")
    for N in (9, 10, 11):
        nb = [gaps.get(N-1), gaps.get(N), gaps.get(N+1)]
        if None not in nb:
            is_min = nb[1] < nb[0] and nb[1] < nb[2]
            print(f"    N={N}: gap[{N-1},{N},{N+1}] = "
                  f"({nb[0]:.5f}, {nb[1]:.5f}, {nb[2]:.5f}) -> "
                  f"{'LOCAL MIN (dip)' if is_min else 'not a dip'}")
    g10_min = (10 in gaps and 9 in gaps and 11 in gaps
               and gaps[10] < gaps[9] and gaps[10] < gaps[11])
    print(f"\n  N=10 a singular-value coalescence dip?  {g10_min}")
    print("  (kill fires if there is NO local minimum at N=10)")
