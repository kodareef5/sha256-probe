#!/usr/bin/env python3
"""
W2-CT1 cross-check — the literal Kalman corank (multi-bit linear control allowed).

The census in W2-CT1.py uses SINGLE-bit deterministic control (the repo's definition) -> 132.
This asks the stronger question the card's literal probe implies: take the GF(2) span of ALL
single-bit-flip output responses, stacked across many base points (the most generous linear
controllable subspace), and compute its corank. Two informative outcomes:
  corank == 132  -> even generous multi-bit/multi-point linear control can't touch the 132:
                    the hard core is a TRUE linear corank (airtight Batch-A).
  corank  < 132  -> some census-hard bits ARE reachable by linear combinations: the single-bit
                    census slightly over-counts; the true linear hard core is smaller.
Full width N=32. Throttled. Reuses shabridge.gf2_rank.
"""
import sys, random
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
s = sb.s

INPUT_BITS = 128
N_OUT = 256

def tail_out(state56, Wpre, free):
    sched = s.build_schedule_tail(Wpre, free)
    final = s.run_tail_rounds(state56, sched, start_round=57)[-1]
    out = 0
    for k, w in enumerate(final):
        out |= (w & 0xffffffff) << (32 * k)
    return out

def corank_at_points(P, rng):
    responses = []
    for _ in range(P):
        M = [rng.getrandbits(32) for _ in range(16)]
        state56, Wpre = s.precompute_state(M)
        free0 = [rng.getrandbits(32) for _ in range(4)]
        base = tail_out(state56, Wpre, free0)
        for i in range(INPUT_BITS):
            w, b = divmod(i, 32)
            free1 = list(free0); free1[w] ^= (1 << b)
            r = tail_out(state56, Wpre, free1) ^ base
            if r:
                responses.append(r)
    rank = sb.gf2_rank(responses, N_OUT)
    return rank, N_OUT - rank, len(responses)

def main():
    rng = random.Random(7)
    print(f"{'#base-points':>12} | {'#responses':>10} | {'rank':>5} | {'corank':>6}")
    for P in (1, 5, 20, 60):
        rank, corank, nresp = corank_at_points(P, random.Random(100 + P))
        print(f"{P:>12} | {nresp:>10} | {rank:>5} | {corank:>6}")
    # decisive: corank at a single base point vs the union over many
    print("\nInterpretation:")
    print(" - single base point corank  = point-wise linear hard core")
    print(" - union-over-points corank  = most generous linear control; >=132 means 132 is a true linear corank")
    print(" - repo/census single-bit deterministic hard core = 132 (see W2-CT1.py)")

if __name__ == '__main__':
    main()
