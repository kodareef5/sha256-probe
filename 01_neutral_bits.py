#!/usr/bin/env python3
"""
Script 1: Neutral Bit Mining

Find bits in M[1..15] that can be flipped without destroying da[56]=0.
The paper uses M[1..15] = 0xffffffff, but this is arbitrary.

For each of the 480 bits in M[1..8] and M[10..15] (skipping M[0] and M[9]
which are kernel-constrained), flip the bit and check if da[56] remains 0.

Output: a list of neutral bits that preserve the da[56]=0 condition.
These can be combined to generate thousands of valid Phase 1 candidates.
"""

import sys
import time

# SHA-256 functions
def ROR(x, n): return ((x >> n) | (x << (32 - n))) & 0xFFFFFFFF
def SHR(x, n): return x >> n
def Ch(e, f, g): return ((e & f) ^ ((~e) & g)) & 0xFFFFFFFF
def Maj(a, b, c): return (a & b) ^ (a & c) ^ (b & c)
def Sigma0(a): return ROR(a, 2) ^ ROR(a, 13) ^ ROR(a, 22)
def Sigma1(e): return ROR(e, 6) ^ ROR(e, 11) ^ ROR(e, 25)
def sigma0(x): return ROR(x, 7) ^ ROR(x, 18) ^ SHR(x, 3)
def sigma1(x): return ROR(x, 17) ^ ROR(x, 19) ^ SHR(x, 10)

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


def compute_da56(M_base):
    """Compute da[56] for a message under the MSB kernel."""
    M1 = M_base[:]
    M2 = M_base[:]
    M2[0] ^= 0x80000000
    M2[9] ^= 0x80000000

    def run_57_rounds(M):
        W = [0] * 57
        for i in range(16):
            W[i] = M[i]
        for i in range(16, 57):
            W[i] = (sigma1(W[i-2]) + W[i-7] + sigma0(W[i-15]) + W[i-16]) & 0xFFFFFFFF
        a, b, c, d, e, f, g, h = IV
        for i in range(57):
            T1 = (h + Sigma1(e) + Ch(e, f, g) + K[i] + W[i]) & 0xFFFFFFFF
            T2 = (Sigma0(a) + Maj(a, b, c)) & 0xFFFFFFFF
            h = g; g = f; f = e; e = (d + T1) & 0xFFFFFFFF
            d = c; c = b; b = a; a = (T1 + T2) & 0xFFFFFFFF
        return a, b, c, d, e, f, g, h

    s1 = run_57_rounds(M1)
    s2 = run_57_rounds(M2)
    return s1[0] ^ s2[0]  # da[56]


def compute_full_diff(M_base):
    """Compute full state differential at round 56."""
    M1 = M_base[:]
    M2 = M_base[:]
    M2[0] ^= 0x80000000
    M2[9] ^= 0x80000000

    def run_57_rounds(M):
        W = [0] * 57
        for i in range(16):
            W[i] = M[i]
        for i in range(16, 57):
            W[i] = (sigma1(W[i-2]) + W[i-7] + sigma0(W[i-15]) + W[i-16]) & 0xFFFFFFFF
        a, b, c, d, e, f, g, h = IV
        for i in range(57):
            T1 = (h + Sigma1(e) + Ch(e, f, g) + K[i] + W[i]) & 0xFFFFFFFF
            T2 = (Sigma0(a) + Maj(a, b, c)) & 0xFFFFFFFF
            h = g; g = f; f = e; e = (d + T1) & 0xFFFFFFFF
            d = c; c = b; b = a; a = (T1 + T2) & 0xFFFFFFFF
        return a, b, c, d, e, f, g, h

    s1 = run_57_rounds(M1)
    s2 = run_57_rounds(M2)
    return tuple(x ^ y for x, y in zip(s1, s2))


# Base message: the paper's candidate
M_base = [0x17149975] + [0xffffffff] * 15

# Verify baseline
da56_base = compute_da56(M_base)
assert da56_base == 0, f"Baseline da[56] should be 0, got {da56_base:#x}"
print(f"Baseline verified: da[56] = 0 for M[0] = 0x17149975, M[1..15] = 0xffffffff")

# Words we can modify (skip 0 and 9, those are kernel-constrained)
modifiable_words = [1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13, 14, 15]

print(f"\nScanning {len(modifiable_words)} words x 32 bits = {len(modifiable_words)*32} single-bit flips...")
start = time.time()

neutral_bits = []  # List of (word_idx, bit_pos) that preserve da[56]=0
semi_neutral = []  # Bits where da[56] has low Hamming weight

for word_idx in modifiable_words:
    for bit in range(32):
        M_test = M_base[:]
        M_test[word_idx] ^= (1 << bit)
        da56 = compute_da56(M_test)
        if da56 == 0:
            neutral_bits.append((word_idx, bit))
        elif bin(da56).count('1') <= 2:
            semi_neutral.append((word_idx, bit, da56))

elapsed = time.time() - start
print(f"Scan completed in {elapsed:.1f}s")

print(f"\n{'='*60}")
print(f"RESULTS")
print(f"{'='*60}")
print(f"Neutral bits (da[56] stays 0): {len(neutral_bits)}")
for word_idx, bit in neutral_bits:
    print(f"  M[{word_idx}] bit {bit}")

print(f"\nSemi-neutral bits (da[56] Hamming weight <= 2): {len(semi_neutral)}")
for word_idx, bit, da56 in semi_neutral[:20]:
    print(f"  M[{word_idx}] bit {bit:2d} -> da[56] = {da56:#010x} (hw={bin(da56).count('1')})")

if len(neutral_bits) >= 2:
    num_candidates = 2 ** len(neutral_bits)
    print(f"\nWith {len(neutral_bits)} neutral bits, we can generate {num_candidates} distinct")
    print(f"da[56]=0 candidates by toggling all combinations.")
    print(f"Each candidate has a different internal state at round 56,")
    print(f"potentially making some sr=60 SAT instances easier than others.")

# Also check: what does da[55] look like for the base and for neutral-flipped variants?
print(f"\n{'='*60}")
print(f"BONUS: Checking da[55] for base and neutral variants")
print(f"{'='*60}")

def compute_da55(M_base):
    """Compute da[55] (a-register diff after round 55)."""
    M1 = M_base[:]
    M2 = M_base[:]
    M2[0] ^= 0x80000000
    M2[9] ^= 0x80000000

    def run_56_rounds(M):
        W = [0] * 56
        for i in range(16):
            W[i] = M[i]
        for i in range(16, 56):
            W[i] = (sigma1(W[i-2]) + W[i-7] + sigma0(W[i-15]) + W[i-16]) & 0xFFFFFFFF
        a, b, c, d, e, f, g, h = IV
        for i in range(56):
            T1 = (h + Sigma1(e) + Ch(e, f, g) + K[i] + W[i]) & 0xFFFFFFFF
            T2 = (Sigma0(a) + Maj(a, b, c)) & 0xFFFFFFFF
            h = g; g = f; f = e; e = (d + T1) & 0xFFFFFFFF
            d = c; c = b; b = a; a = (T1 + T2) & 0xFFFFFFFF
        return a

    return run_56_rounds(M1) ^ run_56_rounds(M2)

da55_base = compute_da55(M_base)
print(f"Base da[55] = {da55_base:#010x} (hw={bin(da55_base).count('1')})")

# Check da[55] for each neutral bit
if neutral_bits:
    best_da55_hw = 32
    best_neutral = None
    for word_idx, bit in neutral_bits:
        M_test = M_base[:]
        M_test[word_idx] ^= (1 << bit)
        da55 = compute_da55(M_test)
        hw = bin(da55).count('1')
        if hw < best_da55_hw:
            best_da55_hw = hw
            best_neutral = (word_idx, bit, da55)

    if best_neutral:
        w, b, d = best_neutral
        print(f"Best da[55] from single neutral flip: M[{w}] bit {b}")
        print(f"  da[55] = {d:#010x} (hw={bin(d).count('1')})")
