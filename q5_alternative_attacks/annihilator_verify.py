#!/usr/bin/env python3
"""
Verify annihilator finding for h[0] at N=4.

Uses direct function evaluation (not monomial list) to test whether
degree-≤4 annihilators actually exist for the FULL h[0] polynomial.

Method: sample points where h[0]=1, build the constraint matrix for g,
check if the null space of the constraint matrix is nontrivial.
"""

import sys, os, time, random
from itertools import combinations
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')


def main():
    spec = __import__('50_precision_homotopy')
    sha = spec.MiniSHA256(4)
    MASK_N = sha.MASK
    K = sha.K

    result = sha.find_m0()
    if result[0] is None:
        print("No candidate at N=4")
        return
    m0, s1, s2, W1_pre, W2_pre = result

    print(f"Annihilator Verification for h[0] at N=4")
    print(f"Candidate: M[0]=0x{m0:x}")
    print(f"Using DIRECT function evaluation (not monomial list)")
    print()

    def eval_h0(x):
        """Evaluate h[0] of the collision difference function at input x.
        x is a 32-bit integer encoding (W1[57..60], W2[57..60])."""
        w1 = [(x >> (i*4)) & MASK_N for i in range(4)]
        w2 = [(x >> ((4+i)*4)) & MASK_N for i in range(4)]

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
            T1a = (h1 + sha.Sigma1(e1) + sha.ch(e1,f1,g1) + K[57+i] + W1[i]) & MASK_N
            T2a = (sha.Sigma0(a1) + sha.maj(a1,b1,c1)) & MASK_N
            h1,g1,f1,e1,d1,c1,b1,a1 = g1,f1,e1,(d1+T1a)&MASK_N,c1,b1,a1,(T1a+T2a)&MASK_N
            T1b = (h2 + sha.Sigma1(e2) + sha.ch(e2,f2,g2) + K[57+i] + W2[i]) & MASK_N
            T2b = (sha.Sigma0(a2) + sha.maj(a2,b2,c2)) & MASK_N
            h2,g2,f2,e2,d2,c2,b2,a2 = g2,f2,e2,(d2+T1b)&MASK_N,c2,b2,a2,(T1b+T2b)&MASK_N

        # Return bit 0 of h1 XOR h2 (register h, position 0)
        return (h1 ^ h2) & 1

    # Step 1: Sample points where h[0] = 1
    print("Sampling points where h[0]=1...")
    random.seed(42)
    f1_points = []
    f0_points = []
    n_tested = 0

    while len(f1_points) < 25000 and n_tested < 100000:
        x = random.getrandbits(32)
        n_tested += 1
        if eval_h0(x):
            f1_points.append(x)
        else:
            f0_points.append(x)

    print(f"  f=1: {len(f1_points)} points")
    print(f"  f=0: {len(f0_points)} points")
    print(f"  Pr[f=1] ≈ {len(f1_points)/n_tested:.4f}")

    # Step 2: Determine active variables
    # From the exact ANF, we know variables x13,x14,x15,x29,x30,x31 are absent
    # Let's verify this empirically
    active_vars = list(range(32))
    # Remove known absent variables for efficiency
    absent = {13, 14, 15, 29, 30, 31}
    active_vars = [v for v in active_vars if v not in absent]
    n_active = len(active_vars)
    print(f"\n  Active variables: {n_active} (removed {sorted(absent)})")

    # Step 3: Build degree-≤d monomial basis
    for max_deg in [3, 4]:
        print(f"\n=== Annihilator Search: degree ≤ {max_deg} ===")

        g_monomials = [()]  # constant term
        for d in range(1, max_deg + 1):
            for combo in combinations(active_vars, d):
                g_monomials.append(combo)
        n_g = len(g_monomials)
        print(f"  Monomial basis size: {n_g}")

        if n_g > 30000:
            print(f"  Too large, skipping")
            continue

        # Step 4: Build constraint matrix
        # For annihilators of f: g(x) = 0 whenever f(x) = 1
        n_constraints = min(len(f1_points), 2 * n_g)
        print(f"  Building {n_constraints} x {n_g} GF(2) matrix...")

        A = np.zeros((n_constraints, n_g), dtype=np.uint8)
        for i in range(n_constraints):
            x = f1_points[i]
            for j, mono in enumerate(g_monomials):
                # Evaluate monomial at x
                val = 1
                for var in mono:
                    val &= (x >> var) & 1
                A[i, j] = val

        # Step 5: Gaussian elimination over GF(2)
        print(f"  Gaussian elimination...")
        t0 = time.time()
        m, n = A.shape
        A_copy = A.copy()
        pivots = []
        row = 0
        for col in range(n):
            # Find pivot
            pivot = None
            for r in range(row, m):
                if A_copy[r, col]:
                    pivot = r
                    break
            if pivot is None:
                continue
            if pivot != row:
                A_copy[[row, pivot]] = A_copy[[pivot, row]]
            pivots.append(col)
            for r in range(m):
                if r != row and A_copy[r, col]:
                    A_copy[r] ^= A_copy[row]
            row += 1
        rank = row
        elapsed = time.time() - t0

        null_dim = n_g - rank
        print(f"  Rank: {rank}/{n_g} in {elapsed:.1f}s")
        print(f"  Null space dimension: {null_dim}")

        if null_dim > 0:
            print(f"\n  *** {null_dim} degree-≤{max_deg} ANNIHILATORS FOUND ***")
            print(f"  Algebraic immunity ≤ {max_deg}")

            # VERIFY: check that these annihilators actually satisfy f·g = 0
            # on INDEPENDENT test points (not used in the matrix)
            print(f"\n  Verifying on {min(len(f1_points) - n_constraints, 5000)} "
                  f"independent f=1 points...")

            # Extract a null space vector
            free_cols = [c for c in range(n_g) if c not in pivots]
            if free_cols:
                # Build one annihilator from the null space
                ann_coeffs = np.zeros(n_g, dtype=np.uint8)
                fc = free_cols[0]
                ann_coeffs[fc] = 1
                # Back-substitute
                for r in range(rank - 1, -1, -1):
                    if A_copy[r, fc]:
                        ann_coeffs[pivots[r]] = 1

                # Count how many terms
                n_terms = int(np.sum(ann_coeffs))
                ann_monos = [g_monomials[j] for j in range(n_g) if ann_coeffs[j]]
                print(f"  Example annihilator: {n_terms} terms")
                if n_terms <= 20:
                    for mono in ann_monos:
                        if mono:
                            print(f"    {'·'.join(f'x{v}' for v in mono)}")
                        else:
                            print(f"    1 (constant)")

                # Verify on test points
                n_verify = min(len(f1_points) - n_constraints, 5000)
                n_violations = 0
                for i in range(n_constraints, n_constraints + n_verify):
                    if i >= len(f1_points):
                        break
                    x = f1_points[i]
                    # Evaluate annihilator at this point
                    g_val = 0
                    for mono in ann_monos:
                        term = 1
                        for var in mono:
                            term &= (x >> var) & 1
                        g_val ^= term
                    if g_val != 0:
                        n_violations += 1

                print(f"  Verification: {n_violations}/{n_verify} violations")
                if n_violations == 0:
                    print(f"  *** VERIFIED: annihilator holds on all test points! ***")
                else:
                    print(f"  *** FAILED: {n_violations} violations "
                          f"({100*n_violations/n_verify:.1f}%) ***")
                    print(f"  The annihilator finding was an artifact of the "
                          f"constraint matrix construction")

                # Also check on f=0 points (annihilator should be free here)
                print(f"\n  Checking annihilator behavior on f=0 points:")
                n_check = min(len(f0_points), 5000)
                g_at_f0 = 0
                for i in range(n_check):
                    x = f0_points[i]
                    g_val = 0
                    for mono in ann_monos:
                        term = 1
                        for var in mono:
                            term &= (x >> var) & 1
                        g_val ^= term
                    g_at_f0 += g_val
                print(f"  g=1 on f=0 points: {g_at_f0}/{n_check} "
                      f"({100*g_at_f0/n_check:.1f}%)")
                print(f"  (Should be ~50% if g is a proper annihilator)")
        else:
            print(f"  No degree-≤{max_deg} annihilators found")
            print(f"  Algebraic immunity > {max_deg}")

    print(f"\nDone.")


if __name__ == "__main__":
    main()
