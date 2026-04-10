#!/usr/bin/env python3
"""
linearization_n8.py — Linearization attack on low-degree bits at N=8.

The macbook ANF analysis at N=4 showed:
- Register d bit 0: degree 9, 1782 monomials
- Register h bit 0: degree 8, 1173 monomials

Linearization: treat each monomial as a new linear variable. The
collision constraint then becomes a linear system that can be solved
by Gaussian elimination. If the number of distinct monomials is
smaller than the number of free bits, the system is tractable.

At N=4: 32 free bits, ~65000 monomials per high-degree bit.
At N=8: 64 free bits, 2^k monomials for degree k.

Strategy:
1. Enumerate the monomials of degree <= k that appear in register d or h
   at some output bit (via random sampling to approximate the ANF)
2. Solve the linear system where each monomial = coefficient
3. Find input values that zero the targeted bits

This is an EXPLORATION experiment to test the linearization approach
at N=8, where we can fully enumerate but the structure should still
mirror N=32.
"""

import sys, os, time, random
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
import importlib.util
spec = importlib.util.spec_from_file_location('precision',
    '/root/sha256_probe/50_precision_homotopy.py')
precision = importlib.util.module_from_spec(spec)
spec.loader.exec_module(precision)
MiniSHA256 = precision.MiniSHA256


def eval_sr60_n8(sha, m0, fill, w1_free, w2_free):
    """Evaluate the sr=60 collision function for N=8 mini-SHA.
    Returns 8 output diff values and total HW."""
    N = 8
    MASK = sha.MASK
    MSB = sha.MSB
    K = sha.K
    IV = sha.IV
    rS0, rS1 = sha.r_Sig0, sha.r_Sig1
    rs0, ss0 = sha.r_sig0, sha.s_sig0
    rs1, ss1 = sha.r_sig1, sha.s_sig1

    def schedule(M):
        W = list(M) + [0] * 48
        for i in range(16, 57):
            x = W[i-2]
            s1v = (((x >> rs1[0]) | (x << (N - rs1[0]))) & MASK) ^ \
                  (((x >> rs1[1]) | (x << (N - rs1[1]))) & MASK) ^ \
                  ((x >> ss1) & MASK)
            y = W[i-15]
            s0v = (((y >> rs0[0]) | (y << (N - rs0[0]))) & MASK) ^ \
                  (((y >> rs0[1]) | (y << (N - rs0[1]))) & MASK) ^ \
                  ((y >> ss0) & MASK)
            W[i] = (s1v + W[i-7] + s0v + W[i-16]) & MASK
        return W

    def compress(W):
        a, b, c, d, e, f, g, h = IV
        for i in range(57):
            T1v = (((e >> rS1[0]) | (e << (N - rS1[0]))) & MASK) ^ \
                  (((e >> rS1[1]) | (e << (N - rS1[1]))) & MASK) ^ \
                  (((e >> rS1[2]) | (e << (N - rS1[2]))) & MASK)
            Chv = ((e & f) ^ ((~e & MASK) & g)) & MASK
            T1 = (h + T1v + Chv + K[i] + W[i]) & MASK
            T2v = (((a >> rS0[0]) | (a << (N - rS0[0]))) & MASK) ^ \
                  (((a >> rS0[1]) | (a << (N - rS0[1]))) & MASK) ^ \
                  (((a >> rS0[2]) | (a << (N - rS0[2]))) & MASK)
            Mjv = ((a & b) ^ (a & c) ^ (b & c)) & MASK
            T2 = (T2v + Mjv) & MASK
            h, g, f, e, d, c, b, a = g, f, e, (d + T1) & MASK, c, b, a, (T1 + T2) & MASK
        return (a, b, c, d, e, f, g, h)

    def full_tail(W_pre, free_words):
        W = list(W_pre)
        W.extend(free_words)
        # Schedule-determined W[61..63]
        for i in range(16, 64):
            if i < 57 or i >= 57 + len(free_words):
                if i >= 57 + len(free_words):
                    x = W[i-2]
                    s1v = (((x >> rs1[0]) | (x << (N - rs1[0]))) & MASK) ^ \
                          (((x >> rs1[1]) | (x << (N - rs1[1]))) & MASK) ^ \
                          ((x >> ss1) & MASK)
                    y = W[i-15]
                    s0v = (((y >> rs0[0]) | (y << (N - rs0[0]))) & MASK) ^ \
                          (((y >> rs0[1]) | (y << (N - rs0[1]))) & MASK) ^ \
                          ((y >> ss0) & MASK)
                    W.append((s1v + W[i-7] + s0v + W[i-16]) & MASK)
        return W

    M1 = [m0] + [fill] * 15
    M2 = list(M1); M2[0] ^= MSB; M2[9] ^= MSB
    W1_pre = schedule(M1)[:57]
    W2_pre = schedule(M2)[:57]
    s1 = compress(schedule(M1))
    s2 = compress(schedule(M2))

    if s1[0] != s2[0]:
        return None

    # Build full schedule with free words
    W1_full = list(W1_pre) + list(w1_free)
    W2_full = list(W2_pre) + list(w2_free)
    for i in range(57 + len(w1_free), 64):
        x1 = W1_full[i-2]
        s1v = (((x1 >> rs1[0]) | (x1 << (N - rs1[0]))) & MASK) ^ \
              (((x1 >> rs1[1]) | (x1 << (N - rs1[1]))) & MASK) ^ \
              ((x1 >> ss1) & MASK)
        y1 = W1_full[i-15]
        s0v = (((y1 >> rs0[0]) | (y1 << (N - rs0[0]))) & MASK) ^ \
              (((y1 >> rs0[1]) | (y1 << (N - rs0[1]))) & MASK) ^ \
              ((y1 >> ss0) & MASK)
        W1_full.append((s1v + W1_full[i-7] + s0v + W1_full[i-16]) & MASK)

        x2 = W2_full[i-2]
        s1v = (((x2 >> rs1[0]) | (x2 << (N - rs1[0]))) & MASK) ^ \
              (((x2 >> rs1[1]) | (x2 << (N - rs1[1]))) & MASK) ^ \
              ((x2 >> ss1) & MASK)
        y2 = W2_full[i-15]
        s0v = (((y2 >> rs0[0]) | (y2 << (N - rs0[0]))) & MASK) ^ \
              (((y2 >> rs0[1]) | (y2 << (N - rs0[1]))) & MASK) ^ \
              ((y2 >> ss0) & MASK)
        W2_full.append((s1v + W2_full[i-7] + s0v + W2_full[i-16]) & MASK)

    # Full compression for both messages
    def comp_full(W):
        a, b, c, d, e, f, g, h = IV
        for i in range(64):
            T1v = (((e >> rS1[0]) | (e << (N - rS1[0]))) & MASK) ^ \
                  (((e >> rS1[1]) | (e << (N - rS1[1]))) & MASK) ^ \
                  (((e >> rS1[2]) | (e << (N - rS1[2]))) & MASK)
            Chv = ((e & f) ^ ((~e & MASK) & g)) & MASK
            T1 = (h + T1v + Chv + K[i] + W[i]) & MASK
            T2v = (((a >> rS0[0]) | (a << (N - rS0[0]))) & MASK) ^ \
                  (((a >> rS0[1]) | (a << (N - rS0[1]))) & MASK) ^ \
                  (((a >> rS0[2]) | (a << (N - rS0[2]))) & MASK)
            Mjv = ((a & b) ^ (a & c) ^ (b & c)) & MASK
            T2 = (T2v + Mjv) & MASK
            h, g, f, e, d, c, b, a = g, f, e, (d + T1) & MASK, c, b, a, (T1 + T2) & MASK
        return (a, b, c, d, e, f, g, h)

    f1 = comp_full(W1_full)
    f2 = comp_full(W2_full)

    diff = [(f1[r] ^ f2[r]) & MASK for r in range(8)]
    total_hw = sum(bin(d).count('1') for d in diff)
    return diff, total_hw


def bit(x, i):
    return (x >> i) & 1


def main():
    sha = MiniSHA256(8)
    m0 = 0xca  # hw_dw56=0 candidate
    fill = 0x03

    # We're going to sample the collision distance HW as a function of
    # free W[57..60] values (64 bits total), and look for linear structure
    # in the output at each bit position.

    # Generate N samples and build the monomial feature matrix
    n_samples = 20000
    n_free_bits = 4 * 8 * 2  # 64 free bits across 4 words × 2 messages

    # Feature: for each monomial, compute its value across samples
    # Start with degree-1 (just the 64 input bits)
    # Then add degree-2 (all pairs = 64*63/2 = 2016)
    # Then degree-3 (too many — truncate)

    # Target: individual output bits of the XOR diff at round 63

    # First, sanity check: run sample and get a diff
    w1_free = [random.randint(0, 0xff) for _ in range(4)]
    w2_free = [random.randint(0, 0xff) for _ in range(4)]
    result = eval_sr60_n8(sha, m0, fill, w1_free, w2_free)
    if result is None:
        print(f"Candidate (0x{m0:02x}, 0x{fill:02x}) is not da[56]=0. Exiting.")
        return
    diff, hw = result
    print(f"Sanity check: diff = {[hex(d) for d in diff]}, HW = {hw}")

    # For linearization: collect (inputs, target_bit_value) for target output bit
    # Target bit: the collision requires each bit to be 0
    # For register h, bit 0 is the lowest degree — good target
    target_reg = 7  # h
    target_bit = 0

    print(f"\nBuilding feature matrix for target bit d{['a','b','c','d','e','f','g','h'][target_reg]}[63] bit {target_bit}")
    print(f"Samples: {n_samples}, Free bits: {n_free_bits}")

    # Collect degree-1 and degree-2 features
    degree_1_count = n_free_bits  # 64
    degree_2_count = n_free_bits * (n_free_bits - 1) // 2  # 2016
    total_features = degree_1_count + degree_2_count + 1  # +1 constant
    print(f"Total features (degree <= 2): {total_features}")

    X = np.zeros((n_samples, total_features), dtype=np.int8)
    y = np.zeros(n_samples, dtype=np.int8)

    rng = random.Random(42)
    for s in range(n_samples):
        w1_free = [rng.randint(0, 0xff) for _ in range(4)]
        w2_free = [rng.randint(0, 0xff) for _ in range(4)]
        result = eval_sr60_n8(sha, m0, fill, w1_free, w2_free)
        if result is None:
            continue
        diff, _ = result
        y[s] = bit(diff[target_reg], target_bit)

        # Extract input bits
        input_bits = []
        for w in w1_free + w2_free:
            for i in range(8):
                input_bits.append(bit(w, i))

        # Degree-1 features
        X[s, 0] = 1  # constant
        for i in range(n_free_bits):
            X[s, 1 + i] = input_bits[i]

        # Degree-2 features
        feat_idx = 1 + n_free_bits
        for i in range(n_free_bits):
            for j in range(i+1, n_free_bits):
                X[s, feat_idx] = input_bits[i] & input_bits[j]
                feat_idx += 1

    print(f"\nFeature matrix shape: {X.shape}, target shape: {y.shape}")
    print(f"Target distribution: {y.sum()}/{len(y)} = {y.mean():.3f}")

    # Compute rank over GF(2)
    print(f"\nComputing rank of feature matrix over GF(2)...")
    X_gf2 = X.astype(np.int8) % 2
    # Use numpy to estimate rank (real) as upper bound
    rank_real = np.linalg.matrix_rank(X_gf2.astype(float))
    print(f"Real rank: {rank_real} (upper bound on GF(2) rank)")

    # Check: can we linearly predict y from X? Solve least squares
    # Over GF(2) this would be Gaussian elimination; here use numpy as approximation
    lstsq_result, residuals, _, _ = np.linalg.lstsq(X.astype(float), y.astype(float), rcond=None)
    y_pred = X.astype(float) @ lstsq_result
    y_pred_binary = (y_pred > 0.5).astype(np.int8)
    accuracy = (y_pred_binary == y).mean()
    print(f"Linear predictor (least squares) accuracy: {accuracy:.4f}")
    print(f"  (0.5 = random baseline, 1.0 = perfect fit)")

    nonzero_coefs = np.sum(np.abs(lstsq_result) > 1e-6)
    print(f"Nonzero coefficients: {nonzero_coefs}/{total_features}")


if __name__ == "__main__":
    main()
