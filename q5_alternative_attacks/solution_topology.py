#!/usr/bin/env python3
"""
solution_topology.py — Characterize the N=8 sr=60 solution space (Issue #12)

Collects many SAT solutions for a single N=8 candidate, then analyzes:
1. Pairwise Hamming distance distribution
2. Backbone variables (bits fixed across >90% of solutions)
3. Clustering structure (do solutions form islands?)
4. Per-bit entropy (which free bits are most constrained?)

This tells us whether the solution space has exploitable STRUCTURE
or is essentially random.

Usage: python3 solution_topology.py [n_solutions] [timeout_per_solve]
"""

import sys, os, time, subprocess, tempfile, random
import numpy as np
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
import importlib.util
spec = importlib.util.spec_from_file_location('n8',
    '/root/sha256_probe/q5_alternative_attacks/n8_hw_dw56_solver_test.py')
n8 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(n8)


def collect_solutions(m0, fill, n_solutions=200, timeout=30, N=8):
    """Collect multiple SAT solutions by adding blocking clauses."""
    cnf, W1, W2 = n8.encode_n8_sr60(m0, fill, N)

    # Identify the free word variables (first allocated vars after constants)
    # In our encoding, free words are allocated as the first non-constant vars.
    # We need to find them from the CNF builder.
    # The free words are 4 words × N bits × 2 messages = 4*N*2 = 64 bits at N=8
    n_free_bits = 4 * N * 2  # 64 for N=8

    # Free vars are typically vars 1..n_free_bits (first allocated)
    # Verify by checking var names if available
    free_vars = list(range(1, n_free_bits + 1))

    tmpdir = tempfile.mkdtemp()
    base_cnf = os.path.join(tmpdir, "base.cnf")
    cnf.write_dimacs(base_cnf)

    # Read the base CNF
    with open(base_cnf) as f:
        lines = f.readlines()

    # Parse header
    header_idx = None
    for i, line in enumerate(lines):
        if line.startswith('p cnf'):
            header_idx = i
            parts = line.split()
            n_vars = int(parts[2])
            n_clauses = int(parts[3])
            break

    clause_lines = [l for l in lines[header_idx+1:] if l.strip() and not l.startswith('c')]

    solutions = []
    blocking_clauses = []

    for trial in range(n_solutions * 3):  # allow some failures
        if len(solutions) >= n_solutions:
            break

        # Write CNF with blocking clauses
        total_clauses = n_clauses + len(blocking_clauses)
        aug_cnf = os.path.join(tmpdir, f"aug_{trial}.cnf")
        with open(aug_cnf, 'w') as f:
            f.write(f"p cnf {n_vars} {total_clauses}\n")
            for line in clause_lines:
                f.write(line)
            for bc in blocking_clauses:
                f.write(bc + "\n")

        # Solve with random seed
        seed = random.randint(1, 10000)
        try:
            proc = subprocess.run(
                ['kissat', '--quiet', f'--seed={seed}', aug_cnf],
                capture_output=True, text=True, timeout=timeout
            )
        except subprocess.TimeoutExpired:
            continue

        if proc.returncode != 10:  # not SAT
            continue

        # Extract assignment for free variables
        assignment = {}
        for line in proc.stdout.split('\n'):
            if line.startswith('v '):
                for tok in line[2:].split():
                    lit = int(tok)
                    if lit == 0:
                        break
                    var = abs(lit)
                    if var in free_vars or var <= n_free_bits:
                        assignment[var] = 1 if lit > 0 else 0

        if len(assignment) < n_free_bits:
            # Try to get all vars
            for line in proc.stdout.split('\n'):
                if line.startswith('v '):
                    for tok in line[2:].split():
                        lit = int(tok)
                        if lit == 0:
                            break
                        var = abs(lit)
                        assignment[var] = 1 if lit > 0 else 0

        # Convert to bit vector
        sol = tuple(assignment.get(v, 0) for v in free_vars)
        solutions.append(sol)

        # Add blocking clause (negate this solution for free vars)
        bc = " ".join(str(-v if assignment.get(v, 0) == 1 else v) for v in free_vars) + " 0"
        blocking_clauses.append(bc)

        if len(solutions) % 20 == 0:
            print(f"  Collected {len(solutions)} solutions...", flush=True)

    return solutions, free_vars


def analyze_topology(solutions):
    """Analyze the structure of the solution space."""
    n = len(solutions)
    n_bits = len(solutions[0])
    S = np.array(solutions, dtype=np.uint8)

    print(f"\n=== Solution Space Topology ({n} solutions, {n_bits} bits) ===\n")

    # 1. Pairwise Hamming distances
    print("1. Pairwise Hamming Distances")
    dists = []
    for i in range(n):
        for j in range(i+1, n):
            d = np.sum(S[i] != S[j])
            dists.append(d)
    dists = np.array(dists)
    print(f"   Mean: {dists.mean():.1f}")
    print(f"   Stdev: {dists.std():.1f}")
    print(f"   Min: {dists.min()}, Max: {dists.max()}")
    print(f"   Expected if uniform random: {n_bits/2:.1f} ± {np.sqrt(n_bits)/2:.1f}")

    is_clustered = dists.std() > np.sqrt(n_bits) / 2 * 1.5
    print(f"   Clustered? {'YES — variance exceeds random baseline' if is_clustered else 'No — consistent with random'}")

    # Distance histogram
    hist = Counter(dists.astype(int))
    print(f"   Distribution:")
    for d in sorted(hist):
        bar = '#' * min(hist[d] // max(1, n*(n-1)//200), 60)
        print(f"     d={d:3d}: {hist[d]:5d} {bar}")

    # 2. Backbone analysis
    print(f"\n2. Backbone Variables (fixed across >90% of solutions)")
    bit_means = S.mean(axis=0)
    backbone_0 = np.where(bit_means < 0.1)[0]
    backbone_1 = np.where(bit_means > 0.9)[0]
    free_bits = np.where((bit_means >= 0.1) & (bit_means <= 0.9))[0]
    print(f"   Fixed to 0: {len(backbone_0)} bits {list(backbone_0)}")
    print(f"   Fixed to 1: {len(backbone_1)} bits {list(backbone_1)}")
    print(f"   Truly free: {len(free_bits)} of {n_bits}")
    print(f"   Effective search dimension: {len(free_bits)} bits")

    if len(backbone_0) + len(backbone_1) > n_bits * 0.3:
        print(f"   *** SIGNIFICANT: {len(backbone_0)+len(backbone_1)} backbone bits = "
              f"{100*(len(backbone_0)+len(backbone_1))/n_bits:.0f}% of space is constrained ***")

    # 3. Per-bit entropy
    print(f"\n3. Per-Bit Entropy")
    entropies = []
    for j in range(n_bits):
        p = bit_means[j]
        if p == 0 or p == 1:
            entropies.append(0)
        else:
            entropies.append(-p * np.log2(p) - (1-p) * np.log2(1-p))
    entropies = np.array(entropies)
    print(f"   Mean entropy: {entropies.mean():.4f} (max possible: 1.0)")
    print(f"   Bits with entropy < 0.5: {np.sum(entropies < 0.5)}")
    print(f"   Bits with entropy > 0.9: {np.sum(entropies > 0.9)}")

    # 4. Bit correlations (top pairs)
    print(f"\n4. Strongest Bit-Bit Correlations")
    if n >= 20:
        corr = np.corrcoef(S.T)
        np.fill_diagonal(corr, 0)
        # Find top 10 absolute correlations
        top_pairs = []
        for i in range(n_bits):
            for j in range(i+1, n_bits):
                top_pairs.append((abs(corr[i,j]), i, j, corr[i,j]))
        top_pairs.sort(reverse=True)
        for r, i, j, raw_r in top_pairs[:10]:
            print(f"   bits ({i:2d}, {j:2d}): r = {raw_r:+.4f}")

        # Effective rank
        U, sv, Vt = np.linalg.svd(S.astype(float) - 0.5)
        energy = np.cumsum(sv**2) / np.sum(sv**2)
        rank_90 = np.searchsorted(energy, 0.9) + 1
        rank_99 = np.searchsorted(energy, 0.99) + 1
        print(f"\n5. Effective Dimensionality (SVD)")
        print(f"   Rank for 90% energy: {rank_90} of {n_bits}")
        print(f"   Rank for 99% energy: {rank_99} of {n_bits}")
        print(f"   Top 5 singular values: {sv[:5]}")
        if rank_90 < n_bits * 0.5:
            print(f"   *** LOW RANK: solution space lives in a {rank_90}-dimensional subspace ***")

    return {
        'n_solutions': n,
        'n_bits': n_bits,
        'hamming_mean': float(dists.mean()),
        'hamming_std': float(dists.std()),
        'backbone_count': len(backbone_0) + len(backbone_1),
        'effective_dim': len(free_bits),
        'mean_entropy': float(entropies.mean()),
    }


def main():
    n_sol = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 30

    # Use a candidate known to be SAT at N=8
    m0, fill = 0xca, 0x03  # hw_dW56=0, fast solver

    print(f"Collecting {n_sol} solutions for N=8 sr=60 (m0=0x{m0:02x}, fill=0x{fill:02x})")
    print(f"Timeout per solve: {timeout}s\n")

    solutions, free_vars = collect_solutions(m0, fill, n_solutions=n_sol, timeout=timeout)

    if len(solutions) < 10:
        print(f"Only collected {len(solutions)} solutions — not enough for analysis")
        return

    print(f"\nCollected {len(solutions)} unique solutions")
    results = analyze_topology(solutions)

    print(f"\n=== Summary ===")
    print(f"Solutions: {results['n_solutions']}")
    print(f"Free bits: {results['n_bits']}")
    print(f"Mean Hamming distance: {results['hamming_mean']:.1f}")
    print(f"Backbone (fixed) bits: {results['backbone_count']}")
    print(f"Effective dimension: {results['effective_dim']}")
    print(f"Mean per-bit entropy: {results['mean_entropy']:.4f}")


if __name__ == "__main__":
    main()
