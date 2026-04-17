#!/usr/bin/env python3
"""
Critical Pair Rank-Defect Predictor (from GPT-5.4 Review 7)

Predicts sr=61 critical pairs WITHOUT SAT calls by analyzing the
linearized schedule bridge as a GF(2) parity-check matrix.

For each sr=60 collision, the schedule constraint W[60] = sigma1(W[58]) + const
defines a linear (over GF(2)) relationship between W[60] bits and W[58] bits.
The cascade collision requires W[60] to satisfy certain nonlinear conditions
(from the round function). The "schedule bridge" is the GF(2) matrix mapping
W[58] bits to W[60] schedule bits.

A critical pair (i,j) is a pair of W[60] bit positions such that freeing them
restores rank consistency: the linearized system becomes solvable.

Method:
1. For each sr=60 collision, compute W[60]_collision and W[60]_schedule
2. The mismatch epsilon = W[60]_coll XOR W[60]_sched is a binary vector
3. sigma1 is a GF(2)-linear function: H * W[58] = W[60]_sched (mod 2, per bit)
4. The constraint "fix all but pair (i,j)" means: H with rows i,j removed
5. If removing rows i,j makes the system consistent with W[60]_coll, the pair is critical
6. Operationally: check if the mismatch epsilon is in the span of columns i,j

Usage: python3 critical_pair_rankdefect.py [N]
"""
import sys, os, re
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

N = int(sys.argv[1]) if len(sys.argv) > 1 else 8
spec = __import__('50_precision_homotopy')
sha = spec.MiniSHA256(N)
MASK = sha.MASK

result = sha.find_m0()
m0, s1, s2, W1p, W2p = result
print(f"N={N}, M[0]=0x{m0:x}")

# sigma1 as a GF(2) matrix: sigma1(x) = ROTR(r0,x) XOR ROTR(r1,x) XOR SHR(s,x)
# Each output bit k depends on input bits at rotated/shifted positions
r0, r1 = sha.r_sig1
s = sha.s_sig1

def sigma1_matrix(n):
    """Build the N×N GF(2) matrix for sigma1 (small sigma 1)."""
    M = [[0]*n for _ in range(n)]
    for k in range(n):
        # ROTR(r0): bit k comes from bit (k+r0) % n
        M[k][(k+r0) % n] ^= 1
        # ROTR(r1): bit k comes from bit (k+r1) % n
        M[k][(k+r1) % n] ^= 1
        # SHR(s): bit k comes from bit (k+s) if k+s < n, else 0
        if k + s < n:
            M[k][k+s] ^= 1
    return M

H = sigma1_matrix(N)
print(f"sigma1 rotation params: r0={r0}, r1={r1}, s={s}")
print(f"sigma1 GF(2) matrix rank: ", end="")

# Compute rank of H
import copy
def gf2_rank(M, n):
    A = copy.deepcopy(M)
    rank = 0
    for col in range(n):
        found = -1
        for row in range(rank, n):
            if A[row][col]: found = row; break
        if found == -1: continue
        A[rank], A[found] = A[found], A[rank]
        for row in range(n):
            if row != rank and A[row][col]:
                A[row] = [A[row][j] ^ A[rank][j] for j in range(n)]
        rank += 1
    return rank

print(gf2_rank(H, N))

# Parse collisions (from cascade DP output)
print(f"\nParsing N={N} collision data...")
collisions = []

# Try from saved file first
for path in [f'/tmp/n{N}_collisions.log',
             f'/Users/mac/Desktop/sha256_review/q5_alternative_attacks/results/20260411_cascade_dp_n{N}_260_collisions.log']:
    if not os.path.exists(path): continue
    with open(path) as f:
        for line in f:
            m = re.match(r'  #\d+: W1=\[([0-9a-f,]+)\] W2=\[([0-9a-f,]+)\]', line)
            if m:
                w1 = [int(x,16) for x in m.group(1).split(',')]
                w2 = [int(x,16) for x in m.group(2).split(',')]
                collisions.append((w1, w2))
    if collisions: break

if not collisions:
    # Generate on the fly for N=8
    import subprocess
    if os.path.exists(f'/tmp/cdp_n{N}'):
        p = subprocess.run([f'/tmp/cdp_n{N}'], capture_output=True, timeout=300)
        for line in p.stdout.decode().split('\n'):
            m = re.match(r'  #\d+: W1=\[([0-9a-f,]+)\] W2=\[([0-9a-f,]+)\]', line)
            if m:
                w1 = [int(x,16) for x in m.group(1).split(',')]
                w2 = [int(x,16) for x in m.group(2).split(',')]
                collisions.append((w1, w2))

print(f"Loaded {len(collisions)} collisions")

if not collisions:
    print("No collisions available!"); sys.exit(1)

# For each collision, compute the schedule mismatch (epsilon)
# W[60]_schedule = sigma1(W[58]) + const
const1 = (W1p[53] + sha.sigma0(W1p[45]) + W1p[44]) & MASK

# Analyze schedule mismatch for each collision
mismatch_vectors = []  # Binary vectors of length N

for w1, w2 in collisions:
    w58 = w1[1]  # W1[58]
    w60_coll = w1[3]  # W1[60] from collision
    w60_sched = (sha.sigma1(w58) + const1) & MASK  # W1[60] from schedule

    epsilon = w60_coll ^ w60_sched  # Mismatch vector
    eps_bits = [(epsilon >> k) & 1 for k in range(N)]
    mismatch_vectors.append(eps_bits)

print(f"\n=== CRITICAL PAIR RANK-DEFECT ANALYSIS ===\n")

# For each pair (i,j), check: how many collisions have epsilon
# in the span of unit vectors e_i, e_j?
# i.e., epsilon has nonzero bits ONLY at positions i and j
# (or at exactly one, or at zero)

pair_scores = defaultdict(int)
pair_details = defaultdict(lambda: {"compatible": 0, "eps_00": 0, "eps_ij": 0})

for i in range(N):
    for j in range(i+1, N):
        compat = 0
        for eps in mismatch_vectors:
            # Check if eps is zero outside positions i,j
            outside_zero = all(eps[k] == 0 for k in range(N) if k != i and k != j)
            if outside_zero:
                compat += 1
        pair_scores[(i,j)] = compat
        pair_details[(i,j)]["compatible"] = compat

# Sort by score (higher = more likely critical)
sorted_pairs = sorted(pair_scores.items(), key=lambda x: -x[1])

print(f"Pair   Compatible   Fraction   Predicted")
print(f"-----  ----------   --------   ---------")
for (i,j), score in sorted_pairs[:15]:
    frac = score / len(collisions) if collisions else 0
    predicted = "CRITICAL" if score > 0 else "non-critical"
    print(f"({i},{j})  {score:8d}    {frac:7.3f}    {predicted}")

# Show pairs that match any collisions
critical = [(i,j) for (i,j), s in pair_scores.items() if s > 0]
print(f"\nPairs with ANY compatible collision: {len(critical)}")
for i,j in sorted(critical):
    print(f"  ({i},{j}): {pair_scores[(i,j)]} collisions ({100*pair_scores[(i,j)]/len(collisions):.1f}%)")

# Compare with known results
if N == 8:
    print(f"\n=== VALIDATION (N=8 MSB kernel) ===")
    print(f"Known critical pairs from SAT: (4,5)")
    print(f"Our prediction for (4,5): {pair_scores.get((4,5), 0)} compatible collisions")
    print(f"Best pair by score: {sorted_pairs[0]}")
    if sorted_pairs[0][0] == (4,5):
        print("PREDICTION MATCHES! ✓")
    else:
        print(f"MISMATCH — predicted {sorted_pairs[0][0]}, known (4,5)")

# Also check: which single bits have the most zero-mismatch?
print(f"\n=== SINGLE-BIT ANALYSIS ===")
for bit in range(N):
    zero_at_bit = sum(1 for eps in mismatch_vectors if eps[bit] == 0)
    print(f"  bit {bit}: eps[{bit}]=0 in {zero_at_bit}/{len(collisions)} ({100*zero_at_bit/len(collisions):.1f}%)")
