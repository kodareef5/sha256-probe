#!/usr/bin/env python3
"""
W2-CT2 — Controllability-rank collapse pins "round 60"?

Card claim: track rank of the round-by-round reachability matrix R_t; the round r* where the
target (delta-H=0) can no longer be covered by Im R_t is the cascade death, and it should land
near 60/64 and MOVE when a rotation constant is swapped (ROR7 -> ROR8).

PROBE (per card): N=8..12. rank(R_t) vs round t. Locate r* where target not in Im R_t.
Kicker: swap a rotation constant and check r* moves.

ADVERSARIAL FOCUS (lead finding #3): the "round-60 knee" keeps failing — control/rigidity
dimension decays SMOOTHLY with no 60->61 discontinuity. So the load-bearing output here is the
actual per-round rank curve and whether there is a genuine *collapse* (sharp drop) vs smooth
saturation. We compute the discrete first/second differences of rank(t) and look for a knee.

Method (GF(2), XOR-linearized round operators from kernels/linround.py — carries dropped, which
is the standard differential linearization the card asks for):
  - A = one linearized round map on the 8N difference state (8N x 8N over GF(2)).
  - B = input directions: the message-word difference enters register a (and via schedule, but
    in the per-round LTV picture the controllable input each round is the dW injected into 'a').
    We take B = the 'a'-block injection (N columns) — one fresh schedule-diff lever per round.
  - Reachability after t rounds: R_t = [B, A B, A^2 B, ..., A^{t-1} B]  (column span).
    rank(R_t) over GF(2) = dimension of reachable difference subspace.
  - Target = delta-H = 0 is the origin; "sr=k reachable" in the card's reading is whether the
    *output functional* delta-H lies in the reachable image. Since 0 is always reachable trivially,
    the meaningful quantity the card intends is the reachable DIMENSION saturating: r* is where
    rank stops growing (saturation) — the round after which no new directions become controllable.
    We report the full rank(t) curve, its saturation round, and test for a sharp collapse.

Throttled via OMP_NUM_THREADS=2 taskpolicy -b. N small (8,10,12).
"""
import sys
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
import linround as lr

def reach_rank_curve(N, rots=None, n_rounds=64, include_ch_maj=True):
    """rank(R_t) for t=1..n_rounds where R_t = [B, AB, ..., A^{t-1}B], A = linearized round.
    B = injection into register 'a' (N columns of the 8N-dim state) — the per-round dW lever."""
    dim = 8 * N
    A = lr.round_matrix(N, rots=rots, include_ch_maj=include_ch_maj)  # 8N x 8N row-bitmasks
    # B columns: unit vectors in the 'a' block (offset 0..N-1). Represent each column as a
    # state-vector bitmask (bit = global state index). Column k = e_{off(a)*N + k} = e_k.
    cols = [1 << (lr.OFF['a'] * N + k) for k in range(N)]   # current A^j B columns (as state vecs)
    accum = list(cols)                                       # all columns gathered so far
    ranks = []
    Acur = cols
    for t in range(1, n_rounds + 1):
        rank = sb.gf2_rank(accum, dim)
        ranks.append(rank)
        # advance: A^{t} B = A * (A^{t-1} B). Apply A (rows = output bit i <- XOR of input bits)
        # to each column vector. col is a state vector (bit set = that state coord). A maps
        # state -> state: (A v)[i] = XOR_{j in row_i} v[j]. row i set bit j means out_i gets in_j.
        Anext = []
        for v in Acur:
            w = 0
            for i in range(dim):
                if bin(A[i] & v).count('1') & 1:
                    w |= (1 << i)
            Anext.append(w)
        Acur = Anext
        accum = accum + Anext
    return ranks

def knee_report(ranks, label):
    dim_full = ranks[-1]
    # first differences (new dims gained per round)
    d1 = [ranks[0]] + [ranks[i] - ranks[i-1] for i in range(1, len(ranks))]
    # saturation round = first t at which rank reaches its final value
    final = ranks[-1]
    sat = next((t+1 for t, r in enumerate(ranks) if r == final), len(ranks))
    print(f"\n[{label}] full reachable dim (saturated) = {final}")
    print(f"  saturation round r* (rank stops growing) = {sat}")
    print(f"  rank curve (rounds 1..64): {ranks}")
    print(f"  per-round gain d1        : {d1}")
    # check for a SHARP collapse: is there a single round where gain drops by a lot, or is it smooth?
    # look at rounds 55..64 specifically (the alleged 60 knee region)
    win = list(range(54, min(64, len(ranks))))  # 0-indexed rounds 55..64
    print(f"  rounds 55..64 ranks      : {[ranks[i] for i in win]}")
    print(f"  rounds 55..64 gains      : {[d1[i] for i in win]}")
    # quantify smoothness: max single-round gain after rank>half, vs std
    return sat, final

def main():
    print("=" * 70)
    print("W2-CT2: reachability rank(t) curve — collapse at 60 or smooth saturation?")
    print("=" * 70)
    for N in (8, 10, 12):
        ranks = reach_rank_curve(N, rots=None, n_rounds=64, include_ch_maj=True)
        sat, final = knee_report(ranks, f"N={N}, SHA rotations")
        print(f"  ==> N={N}: r*/64 = {sat}/64 = {sat/64:.3f}  (card predicts r* ~ 60)")

    # KICKER: swap a rotation constant (Sigma0 uses (2,13,22); perturb first amount 2->3, a
    # 'large' perturbation at small N). Does r* move? Card kill: r* insensitive => dead.
    print("\n" + "=" * 70)
    print("KICKER — rotation-constant swap (Sigma0 2->3, 13->14): does r* move?")
    print("=" * 70)
    N = 12
    r = lr.scaled_rots(N)
    base_rots = (r['S0'], r['S1'])
    # perturbed Sigma0
    S0p = (max(1, r['S0'][0] + 1), r['S0'][1], r['S0'][2])
    pert_rots = (S0p, r['S1'])
    ranks_base = reach_rank_curve(N, rots=base_rots, n_rounds=64, include_ch_maj=True)
    ranks_pert = reach_rank_curve(N, rots=pert_rots, n_rounds=64, include_ch_maj=True)
    sat_b, _ = knee_report(ranks_base, f"N={N} baseline Sigma0={r['S0']}")
    sat_p, _ = knee_report(ranks_pert, f"N={N} perturbed Sigma0={S0p}")
    print(f"\n  r* baseline = {sat_b}, r* perturbed = {sat_p}  ->  moved by {sat_p - sat_b}")

    print("\n" + "=" * 70)
    print("KILL CRITERION: dead if rank monotone-saturates (no collapse) OR r* insensitive to")
    print("large rotation perturbation.")
    print("=" * 70)

if __name__ == '__main__':
    main()
