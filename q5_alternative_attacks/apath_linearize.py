#!/usr/bin/env python3
"""
a-Path Carry-Conditioned Linearization

Both Gemini and GPT-5.4 independently recommended this algorithm:
1. Guess the ~3 free carries/round in Sig0+Maj and T1+T2 (~21 total at N=8)
2. This makes the a-register path LINEAR over GF(2)
3. Solve via Gaussian elimination → parametrize Cascade-1 manifold
4. Feed the parametrized solution into T1 chain constraints

This is a PROOF OF CONCEPT at N=4 where we can verify against known solutions.
"""
import sys, os, time, random
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')


def main():
    spec = __import__('50_precision_homotopy')
    N = 4; sha = spec.MiniSHA256(N)
    MASK = sha.MASK; K = sha.K
    m0, s1, s2, W1p, W2p = sha.find_m0()

    print(f"a-Path Carry-Conditioned Linearization at N={N}")
    print(f"Candidate: M[0]=0x{m0:x}")
    print()

    # From carry analysis: Sig0+Maj has 1/28 free carries, T1+T2 has 2/28
    # At N=4 over 7 rounds: ~3 free carries/round = ~21 total
    # But many are correlated. Let's count EXACTLY.

    # Step 1: For each collision, extract the a-path carries
    collisions = []
    with open('q5_alternative_attacks/results/collision_list_n4.log') as f:
        for line in f:
            if line.startswith('['):
                parts = line.split('W1=[')[1].split('] W2=[')
                w1 = [int(x,16) for x in parts[0].split(',')]
                w2 = [int(x,16) for x in parts[1].split(']')[0].split(',')]
                collisions.append((w1, w2))

    print(f"Loaded {len(collisions)} collision solutions")

    def get_carries(a, b, n):
        carries = []; c = 0
        for i in range(n):
            ai=(a>>i)&1; bi=(b>>i)&1
            c = (ai&bi)|(ai&c)|(bi&c)
            carries.append(c)
        return carries

    # Step 2: Extract a-path carry patterns
    # a-path additions: Sig0+Maj (add 4) and T1+T2 (add 6)
    apath_carries = []  # (round, add_type, [carry_bits_msg1], [carry_bits_msg2])

    for ci, (w1, w2) in enumerate(collisions):
        W1, W2 = list(w1), list(w2)
        W1.append((sha.sigma1(w1[2])+W1p[54]+sha.sigma0(W1p[46])+W1p[45])&MASK)
        W2.append((sha.sigma1(w2[2])+W2p[54]+sha.sigma0(W2p[46])+W2p[45])&MASK)
        W1.append((sha.sigma1(w1[3])+W1p[55]+sha.sigma0(W1p[47])+W1p[46])&MASK)
        W2.append((sha.sigma1(w2[3])+W2p[55]+sha.sigma0(W2p[47])+W2p[46])&MASK)
        W1.append((sha.sigma1(W1[4])+W1p[56]+sha.sigma0(W1p[48])+W1p[47])&MASK)
        W2.append((sha.sigma1(W2[4])+W2p[56]+sha.sigma0(W2p[48])+W2p[47])&MASK)

        pattern = []
        a1,b1,c1,d1,e1,f1,g1,h1 = s1
        a2,b2,c2,d2,e2,f2,g2,h2 = s2
        for r in range(7):
            sig1_1=sha.Sigma1(e1);ch1=sha.ch(e1,f1,g1)
            sig1_2=sha.Sigma1(e2);ch2=sha.ch(e2,f2,g2)
            t1a_1=(h1+sig1_1)&MASK;t1a_2=(h2+sig1_2)&MASK
            t1b_1=(t1a_1+ch1)&MASK;t1b_2=(t1a_2+ch2)&MASK
            kw1=(K[57+r]+W1[r])&MASK;kw2=(K[57+r]+W2[r])&MASK
            T1_1=(t1b_1+kw1)&MASK;T1_2=(t1b_2+kw2)&MASK
            sig0_1=sha.Sigma0(a1);maj1=sha.maj(a1,b1,c1)
            sig0_2=sha.Sigma0(a2);maj2=sha.maj(a2,b2,c2)
            T2_1=(sig0_1+maj1)&MASK;T2_2=(sig0_2+maj2)&MASK

            # a-path carries: Sig0+Maj and T1+T2
            c_sm_1 = get_carries(sig0_1, maj1, N)
            c_sm_2 = get_carries(sig0_2, maj2, N)
            c_tt_1 = get_carries(T1_1, T2_1, N)
            c_tt_2 = get_carries(T1_2, T2_2, N)

            # Carry differences
            dc_sm = [c_sm_1[i]^c_sm_2[i] for i in range(N)]
            dc_tt = [c_tt_1[i]^c_tt_2[i] for i in range(N)]
            pattern.extend(dc_sm + dc_tt)

            h1,g1,f1,e1,d1,c1,b1,a1 = g1,f1,e1,(d1+T1_1)&MASK,c1,b1,a1,(T1_1+T2_1)&MASK
            h2,g2,f2,e2,d2,c2,b2,a2 = g2,f2,e2,(d2+T1_2)&MASK,c2,b2,a2,(T1_2+T2_2)&MASK

        apath_carries.append(tuple(pattern))

    # Step 3: Analyze a-path carry entropy
    import math
    n_distinct = len(set(apath_carries))
    entropy = math.log2(max(1, n_distinct))
    total_bits = len(apath_carries[0])

    print(f"\n=== a-Path Carry Analysis ===")
    print(f"  Total a-path carry-diff bits: {total_bits} (Sig0+Maj + T1+T2, 7 rounds)")
    print(f"  Distinct patterns: {n_distinct}/{len(collisions)}")
    print(f"  Entropy: {entropy:.1f} bits")

    # Count variable bits
    n_variable = 0
    for bit_pos in range(total_bits):
        vals = set(p[bit_pos] for p in apath_carries)
        if len(vals) > 1:
            n_variable += 1
    print(f"  Variable bits: {n_variable}/{total_bits}")
    print(f"  Fixed bits: {total_bits - n_variable}/{total_bits}")

    # Step 4: For EACH distinct a-path carry pattern, how many collisions use it?
    from collections import Counter
    pattern_counts = Counter(apath_carries)
    print(f"\n  Pattern distribution:")
    for pattern, count in pattern_counts.most_common(10):
        bits_str = ''.join(str(b) for b in pattern[:20]) + '...'
        print(f"    [{bits_str}] x{count}")

    # Step 5: Check if a-path pattern uniquely determines the collision
    print(f"\n=== Key Question: Does a-path carry pattern determine the collision? ===")
    if n_distinct == len(collisions):
        print(f"  YES! Each collision has a unique a-path carry pattern.")
        print(f"  The a-path carries are sufficient to identify each collision.")
        print(f"  With only {n_variable} variable bits and {entropy:.1f} bits entropy,")
        print(f"  the a-path is a TINY search space.")
    elif n_distinct < len(collisions):
        max_per_pattern = max(pattern_counts.values())
        print(f"  NO — {len(collisions)} collisions map to {n_distinct} patterns")
        print(f"  Max collisions per pattern: {max_per_pattern}")
        print(f"  The a-path is necessary but not sufficient.")

    # Step 6: If we guess a-path carries, what remains?
    print(f"\n=== Guessing a-Path Carries ===")
    print(f"  Total guess space: 2^{n_variable} = {1<<n_variable}")
    print(f"  Valid guesses (from data): {n_distinct}")
    print(f"  Wastage ratio: {(1<<n_variable)/max(1,n_distinct):.0f}x")
    print(f"  After correct guess: a-register path becomes LINEAR over GF(2)")
    print(f"  Remaining: solve T1 chain constraints")

    print(f"\nDone.", flush=True)


if __name__ == "__main__":
    main()
