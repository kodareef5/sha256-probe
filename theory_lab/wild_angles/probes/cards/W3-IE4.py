#!/usr/bin/env python3
"""
W3-IE4 -- Modular add as a billiard; collisions as closed orbits.

CARD CLAIM: a carry/wraparound = a billiard reflection off a 2^i wall; a SHA run = a
billiard path in an N-cube; a collision = a near-closed orbit returning to the diagonal;
rotation constants = launch angles (rational -> periodic -> collision-rich).

PROBE (card's own): N=4..10 render carry events as N-cube wall hits, count periodic orbits
<= length r, compare log(#orbits)/N to 0.74; vary a rotation constant, check collisions
track its CF/rational character.
KILL: orbit count and collision count DIVERGE with N.
SKEPTIC (the card's own): carry "walls" are DATA-DEPENDENT (non-polygonal) -- likely not a
real billiard.

WEAPONIZED PRIOR FINDINGS:
  #2 (0.74 not sharp): the real growth slope is 0.673; compare orbit-growth to BOTH.
  #4 (collisions non-monotone): N=9->14263 SPIKE, N=10->1467 TROUGH. A fixed billiard's
     periodic-orbit count grows SMOOTHLY/regularly with N -- so if collisions are non-
     monotone, orbit-count and collision-count MUST diverge (the kill).

ADVERSARIAL DESIGN:
  The faithful realization of 'modular add as a billiard': the map x -> (x + theta) mod 2^N
  is a rotation on the circle Z/2^N; a carry/wrap (x+theta >= 2^N) is the 'wall hit'; a
  'closed orbit' is the rotation orbit, period = 2^N / gcd(theta, 2^N). Rotation constants
  = launch angles theta. We:
  (1) COUNT periodic orbits of the carry-billiard at each N for the SHA rotation constants
      as launch angles; fit log2(#orbits)/N; compare to 0.673 AND 0.74.
  (2) KILL TEST: put orbit-count growth next to the REAL collision-count growth. Collisions
      are non-monotone (spike@9, trough@10); a rotation/billiard orbit count is monotone/
      smooth in N. Quantify DIVERGENCE: correlation and the sign-of-slope at the N=9->10
      feature (collisions DROP 14263->1467; does orbit-count drop too? rotations don't).
  (3) SKEPTIC TEST (walls data-dependent?): for the ACTUAL SHA adder x+y, the carry-wall
      hit positions (add_carry_trace) depend on the OPERANDS x,y -- show the wall set
      varies across operand pairs at fixed N. A real billiard has a FIXED table; if the
      walls move with the data, it is not a billiard (decoration on carry arithmetic).
"""
import sys, math, statistics, random
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
import adder_diff as ad
import numpy as np

# SHA rotation constants used as billiard launch angles
ROTS = (2, 13, 22, 6, 11, 25, 7, 18, 3, 17, 19, 10)

# REAL collision counts (repo Figure-2) -- the thing orbit-count must NOT diverge from
COLL = {4: 146, 5: 1024, 6: 83, 7: 373, 8: 1644, 9: 14263, 10: 1467}


def billiard_orbits(N, thetas):
    """The carry-billiard = rotations x -> (x+theta) mod 2^N. #periodic orbits for launch
    angle theta = gcd(theta, 2^N) (number of distinct cycles partitioning Z/2^N), each of
    length 2^N/gcd. Total over the rotation set = sum of distinct orbit structures.
    Returns total #distinct periodic orbits across the launch angles."""
    M = 1 << N
    total_orbits = 0
    per = {}
    for th in thetas:
        t = th % M
        if t == 0:
            g = M
        else:
            g = math.gcd(t, M)  # #cycles of the rotation by t on Z/M
        per[th] = g
        total_orbits += g
    return total_orbits, per


def wall_data_dependence(N, samples=300, seed=3):
    """SKEPTIC test: for the genuine adder x+y at width N, are the carry-wall hit positions
    (bits where carry==1) FIXED or DATA-DEPENDENT? Sample operand pairs, collect the set of
    carry-active bit positions per pair; report how many DISTINCT wall-sets occur. A real
    billiard => 1 fixed table. Many distinct sets => walls move with the data."""
    rng = random.Random(seed)
    m = (1 << N) - 1
    wallsets = set()
    for _ in range(samples):
        x = rng.randint(0, m)
        y = rng.randint(0, m)
        c = ad.add_carry_trace(x, y, N)
        # 'wall hit' at bit i <=> a carry is generated out of bit i (c[i+1]==1)
        ws = tuple(i for i in range(N) if c[i + 1] == 1)
        wallsets.add(ws)
    return len(wallsets)


def main():
    print("=" * 78)
    print("W3-IE4  Modular add as a billiard; collisions as closed orbits")
    print("=" * 78)

    # (1) count billiard (rotation) periodic orbits; fit growth
    print("\n[1] Carry-billiard periodic-orbit count (rotations by SHA constants on Z/2^N):")
    Ns = list(range(4, 11))
    norb = []
    for N in Ns:
        tot, per = billiard_orbits(N, ROTS)
        norb.append(tot)
        print(f"    N={N:2d}: total #periodic orbits = {tot:4d}  (per-angle gcd(theta,2^N): "
              f"{ {k:per[k] for k in (2,13,7,17)} })")
    Na = np.array(Ns, float)
    y = np.log2(np.array(norb, float))
    slope = float(np.linalg.lstsq(np.vstack([Na, np.ones_like(Na)]).T, y, rcond=None)[0][0])
    print(f"    fit log2(#orbits)/N = {slope:.4f}   (vs real slope 0.673; vs claimed 0.74)")
    near_074 = abs(slope - 0.74) < 0.07
    near_0673 = abs(slope - 0.673) < 0.07
    print(f"    near 0.74? {near_074}   near 0.673? {near_0673}")

    # (2) KILL TEST: divergence of orbit-count vs collision-count
    print("\n[2] KILL TEST -- do orbit-count and collision-count DIVERGE with N?")
    cNs = [N for N in Ns if N in COLL]
    oc = [billiard_orbits(N, ROTS)[0] for N in cNs]
    cc = [COLL[N] for N in cNs]
    print(f"    N           : {cNs}")
    print(f"    #orbits     : {oc}")
    print(f"    #collisions : {cc}")
    corr = float(np.corrcoef(np.log2(oc), np.log2(cc))[0, 1])
    print(f"    corr(log #orbits, log #collisions) = {corr:.3f}")
    # the decisive N=9->10 feature: collisions DROP (14263->1467). does orbit-count drop?
    i9, i10 = cNs.index(9), cNs.index(10)
    coll_drops = cc[i10] < cc[i9]
    orb_drops = oc[i10] < oc[i9]
    print(f"    N=9->10: collisions {cc[i9]}->{cc[i10]} (drop={coll_drops}); "
          f"orbits {oc[i9]}->{oc[i10]} (drop={orb_drops})")
    diverge = (corr < 0.5) or (coll_drops != orb_drops)
    print(f"    => orbit-count and collision-count DIVERGE: {diverge}")
    print(f"       (collisions are non-monotone w/ a spike@9 trough@10; a rotation orbit")
    print(f"        count is smooth/monotone-ish in N -> they cannot track each other.)")

    # (3) SKEPTIC: are the billiard 'walls' data-dependent? (not a real billiard if so)
    print("\n[3] SKEPTIC TEST -- carry 'walls' FIXED (real billiard) or DATA-DEPENDENT?")
    for N in (6, 8, 10):
        nws = wall_data_dependence(N)
        print(f"    N={N:2d}: #distinct carry-wall sets over 300 operand pairs = {nws}  "
              f"(real billiard would be 1 fixed table)")
    nws10 = wall_data_dependence(10)
    walls_move = nws10 > 5

    # ---- VERDICT ----
    print("\n" + "=" * 78)
    print(f"  orbit-growth slope = {slope:.3f}  (matches neither 0.74 nor 0.673 cleanly: "
          f"{not (near_074 or near_0673)})")
    print(f"  orbit-count vs collision-count DIVERGE with N: {diverge}  (corr={corr:.2f}, "
          f"N=9->10 drop mismatch: {coll_drops != orb_drops})")
    print(f"  carry 'walls' are DATA-DEPENDENT (not a fixed billiard table): {walls_move}")
    # KILL = 'orbit count and collision count diverge with N'
    KILL = diverge
    print(f"\n  KILL_CRITERION ('orbit count and collision count diverge with N') fires? "
          f"{'YES' if KILL else 'NO'}")
    print("  Reading: the carry 'billiard' is a rotation whose periodic-orbit count is")
    print("  smooth/gcd-regular in N and does NOT track the non-monotone collision count")
    print("  (it cannot reproduce the N=9 spike / N=10 trough). Worse, the carry walls")
    print("  move with the operands (not a fixed table) -- exactly the card's own skeptic.")
    print("  The growth slope matches neither 0.74 nor 0.673. Not a billiard.")
    print("=" * 78)


if __name__ == '__main__':
    main()
