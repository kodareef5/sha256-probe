#!/usr/bin/env python3
"""
Step 2: Per-Round Degree Profile

Map how algebraic degree grows round-by-round through the 7-round tail.

Methodology:
- For each round r (57-63), the free variables are W[57..min(60,r)]
- At round 57: 1 free word (N bits per message)
- At round 58: 2 free words (2N bits per message)
- At round 59: 3 free words (3N bits per message)
- At round 60-63: 4 free words (4N bits per message)

We measure degree via the RESTRICTION TEST:
Fix all but k free bits, check if each output bit changes.
If fixing (n-k) bits always makes output constant, degree ≤ k.

IMPORTANT: We measure degree NORMALIZED by input dimension:
  effective_degree = degree / n_free_bits
A value near 1.0 means "full degree" (maximally complex).
A value near 0 means "nearly linear" (exploitable).

We also measure separately:
- Difference function: state1 XOR state2
- Individual message: state1 alone
- Cascade words only: fix W[58], W[59], vary W[57] + W[60]
- Compatibility words only: fix W[57], W[60], vary W[58] + W[59]
"""

import sys, os, time, random
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from lib.sha256 import *


def eval_state_at_round(state, W_pre, w_free_list, target_round, N=32):
    """
    Evaluate state after target_round given free words.
    w_free_list: list of free words for rounds 57, 58, ...
    target_round: 57-63
    Returns: state tuple (a,b,c,d,e,f,g,h)
    """
    MASK_N = (1 << N) - 1 if N < 32 else 0xFFFFFFFF

    # Build full schedule
    n_free = len(w_free_list)
    schedule = list(w_free_list)

    # Pad with schedule-determined words if needed
    while len(schedule) < 7:
        idx = 57 + len(schedule)
        if idx == 61 and n_free <= 4:
            w = add(sigma1(schedule[2]), W_pre[54], sigma0(W_pre[46]), W_pre[45])
        elif idx == 60 and n_free <= 3:
            w = add(sigma1(schedule[1]), W_pre[53], sigma0(W_pre[45]), W_pre[44])
        elif idx == 62:
            w = add(sigma1(schedule[3 if n_free >= 4 else len(schedule)-1]),
                    W_pre[55], sigma0(W_pre[47]), W_pre[46])
        elif idx == 63:
            w = add(sigma1(schedule[4 if n_free >= 5 else len(schedule)-1]),
                    W_pre[56], sigma0(W_pre[48]), W_pre[47])
        else:
            w = 0  # shouldn't reach here
        schedule.append(w & MASK_N)

    # Run rounds
    a, b, c, d, e, f, g, h = state
    n_rounds = target_round - 56  # rounds 57..target_round
    for i in range(n_rounds):
        T1 = add(h, Sigma1(e), Ch(e, f, g), K[57 + i], schedule[i])
        T2 = add(Sigma0(a), Maj(a, b, c))
        h, g, f, e, d, c, b, a = g, f, e, add(d, T1), c, b, a, add(T1, T2)

    return (a, b, c, d, e, f, g, h)


def restriction_degree_test(state1, state2, W1_pre, W2_pre,
                            target_round, n_free_words,
                            N=8, n_samples=10000, n_trials=50):
    """
    Estimate degree of each state-difference bit at target_round
    as a function of n_free_words free schedule words.

    Method: For each k, fix (total_free - k) bits, flip the remaining k.
    If output changes, the function depends on those k bits.
    """
    MASK_N = (1 << N) - 1 if N < 32 else 0xFFFFFFFF
    n_free_bits = n_free_words * N * 2  # both messages

    print(f"\n  Round {target_round}, {n_free_words} free words ({n_free_bits} free bits):")

    # For each k, measure fraction of output bits that are "unfixed"
    k_values = [1, 2, 3, 4, 6, 8, 12, 16, 24, 32]
    k_values = [k for k in k_values if k <= n_free_bits]

    results = {}
    for k in k_values:
        unchanged_counts = [0] * (8 * N)

        for trial in range(n_trials):
            # Random base point
            base_w1 = [random.getrandbits(N) & MASK_N for _ in range(n_free_words)]
            base_w2 = [random.getrandbits(N) & MASK_N for _ in range(n_free_words)]

            base_s1 = eval_state_at_round(state1, W1_pre, base_w1, target_round, N)
            base_s2 = eval_state_at_round(state2, W2_pre, base_w2, target_round, N)
            base_diff = [base_s1[r] ^ base_s2[r] for r in range(8)]

            # Pick k random free bit positions to flip
            positions = random.sample(range(n_free_bits), min(k, n_free_bits))

            any_change = [False] * (8 * N)
            for pos in positions:
                flip_w1 = list(base_w1)
                flip_w2 = list(base_w2)

                # Decode position: which message, which word, which bit
                if pos < n_free_words * N:
                    # Message 1
                    word_idx = pos // N
                    bit_idx = pos % N
                    flip_w1[word_idx] ^= (1 << bit_idx)
                else:
                    # Message 2
                    adj_pos = pos - n_free_words * N
                    word_idx = adj_pos // N
                    bit_idx = adj_pos % N
                    flip_w2[word_idx] ^= (1 << bit_idx)

                flip_s1 = eval_state_at_round(state1, W1_pre, flip_w1, target_round, N)
                flip_s2 = eval_state_at_round(state2, W2_pre, flip_w2, target_round, N)

                for reg in range(8):
                    changed = (base_s1[reg] ^ flip_s1[reg]) | (base_s2[reg] ^ flip_s2[reg])
                    diff_changed = base_diff[reg] ^ (flip_s1[reg] ^ flip_s2[reg])
                    for b in range(N):
                        if (diff_changed >> b) & 1:
                            any_change[reg * N + b] = True

            for i in range(8 * N):
                if not any_change[i]:
                    unchanged_counts[i] += 1

        avg_unchanged = sum(unchanged_counts) / (n_trials * 8 * N)
        pct = 100 * avg_unchanged
        results[k] = pct

    # Print summary
    print(f"    {'k':>4} {'% unchanged':>12} {'interpretation':>30}")
    for k in k_values:
        pct = results[k]
        interp = ""
        if pct > 90:
            interp = "degree > k (most bits unaffected)"
        elif pct > 50:
            interp = "degree ~ k (some bits affected)"
        elif pct > 10:
            interp = "degree < k (most bits affected)"
        else:
            interp = "degree << k (all bits affected)"
        print(f"    {k:4d} {pct:11.1f}% {interp:>30}")

    # Estimate effective degree: smallest k where < 10% unchanged
    est_degree = n_free_bits  # default: full degree
    for k in k_values:
        if results[k] < 10:
            est_degree = k
            break

    print(f"    Estimated degree: ~{est_degree} / {n_free_bits} free bits "
          f"({100*est_degree/n_free_bits:.0f}% of maximum)")

    return results, est_degree


def per_round_profile(N=8, n_trials=100):
    """Run the full per-round degree profile."""
    MASK_N = (1 << N) - 1 if N < 32 else 0xFFFFFFFF

    # Find candidate
    if N < 32:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
        spec = __import__('50_precision_homotopy')
        sha = spec.MiniSHA256(N)
        m0, s1, s2, W1, W2 = sha.find_m0()
        if m0 is None:
            print(f"No candidate at N={N}")
            return
        state1, state2 = s1, s2
        W1_pre, W2_pre = W1[:57], W2[:57]
        print(f"Candidate: M[0]=0x{m0:x} at N={N}")
    else:
        M1 = [0x17149975] + [0xffffffff] * 15
        M2 = list(M1); M2[0] ^= 0x80000000; M2[9] ^= 0x80000000
        state1, W1_pre = precompute_state(M1)
        state2, W2_pre = precompute_state(M2)
        print(f"Candidate: M[0]=0x17149975 at N={N}")

    print(f"\nPer-Round Degree Profile (N={N})")
    print(f"=" * 60)

    # Profile at each round
    round_degrees = {}
    for target_round in range(57, 64):
        n_free = min(target_round - 56, 4)  # 1 word at r57, 2 at r58, ..., 4 at r60+
        results, est_deg = restriction_degree_test(
            state1, state2, W1_pre, W2_pre,
            target_round, n_free, N=N, n_trials=n_trials)
        round_degrees[target_round] = est_deg

    print(f"\n{'='*60}")
    print(f"DEGREE GROWTH SUMMARY (N={N})")
    print(f"{'='*60}")
    print(f"{'Round':>6} {'Free words':>11} {'Free bits':>10} {'Est degree':>11} {'% of max':>9}")
    for r in range(57, 64):
        n_free = min(r - 56, 4)
        n_bits = n_free * N * 2
        deg = round_degrees[r]
        pct = 100 * deg / n_bits if n_bits > 0 else 0
        marker = ""
        if pct < 50:
            marker = " ← LOW"
        print(f"{r:6d} {n_free:11d} {n_bits:10d} {deg:11d} {pct:8.0f}%{marker}")

    return round_degrees


if __name__ == "__main__":
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    n_trials = int(sys.argv[2]) if len(sys.argv) > 2 else 100

    random.seed(42)
    per_round_profile(N=N, n_trials=n_trials)
