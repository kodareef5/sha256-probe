#!/usr/bin/env python3
"""
Script 2: Z3 SMT Solver for sr=60

Attempt to solve the sr=60 instance (4 free words, zero slack) using
Z3's native BitVector theory instead of boolean CNF (Kissat).

The paper reports Kissat times out at sr=60 (~430s for sr=59).
Z3/Bitwuzla handle 32-bit arithmetic natively, which might make the
difference.

This script:
1. Precomputes 57 rounds of SHA-256 for both messages (deterministic)
2. Encodes rounds 57-63 as Z3 BitVec constraints
3. Applies gap placement: W[62] and W[63] computed from schedule
4. Free variables: W1[57..60] and W2[57..60] (4 words * 2 messages * 32 bits = 256 bits)
5. Collision constraint: H1 == H2 (256 bits)
6. Slack: 256 - 256 = 0 bits (the hard case)
"""

import sys
import time

try:
    from z3 import *
except ImportError:
    print("Z3 not installed. Install with: pip install z3-solver")
    sys.exit(1)

# SHA-256 functions (pure Python for precomputation)
def ROR(x, n): return ((x >> n) | (x << (32 - n))) & 0xFFFFFFFF
def SHR(x, n): return x >> n
def Ch_py(e, f, g): return ((e & f) ^ ((~e) & g)) & 0xFFFFFFFF
def Maj_py(a, b, c): return (a & b) ^ (a & c) ^ (b & c)
def Sigma0_py(a): return ROR(a, 2) ^ ROR(a, 13) ^ ROR(a, 22)
def Sigma1_py(e): return ROR(e, 6) ^ ROR(e, 11) ^ ROR(e, 25)
def sigma0_py(x): return ROR(x, 7) ^ ROR(x, 18) ^ SHR(x, 3)
def sigma1_py(x): return ROR(x, 17) ^ ROR(x, 19) ^ SHR(x, 10)

# Z3 BitVec versions (32-bit)
def ror_z3(x, n):
    return LShR(x, n) | (x << (32 - n))

def Ch_z3(e, f, g):
    return (e & f) ^ (~e & g)

def Maj_z3(a, b, c):
    return (a & b) ^ (a & c) ^ (b & c)

def Sigma0_z3(a):
    return ror_z3(a, 2) ^ ror_z3(a, 13) ^ ror_z3(a, 22)

def Sigma1_z3(e):
    return ror_z3(e, 6) ^ ror_z3(e, 11) ^ ror_z3(e, 25)

def sigma0_z3(x):
    return ror_z3(x, 7) ^ ror_z3(x, 18) ^ LShR(x, 3)

def sigma1_z3(x):
    return ror_z3(x, 17) ^ ror_z3(x, 19) ^ LShR(x, 10)


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
    """Run 57 rounds of SHA-256 and return (state, W[0..56])."""
    W = [0] * 57
    for i in range(16):
        W[i] = M[i]
    for i in range(16, 57):
        W[i] = (sigma1_py(W[i-2]) + W[i-7] + sigma0_py(W[i-15]) + W[i-16]) & 0xFFFFFFFF

    a, b, c, d, e, f, g, h = IV
    for i in range(57):
        T1 = (h + Sigma1_py(e) + Ch_py(e, f, g) + K[i] + W[i]) & 0xFFFFFFFF
        T2 = (Sigma0_py(a) + Maj_py(a, b, c)) & 0xFFFFFFFF
        h = g; g = f; f = e; e = (d + T1) & 0xFFFFFFFF
        d = c; c = b; b = a; a = (T1 + T2) & 0xFFFFFFFF

    return (a, b, c, d, e, f, g, h), W


def solve_sr60(M1, M2, timeout_sec=600):
    """
    Attempt sr=60 solution using Z3 SMT solver.
    Free positions: {57, 58, 59, 60}
    Enforced: W[61] via sigma_1 cascade from W[59]
              W[62] via gap placement from W[60]
              W[63] via gap placement from W[61]
    """
    print(f"Precomputing 57 rounds for both messages...")
    state1, W1_pre = precompute_state(M1)
    state2, W2_pre = precompute_state(M2)

    print(f"State1 after r56: a={state1[0]:08x}")
    print(f"State2 after r56: a={state2[0]:08x}")
    print(f"da[56] = {state1[0] ^ state2[0]:08x}")
    assert state1[0] == state2[0], "da[56] must be 0!"

    print(f"\nSetting up Z3 solver for sr=60 (4 free words, 0 slack)...")
    s = Solver()
    s.set("timeout", timeout_sec * 1000)

    # Create free variables for W[57..60] for both messages
    w1 = [BitVec(f'w1_{i}', 32) for i in range(57, 61)]  # w1[0]=W1[57], ..., w1[3]=W1[60]
    w2 = [BitVec(f'w2_{i}', 32) for i in range(57, 61)]

    # Compute enforced schedule words
    # W[61] = sigma1(W[59]) + W[54] + sigma0(W[46]) + W[45]
    # For sr=60, W[61] is enforced (not free)
    # W[61] depends on W[59] (free, index 2 in our array)
    w1_61 = sigma1_z3(w1[2]) + BitVecVal(W1_pre[54], 32) + BitVecVal(sigma0_py(W1_pre[46]), 32) + BitVecVal(W1_pre[45], 32)
    w2_61 = sigma1_z3(w2[2]) + BitVecVal(W2_pre[54], 32) + BitVecVal(sigma0_py(W2_pre[46]), 32) + BitVecVal(W2_pre[45], 32)

    # W[62] = sigma1(W[60]) + W[55] + sigma0(W[47]) + W[46]
    w1_62 = sigma1_z3(w1[3]) + BitVecVal(W1_pre[55], 32) + BitVecVal(sigma0_py(W1_pre[47]), 32) + BitVecVal(W1_pre[46], 32)
    w2_62 = sigma1_z3(w2[3]) + BitVecVal(W2_pre[55], 32) + BitVecVal(sigma0_py(W2_pre[47]), 32) + BitVecVal(W2_pre[46], 32)

    # W[63] = sigma1(W[61]) + W[56] + sigma0(W[48]) + W[47]
    w1_63 = sigma1_z3(w1_61) + BitVecVal(W1_pre[56], 32) + BitVecVal(sigma0_py(W1_pre[48]), 32) + BitVecVal(W1_pre[47], 32)
    w2_63 = sigma1_z3(w2_61) + BitVecVal(W2_pre[56], 32) + BitVecVal(sigma0_py(W2_pre[48]), 32) + BitVecVal(W2_pre[47], 32)

    # Build schedule word arrays for rounds 57-63
    W1_tail = w1 + [w1_61, w1_62, w1_63]   # indices 57,58,59,60,61,62,63
    W2_tail = w2 + [w2_61, w2_62, w2_63]

    # Run rounds 57-63 symbolically for both messages
    def symbolic_rounds(state_init, W_tail):
        a, b, c, d, e, f, g, h = [BitVecVal(x, 32) for x in state_init]
        for i in range(7):  # rounds 57 to 63
            T1 = h + Sigma1_z3(e) + Ch_z3(e, f, g) + BitVecVal(K[57 + i], 32) + W_tail[i]
            T2 = Sigma0_z3(a) + Maj_z3(a, b, c)
            h = g; g = f; f = e; e = d + T1
            d = c; c = b; b = a; a = T1 + T2
        return (a, b, c, d, e, f, g, h)

    final1 = symbolic_rounds(state1, W1_tail)
    final2 = symbolic_rounds(state2, W2_tail)

    # Davies-Meyer: output = IV + final_state
    # Collision: output1 == output2, i.e., final1[i] == final2[i] for all i
    # (Since IV is the same for both, IV + final1[i] == IV + final2[i] iff final1[i] == final2[i])
    for i in range(8):
        s.add(final1[i] == final2[i])

    print(f"Solver configured. {len(s.assertions())} assertions.")
    print(f"Free variables: 8 x 32-bit = 256 bits")
    print(f"Collision constraint: 8 x 32-bit = 256 bits")
    print(f"Slack: 0 bits")
    print(f"Timeout: {timeout_sec}s")
    print(f"\nSolving...")

    start = time.time()
    result = s.check()
    elapsed = time.time() - start

    print(f"\nResult: {result} ({elapsed:.1f}s)")

    if str(result) == "sat":
        m = s.model()
        print("\n[!!!] SOLUTION FOUND!")
        print("Free words (M1):")
        for i in range(4):
            val = m[w1[i]].as_long()
            print(f"  W1[{57+i}] = 0x{val:08x}")
        print("Free words (M2):")
        for i in range(4):
            val = m[w2[i]].as_long()
            print(f"  W2[{57+i}] = 0x{val:08x}")
    elif str(result) == "unknown":
        print("Solver timed out or gave up.")
        print("Try: longer timeout, different solver (Bitwuzla), or feed different M[1..15] states.")
    else:
        print("UNSAT: No solution exists for this state.")
        print("This would mean sr=60 is impossible for this specific M[0] candidate.")

    return result


# Main
M1 = [0x17149975] + [0xffffffff] * 15
M2 = M1.copy()
M2[0] ^= 0x80000000
M2[9] ^= 0x80000000

# Try with 10-minute timeout
solve_sr60(M1, M2, timeout_sec=600)
