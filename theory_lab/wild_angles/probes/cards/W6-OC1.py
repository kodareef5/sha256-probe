#!/usr/bin/env python3
"""
W6-OC1 — The wall is a singular arc -> dH/du dies at round 61.

Card claim: the cascade is bang-bang for r<=60; at r=61 the control isn't free so the
switching function s_61 = lam_{62}^T (dF/du) collapses on the feasible cone -> a singular
arc -> no unique steering.
Probe: N=8,10 compute s_r = lam_{r+1}^T (dF_r/du_r) for r=57..63; is ||s_r|| full-width
for r<=60 and ~0 at 61?
Kill: ||s_61|| same order as ||s_60|| (no collapse).

ADVERSARIAL FRAMING (prior finding #4): the round map sha_round is IDENTICAL at every r.
So dF_r/du_r (the control column, treating W[r] as a free word) is the SAME map at every
round; the only thing special at 61 is that the *schedule* stops granting a free word.
We therefore separate two notions and report both:
  (A) the INTRINSIC switching function s_r = lam_{r+1}^T B_r^free  (W[r] free, the round's
      own dH/du). If THIS stays full-width at 61, the "singular arc" is a schedule
      bookkeeping artifact, NOT a property of the control Hamiltonian.
  (B) the SCHEDULE-feasible projection: the catalog says "project dF_61/du onto the
      schedule-feasible dW[61]". The feasible free-control cone has dim 0 at r>=61, so
      that projection is trivially 0 -- but only because W[61] is a pinned variable,
      which is the known message-schedule fact, not a collapse of the round.

We measure s_r two ways: (i) GF(2) rank of the switching map, (ii) a scalar magnitude
||s_r|| = number of (output-direction, control-bit) pairs that respond (a Boolean
Frobenius norm) so "full-width vs ~0" is literal.

Reuses _w6oc_engine (exact-carry N-bit tail + finite-diff Jacobians + backward costate).
"""
import sys
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards')
import _w6oc_engine as oc

ROUNDS = oc.ROUNDS


def switch_magnitudes(N, w=(0, 0, 0, 0)):
    """Return per-round (rank s_r, Boolean-Frobenius ||s_r||, sched DOF) for the
    INTRINSIC switching map (W[r] free) and the count of feasible control DOF."""
    D = oc.costate_sweep(N, *w)
    out = {}
    for r in ROUNDS:
        Brows = D['Brows'][r]                    # 8N x N  free-control column
        Lnext = D['Lam'][r + 1]                  # 8N x 8N costate basis at r+1
        Bcols = oc.transpose(Brows, N)           # N columns, each an 8N out-mask
        # switching map s_r: column j (control bit j) pulled back through costate.
        s_cols = [oc.matT_vec_rowmask(Lnext, Bcols[j]) for j in range(N)]
        rk = oc.rank(s_cols)
        fro = sum(bin(c).count('1') for c in s_cols)   # Boolean Frobenius norm
        out[r] = (rk, fro, oc.feasible_dofs(r))
    return out, D['n']


def main():
    print("W6-OC1 : switching function s_r = lam_{r+1}^T (dF_r/du_r) along the cascade")
    print("         (intrinsic = treat W[r] as a free word; round map identical each r)\n")
    for N in (8, 10):
        mags, n = switch_magnitudes(N)
        print(f"=== N={N}  ({n}-dim state) ===")
        print(f"  round | rank s_r | ||s_r||_F (Boolean) | schedule free-DOF")
        for r in ROUNDS:
            rk, fro, dof = mags[r]
            tag = "  <- '61'" if r == 61 else ""
            print(f"  {r:5d} | {rk:8d} | {fro:18d} | {dof:17d}{tag}")
        s60 = mags[60]; s61 = mags[61]
        ratio_rank = s61[0] / s60[0] if s60[0] else float('nan')
        ratio_fro = s61[1] / s60[1] if s60[1] else float('nan')
        print(f"  --> s_61 / s_60 : rank ratio = {ratio_rank:.3f}, "
              f"||.||_F ratio = {ratio_fro:.3f}")
        collapse = (s61[0] == 0) or (s60[0] and s61[0] <= 0.25 * s60[0])
        print(f"  --> intrinsic switching collapse at 61? {collapse}  "
              f"(kill fires iff NO collapse, i.e. s_61 ~ s_60)\n")
    print("INTERPRETATION: if rank/||.|| of s_61 equals s_60 (ratio ~1), the round's own")
    print("dH/du does NOT die at 61; only the schedule free-DOF drops 1->0 (bookkeeping).")


if __name__ == '__main__':
    main()
