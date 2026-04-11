#!/usr/bin/env python3
"""
Solution Variety Analysis: algebraic structure of collision solutions.

We have 49 collision solutions at N=4. Key questions:
1. Do the solutions form a coset of a linear subspace over GF(2)?
2. What's the dimension of the affine span?
3. Are there algebraic relations between solution coordinates?
4. Can we predict new solutions from old ones?

If the solutions span a k-dimensional affine subspace, then:
- Total solutions = 2^k (we've found 49)
- If k=6: 64 total solutions (49/64 = 77% found)
- If k=5: only 32 (but 49>32, so k≥6)
- The (32-k) constraints reduce the search space exponentially

Even if the full solution set isn't affine, the AFFINE HULL reveals
the maximum linear structure. Deviations from linearity quantify
the nonlinear complexity of the collision condition.
"""

import sys, os, time, random
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')


def find_all_collisions_n4():
    """Find all collisions at N=4 exhaustively."""
    spec = __import__('50_precision_homotopy')
    sha = spec.MiniSHA256(4)
    MASK_N = sha.MASK
    K = sha.K

    result = sha.find_m0()
    if result[0] is None:
        return None, None, None
    m0, s1, s2, W1_pre, W2_pre = result

    collisions = []
    for inp in range(1 << 32):
        w1 = [(inp >> (i*4)) & MASK_N for i in range(4)]
        w2 = [(inp >> ((4+i)*4)) & MASK_N for i in range(4)]

        W1 = list(w1)
        W2 = list(w2)
        W1.append((sha.sigma1(w1[2]) + W1_pre[54] + sha.sigma0(W1_pre[46]) + W1_pre[45]) & MASK_N)
        W2.append((sha.sigma1(w2[2]) + W2_pre[54] + sha.sigma0(W2_pre[46]) + W2_pre[45]) & MASK_N)
        W1.append((sha.sigma1(w1[3]) + W1_pre[55] + sha.sigma0(W1_pre[47]) + W1_pre[46]) & MASK_N)
        W2.append((sha.sigma1(w2[3]) + W2_pre[55] + sha.sigma0(W2_pre[47]) + W2_pre[46]) & MASK_N)
        W1.append((sha.sigma1(W1[4]) + W1_pre[56] + sha.sigma0(W1_pre[48]) + W1_pre[47]) & MASK_N)
        W2.append((sha.sigma1(W2[4]) + W2_pre[56] + sha.sigma0(W2_pre[48]) + W2_pre[47]) & MASK_N)

        a1,b1,c1,d1,e1,f1,g1,h1 = s1
        a2,b2,c2,d2,e2,f2,g2,h2 = s2
        for i in range(7):
            T1a = (h1+sha.Sigma1(e1)+sha.ch(e1,f1,g1)+K[57+i]+W1[i]) & MASK_N
            T2a = (sha.Sigma0(a1)+sha.maj(a1,b1,c1)) & MASK_N
            h1,g1,f1,e1,d1,c1,b1,a1 = g1,f1,e1,(d1+T1a)&MASK_N,c1,b1,a1,(T1a+T2a)&MASK_N
            T1b = (h2+sha.Sigma1(e2)+sha.ch(e2,f2,g2)+K[57+i]+W2[i]) & MASK_N
            T2b = (sha.Sigma0(a2)+sha.maj(a2,b2,c2)) & MASK_N
            h2,g2,f2,e2,d2,c2,b2,a2 = g2,f2,e2,(d2+T1b)&MASK_N,c2,b2,a2,(T1b+T2b)&MASK_N

        if all(((v1^v2)&MASK_N) == 0 for v1,v2 in
               [(a1,a2),(b1,b2),(c1,c2),(d1,d2),(e1,e2),(f1,f2),(g1,g2),(h1,h2)]):
            collisions.append(inp)

        if inp > 0 and inp % (1 << 28) == 0:
            print(f"  [{inp >> 28}/16] {len(collisions)} collisions so far...")

    return collisions, m0, sha


def main():
    N = 4
    print(f"Solution Variety Analysis at N={N}")
    print(f"Exhaustive search for all collisions...")

    t0 = time.time()
    collisions, m0, sha = find_all_collisions_n4()
    elapsed = time.time() - t0

    if collisions is None:
        print("No candidate")
        return

    n_sol = len(collisions)
    print(f"\nFound {n_sol} collisions in {elapsed:.0f}s")
    print(f"Candidate: M[0]=0x{m0:x}")

    # Convert to binary matrix (n_sol × 32)
    S = np.zeros((n_sol, 32), dtype=np.uint8)
    for i, inp in enumerate(collisions):
        for bit in range(32):
            S[i, bit] = (inp >> bit) & 1

    # 1. Affine span analysis
    print(f"\n=== Affine Span Analysis ===")
    # Translate to origin: S' = S XOR S[0]
    origin = S[0].copy()
    S_centered = S ^ origin[np.newaxis, :]

    # Rank of centered matrix = dimension of affine span
    rank = gf2_rank(S_centered)
    print(f"  Affine dimension: {rank}")
    print(f"  If solutions were a {rank}-dim affine subspace: 2^{rank} = {1<<rank} solutions")
    print(f"  Actual solutions: {n_sol}")
    if n_sol == (1 << rank):
        print(f"  *** SOLUTIONS FORM A PERFECT AFFINE SUBSPACE! ***")
        print(f"  This means the collision condition is LINEAR in {rank} variables!")
    elif n_sol < (1 << rank):
        print(f"  Solutions are a PROPER SUBSET of their affine span")
        print(f"  Density: {n_sol}/{1<<rank} = {n_sol/(1<<rank):.4f}")
        print(f"  Nonlinear constraints reduce 2^{rank} to {n_sol}")
    else:
        print(f"  ERROR: more solutions than affine span allows?")

    # 2. Linear independence analysis
    print(f"\n=== Linear Independence ===")
    # Which columns of S are linearly dependent?
    col_rank = gf2_rank(S.T)
    print(f"  Column rank: {col_rank}/32")
    print(f"  {32 - col_rank} coordinate constraints (columns in the span of others)")

    # 3. Find the linear constraints
    print(f"\n=== Linear Constraints ===")
    # For each bit position, check if it's determined by the others
    # via a linear relation over GF(2)
    constraints = []
    for target_bit in range(32):
        # Build system: predict target_bit from all other bits
        other_bits = [b for b in range(32) if b != target_bit]
        A = S[:, other_bits].copy()
        b = S[:, target_bit].copy()

        # Solve A*x = b over GF(2) via augmented matrix
        aug = np.hstack([A, b.reshape(-1, 1)])
        rank_aug = gf2_rank(aug)
        rank_A = gf2_rank(A)

        if rank_aug == rank_A:
            # System is consistent — target_bit IS a linear function of others
            # Find the actual coefficients
            coeffs = solve_gf2(A, b)
            if coeffs is not None:
                active = [other_bits[j] for j in range(len(coeffs)) if coeffs[j]]
                constraints.append((target_bit, active))

    if constraints:
        print(f"  Found {len(constraints)} linear constraints:")
        for target, deps in constraints:
            reg_t = ['W1[57]','W1[58]','W1[59]','W1[60]','W2[57]','W2[58]','W2[59]','W2[60]'][target//4]
            bit_t = target % 4
            dep_strs = [f"x{d}" for d in deps]
            print(f"    x{target} ({reg_t}[{bit_t}]) = " + " ⊕ ".join(dep_strs[:8])
                  + (f" + {len(dep_strs)-8} more" if len(dep_strs) > 8 else ""))
    else:
        print(f"  No pure linear constraints found")

    # 4. Pairwise XOR closure test
    print(f"\n=== XOR Closure Test ===")
    # If solutions form a coset, then s_i XOR s_j XOR s_0 is also a solution
    solution_set = set(collisions)
    n_xor_pairs = 0
    n_closed = 0
    for i in range(min(n_sol, 30)):
        for j in range(i+1, min(n_sol, 30)):
            s_new = collisions[i] ^ collisions[j] ^ collisions[0]
            n_xor_pairs += 1
            if s_new in solution_set:
                n_closed += 1

    print(f"  XOR closure: {n_closed}/{n_xor_pairs} "
          f"({100*n_closed/max(1,n_xor_pairs):.1f}%)")
    if n_closed == n_xor_pairs:
        print(f"  *** PERFECT XOR CLOSURE: solutions form a coset! ***")
    else:
        print(f"  Not fully closed — nonlinear component present")

    # 5. Principal Component Analysis (over GF(2): find the basis of the span)
    print(f"\n=== Affine Basis ===")
    basis_vectors = find_gf2_basis(S_centered)
    print(f"  Basis vectors: {len(basis_vectors)}")
    for i, vec in enumerate(basis_vectors[:6]):
        bits = [j for j in range(32) if vec[j]]
        word_decode = []
        for b in bits:
            word = ['W1[57]','W1[58]','W1[59]','W1[60]',
                    'W2[57]','W2[58]','W2[59]','W2[60]'][b//4]
            pos = b % 4
            word_decode.append(f"{word}[{pos}]")
        print(f"    v{i}: {' '.join(word_decode[:6])}"
              + (f" +{len(word_decode)-6}more" if len(word_decode) > 6 else ""))

    # 6. Hamming weight distribution
    print(f"\n=== Solution Hamming Weight ===")
    hws = [bin(c).count('1') for c in collisions]
    print(f"  Mean: {np.mean(hws):.1f}")
    print(f"  Min: {min(hws)}, Max: {max(hws)}")
    print(f"  Std: {np.std(hws):.1f}")
    print(f"  Expected random: {16.0}")

    print(f"\nDone.")


def gf2_rank(A):
    """Rank of a GF(2) matrix."""
    m, n = A.shape
    A = A.copy()
    row = 0
    for col in range(n):
        pivot = None
        for r in range(row, m):
            if A[r, col]:
                pivot = r
                break
        if pivot is None:
            continue
        if pivot != row:
            A[[row, pivot]] = A[[pivot, row]]
        for r in range(m):
            if r != row and A[r, col]:
                A[r] ^= A[row]
        row += 1
    return row


def solve_gf2(A, b):
    """Solve Ax = b over GF(2). Returns None if no solution."""
    m, n = A.shape
    aug = np.hstack([A, b.reshape(-1, 1)]).copy()
    pivots = []
    row = 0
    for col in range(n):
        pivot = None
        for r in range(row, m):
            if aug[r, col]:
                pivot = r
                break
        if pivot is None:
            continue
        if pivot != row:
            aug[[row, pivot]] = aug[[pivot, row]]
        pivots.append(col)
        for r in range(m):
            if r != row and aug[r, col]:
                aug[r] ^= aug[row]
        row += 1
    # Check consistency
    for r in range(row, m):
        if aug[r, n]:
            return None  # Inconsistent
    # Extract solution
    x = np.zeros(n, dtype=np.uint8)
    for i, col in enumerate(pivots):
        x[col] = aug[i, n]
    return x


def find_gf2_basis(S):
    """Find a basis for the row span of S over GF(2)."""
    A = S.copy()
    m, n = A.shape
    basis = []
    row = 0
    for col in range(n):
        pivot = None
        for r in range(row, m):
            if A[r, col]:
                pivot = r
                break
        if pivot is None:
            continue
        if pivot != row:
            A[[row, pivot]] = A[[pivot, row]]
        basis.append(A[row].copy())
        for r in range(m):
            if r != row and A[r, col]:
                A[r] ^= A[row]
        row += 1
    return basis


if __name__ == "__main__":
    main()
