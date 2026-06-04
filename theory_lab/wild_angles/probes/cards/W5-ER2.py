#!/usr/bin/env python3
"""
W5-ER2 -- Matrix-tree spanning-forest count -> 0.74 as tree-entropy.

Card claim (CATALOG): each collision <-> a unique carry vector; reinterpret admissible carry
assignments as weighted spanning forests of the carry-coupling graph; Kirchhoff counts them as
a Laplacian minor det; log2 det ~ 0.74 N.

probe: N=4,8,10,12 (known counts 49,260,946,~2955); build the carry-coupling Laplacian (edge
weight = local carry-prop probability), slogdet of a minor; slope vs N near 0.74? count tracks
C (r2 > 0.9)?
kill: best-fit slope NOT in [0.70,0.78] for ALL physically-motivated weightings, or r2 < 0.9 on
the 4 points.
skeptic (card's own): carries are nonlinear / not XOR-closed -- a determinant may be the wrong
counting class and hit 0.74 only via a free constant; weights must be fixed A PRIORI from carry
physics, not tuned. (!= eigenvalue list: a det of a Laplacian MINOR / cofactor.)

==========================================================================================
PRIOR FINDING #2 (adversarial bar): 0.74 is NOT sharp. The genuine asymptotic slope is ~0.673,
with per-segment spread 0.72-1.04. The raw 4 known counts happen to least-squares-fit 0.7401
(r2=0.99) only because the noisy per-segment slopes (0.60, 0.93, 0.82) average out. So to CONFIRM
we need the MATRIX-TREE DETERMINANT (a fixed-a-priori carry-physics object) to *independently*
reproduce BOTH the count (r2>0.9 tracking) AND the slope in [0.70,0.78] -- WITHOUT a tuned
constant. A determinant that merely admits 0.74 after fitting one free additive constant is a
rename, not a derivation. We test several a-priori carry-physics weightings and report each
slope, the count-tracking r2, and whether any free constant was needed.
==========================================================================================

THE CARRY-COUPLING GRAPH (physically motivated, fixed a priori):
 The tail collision is governed by the modular-adder carry chains. We build a Laplacian on the
 N carry-lane nodes (bits 0..N-1) of the adder network. Three a-priori weightings of the
 lane->lane (i -> i+1) carry-propagation conductance:
   (W1) "fair carry"   p = 1/2  (a random full-adder propagates an incoming carry w.p. 1/2)
   (W2) "Lipmaa-Moriai-mean": mean per-bit XOR-diff carry-propagation probability over random
        differentials at that lane (measured from adder_diff.lm physics, NOT tuned).
   (W3) "active-lane"  p = measured P(carry-difference != 0 at lane i) over random input pairs
        with a random nonzero input difference (the real carry-diff activity).
 Each gives a weighted path/cycle Laplacian; the Kirchhoff number = det of the (n-1)-minor =
 weighted spanning-tree count. We compare log2(treecount) vs N to the known collision counts.

We also include the carry-coupling MATRIX from linround (the genuine T1/T2 carry adjacency over
the 8N difference state) as a 4th, structure-faithful weighting, and take its Laplacian-minor det.
"""
import sys, random, time
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
import adder_diff as ad
import numpy as np
s = sb.s
np.seterr(all='ignore')

KNOWN_N = [4, 8, 10, 12]
KNOWN_COUNT = [49, 260, 946, 2955]          # from CATALOG W5-ER2 / repo enumerator
KNOWN_LOG2 = [np.log2(c) for c in KNOWN_COUNT]


def path_laplacian(conduct):
    """Weighted PATH graph Laplacian on len(conduct)+1 nodes; conduct[i] = edge (i,i+1)."""
    n = len(conduct) + 1
    Lap = np.zeros((n, n))
    for i, w in enumerate(conduct):
        Lap[i, i] += w; Lap[i + 1, i + 1] += w
        Lap[i, i + 1] -= w; Lap[i + 1, i] -= w
    return Lap


def cycle_laplacian(conduct):
    """Weighted CYCLE graph Laplacian on len(conduct) nodes (carry chain wraps; gives a
    nontrivial spanning-tree count = sum of products, unlike a path whose tree-count is the
    product of all edge weights)."""
    n = len(conduct)
    Lap = np.zeros((n, n))
    for i, w in enumerate(conduct):
        j = (i + 1) % n
        Lap[i, i] += w; Lap[j, j] += w
        Lap[i, j] -= w; Lap[j, i] -= w
    return Lap


def kirchhoff(Lap):
    """Weighted spanning-tree count = any (n-1)x(n-1) cofactor of the Laplacian (delete row/col 0)."""
    M = Lap[1:, 1:]
    sign, logdet = np.linalg.slogdet(M)
    if sign <= 0:
        return None
    return logdet / np.log(2)        # log2 of the tree count


def carry_prop_fair(N):
    """W1: every lane propagates w.p. 1/2."""
    return [0.5] * N


def carry_prop_lm(N, samples=4000, seed=11):
    """W2: a-priori mean Lipmaa-Moriai per-lane carry-prop probability. For random (a,b,g)
    XOR-differentials of an N-bit adder, the probability that lane i is a 'propagate' (eq-fails)
    lane. Fixed from carry physics; no tuning."""
    rng = random.Random(seed + N)
    m = (1 << N) - 1
    cnt = [0] * N
    tot = 0
    for _ in range(samples):
        a = rng.getrandbits(N); b = rng.getrandbits(N)
        g = rng.getrandbits(N)
        if not ad.lm_compatible(a, b, g, N):
            continue
        eq = (~(a ^ b)) & (~(a ^ g)) & m
        prop = (~eq) & m                      # lanes where the carry is NOT pinned (free/propagate)
        for i in range(N):
            cnt[i] += (prop >> i) & 1
        tot += 1
    if tot == 0:
        return [0.5] * N
    return [max(1e-6, cnt[i] / tot) for i in range(N)]


def carry_prop_active(N, samples=4000, seed=23):
    """W3: measured P(carry-difference != 0 at lane i) for random input pairs with a random
    nonzero input difference -- the genuine carry-diff activity per lane (carry physics)."""
    rng = random.Random(seed + N)
    m = (1 << N) - 1
    cnt = [0] * N
    for _ in range(samples):
        x = rng.getrandbits(N); y = rng.getrandbits(N)
        dx = rng.getrandbits(N) or 1; dy = rng.getrandbits(N)
        pat = ad.diff_carry_pattern(x, y, dx & m, dy & m, N)   # list len N of {-1,0,+1}
        for i in range(N):
            if pat[i] != 0:
                cnt[i] += 1
    return [max(1e-6, cnt[i] / samples) for i in range(N)]


def fit_slope(Ns, logvals):
    """log2val ~ slope*N + c. Returns (slope, intercept, r2)."""
    Ns = np.asarray(Ns, float); y = np.asarray(logvals, float)
    A = np.vstack([Ns, np.ones_like(Ns)]).T
    (slope, c), *_ = np.linalg.lstsq(A, y, rcond=None)
    pred = A @ np.array([slope, c])
    ss_res = ((y - pred) ** 2).sum(); ss_tot = ((y - y.mean()) ** 2).sum()
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float('nan')
    return slope, c, r2


def main():
    print("=" * 80)
    print("W5-ER2: matrix-tree (Kirchhoff minor det) of carry-coupling Laplacian -> 0.74 N?")
    print("=" * 80)
    print(f"  Known collision counts: N={KNOWN_N} -> {KNOWN_COUNT} (log2 {[round(v,2) for v in KNOWN_LOG2]})")
    s_raw, c_raw, r2_raw = fit_slope(KNOWN_N, KNOWN_LOG2)
    print(f"  RAW-COUNT reference fit: slope={s_raw:.4f}  r2={r2_raw:.4f}  "
          f"(prior finding #2: true asymptotic ~0.673, this 0.74 is a 4-point coincidence)")
    print(f"  per-segment raw slopes: " +
          ", ".join(f"{KNOWN_N[i]}->{KNOWN_N[i+1]}={(KNOWN_LOG2[i+1]-KNOWN_LOG2[i])/(KNOWN_N[i+1]-KNOWN_N[i]):.3f}"
                    for i in range(len(KNOWN_N)-1)))

    weightings = {
        'W1 fair-1/2 (path)':   ('path',  carry_prop_fair),
        'W1 fair-1/2 (cycle)':  ('cycle', carry_prop_fair),
        'W2 LM-prop  (path)':   ('path',  carry_prop_lm),
        'W2 LM-prop  (cycle)':  ('cycle', carry_prop_lm),
        'W3 active   (path)':   ('path',  carry_prop_active),
        'W3 active   (cycle)':  ('cycle', carry_prop_active),
    }

    summary = []
    for name, (topo, wfn) in weightings.items():
        t0 = time.time()
        logvals = []
        for N in KNOWN_N:
            cond = wfn(N)
            Lap = path_laplacian(cond) if topo == 'path' else cycle_laplacian(cond)
            lt = kirchhoff(Lap)
            logvals.append(lt if lt is not None else float('nan'))
        slope, c, r2 = fit_slope(KNOWN_N, logvals)
        # correlation between det-log2 and the actual collision-count-log2 (count tracking)
        a = np.array(logvals); b = np.array(KNOWN_LOG2)
        if np.all(np.isfinite(a)) and a.std() > 0:
            r_track = np.corrcoef(a, b)[0, 1]
            r2_track = r_track ** 2
        else:
            r2_track = float('nan')
        summary.append((name, slope, r2, r2_track, logvals))
        vals = ", ".join(f"{v:+.2f}" for v in logvals)
        print(f"\n  [{name}]  ({time.time()-t0:.1f}s)")
        print(f"    log2(tree-count) per N: [{vals}]")
        print(f"    slope vs N = {slope:.4f}   self-fit r2={r2:.3f}   "
              f"r2 tracking actual count = {r2_track:.3f}")

    print("\n" + "=" * 80)
    print("DECISION (kill: slope NOT in [0.70,0.78] for ALL weightings, OR r2<0.9 tracking):")
    in_band = [(nm, sl) for nm, sl, _, _, _ in summary if 0.70 <= sl <= 0.78]
    good_track = [(nm, rt) for nm, _, _, rt, _ in summary if rt >= 0.9]
    print(f"  weightings with slope in [0.70,0.78]: {[(nm, round(sl,3)) for nm,sl in in_band] or 'NONE'}")
    print(f"  weightings tracking the count r2>=0.9: {[(nm, round(rt,3)) for nm,rt in good_track] or 'NONE'}")
    # A CONFIRM needs the SAME weighting to be both in-band AND tracking (no tuned constant).
    both = [nm for nm, sl, _, rt, _ in summary if (0.70 <= sl <= 0.78 and rt >= 0.9)]
    print(f"  weightings satisfying BOTH (slope-band AND r2>=0.9), a-priori: {both or 'NONE'}")
    if not both:
        print("  => KILL FIRES: no a-priori carry-physics weighting reproduces both the 0.74")
        print("     slope and the count-tracking. (Any single weighting that hits 0.74 fails to")
        print("     track, or vice versa -> the determinant is the wrong counting class, hitting")
        print("     ~0.74 only via a free constant = a rename, per prior finding #2.)")
    else:
        print(f"  => SURVIVES/CONFIRM candidate: {both} -- skeptic re-check the a-priori weight.")
    print("=" * 80)


if __name__ == '__main__':
    main()
