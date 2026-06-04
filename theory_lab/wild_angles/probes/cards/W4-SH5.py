#!/usr/bin/env python3
"""
W4-SH5 -- Carry-filtered sheaf -> graded H^0 sheds the overcount, exponent -> 0.74.

Card probe: "N=2..5 dim ker(L^0) vs dim ker(L^1, +order-1 carry constraints) vs the
brute-force count; do carry layers *monotonically decrease* ker toward the true
count, log2/N -> 0.74?"
Kill: "carry layers don't shrink ker toward (or past) the true count, or exponent
not in [0.6,0.9]."

Two clauses (prior-finding #2: 0.74 is SUSPECT / not sharp vs 0.673):
  [A SHRINK]  does adding carry-order layers MONOTONICALLY reduce dim ker(L^k) toward
              the EXACT modular collision count on the same small tail?
  [B EXPONENT] is the growth exponent of the (limiting) kernel / true count in
              [0.6,0.9], and is 0.74 *sharp* vs 0.673?  We reproduce the established
              collision-count slope and expose its pair-spread.
"""
import sys
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
import sheaf_delta as sd
import numpy as np
np.seterr(all='ignore')

def raw_nullity(N, R, carry_order):
    rows, nc, info = sd.assemble(N, R, force_collision=True, carry_order=carry_order)
    masks, _ = sd.rows_to_bitmask(rows)
    rank = sd.gf2_rank_masks(masks)
    return nc - rank, info['carry_vars']

def collision_dofs(N, R, carry_order):
    """Linear collision dofs = raw nullity minus the free-carry-variable count.
    Each carry var is a fresh column with exactly one defining relation, so it does
    not add NET freedom -- collision dofs = raw_nullity here equals the register/sched
    freedom that satisfies all linearized relations (carry vars are determined)."""
    nul, cv = raw_nullity(N, R, carry_order)
    return nul

def exact_modular_count(N, R, seed=11):
    """EXACT count of modular collisions on the R-round tail at width N, single random
    base, free space = da on reg a + dW[0..R-1]. Trivial collision (all-zero) counted."""
    import random
    rng = random.Random(seed + 100*N + R)
    base_state = tuple(rng.getrandbits(N) for _ in range(8))
    base_sched = tuple(rng.getrandbits(N) for _ in range(R))
    m = sd.maskN(N)
    space_bits = N + R*N
    coll = 0
    total = 1 << space_bits
    if space_bits <= 22:
        for x in range(total):
            da = x & m
            dW = tuple((x >> ((r+1)*N)) & m for r in range(R))
            out = sd.modular_tail_out((da,0,0,0,0,0,0,0), dW, base_state, base_sched, N)
            if all(o == 0 for o in out): coll += 1
        return coll, True
    return -1, False

def run():
    print("=== W4-SH5: carry-filtered sheaf -> graded H^0 sheds overcount -> 0.74 ===\n")

    print("[A SHRINK] dim ker(L^k) as the carry-order filtration k increases, vs the")
    print("EXACT modular collision count on the same R-round tail (R=4).")
    print(f"  {'N':>2} {'R':>2} | {'k=0':>5} {'k=1':>5} {'k=2':>5} {'k=N':>5} | "
          f"{'mod #coll':>9} {'log2#coll':>9} | {'monotone shrink to count?':>26}")
    for N in (3, 4, 5):
        R = 4
        d0 = collision_dofs(N, R, 0)
        d1 = collision_dofs(N, R, 1)
        d2 = collision_dofs(N, R, 2)
        dN = collision_dofs(N, R, N)
        nc_count, exact = exact_modular_count(N, R) if (N + R*N) <= 22 else (-1, False)
        log2c = np.log2(nc_count) if nc_count > 0 else float('nan')
        seq = [d0, d1, d2, dN]
        mono = all(seq[i] >= seq[i+1] for i in range(len(seq)-1))
        reaches = (dN <= (log2c + 0.5)) if nc_count > 0 else False
        verdict = ("shrinks&reaches" if (mono and seq[0] > seq[-1] and reaches)
                   else "NO shrink (flat)" if seq[0] == seq[-1]
                   else "shrinks-not-enough")
        ctxt = f"{nc_count}" if nc_count >= 0 else "n/a"
        print(f"  {N:>2} {R:>2} | {d0:>5} {d1:>5} {d2:>5} {dN:>5} | "
              f"{ctxt:>9} {log2c:>9.2f} | {verdict:>26}")
    print("  -> kill fires if ker does NOT shrink toward the count (carry layers add a")
    print("     fresh var + one relation each => NET-ZERO change; a LINEAR filtration")
    print("     cannot capture the nonlinear carry that actually reduces the count).")

    print("\n[B EXPONENT] the only place 0.74 lives: the established sr=60 collision-count")
    print("slope, with its pair-spread (prior-finding #2: 0.74 not sharp vs 0.673).")
    EST = {4: 49, 8: 260, 10: 946, 12: 2955}
    Ns = sorted(EST); logs = [np.log2(EST[n]) for n in Ns]
    m_glob, b_glob = np.polyfit(Ns, logs, 1)
    pair_slopes = [(logs[i+1]-logs[i])/(Ns[i+1]-Ns[i]) for i in range(len(Ns)-1)]
    print(f"  counts {EST}")
    print(f"  log2 = {[round(float(x),2) for x in logs]}")
    print(f"  GLOBAL slope = {m_glob:.3f}   adjacent-pair slopes = "
          f"{[round(float(s),3) for s in pair_slopes]}")
    print(f"  pair-spread = {max(pair_slopes)-min(pair_slopes):.3f}; "
          f"|0.74-0.673| = {abs(0.74-0.673):.3f} "
          f"-> {'SWALLOWED by spread (0.74 NOT sharp)' if (max(pair_slopes)-min(pair_slopes)) > abs(0.74-0.673) else 'sharp'}")
    in_band = 0.6 <= m_glob <= 0.9
    print(f"  global slope in [0.6,0.9]? {in_band} (value {m_glob:.3f})")

if __name__ == '__main__':
    run()
