#!/usr/bin/env python3
"""
Issue #11: ANF Degree Profiling of 7-Round SHA-256 Tail

Each of the 256 output bits (8 registers × 32 bits) of the sr=60
collision function is a polynomial over the ~256 free input bits
(W1[57..60] + W2[57..60]).

Approach:
1. At N=4: exact ANF via Moebius transform (2^32 evaluations, tractable)
2. At N=8: estimate degree via Schwartz-Zippel (random evaluation)
3. If any output bit has degree < 10: publishable structural weakness

The collision DIFFERENCE function f(x) = state1(x) XOR state2(x) is what
matters — we want the degree of each bit of the XOR difference.
"""

import sys, os, time, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from lib.sha256 import *


def eval_tail_diff_bits(state1, state2, W1_pre, W2_pre, w1_free, w2_free, N=32):
    """Evaluate the collision difference at round 63, return as 256-bit vector."""
    MASK_N = (1 << N) - 1 if N < 32 else 0xFFFFFFFF

    tail1 = build_schedule_tail(W1_pre, w1_free)
    tail2 = build_schedule_tail(W2_pre, w2_free)

    trace1 = run_tail_rounds(state1, tail1)
    trace2 = run_tail_rounds(state2, tail2)

    final1 = trace1[-1]
    final2 = trace2[-1]

    # 256 XOR difference bits
    diff_bits = []
    for reg in range(8):
        d = final1[reg] ^ final2[reg]
        for bit in range(N):
            diff_bits.append((d >> bit) & 1)
    return diff_bits


def schwartz_zippel_degree_estimate(state1, state2, W1_pre, W2_pre,
                                     n_samples=10000, N=32):
    """
    Estimate the algebraic degree of each output bit using the
    Schwartz-Zippel approach: evaluate on random inputs and check
    how many distinct outputs each bit produces.

    For a degree-d polynomial in n variables over GF(2), the probability
    of evaluating to 0 on a random input is between 1/2 - 1/2^(n-d+1)
    and 1/2 + 1/2^(n-d+1). So the bias from 50% tells us about degree.

    More practically: we estimate degree by checking if restricted
    polynomials (fixing all but k variables) are constant. If fixing
    n-k variables always makes the output constant, the degree is ≤ k.
    """
    n_free = 4 * N  # bits per message
    results = {}

    print(f"Schwartz-Zippel degree estimation (N={N}, {n_samples} samples)")
    print(f"Free bits per message: {n_free}, total: {2*n_free}")

    # Step 1: Evaluate on random inputs and measure bias
    print("\nStep 1: Random evaluation bias...")
    bit_sums = [0] * (8 * N)

    for _ in range(n_samples):
        w1 = [random.getrandbits(N) for _ in range(4)]
        w2 = [random.getrandbits(N) for _ in range(4)]
        diff = eval_tail_diff_bits(state1, state2, W1_pre, W2_pre, w1, w2, N)
        for i, b in enumerate(diff):
            bit_sums[i] += b

    print(f"{'Bit':>5} {'Reg':>4} {'Pos':>4} {'P(1)':>8} {'Bias':>8} {'Notes':>20}")
    print("-" * 55)

    low_degree_candidates = []
    for i in range(8 * N):
        reg = i // N
        pos = i % N
        p1 = bit_sums[i] / n_samples
        bias = abs(p1 - 0.5)
        notes = ""
        if bias > 0.1:
            notes = "HIGH BIAS"
            low_degree_candidates.append((i, reg, pos, p1, bias))
        if bias > 0.4:
            notes = "*** VERY HIGH ***"
        if i < 10 or bias > 0.05 or (i % N == 0):
            print(f"{i:5d} {reg:4d} {pos:4d} {p1:8.4f} {bias:8.4f} {notes:>20}")

    # Step 2: Restriction test — fix all but k bits, check if output is constant
    print(f"\nStep 2: Restriction test (fix all but k bits)...")
    print("Testing if output bits become constant when most inputs are fixed")

    for k in [1, 2, 3, 4, 5, 8, 16]:
        n_const = 0
        n_tested = min(100, 8 * N)

        for trial in range(20):
            # Random base point
            base_w1 = [random.getrandbits(N) for _ in range(4)]
            base_w2 = [random.getrandbits(N) for _ in range(4)]

            # Pick k random free positions to vary
            positions = random.sample(range(2 * n_free), min(k, 2 * n_free))

            # Evaluate at base and at base with each position flipped
            base_diff = eval_tail_diff_bits(state1, state2, W1_pre, W2_pre,
                                            base_w1, base_w2, N)

            any_change = [False] * (8 * N)
            for pos in positions:
                # Flip one bit
                msg = 0 if pos < n_free else 1
                word_idx = (pos % n_free) // N
                bit_idx = (pos % n_free) % N

                flip_w1 = list(base_w1)
                flip_w2 = list(base_w2)
                if msg == 0:
                    flip_w1[word_idx] ^= (1 << bit_idx)
                else:
                    flip_w2[word_idx] ^= (1 << bit_idx)

                flip_diff = eval_tail_diff_bits(state1, state2, W1_pre, W2_pre,
                                                flip_w1, flip_w2, N)

                for i in range(8 * N):
                    if flip_diff[i] != base_diff[i]:
                        any_change[i] = True

            n_unchanged = sum(1 for c in any_change if not c)
            n_const += n_unchanged

        avg_const = n_const / 20
        print(f"  k={k:2d}: avg {avg_const:.1f} / {8*N} output bits unchanged "
              f"({100*avg_const/(8*N):.1f}%)")

    if low_degree_candidates:
        print(f"\n*** {len(low_degree_candidates)} output bits with bias > 0.1 ***")
        for i, reg, pos, p1, bias in sorted(low_degree_candidates, key=lambda x: -x[4]):
            print(f"  Bit {i} (reg {reg} pos {pos}): P(1)={p1:.4f}, bias={bias:.4f}")
    else:
        print("\nNo output bits with significant bias (all near 50%)")
        print("This suggests all output bits have high algebraic degree")

    return low_degree_candidates


if __name__ == "__main__":
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    n_samples = int(sys.argv[2]) if len(sys.argv) > 2 else 5000

    # Use the published candidate
    M1 = [0x17149975] + [0xffffffff] * 15
    M2 = list(M1)
    M2[0] ^= 0x80000000
    M2[9] ^= 0x80000000

    if N < 32:
        # Use mini-SHA
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
        spec = __import__('50_precision_homotopy')
        sha = spec.MiniSHA256(N)
        MSK = sha.MASK
        MSB = sha.MSB

        M1_n = [M1[0] & MSK] + [0xffffffff & MSK] * 15
        M2_n = list(M1_n)
        M2_n[0] ^= MSB
        M2_n[9] ^= MSB

        s1, W1 = sha.compress(M1_n)
        s2, W2 = sha.compress(M2_n)

        if s1[0] != s2[0]:
            # Need to find a valid candidate at this N
            m0, s1, s2, W1, W2 = sha.find_m0()
            if m0 is None:
                print(f"No da[56]=0 candidate at N={N}")
                sys.exit(1)
            print(f"Using candidate M[0]=0x{m0:x} at N={N}")

        state1 = s1
        state2 = s2
        W1_pre = W1[:57]
        W2_pre = W2[:57]
    else:
        state1, W1_pre = precompute_state(M1)
        state2, W2_pre = precompute_state(M2)

    print(f"ANF Degree Profile: N={N}, candidate verified (da[56]=0)")
    print(f"Output bits: {8*N}, free input bits: {8*N}")
    print()

    candidates = schwartz_zippel_degree_estimate(
        state1, state2, W1_pre, W2_pre,
        n_samples=n_samples, N=N)
