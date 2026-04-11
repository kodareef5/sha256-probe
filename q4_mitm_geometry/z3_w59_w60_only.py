#!/usr/bin/env python3
"""
Simpler Z3 formulation: fix cert's W[57], W[58], search for any (W[59], W[60])
that satisfies round-61 closure. We KNOW many solutions exist (from the W[59]
family experiment: 64 W[59] values × 8192 W[60] each).

If Z3 can find them, the formulation is correct. If not, there's a bug.

Also tests Z3's bit-vector reasoning speed on a simpler version of the problem.
"""
from z3 import *
import time

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

M1 = [0x17149975] + [0xffffffff] * 15
M2 = [0x97149975] + [0xffffffff] * 8 + [0x7fffffff] + [0xffffffff] * 6

def compute_state(M):
    W = list(M) + [0] * 48
    for i in range(16, 64):
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

def cascade_dw_py(s1, s2):
    dh = (s1[7] - s2[7]) & MASK
    dSig1 = (Sigma1(s1[4]) - Sigma1(s2[4])) & MASK
    dCh = (Ch(s1[4], s1[5], s1[6]) - Ch(s2[4], s2[5], s2[6])) & MASK
    T2_1 = (Sigma0(s1[0]) + Maj(s1[0], s1[1], s1[2])) & MASK
    T2_2 = (Sigma0(s2[0]) + Maj(s2[0], s2[1], s2[2])) & MASK
    return (dh + dSig1 + dCh + T2_1 - T2_2) & MASK

def one_round_py(state, W, round_idx):
    a, b, c, d, e, f, g, h = state
    T1 = (h + Sigma1(e) + Ch(e, f, g) + K[round_idx] + W) & MASK
    T2 = (Sigma0(a) + Maj(a, b, c)) & MASK
    return [(T1 + T2) & MASK, a, b, c, (d + T1) & MASK, e, f, g]

C57 = cascade_dw_py(s1, s2)

# Apply cert W[57], W[58] in Python (constants)
cert_w57 = 0x9ccfa55e
cert_w58 = 0xd9d64416

s1a = one_round_py(s1, cert_w57, 57)
s2a = one_round_py(s2, (cert_w57 + C57) & MASK, 57)
C58 = cascade_dw_py(s1a, s2a)
s1b = one_round_py(s1a, cert_w58, 58)
s2b = one_round_py(s2a, (cert_w58 + C58) & MASK, 58)
C59 = cascade_dw_py(s1b, s2b)
print(f"After cert W[57], W[58]: C59 = 0x{C59:08x}")

# Now Z3: free W[59], W[60]
def Z3_ROR(x, n): return RotateRight(x, n)
def Z3_Ch(e, f, g): return (e & f) ^ (~e & g)
def Z3_Maj(a, b, c): return (a & b) ^ (a & c) ^ (b & c)
def Z3_Sigma0(x): return Z3_ROR(x, 2) ^ Z3_ROR(x, 13) ^ Z3_ROR(x, 22)
def Z3_Sigma1(x): return Z3_ROR(x, 6) ^ Z3_ROR(x, 11) ^ Z3_ROR(x, 25)
def Z3_sigma1(x): return Z3_ROR(x, 17) ^ Z3_ROR(x, 19) ^ LShR(x, 10)

W1_59 = BitVec('W1_59', 32)
W1_60 = BitVec('W1_60', 32)

S1_59 = [BitVecVal(x, 32) for x in s1b]
S2_59 = [BitVecVal(x, 32) for x in s2b]

W2_59 = W1_59 + BitVecVal(C59, 32)

# Round 59
def Z3_one_round(state, W, round_idx):
    a, b, c, d, e, f, g, h = state
    T1 = h + Z3_Sigma1(e) + Z3_Ch(e, f, g) + BitVecVal(K[round_idx], 32) + W
    T2 = Z3_Sigma0(a) + Z3_Maj(a, b, c)
    return [T1 + T2, a, b, c, d + T1, e, f, g]

def Z3_cascade_dw(s1, s2):
    dh = s1[7] - s2[7]
    dSig1 = Z3_Sigma1(s1[4]) - Z3_Sigma1(s2[4])
    dCh = Z3_Ch(s1[4], s1[5], s1[6]) - Z3_Ch(s2[4], s2[5], s2[6])
    T2_1 = Z3_Sigma0(s1[0]) + Z3_Maj(s1[0], s1[1], s1[2])
    T2_2 = Z3_Sigma0(s2[0]) + Z3_Maj(s2[0], s2[1], s2[2])
    return dh + dSig1 + dCh + T2_1 - T2_2

S1_60 = Z3_one_round(S1_59, W1_59, 59)
S2_60 = Z3_one_round(S2_59, W2_59, 59)
C60 = Z3_cascade_dw(S1_60, S2_60)
W2_60 = W1_60 + C60
S1_61 = Z3_one_round(S1_60, W1_60, 60)
S2_61 = Z3_one_round(S2_60, W2_60, 60)

# Round 61 closure
sched_const1_61 = (W1_pre[54] + sigma0(W1_pre[46]) + W1_pre[45]) & MASK
sched_const2_61 = (W2_pre[54] + sigma0(W2_pre[46]) + W2_pre[45]) & MASK

C61_target = Z3_sigma1(W2_59) - Z3_sigma1(W1_59) + BitVecVal(sched_const2_61, 32) - BitVecVal(sched_const1_61, 32)
C61_actual = Z3_cascade_dw(S1_61, S2_61)

solver = Solver()
solver.set("timeout", 120000)  # 2 min
solver.add(C61_actual == C61_target)

# We expect to find cert (W59=0x9e3ffb08, W60=0xb6befe82) plus many others
print("\n=== Z3 solving (W57, W58 fixed to cert) ===")
print("Free: W[59], W[60] (64 bits)")
print("Constraint: round-61 closure")
print()

t0 = time.time()
result = solver.check()
t1 = time.time()
print(f"Result: {result}  ({t1-t0:.1f}s)")

if result == sat:
    m = solver.model()
    w59 = m[W1_59].as_long()
    w60 = m[W1_60].as_long()
    print(f"\nFound: W[59] = 0x{w59:08x}, W[60] = 0x{w60:08x}")
    if w59 == 0x9e3ffb08:
        print("That's the cert W[59]!")
    cert_w60_check = (w60 == 0xb6befe82)
    print(f"W[60] is cert's: {cert_w60_check}")
elif result == unsat:
    print("\nUNSAT — no solutions exist! (BUG: cert should be a solution)")
else:
    print("\nUNKNOWN — Z3 timed out")
