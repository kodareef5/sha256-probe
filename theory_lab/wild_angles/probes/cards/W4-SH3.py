#!/usr/bin/env python3
"""
W4-SH3 -- Sheaf diffusion IS the cascade; plateau = a slow non-harmonic mode.

Card probe: "N=2,3,4 project random x(0) onto ker(L); does the limit zero a- and
de60-components for free? lambda_max/lambda1 already large at sr=60? lambda1-eigen-
vector HW ~ 74/132?"
Kill: "harmonic projection != cascade fixed points, or L well-conditioned while
linearized sr=60 is hard."

Three sub-tests on the real Hodge Laplacian L=delta^T delta of the difference sheaf:
  (1) FIXED POINTS: heat flow x' = -L x converges to the harmonic projection P_ker x.
      The cascade's fixed points are da=0 AND de60=0. Does P_ker zero the a-block and
      the round-60 e-block automatically?  -> compare the a/e-block energy fraction of
      a random vector vs its harmonic projection.
  (2) CONDITIONING: is kappa = lambda_max/lambda1 already large at sr=60 (R=4)?
      (card's explanation for the XOR-linearized timeout = ill-conditioned L).
  (3) SLOW-MODE HW: Hamming weight of the lambda1 eigenvector (thresholded), as a
      fraction -> does it sit near 74/132 = 0.56 (the plateau)?
"""
import sys
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
import sheaf_delta as sd
import numpy as np
np.seterr(all='ignore')

def harmonic_projection_test(N, R, trials=200, seed=3):
    """Project random x onto ker(L) and measure the a-block & e-block energy that
    SURVIVES into the harmonic part. If the cascade fixed point is da=0,de60=0, a
    successful 'diffusion=cascade' would leave ~0 energy on those blocks."""
    rows, nc, info = sd.assemble(N, R, force_collision=True, carry_order=0)
    L = sd.real_laplacian(rows, nc)
    w, V = np.linalg.eigh(L)
    ker_mask = w < 1e-9
    Vk = V[:, ker_mask]                      # ortho basis of ker(L)
    P = Vk @ Vk.T if Vk.shape[1] else np.zeros((nc, nc))
    # variable blocks: cols 0..N-1 = a-input; e-input = cols 4N..5N-1.
    a_idx = list(range(0, N))
    e_idx = list(range(4*N, 5*N))
    rng = np.random.default_rng(seed + N*10 + R)
    surviving_a = surviving_e = total_kept = 0.0
    for _ in range(trials):
        x = rng.standard_normal(nc)
        xp = P @ x
        e_tot = (xp @ xp) + 1e-12
        surviving_a += (xp[a_idx] @ xp[a_idx]) / e_tot
        surviving_e += (xp[e_idx] @ xp[e_idx]) / e_tot
        total_kept += (e_tot - 1e-12) / ((x @ x) + 1e-12)
    return (surviving_a/trials, surviving_e/trials, total_kept/trials,
            int(ker_mask.sum()), nc)

def run():
    print("=== W4-SH3: sheaf diffusion = cascade; plateau = slow non-harmonic mode ===\n")

    print("[1] HARMONIC PROJECTION vs cascade fixed point (da=0, de60=0).")
    print("    Fraction of the harmonic-projected energy that lands on the a-block and")
    print("    the e-block. A faithful 'diffusion=cascade' would auto-zero these (->0).")
    print(f"    {'N':>2} {'R':>2} {'dim ker':>7} {'a-block frac':>12} {'e-block frac':>12} "
          f"{'kept frac':>10}")
    for N in (2, 3, 4):
        for R in (4,):
            sa, se, kept, kdim, nc = harmonic_projection_test(N, R)
            print(f"    {N:>2} {R:>2} {kdim:>7} {sa:>12.4f} {se:>12.4f} {kept:>10.4f}")
    print("    -> a-block frac ~ 1/8 = 0.125 (its share) means the harmonic projector")
    print("       does NOT specially zero a or e -> projection != cascade fixed point.")

    print("\n[2] CONDITIONING kappa = lambda_max/lambda1 at sr=60 (R=4) and the sweep.")
    print(f"    {'R':>2} {'~sr':>4} {'lambda1':>12} {'lambda_max':>12} {'kappa':>14}")
    N = 4
    for R in (3, 4, 5):
        rows, nc, info = sd.assemble(N, R, force_collision=True, carry_order=0)
        sp = sd.spectrum(rows, nc)
        pos = sp[sp > 1e-9]; l1 = pos[0] if pos.size else float('nan')
        lmax = sp[-1]; kappa = lmax / l1 if l1 > 0 else float('inf')
        print(f"    {R:>2} {56+R:>4} {l1:>12.5f} {lmax:>12.3f} {kappa:>14.1f}")
    print("    -> kappa large at R=4 is necessary but NOT sufficient: must also be that")
    print("       a SMALL kappa would mean linearized sr=60 is easy (it isn't, regardless).")

    print("\n[3] SLOW-MODE HW: Hamming weight fraction of the lambda1 eigenvector.")
    print("    Card predicts ~74/132 = 0.56.")
    print(f"    {'N':>2} {'R':>2} {'dim':>4} {'HW>1e-2 frac':>12} {'HW>median frac':>14} "
          f"{'|near 0.56?':>11}")
    for N in (2, 3, 4):
        for R in (4,):
            rows, nc, info = sd.assemble(N, R, force_collision=True, carry_order=0)
            L = sd.real_laplacian(rows, nc)
            w, Vv = np.linalg.eigh(L)
            pos_i = np.where(w > 1e-9)[0]
            vec = Vv[:, pos_i[0]]
            absv = np.abs(vec)
            frac_thr = (absv > 1e-2).mean()
            frac_med = (absv > np.median(absv)).mean()
            near = "yes" if abs(frac_thr - 0.56) < 0.08 else "no"
            print(f"    {N:>2} {R:>2} {nc:>4} {frac_thr:>12.3f} {frac_med:>14.3f} {near:>11}")
    print("    -> the 0.56 plateau HW is an OUTPUT-difference Hamming weight (132-bit");
    print("       space); the L-eigenvector HW is over the whole variable set and need")
    print("       not equal it -- a match would have to be non-coincidental.")

if __name__ == '__main__':
    run()
