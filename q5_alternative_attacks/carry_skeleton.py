#!/usr/bin/env python3
"""
Carry-Conditioned Linearization: Expose the Carry Skeleton

THE key insight from both Gemini 3.1 Pro and GPT-5.4 external reviews:

For modular addition z = x + y over 2^N:
  z_i = x_i XOR y_i XOR c_i
  c_{i+1} = maj(x_i, y_i, c_i)

Once carry bits c_i are fixed, z_i is LINEAR in x_i, y_i.

SHA-256's 7-round tail has ~14 modular additions per round × 7 rounds = ~98 additions.
Each addition has N carry bits. Total carry bits: ~98 × N.

But most carries are DETERMINED by the cascade constraints and constant state:
- Rounds 57-59: many operands are constant (precomputed state)
- Cascade-1 makes da57=0 (zeroes many carry differences)
- Schedule-determined rounds have fewer free additions

The question: how many carry bits are TRULY free (not determined)?
If it's ~20-30, the nonlinear skeleton is tiny and tractable.
If it's ~100+, carries don't help.

This script counts and characterizes the carry skeleton.
"""

import sys, os, time, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from lib.sha256 import *


def count_carry_skeleton(N_width=32):
    """Count the number of addition carry bits in the 7-round tail."""

    print(f"Carry Skeleton Analysis at N={N_width}")

    # SHA-256 round function additions:
    # T1 = h + Sigma1(e) + Ch(e,f,g) + K[r] + W[r]    -- 4 additions
    # T2 = Sigma0(a) + Maj(a,b,c)                       -- 1 addition
    # e_new = d + T1                                     -- 1 addition
    # a_new = T1 + T2                                    -- 1 addition
    # Total per round: 7 additions (but some combine as add(h,Sig1,Ch,K,W) = 4-way)

    # Actually counting distinct additions in our encoding:
    # add(h, Sigma1(e), Ch(e,f,g), K[r], W[r]) — this is a 5-input addition
    # Implemented as chain: ((h + Sigma1(e)) + Ch(e,f,g)) + (K[r] + W[r])
    # = 4 binary additions for T1
    # add(Sigma0(a), Maj(a,b,c)) — 1 binary addition for T2
    # d + T1 — 1 binary addition for e_new
    # T1 + T2 — 1 binary addition for a_new
    # Total per round: 7 binary additions

    adds_per_round = 7
    n_rounds = 7
    total_adds = adds_per_round * n_rounds
    total_carries = total_adds * N_width

    print(f"\n=== Addition Count ===")
    print(f"  Additions per round: {adds_per_round}")
    print(f"  Rounds: {n_rounds}")
    print(f"  Total binary additions: {total_adds}")
    print(f"  Carry bits per addition: {N_width}")
    print(f"  Total carry bits: {total_carries}")

    # Now: how many are determined by constants?
    # In rounds 57-63, the state entering round 57 is constant.
    # So at round 57:
    #   T1 = h56 + Sigma1(e56) + Ch(e56,f56,g56) + K[57] + W[57]
    # Here h56, Sigma1(e56), Ch(e56,f56,g56), K[57] are ALL constants.
    # Only W[57] is free. So T1 = C + W[57], and the carries of this
    # addition are DETERMINED by C and W[57]. That's one free operand.
    #
    # T2 = Sigma0(a56) + Maj(a56,b56,c56) = constant
    # e_new = d56 + T1 = constant + T1, carries determined by T1
    # a_new = T1 + T2, carries determined by T1

    # For each round, count: how many addition operands are free?
    print(f"\n=== Per-Round Free Operand Analysis ===")
    print(f"  (Each addition has 2 inputs; count how many are non-constant)")
    print()

    round_info = []
    for r in range(7):
        rnd = 57 + r
        # Determine which operands are free at this round
        # After round 56: state is constant
        # After round 57: a57, e57 depend on W[57] (1 free word)
        # After round 58: more state depends on W[57], W[58]
        # etc.

        if r == 0:
            # Round 57: state is constant, W[57] is free
            # T1 = (constant) + W[57] → 1 free operand per addition in T1 chain
            # T2 = constant → 0 free
            # e_new = constant + T1 → T1 has W[57] dependency
            # a_new = T1 + T2 → T1 has W[57] dependency
            free_operand_adds = 4  # the 4 additions in T1 chain each have 1 free input
            const_adds = 3  # T2, e_new offset, a_new offset (but T1 is already non-const)
            n_free_inputs_per_msg = 1  # just W[57]
        elif r == 1:
            # Round 58: state has a57(free), b57=a56(const), ..., e57(free)
            # More operands become free
            n_free_inputs_per_msg = 2  # W[57], W[58]
            free_operand_adds = 5
            const_adds = 2
        elif r == 2:
            # Round 59: more state bits free
            n_free_inputs_per_msg = 3
            free_operand_adds = 6
            const_adds = 1
        else:
            # Rounds 60-63: all state depends on free words
            n_free_inputs_per_msg = 4
            free_operand_adds = 7
            const_adds = 0

        # For the DIFFERENCE function (two messages):
        # If both operands are constant → carry difference = 0 (determined)
        # If one operand depends on free vars → carry difference may vary
        # Key: carry bits where BOTH messages' carries are independently free

        total_free_carries = free_operand_adds * N_width
        total_const_carries = const_adds * N_width

        round_info.append({
            'round': rnd,
            'free_adds': free_operand_adds,
            'const_adds': const_adds,
            'free_carries': total_free_carries,
            'const_carries': total_const_carries,
        })

        print(f"  Round {rnd}: {free_operand_adds} free + {const_adds} const additions"
              f" → {total_free_carries} free carries, {total_const_carries} determined")

    total_free = sum(r['free_carries'] for r in round_info)
    total_const = sum(r['const_carries'] for r in round_info)
    print(f"\n  TOTAL: {total_free} potentially free carries + {total_const} determined")
    print(f"  Out of {total_carries} total carry bits")

    # But this overcounts! Many "free" carries are actually determined
    # because their inputs are determined by previous round outputs.
    # The REAL question is: how many carry bits in the DIFFERENCE
    # (carry1 XOR carry2) are free?

    print(f"\n=== Carry Difference Analysis ===")
    print(f"  For two-message collision, the carry DIFFERENCE dc_i = c1_i XOR c2_i")
    print(f"  is what matters. dc_i = 0 when both messages have the same carry.")
    print()

    # At round 57, T1 = C + W[r]. The carry difference depends on W1[r] vs W2[r].
    # With cascade-1: W2[57] = W1[57] + const, so dW[57] is a constant.
    # This means the carry pattern of T1 at round 57 is determined by W1[57] alone.
    # But within T1's chain of additions, the carries still depend on W1[57]'s bits.

    # Key insight from GPT-5.4: the CARRY SKELETON is the set of carry bits
    # that cannot be determined from the message word bits and cascade constraints.
    # After conditioning on the carry skeleton, the rest is linear.

    # Let's estimate by simulation: for random inputs, how many carry differences
    # are actually non-constant?

    print(f"  Simulating carry difference variability...")
    print(f"  (Sample 10000 random inputs, check which carry diffs vary)")

    if N_width <= 8:
        import importlib
        spec = importlib.import_module('50_precision_homotopy')
        sha_mini = spec.MiniSHA256(N_width)
        MASK = sha_mini.MASK
        Kvals = sha_mini.K
        m0, s1, s2, W1p, W2p = sha_mini.find_m0()
        if m0 is None:
            print("No candidate"); return

        def get_carries(a_val, b_val, n_bits):
            """Compute carry bits for a + b mod 2^n."""
            carries = []
            c = 0
            for i in range(n_bits):
                ai = (a_val >> i) & 1
                bi = (b_val >> i) & 1
                c = (ai & bi) | (ai & c) | (bi & c)
                carries.append(c)
            return carries

        random.seed(42)
        n_samples = 10000
        # Track all carry bits across all rounds
        all_carry_diffs = {}  # (round, add_idx, bit) -> list of values

        for trial in range(n_samples):
            w1 = [random.randint(0, MASK) for _ in range(4)]
            w2 = [random.randint(0, MASK) for _ in range(4)]

            # Run both messages through 7 rounds, tracking carries
            a1,b1,c1,d1,e1,f1,g1,h1 = s1
            a2,b2,c2,d2,e2,f2,g2,h2 = s2

            # Build schedule
            W1 = list(w1)
            W2 = list(w2)
            W1.append((sha_mini.sigma1(w1[2]) + W1p[54] + sha_mini.sigma0(W1p[46]) + W1p[45]) & MASK)
            W2.append((sha_mini.sigma1(w2[2]) + W2p[54] + sha_mini.sigma0(W2p[46]) + W2p[45]) & MASK)
            W1.append((sha_mini.sigma1(w1[3]) + W1p[55] + sha_mini.sigma0(W1p[47]) + W1p[46]) & MASK)
            W2.append((sha_mini.sigma1(w2[3]) + W2p[55] + sha_mini.sigma0(W2p[47]) + W2p[46]) & MASK)
            W1.append((sha_mini.sigma1(W1[4]) + W1p[56] + sha_mini.sigma0(W1p[48]) + W1p[47]) & MASK)
            W2.append((sha_mini.sigma1(W2[4]) + W2p[56] + sha_mini.sigma0(W2p[48]) + W2p[47]) & MASK)

            for r in range(7):
                # Message 1 additions (track carries)
                # T1 chain: h + Sigma1(e) + Ch(e,f,g) + K + W
                sig1_1 = sha_mini.Sigma1(e1)
                ch1 = sha_mini.ch(e1, f1, g1)
                t1a_1 = (h1 + sig1_1) & MASK
                t1b_1 = (t1a_1 + ch1) & MASK
                kw1 = (Kvals[57+r] + W1[r]) & MASK
                T1_1 = (t1b_1 + kw1) & MASK

                sig1_2 = sha_mini.Sigma1(e2)
                ch2 = sha_mini.ch(e2, f2, g2)
                t1a_2 = (h2 + sig1_2) & MASK
                t1b_2 = (t1a_2 + ch2) & MASK
                kw2 = (Kvals[57+r] + W2[r]) & MASK
                T1_2 = (t1b_2 + kw2) & MASK

                # Track carry differences for each addition
                for add_idx, (x1, y1, x2, y2) in enumerate([
                    (h1, sig1_1, h2, sig1_2),           # add 0: h + Sigma1(e)
                    (t1a_1, ch1, t1a_2, ch2),           # add 1: prev + Ch
                    (t1b_1, kw1, t1b_2, kw2),           # add 2: prev + K+W
                    (Kvals[57+r], W1[r], Kvals[57+r], W2[r]),  # add 3: K + W
                ]):
                    c1_bits = get_carries(x1, y1, N_width)
                    c2_bits = get_carries(x2, y2, N_width)
                    for bit in range(N_width):
                        key = (r, add_idx, bit)
                        dc = c1_bits[bit] ^ c2_bits[bit]
                        if key not in all_carry_diffs:
                            all_carry_diffs[key] = set()
                        all_carry_diffs[key].add(dc)

                # T2, e_new, a_new
                sig0_1 = sha_mini.Sigma0(a1); maj1 = sha_mini.maj(a1, b1, c1)
                sig0_2 = sha_mini.Sigma0(a2); maj2 = sha_mini.maj(a2, b2, c2)
                T2_1 = (sig0_1 + maj1) & MASK
                T2_2 = (sig0_2 + maj2) & MASK

                for add_idx, (x1, y1, x2, y2) in enumerate([
                    (sig0_1, maj1, sig0_2, maj2),       # add 4: Sigma0 + Maj
                    (d1, T1_1, d2, T1_2),               # add 5: d + T1
                    (T1_1, T2_1, T1_2, T2_2),           # add 6: T1 + T2
                ], start=4):
                    c1_bits = get_carries(x1, y1, N_width)
                    c2_bits = get_carries(x2, y2, N_width)
                    for bit in range(N_width):
                        key = (r, add_idx, bit)
                        dc = c1_bits[bit] ^ c2_bits[bit]
                        if key not in all_carry_diffs:
                            all_carry_diffs[key] = set()
                        all_carry_diffs[key].add(dc)

                # Update state
                h1,g1,f1,e1,d1,c1,b1,a1 = g1,f1,e1,(d1+T1_1)&MASK,c1,b1,a1,(T1_1+T2_1)&MASK
                h2,g2,f2,e2,d2,c2,b2,a2 = g2,f2,e2,(d2+T1_2)&MASK,c2,b2,a2,(T1_2+T2_2)&MASK

        # Analyze results
        n_constant_0 = 0  # carry diff always 0
        n_constant_1 = 0  # carry diff always 1
        n_variable = 0    # carry diff varies

        for key in sorted(all_carry_diffs.keys()):
            vals = all_carry_diffs[key]
            if vals == {0}:
                n_constant_0 += 1
            elif vals == {1}:
                n_constant_1 += 1
            else:
                n_variable += 1

        total = n_constant_0 + n_constant_1 + n_variable
        print(f"\n  Carry difference classification ({n_samples} samples, N={N_width}):")
        print(f"    Always 0 (determined, no difference):  {n_constant_0} ({100*n_constant_0/total:.1f}%)")
        print(f"    Always 1 (determined, constant diff):  {n_constant_1} ({100*n_constant_1/total:.1f}%)")
        print(f"    Variable (the true nonlinear skeleton): {n_variable} ({100*n_variable/total:.1f}%)")
        print(f"    Total carry bits tracked: {total}")
        print()
        print(f"  *** THE CARRY SKELETON HAS {n_variable} FREE BITS ***")
        print(f"  (out of {total} total carry difference bits)")
        print(f"  Conditioning on these {n_variable} bits makes the rest linear over GF(2).")
        print(f"  Brute-forcing the skeleton: 2^{n_variable} = {1<<min(n_variable,60)}")
        if n_variable <= 40:
            print(f"  THIS IS TRACTABLE! Carry-conditioned linearization attack is feasible.")
        else:
            print(f"  Still too large for brute force. Need carry-reduction strategies.")

        # Per-round breakdown
        print(f"\n  Per-round variable carry count:")
        for r in range(7):
            n_var_r = sum(1 for (rr,_,_), v in all_carry_diffs.items() if rr == r and len(v) > 1)
            n_tot_r = sum(1 for (rr,_,_) in all_carry_diffs if rr == r)
            print(f"    Round {57+r}: {n_var_r}/{n_tot_r} variable carries")

    else:
        print(f"  (N={N_width} simulation would be too slow in Python)")
        print(f"  Estimate: at N=32, variable carries ≈ {N_width} × (N=8 fraction)")

    print(f"\nDone.")


if __name__ == "__main__":
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    count_carry_skeleton(N)
