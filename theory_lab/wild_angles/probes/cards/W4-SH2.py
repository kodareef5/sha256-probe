#!/usr/bin/env python3
"""
W4-SH2 -- dim H^1 = 132 (hard-core bits = gluing obstructions).

Card probe: "N=2,3,4 dim H^1/dim C^0 -> 0.516? extract the H^1-basis support (ker
delta^T) and correlate with hard-core positions."
Kill: "ratio !-> 0.51, or support uncorrelated (rho<0.3)."

CRITICAL (prior-finding #1): a REAL sheaf-cohomology dimension over GF(2) is
#edges - rank(delta) and will land at 0 or 128, NEVER 132. The '132' is ONLY the
single-bit deterministic-control census (W2-CT1), not a coboundary rank-deficiency.
This probe computes the genuine H^1 and its ratio to C^0, and tests the 132/0.516
claim head-on -- adversarially, to catch the category error.

We build the 2-term cellular cochain complex on the difference sheaf:
  C^0 = stalks on cells (register-diff words per round)  [dim = ncols]
  C^1 = the round-relation rows of delta                 [dim = #rows]
  delta : C^0 -> C^1   (the coboundary; rows = local constraints)
  H^1 = coker(delta) = dim C^1 - rank(delta)   (local constraints not satisfiable
        by adjusting a single stalk = gluing obstructions, the card's definition)
We report dim H^1, dim C^0, the ratio, and where the H^1-support (a basis of
coker, i.e. left-null space of delta) lives vs the 132 hard-core register pattern.
"""
import sys
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
import sheaf_delta as sd
import numpy as np
np.seterr(all='ignore')

def gf2_left_nullspace_dim_and_support(rows, ncols):
    """coker(delta) over GF(2): build the (#rows x ncols) 0/1 matrix, the left-null
    space = combinations of rows summing to 0 (a relation among the local constraints
    = an H^1 class). dim H^1 = #rows - rank. We also return the column-support
    histogram of a basis of that left-null space (which variables the obstructions
    touch), to correlate with the hard-core register positions.
    Implemented by augmenting each row with an identity tag, RREF over GF(2); tag bits
    of zero-data rows give the left-null basis."""
    R = len(rows)
    # augmented rows: data bits [0..ncols) ++ tag bits [ncols..ncols+R)
    aug = []
    for i, r in enumerate(rows):
        m = 0
        for v in r:
            m |= (1 << v)
        m |= (1 << (ncols + i))          # identity tag
        aug.append(m)
    # RREF on data columns only (0..ncols-1)
    pivots = []
    rr = 0
    n = len(aug)
    for col in range(ncols):
        bit = 1 << col
        sel = next((k for k in range(rr, n) if aug[k] & bit), None)
        if sel is None:
            continue
        aug[rr], aug[sel] = aug[sel], aug[rr]
        for k in range(n):
            if k != rr and (aug[k] & bit):
                aug[k] ^= aug[rr]
        pivots.append(col); rr += 1
        if rr == n: break
    rank = rr
    # rows now with zero data-part (index >= rank after elimination) -> their tag part
    # is a left-null combination. Collect their *data* support is zero; we instead want
    # the SUPPORT of the obstruction in C^1 terms mapped back: use the tags to know
    # which original rows combine, then OR their column supports for a 'where it lives'.
    h1_dim = R - rank
    # build column-support histogram over the left-null basis
    supp_hist = np.zeros(ncols, dtype=int)
    cnt = 0
    for k in range(n):
        data = aug[k] & ((1 << ncols) - 1)
        if data == 0:                    # a left-null relation
            tag = aug[k] >> ncols
            # OR the original rows it combines
            colmask = 0
            tt = tag
            while tt:
                idx = (tt & -tt).bit_length() - 1
                for v in rows[idx]:
                    colmask |= (1 << v)
                tt &= tt - 1
            cm = colmask
            while cm:
                j = (cm & -cm).bit_length() - 1
                supp_hist[j] += 1
                cm &= cm - 1
            cnt += 1
            if cnt >= h1_dim:
                pass
    return h1_dim, rank, supp_hist

def run():
    print("=== W4-SH2: dim H^1 = 132 (gluing obstructions)?  [category-error guard] ===\n")
    print("Real sheaf H^1 = #edges(C^1) - rank(delta)  [coker over GF(2)].")
    print("Card predicts dim H^1 = 132 and dim H^1 / dim C^0 -> 0.516 (=132/256).\n")
    print("  [STEELMAN] graded complex: fresh stalks every round + per-round glue")
    print("  relations (C^1), so coker can be genuinely nonzero.")
    print(f"  {'N':>2} {'R':>2} | {'dim C^0':>7} {'dim C^1':>7} {'rank d':>7} "
          f"{'dim H^1':>7} {'H^1/C^0':>8} {'near 132?':>9} {'near .516?':>10}")
    for N in (2, 3, 4):
        for R in (4, 7):     # R=7 ~ the genuine sr=60 tail (rounds 57..63)
            rows, nc, info = sd.assemble_graded(N, R, force_collision=True)
            h1, rank, supp = gf2_left_nullspace_dim_and_support(rows, nc)
            c0 = nc; c1 = len(rows)
            ratio = h1 / c0 if c0 else 0.0
            near132 = "yes" if h1 == 132 else f"no({h1})"
            near516 = "yes" if abs(ratio - 0.516) < 0.05 else f"no({ratio:.3f})"
            print(f"  {N:>2} {R:>2} | {c0:>7} {c1:>7} {rank:>7} {h1:>7} "
                  f"{ratio:>8.3f} {near132:>9} {near516:>10}")

    print("\n  [cross-check] degenerate complex (output-pin only, the SH1 sheaf):")
    for N in (3, 4):
        rows, nc, info = sd.assemble(N, 7, force_collision=True, carry_order=0)
        h1, rank, _ = gf2_left_nullspace_dim_and_support(rows, nc)
        print(f"    N={N} R=7: dim C^1={len(rows)} rank={rank} dim H^1={h1}")

    print("\n[support correlation] where the H^1-basis (coker) support lives, by register")
    print("block, vs the hard-core pattern {a,b,e,f fully + 4 dc}. N=4, R=7:")
    N, R = 4, 7
    rows, nc, info = sd.assemble_graded(N, R, force_collision=True)
    h1, rank, supp = gf2_left_nullspace_dim_and_support(rows, nc)
    # the first 8N columns are the INPUT register diffs a..h (the only ones with a
    # register identity); report obstruction support concentrated there.
    REG = ('a','b','c','d','e','f','g','h')
    print(f"  dim H^1 = {h1}; input-register-block support histogram (cols 0..{8*N-1}):")
    for k, name in enumerate(REG):
        block = supp[k*N:(k+1)*N]
        print(f"    reg {name}: support touches {int((block>0).sum())}/{N} bits "
              f"(total weight {int(block.sum())})")
    # crude correlation: hard-core indicator on input registers is meaningless for the
    # INPUT block (hard core is an OUTPUT-bit property). State this honestly.
    print("\n  NOTE: the 132 hard core is an OUTPUT-bit (round-63) property; the coker")
    print("  support lives on the relation/constraint columns, not output-register bits,")
    print("  so a >0.3 rank correlation with the 132 pattern is not even well-defined here.")

if __name__ == '__main__':
    run()
