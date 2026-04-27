"""Verify sr=60 collision under SEMI-FREE-START model:
  - W[0..56] from default M = [0x17149975, 0xff, ..., 0xff] schedule
  - W[57..60] FROM CERT (chosen freely)
  - W[61..63] from schedule recursion using cert W[57..60] + default W[45..56]
  - Run all 64 rounds; check final state matches between M1 and M2.

This is the ACTUAL semi-free-start collision verification.
"""
import sys, struct
sys.path.insert(0, '/Users/mac/Desktop/sha256_review')
from lib.sha256 import K, IV, MASK, Sigma0, Sigma1, Ch, Maj, sigma0, sigma1

def sha_round(s, k, w):
    a,b,c,d,e,f,g,h = s
    T1 = (h + Sigma1(e) + Ch(e,f,g) + k + w) & MASK
    T2 = (Sigma0(a) + Maj(a,b,c)) & MASK
    return [(T1+T2)&MASK, a, b, c, (d+T1)&MASK, e, f, g]

def schedule_default(M):
    """Default schedule from M[0..15]."""
    W = list(M) + [0]*48
    for i in range(16, 64):
        W[i] = (sigma1(W[i-2]) + W[i-7] + sigma0(W[i-15]) + W[i-16]) & MASK
    return W

# Build M1 default + cert overrides for W[57..60]
M1 = [0x17149975] + [0xffffffff]*15
M2 = list(M1)
M2[0] ^= 0x80000000
M2[9] ^= 0x80000000

W1_default = schedule_default(M1)
W2_default = schedule_default(M2)

# Override W[57..60] with cert values
W1 = list(W1_default)
W2 = list(W2_default)
W1[57] = 0x9ccfa55e
W1[58] = 0xd9d64416
W1[59] = 0x9e3ffb08
W1[60] = 0xb6befe82
W2[57] = 0x72e6c8cd
W2[58] = 0x4b96ca51
W2[59] = 0x587ffaa6
W2[60] = 0xea3ce26b

# Extend W[61..63] using schedule recursion with the cert W[57..60]
for k in range(61, 64):
    W1[k] = (sigma1(W1[k-2]) + W1[k-7] + sigma0(W1[k-15]) + W1[k-16]) & MASK
    W2[k] = (sigma1(W2[k-2]) + W2[k-7] + sigma0(W2[k-15]) + W2[k-16]) & MASK

print(f"W1[57..63] = {[hex(W1[k]) for k in range(57,64)]}")
print(f"W2[57..63] = {[hex(W2[k]) for k in range(57,64)]}")
print(f"dW[57..63] = {[hex((W2[k]-W1[k])&MASK) for k in range(57,64)]}")
print()

# Run 64 rounds for both
def run64(W):
    state = list(IV)
    for r in range(64):
        state = sha_round(state, K[r], W[r])
    return state

s1_after_64 = run64(W1)
s2_after_64 = run64(W2)

print(f"State after 64 rounds (state[slot 64]):")
print(f"  M1: {[hex(x) for x in s1_after_64]}")
print(f"  M2: {[hex(x) for x in s2_after_64]}")
print(f"  diffs: {[hex(s1_after_64[i]^s2_after_64[i]) for i in range(8)]}")
print(f"  STATE MATCHES (full collision): {s1_after_64 == s2_after_64}")
print(f"  Components matching: {sum(1 for i in range(8) if s1_after_64[i]==s2_after_64[i])}/8")

# Also check at slot 61 (after rounds 0..60)
def run_to(W, k):
    state = list(IV)
    for r in range(k):
        state = sha_round(state, K[r], W[r])
    return state

s1_at_61 = run_to(W1, 61)
s2_at_61 = run_to(W2, 61)
print(f"\nState at slot 61 (after rounds 0..60):")
print(f"  diffs: {[hex(s1_at_61[i]^s2_at_61[i]) for i in range(8)]}")
print(f"  STATE MATCHES (sr=60 collision): {s1_at_61 == s2_at_61}")
print(f"  Components matching: {sum(1 for i in range(8) if s1_at_61[i]==s2_at_61[i])}/8")

# Final hash
final1 = [(IV[i] + s1_after_64[i]) & MASK for i in range(8)]
final2 = [(IV[i] + s2_after_64[i]) & MASK for i in range(8)]
hash1 = b''.join(struct.pack('>I', x) for x in final1).hex()
hash2 = b''.join(struct.pack('>I', x) for x in final2).hex()
cert_hash = "ba6287f0dcaf9857d89ad44a6cced1e2adf8a242524236fbc0c656cd50a7e23b"
print(f"\nFinal hashes:")
print(f"  M1: {hash1}")
print(f"  M2: {hash2}")
print(f"  Cert: {cert_hash}")
print(f"  M1 hash == M2 hash (FULL collision): {hash1 == hash2}")
print(f"  M1 hash == cert: {hash1 == cert_hash}")
