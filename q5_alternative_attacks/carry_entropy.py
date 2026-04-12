#!/usr/bin/env python3
"""
Carry Entropy Analysis

For each collision (W1[57..60]), extract ALL carry bits from ALL additions
in rounds 57-63 for both messages. Compute the rank of the carry matrix.

Carry Entropy Theorem: rank(carry_matrix) = log2(#collisions)

Usage: ./cascade_dp_neon N threads | grep '^COLL' | python3 carry_entropy.py N
"""
import sys, numpy as np

N = int(sys.argv[1]) if len(sys.argv) > 1 else 8
MASK = (1 << N) - 1
MSB = 1 << (N - 1)

sys.path.insert(0, '..')
spec = __import__('50_precision_homotopy')
sha = spec.MiniSHA256(N)
K = sha.K
result = sha.find_m0()
m0, s1_init, s2_init, W1p, W2p = result

def extract_carries(x, y, n=N):
    """Extract N-1 carry bits from addition z = x + y mod 2^N."""
    carries = []
    c = 0
    for i in range(n):
        xi = (x >> i) & 1
        yi = (y >> i) & 1
        c = (xi & yi) | (xi & c) | (yi & c)
        if i < n - 1:  # skip last carry (overflow, discarded)
            carries.append(c)
    return carries

def round_carries(s, k, w):
    """Run one SHA round and extract all carry bits.
    Returns (new_state, carry_vector)."""
    carries = []
    # T1 = h + Sigma1(e) + Ch(e,f,g) + K + W
    sig1 = sha.Sigma1(s[4])
    ch = sha.ch(s[4], s[5], s[6])

    t1a = s[7]  # h
    t1b = sig1
    carries += extract_carries(t1a, t1b)  # h + Sig1
    t1ab = (t1a + t1b) & MASK

    carries += extract_carries(t1ab, ch)   # (h+Sig1) + Ch
    t1abc = (t1ab + ch) & MASK

    carries += extract_carries(t1abc, k)   # (...) + K
    t1abck = (t1abc + k) & MASK

    carries += extract_carries(t1abck, w)  # (...) + W = T1
    T1 = (t1abck + w) & MASK

    # T2 = Sigma0(a) + Maj(a,b,c)
    sig0 = sha.Sigma0(s[0])
    maj = sha.maj(s[0], s[1], s[2])
    carries += extract_carries(sig0, maj)  # Sig0 + Maj = T2
    T2 = (sig0 + maj) & MASK

    # new_e = d + T1
    carries += extract_carries(s[3], T1)
    new_e = (s[3] + T1) & MASK

    # new_a = T1 + T2
    carries += extract_carries(T1, T2)
    new_a = (T1 + T2) & MASK

    new_state = [new_a, s[0], s[1], s[2], new_e, s[4], s[5], s[6]]
    return new_state, carries

def find_w2(sa, sb, rnd, w1):
    r1 = (sa[7]+sha.Sigma1(sa[4])+sha.ch(sa[4],sa[5],sa[6])+K[rnd]) & MASK
    r2 = (sb[7]+sha.Sigma1(sb[4])+sha.ch(sb[4],sb[5],sb[6])+K[rnd]) & MASK
    t21 = (sha.Sigma0(sa[0])+sha.maj(sa[0],sa[1],sa[2])) & MASK
    t22 = (sha.Sigma0(sb[0])+sha.maj(sb[0],sb[1],sb[2])) & MASK
    return (w1+r1-r2+t21-t22) & MASK

# Read collisions from stdin
collisions = []
for line in sys.stdin:
    if line.startswith('COLL'):
        parts = line.strip().split()
        w = [int(x, 16) for x in parts[1:5]]
        collisions.append(w)

print(f"N={N}, {len(collisions)} collisions loaded")

if not collisions:
    print("No collisions found in input!")
    sys.exit(1)

# Extract carry vectors for each collision
carry_vectors = []
for ci, (w57, w58, w59, w60) in enumerate(collisions):
    all_carries = []

    # Build message schedule
    W1 = [w57, w58, w59, w60]
    sa = list(s1_init); sb = list(s2_init)
    w57b = find_w2(sa, sb, 57, w57)

    # Compute cascade W2 for each round
    W2 = [w57b]
    sa_r, ca = round_carries(sa, K[57], w57)
    all_carries += ca

    sb_tmp = list(sb)
    sb_r, cb = round_carries(sb_tmp, K[57], w57b)
    all_carries += cb

    sa = sa_r; sb = sb_r

    w58b = find_w2(sa, sb, 58, w58)
    W2.append(w58b)
    sa_r, ca = round_carries(sa, K[58], w58)
    all_carries += ca
    sb_r, cb = round_carries(sb, K[58], w58b)
    all_carries += cb
    sa = sa_r; sb = sb_r

    w59b = find_w2(sa, sb, 59, w59)
    W2.append(w59b)
    sa_r, ca = round_carries(sa, K[59], w59)
    all_carries += ca
    sb_r, cb = round_carries(sb, K[59], w59b)
    all_carries += cb
    sa = sa_r; sb = sb_r

    w60b = find_w2(sa, sb, 60, w60)
    W2.append(w60b)
    sa_r, ca = round_carries(sa, K[60], w60)
    all_carries += ca
    sb_r, cb = round_carries(sb, K[60], w60b)
    all_carries += cb
    sa = sa_r; sb = sb_r

    # Schedule words for rounds 61-63
    W1.append((sha.sigma1(W1[2])+W1p[54]+sha.sigma0(W1p[46])+W1p[45])&MASK)
    W2.append((sha.sigma1(W2[2])+W2p[54]+sha.sigma0(W2p[46])+W2p[45])&MASK)
    W1.append((sha.sigma1(W1[3])+W1p[55]+sha.sigma0(W1p[47])+W1p[46])&MASK)
    W2.append((sha.sigma1(W2[3])+W2p[55]+sha.sigma0(W2p[47])+W2p[46])&MASK)
    W1.append((sha.sigma1(W1[4])+W1p[56]+sha.sigma0(W1p[48])+W1p[47])&MASK)
    W2.append((sha.sigma1(W2[4])+W2p[56]+sha.sigma0(W2p[48])+W2p[47])&MASK)

    for r in range(3):
        sa_r, ca = round_carries(sa, K[61+r], W1[4+r])
        all_carries += ca
        sb_r, cb = round_carries(sb, K[61+r], W2[4+r])
        all_carries += cb
        sa = sa_r; sb = sb_r

    # Verify collision
    ok = all(sa[i] == sb[i] for i in range(8))
    if not ok:
        print(f"  WARNING: collision {ci} failed verification!")

    carry_vectors.append(all_carries)

# Convert to numpy matrix and compute rank
M = np.array(carry_vectors, dtype=np.float64)
print(f"Carry matrix: {M.shape[0]} collisions × {M.shape[1]} carry bits")

# Compute rank via SVD
U, S, Vt = np.linalg.svd(M, full_matrices=False)
tol = max(M.shape) * S[0] * np.finfo(float).eps * 100
rank = np.sum(S > tol)

# Carry entropy
entropy = np.log2(len(collisions)) if len(collisions) > 0 else 0

print(f"\nResults:")
print(f"  #collisions: {len(collisions)}")
print(f"  log2(#coll): {entropy:.2f}")
print(f"  Carry matrix rank: {rank}")
print(f"  Carry entropy = rank: {'YES' if abs(rank - entropy) < 1.5 else 'NO'}")
print(f"  Singular values (top 20): {S[:20].round(2)}")

# Also compute carry-DIFF matrix (carry1 XOR carry2 for each collision)
# This is what the GPU laptop analyzed
carry_diffs = []
n_carries_per_round = 7 * (N - 1)
for cv in carry_vectors:
    mid = len(cv) // 2  # first half = msg1, second half = msg2...
    # Actually carries are interleaved: round57_msg1, round57_msg2, round58_msg1, ...
    diff = []
    for i in range(0, len(cv), 2 * n_carries_per_round):
        msg1_carries = cv[i:i+n_carries_per_round]
        msg2_carries = cv[i+n_carries_per_round:i+2*n_carries_per_round]
        if len(msg1_carries) == len(msg2_carries):
            diff += [a ^ b for a, b in zip(msg1_carries, msg2_carries)]
    carry_diffs.append(diff)

if carry_diffs and all(len(d) == len(carry_diffs[0]) for d in carry_diffs):
    Md = np.array(carry_diffs, dtype=np.float64)
    Ud, Sd, Vtd = np.linalg.svd(Md, full_matrices=False)
    tol_d = max(Md.shape) * Sd[0] * np.finfo(float).eps * 100
    rank_d = np.sum(Sd > tol_d)
    n_invariant = np.sum(Md.std(axis=0) < 0.01)
    print(f"\nCarry-diff analysis:")
    print(f"  Carry-diff matrix: {Md.shape}")
    print(f"  Carry-diff rank: {rank_d}")
    print(f"  Invariant carry-diff bits: {n_invariant}/{Md.shape[1]}")
    print(f"  Invariant fraction: {100*n_invariant/Md.shape[1]:.1f}%")

print("\nDone.")
