#!/usr/bin/env python3
"""
Z3 formulation of the round-61 closure constraint for cert kernel.

Free variables: W1[57], W1[58], W1[59], W1[60] (each 32-bit)
Cert kernel: M[0]=0x17149975, M[1..15]=0xff, dM[0]=dM[9]=0x80000000

Constraint: After cascading through rounds 57, 58, 59, 60, the cascade_dw
at round 61 should equal 0 (i.e., the round-61 closure holds).

If Z3 finds an assignment, it's a new "cert-like" prefix that admits an
sr=60 collision.

We start by ASSERTING the cert solution to verify our formulation is correct,
then ask Z3 to find ANOTHER solution.
"""
from z3 import *
import time

# Cert kernel: M[0]=0x17149975, others 0xff
# Pre-computed state at start of round 57 (M1 and M2)
M1 = [0x17149975] + [0xffffffff] * 15
M2 = [0x97149975] + [0xffffffff] * 8 + [0x7fffffff] + [0xffffffff] * 6  # XOR pattern: M[0] and M[9] flip MSB

# Compute pre-round-57 state in Python (concrete)
K = [0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
     0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
     0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
     0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
     0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
     0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
     0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
     0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2]
IV = [0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19]
MASK = 0xFFFFFFFF

def ROR(x, n): return ((x >> n) | (x << (32 - n))) & MASK
def Ch(e, f, g): return (e & f) ^ (~e & g) & MASK
def Maj(a, b, c): return (a & b) ^ (a & c) ^ (b & c)
def Sigma0(x): return ROR(x, 2) ^ ROR(x, 13) ^ ROR(x, 22)
def Sigma1(x): return ROR(x, 6) ^ ROR(x, 11) ^ ROR(x, 25)
def sigma0(x): return ROR(x, 7) ^ ROR(x, 18) ^ (x >> 3)
def sigma1(x): return ROR(x, 17) ^ ROR(x, 19) ^ (x >> 10)

def compute_state(M):
    W = list(M) + [0] * 48
    for i in range(16, 57):
        W[i] = (sigma1(W[i-2]) + W[i-7] + sigma0(W[i-15]) + W[i-16]) & MASK
    a, b, c, d, e, f, g, h = IV
    for i in range(57):
        T1 = (h + Sigma1(e) + Ch(e, f, g) + K[i] + W[i]) & MASK
        T2 = (Sigma0(a) + Maj(a, b, c)) & MASK
        h = g; g = f; f = e; e = (d + T1) & MASK
        d = c; c = b; b = a; a = (T1 + T2) & MASK
    return [a, b, c, d, e, f, g, h], W

s1, W1_pre = compute_state(M1)
s2, W2_pre = compute_state(M2)
print(f"M1 state at start of round 57: {[hex(x) for x in s1]}")
print(f"M2 state at start of round 57: {[hex(x) for x in s2]}")

# Z3 bit-vector helpers for the round function
def Z3_ROR(x, n):
    return RotateRight(x, n)
def Z3_Ch(e, f, g):
    return (e & f) ^ (~e & g)
def Z3_Maj(a, b, c):
    return (a & b) ^ (a & c) ^ (b & c)
def Z3_Sigma0(x):
    return Z3_ROR(x, 2) ^ Z3_ROR(x, 13) ^ Z3_ROR(x, 22)
def Z3_Sigma1(x):
    return Z3_ROR(x, 6) ^ Z3_ROR(x, 11) ^ Z3_ROR(x, 25)
def Z3_sigma0(x):
    return Z3_ROR(x, 7) ^ Z3_ROR(x, 18) ^ LShR(x, 3)
def Z3_sigma1(x):
    return Z3_ROR(x, 17) ^ Z3_ROR(x, 19) ^ LShR(x, 10)

# Free variables: W1[57], W1[58], W1[59], W1[60]
W1_57 = BitVec('W1_57', 32)
W1_58 = BitVec('W1_58', 32)
W1_59 = BitVec('W1_59', 32)
W1_60 = BitVec('W1_60', 32)

solver = Solver()
solver.set("timeout", 600000)  # 10 min

# Initial states (constants)
S1_57 = [BitVecVal(x, 32) for x in s1]
S2_57 = [BitVecVal(x, 32) for x in s2]

# Simulate one round of SHA-256 in Z3
def Z3_one_round(state, W, round_idx):
    a, b, c, d, e, f, g, h = state
    T1 = h + Z3_Sigma1(e) + Z3_Ch(e, f, g) + BitVecVal(K[round_idx], 32) + W
    T2 = Z3_Sigma0(a) + Z3_Maj(a, b, c)
    new_a = T1 + T2
    new_e = d + T1
    return [new_a, a, b, c, new_e, e, f, g]

def Z3_cascade_dw(s1, s2):
    """Compute cascade_dw at this round (s1 vs s2)"""
    dh = s1[7] - s2[7]
    dSig1 = Z3_Sigma1(s1[4]) - Z3_Sigma1(s2[4])
    dCh = Z3_Ch(s1[4], s1[5], s1[6]) - Z3_Ch(s2[4], s2[5], s2[6])
    T2_1 = Z3_Sigma0(s1[0]) + Z3_Maj(s1[0], s1[1], s1[2])
    T2_2 = Z3_Sigma0(s2[0]) + Z3_Maj(s2[0], s2[1], s2[2])
    return dh + dSig1 + dCh + T2_1 - T2_2

# Compute cascade chain through rounds 57, 58, 59, 60
C57 = Z3_cascade_dw(S1_57, S2_57)
W2_57 = W1_57 + C57

S1_58 = Z3_one_round(S1_57, W1_57, 57)
S2_58 = Z3_one_round(S2_57, W2_57, 57)

C58 = Z3_cascade_dw(S1_58, S2_58)
W2_58 = W1_58 + C58
S1_59 = Z3_one_round(S1_58, W1_58, 58)
S2_59 = Z3_one_round(S2_58, W2_58, 58)

C59 = Z3_cascade_dw(S1_59, S2_59)
W2_59 = W1_59 + C59
S1_60 = Z3_one_round(S1_59, W1_59, 59)
S2_60 = Z3_one_round(S2_59, W2_59, 59)

C60 = Z3_cascade_dw(S1_60, S2_60)
W2_60 = W1_60 + C60

# Round 61 closure: state must converge after round 60
S1_61 = Z3_one_round(S1_60, W1_60, 60)
S2_61 = Z3_one_round(S2_60, W2_60, 60)

# For round 61 closure: cascade_dw at round 61 should equal the
# scheduled difference (W2[61] - W1[61]) where W[61] = sigma1(W[59]) + W[54] + sigma0(W[46]) + W[45]
# W[54], W[46], W[45] are pre-computed (independent of free W[57..60])
sched_const1_61 = (W1_pre[54] + sigma0(W1_pre[46]) + W1_pre[45]) & MASK
sched_const2_61 = (W2_pre[54] + sigma0(W2_pre[46]) + W2_pre[45]) & MASK

C61_target = Z3_sigma1(W2_59) - Z3_sigma1(W1_59) + BitVecVal(sched_const2_61, 32) - BitVecVal(sched_const1_61, 32)
C61_actual = Z3_cascade_dw(S1_61, S2_61)

# The closure constraint
solver.add(C61_actual == C61_target)

# Forbid the cert solution (find a DIFFERENT one)
cert_w57 = 0x9ccfa55e
cert_w58 = 0xd9d64416
cert_w59 = 0x9e3ffb08
cert_w60 = 0xb6befe82
solver.add(Or(W1_57 != cert_w57, W1_58 != cert_w58, W1_59 != cert_w59, W1_60 != cert_w60))

print("\n=== Z3 solving ===")
print("Variables: W1[57..60] (128 bits free)")
print("Constraint: round-61 closure (cascade_dw = sigma1 difference)")
print("Excluded: cert solution")
print("Timeout: 600 seconds")

t0 = time.time()
result = solver.check()
t1 = time.time()
print(f"\nResult: {result}  ({t1-t0:.1f}s)")

if result == sat:
    m = solver.model()
    w57 = m[W1_57].as_long()
    w58 = m[W1_58].as_long()
    w59 = m[W1_59].as_long()
    w60 = m[W1_60].as_long()
    print(f"\n*** FOUND new prefix ***")
    print(f"W1[57] = 0x{w57:08x}")
    print(f"W1[58] = 0x{w58:08x}")
    print(f"W1[59] = 0x{w59:08x}")
    print(f"W1[60] = 0x{w60:08x}")
elif result == unsat:
    print("\nUNSAT — no other prefix exists with this round-61 closure!")
    print("(Combined with cert excluded, the cert is the UNIQUE solution.)")
else:
    print("\nUNKNOWN — Z3 timed out or gave up")
