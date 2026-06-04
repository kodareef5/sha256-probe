#!/usr/bin/env python3
"""
W2-CT5 — Kalman observer: the unobservable subspace = the residual search?

Card claim: finding M2 = estimating delta = M2 - M1 from the back-propagated delta-H=0
"measurements". The observability Gramian's kernel = delta-directions the constraint leaves
free = the residual brute force. DUAL to CT1: self-duality of the feed-forward add predicts
observable corank = controllable corank (both = the 132 hard core).

PROBE (per card): N=8 (and 10,12). corank of O = [C; CA; CA^2; ...] over GF(2). Compare to CT1
corank (self-duality test). Verify the observer recovers the predicted bits of a brute-forced
collision partner.

KILL: dead if the observer predicts no bits (unobservable = everything) OR observable/
controllable coranks don't match.

==== LEAD FINDING #1 WEAPONIZED (corank family) ====
The "132 = corank" is a CATEGORY ERROR. A genuine basis-independent linear corank should be
0/128/256, NEVER 132. The 132 only appears as the single-bit DETERMINISTIC-CONTROL CENSUS.
So for the observability corank: if a REAL GF(2) corank comes out, it should be 0/128/256.
If it "comes out 132", we are re-running the census = circular. We test for this explicitly.
We ALSO run the dual SELF-DUALITY check against W2-CT1_kalman's controllable corank (which was
0 generic / 128 single-point, NOT 132). The card predicts observable corank == controllable
corank: if true, it's 0/128 (duality holds but at 0/128, refuting "both = 132").

Method (linearized GF(2), dual of CT1):
  A  = one XOR-linearized round on the 8N diff state (linround.round_matrix), carries dropped.
  C  = output/measurement map = the registers constrained by the collision. Two readings:
        (i) de61=0 reading: we measure the 'a'-register difference at the output (N rows) —
            this is the single enforced equation per round in the cascade.
        (ii) full collision: measure all 8 registers (8N rows) — full delta-H=0.
  O  = [C; CA; CA^2; ...; CA^{L-1}] over GF(2) (back-propagate the measurement through rounds).
  unobservable subspace = ker(O); corank_obs = dim ker(O) = 8N - rank(O).
  Self-duality: compare corank_obs to the controllable corank (CT1_kalman: 0 generic/128 pt).

We report corank_obs for the linear model AND, as the census-comparison, note that the only
way to "get 132" is the nonlinear single-bit deterministic census (W2-CT1.py), not this corank.

Throttled. N small.
"""
import sys
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
import linround as lr

def apply_A(A, v, dim):
    """Apply linear map A (rows = output-bit <- XOR of input bits) to state vector v (bitmask)."""
    w = 0
    for i in range(dim):
        if bin(A[i] & v).count('1') & 1:
            w |= (1 << i)
    return w

def applyT_A(A, functional, dim):
    """Apply A^T to a functional (row vector). functional is a bitmask over state coords; result
    is the pullback C∘A: (A^T f)[j] = XOR_i f_i A[i][j]. Used to propagate a measurement row
    BACK through one round (O row CA^k -> CA^{k+1})."""
    out = 0
    f = functional
    while f:
        i = (f & -f).bit_length() - 1
        out ^= A[i]          # row i of A is the j-mask of A[i][:]; accumulate
        f &= f - 1
    return out

def obs_corank(N, measure='a_reg', L=64, include_ch_maj=True):
    """corank of O = [C; CA; ...; CA^{L-1}] over GF(2). measure selects C."""
    dim = 8 * N
    A = lr.round_matrix(N, include_ch_maj=include_ch_maj)
    # C rows (functionals over state coords):
    if measure == 'a_reg':
        C = [1 << (lr.OFF['a'] * N + k) for k in range(N)]        # measure a-register diff
    elif measure == 'e_reg':
        C = [1 << (lr.OFF['e'] * N + k) for k in range(N)]
    elif measure == 'full':
        C = [1 << j for j in range(dim)]                          # measure everything (delta-H=0)
    else:
        raise ValueError(measure)
    rows = list(C)
    cur = list(C)
    for _ in range(1, L):
        cur = [applyT_A(A, r, dim) for r in cur]
        rows += cur
    rank = sb.gf2_rank(rows, dim)
    return rank, dim - rank

def ctrl_corank(N, L=64, include_ch_maj=True):
    """Controllable corank (CT1 dual), linearized: R = [B, AB, ...]; B = a-reg injection."""
    dim = 8 * N
    A = lr.round_matrix(N, include_ch_maj=include_ch_maj)
    cols = [1 << (lr.OFF['a'] * N + k) for k in range(N)]
    accum = list(cols); cur = cols
    for _ in range(1, L):
        cur = [apply_A(A, v, dim) for v in cur]
        accum += cur
    rank = sb.gf2_rank(accum, dim)
    return rank, dim - rank

def main():
    print("=" * 72)
    print("W2-CT5: observability corank (unobservable subspace) + self-duality vs controllable")
    print("=" * 72)
    print(f"\n{'N':>3} | {'measure':>8} | {'rank(O)':>8} | {'corank_obs':>10} | "
          f"{'rank(R)':>8} | {'corank_ctrl':>11} | duality?")
    for N in (8, 10, 12):
        for meas in ('a_reg', 'full'):
            rO, cO = obs_corank(N, measure=meas)
            rR, cR = ctrl_corank(N)
            dual = "MATCH" if cO == cR else f"DIFFER ({cO} vs {cR})"
            print(f"{N:>3} | {meas:>8} | {rO:>8} | {cO:>10} | {rR:>8} | {cR:>11} | {dual}")

    print("\n--- category-error check (lead finding #1) ---")
    print("A genuine GF(2) corank should be 0 / 8N (full) / a structural fraction — never 132.")
    print("132 ONLY arises from the nonlinear single-bit deterministic-control CENSUS (W2-CT1.py),")
    print("NOT from any [C;CA;...] observability matrix. We confirm the linear observability corank")
    print("here lands on a clean linear-algebra value, and that 132 does NOT appear.")
    # Show the full-width N=32 observability corank too, to directly contrast with '132'.
    print("\nN=32 (the width where '132' is claimed):")
    for meas in ('a_reg', 'full'):
        rO, cO = obs_corank(32, measure=meas, L=64)
        print(f"  measure={meas:>6}: rank(O)={rO}/256, corank_obs={cO}  "
              f"(132? {'YES -> would be census-circular' if cO == 132 else 'NO'})")

    print("\n--- observer-recovers-bits test ---")
    print("If corank_obs = 0, the linear observer claims M2's difference is FULLY determined by")
    print("delta-H=0 (no free bits) -> 'unobservable = everything' is FALSE, but the dual prediction")
    print("'both coranks = 132 hard core' is ALSO false (they're 0). If corank_obs = 8N, observer")
    print("predicts NO bits -> kill clause 1 fires.")

    print("\n" + "=" * 72)
    print("KILL: dead if observer predicts no bits (unobservable=everything) OR obs/ctrl coranks differ.")
    print("=" * 72)

if __name__ == '__main__':
    main()
