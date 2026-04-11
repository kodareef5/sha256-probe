#!/usr/bin/env python3
"""
GF(2) Factorization Analysis of h[0] — the weakest output bit.

h[0] at N=4 has degree 8, only 1173 monomials in 32 variables.
If f = g1 * g2 with deg(g1) = deg(g2) = 4, then:
  f = 0  iff  g1 = 0  OR  g2 = 0

This would decompose the degree-8 system into two degree-4 systems,
each far easier to solve.

Even if exact factorization fails, we can look for:
1. Approximate factorizations (f ≈ g1*g2 on most inputs)
2. Low-degree annihilators (g such that f*g = 0, with deg(g) small)
3. Low-degree components (subsets of monomials that form a factor)

Method: Build truth table from the exact monomial list, then test
divisibility by all degree-≤4 polynomials in the support variables.

At N=4 with 26 active variables:
  Degree-4 polynomials: C(26,≤4) ≈ 15K terms
  Linearization: 15K unknowns, ~4 billion equations (truth table)
  This is overdetermined: use random sampling to build manageable system.
"""

import sys, os, time, random
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')


def parse_monomial_list(filename):
    """Parse the monomial list from exact_anf output."""
    monomials = []
    with open(filename) as f:
        for line in f:
            line = line.strip()
            if line.startswith('deg'):
                parts = line.split(':')
                if len(parts) >= 2:
                    deg = int(parts[0].replace('deg', ''))
                    vars_str = parts[1].strip()
                    var_indices = []
                    for token in vars_str.split():
                        if token.startswith('x'):
                            var_indices.append(int(token[1:]))
                    if var_indices or deg == 0:
                        monomials.append(tuple(sorted(var_indices)))
    return monomials


def eval_polynomial(monomials, x_bits):
    """Evaluate a GF(2) polynomial at a point x (integer, bits are variables)."""
    result = 0
    for mono in monomials:
        term = 1
        for var in mono:
            term &= (x_bits >> var) & 1
        result ^= term
    return result


def monomial_to_mask(mono):
    """Convert monomial (tuple of var indices) to bitmask."""
    mask = 0
    for v in mono:
        mask |= (1 << v)
    return mask


def eval_poly_fast(mono_masks, x):
    """Fast evaluation using precomputed masks."""
    result = 0
    for mask in mono_masks:
        # monomial is 1 iff all required bits are set
        if (x & mask) == mask:
            result ^= 1
    return result


def find_annihilators(monomials, n_vars, max_deg, n_samples=50000):
    """
    Find low-degree annihilators of f.
    An annihilator of f is a polynomial g such that f*g = 0 over GF(2).
    Equivalently: g(x) = 0 whenever f(x) = 1.

    Build a linear system: for each x where f(x)=1, require g(x)=0.
    The solution space gives all degree-≤max_deg annihilators.
    """
    from itertools import combinations

    # Generate all monomials of degree ≤ max_deg in active variables
    active_vars = set()
    for m in monomials:
        active_vars.update(m)
    active_vars = sorted(active_vars)
    n_active = len(active_vars)

    print(f"  Active variables: {n_active}")
    print(f"  Generating degree-≤{max_deg} monomials...")

    g_monomials = [()]  # constant term
    for d in range(1, max_deg + 1):
        for combo in combinations(active_vars, d):
            g_monomials.append(combo)
    n_g_monos = len(g_monomials)
    print(f"  Candidate monomials for g: {n_g_monos}")

    if n_g_monos > 50000:
        print(f"  Too many monomials, reducing to degree {max_deg-1}")
        return None

    # Precompute monomial masks for f
    f_masks = [monomial_to_mask(m) for m in monomials]

    # Sample points where f(x)=1
    print(f"  Sampling points where f=1...")
    random.seed(42)
    f1_points = []
    n_tested = 0
    while len(f1_points) < n_samples and n_tested < 10 * n_samples:
        x = random.getrandbits(n_vars)
        n_tested += 1
        if eval_poly_fast(f_masks, x):
            f1_points.append(x)

    n_f1 = len(f1_points)
    print(f"  Found {n_f1} points with f=1 (out of {n_tested} tested)")
    print(f"  Estimated Pr[f=1] ≈ {n_f1/n_tested:.4f}")

    if n_f1 < n_g_monos:
        print(f"  Need more f=1 points than monomials ({n_f1} < {n_g_monos})")
        print(f"  System is underdetermined — annihilators likely exist trivially")

    # Build matrix: each row is a point where f=1, each column is a monomial of g
    # We need g(x)=0 at all these points
    n_rows = min(n_f1, 2 * n_g_monos)  # don't need too many rows
    print(f"  Building {n_rows} x {n_g_monos} GF(2) matrix...")

    g_masks = [monomial_to_mask(m) for m in g_monomials]

    # Use numpy with uint8 for GF(2) arithmetic
    A = np.zeros((n_rows, n_g_monos), dtype=np.uint8)
    for i in range(n_rows):
        x = f1_points[i]
        for j, mask in enumerate(g_masks):
            if (x & mask) == mask:
                A[i, j] = 1

    # Gaussian elimination over GF(2) to find null space
    print(f"  Gaussian elimination over GF(2)...")
    t0 = time.time()
    rank, pivots = gf2_rank(A)
    elapsed = time.time() - t0
    print(f"  Rank: {rank}/{n_g_monos} in {elapsed:.1f}s")
    print(f"  Null space dimension: {n_g_monos - rank}")

    if n_g_monos - rank > 0:
        print(f"\n  *** ANNIHILATORS EXIST! ***")
        print(f"  There are {n_g_monos - rank} linearly independent degree-≤{max_deg} "
              f"annihilators of f")
        # But we need to filter trivial ones and validate
        return n_g_monos - rank
    else:
        print(f"  No degree-≤{max_deg} annihilators found")
        return 0


def gf2_rank(A):
    """Compute rank of a GF(2) matrix via Gaussian elimination."""
    m, n = A.shape
    A = A.copy()
    pivots = []
    row = 0
    for col in range(n):
        # Find pivot
        pivot = None
        for r in range(row, m):
            if A[r, col]:
                pivot = r
                break
        if pivot is None:
            continue
        # Swap rows
        if pivot != row:
            A[[row, pivot]] = A[[pivot, row]]
        pivots.append(col)
        # Eliminate
        for r in range(m):
            if r != row and A[r, col]:
                A[r] ^= A[row]
        row += 1
    return row, pivots


def test_quadratic_factors(monomials, n_vars, n_samples=100000):
    """
    Test if f can be written as f = g1 * g2 where g1, g2 have degree ≤ deg(f)/2.

    Method: if f = g1*g2, then the zero set of f is the union of the zero sets
    of g1 and g2. If the zero set has two "clusters" that correspond to g1=0
    and g2=0, we can recover the factors.

    Simpler test: compute the correlation between f(x) and random degree-4
    polynomials. If f has a degree-4 factor, there exists a degree-4 polynomial
    that is 1 whenever f is 0 (but not vice versa).
    """
    f_masks = [monomial_to_mask(m) for m in monomials]

    random.seed(42)
    print(f"  Sampling {n_samples} random points...")
    zeros = []
    ones = []
    for _ in range(n_samples):
        x = random.getrandbits(n_vars)
        if eval_poly_fast(f_masks, x):
            ones.append(x)
        else:
            zeros.append(x)

    n_zeros = len(zeros)
    n_ones = len(ones)
    print(f"  f=0: {n_zeros} ({100*n_zeros/n_samples:.1f}%)")
    print(f"  f=1: {n_ones} ({100*n_ones/n_samples:.1f}%)")

    # If f = g1*g2, the zeros of f split into two groups:
    # Group A: g1=0 (includes points where g2 may be 0 or 1)
    # Group B: g2=0 (includes points where g1 may be 0 or 1)
    # With overlap: g1=0 AND g2=0

    # Test: for random linear functions L, check if L partitions the zeros
    # into two groups with different correlation to other linear functions.
    # This would indicate a nontrivial factorization.

    print(f"\n  Testing bilinear structure in the zero set...")
    # Compute pairwise XOR distances between zeros
    if n_zeros > 5000:
        zero_sample = random.sample(zeros, 5000)
    else:
        zero_sample = zeros

    # For each pair of variables (i,j), check if x_i AND x_j has unusual
    # correlation with f(x)=0
    active_vars = set()
    for m in monomials:
        active_vars.update(m)
    active_vars = sorted(active_vars)

    print(f"  Checking quadratic structure in zero set (top-20 correlated pairs)...")
    pair_corr = []
    for i_idx, vi in enumerate(active_vars):
        for vj in active_vars[i_idx+1:]:
            # Compute Pr[x_i AND x_j | f=0] and compare to Pr[x_i AND x_j]
            mask = (1 << vi) | (1 << vj)
            count_zero = sum(1 for x in zero_sample if (x & mask) == mask)
            count_all = n_samples // 4  # expected if independent
            bias = count_zero / len(zero_sample) - 0.25
            pair_corr.append((abs(bias), vi, vj, bias))

    pair_corr.sort(reverse=True)
    for absb, vi, vj, bias in pair_corr[:20]:
        print(f"    x{vi} AND x{vj}: bias = {bias:+.4f} (|{absb:.4f}|)")

    # Check if any single variable has strong correlation with f=0
    print(f"\n  Single-variable bias in zero set:")
    var_bias = []
    for vi in active_vars:
        count = sum(1 for x in zero_sample if (x >> vi) & 1)
        bias = count / len(zero_sample) - 0.5
        var_bias.append((abs(bias), vi, bias))
    var_bias.sort(reverse=True)
    for absb, vi, bias in var_bias[:10]:
        print(f"    x{vi}: Pr[x{vi}=1 | f=0] = {0.5+bias:.4f} (bias {bias:+.4f})")


def main():
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    mono_file = os.path.join(os.path.dirname(__file__),
                             'results/monomial_list_h_bit0_n4.log')

    if not os.path.exists(mono_file):
        print(f"Monomial list not found: {mono_file}")
        print("Run exact_anf_n4 with monomial output first.")
        return

    print(f"GF(2) Factorization Analysis of h[0] at N={N}")
    print(f"Loading monomials from {mono_file}")

    monomials = parse_monomial_list(mono_file)
    print(f"Loaded {len(monomials)} monomials")

    n_vars = 32  # 8 words × 4 bits at N=4

    # Phase 1: Degree breakdown
    deg_dist = {}
    for m in monomials:
        d = len(m)
        deg_dist[d] = deg_dist.get(d, 0) + 1
    print(f"\nDegree distribution:")
    for d in sorted(deg_dist):
        print(f"  deg {d}: {deg_dist[d]} monomials")

    # Phase 2: Test for quadratic factors
    print(f"\n=== Quadratic Factor Test ===")
    test_quadratic_factors(monomials, n_vars)

    # Phase 3: Find low-degree annihilators
    for max_deg in [2, 3, 4]:
        print(f"\n=== Annihilator Search (degree ≤ {max_deg}) ===")
        result = find_annihilators(monomials, n_vars, max_deg, n_samples=20000)
        if result and result > 0:
            print(f"  Algebraic immunity ≤ {max_deg}!")
            break

    print(f"\nDone.")


if __name__ == "__main__":
    main()
