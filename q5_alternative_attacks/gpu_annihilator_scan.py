#!/usr/bin/env python3
"""
GPU Annihilator Scanner: Test algebraic immunity of output bits at N=4.

Macbook found potential AI ≤ 4 for h[0] (via monomial list, needs verification).
This tool extends the analysis by:

1. Directly evaluating the sr=60 difference function at random sample points
2. For each output bit, building the evaluation matrix of all degree-≤d monomials
3. Finding annihilators via GF(2) null-space on GPU
4. Reporting AI for all 8 output registers' LSBs (tests cascade-ordering hypothesis)

Algorithm:
- Sample ~30000 random inputs
- Build monomial matrix M[i,j] = monomial_j(x_i) for degree ≤ d
- For target bit t, restrict to rows where t(x_i) = 1 (the "1-set")
- Find null space of restricted matrix = annihilators of t at degree ≤ d
"""
import sys, os, time
import numpy as np
import torch

MASK32 = 0xFFFFFFFF
K32 = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
]


def scale_rot(k, N=4):
    return max(1, round(k * N / 32))


class MiniSHA:
    def __init__(self, N=4):
        self.N = N
        self.MASK = (1 << N) - 1
        self.MSB = 1 << (N-1)
        self.rS0 = [scale_rot(2,N), scale_rot(13,N), scale_rot(22,N)]
        self.rS1 = [scale_rot(6,N), scale_rot(11,N), scale_rot(25,N)]
        self.rs0 = [scale_rot(7,N), scale_rot(18,N)]; self.ss0 = scale_rot(3,N)
        self.rs1 = [scale_rot(17,N), scale_rot(19,N)]; self.ss1 = scale_rot(10,N)
        self.K = [k & self.MASK for k in K32]
        self.IV = [v & self.MASK for v in [0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,
                                             0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19]]

    def ror(self, x, k):
        k = k % self.N
        return ((x >> k) | (x << (self.N - k))) & self.MASK

    def Sigma0(self, a):
        return self.ror(a, self.rS0[0]) ^ self.ror(a, self.rS0[1]) ^ self.ror(a, self.rS0[2])
    def Sigma1(self, e):
        return self.ror(e, self.rS1[0]) ^ self.ror(e, self.rS1[1]) ^ self.ror(e, self.rS1[2])
    def sigma0(self, x):
        return self.ror(x, self.rs0[0]) ^ self.ror(x, self.rs0[1]) ^ ((x >> self.ss0) & self.MASK)
    def sigma1(self, x):
        return self.ror(x, self.rs1[0]) ^ self.ror(x, self.rs1[1]) ^ ((x >> self.ss1) & self.MASK)
    def Ch(self, e, f, g): return (e & f) ^ ((~e & self.MASK) & g)
    def Maj(self, a, b, c): return (a & b) ^ (a & c) ^ (b & c)

    def compress_56(self, M):
        W = list(M) + [0] * 48
        for i in range(16, 64):
            W[i] = (self.sigma1(W[i-2]) + W[i-7] + self.sigma0(W[i-15]) + W[i-16]) & self.MASK
        a,b,c,d,e,f,g,h = self.IV
        for i in range(56):
            T1 = (h + self.Sigma1(e) + self.Ch(e,f,g) + self.K[i] + W[i]) & self.MASK
            T2 = (self.Sigma0(a) + self.Maj(a,b,c)) & self.MASK
            h,g,f,e,d,c,b,a = g,f,e,(d+T1)&self.MASK,c,b,a,(T1+T2)&self.MASK
        return [a,b,c,d,e,f,g,h], W[:57]


def find_sr60_candidate(sha):
    fill = sha.MASK
    for m0 in range(1, 1 << sha.N):
        M1 = [m0] + [fill] * 15
        M2 = list(M1)
        M2[0] ^= sha.MSB
        M2[9] ^= sha.MSB
        s1, W1 = sha.compress_56(M1)
        s2, W2 = sha.compress_56(M2)
        if s1[0] == s2[0]:
            return m0, s1, s2, W1, W2
    return None


def sample_diff_function(sha, s1, s2, W1_pre, W2_pre, n_samples=50000, seed=42):
    """
    Sample random inputs (W1[57..60], W2[57..60] at N bits each = 8N input bits).
    For each sample, compute state diff at round 63 (8 registers × N bits = 8N output bits).
    Return inputs (as bit matrix) and outputs (as bit matrix).
    """
    rng = np.random.default_rng(seed)
    N = sha.N
    MASK = sha.MASK
    n_input_bits = 8 * N
    n_output_bits = 8 * N

    # Sample inputs
    # Each input: 8 words × N bits each
    inputs = rng.integers(0, 1 << n_input_bits, size=n_samples, dtype=np.uint64)

    # Compute schedule constants
    C61_1 = (W1_pre[54] + sha.sigma0(W1_pre[46]) + W1_pre[45]) & MASK
    C61_2 = (W2_pre[54] + sha.sigma0(W2_pre[46]) + W2_pre[45]) & MASK
    C62_1 = (W1_pre[55] + sha.sigma0(W1_pre[47]) + W1_pre[46]) & MASK
    C62_2 = (W2_pre[55] + sha.sigma0(W2_pre[47]) + W2_pre[46]) & MASK
    C63_1 = (W1_pre[56] + sha.sigma0(W1_pre[48]) + W1_pre[47]) & MASK
    C63_2 = (W2_pre[56] + sha.sigma0(W2_pre[48]) + W2_pre[47]) & MASK

    # Extract free words
    outputs = np.zeros((n_samples, n_output_bits), dtype=np.uint8)
    input_bits = np.zeros((n_samples, n_input_bits), dtype=np.uint8)

    for i in range(n_samples):
        idx = int(inputs[i])
        # Unpack
        w = [(idx >> (j * N)) & MASK for j in range(8)]
        # w[0..3] = W1[57..60], w[4..7] = W2[57..60]

        # Compute W[61..63]
        W1_61 = (sha.sigma1(w[2]) + C61_1) & MASK
        W2_61 = (sha.sigma1(w[6]) + C61_2) & MASK
        W1_62 = (sha.sigma1(w[3]) + C62_1) & MASK
        W2_62 = (sha.sigma1(w[7]) + C62_2) & MASK
        W1_63 = (sha.sigma1(W1_61) + C63_1) & MASK
        W2_63 = (sha.sigma1(W2_61) + C63_2) & MASK

        # Run 7 rounds for both
        st1 = list(s1)
        W1s = [w[0], w[1], w[2], w[3], W1_61, W1_62, W1_63]
        for r in range(7):
            a,b,c,d,e,f,g,h = st1
            T1 = (h + sha.Sigma1(e) + sha.Ch(e,f,g) + sha.K[57+r] + W1s[r]) & MASK
            T2 = (sha.Sigma0(a) + sha.Maj(a,b,c)) & MASK
            st1 = [(T1+T2)&MASK, a, b, c, (d+T1)&MASK, e, f, g]

        st2 = list(s2)
        W2s = [w[4], w[5], w[6], w[7], W2_61, W2_62, W2_63]
        for r in range(7):
            a,b,c,d,e,f,g,h = st2
            T1 = (h + sha.Sigma1(e) + sha.Ch(e,f,g) + sha.K[57+r] + W2s[r]) & MASK
            T2 = (sha.Sigma0(a) + sha.Maj(a,b,c)) & MASK
            st2 = [(T1+T2)&MASK, a, b, c, (d+T1)&MASK, e, f, g]

        # Compute diff and extract bits
        for reg in range(8):
            d = st1[reg] ^ st2[reg]
            for bit in range(N):
                outputs[i, reg * N + bit] = (d >> bit) & 1

        # Extract input bits
        for j in range(n_input_bits):
            input_bits[i, j] = (idx >> j) & 1

    return input_bits, outputs


def monomials_up_to_degree(n_vars, max_deg):
    """Return list of monomials (as frozensets of variable indices) of degree ≤ max_deg."""
    from itertools import combinations
    monomials = [frozenset()]  # constant
    for d in range(1, max_deg + 1):
        for combo in combinations(range(n_vars), d):
            monomials.append(frozenset(combo))
    return monomials


def evaluate_monomials_packed(inputs, monomials):
    """
    Vectorized monomial evaluation, returning bitpacked uint64 rows.

    inputs: (n_samples, n_vars) uint8 array
    monomials: list of frozensets of variable indices
    Returns: packed (n_samples, n_words) uint64 array, n_cols
    """
    n_samples, n_vars = inputs.shape
    n_mono = len(monomials)
    n_words = (n_mono + 63) // 64

    packed = np.zeros((n_samples, n_words), dtype=np.uint64)

    # Precompute input columns for fast access
    for j, mono in enumerate(monomials):
        if len(mono) == 0:
            # constant 1 — set bit j for all rows
            word_idx = j // 64
            bit_pos = j % 64
            packed[:, word_idx] |= np.uint64(1 << bit_pos)
            continue

        # Compute the monomial value for all samples (bool column)
        col = inputs[:, list(mono)[0]].astype(np.uint8)
        for v in list(mono)[1:]:
            col &= inputs[:, v]

        # Set bit j in packed for rows where col == 1
        word_idx = j // 64
        bit_pos = j % 64
        mask = np.uint64(1 << bit_pos)
        packed[col == 1, word_idx] |= mask

    return packed, n_mono


def gf2_rank_packed(packed, n_cols):
    """
    Compute GF(2) rank of a bitpacked matrix via vectorized Gaussian elimination.

    packed: (n_rows, n_words) uint64 array
    n_cols: number of columns (bits)
    Returns: rank
    """
    n_rows, n_words = packed.shape
    rank = 0

    for col in range(n_cols):
        word_idx = col // 64
        bit_mask = np.uint64(1 << (col % 64))

        # Find rows with this bit set, starting from rank
        has_bit = (packed[rank:, word_idx] & bit_mask) != 0
        if not has_bit.any():
            continue

        pivot_rel = int(np.argmax(has_bit))
        pivot = rank + pivot_rel

        # Swap
        if pivot != rank:
            tmp = packed[rank].copy()
            packed[rank] = packed[pivot]
            packed[pivot] = tmp

        # XOR pivot row into all OTHER rows that have this bit set
        pivot_row = packed[rank]
        all_has_bit = (packed[:, word_idx] & bit_mask) != 0
        all_has_bit[rank] = False  # don't XOR into the pivot itself
        # Vectorized XOR
        rows_to_xor = np.where(all_has_bit)[0]
        if len(rows_to_xor) > 0:
            packed[rows_to_xor] ^= pivot_row[np.newaxis, :]

        rank += 1
        if rank == n_rows:
            break

    return rank


def find_ai(packed_ones, n_mono):
    """Wrapper. Returns nullity (# annihilators)."""
    n_rows = packed_ones.shape[0]
    if n_rows == 0:
        return n_mono
    rank = gf2_rank_packed(packed_ones, n_mono)
    return n_mono - rank


def main():
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    n_samples = int(sys.argv[2]) if len(sys.argv) > 2 else 20000
    max_degree = int(sys.argv[3]) if len(sys.argv) > 3 else 4

    sha = MiniSHA(N)
    print(f"=== GPU Annihilator Scanner at N={N} ===", flush=True)
    print(f"Samples: {n_samples}, max degree: {max_degree}", flush=True)

    print(f"\nFinding sr=60 candidate...", flush=True)
    result = find_sr60_candidate(sha)
    if result is None:
        print("ERROR: No candidate", flush=True)
        return
    m0, s1, s2, W1, W2 = result
    print(f"  m0=0x{m0:x}", flush=True)

    print(f"\nSampling {n_samples} random (input, output) pairs...", flush=True)
    t0 = time.time()
    inputs, outputs = sample_diff_function(sha, s1, s2, W1, W2, n_samples)
    print(f"  Done in {time.time()-t0:.1f}s", flush=True)

    n_input_bits = 8 * N
    n_output_bits = 8 * N

    # Generate monomials up to max degree
    monomials = monomials_up_to_degree(n_input_bits, max_degree)
    n_mono = len(monomials)
    print(f"\nMonomials up to degree {max_degree}: {n_mono}", flush=True)

    print(f"\nEvaluating monomials on samples (bitpacked)...", flush=True)
    t0 = time.time()
    packed_M, _ = evaluate_monomials_packed(inputs, monomials)
    print(f"  Packed shape: {packed_M.shape} uint64, {time.time()-t0:.1f}s", flush=True)

    print(f"\n--- Algebraic Immunity Analysis ---", flush=True)
    reg_names = ['a','b','c','d','e','f','g','h']
    results = {}

    for out_bit in range(n_output_bits):
        reg = out_bit // N
        bit = out_bit % N
        target = outputs[:, out_bit]

        ones_count = int(target.sum())
        if ones_count == 0 or ones_count == n_samples:
            print(f"  d{reg_names[reg]}[{bit}]: degenerate ({ones_count}/{n_samples})",
                  flush=True)
            continue

        # Restrict matrix to 1-set
        ones_mask = target == 1
        packed_ones = packed_M[ones_mask].copy()

        t0 = time.time()
        rank = gf2_rank_packed(packed_ones, n_mono)
        elapsed = time.time() - t0
        nullity = n_mono - rank
        results[(reg, bit)] = (rank, nullity, ones_count, elapsed)

        marker = " <-- ANNIHILATORS" if nullity > 0 else ""
        print(f"  d{reg_names[reg]}[{bit}]: 1-set={ones_count}, rank={rank}/{n_mono}, "
              f"nullity={nullity} ({elapsed:.1f}s){marker}", flush=True)

    print(f"\n--- Cascade ordering test (LSBs) ---", flush=True)
    for reg in range(8):
        if (reg, 0) in results:
            r, nul, ones, _ = results[(reg, 0)]
            print(f"  d{reg_names[reg]}[0]: rank={r}, nullity={nul}", flush=True)


if __name__ == "__main__":
    main()
