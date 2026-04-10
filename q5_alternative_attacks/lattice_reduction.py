#!/usr/bin/env python3
"""
Issue #15: Lattice Reduction on Modular Additions

Each modular addition a + b = c (mod 2^N) in the 7-round tail can be
viewed as a lattice constraint. The ~30 additions across 7 rounds form
a lattice problem in ~90 dimensions.

LLL/BKZ reduction finds short vectors — these correspond to "easy" input
combinations where carries don't propagate far.

This is how knapsack cryptosystems were broken. SHA-256's additions have
the same algebraic structure.

Approach:
1. Map the 7-round tail to a system of modular equations
2. Build the lattice basis matrix
3. Run LLL reduction
4. Analyze short vectors for collision-relevant structure
"""

import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from lib.sha256 import *

try:
    from sage.all import matrix, ZZ, QQ, vector, identity_matrix
    HAS_SAGE = True
except ImportError:
    HAS_SAGE = False

import numpy as np


def map_tail_additions(state1, state2, W1_pre, W2_pre, N=32):
    """
    Map all modular additions in the 7-round tail to a list of
    (a, b, c) triples where a + b = c (mod 2^N).

    Each round has:
      T1 = h + Sigma1(e) + Ch(e,f,g) + K[i] + W[i]  (5-input addition)
      T2 = Sigma0(a) + Maj(a,b,c)  (2-input addition)
      a_new = T1 + T2
      e_new = d + T1

    The non-linear parts (Sigma, Ch, Maj) are treated as known functions
    of the current state, which we can evaluate.
    """
    MASK_N = (1 << N) - 1 if N < 32 else 0xFFFFFFFF

    additions = []
    dependencies = []  # which free variables each addition depends on

    # For each round 57-63, trace the additions
    # We track symbolically which additions depend on free variables
    print(f"Mapping modular additions in 7-round tail (N={N})...")

    # Simulate with random free words to get concrete values
    # Then analyze the STRUCTURE of dependencies
    import random
    random.seed(42)

    w1_free = [random.getrandbits(N) & MASK_N for _ in range(4)]
    w2_free = [random.getrandbits(N) & MASK_N for _ in range(4)]

    tail1 = build_schedule_tail(W1_pre, w1_free)
    tail2 = build_schedule_tail(W2_pre, w2_free)

    # Count additions per round
    # Round i: 5 additions for T1 (h + Sig1 + Ch + K + W),
    #          1 addition for T2 (Sig0 + Maj),
    #          1 for a_new (T1 + T2),
    #          1 for e_new (d + T1)
    # = 8 additions per round × 2 messages × 7 rounds = 112 additions
    # But some are additions of constants (simplify away)

    n_additions = 0
    n_free_additions = 0  # additions involving at least one free variable

    a1, b1, c1, d1, e1, f1, g1, h1 = state1
    a2, b2, c2, d2, e2, f2, g2, h2 = state2

    for r in range(7):
        round_num = 57 + r
        W1_r = tail1[r]
        W2_r = tail2[r]

        # Message 1 additions
        sig1_1 = Sigma1(e1)
        ch_1 = Ch(e1, f1, g1)
        # T1 = h + Sigma1 + Ch + K + W (chain of 4 additions)
        t1_1 = add(h1, sig1_1)
        n_additions += 1
        t1_2 = add(t1_1, ch_1)
        n_additions += 1
        t1_3 = add(t1_2, K[round_num])
        n_additions += 1
        T1_1 = add(t1_3, W1_r)
        n_additions += 1
        if r < 4:  # W is free
            n_free_additions += 1

        sig0_1 = Sigma0(a1)
        maj_1 = Maj(a1, b1, c1)
        T2_1 = add(sig0_1, maj_1)
        n_additions += 1

        a1_new = add(T1_1, T2_1)
        n_additions += 1
        e1_new = add(d1, T1_1)
        n_additions += 1

        h1, g1, f1, e1, d1, c1, b1, a1 = g1, f1, e1, e1_new, c1, b1, a1, a1_new

        # Same for message 2
        sig1_2 = Sigma1(e2)
        ch_2 = Ch(e2, f2, g2)
        t2_1 = add(h2, sig1_2)
        t2_2 = add(t2_1, ch_2)
        t2_3 = add(t2_2, K[round_num])
        T1_2 = add(t2_3, W2_r)
        n_additions += 4

        sig0_2 = Sigma0(a2)
        maj_2 = Maj(a2, b2, c2)
        T2_2 = add(sig0_2, maj_2)
        n_additions += 1

        a2_new = add(T1_2, T2_2)
        n_additions += 1
        e2_new = add(d2, T1_2)
        n_additions += 1

        h2, g2, f2, e2, d2, c2, b2, a2 = g2, f2, e2, e2_new, c2, b2, a2, a2_new

    print(f"  Total additions: {n_additions}")
    print(f"  Free-variable additions: {n_free_additions}")
    print(f"  Additions per round: ~{n_additions/7:.1f}")

    return n_additions, n_free_additions


def build_lattice_basis(state1, state2, W1_pre, W2_pre, N=32):
    """
    Build a lattice basis from the modular addition constraints.

    The key idea: for the DIFFERENCE a1-a2, the additions become:
      dT1 = dh + dSigma1 + dCh + dW  (mod 2^N)

    Each of these is a modular equation in the free variable differences
    dW[57..60]. We can express the collision constraint as:
      A * x = b  (mod 2^N)

    where x = (dW[57], dW[58], dW[59], dW[60]) and A encodes the
    round-by-round propagation.

    LLL on the lattice [I | A^T] finds short vectors corresponding to
    inputs where the carry propagation is minimal.
    """
    MASK_N = (1 << N) - 1 if N < 32 else 0xFFFFFFFF

    print(f"\nBuilding lattice basis (N={N})...")

    # The collision constraint is:
    # final_state1(W1[57..60]) = final_state2(W2[57..60])
    #
    # This is 8*N equations in 8*N unknowns (4 words × N bits × 2 messages).
    # But the equations are non-linear (due to Ch, Maj, Sigma).
    #
    # Linearization: treat the XOR/rotation parts as linear (they are over GF(2))
    # and the additions as lattice constraints (they are over Z/2^N Z).
    #
    # The lattice dimension is:
    #   8 free words (4 per message) × N bits = 8N
    #   + 8 output constraint words × N bits = 8N
    #   Total: 16N dimensions
    #
    # For N=32: 512-dimensional lattice. LLL handles this in seconds.

    dim = 8 * N  # free variable bits (4 words × 2 messages × N bits)
    print(f"  Lattice dimension: {dim} (free variables)")

    # Compute the Jacobian: how does each free bit affect each output bit?
    # Use finite differences (flip each input bit, observe output changes)
    print(f"  Computing Jacobian via finite differences ({dim} input bits)...")

    t0 = time.time()

    # Base evaluation
    base_w1 = [0x12345678 & MASK_N] * 4
    base_w2 = [0x9abcdef0 & MASK_N] * 4

    tail1 = build_schedule_tail(W1_pre, base_w1)
    tail2 = build_schedule_tail(W2_pre, base_w2)
    trace1 = run_tail_rounds(state1, tail1)
    trace2 = run_tail_rounds(state2, tail2)
    base_diff = [trace1[-1][r] ^ trace2[-1][r] for r in range(8)]

    # Jacobian: J[i][j] = 1 if flipping input bit j changes output bit i
    jacobian = np.zeros((8 * N, dim), dtype=np.int8)

    for msg in [0, 1]:
        for word in range(4):
            for bit in range(N):
                col = msg * 4 * N + word * N + bit

                flip_w1 = list(base_w1)
                flip_w2 = list(base_w2)
                if msg == 0:
                    flip_w1[word] ^= (1 << bit)
                else:
                    flip_w2[word] ^= (1 << bit)

                tail1_f = build_schedule_tail(W1_pre, flip_w1)
                tail2_f = build_schedule_tail(W2_pre, flip_w2)
                trace1_f = run_tail_rounds(state1, tail1_f)
                trace2_f = run_tail_rounds(state2, tail2_f)

                for reg in range(8):
                    diff_f = trace1_f[-1][reg] ^ trace2_f[-1][reg]
                    changed = base_diff[reg] ^ diff_f
                    for b in range(N):
                        if (changed >> b) & 1:
                            row = reg * N + b
                            jacobian[row][col] = 1

    elapsed = time.time() - t0
    print(f"  Jacobian computed in {elapsed:.1f}s")

    # Analyze Jacobian
    rank = np.linalg.matrix_rank(jacobian.astype(float))
    density = np.sum(jacobian) / (jacobian.shape[0] * jacobian.shape[1])
    avg_deps = np.mean(np.sum(jacobian, axis=1))
    avg_influence = np.mean(np.sum(jacobian, axis=0))

    print(f"  Jacobian shape: {jacobian.shape}")
    print(f"  Rank: {rank} / {min(jacobian.shape)}")
    print(f"  Density: {density:.4f}")
    print(f"  Avg output dependencies: {avg_deps:.1f} input bits")
    print(f"  Avg input influence: {avg_influence:.1f} output bits")

    # Per-register analysis
    print(f"\n  Per-register influence:")
    for reg in range(8):
        reg_rows = jacobian[reg*N:(reg+1)*N, :]
        reg_rank = np.linalg.matrix_rank(reg_rows.astype(float))
        reg_density = np.sum(reg_rows) / (reg_rows.shape[0] * reg_rows.shape[1])
        print(f"    reg {reg} ({'abcdefgh'[reg]}): rank={reg_rank}, density={reg_density:.4f}")

    # Per-word input influence
    print(f"\n  Per-word input influence (which free words affect the most output bits):")
    for msg in [0, 1]:
        for word in range(4):
            cols = slice(msg*4*N + word*N, msg*4*N + (word+1)*N)
            word_influence = np.sum(jacobian[:, cols])
            print(f"    W{msg+1}[{57+word}]: {word_influence} total influences "
                  f"({word_influence/(N*8*N)*100:.1f}% of matrix)")

    if HAS_SAGE:
        print(f"\n  Running LLL reduction on GF(2) Jacobian...")
        M_sage = matrix(ZZ, jacobian.tolist())
        # Build lattice: [I | lambda * J^T] where lambda scales the constraint
        # LLL finds short vectors that approximately satisfy the constraints
        lam = 100  # constraint weight
        L = identity_matrix(ZZ, dim).augment(lam * M_sage.transpose())
        L_reduced = L.LLL()
        short_norms = sorted([v.norm().n() for v in L_reduced])
        print(f"  Shortest 5 vectors: {short_norms[:5]}")
    else:
        print(f"\n  Sage not available — skipping LLL reduction")
        print(f"  Install sagemath for full lattice analysis")

    return jacobian


if __name__ == "__main__":
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 32

    M1 = [0x17149975] + [0xffffffff] * 15
    M2 = list(M1)
    M2[0] ^= 0x80000000
    M2[9] ^= 0x80000000

    if N < 32:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
        spec = __import__('50_precision_homotopy')
        sha = spec.MiniSHA256(N)
        m0, s1, s2, W1, W2 = sha.find_m0()
        if m0 is None:
            print(f"No candidate at N={N}")
            sys.exit(1)
        state1, state2 = s1, s2
        W1_pre, W2_pre = W1[:57], W2[:57]
        print(f"Using candidate M[0]=0x{m0:x} at N={N}")
    else:
        state1, W1_pre = precompute_state(M1)
        state2, W2_pre = precompute_state(M2)

    print(f"Lattice Reduction Analysis: N={N}")
    print(f"Published candidate M[0]=0x17149975\n")

    n_add, n_free = map_tail_additions(state1, state2, W1_pre, W2_pre, N)
    jacobian = build_lattice_basis(state1, state2, W1_pre, W2_pre, N)
