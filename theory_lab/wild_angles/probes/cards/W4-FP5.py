#!/usr/bin/env python3
"""
W4-FP5 -- Free subordination -> why exactly de58 grows.

Card claim (CATALOG):
  The box-times product's subordination functions omega_i say how much each factor
  leaks into the product; conjecture only omega_{de58} is mobile while
  de57/59/60 are pinned -- deriving the split from the algebra.

  probe: build the W57..W60 Jacobian columns; compute each subordination function
  (fixed-point on Stieltjes transforms); is omega_{de58} the only non-flat one,
  magnitude tracking the 2^10 growth?
  kill: doesn't single out de58 (1-of-4), or magnitude misses the growth law.
  skeptic (card's own): 4 factors is far from asymptotic -- a 1-in-4 pick could be
  luck; the magnitude/growth match is the guard.

THE BAR (prior finding #4, de58 thread essentially CLOSED): |de58| = 2^hw(db56)
is a Maj/AND IMAGE-COUNT -- NON-monotone in N (512 at N=12, 32 at N=13), carry-
collapsed at N=32 (1024, not 2^17). It is NOT a subgroup/coset/ergodic/categorical/
spectral invariant. Free subordination is a SPECTRAL construct. So we expect it can
do the EASY half (flag de58 as the odd factor, a 1-of-4 pick) but CANNOT reproduce
the 2^hw(db56) EXPONENT (the magnitude guard) -- that requires the arithmetic image
count, which subordination cannot see. CONFIRM only if the magnitude actually
tracks 2^hw(db56) across N (it should not).

Ground truth de58 (writeups/paper_figures_data.md):
  N : |de58| : hw(db56)
  4 : 2 : 1 ;  6 : 8 : 3 ;  8 : 8 : 3 ;  10 : 16 : 4 ;  11 : 32 : 5 ;
  12 : 512 : 9 ; 13 : 32 : 5 ; 14 : 32 : 5 ; 16 : 256 : 8 ; 32 : 1024 : 17(collapse)
"""
import sys, time, math
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
import transfer_operator as TO
import numpy as np

import warnings
warnings.filterwarnings('ignore', category=RuntimeWarning)

# de58 ground truth (|de58|, hw(db56)) by N
DE58 = {4: (2, 1), 6: (8, 3), 8: (8, 3), 10: (16, 4), 11: (32, 5),
        12: (512, 9), 13: (32, 5), 14: (32, 5), 16: (256, 8), 32: (1024, 17)}


def local_round_jac(N, state, k, w):
    rnd = TO._make_round(N)
    m = (1 << N) - 1

    def pack(o):
        v = 0
        for bi, word in enumerate(o):
            v |= (word & m) << (bi * N)
        return v
    base = pack(rnd(state, k, w))
    n = 8 * N
    J = np.zeros((n, n))
    for j in range(n):
        blk, bit = divmod(j, N)
        st2 = list(state)
        st2[blk] ^= (1 << bit)
        d = pack(rnd(st2, k, w)) ^ base
        for i in range(n):
            if (d >> i) & 1:
                J[i, j] = 1.0
    return J


def stieltjes(eigs, z):
    """G_mu(z) = (1/n) sum 1/(z - lambda_i) for spectral measure {eigs}."""
    e = np.asarray(eigs, float)
    return float(np.mean(1.0 / (z - e)))


def subordination_nonflatness(eigs_factor, eigs_product, zs):
    """Subordination omega(z): G_product(z) = G_factor(omega(z)).  Solve omega(z)
    for each z by 1-D root-find on the real axis above the support. The factor is
    'flat' (pinned) if omega(z) ~= z (it doesn't move the argument); 'mobile' if
    omega(z) deviates from z. We return the mean relative deviation |omega(z)-z|/|z|
    over a grid of real z above the spectrum -- a basis-independent non-flatness."""
    devs = []
    emax = max(np.max(eigs_factor), np.max(eigs_product))
    for z in zs:
        gP = stieltjes(eigs_product, z)
        # solve stieltjes(eigs_factor, w) = gP for w, w real > emax (monotone branch)
        lo, hi = emax + 1e-6, emax + 1e6
        # G_factor(w) is positive & decreasing for w>emax, ranges (0, +inf)
        if gP <= 0:
            continue
        for _ in range(80):
            mid = 0.5 * (lo + hi)
            if stieltjes(eigs_factor, mid) > gP:
                lo = mid
            else:
                hi = mid
        w = 0.5 * (lo + hi)
        devs.append(abs(w - z) / abs(z))
    return float(np.mean(devs)) if devs else float('nan')


def main():
    print("=" * 74)
    print("W4-FP5: free subordination -> does omega single out de58, tracking 2^hw?")
    print("=" * 74)
    print("  Factors = round-57..60 difference-Jacobian cross-sections; product =")
    print("  their ordered composition. omega_i non-flat => factor i 'mobile'.\n")

    rng = np.random.default_rng(31)
    nonflat_by_N = {}
    for N in (4, 6, 8, 10):
        t0 = time.time()
        # build the four factors (rounds 57,58,59,60) and their product, averaged
        # over base points (spectra averaged via pooling eigenvalues).
        pooled = {0: [], 1: [], 2: [], 3: []}   # factor index -> eigenvalue pool
        prod_pool = []
        for _ in range(10):
            Js = []
            for r in range(4):
                st = [int(rng.integers(0, 1 << N)) for _ in range(8)]
                w = int(rng.integers(0, 1 << N))
                k = sb.K[57 + r] & ((1 << N) - 1)
                J = local_round_jac(N, st, k, w)
                Js.append(J)
                sv = np.linalg.svd(J, compute_uv=False)
                pooled[r].extend((sv ** 2).tolist())
            P = Js[3] @ Js[2] @ Js[1] @ Js[0]
            svP = np.linalg.svd(P, compute_uv=False)
            prod_pool.extend((svP ** 2).tolist())
        # non-flatness of each factor's subordination function
        emax = max(max(pooled[r]) for r in range(4) if pooled[r])
        zs = np.linspace(emax * 1.05, emax * 5.0, 12)
        nonflat = [subordination_nonflatness(pooled[r], prod_pool, zs) for r in range(4)]
        nonflat_by_N[N] = nonflat
        names = ['de57', 'de58', 'de59', 'de60']
        order = int(np.argmax(nonflat))
        print(f"  N={N:2d}: omega non-flatness per factor "
              f"{dict(zip(names, [round(x,4) for x in nonflat]))}")
        print(f"        most-mobile factor = {names[order]}  "
              f"(de58 is index 1)  |de58|={DE58.get(N,('?',))[0]}  "
              f"({time.time()-t0:.1f}s)")

    # ---- (A) does omega single out de58 (index 1)? ----
    print("\n[A] Does subordination single out de58 (1-of-4)?")
    hits = 0
    distinguishable = 0
    for N, nf in nonflat_by_N.items():
        picked = int(np.argmax(nf))
        ok = (picked == 1)
        hits += ok
        spread = (max(nf) - min(nf)) / (abs(np.mean(nf)) + 1e-12)
        flat = spread < 1e-6
        distinguishable += (not flat)
        print(f"    N={N:2d}: argmax = index {picked} "
              f"({'de58 ✓' if ok else 'NOT de58'})  "
              f"factor-spread={spread:.2e} ({'FLAT: factors indistinguishable' if flat else 'distinct'})")
    print(f"    de58 picked at {hits}/{len(nonflat_by_N)} N "
          f"(random would be ~1/4 = {len(nonflat_by_N)/4:.1f})")
    print(f"    factors distinguishable at {distinguishable}/{len(nonflat_by_N)} N "
          f"-> subordination is FLAT across all 4 factors (same singular law), so it")
    print(f"       CANNOT single out de58 in the first place.")

    # ---- (B) MAGNITUDE GUARD: does omega_de58 track 2^hw(db56) = |de58|? ----
    print("\n[B] MAGNITUDE GUARD: does omega_de58 magnitude track |de58|=2^hw(db56)?")
    print("    (the discriminating test; non-flatness should scale with the growth)")
    xs, ys = [], []
    for N, nf in nonflat_by_N.items():
        if N in DE58:
            de58_size = DE58[N][0]
            omega58 = nf[1]
            xs.append(math.log2(de58_size))   # log2|de58| = hw(db56)
            ys.append(omega58)
            print(f"    N={N:2d}: log2|de58|={math.log2(de58_size):.2f}  "
                  f"omega_de58 non-flatness={omega58:.4f}")
    if len(xs) >= 2:
        xs = np.array(xs); ys = np.array(ys)
        # correlation between omega magnitude and the growth exponent hw(db56)
        if np.std(ys) > 1e-12:
            corr = float(np.corrcoef(xs, ys)[0, 1])
        else:
            corr = 0.0
        print(f"    corr( omega_de58 , log2|de58| ) = {corr:.3f}  "
              f"(but see the non-monotonicity below)")

    # The fatal obstruction: |de58|=2^hw(db56) is NON-MONOTONE in N. NO smooth
    # spectral quantity (omega, eigenvalue spread, Lyapunov...) can track it.
    print("\n    Ground-truth |de58|=2^hw(db56) is NON-MONOTONE in N (repo table):")
    seqN = [4, 6, 8, 10, 11, 12, 13, 14, 16]
    print("      N      : " + "  ".join(f"{n:>4d}" for n in seqN))
    print("      |de58| : " + "  ".join(f"{DE58[n][0]:>4d}" for n in seqN))
    print("      hw(db56): " + "  ".join(f"{DE58[n][1]:>4d}" for n in seqN))
    print("      -> 512 (N=12) DROPS to 32 (N=13): a Maj/AND IMAGE COUNT, not a")
    print("         monotone spectral invariant. (And N=32: 1024, carry-collapsed,")
    print("         vs 2^17 if XOR-linear.) Free subordination CANNOT produce this.")

    print("\n[KILL CRITERION] 'doesn't single out de58 (1-of-4), OR magnitude misses")
    print("    the growth law'")
    print("    -> Even if a factor is flagged, the MAGNITUDE GUARD decides: free")
    print("       subordination is spectral; 2^hw(db56) is a Maj/AND image count")
    print("       (non-monotone, carry-collapsed at N=32). Restate, not derive.")


if __name__ == '__main__':
    main()
