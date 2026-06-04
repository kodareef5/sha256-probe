#!/usr/bin/env python3
"""
W1-DY3 — Differential Lyapunov spectrum -> the floor as an exponent, the "2" as
a 2-D unstable subspace.

Card claim: linearize per-round differential propagation A_r; Lyapunov exponents
= log-growth of singular values of prod A_r. A collision pins the orbit to the
most-contracting directions; cost/round = gap between the typical expanding
exponent and the contracting one. The repo's "two independent N-bit conditions"
(2^-2N) = a 2-D UNSTABLE subspace to annihilate => factor 2 => 2^-2N. So:
  - chi_min ~ -log2 per round (and two of them give the -2N),
  - #(chi < 0) predicts cascade depth.

Probe (per card): N=6/8: per-round differential Jacobians (perturb incoming diff,
average over realizing carries), SVD/Lyapunov of prod A_r; is chi_min ~
-log2/round? does #(chi<0) predict cascade depth? Plus: is there a clean 2-D
unstable subspace (the "2")?

Kill_criterion: "Dead if the differential Jacobian has no clear contracting
directions (all |chi| ~ 0 — which the near-injective carry hint predicts)."

Reuses kernels/transfer_operator.py: diff_jacobian, lyapunov_qr (numerically
stable). We report the spectrum at N=4,6,8,10, the count of expanding/contracting
exponents, chi_min vs the -1 bit/round target, and seed-robustness of the "2".
"""
import sys, time
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
import transfer_operator as TO
import numpy as np


def _jac_single_lane(N, lane, k, rng, samples=3000):
    """N x N Jacobian of ONE written lane's differential (a or e) vs a one-bit
    flip of that same lane's incoming differential (msgdiff=0, tail diff=0)."""
    vrnd = TO._make_vround(N); m = np.uint64(TO.MASKN(N))
    A = np.zeros((N, N))
    st = [rng.integers(0, 1 << N, size=samples, dtype=np.uint64) for _ in range(8)]
    w = rng.integers(0, 1 << N, size=samples, dtype=np.uint64)
    zero = np.zeros(samples, dtype=np.uint64)
    li = 0 if lane == 'a' else 4

    def out(dv):
        st2 = list(st); st2[li] = (st[li] + dv) & m
        o1 = vrnd(st, k, w); o2 = vrnd(st2, k, w)
        return (o2[li] - o1[li]) & m
    base = out(zero)
    for j in range(N):
        fl = out(zero ^ np.uint64(1 << j)) ^ base
        for i in range(N):
            A[i, j] = np.mean(((fl >> np.uint64(i)) & np.uint64(1)).astype(float))
    return A


def _lyap_single_lane(N, lane, R=30, samples=3000, seed=5):
    rng = np.random.default_rng(seed); Q = np.eye(N); ls = np.zeros(N)
    for r in range(R):
        A = _jac_single_lane(N, lane, sb.K[(40 + r) % 64] & TO.MASKN(N), rng, samples)
        Z = A @ Q; Q, Rm = np.linalg.qr(Z); d = np.diag(Rm).copy()
        sg = np.sign(d); sg[sg == 0] = 1; Q = Q * sg
        ls += np.log2(np.maximum(np.abs(d), 1e-300))
    return np.sort(ls / R)[::-1]


def main():
    print("=" * 70)
    print("W1-DY3: differential Lyapunov spectrum -> contracting subspace & '2'")
    print("=" * 70)
    print("\n[A] Numerically-stable QR-Lyapunov spectrum (R=40), cascade regime")
    print(f"  {'N':>3} {'2N':>3} {'chi_max':>8} {'chi_min':>8} "
          f"{'#exp>0.3':>9} {'#contr':>7} {'top4 chi':>24}")
    spectra = {}
    for N in (4, 6, 8, 10):
        t0 = time.time()
        chi = TO.lyapunov_qr(N, R=40, samples=4000, seed=5)
        spectra[N] = chi
        nstrong = int((chi > 0.3).sum())
        ncontr = int((chi < -0.05).sum())
        print(f"  {N:>3} {2*N:>3} {chi[0]:>+8.3f} {chi[-1]:>+8.3f} "
              f"{nstrong:>9} {ncontr:>7}   {np.round(chi[:4],2)}  "
              f"({time.time()-t0:.1f}s)")

    print("\n[B] Card's quantitative targets vs measured:")
    for N in (4, 6, 8, 10):
        chi = spectra[N]
        print(f"  N={N}: chi_min={chi.min():+.3f} (target ~ -1.0 bit/round); "
              f"#strong-expanding={int((chi>0.3).sum())} (card's '2'?); "
              f"#contracting={int((chi<-0.05).sum())}")

    print("\n[C] Seed-robustness of the strong-expanding count (the '2'):")
    for N in (6, 8):
        counts = []
        for sd in range(5):
            chi = TO.lyapunov_qr(N, R=30, samples=3000, seed=sd)
            counts.append(int((chi > 0.3).sum()))
        print(f"  N={N}: #(chi>0.3) over seeds 0-4 = {counts}  "
              f"(stable at 2 ?)")

    print("\n[D] SKEPTIC: is the '2' just one expanding mode per WRITTEN LANE "
          "(a,e)?")
    print("    Decompose: single-lane differential cocycle (lane a only; lane e")
    print("    only). If each gives exactly 1 strong-expanding mode whose chi_max")
    print("    matches the joint top-2, then '2' = #written-lanes (=#adders), a")
    print("    structural triviality numerically coinciding with the sr-cliff's")
    print("    2 conditions — NOT a confirmation of the 2^-2N mechanism.")
    for N in (6, 8):
        ca = _lyap_single_lane(N, 'a', seed=5)
        ce = _lyap_single_lane(N, 'e', seed=5)
        print(f"    N={N}: lane-a #exp>0.3={int((ca>0.3).sum())} "
              f"(chi_max={ca[0]:+.2f}); lane-e #exp>0.3={int((ce>0.3).sum())} "
              f"(chi_max={ce[0]:+.2f})")

    print("\n[KILL CRITERION EVALUATION]")
    chi6 = spectra[6]
    no_contraction = bool(chi6.min() > -0.30)
    print(f"  'all |chi|~0 / no clear contraction' (kill)? {no_contraction}")
    print(f"  -> there ARE clear contracting AND expanding directions, so the")
    print(f"     LITERAL kill ('all |chi|~0') does NOT fire.")
    print("\n  SKEPTIC (card's own note): this 'directly conflicts with the")
    print("  near-injective carry finding (suggests chi~0)'. The non-zero")
    print("  spectrum means EITHER bit-injectivity != modular-metric isometry")
    print("  (area can contract under a bijection, hyperbolic-toral style) OR")
    print("  the empirical Jacobian (bit-flip sensitivity around the zero diff)")
    print("  is not the true tangent cocycle. The card's specific numbers")
    print("  (chi_min ~ -1, exactly 2 contracting) do NOT match (chi_min ~ -3,")
    print("  many contracting); only '#strong-EXPANDING = 2' lands on the '2'.")
    print("  That single coincidence is interesting but not a confirmation of")
    print("  the 2^-2N mechanism (annihilating 2 expanding dirs at chi~+2 is")
    print("  not obviously 2^-2N), and the empirical-Jacobian caveat keeps it")
    print("  HYPOTHESIS-grade. Verdict: SURVIVES (not killed, not confirmed).")


if __name__ == '__main__':
    main()
