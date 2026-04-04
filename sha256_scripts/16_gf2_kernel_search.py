#!/usr/bin/env python3
"""
Script 16: GF(2) Kernel Search for Extended Differential Cancellation

The paper proved the MSB kernel (dM[0]=dM[9]=0x80000000) is the unique
optimal 2-word kernel. But it only guarantees dW[16..23]=0 (8 consecutive
zero schedule diffs). The paper also proved no 3-word extension improves
the consecutive zero count.

However, this leaves open:
1. Can a multi-word kernel create zeros at SPECIFIC late positions (e.g., 55,56,57)?
2. What's the minimum-weight kernel that makes dW[t]=0 for arbitrary t?

The message schedule is LINEAR over GF(2) (ignoring carries in addition):
  dW[i] = sigma1(dW[i-2]) XOR dW[i-7] XOR sigma0(dW[i-15]) XOR dW[i-16]

We build the 512x1536 GF(2) expansion matrix and use Gaussian elimination
to find kernels targeting specific schedule positions.

Goal: find a low-weight input difference that creates dW[t]=0 at
positions relevant to the SAT tail, potentially enabling a new attack
vector for sr=60.
"""

import numpy as np
import time


def build_schedule_expansion_matrix_gf2():
    """
    Build the 512x2048 GF(2) matrix M such that:
      W_expanded = M * M_input  (over GF(2))

    where M_input is the 512-bit input (16 words x 32 bits, LSB first)
    and W_expanded is the 2048-bit full schedule (64 words x 32 bits).

    W[0..15] = M[0..15] (identity)
    W[i] = sigma1(W[i-2]) XOR W[i-7] XOR sigma0(W[i-15]) XOR W[i-16]
    """

    # sigma0(x) = ROTR(x,7) XOR ROTR(x,18) XOR SHR(x,3)
    # sigma1(x) = ROTR(x,17) XOR ROTR(x,19) XOR SHR(x,10)
    # These are LINEAR over GF(2).

    def rotr_matrix(n):
        """32x32 rotation matrix (right rotation by n)."""
        M = np.zeros((32, 32), dtype=np.uint8)
        for i in range(32):
            M[i][(i + n) % 32] = 1
        return M

    def shr_matrix(n):
        """32x32 shift right matrix."""
        M = np.zeros((32, 32), dtype=np.uint8)
        for i in range(32 - n):
            M[i][i + n] = 1
        return M

    sigma0_mat = (rotr_matrix(7) ^ rotr_matrix(18) ^ shr_matrix(3)) % 2
    sigma1_mat = (rotr_matrix(17) ^ rotr_matrix(19) ^ shr_matrix(10)) % 2

    # Build the full schedule as a function of the 16 input words.
    # W[i] is represented as a 32x512 binary matrix (each row is a bit,
    # each column is an input bit).

    # W[i] has 32 bits, each expressed as a linear combination of 512 input bits.
    W = [None] * 64

    # W[0..15] = identity blocks
    for i in range(16):
        W[i] = np.zeros((32, 512), dtype=np.uint8)
        for bit in range(32):
            W[i][bit][i * 32 + bit] = 1

    # W[16..63] via recurrence
    for i in range(16, 64):
        # dW[i] = sigma1(dW[i-2]) + dW[i-7] + sigma0(dW[i-15]) + dW[i-16]
        # Over GF(2), + is XOR
        term1 = (sigma1_mat @ W[i - 2]) % 2
        term2 = W[i - 7]
        term3 = (sigma0_mat @ W[i - 15]) % 2
        term4 = W[i - 16]
        W[i] = (term1 ^ term2 ^ term3 ^ term4) % 2

    return W


def find_kernel_for_positions(W, target_positions):
    """
    Find a low-weight input difference dM that makes dW[t]=0
    for all t in target_positions.

    This is a system of linear equations over GF(2):
      For each t in target_positions: W[t] * dM = 0 (mod 2)

    The solution space is the null space of the matrix formed by
    stacking the W[t] rows.

    Returns the null space basis vectors.
    """

    # Stack the constraint matrices
    rows = []
    for t in target_positions:
        for bit in range(32):
            rows.append(W[t][bit])

    A = np.array(rows, dtype=np.uint8)
    n_constraints, n_vars = A.shape

    print(f"  System: {n_constraints} equations x {n_vars} variables over GF(2)")

    # Gaussian elimination over GF(2)
    A = A.copy()
    pivot_cols = []
    row = 0
    for col in range(n_vars):
        # Find pivot
        found = False
        for r in range(row, n_constraints):
            if A[r, col]:
                found = True
                A[[row, r]] = A[[r, row]]
                break
        if not found:
            continue
        pivot_cols.append(col)
        # Eliminate
        for r in range(n_constraints):
            if r != row and A[r, col]:
                A[r] = (A[r] ^ A[row]) % 2
        row += 1

    rank = len(pivot_cols)
    null_dim = n_vars - rank
    print(f"  Rank: {rank}, Null space dimension: {null_dim}")

    # Extract null space basis
    # Free variables: those NOT in pivot_cols
    free_cols = [c for c in range(n_vars) if c not in pivot_cols]

    null_basis = []
    for fc in free_cols[:min(100, len(free_cols))]:  # Limit for sanity
        x = np.zeros(n_vars, dtype=np.uint8)
        x[fc] = 1
        # Back-substitute
        for i in range(rank - 1, -1, -1):
            s = 0
            for j in range(n_vars):
                if j != pivot_cols[i]:
                    s ^= A[i, j] & x[j]
            x[pivot_cols[i]] = s
        null_basis.append(x)

    return null_basis, rank, null_dim


def vector_to_message_diff(vec):
    """Convert a 512-bit vector to 16 x 32-bit word differences."""
    words = []
    for i in range(16):
        val = 0
        for bit in range(32):
            if vec[i * 32 + bit]:
                val |= (1 << bit)
        words.append(val)
    return words


def hamming_weight(words):
    """Total Hamming weight of a list of 32-bit words."""
    return sum(bin(w).count('1') for w in words)


def count_nonzero_words(words):
    """Count non-zero words."""
    return sum(1 for w in words if w != 0)


def main():
    print("=" * 70, flush=True)
    print("GF(2) Kernel Search for SHA-256 Schedule", flush=True)
    print("=" * 70, flush=True)

    print("\nBuilding schedule expansion matrix...", flush=True)
    t0 = time.time()
    W = build_schedule_expansion_matrix_gf2()
    print(f"  Built in {time.time() - t0:.2f}s", flush=True)

    # Verify: MSB kernel should give dW[16..23] = 0
    print("\n--- Verification: MSB kernel ---", flush=True)
    msb_kernel = np.zeros(512, dtype=np.uint8)
    msb_kernel[0 * 32 + 31] = 1  # dM[0] bit 31 (MSB)
    msb_kernel[9 * 32 + 31] = 1  # dM[9] bit 31 (MSB)

    for t in range(16, 32):
        dW_t = (W[t] @ msb_kernel) % 2
        hw = int(np.sum(dW_t))
        if t < 24 or hw == 0:
            print(f"  dW[{t}]: hw={hw} {'<-- ZERO' if hw == 0 else ''}", flush=True)

    # Search 1: Kernels that zero out late schedule positions
    print("\n--- Search 1: Kernels for late schedule zeros ---", flush=True)
    target_sets = [
        [55, 56],           # da[55]=da[56]=0 equivalent in schedule
        [54, 55, 56],       # extend further back
        [55, 56, 57],       # target the SAT boundary
        [53, 54, 55, 56],   # even more
        [56],               # just W[56]=0
        [57],               # just W[57]=0
    ]

    for targets in target_sets:
        print(f"\n  Target: dW[{','.join(str(t) for t in targets)}] = 0", flush=True)
        null_basis, rank, null_dim = find_kernel_for_positions(W, targets)

        if null_dim == 0:
            print(f"  No solution exists! (full rank system)", flush=True)
            continue

        # Find minimum-weight kernel
        best_hw = 999
        best_kernel = None
        best_nwords = 99

        # Try individual basis vectors
        for v in null_basis:
            msg = vector_to_message_diff(v)
            hw = hamming_weight(msg)
            nw = count_nonzero_words(msg)
            if hw > 0 and (nw < best_nwords or (nw == best_nwords and hw < best_hw)):
                best_hw = hw
                best_nwords = nw
                best_kernel = msg

        # Try XOR combinations of 2 basis vectors (for lower weight)
        if len(null_basis) >= 2:
            for i in range(min(50, len(null_basis))):
                for j in range(i + 1, min(50, len(null_basis))):
                    v = (null_basis[i] ^ null_basis[j]) % 2
                    msg = vector_to_message_diff(v)
                    hw = hamming_weight(msg)
                    nw = count_nonzero_words(msg)
                    if hw > 0 and (nw < best_nwords or (nw == best_nwords and hw < best_hw)):
                        best_hw = hw
                        best_nwords = nw
                        best_kernel = msg

        if best_kernel:
            print(f"  Best kernel: {best_nwords} nonzero words, hw={best_hw}", flush=True)
            for i, w in enumerate(best_kernel):
                if w:
                    print(f"    dM[{i}] = 0x{w:08x} (hw={bin(w).count('1')})", flush=True)

            # Verify: compute dW at target positions
            v = np.zeros(512, dtype=np.uint8)
            for i in range(16):
                for bit in range(32):
                    if (best_kernel[i] >> bit) & 1:
                        v[i * 32 + bit] = 1
            print(f"  Verification:", flush=True)
            for t in targets:
                dW_t = (W[t] @ v) % 2
                hw = int(np.sum(dW_t))
                print(f"    dW[{t}]: hw={hw} {'OK' if hw == 0 else 'FAIL'}", flush=True)

            # Also show what happens at other late positions
            print(f"  Other late positions:", flush=True)
            for t in range(48, 64):
                dW_t = (W[t] @ v) % 2
                hw = int(np.sum(dW_t))
                if hw == 0:
                    print(f"    dW[{t}]: hw={hw} <-- BONUS ZERO", flush=True)

    # Search 2: Which single late positions CAN be zeroed with 2-word kernels?
    print("\n\n--- Search 2: 2-word kernels for individual late positions ---", flush=True)
    print("  (Looking for 2-word input differences that zero specific dW[t])", flush=True)

    for t in range(48, 64):
        null_basis, rank, null_dim = find_kernel_for_positions(W, [t])

        # Find lowest-weight 2-word kernel in null space
        best_2word = None
        best_2word_hw = 999

        for v in null_basis[:100]:
            msg = vector_to_message_diff(v)
            nw = count_nonzero_words(msg)
            hw = hamming_weight(msg)
            if nw <= 2 and hw > 0 and hw < best_2word_hw:
                best_2word = msg
                best_2word_hw = hw

        if len(null_basis) >= 2:
            for i in range(min(50, len(null_basis))):
                for j in range(i + 1, min(50, len(null_basis))):
                    v = (null_basis[i] ^ null_basis[j]) % 2
                    msg = vector_to_message_diff(v)
                    nw = count_nonzero_words(msg)
                    hw = hamming_weight(msg)
                    if nw <= 2 and hw > 0 and hw < best_2word_hw:
                        best_2word = msg
                        best_2word_hw = hw

        status = f"hw={best_2word_hw}" if best_2word else "none found"
        marker = " <-- !" if best_2word and best_2word_hw <= 4 else ""
        print(f"  dW[{t}]=0: dim={null_dim}, best 2-word: {status}{marker}", flush=True)


if __name__ == "__main__":
    main()
