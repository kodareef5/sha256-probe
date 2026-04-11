#!/usr/bin/env python3
"""
Analyze near-collision solutions: what does dh look like when a-g match?

For each near-collision solution (registers a-g equal, h free), we:
1. Re-evaluate to extract actual W values and dh
2. Characterize the dh distribution
3. Look for patterns: is dh always in a small subspace?
4. Check if dh has low Hamming weight
5. Look for linear relations among the dh values
"""
import sys, os, time, random, collections
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')


def analyze_n8():
    """Generate near-collisions at N=8 by exhaustive search and analyze dh."""
    spec = __import__('50_precision_homotopy')
    sha = spec.MiniSHA256(8)
    MASK = sha.MASK
    K = sha.K
    m0, s1, s2, W1p, W2p = sha.find_m0()
    if m0 is None:
        print("No candidate"); return

    print(f"Near-Collision dh Analysis at N=8")
    print(f"Candidate: M[0]=0x{m0:02x}")
    print(f"Finding near-collisions (a-g match, h free) by random search...")

    def eval_full(w1, w2):
        W1, W2 = list(w1), list(w2)
        W1.append((sha.sigma1(w1[2]) + W1p[54] + sha.sigma0(W1p[46]) + W1p[45]) & MASK)
        W2.append((sha.sigma1(w2[2]) + W2p[54] + sha.sigma0(W2p[46]) + W2p[45]) & MASK)
        W1.append((sha.sigma1(w1[3]) + W1p[55] + sha.sigma0(W1p[47]) + W1p[46]) & MASK)
        W2.append((sha.sigma1(w2[3]) + W2p[55] + sha.sigma0(W2p[47]) + W2p[46]) & MASK)
        W1.append((sha.sigma1(W1[4]) + W1p[56] + sha.sigma0(W1p[48]) + W1p[47]) & MASK)
        W2.append((sha.sigma1(W2[4]) + W2p[56] + sha.sigma0(W2p[48]) + W2p[47]) & MASK)
        a1,b1,c1,d1,e1,f1,g1,h1 = s1
        a2,b2,c2,d2,e2,f2,g2,h2 = s2
        for i in range(7):
            T1a=(h1+sha.Sigma1(e1)+sha.ch(e1,f1,g1)+K[57+i]+W1[i])&MASK
            T2a=(sha.Sigma0(a1)+sha.maj(a1,b1,c1))&MASK
            h1,g1,f1,e1,d1,c1,b1,a1=g1,f1,e1,(d1+T1a)&MASK,c1,b1,a1,(T1a+T2a)&MASK
            T1b=(h2+sha.Sigma1(e2)+sha.ch(e2,f2,g2)+K[57+i]+W2[i])&MASK
            T2b=(sha.Sigma0(a2)+sha.maj(a2,b2,c2))&MASK
            h2,g2,f2,e2,d2,c2,b2,a2=g2,f2,e2,(d2+T1b)&MASK,c2,b2,a2,(T1b+T2b)&MASK
        return (a1,b1,c1,d1,e1,f1,g1,h1), (a2,b2,c2,d2,e2,f2,g2,h2)

    # Use SAT solutions from the near_collision_skip_h run,
    # OR find them by random search (at N=8, collision density is ~95/2^64,
    # near-collision density should be much higher)

    # Method: enumerate systematically. At N=8 with 64 free bits,
    # random search won't find near-collisions either.
    # But we KNOW 95 full collisions exist. Each full collision is also
    # a near-collision. Plus there should be MORE near-collisions.

    # Better approach: enumerate small neighborhoods of known collision solutions
    # At N=8, we can use the SAT solutions from the topology study.
    # For now, use the cascade chain to find near-collisions.

    # Cascade constant
    dh56 = (s1[7] - s2[7]) & MASK
    dSig1 = (sha.Sigma1(s1[4]) - sha.Sigma1(s2[4])) & MASK
    dCh = (sha.ch(s1[4],s1[5],s1[6]) - sha.ch(s2[4],s2[5],s2[6])) & MASK
    T2_1 = (sha.Sigma0(s1[0]) + sha.maj(s1[0],s1[1],s1[2])) & MASK
    T2_2 = (sha.Sigma0(s2[0]) + sha.maj(s2[0],s2[1],s2[2])) & MASK
    C_w57 = (dh56 + dSig1 + dCh + (T2_1 - T2_2)) & MASK

    print(f"  Cascade: W2[57] = W1[57] + 0x{C_w57:02x}")

    # Random search with cascade constraint
    random.seed(42)
    near_collisions = []  # (w1, w2, dh_xor, dh_add)
    full_collisions = []
    n_tested = 0
    t0 = time.time()

    while len(near_collisions) < 200 and n_tested < 50000000:
        w1_57 = random.randint(0, MASK)
        w2_57 = (w1_57 + C_w57) & MASK
        w1 = [w1_57, random.randint(0,MASK), random.randint(0,MASK), random.randint(0,MASK)]
        w2 = [w2_57, random.randint(0,MASK), random.randint(0,MASK), random.randint(0,MASK)]

        st1, st2 = eval_full(w1, w2)
        n_tested += 1

        # Check a-g match
        ag_match = all(st1[i] == st2[i] for i in range(7))
        if ag_match:
            dh_xor = st1[7] ^ st2[7]
            dh_add = (st1[7] - st2[7]) & MASK
            near_collisions.append((w1, w2, dh_xor, dh_add, st1[7], st2[7]))
            if dh_xor == 0:
                full_collisions.append((w1, w2))
            if len(near_collisions) <= 10:
                print(f"  NC #{len(near_collisions)}: dh_xor=0x{dh_xor:02x} "
                      f"(hw={bin(dh_xor).count('1')}) dh_add=0x{dh_add:02x} "
                      f"at {n_tested} samples")

        if n_tested % 5000000 == 0:
            elapsed = time.time() - t0
            rate = n_tested / elapsed
            print(f"  [{n_tested/1e6:.0f}M] {len(near_collisions)} NCs, "
                  f"{len(full_collisions)} full, {rate/1e6:.1f}M/s")

    elapsed = time.time() - t0
    print(f"\nSearch complete: {n_tested} tested in {elapsed:.0f}s")
    print(f"Near-collisions (a-g match): {len(near_collisions)}")
    print(f"Full collisions (all match): {len(full_collisions)}")
    print(f"NC rate: 1 per {n_tested/max(1,len(near_collisions)):.0f} samples")

    if not near_collisions:
        print("No near-collisions found. Try SAT-based approach.")
        return

    # Analyze dh distribution
    print(f"\n=== dh XOR Distribution ===")
    dh_xors = [nc[2] for nc in near_collisions]
    dh_hws = [bin(d).count('1') for d in dh_xors]
    print(f"  Distinct dh values: {len(set(dh_xors))}/{len(dh_xors)}")
    print(f"  dh HW: min={min(dh_hws)}, max={max(dh_hws)}, mean={np.mean(dh_hws):.1f}")

    hw_dist = collections.Counter(dh_hws)
    print(f"  HW distribution:")
    for hw in sorted(hw_dist):
        print(f"    hw={hw}: {hw_dist[hw]} ({100*hw_dist[hw]/len(dh_hws):.1f}%)")

    # Check if dh values span a small subspace
    print(f"\n=== dh Subspace Analysis ===")
    dh_bits = np.array([[((d >> b) & 1) for b in range(8)] for d in dh_xors], dtype=np.uint8)
    # GF(2) rank
    A = dh_bits.copy()
    rank = 0
    for col in range(8):
        piv = None
        for r in range(rank, A.shape[0]):
            if A[r, col]: piv = r; break
        if piv is None: continue
        if piv != rank: A[[rank, piv]] = A[[piv, rank]]
        for r in range(A.shape[0]):
            if r != rank and A[r, col]: A[r] ^= A[rank]
        rank += 1
    print(f"  GF(2) rank of dh values: {rank}/8")
    if rank < 8:
        print(f"  *** dh is confined to a {rank}-dim subspace! ***")
        print(f"  This means {8-rank} bits of h are DETERMINED by a-g match!")
    else:
        print(f"  dh spans full 8-bit space (no subspace constraint)")

    # Additive difference analysis
    print(f"\n=== dh Additive Distribution ===")
    dh_adds = [nc[3] for nc in near_collisions]
    print(f"  Distinct dh_add values: {len(set(dh_adds))}")
    add_dist = collections.Counter(dh_adds)
    for val, count in add_dist.most_common(10):
        print(f"    dh_add=0x{val:02x} ({val:3d}): {count} times")

    # Check if dh_add is always constant
    if len(set(dh_adds)) == 1:
        print(f"\n  *** dh ADDITIVE DIFFERENCE IS CONSTANT: 0x{dh_adds[0]:02x} ***")
        print(f"  This means h1 - h2 is the SAME for all near-collisions!")
        print(f"  Collision requires dh_add = 0, which constrains h1 = h2 exactly.")

    print(f"\nDone.")


if __name__ == "__main__":
    analyze_n8()
