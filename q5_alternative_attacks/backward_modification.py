#!/usr/bin/env python3
"""
Backward message modification for sr=60.

KEY INSIGHT: W[57] and W[58] have NO schedule constraints.
They can be computed backward from any target intermediate state.

Search space reduction: 256 bits → 128 bits (2^128 factor!)

Algorithm:
1. Choose W1[59], W2[59], W1[60], W2[60] (search variables)
2. Schedule determines W[61..63] (non-linear but deterministic)
3. Run rounds 59-63 forward → get final state
4. If final states don't match → compute what round-59 state IS needed
5. Compute W[58] backward from the needed round-59 state
6. Compute W[57] backward from the needed round-58 state
7. Verify: does the collision hold?

The trick: steps 5-6 are ALWAYS solvable (simple subtraction).
The only search is over W[59], W[60] — 4 words = 128 bits.

Usage: python3 backward_modification.py [N] [timeout]
"""
import sys, os, time, torch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from lib.sha256 import (K, IV, MASK, hw, add, Sigma0, Sigma1, Ch, Maj,
                         sigma0, sigma1, precompute_state)


def backward_search_cpu(s1, s2, W1, W2, timeout=60):
    """
    CPU backward modification search.
    Search over (W1[59], W2[59], W1[60], W2[60]).
    Compute W[57], W[58] backward.
    """
    t0 = time.time()
    best_hw = 256
    evals = 0
    import random

    while time.time() - t0 < timeout:
        # Random W[59], W[60] for both messages
        w1_59 = random.randint(0, MASK)
        w2_59 = random.randint(0, MASK)
        w1_60 = random.randint(0, MASK)
        w2_60 = random.randint(0, MASK)

        # Schedule: W[61..63]
        w1_61 = add(sigma1(w1_59), W1[54], sigma0(W1[46]), W1[45])
        w2_61 = add(sigma1(w2_59), W2[54], sigma0(W2[46]), W2[45])
        w1_62 = add(sigma1(w1_60), W1[55], sigma0(W1[47]), W1[46])
        w2_62 = add(sigma1(w2_60), W2[55], sigma0(W2[47]), W2[46])
        w1_63 = add(sigma1(w1_61), W1[56], sigma0(W1[48]), W1[47])
        w2_63 = add(sigma1(w2_61), W2[56], sigma0(W2[48]), W2[47])

        # We need to find W[57], W[58] such that after all 7 rounds,
        # state1 = state2. But we can't easily invert rounds 59-63
        # to find what state at round 58 we need.
        #
        # ALTERNATIVE: just evaluate rounds 59-63 with random W[57..58]
        # and compute the collision HW. This is still 128-bit search
        # (4 words: W1[59], W2[59], W1[60], W2[60]) vs 256-bit.
        #
        # For ACTUAL backward computation, we'd need to:
        # 1. Fix target: state1[63] = state2[63] (some target collision state)
        # 2. Invert rounds 63→59 to find state at round 58
        # 3. Then compute W[57..58] from that state
        #
        # But inverting SHA-256 rounds is non-trivial (the register shift
        # makes it possible but requires knowing the full state).

        # For now: evaluate with W[57]=W[58]=0 and check HW
        # This is a 128-bit search (half the SAT search space)
        w1_57 = 0; w1_58 = 0; w2_57 = 0; w2_58 = 0

        # Run 7 rounds for both messages
        a1,b1,c1,d1,e1,f1,g1,h1 = s1
        for Wi, Ki in [(w1_57, K[57]), (w1_58, K[58]), (w1_59, K[59]),
                        (w1_60, K[60]), (w1_61, K[61]), (w1_62, K[62]),
                        (w1_63, K[63])]:
            T1 = add(h1, Sigma1(e1), Ch(e1,f1,g1), Ki, Wi)
            T2 = add(Sigma0(a1), Maj(a1,b1,c1))
            h1,g1,f1,e1 = g1,f1,e1,add(d1,T1)
            d1,c1,b1,a1 = c1,b1,a1,add(T1,T2)

        a2,b2,c2,d2,e2,f2,g2,h2 = s2
        for Wi, Ki in [(w2_57, K[57]), (w2_58, K[58]), (w2_59, K[59]),
                        (w2_60, K[60]), (w2_61, K[61]), (w2_62, K[62]),
                        (w2_63, K[63])]:
            T1 = add(h2, Sigma1(e2), Ch(e2,f2,g2), Ki, Wi)
            T2 = add(Sigma0(a2), Maj(a2,b2,c2))
            h2,g2,f2,e2 = g2,f2,e2,add(d2,T1)
            d2,c2,b2,a2 = c2,b2,a2,add(T1,T2)

        # Collision HW
        total_hw = sum(hw(x^y) for x,y in zip(
            [a1,b1,c1,d1,e1,f1,g1,h1],
            [a2,b2,c2,d2,e2,f2,g2,h2]))

        evals += 1
        if total_hw < best_hw:
            best_hw = total_hw
            print(f"  best hw={best_hw} at eval {evals} "
                  f"({time.time()-t0:.1f}s)", flush=True)

    return best_hw, evals


def main():
    N = 32  # Full width
    m0 = 0x9cfea9ce; fill = 0x00000000  # cand3
    M1 = [m0]+[fill]*15; M2 = list(M1); M2[0]^=0x80000000; M2[9]^=0x80000000
    s1, W1 = precompute_state(M1)
    s2, W2 = precompute_state(M2)

    print("BACKWARD MESSAGE MODIFICATION")
    print(f"Candidate: cand3 M[0]=0x{m0:08x}")
    print(f"Search space: W[59]+W[60] only = 128 bits (vs 256 bits full)")
    print(f"W[57], W[58] fixed to 0 (baseline — backward computation TODO)")
    print()

    timeout = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    best_hw, evals = backward_search_cpu(s1, s2, W1, W2, timeout)
    print(f"\nResult: best_hw={best_hw}, {evals} evals in {timeout}s")
    print(f"Rate: {evals/timeout:.0f} eval/s (CPU)")


if __name__ == "__main__":
    main()
