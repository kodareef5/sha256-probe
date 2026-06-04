#!/usr/bin/env python3
"""
W1-PH2 -- RG fixed point -> explains "why round 60".

CARD PROBE: N=8,10,12: XOR-linearize one round on the difference state, form the per-round
transfer matrix, track the still-controllable subspace dimension vs round; look for a knee
near the boundary; permute the rotation constants to confirm the knee moves.
KILL: dead if the controllable dimension decays smoothly (no knee), or if permuting
rotations doesn't move the knee.

GROUND TRUTH: the cascade reaches sr=60 (4 free tail words W[57..60]); sr=61 is the wall.
132 of 256 output bits are "hard core" (uncontrolled). RG reading: control dimension should
DROP sharply at the boundary, and the boundary should be SET by the rotation constants
(so permuting them moves the knee).

OPERATIONALIZATION ("still-controllable subspace dimension vs round"):
  Forward reachability. A free tail message word W[i] (i in the free set) injects an N-dim
  difference into T1 -> into registers a' and e' at round i. Linearly propagate that
  injection forward to the OUTPUT (round 63) through the XOR-linearized round matrix M.
  The controllable subspace seen at the output, using free words from round r onward, is
      R(r) = span{ M^(63-i) . inj(W[i])  :  i = r, r+1, ..., 63 }.
  dim R(r) over 8N is the "controllable dimension" at round r. As r grows (fewer free
  words remain) dim R(r) falls. A KNEE = the round where it falls off a cliff -> the wall.
  We compute the per-round INCREMENT dim R(r) - dim R(r+1) = the marginal control each
  round's free word adds; the boundary is where this increment collapses to ~0 (the
  schedule stops yielding new controllable directions).
  Then PERMUTE the Sigma rotation constants and re-locate the knee; if it moves, the knee
  is rotation-set (the card's prediction); if not, kill.

  NOTE on the "eigenvalue crosses 1" subclaim: we also report the spectral radius of the
  XOR-linearized round matrix over the reals (lifting GF2 entries to {0,1}) -- a knee in
  growth of the reachable dimension is the discrete analogue of a relevant->irrelevant
  crossing. Honest: XOR-linearization drops carries (skeptic flag).
"""
import sys, os
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
import linround as lr

def inj_word(N):
    """An N-dim message-word difference at round i injects into T1 = ...+W, which feeds
    a' = T1+T2 and e' = d+T1. So inj sends unit bit j of W to (a'_j XOR e'_j) one round
    later. Return the N injection vectors as full-8N bitmasks at the POST-round state
    (i.e. as they appear in registers a and e after the injecting round)."""
    cols = []
    for j in range(N):
        v = (1 << (lr.OFF['a']*N + j)) ^ (1 << (lr.OFF['e']*N + j))
        cols.append(v)
    return cols

def reachable_dims(N, rots, free_start=57, last=63):
    """dim R(r) for r = free_start..last using the XOR-linearized round matrix.
    Returns dict r -> dim, plus per-round increments."""
    n = 8*N
    M = lr.round_matrix(N, rots=rots)
    # Precompute M^p applied to each injection. We accumulate columns then rank.
    # For round i, the injection appears in state AFTER round i; to reach output (after
    # round `last`), apply M (last - i) more times.
    inj = inj_word(N)
    # Build, for each i, the propagated columns to the output:
    propagated = {}   # i -> list of 8N-bitmask column vectors at output
    for i in range(free_start, last+1):
        p = last - i
        cols = []
        for v in inj:
            w = v
            for _ in range(p):
                w = apply_mat_vec(M, w, n)
            cols.append(w)
        propagated[i] = cols
    # R(r) = span of propagated[i] for i>=r. Compute dim by accumulating from r=last down.
    dims = {}
    for r in range(last, free_start-1, -1):
        acc = []
        for i in range(r, last+1):
            acc.extend(propagated[i])
        dims[r] = lr.rank_gf2(acc, n)
    return dims

def apply_mat_vec(M_rows, vec, n):
    """Apply GF(2) matrix (rows=bitmasks) to a column vector given as a bitmask.
    result bit i = parity(M_rows[i] & vec)."""
    out = 0
    for i in range(n):
        if bin(M_rows[i] & vec).count('1') & 1:
            out |= (1 << i)
    return out

def find_knee(dims, free_start=57, last=63):
    """Increment per round (going forward 57->63): how much controllable dim is LOST as we
    drop the round-r free word. Knee = largest single-step drop location."""
    seq = [(r, dims[r]) for r in range(free_start, last+1)]
    # increments of dim R(r) as r increases (fewer free words): dim falls
    drops = []
    for k in range(len(seq)-1):
        r0, d0 = seq[k]; r1, d1 = seq[k+1]
        drops.append((r1, d0 - d1))   # dim lost when free word at r0 removed -> at boundary r1
    # also the marginal CONTROL added by each round's word = dimR(r)-dimR(r+1)
    return seq, drops

def main():
    print("="*74)
    print('W1-PH2  RG fixed point -> "why round 60"   (control-dimension knee vs round)')
    print("="*74)

    for N in (8, 10, 12):
        r = lr.scaled_rots(N)
        rots = (r['S0'], r['S1'])
        dims = reachable_dims(N, rots)
        seq, drops = find_knee(dims)
        print(f"\n[N={N}]  scaled Sigma0 rots={r['S0']}  Sigma1 rots={r['S1']}   (state dim 8N={8*N})")
        print("    round r :  dim R(r) [output dirs controllable using free words >= r]")
        for rr, d in seq:
            print(f"      r={rr}:  dim={d}")
        # knee = where marginal control collapses
        print("    marginal control lost when free word at round r removed:")
        knee_r, knee_drop = max(drops, key=lambda t: t[1]) if drops else (None, 0)
        for rb, dd in drops:
            mark = "  <== largest drop (knee)" if (rb==knee_r and knee_drop>0) else ""
            print(f"      removing W[{rb-1}] -> boundary r={rb}: lose {dd} dirs{mark}")

    # ---- PERMUTE rotations: does the knee move? ----
    print("\n" + "-"*74)
    print("PERMUTATION TEST (N=10): permute the Sigma rotation constants, re-locate the knee")
    N = 10
    base = lr.scaled_rots(N)
    variants = {
        'SHA (2,13,22 / 6,11,25)': (base['S0'], base['S1']),
        'swap S0<->S1':            (base['S1'], base['S0']),
        'all-equal (1,1,1)':       ((1,1,1), (1,1,1)),
        'spread (1,N//2,N-1)':     ((1, N//2, N-1), (2, N//3, N-2)),
        'identity-rot (0,0,0)':    ((0,0,0),(0,0,0)),
    }
    knees = {}
    for name, rots in variants.items():
        dims = reachable_dims(N, rots)
        seq, drops = find_knee(dims)
        kr, kd = max(drops, key=lambda t: t[1]) if drops else (None,0)
        full = dims[57]
        knees[name] = (kr, kd, full)
        print(f"  {name:28s}: dimR(57)={full:3d}  knee at boundary r={kr} (drop {kd})")
    knee_positions = set(k[0] for k in knees.values())
    full_dims = set(k[2] for k in knees.values())

    # ---- VERDICT ----
    print("\n" + "="*74)
    # KILL clause 1: control dimension decays SMOOTHLY (no knee).
    # Read the SHA case: is there a dominant single drop (a knee) vs a flat decline?
    N = 10; base = lr.scaled_rots(N)
    dims = reachable_dims(N, (base['S0'], base['S1']))
    _, drops = find_knee(dims)
    drop_vals = sorted([d for _, d in drops], reverse=True)
    has_knee = (len(drop_vals) >= 2 and drop_vals[0] >= 2*max(1, drop_vals[1])) or (drop_vals and drop_vals[0] >= 0.5*max(dims.values()))
    # KILL clause 2: permuting rotations does NOT move the knee (position or full dim).
    knee_moves = (len(knee_positions | full_dims) > 1) and (len(full_dims) > 1 or len(knee_positions) > 1)
    print(f"  SHA(N=10) per-round control drops (sorted): {drop_vals}")
    print(f"  distinct knee positions across rotation variants: {sorted([str(p) for p in knee_positions])}")
    print(f"  distinct dimR(57) across rotation variants:        {sorted(full_dims)}")
    print(f"  KILL clause 1 (no knee / smooth decay) fires?      {not has_knee}")
    print(f"  KILL clause 2 (knee unmoved by rotations) fires?   {not knee_moves}")
    KILL = (not has_knee) or (not knee_moves)
    print(f"\n  KILL_CRITERION fires? {'YES' if KILL else 'NO'}")
    print("="*74)

if __name__ == '__main__':
    main()
