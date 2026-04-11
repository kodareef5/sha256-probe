#!/usr/bin/env python3
"""
Cascade-Constrained Polynomial Interpolation

Key insight from combined findings:
1. Server: Round-62 constraint makes W[60] a function of W[57..59]
2. Macbook (ANF): h[0] depends on only W[60][0] (and linearly!)
3. Macbook (cascade chain): dW[57] = const, dW[58] = f(W1[57])

Combined: the collision function, after applying all cascade constraints,
is a polynomial in at most 3*N = 96 bits (at N=32) or 3*N = 24 bits (at N=8).

This script:
1. Enumerates the cascade-constrained search space at N=8
2. For each W1[57], computes the cascade chain to determine W2[57], dW[58]
3. For each (W1[57], W1[58], W1[59]), determines W[60] via round-62 inverter
4. Computes the Hamming weight of the remaining register differences
5. Profiles the polynomial structure of the resulting function

At N=8 with 24 free bits: 2^24 = 16M evaluations. Feasible in Python in ~minutes.
"""

import sys, os, time, random, collections
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')


def run_cascade_interpolation(N=8):
    spec = __import__('50_precision_homotopy')
    sha = spec.MiniSHA256(N)
    MASK_N = sha.MASK
    MSB = sha.MSB

    result = sha.find_m0()
    if result[0] is None:
        print(f"No candidate at N={N}")
        return
    m0, s1, s2, W1_pre, W2_pre = result

    K = sha.K

    print(f"Cascade-Constrained Polynomial Interpolation at N={N}")
    print(f"Candidate: M[0]=0x{m0:x}")
    print()

    # Step 1: Compute dW[57] (the cascade-1 constant)
    dh = (s1[7] - s2[7]) & MASK_N
    dSig1 = (sha.Sigma1(s1[4]) - sha.Sigma1(s2[4])) & MASK_N
    dCh = (sha.ch(s1[4], s1[5], s1[6]) - sha.ch(s2[4], s2[5], s2[6])) & MASK_N
    T2_1 = (sha.Sigma0(s1[0]) + sha.maj(s1[0], s1[1], s1[2])) & MASK_N
    T2_2 = (sha.Sigma0(s2[0]) + sha.maj(s2[0], s2[1], s2[2])) & MASK_N
    dT2 = (T2_1 - T2_2) & MASK_N
    C_w57 = (dh + dSig1 + dCh + dT2) & MASK_N
    print(f"Cascade constant: W2[57] = W1[57] + 0x{C_w57:02x}")

    # Step 2: Compute dW[58] as a function of W1[57]
    # After round 57 with da57=0, compute round 58 state and derive dW[58]
    def compute_round57_state(w1_57):
        """Given W1[57], compute state after round 57 for both messages."""
        w2_57 = (w1_57 + C_w57) & MASK_N
        T1_1 = (s1[7] + sha.Sigma1(s1[4]) + sha.ch(s1[4],s1[5],s1[6]) + K[57] + w1_57) & MASK_N
        T2_1_v = (sha.Sigma0(s1[0]) + sha.maj(s1[0],s1[1],s1[2])) & MASK_N
        a57_1 = (T1_1 + T2_1_v) & MASK_N
        e57_1 = (s1[3] + T1_1) & MASK_N

        T1_2 = (s2[7] + sha.Sigma1(s2[4]) + sha.ch(s2[4],s2[5],s2[6]) + K[57] + w2_57) & MASK_N
        T2_2_v = (sha.Sigma0(s2[0]) + sha.maj(s2[0],s2[1],s2[2])) & MASK_N
        a57_2 = (T1_2 + T2_2_v) & MASK_N
        e57_2 = (s2[3] + T1_2) & MASK_N

        st57_1 = (a57_1, s1[0], s1[1], s1[2], e57_1, s1[4], s1[5], s1[6])
        st57_2 = (a57_2, s2[0], s2[1], s2[2], e57_2, s2[4], s2[5], s2[6])
        return st57_1, st57_2

    def compute_dW58(w1_57):
        """Compute the value of dW[58] that makes db58=0, given W1[57]."""
        st57_1, st57_2 = compute_round57_state(w1_57)
        # For db58 = 0: need da58 = a57_1 (which is state-57 b register)
        # Actually db58 = a57_1 == a57_2 (since da57=0, they're the same)
        # The shift register propagation makes this automatic.
        # But dW[58] is determined by requiring db58=0.
        #
        # At round 58: a58 = T1_58 + T2_58
        # b58 = a57 (shift register)
        # So db58 = da57 = 0 automatically!
        # Therefore dW[58] is NOT constrained by cascade-1.
        #
        # Actually: cascade-1 gives da57=0 → db58=0 → dc59=0 → dd59=0
        # These are all from the shift register. dW[58] is genuinely free.
        # What we need is: W2[58] is chosen independently of W1[58].
        return None  # dW[58] is free (not constrained)

    print(f"dW[58]: not constrained by cascade-1 (both messages choose independently)")

    # Step 3: Full evaluation with cascade constraints
    def eval_cascade_constrained(w1_57, w1_58, w1_59, w2_58, w2_59):
        """
        Evaluate the collision function with cascade-1 constraint applied.
        W2[57] = W1[57] + C. W1[60] and W2[60] are free (NOT cascade-constrained
        at sr=60). But we can try computing what W[60] the schedule would give.

        At sr=60, W[60] is free. Return the full state diff for all W[60].
        """
        w2_57 = (w1_57 + C_w57) & MASK_N

        # Build schedule with W[60] free
        w1 = [w1_57, w1_58, w1_59]
        w2 = [w2_57, w2_58, w2_59]

        # Schedule-determined W[60]
        w1_60_sched = (sha.sigma1(w1_59) + W1_pre[53] + sha.sigma0(W1_pre[45]) + W1_pre[44]) & MASK_N
        w2_60_sched = (sha.sigma1(w2_59) + W2_pre[53] + sha.sigma0(W2_pre[45]) + W2_pre[44]) & MASK_N

        return w1_60_sched, w2_60_sched

    def eval_full_constrained(w1_57, w1_58, w1_59, w2_58, w2_59, w1_60, w2_60):
        """Full 7-round eval with cascade-1 constraint applied."""
        w2_57 = (w1_57 + C_w57) & MASK_N

        W1 = [w1_57, w1_58, w1_59, w1_60]
        W2 = [w2_57, w2_58, w2_59, w2_60]

        W1.append((sha.sigma1(W1[2]) + W1_pre[54] + sha.sigma0(W1_pre[46]) + W1_pre[45]) & MASK_N)
        W2.append((sha.sigma1(W2[2]) + W2_pre[54] + sha.sigma0(W2_pre[46]) + W2_pre[45]) & MASK_N)
        W1.append((sha.sigma1(W1[3]) + W1_pre[55] + sha.sigma0(W1_pre[47]) + W1_pre[46]) & MASK_N)
        W2.append((sha.sigma1(W2[3]) + W2_pre[55] + sha.sigma0(W2_pre[47]) + W2_pre[46]) & MASK_N)
        W1.append((sha.sigma1(W1[4]) + W1_pre[56] + sha.sigma0(W1_pre[48]) + W1_pre[47]) & MASK_N)
        W2.append((sha.sigma1(W2[4]) + W2_pre[56] + sha.sigma0(W2_pre[48]) + W2_pre[47]) & MASK_N)

        a1,b1,c1,d1,e1,f1,g1,h1 = s1
        a2,b2,c2,d2,e2,f2,g2,h2 = s2
        for i in range(7):
            T1a = (h1 + sha.Sigma1(e1) + sha.ch(e1,f1,g1) + K[57+i] + W1[i]) & MASK_N
            T2a = (sha.Sigma0(a1) + sha.maj(a1,b1,c1)) & MASK_N
            h1,g1,f1,e1,d1,c1,b1,a1 = g1,f1,e1,(d1+T1a)&MASK_N,c1,b1,a1,(T1a+T2a)&MASK_N
            T1b = (h2 + sha.Sigma1(e2) + sha.ch(e2,f2,g2) + K[57+i] + W2[i]) & MASK_N
            T2b = (sha.Sigma0(a2) + sha.maj(a2,b2,c2)) & MASK_N
            h2,g2,f2,e2,d2,c2,b2,a2 = g2,f2,e2,(d2+T1b)&MASK_N,c2,b2,a2,(T1b+T2b)&MASK_N

        return (a1,b1,c1,d1,e1,f1,g1,h1), (a2,b2,c2,d2,e2,f2,g2,h2)

    # Step 4: Profile the collision function over the cascade-constrained space
    # At N=8: 5 free N-bit words = 40 bits, plus 2 W[60] = 56 bits total
    # With cascade-1 applied: W2[57] determined, so 7 free words = 56 bits
    # Full search: 2^56 at N=8 = too large

    # Sample-based approach: random W[57..60] with cascade constraint
    print(f"\n=== Cascade-Constrained HW Profile ===")
    print(f"Free variables: W1[57](N), W1[58](N), W1[59](N), W2[58](N), W2[59](N), W1[60](N), W2[60](N)")
    print(f"Constrained: W2[57] = W1[57] + C")
    print(f"Total free bits: {7*N}")
    print(f"Sampling 500K random points...")

    random.seed(42)
    n_samples = 500000
    hw_counts = collections.Counter()
    hw_per_reg = {r: collections.Counter() for r in range(8)}
    best_hw = 999
    best_point = None
    collisions = []

    t0 = time.time()
    for trial in range(n_samples):
        w1_57 = random.randint(0, MASK_N)
        w1_58 = random.randint(0, MASK_N)
        w1_59 = random.randint(0, MASK_N)
        w2_58 = random.randint(0, MASK_N)
        w2_59 = random.randint(0, MASK_N)
        w1_60 = random.randint(0, MASK_N)
        w2_60 = random.randint(0, MASK_N)

        st1, st2 = eval_full_constrained(w1_57, w1_58, w1_59, w2_58, w2_59, w1_60, w2_60)

        total_hw = 0
        for r in range(8):
            rh = bin(st1[r] ^ st2[r]).count('1')
            hw_per_reg[r][rh] += 1
            total_hw += rh

        hw_counts[total_hw] += 1
        if total_hw < best_hw:
            best_hw = total_hw
            best_point = (w1_57, w1_58, w1_59, w2_58, w2_59, w1_60, w2_60)
        if total_hw == 0:
            collisions.append(best_point)

        if trial > 0 and trial % 100000 == 0:
            elapsed = time.time() - t0
            print(f"  [{trial/n_samples*100:.0f}%] best_hw={best_hw}, "
                  f"collisions={len(collisions)}, {elapsed:.0f}s")

    elapsed = time.time() - t0
    print(f"\nSampling complete: {n_samples} points in {elapsed:.1f}s")
    print(f"Best HW: {best_hw}")
    print(f"Collisions: {len(collisions)}")

    # HW distribution
    mean_hw = sum(hw * c for hw, c in hw_counts.items()) / n_samples
    print(f"\nHW distribution (cascade-constrained):")
    print(f"  Mean: {mean_hw:.1f}")
    print(f"  HW   Count    Pct")
    for hw in sorted(hw_counts.keys()):
        if hw <= best_hw + 10 or hw_counts[hw] > n_samples * 0.001:
            pct = 100 * hw_counts[hw] / n_samples
            bar = '#' * min(60, int(pct * 2))
            print(f"  {hw:3d}  {hw_counts[hw]:7d}  {pct:5.2f}%  {bar}")

    # Per-register mean HW
    reg_names = ['a','b','c','d','e','f','g','h']
    print(f"\nPer-register mean HW:")
    for r in range(8):
        mean_r = sum(hw * c for hw, c in hw_per_reg[r].items()) / n_samples
        print(f"  {reg_names[r]}: {mean_r:.2f}/{N}")

    # Step 5: Compare with schedule-determined W[60]
    print(f"\n=== Schedule-Determined W[60] (sr=61 proxy) ===")
    print(f"What if we force W[60] = schedule(W[58])? (5 free words = {5*N} bits)")

    hw_sched = collections.Counter()
    best_hw_sched = 999
    collisions_sched = []

    for trial in range(n_samples):
        w1_57 = random.randint(0, MASK_N)
        w1_58 = random.randint(0, MASK_N)
        w1_59 = random.randint(0, MASK_N)
        w2_58 = random.randint(0, MASK_N)
        w2_59 = random.randint(0, MASK_N)

        # Schedule-determined W[60]
        w1_60 = (sha.sigma1(w1_58) + W1_pre[53] + sha.sigma0(W1_pre[45]) + W1_pre[44]) & MASK_N
        w2_60 = (sha.sigma1(w2_58) + W2_pre[53] + sha.sigma0(W2_pre[45]) + W2_pre[44]) & MASK_N

        st1, st2 = eval_full_constrained(w1_57, w1_58, w1_59, w2_58, w2_59, w1_60, w2_60)
        hw = sum(bin(st1[r] ^ st2[r]).count('1') for r in range(8))
        hw_sched[hw] += 1
        if hw < best_hw_sched:
            best_hw_sched = hw
        if hw == 0:
            collisions_sched.append((w1_57, w1_58, w1_59, w2_58, w2_59))

    mean_hw_sched = sum(hw * c for hw, c in hw_sched.items()) / n_samples
    print(f"  Mean HW (schedule W[60]): {mean_hw_sched:.1f}")
    print(f"  Best HW: {best_hw_sched}")
    print(f"  Collisions: {len(collisions_sched)}")
    print(f"  Diff from free W[60]: {mean_hw_sched - mean_hw:+.1f} mean HW")

    # Step 6: Verify collisions
    if collisions:
        print(f"\n=== Collision Verification ===")
        for c in collisions[:5]:
            w1_57, w1_58, w1_59, w2_58, w2_59, w1_60, w2_60 = c
            st1, st2 = eval_full_constrained(w1_57, w1_58, w1_59, w2_58, w2_59, w1_60, w2_60)
            ok = all(st1[r] == st2[r] for r in range(8))
            print(f"  W1[57..60]={[hex(x) for x in [w1_57,w1_58,w1_59,w1_60]]} OK={ok}")

    print(f"\nDone.")
    return best_hw, len(collisions), mean_hw


if __name__ == "__main__":
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    run_cascade_interpolation(N)
