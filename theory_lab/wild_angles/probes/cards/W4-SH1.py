#!/usr/bin/env python3
"""
W4-SH1 -- Sheaf-Laplacian kernel = collision count; spectral-gap collapse = the boundary.

Card probe: "N=2,3,4 assemble delta from GF(2) round Jacobians (Sigma/sigma exact,
Ch/Maj linearized, add as XOR), eigvalsh(delta^T delta); does dim ker track the
brute-force count? lambda1(60) vs lambda1(61)?"
Kill: "ker doesn't track the count, or lambda1 doesn't collapse (2x)."

Two clauses, scored separately (prior-finding #4/#5):
  (A) EQUALITY/TRACKING: does dim ker(L) (linear collision space) EQUAL log2(modular
      collision count), or merely correlate? We compute BOTH on the SAME R-round tail
      at width N: the GF(2) linear-sheaf nullity, and the EXACT modular collision count.
  (B) GAP COLLAPSE: sweep last-glued round; does lambda1 actually collapse by >=2x at
      the 60->61 boundary, or saturate smoothly (the "no round-60 knee", #4)?
"""
import sys
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
import sheaf_delta as sd
import numpy as np
np.seterr(all='ignore')

def linear_kernel(N, R, match_free=True):
    """Linear-sheaf collision-space dimension. If match_free, restrict the free
    inputs to the SAME set the modular count uses (da on reg 'a' + the R dW words)
    by pinning db..dh = 0, so both sides measure the same difference-freedom."""
    rows, nc, info = sd.assemble(N, R, force_collision=True, carry_order=0)
    if match_free:
        # pin register diffs b..h (ids N..8N-1) to zero
        for vid in range(N, 8 * N):
            rows.append(frozenset((vid,)))
    masks, _ = sd.rows_to_bitmask(rows)
    rank = sd.gf2_rank_masks(masks)
    return nc - rank, rank, nc

def modular_collision_count(N, R, seed=7):
    """EXACT count of modular collisions on the R-round tail at width N.
    Free space here = the input register diff on register 'a' (da, N bits) PLUS the R
    schedule diffs dW (each N bits) -- the joint difference freedom. A collision = the
    realized modular output diff is all-zero for the realized random base point
    (da=0,dW=0 is the trivial collision and is counted). Full enumeration when the
    space (N + R*N bits) is small, else sample. Returns (n_coll, space_bits, exact?)."""
    import random
    rng = random.Random(seed + 100 * N + R)
    base_state = tuple(rng.getrandbits(N) for _ in range(8))
    base_sched = tuple(rng.getrandbits(N) for _ in range(R))
    m = sd.maskN(N)
    space_bits = N + R * N           # da + dW[0..R-1]
    coll = 0
    if space_bits <= 22:
        total = 1 << space_bits
        for x in range(total):
            da = x & m
            dW = tuple((x >> ((r + 1) * N)) & m for r in range(R))
            reg_in = (da, 0, 0, 0, 0, 0, 0, 0)
            out = sd.modular_tail_out(reg_in, dW, base_state, base_sched, N)
            if all(o == 0 for o in out):
                coll += 1
        return coll, space_bits, True
    else:
        SAMPLES = 1 << 21
        for _ in range(SAMPLES):
            da = rng.getrandbits(N)
            dW = tuple(rng.getrandbits(N) for _ in range(R))
            reg_in = (da, 0, 0, 0, 0, 0, 0, 0)
            out = sd.modular_tail_out(reg_in, dW, base_state, base_sched, N)
            if all(o == 0 for o in out):
                coll += 1
        # scale the sampled hit-rate back up to the full space
        est = coll * (total_space := (1 << space_bits)) / SAMPLES
        return int(round(est)), space_bits, False

def run():
    print("=== W4-SH1: sheaf-Laplacian kernel vs collision count; gap collapse ===\n")

    print("[A1] DEGENERATE small-tail check: linear ker vs EXACT modular #coll on the")
    print("     SAME short R-round tail, matched free space (da + dW, db..dh pinned).\n")
    print(f"    {'N':>2} {'R':>2} | {'lin nullity':>11} {'lin rank':>8} | "
          f"{'mod #coll':>9} {'log2(#coll)':>11} {'exact?':>6}")
    for N in (2, 3, 4):
        for R in (2, 3):
            nul, rank, nc = linear_kernel(N, R, match_free=True)
            ncoll, sbits, exact = modular_collision_count(N, R)
            log2c = np.log2(ncoll) if ncoll > 0 else float('-inf')
            print(f"    {N:>2} {R:>2} | {nul:>11} {rank:>8} | "
                  f"{ncoll:>9} {log2c:>11.3f} {str(exact):>6}")
    print("    (both find only the trivial collision on one base point -> uninformative;")
    print("     the real test is vs the established LARGE sr=60 counts below.)")

    print("\n[A2] HEADLINE EQUALITY: does dim ker(L) EQUAL the established brute-force")
    print("     sr=60 collision count?  Established counts (repo, reproduced by IG5):")
    print("       N=4:49  N=8:260  N=10:946  N=12:2955  -> log2 = 5.6, 8.0, 9.9, 11.5\n")
    EST = {4: 49, 8: 260, 10: 946, 12: 2955}
    # linear-sheaf collision dofs with the NATURAL attack free-set: the input kernel
    # word da free + the genuine sr=60 tail depth (rounds 57..63 => R=7), carries dropped.
    print(f"    {'N':>3} {'est #coll':>9} {'log2(est)':>9} | "
          f"{'lin nullity (R=7)':>17} {'2^nullity':>12} {'EQUAL?':>7}")
    for N in (4, 8, 10, 12):
        nul, rank, nc = linear_kernel(N, 7, match_free=True)
        est = EST[N]; log2e = np.log2(est)
        equal = "yes" if abs(nul - log2e) < 0.5 else "NO"
        twonul = 2 ** nul
        print(f"    {N:>3} {est:>9} {log2e:>9.2f} | {nul:>17} {twonul:>12} {equal:>7}")
    print("\n    -> dim ker(L) is an INTEGER GF(2)-subspace dim; log2(count) is non-integer")
    print("       and grows ~0.74-0.96*N (saturating). If they never coincide -> ker does")
    print("       NOT equal the count (rename/analogy, prior-finding #5).")

    print("\n[B] GAP COLLAPSE: lambda1 of L sweeping the last-glued round r (depth).")
    print("    We map 'round 57..61' to tail-depth R=1..5 (R=4 ~ sr=60, R=5 ~ sr=61),")
    print("    width N=4; look for a >=2x drop in lambda1 at the 60->61 step.\n")
    N = 4
    print(f"    {'R(depth)':>9} {'~sr-round':>9} {'lambda1':>12} {'lambda_max':>12} "
          f"{'#zero-modes':>11} {'gap ratio vs prev':>17}")
    prev_l1 = None
    for R in (1, 2, 3, 4, 5):
        rows, nc, info = sd.assemble(N, R, force_collision=True, carry_order=0)
        sp = sd.spectrum(rows, nc)
        nz = int((sp < 1e-9).sum())
        pos = sp[sp > 1e-9]
        l1 = pos[0] if pos.size else 0.0
        lmax = sp[-1]
        ratio = (prev_l1 / l1) if (prev_l1 and l1 > 0) else float('nan')
        srlab = 56 + R
        print(f"    {R:>9} {srlab:>9} {l1:>12.5f} {lmax:>12.3f} {nz:>11} {ratio:>17.3f}")
        prev_l1 = l1
    print("\n    -> KILL clause (B) fires unless lambda1 drops >=2x specifically at the")
    print("       60->61 step (R=4->5) and NOT smoothly across every step.")

if __name__ == '__main__':
    run()
