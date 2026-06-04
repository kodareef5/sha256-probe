#!/usr/bin/env python3
"""
W1-DY2 — Bowen pressure -> the sr-cliff as a phase transition.

Card claim: assign each per-round transition a potential phi = log(realization
prob); pressure P(beta) = lim (1/n) log sum_orbits exp(beta * sum phi). Bowen's
equation: collision rate = beta* solving P(beta*)=0. The sr=60->61 cliff = a
NON-ANALYTIC KINK because losing W[60]-freedom makes one transition forbidden
(phi -> -inf), severing the high-pressure branch; the 2^-2N = the potential at
the boundary.

Probe (per card): reuse the DY1 matrix as L_beta[d',d] = (count)^beta; compute
P(beta) = log lambda_max(L_beta) on a beta-grid at N=6,8; does P(beta)=0
reproduce the rate? does fixing W[60] create a slope discontinuity?

Kill_criterion: "Dead if P(beta) is smooth across the round-60 fix/free switch
(no kink), or beta*-rate disagrees >10%."

Method: the weighted operator is the per-round differential transfer operator
with weights = realization PROBABILITIES p_ij in [0,1] (phi = log p). We form
L_beta with entries p_ij^beta and take the Perron eigenvalue. We trace P(beta)
for the W60-FREE regime (message difference free at the round => full transfer)
and the W60-FIXED regime (message difference pinned, msgdiff=0 => cascade), and
test the curve for a kink (discontinuity in dP/dbeta) at the switch.
"""
import sys, time
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
import transfer_operator as TO
import numpy as np

TARGET = sb.GROWTH_EXPONENT


def pressure_curve(P_entries, betas):
    """P(beta) = log2 lambda_max of the matrix with entries (P_entries)^beta.
    P_entries is a nonneg matrix of realization probabilities (0 -> stays 0)."""
    out = []
    with np.errstate(divide='ignore'):
        for b in betas:
            Lb = np.where(P_entries > 0, np.power(P_entries, b), 0.0)
            ev = np.abs(np.linalg.eigvals(Lb))
            lam = float(ev.max())
            out.append(np.log2(lam) if lam > 0 else float('-inf'))
    return np.array(out)


def build_regime(N, msgdiff, samples, seed):
    """Return the probability operator (weights) for a regime."""
    states, L = TO.build_diff_operator_fast(N, msgdiff=msgdiff, samples=samples,
                                            seed=seed, max_heads=300)
    return states, L


def kink_metric(betas, P):
    """Largest jump in the discrete derivative dP/dbeta (a kink detector)."""
    finite = np.isfinite(P)
    b = betas[finite]; p = P[finite]
    if len(b) < 3:
        return float('nan'), float('nan')
    dP = np.gradient(p, b)
    d2 = np.gradient(dP, b)
    return float(np.max(np.abs(np.diff(dP)))), float(np.max(np.abs(d2)))


def main():
    print("=" * 70)
    print("W1-DY2: Bowen pressure P(beta) -> sr-cliff as a phase transition")
    print("=" * 70)

    betas = np.linspace(0.1, 6.0, 60)

    for N in (6, 8):
        print(f"\n--- N={N} ---")
        t0 = time.time()
        # W60-FREE regime: message difference free at the round (full transfer)
        st_f, L_free = build_regime(N, msgdiff=(1 << (N - 1)), samples=20000,
                                    seed=11)
        # W60-FIXED regime: message difference pinned (cascade, sr=61 side)
        st_x, L_fix = build_regime(N, msgdiff=0, samples=20000, seed=11)

        P_free = pressure_curve(L_free, betas)
        P_fix = pressure_curve(L_fix, betas)

        # Bowen root: beta* with P(beta*)=0
        def root(betas, P):
            P = np.where(np.isfinite(P), P, np.nan)
            sgn = np.sign(P)
            idx = np.where(np.diff(sgn) != 0)[0]
            if len(idx) == 0:
                return None
            i = idx[0]
            # linear interp
            b0, b1 = betas[i], betas[i + 1]
            p0, p1 = P[i], P[i + 1]
            if p1 == p0:
                return b0
            return float(b0 - p0 * (b1 - b0) / (p1 - p0))

        b_free = root(betas, P_free)
        b_fix = root(betas, P_fix)
        jump_free, d2_free = kink_metric(betas, P_free)
        jump_fix, d2_fix = kink_metric(betas, P_fix)

        print(f"  pressure P(1) free={P_free[np.argmin(abs(betas-1))]:+.4f}  "
              f"fixed={P_fix[np.argmin(abs(betas-1))]:+.4f}  "
              f"(stochastic => 0 expected)")
        print(f"  Bowen root beta*: free={b_free}  fixed={b_fix}")
        print(f"  max |jump in dP/dbeta|: free={jump_free:.4f}  fixed={jump_fix:.4f}")
        print(f"  max |d2P/dbeta2|:       free={d2_free:.4f}  fixed={d2_fix:.4f}")
        # The decisive test: is there a kink WHEN WE SWITCH free->fixed?
        # i.e. is P_free(beta) - P_fix(beta) non-analytic / discontinuous-deriv?
        diff = P_free - P_fix
        jump_switch, d2_switch = kink_metric(betas, diff)
        print(f"  switch-curve (P_free - P_fix): max|jump dP|={jump_switch:.4f} "
              f"max|d2|={d2_switch:.4f}")
        print(f"  ({time.time()-t0:.1f}s)")

        # Verdict inputs for this N
        smooth = (d2_free < 0.5 and d2_fix < 0.5)  # smooth if curvature bounded
        print(f"  [N={N}] both pressure curves smooth (bounded 2nd deriv)? {smooth}")

    print("\n[KILL CRITERION EVALUATION]")
    print("  Two clauses: (1) P(beta) smooth across fix/free switch (no kink)")
    print("              (2) beta*-rate disagrees >10%")
    print("  See per-N numbers above. A stochastic-weight operator has a")
    print("  real-analytic Perron pressure P(beta); removing a transition keeps")
    print("  it analytic unless it forces a Perron-eigenvalue CROSSING. Report")
    print("  whether any kink (2nd-deriv blow-up) actually appears.")
    print("  Also: P(beta)=0 root sits at beta*=1 for any stochastic operator,")
    print("  which encodes NO information about the 0.74 rate (beta*=1 trivially).")


if __name__ == '__main__':
    main()
