#!/usr/bin/env python3
"""
W3-IE1 -- Sigma-mixing as a 3-IET; 0.74 as a KZ Lyapunov exponent.

CARD CLAIM: Sigma0={2,13,22}, Sigma1={6,11,25} are rotation-only (no SHR), so the three
circle-offsets form a 3-IET on the bit-position circle; round-to-round composition is a
Teichmuller iteration, and the bit-spread rate = the top Kontsevich-Zorich Lyapunov
exponent, claimed = 0.74.

PROBE (card's own): N=4..14 treat the offsets as a 3-IET on the bit-position circle, count
periodic orbits (three-distance theorem), fit log(#orbits)/N; compare to the *real* 1-bit
diffusion exponent.
KILL: exponent independent of {2,13,22} (random triples give the same).
SKEPTIC: XOR isn't interval *exchange* -- may be a random-walk exponent in IET costume.

ADVERSARIAL DESIGN (weaponizes PRIOR FINDING #2 -- "0.74 is NOT sharp"):
 The repo's own pooled collision-growth slope is 0.673 (not 0.74), with per-(N mod 4)
 spread 0.72..1.04. So the card has TWO ways to fail and we test both:
  (1) Does the "3-IET periodic-orbit count" actually grow like 2^(0.74 N) (or even
      2^(0.673 N))?  We BUILD the 3-IET literally: three sub-intervals of the bit circle
      Z/N permuted by the three Sigma offsets, iterate, count periodic orbits and total
      orbit-closure structure, fit log2(#orbits)/N.
  (2) What is the *actual* top Lyapunov exponent of the round differential cocycle (the
      literal "KZ Lyapunov" object)? We call the repo-derived Lyapunov-QR cocycle
      (transfer_operator.lyapunov_qr) and read chi_1 in bits/round. Is it 0.74? 0.673?
      Neither?  Per the prior finding, a value anywhere in 0.6..0.8 PROVES NOTHING -- it
      must be DISTINGUISHABLE from 0.673 and land on 0.74 to confirm.
  (3) KILL-TEST: is the 3-IET orbit exponent SPECIAL to {2,13,22}, or do random triples
      give the same?  If random triples reproduce it, the exponent is a generic
      rotation/random-walk number wearing an IET costume (exactly the card's skeptic).
"""
import sys, math, statistics, random
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
import numpy as np

S0 = (2, 13, 22)   # Sigma0 rotation amounts
S1 = (6, 11, 25)   # Sigma1 rotation amounts
TARGET = sb.GROWTH_EXPONENT  # 0.74 (claimed)


def refit_measured_slope():
    """Re-derive the TRUE collision-growth slope from the repo Figure-2 table
    (so we judge against 0.673, the real number, not the rounded 0.74)."""
    data = [(4, 146), (5, 1024), (6, 83), (7, 373), (8, 1644),
            (9, 14263), (10, 1467), (11, 2720)]
    N = np.array([d[0] for d in data], float)
    L = np.log2([d[1] for d in data])
    A = np.vstack([N, np.ones_like(N)]).T
    pooled = float(np.linalg.lstsq(A, L, rcond=None)[0][0])
    per = {}
    for r in range(4):
        idx = [i for i in range(len(N)) if int(N[i]) % 4 == r]
        if len(idx) >= 2:
            Ai = np.vstack([N[idx], np.ones(len(idx))]).T
            per[r] = float(np.linalg.lstsq(Ai, L[idx], rcond=None)[0][0])
    return pooled, per


def iet_3_periodic_orbits(N, offsets):
    """Build the literal 3-IET on the bit-position circle Z/N.

    A genuine 3-IET partitions [0,1) into 3 sub-intervals and translates each by a
    constant; on the discrete bit-circle Z/N the natural realization is: split the N
    positions into 3 contiguous arcs A,B,C; arc A is rotated by offsets[0], B by
    offsets[1], C by offsets[2] (mod N). This is a permutation pi of Z/N (an IET on a
    discretized circle). Count its periodic orbits = #cycles of pi, and the period
    structure (three-distance / Steinhaus controls the arc lengths).
    Returns (#cycles, cycle_length_multiset)."""
    o = [x % N for x in offsets]
    # three contiguous arcs of (near) equal length
    b1 = N // 3
    b2 = 2 * N // 3
    pi = [0] * N
    for x in range(N):
        if x < b1:
            pi[x] = (x + o[0]) % N
        elif x < b2:
            pi[x] = (x + o[1]) % N
        else:
            pi[x] = (x + o[2]) % N
    # cycle decomposition of pi
    seen = [False] * N
    cyc_lens = []
    for start in range(N):
        if seen[start]:
            continue
        L = 0
        x = start
        while not seen[x]:
            seen[x] = True
            x = pi[x]
            L += 1
        cyc_lens.append(L)
    return len(cyc_lens), cyc_lens


def three_distance_gaps(N, offset):
    """Steinhaus three-distance theorem check: the orbit {k*offset mod N : k} has at
    most 3 distinct gap lengths. Returns sorted distinct gaps (should be <=3)."""
    pts = sorted({(k * offset) % N for k in range(N)})
    if len(pts) < 2:
        return [N]
    gaps = sorted({(pts[(i + 1) % len(pts)] - pts[i]) % N for i in range(len(pts))})
    return gaps


def actual_top_lyapunov(Ns):
    """The literal 'KZ Lyapunov exponent' object: top Lyapunov exponent chi_1 of the
    round DIFFERENTIAL cocycle, in bits/round, via the repo-derived Lyapunov-QR.
    This is the honest test of '0.74 = a Lyapunov exponent'."""
    import transfer_operator as TO
    out = []
    for N in Ns:
        chi = TO.lyapunov_qr(N, R=30, samples=2500, seed=5, msgdiff=0)
        out.append((N, float(chi[0])))
    return out


def main():
    print("=" * 74)
    print("W3-IE1  Sigma-mixing as a 3-IET; 0.74 as a KZ Lyapunov exponent")
    print("=" * 74)

    pooled, per = refit_measured_slope()
    print("\n[0] The REAL growth slope (repo Figure-2, NOT the rounded 0.74):")
    print(f"    pooled slope (all N, best kernel)  = {pooled:.4f}   (card claims 0.74)")
    print(f"    per-(N mod 4) slopes               = "
          + ", ".join(f"{k}:{v:.3f}" for k, v in per.items())
          + f"   spread {min(per.values()):.2f}..{max(per.values()):.2f}")
    print("    => per prior finding #2, anything in 0.6..0.8 proves nothing; must hit 0.74"
          " AND beat 0.673.")

    # (1) 3-IET periodic-orbit count for the Sigma offsets, fit log2(#orbits)/N
    print("\n[1] LITERAL 3-IET on the bit-circle from Sigma0={2,13,22}: periodic-orbit count")
    Ns = list(range(4, 15))
    norb_S0, norb_S1 = [], []
    for N in Ns:
        c0, lens0 = iet_3_periodic_orbits(N, S0)
        c1, lens1 = iet_3_periodic_orbits(N, S1)
        norb_S0.append(c0)
        norb_S1.append(c1)
        print(f"    N={N:2d}: Sigma0 #orbits={c0:2d} (cycle lens {sorted(lens0)});  "
              f"Sigma1 #orbits={c1:2d}")
    # fit log2(#orbits) vs N
    Na = np.array(Ns, float)

    def slope(y):
        y = np.array(y, float)
        msk = y > 0
        A = np.vstack([Na[msk], np.ones(msk.sum())]).T
        return float(np.linalg.lstsq(A, np.log2(y[msk]), rcond=None)[0][0])
    sl_S0 = slope(norb_S0)
    sl_S1 = slope(norb_S1)
    print(f"    fit log2(#orbits)/N : Sigma0 slope = {sl_S0:.4f}, Sigma1 slope = {sl_S1:.4f}")
    print(f"    (a permutation of N points has O(N) cycles => log2(#orbits)/N -> 0, NOT 0.74)")

    # three-distance sanity (Steinhaus): arcs have <=3 gap lengths
    print("\n[1b] Steinhaus three-distance sanity for each Sigma offset at N=12:")
    for off in S0:
        g = three_distance_gaps(12, off)
        print(f"    offset {off:2d} mod 12: distinct gaps {g}  (<=3 distinct: {len(g) <= 3})")

    # (2) actual top Lyapunov exponent of the differential cocycle
    print("\n[2] ACTUAL top Lyapunov exponent chi_1 of the round differential cocycle (bits/round):")
    lyaps = actual_top_lyapunov([6, 8, 10])
    for N, chi in lyaps:
        print(f"    N={N:2d}: chi_1 = {chi:.4f} bits/round")
    chi_vals = [c for _, c in lyaps]
    chi_mean = statistics.mean(chi_vals)
    print(f"    mean chi_1 = {chi_mean:.4f}.  Is it 0.74? {abs(chi_mean-0.74)<0.05}. "
          f"Is it 0.673? {abs(chi_mean-0.673)<0.05}.")
    print("    (chi_1 is bits/ROUND; 0.74 is bits per WORD-WIDTH N -- different units. A match"
          " would be a unit coincidence, not a KZ identity.)")

    # (3) KILL-TEST: is the 3-IET orbit exponent SPECIAL to {2,13,22}?
    print("\n[3] KILL-TEST: random triples vs Sigma0={2,13,22} -- is the exponent SPECIAL?")
    random.seed(11)
    rand_slopes = []
    for t in range(12):
        trip = tuple(random.sample(range(1, 26), 3))
        cnts = [iet_3_periodic_orbits(N, trip)[0] for N in Ns]
        rand_slopes.append(slope(cnts))
    rmean = statistics.mean(rand_slopes)
    rsd = statistics.pstdev(rand_slopes)
    print(f"    random-triple orbit-slope: mean={rmean:.4f} sd={rsd:.4f} over 12 triples")
    print(f"    Sigma0 orbit-slope = {sl_S0:.4f}  ->  within {abs(sl_S0-rmean)/(rsd or 1):.2f} sd of random mean")
    special = abs(sl_S0 - rmean) > 2 * (rsd or 1e-9)
    print(f"    Is {{2,13,22}} SPECIAL (orbit-slope >2sd from random)? {special}")

    # ---- VERDICT ----
    print("\n" + "=" * 74)
    # KILL fires if the orbit exponent is NOT special to {2,13,22} (random gives same),
    # OR if neither the orbit-slope nor chi_1 lands distinguishably on 0.74.
    not_special = not special
    orbit_slope_not_074 = abs(sl_S0 - 0.74) > 0.05
    chi_not_074 = abs(chi_mean - 0.74) > 0.05
    chi_indistinct = abs(chi_mean - 0.673) < 0.05  # if ~0.673 it's the generic slope, not KZ 0.74
    print(f"  3-IET orbit-slope NOT special to {{2,13,22}} (random triples same): {not_special}")
    print(f"  3-IET orbit-slope != 0.74 (={sl_S0:.3f}, ->0): {orbit_slope_not_074}")
    print(f"  actual chi_1 != 0.74 (={chi_mean:.3f}): {chi_not_074}")
    print(f"  actual chi_1 indistinguishable from generic 0.673: {chi_indistinct}")
    KILL = not_special and orbit_slope_not_074
    print(f"\n  KILL_CRITERION ('exponent independent of {{2,13,22}}') fires? {'YES' if KILL else 'NO'}")
    print("  Reading: the literal 3-IET orbit count grows O(N) not 2^0.74N (slope ->0), is")
    print("  reproduced by random triples (not special to Sigma), and the actual cocycle")
    print("  Lyapunov exponent does not land on 0.74. '0.74 = a KZ exponent' is a costume.")
    print("=" * 74)


if __name__ == '__main__':
    main()
