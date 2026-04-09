#!/usr/bin/env python3
"""
lattice_additions.py — Lattice reduction on modular addition chains (Issue #15)

The 7-round SHA-256 tail has ~30 modular additions. Each addition
a + b = c (mod 2^32) defines a lattice constraint. We build a lattice
from these constraints and run LLL to find short vectors — these
correspond to input combinations where carries don't propagate far.

If short vectors exist, they reveal "easy directions" in the free word
space that a SAT solver can't see.

Usage: python3 lattice_additions.py
"""

import sys, os
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from lib.sha256 import *


def analyze_addition_chain(m0=0x17149975, fill=0xFFFFFFFF):
    """
    Trace the modular additions in the 7-round tail and build
    a system of equations over Z (before reduction mod 2^32).

    Each SHA-256 round computes:
      T1 = h + Sigma1(e) + Ch(e,f,g) + K[i] + W[i]  (5-way addition)
      T2 = Sigma0(a) + Maj(a,b,c)                    (2-way addition)
      e_new = d + T1                                  (2-way)
      a_new = T1 + T2                                 (2-way)

    The nonlinear functions (Sigma, Ch, Maj) are bitwise, not additions.
    But their OUTPUTS feed into additions. So we can treat them as
    "oracle values" and build a lattice from the addition structure alone.
    """
    M1 = [m0] + [fill] * 15
    M2 = list(M1); M2[0] ^= 0x80000000; M2[9] ^= 0x80000000
    s1, W1_pre = precompute_state(M1)
    s2, W2_pre = precompute_state(M2)

    print(f"=== Lattice Analysis of 7-Round Tail ===")
    print(f"Candidate: M[0]=0x{m0:08x}, fill=0x{fill:08x}")
    print()

    # The DIFFERENCE equations are what matter for collision.
    # For each addition a + b = c (mod 2^32):
    #   da + db + carry_diff = dc (mod 2^32)
    #
    # The carry_diff depends nonlinearly on exact values.
    # But in the XOR-differential model (ignoring carries):
    #   da XOR db = dc  (F_2-linear approximation)
    #
    # The gap between XOR-linear and modular-arithmetic is
    # exactly the carry propagation — which is what makes SAT hard.
    #
    # Lattice approach: treat the problem over Z (integers) instead of Z/2^32.
    # The modular reduction is a lattice constraint: c = a + b + k*2^32 for some k.

    # Count additions per round
    print("Addition structure per round:")
    print("  T1 = h + Sigma1(e) + Ch(e,f,g) + K + W    (5 inputs)")
    print("  T2 = Sigma0(a) + Maj(a,b,c)                (2 inputs)")
    print("  e_new = d + T1                              (2 inputs)")
    print("  a_new = T1 + T2                             (2 inputs)")
    print(f"  Per round: 4 addition operations, ~11 addition inputs")
    print(f"  7 rounds: ~28 addition operations")
    print()

    # For the SCHEDULE part:
    # W[61] = sigma1(W[59]) + W[54] + sigma0(W[46]) + W[45]  (4-way)
    # W[62] = sigma1(W[60]) + W[55] + sigma0(W[47]) + W[46]  (4-way)
    # W[63] = sigma1(W[61]) + W[56] + sigma0(W[48]) + W[47]  (4-way)
    print("Schedule additions: 3 equations × 4 inputs each = 12 more additions")
    print(f"Total: ~40 modular additions in the full tail")
    print()

    # Build a simple lattice: differences propagation
    # For the collision, we need all 8 output difference registers to be 0.
    # The free variables are dW[57], dW[58], dW[59], dW[60] (each 32-bit).
    #
    # Over Z, each output register is a POLYNOMIAL in the dW values,
    # with nonlinear terms from Sigma/Ch/Maj. If we linearize
    # (drop all nonlinear terms), we get an integer lattice problem.

    # Compute the F_2-linear Jacobian of the tail
    # (i.e., which output bits depend on which input bits, ignoring carries)
    print("Computing F_2-linear Jacobian (carry-free approximation)...")

    n_free = 4  # dW[57..60]
    n_bits = 32

    # For each free word bit, trace through the XOR-linear approximation
    # of 7 rounds and measure which output diff bits flip.
    jacobian = np.zeros((n_free * n_bits, 8 * n_bits), dtype=np.int8)

    for word_idx in range(n_free):
        for bit_pos in range(n_bits):
            # Set dW[57+word_idx] to have only this bit set
            dW_test = [0] * 4
            dW_test[word_idx] = 1 << bit_pos

            # Trace through schedule (XOR-linear)
            # dW[61] = sigma1(dW[59]) XOR dW[54] XOR sigma0(dW[46]) XOR dW[45]
            # Since dW[54], sigma0(dW[46]), dW[45] are all 0 (pre-schedule diffs are fixed):
            dW = list(dW_test)  # [dW57, dW58, dW59, dW60]

            # dW[61] depends on dW[59] via sigma1
            dW61 = sigma1(dW[2])  # sigma1 is F_2-linear
            dW.append(dW61)
            # dW[62] depends on dW[60] via sigma1
            dW62 = sigma1(dW[3])
            dW.append(dW62)
            # dW[63] depends on dW[61] via sigma1
            dW63 = sigma1(dW61)
            dW.append(dW63)

            # Now trace through 7 compression rounds (XOR-linear approx)
            # In XOR-linear model:
            #   dT1 = dh XOR dSigma1(de) XOR dCh(de,df,dg) XOR dW[i]
            #   dT2 = dSigma0(da) XOR dMaj(da,db,dc)
            #   de_new = dd XOR dT1
            #   da_new = dT1 XOR dT2
            #
            # For XOR-linear: dCh(de,df,dg) ≈ de XOR df XOR dg (loose approx)
            #                 dMaj(da,db,dc) ≈ da XOR db XOR dc (loose approx)
            #
            # These are VERY loose — Ch and Maj are NOT linear. But this gives
            # the lattice structure.

            da, db, dc, dd, de, df, dg, dh = 0, 0, 0, 0, 0, 0, 0, 0
            # da=0 by candidate property (da[56]=0)

            for r in range(7):
                dSig1 = Sigma1(de) if de != 0 else 0  # Sigma1 is F_2-linear
                dCh = de ^ df ^ dg  # XOR approximation of Ch differential
                dSig0 = Sigma0(da) if da != 0 else 0
                dMaj = da ^ db ^ dc  # XOR approximation of Maj differential

                dT1 = dh ^ dSig1 ^ dCh ^ dW[r]
                dT2 = dSig0 ^ dMaj
                da_new = dT1 ^ dT2
                de_new = dd ^ dT1

                dh, dg, df, de, dd, dc, db, da = dg, df, de, de_new, dc, db, da, da_new

            # Record output diff bits
            state_diff = [da, db, dc, dd, de, df, dg, dh]
            in_idx = word_idx * n_bits + bit_pos
            for reg in range(8):
                for b in range(n_bits):
                    if (state_diff[reg] >> b) & 1:
                        out_idx = reg * n_bits + b
                        jacobian[in_idx, out_idx] = 1

    # Analyze the Jacobian
    rank = np.linalg.matrix_rank(jacobian.astype(float))
    print(f"\nF_2-linear Jacobian: {jacobian.shape[0]}×{jacobian.shape[1]}")
    print(f"Rank: {rank} of {min(jacobian.shape)}")
    print(f"Null space dimension: {jacobian.shape[0] - rank}")

    # Row weight distribution (how many output bits does each input bit affect?)
    row_weights = jacobian.sum(axis=1)
    print(f"\nInput bit influence (row weights):")
    print(f"  Mean: {row_weights.mean():.1f}")
    print(f"  Min: {row_weights.min()}, Max: {row_weights.max()}")

    # Column weight distribution (how many input bits affect each output bit?)
    col_weights = jacobian.sum(axis=0)
    print(f"\nOutput bit sensitivity (column weights):")
    print(f"  Mean: {col_weights.mean():.1f}")
    print(f"  Min: {col_weights.min()}, Max: {col_weights.max()}")
    weakest = np.argsort(col_weights)[:10]
    print(f"  Weakest output bits (fewest inputs):")
    regs = ['a','b','c','d','e','f','g','h']
    for idx in weakest:
        reg = idx // 32
        bit = idx % 32
        print(f"    d{regs[reg]}[63] bit {bit}: influenced by {col_weights[idx]} input bits")

    # SVD for effective rank
    U, sv, Vt = np.linalg.svd(jacobian.astype(float), full_matrices=False)
    print(f"\nSVD top 10 singular values: {sv[:10].round(2)}")
    energy = np.cumsum(sv**2) / np.sum(sv**2)
    rank_90 = np.searchsorted(energy, 0.9) + 1
    print(f"Rank for 90% energy: {rank_90}")

    return jacobian, rank


if __name__ == "__main__":
    jacobian, rank = analyze_addition_chain()
