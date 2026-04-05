#!/usr/bin/env python3
"""
Script 07: Progressive Constraint Tightening

Solves sr=59 (5 free words) but adds a PARTIAL schedule compliance
constraint on W[61]: require the low k bits of W1[61] (and W2[61])
to match the schedule equation.

At k=0:  standard sr=59 (the paper's solved problem)
At k=32: full sr=60 (the unsolved problem)

Maps the hardness phase transition:
  - If transition is at k=1: sr=60 is fundamentally discontinuous, no incremental path
  - If transition is gradual (k=24 ok, k=32 hard): hybrid approach possible
    (SAT for first k bits, brute-force remaining 32-k bits)
"""

import sys
import time

try:
    from z3 import *
except ImportError:
    print("Z3 not installed. Install with: pip install z3-solver")
    sys.exit(1)

# SHA-256 functions
def ROR(x, n): return ((x >> n) | (x << (32 - n))) & 0xFFFFFFFF
def SHR(x, n): return x >> n
def Ch_py(e, f, g): return ((e & f) ^ ((~e) & g)) & 0xFFFFFFFF
def Maj_py(a, b, c): return (a & b) ^ (a & c) ^ (b & c)
def Sigma0_py(a): return ROR(a, 2) ^ ROR(a, 13) ^ ROR(a, 22)
def Sigma1_py(e): return ROR(e, 6) ^ ROR(e, 11) ^ ROR(e, 25)
def sigma0_py(x): return ROR(x, 7) ^ ROR(x, 18) ^ SHR(x, 3)
def sigma1_py(x): return ROR(x, 17) ^ ROR(x, 19) ^ SHR(x, 10)

def ror_z3(x, n): return LShR(x, n) | (x << (32 - n))
def Ch_z3(e, f, g): return (e & f) ^ (~e & g)
def Maj_z3(a, b, c): return (a & b) ^ (a & c) ^ (b & c)
def Sigma0_z3(a): return ror_z3(a, 2) ^ ror_z3(a, 13) ^ ror_z3(a, 22)
def Sigma1_z3(e): return ror_z3(e, 6) ^ ror_z3(e, 11) ^ ror_z3(e, 25)
def sigma0_z3(x): return ror_z3(x, 7) ^ ror_z3(x, 18) ^ LShR(x, 3)
def sigma1_z3(x): return ror_z3(x, 17) ^ ror_z3(x, 19) ^ LShR(x, 10)

K = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
]
IV = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
      0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19]


def precompute_state(M):
    W = [0] * 57
    for i in range(16): W[i] = M[i]
    for i in range(16, 57):
        W[i] = (sigma1_py(W[i-2]) + W[i-7] + sigma0_py(W[i-15]) + W[i-16]) & 0xFFFFFFFF
    a, b, c, d, e, f, g, h = IV
    for i in range(57):
        T1 = (h + Sigma1_py(e) + Ch_py(e, f, g) + K[i] + W[i]) & 0xFFFFFFFF
        T2 = (Sigma0_py(a) + Maj_py(a, b, c)) & 0xFFFFFFFF
        h = g; g = f; f = e; e = (d + T1) & 0xFFFFFFFF
        d = c; c = b; b = a; a = (T1 + T2) & 0xFFFFFFFF
    return (a, b, c, d, e, f, g, h), W


def solve_with_k_bits(state1, state2, W1_pre, W2_pre, k_bits, timeout_sec=600):
    """
    Solve sr=59 + k bits of W[61] schedule compliance.

    Free: W1[57..61], W2[57..61] (5 words each = sr=59)
    Extra constraint: low k_bits of W1[61] must match schedule equation
                     (and same for W2[61])

    The schedule equation for W[61] is:
      W[61] = sigma1(W[59]) + W[54] + sigma0(W[46]) + W[45]

    At k=0: pure sr=59 (should solve in <600s based on paper)
    At k=32: full sr=60
    """
    s = Solver()
    s.set("timeout", timeout_sec * 1000)

    # Free variables: W1[57..61] and W2[57..61]
    w1 = [BitVec(f'w1_{57+i}', 32) for i in range(5)]  # w1[0..4] = W1[57..61]
    w2 = [BitVec(f'w2_{57+i}', 32) for i in range(5)]

    # Schedule enforcement for W[62] and W[63] (gap placement, always enforced)
    # W1[62] = sigma1(W1[60]) + W1[55] + sigma0(W1[47]) + W1[46]
    w1_62 = sigma1_z3(w1[3]) + BitVecVal(W1_pre[55], 32) + BitVecVal(sigma0_py(W1_pre[47]), 32) + BitVecVal(W1_pre[46], 32)
    w2_62 = sigma1_z3(w2[3]) + BitVecVal(W2_pre[55], 32) + BitVecVal(sigma0_py(W2_pre[47]), 32) + BitVecVal(W2_pre[46], 32)

    # W1[63] = sigma1(W1[61]) + W1[56] + sigma0(W1[48]) + W1[47]
    w1_63 = sigma1_z3(w1[4]) + BitVecVal(W1_pre[56], 32) + BitVecVal(sigma0_py(W1_pre[48]), 32) + BitVecVal(W1_pre[47], 32)
    w2_63 = sigma1_z3(w2[4]) + BitVecVal(W2_pre[56], 32) + BitVecVal(sigma0_py(W2_pre[48]), 32) + BitVecVal(W2_pre[47], 32)

    W1_tail = list(w1) + [w1_62, w1_63]  # 7 words: 57,58,59,60,61,62,63
    W2_tail = list(w2) + [w2_62, w2_63]

    # Run rounds 57-63 symbolically
    def symbolic_rounds(state_init, W_tail):
        a, b, c, d, e, f, g, h = [BitVecVal(x, 32) for x in state_init]
        for i in range(7):
            T1 = h + Sigma1_z3(e) + Ch_z3(e, f, g) + BitVecVal(K[57+i], 32) + W_tail[i]
            T2 = Sigma0_z3(a) + Maj_z3(a, b, c)
            h = g; g = f; f = e; e = d + T1
            d = c; c = b; b = a; a = T1 + T2
        return (a, b, c, d, e, f, g, h)

    final1 = symbolic_rounds(state1, W1_tail)
    final2 = symbolic_rounds(state2, W2_tail)

    # Collision constraint
    for i in range(8):
        s.add(final1[i] == final2[i])

    # Progressive schedule compliance for W[61]
    # W[61]_schedule = sigma1(W[59]) + W[54] + sigma0(W[46]) + W[45]
    if k_bits > 0:
        w1_61_sched = sigma1_z3(w1[2]) + BitVecVal(W1_pre[54], 32) + BitVecVal(sigma0_py(W1_pre[46]), 32) + BitVecVal(W1_pre[45], 32)
        w2_61_sched = sigma1_z3(w2[2]) + BitVecVal(W2_pre[54], 32) + BitVecVal(sigma0_py(W2_pre[46]), 32) + BitVecVal(W2_pre[45], 32)

        if k_bits >= 32:
            # Full compliance: W[61] == schedule value
            s.add(w1[4] == w1_61_sched)
            s.add(w2[4] == w2_61_sched)
        else:
            # Partial: only low k bits must match
            mask = BitVecVal((1 << k_bits) - 1, 32)
            s.add((w1[4] & mask) == (w1_61_sched & mask))
            s.add((w2[4] & mask) == (w2_61_sched & mask))

    result = s.check()
    return result, s


def main():
    M1 = [0x17149975] + [0xffffffff] * 15
    M2 = M1.copy()
    M2[0] ^= 0x80000000
    M2[9] ^= 0x80000000

    state1, W1_pre = precompute_state(M1)
    state2, W2_pre = precompute_state(M2)

    assert state1[0] == state2[0], "da[56] must be 0!"

    timeout = int(sys.argv[1]) if len(sys.argv) > 1 else 600

    # Test increasing k values
    k_values = [0, 1, 2, 4, 8, 12, 16, 20, 24, 28, 32]

    print("=" * 70)
    print("Progressive Constraint Tightening: sr=59 -> sr=60")
    print(f"Timeout per instance: {timeout}s")
    print("=" * 70)
    print(f"\n{'k_bits':>8} {'Slack':>8} {'Result':>10} {'Time':>10} {'Effective sr':>14}")
    print("-" * 55)

    results = []
    for k in k_values:
        # Slack: at k=0, sr=59 has 5*2*32=320 bits freedom, 256 constraint -> 64 slack
        # Each bit of W[61] schedule compliance removes ~1 bit of freedom (from each message)
        # So slack = 64 - 2*k (one constraint bit per message)
        slack = max(64 - 2 * k, 0)
        eff_sr = 59 + k / 32.0

        print(f"  k={k:3d}   {slack:4d}    ", end="", flush=True)
        start = time.time()
        result, solver = solve_with_k_bits(state1, state2, W1_pre, W2_pre, k, timeout)
        elapsed = time.time() - start

        result_str = str(result)
        print(f"{result_str:10s} {elapsed:8.1f}s   sr={eff_sr:.1f}")
        results.append((k, slack, result_str, elapsed, eff_sr))

        if result_str == "unsat":
            print(f"\n  UNSAT at k={k}! The schedule constraint is incompatible")
            print(f"  with collision for this candidate. sr=60 is impossible here.")
            break

        if result_str == "unknown" and elapsed >= timeout * 0.95:
            print(f"\n  Timeout at k={k} (slack={slack}). Hardness wall reached.")
            # Try one more k to confirm
            if k < 32:
                continue

    print("\n" + "=" * 70)
    print("PHASE TRANSITION MAP")
    print("=" * 70)
    for k, slack, result, elapsed, eff_sr in results:
        bar = "#" * min(int(elapsed / 10), 50)
        status = "OK" if result == "sat" else ("HARD" if result == "unknown" else "IMPOSSIBLE")
        print(f"  k={k:3d} (sr={eff_sr:.1f}, slack={slack:3d}): {elapsed:8.1f}s [{status}] {bar}")

    # Identify the transition point
    last_sat_k = -1
    first_hard_k = 33
    for k, _, result, _, _ in results:
        if result == "sat":
            last_sat_k = k
        elif result in ("unknown", "unsat") and k < first_hard_k:
            first_hard_k = k

    print(f"\n  Last solved: k={last_sat_k} (sr={59 + last_sat_k/32:.1f})")
    print(f"  First hard:  k={first_hard_k} (sr={59 + first_hard_k/32:.1f})")

    if last_sat_k >= 16:
        remaining = 32 - last_sat_k
        n_instances = 2 ** remaining
        print(f"\n  HYBRID OPPORTUNITY: Solve k={last_sat_k} by SAT, brute-force remaining {remaining} bits")
        print(f"  This requires {n_instances} SAT instances (each ~{results[len([r for r in results if r[0] <= last_sat_k])-1][3]:.0f}s)")
        est_hours = n_instances * results[len([r for r in results if r[0] <= last_sat_k])-1][3] / 3600
        print(f"  Estimated total: ~{est_hours:.1f} hours")


if __name__ == "__main__":
    main()
