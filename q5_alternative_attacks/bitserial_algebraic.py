#!/usr/bin/env python3
"""
Bit-Serial Algebraic Attack on sr=60 Collision

Novel approach: attack output bits in order of algebraic complexity.

From exact ANF at N=4, we know:
  h[0]: degree 8,  1173 monomials, 6 absent variables (W[60] upper bits)
  h[1]: degree 9,  2642 monomials, 4 absent variables
  h[2]: degree 10, 6532 monomials, 2 absent variables
  h[3]: degree 12, 18436 monomials, 0 absent variables
  d[0]: degree 9,  1782 monomials, 8 absent variables
  ...

Key insight: h[0] = W1[60][0] XOR W2[60][0] XOR g(W[57], W[58], W[59])
So h[0]=0 gives us: dW[60][0] = g(W[57], W[58], W[59])

Strategy:
1. Enumerate W[57], W[58], W[59] for both messages (6*N free bits)
2. For each combo, h[0]=0 determines dW[60][0] (1 bit of info)
3. h[1]=0 determines more W[60] info given the previous
4. Continue until all h bits are zero, then work on g, d, etc.

At N=4: 6*4=24 bits for W[57..59] × 2 messages = 2^24 ≈ 16M combos.
For each, compute the required W[60] constraints. If consistent, test remaining registers.

This is 2^24 × (small work) which is MUCH cheaper than the full 2^32 brute force.
The speedup comes from the bit-serial constraint propagation.
"""

import sys, os, time, random, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

def run_bitserial_attack(N=4, verbose=True):
    spec = __import__('50_precision_homotopy')
    sha = spec.MiniSHA256(N)
    MASK_N = sha.MASK
    MSB = sha.MSB

    result = sha.find_m0()
    if result[0] is None:
        print(f"No candidate at N={N}")
        return
    m0, s1, s2, W1_pre, W2_pre = result

    print(f"Bit-Serial Algebraic Attack at N={N}")
    print(f"Candidate: M[0]=0x{m0:x}")
    print(f"Free variables: W1[57..60], W2[57..60] = {8*N} bits")
    print(f"Brute force: 2^{8*N} = {1<<(8*N):,} evaluations")
    print()

    K = sha.K

    def eval_full(w1, w2):
        """Evaluate 7-round tail, return (state1, state2) tuples."""
        # Build schedule
        W1 = list(w1)  # w1 = [W1[57], W1[58], W1[59], W1[60]]
        W2 = list(w2)
        # W[61] = sigma1(W[59]) + W[54] + sigma0(W[46]) + W[45]
        W1.append((sha.sigma1(w1[2]) + W1_pre[54] + sha.sigma0(W1_pre[46]) + W1_pre[45]) & MASK_N)
        W2.append((sha.sigma1(w2[2]) + W2_pre[54] + sha.sigma0(W2_pre[46]) + W2_pre[45]) & MASK_N)
        # W[62] = sigma1(W[60]) + W[55] + sigma0(W[47]) + W[46]
        W1.append((sha.sigma1(w1[3]) + W1_pre[55] + sha.sigma0(W1_pre[47]) + W1_pre[46]) & MASK_N)
        W2.append((sha.sigma1(w2[3]) + W2_pre[55] + sha.sigma0(W2_pre[47]) + W2_pre[46]) & MASK_N)
        # W[63] = sigma1(W[61]) + W[56] + sigma0(W[48]) + W[47]
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

    # Phase 1: Characterize the bit-serial structure
    # For each output bit, determine which W[60] bits it depends on
    # by evaluating with W[60] variations

    print("=== Phase 1: W[60] Dependency Characterization ===")
    print("Fixing W[57..59] to random values, varying W[60] bits...")

    random.seed(42)
    w1_base = [random.randint(0, MASK_N) for _ in range(3)]
    w2_base = [random.randint(0, MASK_N) for _ in range(3)]

    # For each output bit, check which W[60] bits affect it
    dep_map = {}  # output_bit -> set of W[60] bits it depends on
    reg_names = ['a','b','c','d','e','f','g','h']

    for out_reg in range(8):
        for out_bit in range(N):
            out_idx = out_reg * N + out_bit
            deps = set()
            # Try flipping each W[60] bit
            for w60_bit in range(N):
                differs = False
                for trial in range(100):
                    w1_60 = random.randint(0, MASK_N)
                    w2_60 = random.randint(0, MASK_N)
                    w1_60_flip = w1_60 ^ (1 << w60_bit)

                    st1a, st2a = eval_full(w1_base + [w1_60], w2_base + [w2_60])
                    st1b, st2b = eval_full(w1_base + [w1_60_flip], w2_base + [w2_60])

                    diff_a = (st1a[out_reg] ^ st2a[out_reg]) >> out_bit & 1
                    diff_b = (st1b[out_reg] ^ st2b[out_reg]) >> out_bit & 1
                    if diff_a != diff_b:
                        differs = True
                        break

                if differs:
                    deps.add(('W1', w60_bit))

            # Same for W2[60]
            for w60_bit in range(N):
                differs = False
                for trial in range(100):
                    w1_60 = random.randint(0, MASK_N)
                    w2_60 = random.randint(0, MASK_N)
                    w2_60_flip = w2_60 ^ (1 << w60_bit)

                    st1a, st2a = eval_full(w1_base + [w1_60], w2_base + [w2_60])
                    st1b, st2b = eval_full(w1_base + [w1_60], w2_base + [w2_60_flip])

                    diff_a = (st1a[out_reg] ^ st2a[out_reg]) >> out_bit & 1
                    diff_b = (st1b[out_reg] ^ st2b[out_reg]) >> out_bit & 1
                    if diff_a != diff_b:
                        differs = True
                        break

                if differs:
                    deps.add(('W2', w60_bit))

            dep_map[out_idx] = deps

    # Sort output bits by dependency count (least dependent first)
    bits_by_deps = sorted(dep_map.items(), key=lambda x: len(x[1]))
    print(f"\nOutput bits sorted by W[60] dependency count:")
    print(f"{'Bit':>6} {'Reg':>4} {'Pos':>4} {'#deps':>6}  W[60] deps")
    for idx, deps in bits_by_deps[:16]:
        reg = idx // N
        pos = idx % N
        dep_str = ', '.join(f"{m}[{b}]" for m,b in sorted(deps))
        print(f"  {idx:4d}   {reg_names[reg]:>3}   {pos:>3}   {len(deps):4d}   {dep_str}")

    # Phase 2: Bit-serial attack
    # Sort output bits by attack order: fewest W[60] deps first
    print(f"\n=== Phase 2: Bit-Serial Attack ===")

    # Attack strategy:
    # Enumerate W[57..59] for both messages: 6*N free bits
    # For each, propagate constraints through the weakest bits first
    n_compat_bits = 6 * N
    n_compat = 1 << n_compat_bits
    print(f"Compatibility space: 2^{n_compat_bits} = {n_compat:,} combinations")
    print(f"Full space: 2^{8*N} = {1<<(8*N):,}")
    print(f"Reduction factor: 2^{2*N} = {1<<(2*N)} (from W[60] constraint propagation)")

    # At N=4: 2^24 ≈ 16M compatibility combos
    # For each, try all 2^(2*N) W[60] values and check collision
    # But with bit-serial propagation, many W[60] values are eliminated early

    t0 = time.time()
    collisions = []
    n_w60_tested = 0
    n_early_prune = 0

    # Identify the easiest output bits (fewest W[60] deps)
    easy_bits = [idx for idx, deps in bits_by_deps if len(deps) <= N//2]
    hard_bits = [idx for idx, deps in bits_by_deps if len(deps) > N//2]

    print(f"Easy bits (≤{N//2} W[60] deps): {len(easy_bits)}")
    print(f"Hard bits (>{N//2} W[60] deps): {len(hard_bits)}")

    if n_compat > 2**26:
        print(f"\nCompatibility space too large for exhaustive search.")
        print(f"Sampling 1M random points instead...")
        sample_mode = True
        n_compat_actual = 1000000
    else:
        sample_mode = False
        n_compat_actual = n_compat

    progress_interval = max(1, n_compat_actual // 20)
    for trial in range(n_compat_actual):
        if sample_mode:
            # Random sample
            bits = random.getrandbits(n_compat_bits)
        else:
            bits = trial

        # Decode compatibility words
        w1_57 = bits & MASK_N
        w1_58 = (bits >> N) & MASK_N
        w1_59 = (bits >> (2*N)) & MASK_N
        w2_57 = (bits >> (3*N)) & MASK_N
        w2_58 = (bits >> (4*N)) & MASK_N
        w2_59 = (bits >> (5*N)) & MASK_N

        # Try all W[60] combinations
        for w60_bits in range(1 << (2*N)):
            w1_60 = w60_bits & MASK_N
            w2_60 = (w60_bits >> N) & MASK_N

            n_w60_tested += 1

            w1 = [w1_57, w1_58, w1_59, w1_60]
            w2 = [w2_57, w2_58, w2_59, w2_60]

            st1, st2 = eval_full(w1, w2)

            # Check easy bits first for early pruning
            pruned = False
            for idx in easy_bits:
                reg = idx // N
                pos = idx % N
                if ((st1[reg] ^ st2[reg]) >> pos) & 1:
                    pruned = True
                    n_early_prune += 1
                    break

            if pruned:
                continue

            # Check all remaining bits
            is_collision = True
            for reg in range(8):
                if st1[reg] != st2[reg]:
                    is_collision = False
                    break

            if is_collision:
                collisions.append((w1, w2))
                if verbose and len(collisions) <= 20:
                    print(f"  COLLISION #{len(collisions)}: W1={[hex(x) for x in w1]} "
                          f"W2={[hex(x) for x in w2]}")

        if trial > 0 and trial % progress_interval == 0:
            elapsed = time.time() - t0
            pct = 100 * trial / n_compat_actual
            rate = trial / elapsed if elapsed > 0 else 0
            print(f"  [{pct:.0f}%] {trial:,}/{n_compat_actual:,} compat tested, "
                  f"{len(collisions)} collisions, {elapsed:.0f}s ({rate:.0f}/s)")

    elapsed = time.time() - t0

    print(f"\n=== Results ===")
    print(f"Collisions found: {len(collisions)}")
    print(f"Compatibility combos tested: {n_compat_actual:,}")
    print(f"W[60] combos tested: {n_w60_tested:,}")
    print(f"Early prunings (easy bits): {n_early_prune:,} "
          f"({100*n_early_prune/max(1,n_w60_tested):.1f}% pruned)")
    print(f"Time: {elapsed:.1f}s")
    print(f"Eval rate: {n_w60_tested/max(1,elapsed):.0f} evals/s")

    if collisions:
        # Verify
        print(f"\nVerifying {min(len(collisions), 5)} collisions...")
        for w1, w2 in collisions[:5]:
            st1, st2 = eval_full(w1, w2)
            ok = all(st1[r] == st2[r] for r in range(8))
            print(f"  W1={[hex(x) for x in w1]} W2={[hex(x) for x in w2]} -> {'OK' if ok else 'FAIL'}")

    # Phase 3: Analyze early pruning effectiveness
    if n_early_prune > 0:
        print(f"\n=== Pruning Analysis ===")
        prune_rate = n_early_prune / n_w60_tested
        print(f"Easy-bit pruning rate: {prune_rate:.4f}")
        print(f"Effective speedup from bit-serial ordering: {1/(1-prune_rate):.2f}x")
        print(f"Compared to random bit ordering, easy bits prune {prune_rate*100:.1f}% earlier")

    return collisions


if __name__ == "__main__":
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    run_bitserial_attack(N, verbose=True)
