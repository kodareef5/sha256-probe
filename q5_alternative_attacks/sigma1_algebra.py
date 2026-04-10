#!/usr/bin/env python3
"""
Step 1: sigma1 Cascade Algebra

Compute the complete algebraic structure of sigma1 and the
sigma1-addition-sigma1 cascade that generates W[61] and W[63]
from the free schedule words.

This is the foundation of the sr=61 impossibility and may reveal
exploitable structure for other attacks.
"""

import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from lib.sha256 import *


def sigma1_gf2_matrix(N=32):
    """Build the GF(2) matrix of sigma1 at word width N."""
    # sigma1(x) = ROR(x, r1) XOR ROR(x, r2) XOR SHR(x, s)
    # At N=32: r1=17, r2=19, s=10
    # At other N: scaled rotations

    if N == 32:
        r1, r2, s = 17, 19, 10
    else:
        # Use the same scaling as MiniSHA256
        r1 = max(1, round(17 * N / 32))
        r2 = max(1, round(19 * N / 32))
        s = max(1, round(10 * N / 32))

    M = np.zeros((N, N), dtype=np.int8)
    for j in range(N):  # input bit j
        # ROR(x, r1): bit j goes to position (j - r1) % N
        M[(j - r1) % N, j] ^= 1
        # ROR(x, r2): bit j goes to position (j - r2) % N
        M[(j - r2) % N, j] ^= 1
        # SHR(x, s): bit j goes to position j - s (if j >= s, else lost)
        if j >= s:
            M[j - s, j] ^= 1

    return M, (r1, r2, s)


def analyze_gf2_matrix(M, name, N):
    """Analyze properties of a GF(2) matrix."""
    print(f"\n{'='*60}")
    print(f"  {name} (N={N})")
    print(f"{'='*60}")

    # Rank over GF(2) — use modular arithmetic
    # numpy doesn't have native GF(2), so we use the real rank as proxy
    # (for 0/1 matrices, rank over R ≥ rank over GF(2), but usually equal for these)
    rank_R = np.linalg.matrix_rank(M.astype(float))

    # Exact GF(2) rank via Gaussian elimination
    A = M.copy()
    rank = 0
    for col in range(N):
        # Find pivot
        pivot = -1
        for row in range(rank, N):
            if A[row, col] == 1:
                pivot = row
                break
        if pivot == -1:
            continue
        # Swap
        A[[rank, pivot]] = A[[pivot, rank]]
        # Eliminate
        for row in range(N):
            if row != rank and A[row, col] == 1:
                A[row] = (A[row] + A[rank]) % 2
        rank += 1

    print(f"  Size: {N}×{N}")
    print(f"  GF(2) rank: {rank} / {N}")
    print(f"  Invertible: {'YES' if rank == N else 'NO (null space dim = ' + str(N - rank) + ')'}")

    # Density (fraction of 1s)
    density = np.sum(M) / (N * N)
    print(f"  Density: {density:.4f} ({np.sum(M)} ones)")

    # Row weights (how many inputs affect each output bit)
    row_weights = np.sum(M, axis=1)
    print(f"  Row weights: min={row_weights.min()}, max={row_weights.max()}, "
          f"mean={row_weights.mean():.1f}")

    # Column weights (how many outputs each input bit affects)
    col_weights = np.sum(M, axis=0)
    print(f"  Col weights: min={col_weights.min()}, max={col_weights.max()}, "
          f"mean={col_weights.mean():.1f}")

    # Compute M^2 (GF(2))
    M2 = (M @ M) % 2
    rank2 = 0
    A2 = M2.copy()
    for col in range(N):
        pivot = -1
        for row in range(rank2, N):
            if A2[row, col] == 1:
                pivot = row
                break
        if pivot == -1:
            continue
        A2[[rank2, pivot]] = A2[[pivot, rank2]]
        for row in range(N):
            if row != rank2 and A2[row, col] == 1:
                A2[row] = (A2[row] + A2[rank2]) % 2
        rank2 += 1

    print(f"  M² rank: {rank2} / {N}")
    print(f"  M² density: {np.sum(M2) / (N*N):.4f}")

    # Check if M has any fixed points (Mx = x over GF(2))
    # i.e., (M - I)x = 0, i.e., null space of (M + I) mod 2
    MI = (M + np.eye(N, dtype=np.int8)) % 2
    # GF(2) null space dimension
    rank_MI = 0
    A_MI = MI.copy()
    for col in range(N):
        pivot = -1
        for row in range(rank_MI, N):
            if A_MI[row, col] == 1:
                pivot = row
                break
        if pivot == -1:
            continue
        A_MI[[rank_MI, pivot]] = A_MI[[pivot, rank_MI]]
        for row in range(N):
            if row != rank_MI and A_MI[row, col] == 1:
                A_MI[row] = (A_MI[row] + A_MI[rank_MI]) % 2
        rank_MI += 1
    nullity_MI = N - rank_MI
    print(f"  Fixed points (Mx=x): {2**nullity_MI} (null space dim = {nullity_MI})")

    # Minimal polynomial (order of M in the group)
    Mk = np.eye(N, dtype=np.int8)
    order = 0
    for k in range(1, 2*N + 1):
        Mk = (Mk @ M) % 2
        if np.array_equal(Mk, np.eye(N, dtype=np.int8)):
            order = k
            break
    if order > 0:
        print(f"  Order (M^k = I): {order}")
    else:
        print(f"  Order: > {2*N} (or not in group)")

    return rank, M2


def analyze_cascade_at_N(N):
    """
    Analyze the sigma1-addition-sigma1 cascade at word width N.

    W[61] = sigma1(W[59]) + C1
    W[63] = sigma1(W[61]) + C2 = sigma1(sigma1(W[59]) + C1) + C2

    The LINEAR part of sigma1 is captured by the GF(2) matrix.
    The NONLINEAR part comes from modular addition with C1.

    At small N, we can compute the exact truth table of the cascade.
    """
    print(f"\n{'='*60}")
    print(f"  sigma1-addition-sigma1 CASCADE (N={N})")
    print(f"{'='*60}")

    M_sig1, (r1, r2, s) = sigma1_gf2_matrix(N)
    MASK_N = (1 << N) - 1

    def sigma1_N(x):
        """sigma1 at N bits."""
        return (((x >> r1) | (x << (N - r1))) ^ ((x >> r2) | (x << (N - r2))) ^ (x >> s)) & MASK_N

    # Use the published candidate's constants
    # C1 and C2 depend on the precomputed schedule — use actual values
    M1 = [0x17149975] + [0xffffffff] * 15
    M2_msg = list(M1); M2_msg[0] ^= (1 << (N-1)); M2_msg[9] ^= (1 << (N-1))

    if N == 32:
        _, W1_pre = precompute_state(M1)
        _, W2_pre = precompute_state(M2_msg)
        C1_1 = (W1_pre[54] + sigma0(W1_pre[46]) + W1_pre[45]) & MASK
        C1_2 = (W2_pre[54] + sigma0(W2_pre[46]) + W2_pre[45]) & MASK
        C2_1 = (W1_pre[56] + sigma0(W1_pre[48]) + W1_pre[47]) & MASK
        C2_2 = (W2_pre[56] + sigma0(W2_pre[48]) + W2_pre[47]) & MASK
    else:
        # For mini-SHA, import and compute
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
        spec = __import__('50_precision_homotopy')
        sha = spec.MiniSHA256(N)
        m0_val, s1, s2, W1, W2 = sha.find_m0()
        if m0_val is None:
            print(f"  No candidate at N={N}, skipping cascade analysis")
            return
        C1_1 = (W1[54] + sha.sigma0(W1[46]) + W1[45]) & MASK_N
        C1_2 = (W2[54] + sha.sigma0(W2[46]) + W2[45]) & MASK_N
        C2_1 = (W1[56] + sha.sigma0(W1[48]) + W1[47]) & MASK_N
        C2_2 = (W2[56] + sha.sigma0(W2[48]) + W2[47]) & MASK_N

    print(f"  Constants (msg1): C1=0x{C1_1:0{N//4}x}, C2=0x{C2_1:0{N//4}x}")
    print(f"  Constants (msg2): C1=0x{C1_2:0{N//4}x}, C2=0x{C2_2:0{N//4}x}")

    def cascade_msg1(w59):
        w61 = (sigma1_N(w59) + C1_1) & MASK_N
        w63 = (sigma1_N(w61) + C2_1) & MASK_N
        return w61, w63

    def cascade_msg2(w59):
        w61 = (sigma1_N(w59) + C1_2) & MASK_N
        w63 = (sigma1_N(w61) + C2_2) & MASK_N
        return w61, w63

    if N <= 16:
        # Full truth table analysis
        print(f"\n  Full truth table analysis (2^{N} = {1<<N} entries)...")

        # For each W1[59] value, compute dW[63] = cascade_msg1(w59) XOR cascade_msg2(w59')
        # But W1[59] and W2[59] are INDEPENDENT free variables
        # The cascade acts on each message separately

        # Analyze SINGLE-MESSAGE cascade: degree of W[63] as function of W[59]
        truth_table_63 = np.zeros(1 << N, dtype=np.uint32)
        truth_table_61 = np.zeros(1 << N, dtype=np.uint32)

        for w59 in range(1 << N):
            w61, w63 = cascade_msg1(w59)
            truth_table_61[w59] = w61
            truth_table_63[w59] = w63

        # Per-bit ANF degree via Moebius transform
        print(f"\n  Per-bit degree of W[63] = sigma1(sigma1(W[59]) + C1) + C2:")
        degrees_63 = []
        for bit in range(N):
            # Extract single-bit truth table
            tt = np.array([(truth_table_63[x] >> bit) & 1 for x in range(1 << N)], dtype=np.int8)

            # Moebius transform (in-place, GF(2))
            anf = tt.copy()
            for i in range(N):
                step = 1 << i
                for j in range(0, 1 << N, 2 * step):
                    for k in range(step):
                        anf[j + k + step] ^= anf[j + k]

            # Degree = max weight of nonzero monomial
            degree = 0
            n_monomials = 0
            for idx in range(1 << N):
                if anf[idx]:
                    n_monomials += 1
                    w = bin(idx).count('1')
                    if w > degree:
                        degree = w

            degrees_63.append(degree)
            print(f"    bit {bit:2d}: degree={degree:2d}, monomials={n_monomials}")

        print(f"\n  W[63] degree summary: min={min(degrees_63)}, max={max(degrees_63)}, "
              f"mean={sum(degrees_63)/len(degrees_63):.1f}")

        # Same for W[61] (single sigma1 + addition)
        print(f"\n  Per-bit degree of W[61] = sigma1(W[59]) + C1:")
        degrees_61 = []
        for bit in range(N):
            tt = np.array([(truth_table_61[x] >> bit) & 1 for x in range(1 << N)], dtype=np.int8)
            anf = tt.copy()
            for i in range(N):
                step = 1 << i
                for j in range(0, 1 << N, 2 * step):
                    for k in range(step):
                        anf[j + k + step] ^= anf[j + k]
            degree = 0
            n_monomials = 0
            for idx in range(1 << N):
                if anf[idx]:
                    n_monomials += 1
                    w = bin(idx).count('1')
                    if w > degree:
                        degree = w
            degrees_61.append(degree)

        print(f"  W[61] degree summary: min={min(degrees_61)}, max={max(degrees_61)}, "
              f"mean={sum(degrees_61)/len(degrees_61):.1f}")

        # KEY QUESTION: how does dW[63] depend on (dW[59])?
        # dW[63] = cascade_msg1(W1[59]) XOR cascade_msg2(W2[59])
        # This is a function of TWO N-bit inputs → 2^(2N) truth table
        if N <= 10:
            print(f"\n  dW[63] analysis: function of (W1[59], W2[59])...")
            hw_dist = {}
            for w1_59 in range(1 << N):
                for w2_59 in range(1 << N):
                    _, w63_1 = cascade_msg1(w1_59)
                    _, w63_2 = cascade_msg2(w2_59)
                    dw63 = w63_1 ^ w63_2
                    h = bin(dw63).count('1')
                    hw_dist[h] = hw_dist.get(h, 0) + 1

            print(f"  dW[63] HW distribution over all (W1[59], W2[59]) pairs:")
            total = sum(hw_dist.values())
            for h in sorted(hw_dist.keys()):
                pct = 100 * hw_dist[h] / total
                if pct > 0.5:
                    print(f"    hw={h:2d}: {hw_dist[h]:8d} ({pct:5.1f}%)")
            # How often is dW[63] = 0?
            zero_count = hw_dist.get(0, 0)
            print(f"  P(dW[63]=0) = {zero_count}/{total} = {zero_count/total:.6f}")
            if zero_count > 0:
                print(f"  *** {zero_count} pairs produce dW[63]=0! ***")

    else:
        # Sampling analysis for large N
        import random
        random.seed(42)
        n_samples = 100000

        print(f"\n  Sampling cascade properties ({n_samples} samples)...")

        hw_61 = []
        hw_63 = []
        for _ in range(n_samples):
            w59 = random.getrandbits(N)
            w61, w63 = cascade_msg1(w59)
            hw_61.append(bin(w61).count('1'))
            hw_63.append(bin(w63).count('1'))

        print(f"  W[61] HW: mean={sum(hw_61)/len(hw_61):.1f}, "
              f"min={min(hw_61)}, max={max(hw_61)}")
        print(f"  W[63] HW: mean={sum(hw_63)/len(hw_63):.1f}, "
              f"min={min(hw_63)}, max={max(hw_63)}")


def compare_all_sigma_functions(N=32):
    """Compare sigma0, sigma1, Sigma0, Sigma1 matrices."""
    print(f"\n{'='*60}")
    print(f"  ALL SIGMA FUNCTIONS COMPARED (N={N})")
    print(f"{'='*60}")

    funcs = {
        'sigma0': (7, 18, 3),    # ROR(7) XOR ROR(18) XOR SHR(3)
        'sigma1': (17, 19, 10),   # ROR(17) XOR ROR(19) XOR SHR(10)
        'Sigma0': (2, 13, 22),    # ROR(2) XOR ROR(13) XOR ROR(22) — all rotations, no shift
        'Sigma1': (6, 11, 25),    # ROR(6) XOR ROR(11) XOR ROR(25) — all rotations, no shift
    }

    for name, (p1, p2, p3) in funcs.items():
        if N < 32:
            p1 = max(1, round(p1 * N / 32))
            p2 = max(1, round(p2 * N / 32))
            p3 = max(1, round(p3 * N / 32))

        M = np.zeros((N, N), dtype=np.int8)
        is_shift = (name in ['sigma0', 'sigma1'])  # lowercase = has SHR

        for j in range(N):
            M[(j - p1) % N, j] ^= 1
            M[(j - p2) % N, j] ^= 1
            if is_shift:
                if j >= p3:
                    M[j - p3, j] ^= 1
            else:
                M[(j - p3) % N, j] ^= 1

        analyze_gf2_matrix(M, f"{name} (params {p1},{p2},{p3})", N)


if __name__ == "__main__":
    print("sigma1 Cascade Algebra")
    print("=" * 60)

    # Analyze sigma1 matrix at multiple word widths
    for N in [8, 10, 16, 32]:
        M, params = sigma1_gf2_matrix(N)
        analyze_gf2_matrix(M, f"sigma1 (params {params})", N)

    # Compare all four sigma functions at N=32
    compare_all_sigma_functions(32)

    # Cascade analysis at small N (exact) and N=32 (sampling)
    for N in [8, 10, 32]:
        analyze_cascade_at_N(N)
