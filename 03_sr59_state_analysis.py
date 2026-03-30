#!/usr/bin/env python3
"""
Script 3: Analyze the verified sr=59 collision state

Extract and analyze the full internal state at every round for both
messages in the verified collision. Look for structural patterns that
could inform sr=60 attacks:
- What do the free word differences look like?
- What's the Hamming weight pattern of register diffs across rounds?
- Are there rounds where diffs are unusually small (potential constraints)?
"""

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


def full_compression_trace(M, free_words_57_61):
    """Run full 64-round compression with trace of all states."""
    W = [0] * 64
    for i in range(16):
        W[i] = M[i]
    for i in range(16, 57):
        W[i] = (sigma1(W[i-2]) + W[i-7] + sigma0(W[i-15]) + W[i-16]) & 0xFFFFFFFF
    for i in range(5):
        W[57 + i] = free_words_57_61[i]
    W[62] = (sigma1(W[60]) + W[55] + sigma0(W[47]) + W[46]) & 0xFFFFFFFF
    W[63] = (sigma1(W[61]) + W[56] + sigma0(W[48]) + W[47]) & 0xFFFFFFFF

    states = []
    a, b, c, d, e, f, g, h = IV
    states.append((a, b, c, d, e, f, g, h))
    for i in range(64):
        T1 = (h + Sigma1(e) + Ch(e, f, g) + K[i] + W[i]) & 0xFFFFFFFF
        T2 = (Sigma0(a) + Maj(a, b, c)) & 0xFFFFFFFF
        h = g; g = f; f = e; e = (d + T1) & 0xFFFFFFFF
        d = c; c = b; b = a; a = (T1 + T2) & 0xFFFFFFFF
        states.append((a, b, c, d, e, f, g, h))

    return states, W


# Data from the paper
M1 = [0x17149975] + [0xffffffff] * 15
M2 = M1.copy()
M2[0] = M1[0] ^ 0x80000000
M2[9] = M1[9] ^ 0x80000000

W1_free = [0x35ff2fce, 0x091194cf, 0x92290bc7, 0xc136a254, 0xc6841268]
W2_free = [0x0c16533d, 0x8792091f, 0x93a0f3b6, 0x8b270b72, 0x40110184]

states1, W1 = full_compression_trace(M1, W1_free)
states2, W2 = full_compression_trace(M2, W2_free)

# Print schedule word differences
print("=" * 70)
print("Schedule Word Analysis (W[i] differences)")
print("=" * 70)
print(f"{'Round':>5} {'W1[i]':>10} {'W2[i]':>10} {'dW[i]':>10} {'hw':>4}")
print("-" * 45)
for i in range(64):
    dw = W1[i] ^ W2[i]
    hw = bin(dw).count('1')
    marker = ""
    if i < 24 and dw == 0:
        marker = " (zero-diff, MSB kernel)"
    elif 57 <= i <= 61:
        marker = " <-- FREE"
    elif i >= 62:
        marker = " (gap-placed)"
    print(f"{i:5d} {W1[i]:10x} {W2[i]:10x} {dw:10x} {hw:4d}{marker}")

# Print state differentials at each round
print("\n" + "=" * 70)
print("State Differential Analysis (a-register XOR diff at each round)")
print("=" * 70)
print(f"{'Round':>5} {'da':>10} {'hw(da)':>7} {'db':>10} {'dc':>10} {'dd':>10}")
print("-" * 55)
for r in range(65):
    da = states1[r][0] ^ states2[r][0]
    db = states1[r][1] ^ states2[r][1]
    dc = states1[r][2] ^ states2[r][2]
    dd = states1[r][3] ^ states2[r][3]
    hw_da = bin(da).count('1')
    marker = ""
    if da == 0:
        marker = " <-- da=0!"
    if r == 64:
        marker = " <-- FINAL (should match)"
    print(f"{r:5d} {da:10x} {hw_da:7d} {db:10x} {dc:10x} {dd:10x}{marker}")

# Analyze total state Hamming weight at each round
print("\n" + "=" * 70)
print("Total State Hamming Weight (sum of hw across all 8 registers)")
print("=" * 70)
for r in range(65):
    total_hw = sum(bin(states1[r][i] ^ states2[r][i]).count('1') for i in range(8))
    bar = "#" * (total_hw // 4)
    marker = " <-- COLLISION" if total_hw == 0 and r > 0 else ""
    print(f"Round {r:3d}: hw={total_hw:4d} {bar}{marker}")

# Free word analysis
print("\n" + "=" * 70)
print("Free Word Difference Analysis")
print("=" * 70)
for i in range(5):
    dw = W1_free[i] ^ W2_free[i]
    print(f"W[{57+i}]: dW = {dw:08x} (hw={bin(dw).count('1')})")
