#!/usr/bin/env python3
"""
Wang-Style Message Modification for sr=60 Tail

Classic Wang attack (2005): given a differential path, modify message words
to satisfy conditions on intermediate states.

For sr=60 tail:
- Differential path: cascade-1 (da57=0 → db58=0 → dc59=0 → dd59=0)
                      + cascade-2 (de60=0 → df61=0 → dg62=0 → dh63=0)
- Free words: W[57..60]
- Conditions: specific bit conditions on a57, e57, etc.

Wang modification works backwards from the conditions:
1. Determine what conditions each round's state must satisfy
2. Starting from the last free word, adjust to satisfy the conditions
3. Propagate changes forward to verify

At N=4 and N=8, we can extract the actual conditions from collision solutions
and test whether Wang-style modification can construct collisions faster
than SAT/brute force.
"""

import sys, os, time, random, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')


def wang_analysis(N=4):
    spec = __import__('50_precision_homotopy')
    sha = spec.MiniSHA256(N)
    MASK_N = sha.MASK
    MSB = sha.MSB
    K = sha.K

    result = sha.find_m0()
    if result[0] is None:
        print(f"No candidate at N={N}")
        return
    m0, s1, s2, W1_pre, W2_pre = result

    print(f"Wang-Style Modification Analysis at N={N}")
    print(f"Candidate: M[0]=0x{m0:x}")

    # Step 1: Extract differential conditions from known collisions
    # Find all collisions at N=4 (or sample at N=8)
    print(f"\n=== Step 1: Extract Differential Conditions ===")

    # Compute the cascade offset
    dh = (s1[7] - s2[7]) & MASK_N
    dSig1 = (sha.Sigma1(s1[4]) - sha.Sigma1(s2[4])) & MASK_N
    dCh = (sha.ch(s1[4], s1[5], s1[6]) - sha.ch(s2[4], s2[5], s2[6])) & MASK_N
    T2_1 = (sha.Sigma0(s1[0]) + sha.maj(s1[0], s1[1], s1[2])) & MASK_N
    T2_2 = (sha.Sigma0(s2[0]) + sha.maj(s2[0], s2[1], s2[2])) & MASK_N
    dT2 = (T2_1 - T2_2) & MASK_N
    C_w57 = (dh + dSig1 + dCh + dT2) & MASK_N

    def eval_per_round(w1, w2):
        """Compute per-round state for both messages. Return list of 8 state tuples."""
        W1 = list(w1)
        W2 = list(w2)
        W1.append((sha.sigma1(w1[2]) + W1_pre[54] + sha.sigma0(W1_pre[46]) + W1_pre[45]) & MASK_N)
        W2.append((sha.sigma1(w2[2]) + W2_pre[54] + sha.sigma0(W2_pre[46]) + W2_pre[45]) & MASK_N)
        W1.append((sha.sigma1(w1[3]) + W1_pre[55] + sha.sigma0(W1_pre[47]) + W1_pre[46]) & MASK_N)
        W2.append((sha.sigma1(w2[3]) + W2_pre[55] + sha.sigma0(W2_pre[47]) + W2_pre[46]) & MASK_N)
        W1.append((sha.sigma1(W1[4]) + W1_pre[56] + sha.sigma0(W1_pre[48]) + W1_pre[47]) & MASK_N)
        W2.append((sha.sigma1(W2[4]) + W2_pre[56] + sha.sigma0(W2_pre[48]) + W2_pre[47]) & MASK_N)

        rounds1 = [s1]
        rounds2 = [s2]
        a1,b1,c1,d1,e1,f1,g1,h1 = s1
        a2,b2,c2,d2,e2,f2,g2,h2 = s2

        for i in range(7):
            T1a = (h1 + sha.Sigma1(e1) + sha.ch(e1,f1,g1) + K[57+i] + W1[i]) & MASK_N
            T2a = (sha.Sigma0(a1) + sha.maj(a1,b1,c1)) & MASK_N
            h1,g1,f1,e1,d1,c1,b1,a1 = g1,f1,e1,(d1+T1a)&MASK_N,c1,b1,a1,(T1a+T2a)&MASK_N
            rounds1.append((a1,b1,c1,d1,e1,f1,g1,h1))

            T1b = (h2 + sha.Sigma1(e2) + sha.ch(e2,f2,g2) + K[57+i] + W2[i]) & MASK_N
            T2b = (sha.Sigma0(a2) + sha.maj(a2,b2,c2)) & MASK_N
            h2,g2,f2,e2,d2,c2,b2,a2 = g2,f2,e2,(d2+T1b)&MASK_N,c2,b2,a2,(T1b+T2b)&MASK_N
            rounds2.append((a2,b2,c2,d2,e2,f2,g2,h2))

        return rounds1, rounds2, W1, W2

    # Enumerate collisions at N=4 (or sample at N=8)
    if N <= 6:
        print(f"Exhaustive collision search at N={N}...")
        collisions = []
        t0 = time.time()
        for w1_57 in range(1 << N):
            w2_57 = (w1_57 + C_w57) & MASK_N
            for w1_58 in range(1 << N):
                for w1_59 in range(1 << N):
                    for w1_60 in range(1 << N):
                        for w2_58 in range(1 << N):
                            for w2_59 in range(1 << N):
                                for w2_60 in range(1 << N):
                                    w1 = [w1_57, w1_58, w1_59, w1_60]
                                    w2 = [w2_57, w2_58, w2_59, w2_60]
                                    r1, r2, _, _ = eval_per_round(w1, w2)
                                    if all(r1[7][reg] == r2[7][reg] for reg in range(8)):
                                        collisions.append((w1, w2, r1, r2))
                                        if len(collisions) <= 5:
                                            print(f"  Collision #{len(collisions)}: "
                                                  f"W1={[hex(x) for x in w1]}")
            if time.time() - t0 > 300:
                print(f"  Time limit after W1[57]=0x{w1_57:x}")
                break
        print(f"Found {len(collisions)} collisions in {time.time()-t0:.0f}s")
    else:
        # At N=8, use SAT solutions or sample
        print(f"Using random sampling at N={N}...")
        collisions = []

    if not collisions:
        print("No collisions to analyze. Using random differential paths instead.")
        # Generate near-collision paths for analysis
        random.seed(42)
        paths = []
        for _ in range(1000):
            w1_57 = random.randint(0, MASK_N)
            w2_57 = (w1_57 + C_w57) & MASK_N
            w1 = [w1_57] + [random.randint(0, MASK_N) for _ in range(3)]
            w2 = [w2_57] + [random.randint(0, MASK_N) for _ in range(3)]
            r1, r2, _, _ = eval_per_round(w1, w2)
            hw = sum(bin(r1[7][reg] ^ r2[7][reg]).count('1') for reg in range(8))
            paths.append((hw, w1, w2, r1, r2))
        paths.sort()
        print(f"Near-collisions: best HW={paths[0][0]}")
        # Use the best near-collisions as our paths
        for hw, w1, w2, r1, r2 in paths[:5]:
            collisions.append((w1, w2, r1, r2))

    # Step 2: Extract per-round conditions
    print(f"\n=== Step 2: Per-Round Differential Conditions ===")
    reg_names = ['a','b','c','d','e','f','g','h']

    for ci, (w1, w2, r1, r2) in enumerate(collisions[:3]):
        print(f"\nCollision/path #{ci+1}:")
        for rnd in range(8):
            diffs = []
            for reg in range(8):
                d = r1[rnd][reg] ^ r2[rnd][reg]
                hw = bin(d).count('1')
                diffs.append((reg_names[reg], d, hw))
            total_hw = sum(d[2] for d in diffs)
            active = [f"d{n}=0x{d:0{(N+3)//4}x}(hw{hw})" for n,d,hw in diffs if hw > 0]
            zero = [n for n,d,hw in diffs if hw == 0]
            print(f"  Round {56+rnd}: total_hw={total_hw:2d}  "
                  f"zero=[{','.join(zero)}]  active=[{'; '.join(active[:4])}]")

    # Step 3: Wang-style modification attempt
    print(f"\n=== Step 3: Wang Modification Prototype ===")
    print(f"Strategy: fix cascade-1 (W2[57]=W1[57]+C), then adjust W[58..60]")
    print(f"to satisfy per-round conditions bit by bit.")

    # Simple greedy modification: for each W[58..60] word, try to minimize
    # the number of unsatisfied conditions at the next round
    random.seed(123)
    n_trials = 100000
    n_success = 0
    best_hw = N * 8

    for trial in range(n_trials):
        w1_57 = random.randint(0, MASK_N)
        w2_57 = (w1_57 + C_w57) & MASK_N

        # Greedy: for W[58], try all values and pick the one that minimizes
        # the round-58 differential conditions
        best_w58 = None
        best_r58_hw = N * 8
        for w1_58 in range(1 << N):
            for w2_58 in range(1 << N):
                # Compute round 57 state
                a1,b1,c1,d1,e1,f1,g1,h1 = s1
                a2,b2,c2,d2,e2,f2,g2,h2 = s2
                T1a = (h1+sha.Sigma1(e1)+sha.ch(e1,f1,g1)+K[57]+w1_57) & MASK_N
                T2a = (sha.Sigma0(a1)+sha.maj(a1,b1,c1)) & MASK_N
                h1,g1,f1,e1,d1,c1,b1,a1 = g1,f1,e1,(d1+T1a)&MASK_N,c1,b1,a1,(T1a+T2a)&MASK_N

                T1b = (h2+sha.Sigma1(e2)+sha.ch(e2,f2,g2)+K[57]+w2_57) & MASK_N
                T2b = (sha.Sigma0(a2)+sha.maj(a2,b2,c2)) & MASK_N
                h2,g2,f2,e2,d2,c2,b2,a2 = g2,f2,e2,(d2+T1b)&MASK_N,c2,b2,a2,(T1b+T2b)&MASK_N

                # Round 58
                T1a = (h1+sha.Sigma1(e1)+sha.ch(e1,f1,g1)+K[58]+w1_58) & MASK_N
                T2a = (sha.Sigma0(a1)+sha.maj(a1,b1,c1)) & MASK_N
                na1 = (T1a+T2a)&MASK_N; ne1 = (d1+T1a)&MASK_N

                T1b = (h2+sha.Sigma1(e2)+sha.ch(e2,f2,g2)+K[58]+w2_58) & MASK_N
                T2b = (sha.Sigma0(a2)+sha.maj(a2,b2,c2)) & MASK_N
                na2 = (T1b+T2b)&MASK_N; ne2 = (d2+T1b)&MASK_N

                hw58 = bin(na1^na2).count('1') + bin(ne1^ne2).count('1')
                if hw58 < best_r58_hw:
                    best_r58_hw = hw58
                    best_w58 = (w1_58, w2_58)

        if best_r58_hw == 0 and best_w58 and trial < 10:
            print(f"  Trial {trial}: da58=de58=0 with W58={best_w58}")

        # Continue with best W[58] and random W[59], W[60]
        if best_w58:
            w1_58, w2_58 = best_w58
            w1 = [w1_57, w1_58, random.randint(0,MASK_N), random.randint(0,MASK_N)]
            w2 = [w2_57, w2_58, random.randint(0,MASK_N), random.randint(0,MASK_N)]
            r1, r2, _, _ = eval_per_round(w1, w2)
            hw = sum(bin(r1[7][reg]^r2[7][reg]).count('1') for reg in range(8))
            if hw < best_hw:
                best_hw = hw
                if trial < 20 or hw < N:
                    print(f"  Trial {trial}: best_hw={hw} (W58 gave r58_hw={best_r58_hw})")
            if hw == 0:
                n_success += 1

        if trial > 0 and trial % 10000 == 0:
            print(f"  [{trial}/{n_trials}] best_hw={best_hw}, successes={n_success}")

    print(f"\nWang modification results:")
    print(f"  Trials: {n_trials}")
    print(f"  Best HW: {best_hw}")
    print(f"  Collisions: {n_success}")
    print(f"  Note: greedy W[58] selection + random W[59..60]")

    print(f"\nDone.")


if __name__ == "__main__":
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    wang_analysis(N)
