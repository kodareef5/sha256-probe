#!/usr/bin/env python3
"""
W3-LL4 — Schedule taps as a covering design -> collision peaks at design-resonant N.

Card: read lags {2,7,15,16} as a design block; its difference multiset Δ tiles Z_N;
GAPS in coverage (high non-uniformity) = surviving free directions = collision-rich
N (claim: N=10 is a coverage gap). The 132 ≈ rotation fixed-point count.

Probe (honoring the card):
  * Δ mod N coverage-uniformity score U(N) for N=4..16
  * correlate U(N) with the collision-count RESIDUAL (after the 0.74N trend)
  * does N=10 align with a coverage gap?
  * rotation fixed-points ≈ 132?
  * predict N=18,20 out-of-sample.

Kill: |r| < 0.3, OR fixed-points nowhere near 132.

SUSPECT per lead #4: PH5 showed N=10 is a yield TROUGH (N=9=14263 >> N=10=1467);
the real structure is N-mod-4 oscillation, not an N=10 resonance. CT3 found no
N=10 pole resonance. The "132 ≈ rotation fixed-points" is likely the 132-corank
category error (lead #1).
"""
import sys, math
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb

TAPS = (2, 7, 15, 16)   # schedule lags (word-index taps)

# --- measured collision yields (writeups/paper_figures_data.md Fig 2, best kernel) ---
YIELD = {4: 146, 5: 1024, 6: 83, 7: 373, 8: 1644, 9: 14263, 10: 1467,
         11: 2720, 12: 4900}   # log2 used below

def diff_multiset_mod(N, lags=TAPS):
    """Δ = all pairwise differences of the lags, reduced mod N (a covering design's
    difference multiset). Returns the multiset (list) of residues hit."""
    diffs = []
    for i in range(len(lags)):
        for j in range(len(lags)):
            if i != j:
                diffs.append((lags[i] - lags[j]) % N)
    return diffs

def coverage_uniformity(N, lags=TAPS):
    """U(N): how UNEVENLY Δ covers Z_N. We score the non-uniformity (the card says
    high non-uniformity = coverage gaps = collision-rich). Use the normalized
    L2 deviation of the residue histogram from flat, AND the # of uncovered residues."""
    diffs = diff_multiset_mod(N, lags)
    hist = [0] * N
    for d in diffs:
        hist[d] += 1
    total = len(diffs)
    mean = total / N
    # L2 non-uniformity (chi-square-like), normalized
    var = sum((h - mean) ** 2 for h in hist) / N
    nonunif = math.sqrt(var) / mean if mean else 0.0
    uncovered = sum(1 for h in hist if h == 0)
    frac_uncovered = uncovered / N
    return dict(nonunif=nonunif, uncovered=uncovered, frac_uncovered=frac_uncovered,
                hist=hist)

def rotation_fixed_points(N):
    """The card claims 132 ≈ 'rotation fixed-point count'. Compute fixed points of
    the schedule's rotation maps. SHA Σ/σ use rotation amounts; a rotation by r on
    an N-bit word fixes a bit-pattern iff it's periodic with period gcd(r,N).
    # fixed words under ROR_r = 2^gcd(r,N). Sum/compose over the 6 rotation amounts
    used by Σ0,Σ1 (the diffusion maps), at the literal 32-bit width (where 132 lives)."""
    # literal 32-bit rotation amounts in Σ0={2,13,22}, Σ1={6,11,25}, σ0={7,18,(3 shr)}, σ1={17,19,(10 shr)}
    rots = [2, 13, 22, 6, 11, 25, 7, 18, 17, 19]
    fps = {}
    for r in rots:
        g = math.gcd(r, N)
        fps[r] = 2 ** g     # # N-bit words fixed by ROR_r
    # several candidate "fixed-point counts" the card could mean:
    total_distinct_bits = None
    # (a) sum of log2(fixed) = sum of gcd(r,N) (a bit-count)
    sum_gcd = sum(math.gcd(r, N) for r in rots)
    # (b) Σ0 alone fixed-space dim = bits fixed by ALL of Σ0's rotations simultaneously
    return dict(sum_gcd=sum_gcd, fps_per_rot={r: math.gcd(r, N) for r in rots})

def pearson(xs, ys):
    n = len(xs)
    mx = sum(xs) / n; my = sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    return sxy / math.sqrt(sxx * syy) if sxx and syy else 0.0

def main():
    print("===== W3-LL4 schedule taps as covering design =====")
    Ns = sorted(YIELD)
    print(f"{'N':>3} {'log2 yield':>10} {'Nmod4':>5} {'U(nonunif)':>10} {'frac_uncov':>10} "
          f"{'Δ-hist':>20}")
    rows = {}
    for N in Ns:
        cov = coverage_uniformity(N)
        logy = math.log2(YIELD[N])
        rows[N] = (logy, cov['nonunif'], cov['frac_uncovered'], N % 4)
        print(f"{N:>3} {logy:>10.2f} {N%4:>5} {cov['nonunif']:>10.3f} {cov['frac_uncovered']:>10.3f} "
              f"{str(cov['hist']):>20}")

    # detrend yield by the documented 0.74 N growth, then correlate residual vs U(N)
    resid = {N: rows[N][0] - sb.GROWTH_EXPONENT * N for N in Ns}
    U = {N: rows[N][1] for N in Ns}
    fu = {N: rows[N][2] for N in Ns}
    r_nonunif = pearson([U[N] for N in Ns], [resid[N] for N in Ns])
    r_uncov = pearson([fu[N] for N in Ns], [resid[N] for N in Ns])
    print(f"\n  residual(N) = log2 yield − 0.74·N :")
    for N in Ns:
        print(f"    N={N}: resid={resid[N]:+.2f}  U={U[N]:.3f}  frac_uncov={fu[N]:.3f}")
    print(f"\n  Pearson r( U_nonunif , residual ) = {r_nonunif:+.3f}")
    print(f"  Pearson r( frac_uncovered , residual ) = {r_uncov:+.3f}")
    kill_corr = (abs(r_nonunif) < 0.3 and abs(r_uncov) < 0.3)

    # N=10 alignment: is it a coverage gap AND a yield peak?
    print(f"\n  N=10 check: U={U[10]:.3f} (rank {sorted(U.values(),reverse=True).index(U[10])+1}/{len(Ns)} most non-uniform), "
          f"yield log2={rows[10][0]:.2f} (rank {sorted([rows[n][0] for n in Ns],reverse=True).index(rows[10][0])+1}/{len(Ns)})")
    print(f"  yield peak is actually at N={max(Ns, key=lambda n: rows[n][0])} "
          f"(N=10 is a {'PEAK' if rows[10][0]==max(rows[n][0] for n in Ns) else 'NON-peak/trough'})")

    # rotation fixed-points vs 132
    print(f"\n  rotation fixed-point counts (the '≈132' claim):")
    for N in (8, 10, 12, 32):
        fp = rotation_fixed_points(N)
        print(f"    N={N}: sum_gcd(r,N)={fp['sum_gcd']}  (2^that overflows; the card wants ~132)")
    fp32 = rotation_fixed_points(32)['sum_gcd']
    near132 = abs(fp32 - 132) <= 20
    print(f"  sum_gcd @N=32 = {fp32}  -> within 20 of 132? {near132}")

    # out-of-sample prediction at N=18,20 (card says predict resonant N)
    print(f"\n  out-of-sample U(N) for the predicted N=18,20 (vs the N=9 in-sample peak):")
    for N in (9, 18, 20):
        cov = coverage_uniformity(N)
        print(f"    N={N}: U_nonunif={cov['nonunif']:.3f}  frac_uncov={cov['frac_uncovered']:.3f}")

    print(f"\n  KILL: |r|<0.3 on BOTH scores? {kill_corr}   fixed-points NOT near 132? {not near132}")
    fired = kill_corr or (not near132)
    print(f"  kill_criterion FIRED? {fired}")
    return r_nonunif, r_uncov, near132, fired

if __name__ == '__main__':
    main()
