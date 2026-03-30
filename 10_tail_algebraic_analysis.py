#!/usr/bin/env python3
"""
Script 10: Algebraic Degree Analysis of the 7-Round Tail

Estimates the algebraic degree of each output bit as a Boolean polynomial
over the 128 input bits (W1[57..60]) in GF(2).

Key question: if any output bits have degree <= 3, XL/linearization attacks
could solve the system in polynomial time.

Method: Probabilistic degree estimation via random affine subspace restriction.
If f restricted to every d-dimensional subspace has degree d, then deg(f) >= d.
We test increasing d until the degree plateaus.

Also checks for LINEAR RELATIONS among output bits, which would reduce
the effective constraint count below 192 (6 registers x 32 bits).
"""

import random
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
M32 = 0xFFFFFFFF


def precompute():
    M1 = [0x17149975] + [0xffffffff] * 15
    M2 = M1.copy()
    M2[0] ^= 0x80000000
    M2[9] ^= 0x80000000
    results = []
    for msg in [M1, M2]:
        W = [0] * 57
        for i in range(16): W[i] = msg[i]
        for i in range(16, 57):
            W[i] = (sigma1(W[i-2]) + W[i-7] + sigma0(W[i-15]) + W[i-16]) & M32
        a, b, c, d, e, f, g, h = IV
        for i in range(57):
            T1 = (h + Sigma1(e) + Ch(e, f, g) + K[i] + W[i]) & M32
            T2 = (Sigma0(a) + Maj(a, b, c)) & M32
            h = g; g = f; f = e; e = (d + T1) & M32
            d = c; c = b; b = a; a = (T1 + T2) & M32
        results.append(((a, b, c, d, e, f, g, h), W))
    return results[0], results[1]


(STATE1, W1_PRE), (STATE2, W2_PRE) = precompute()


def eval_collision_function(w1_bits):
    """
    Given 128 bits (as 4 x 32-bit words for W1[57..60]),
    compute the output diff (256 bits as 8 x 32-bit words).
    W2[57..60] are also free but we fix them at 0 for this analysis
    since we're studying the structure of one message's contribution.

    Actually, for the collision, we need BOTH messages' free words.
    But since we're measuring degree of the diff function, we use
    W2 = constant and vary only W1.
    """
    w57, w58, w59, w60 = w1_bits

    # Message 1 tail
    w61_1 = (sigma1(w59) + W1_PRE[54] + sigma0(W1_PRE[46]) + W1_PRE[45]) & M32
    w62_1 = (sigma1(w60) + W1_PRE[55] + sigma0(W1_PRE[47]) + W1_PRE[46]) & M32
    w63_1 = (sigma1(w61_1) + W1_PRE[56] + sigma0(W1_PRE[48]) + W1_PRE[47]) & M32
    W1 = [w57, w58, w59, w60, w61_1, w62_1, w63_1]

    a, b, c, d, e, f, g, h = STATE1
    for i in range(7):
        T1 = (h + Sigma1(e) + Ch(e, f, g) + K[57+i] + W1[i]) & M32
        T2 = (Sigma0(a) + Maj(a, b, c)) & M32
        h = g; g = f; f = e; e = (d + T1) & M32
        d = c; c = b; b = a; a = (T1 + T2) & M32

    return (a, b, c, d, e, f, g, h)


def estimate_degree_subspace(dim, n_trials=100):
    """
    Estimate algebraic degree by restricting to random affine subspaces.

    For a d-dimensional subspace, a degree-k polynomial has at most C(d,k)
    nonzero coefficients. The Mobius transform of the function values over
    the subspace gives the ANF coefficients.

    If the highest-degree coefficient is always nonzero, deg >= d.
    If it's always zero, deg < d.
    """
    if dim > 20:
        return None  # Too expensive (2^dim evaluations per trial)

    max_degree_seen = 0

    for trial in range(n_trials):
        # Random affine subspace: origin + d basis vectors in {0,1}^128
        origin = [random.getrandbits(32) for _ in range(4)]

        # Random basis: d vectors in {0,1}^128
        basis = []
        for _ in range(dim):
            vec = [random.getrandbits(32) for _ in range(4)]
            basis.append(vec)

        # Evaluate function at all 2^d points of the subspace
        evals = []
        for mask in range(1 << dim):
            point = origin[:]
            for j in range(dim):
                if mask & (1 << j):
                    for w in range(4):
                        point[w] ^= basis[j][w]
            result = eval_collision_function(tuple(point))
            evals.append(result)

        # Mobius transform to get ANF coefficients
        # For each output bit, check if the degree-d coefficient is nonzero
        anf = list(evals)
        for i in range(dim):
            step = 1 << i
            for j in range(0, 1 << dim, step << 1):
                for k in range(step):
                    # anf[j+k+step] ^= anf[j+k]  (but for tuples of uint32)
                    old = anf[j + k]
                    new_val = anf[j + k + step]
                    anf[j + k + step] = tuple(new_val[w] ^ old[w] for w in range(8))

        # The degree-d coefficient is anf[(1<<dim)-1]
        top_coeff = anf[(1 << dim) - 1]
        # Count how many output bits have nonzero degree-d coefficient
        nonzero_bits = 0
        for w in range(8):
            nonzero_bits += bin(top_coeff[w]).count('1')

        if nonzero_bits > 0:
            max_degree_seen = max(max_degree_seen, dim)

    return max_degree_seen


def check_linear_relations(n_samples=10000):
    """
    Check for linear relations among output diff bits.
    If some output bits are XOR of other output bits, the effective
    constraint count is reduced.
    """
    print("=" * 70)
    print("Linear Relation Analysis")
    print("(Are any output diff bits linearly dependent?)")
    print("=" * 70)

    # Collect output diff samples
    samples = []
    for _ in range(n_samples):
        w1 = tuple(random.getrandbits(32) for _ in range(4))
        out = eval_collision_function(w1)
        # Flatten to 256 bits
        bits = 0
        for w in range(8):
            bits |= (out[w] << (w * 32))
        samples.append(bits)

    # Check pairwise XOR: are any two output bits always equal?
    print(f"\nChecking pairwise relations among 256 output bits ({n_samples} samples)...")

    # For efficiency, check in 32-bit chunks
    always_equal_pairs = 0
    always_opposite_pairs = 0

    # Sample a subset of bit pairs
    checked = 0
    for i in range(0, 256, 4):  # Check every 4th bit
        for j in range(i + 1, min(i + 64, 256), 4):
            xor_count = 0
            for s in samples:
                bi = (s >> i) & 1
                bj = (s >> j) & 1
                xor_count += bi ^ bj

            if xor_count == 0:
                always_equal_pairs += 1
            elif xor_count == n_samples:
                always_opposite_pairs += 1
            checked += 1

    print(f"  Checked {checked} pairs")
    print(f"  Always equal: {always_equal_pairs}")
    print(f"  Always opposite: {always_opposite_pairs}")
    print(f"  (Expected 0 for random function)")

    # Check for XOR triplets: bit_i ^ bit_j ^ bit_k = 0
    # (This would indicate degree-1 relations)
    print("\nChecking for XOR triplets (bit_i ^ bit_j = bit_k)...")
    triplets_found = 0
    for i in range(0, 64, 8):
        for j in range(i + 8, 128, 8):
            for k in range(128, 256, 8):
                count = 0
                for s in samples[:1000]:  # Subset for speed
                    bi = (s >> i) & 1
                    bj = (s >> j) & 1
                    bk = (s >> k) & 1
                    if bi ^ bj == bk:
                        count += 1
                if count == 1000:
                    triplets_found += 1
                    print(f"  FOUND: bit {i} ^ bit {j} = bit {k}")

    print(f"  Triplets found: {triplets_found}")
    if triplets_found > 0:
        print("  [!] Linear structure detected! This is exploitable.")
    else:
        print("  No linear structure found. Output appears random.")


def main():
    print("=" * 70)
    print("SHA-256 7-Round Tail Algebraic Degree Analysis")
    print("=" * 70)

    # 1. Degree estimation
    print("\nPhase 1: Algebraic degree estimation via subspace restriction")
    print("(Testing if output has low algebraic degree in GF(2))")
    print()

    for dim in range(1, 16):
        n_trials = max(10, 50 // dim)
        t0 = time.time()
        degree = estimate_degree_subspace(dim, n_trials)
        elapsed = time.time() - t0

        if degree is None:
            print(f"  dim={dim:2d}: SKIPPED (too expensive)")
            break

        print(f"  dim={dim:2d}: max degree seen = {degree:2d} ({elapsed:.1f}s, {n_trials} trials)",
              end="")
        if degree == dim:
            print(" <- FULL DEGREE (function uses all interactions)")
        elif degree < dim:
            print(f" <- REDUCED! (degree gap = {dim - degree})")
        else:
            print()

    # 2. Linear relations
    print()
    check_linear_relations(5000)

    # 3. Quadratic structure test
    print("\n" + "=" * 70)
    print("Quadratic Structure Test")
    print("(Is the function closer to quadratic or to random?)")
    print("=" * 70)

    # For a random function, the degree should equal the dimension for all tested d.
    # For a quadratic function, degree plateaus at 2.
    # For SHA-256's 7-round tail, we expect high degree but want to verify.

    print("\nIf degree = dim for all tested dimensions, the tail has full")
    print("algebraic complexity and algebraic attacks are not viable.")
    print("If degree plateaus at some value k < dim, XL-style attacks")
    print("with complexity O(n^k) might be feasible.")


if __name__ == "__main__":
    main()
