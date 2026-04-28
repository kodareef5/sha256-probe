#!/usr/bin/env python3
"""
tanner_4cycle_count.py — count length-4 cycles in a CNF Tanner graph.

A cnf instance defines a bipartite graph: variables on one side, clauses
on the other; edge if variable appears in clause. A length-4 cycle in
this bipartite graph is a pair of variables sharing two clauses
(equivalently, a pair of clauses sharing two variables).

This is the pre-implementation structural check for BP-Bethe on
cascade_aux (per F134 plan): if the 4-cycle structure clusters in a
specific way, BP-Bethe with level-4 cluster correction is the right
algorithm; if not, the principles-framework prediction needs revision.

Usage:
    python3 tanner_4cycle_count.py <path/to.cnf> [--limit N]

Output:
    - n_vars, n_clauses
    - mean clause length, max clause length
    - 4-cycle count (= number of (var pair, clause pair) where the
      two vars co-appear in both clauses)
    - per-clause-pair shared-variable distribution
"""

import argparse
import sys
import time
from collections import defaultdict


def parse_cnf(path):
    """Yield (n_vars, n_clauses, list[set[var_abs]])."""
    n_vars = 0
    n_clauses_decl = 0
    clauses = []
    with open(path) as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("c"):
                continue
            if s.startswith("p"):
                parts = s.split()
                n_vars = int(parts[2])
                n_clauses_decl = int(parts[3])
                continue
            tokens = s.split()
            if not tokens:
                continue
            lits = [int(t) for t in tokens]
            if lits and lits[-1] == 0:
                lits = lits[:-1]
            if not lits:
                continue
            clauses.append(frozenset(abs(l) for l in lits))
    return n_vars, n_clauses_decl, clauses


def count_4cycles(clauses, max_clauses=None):
    """
    A 4-cycle in the variable-clause bipartite graph is a pair of clauses
    sharing two distinct variables. Count = sum over all clause-pairs
    of C(shared_count, 2).

    Equivalent and faster: for each variable v, list clauses containing v.
    A 4-cycle = (v, w, c1, c2) with v ≠ w, both v,w in c1 AND both in c2.

    To count efficiently:
    - For each pair of clauses (c1, c2), count shared variables k,
      contribute C(k, 2) to the 4-cycle count.

    Iterating all clause-pairs is O(C^2 * mean_clause_size), too slow for
    52k clauses. Smarter: build var → clause-set map, for each pair of
    clauses sharing variable v, walk the intersection. Even simpler for
    counting only: for each pair (v, w), the number of clauses containing
    both is k_{v,w}; 4-cycles incident on (v,w) = C(k_{v,w}, 2).

    We use the var-pair indexing approach. For each clause, enumerate all
    (v, w) pairs in the clause and count their multiplicities.
    """
    pair_count = defaultdict(int)  # (v, w) sorted -> # clauses containing both
    if max_clauses is not None:
        clauses = clauses[:max_clauses]
    for clause in clauses:
        sorted_vars = sorted(clause)
        L = len(sorted_vars)
        for i in range(L):
            for j in range(i + 1, L):
                pair_count[(sorted_vars[i], sorted_vars[j])] += 1
    # Sum C(k,2) for k >= 2 over all pairs
    cycles = 0
    multiplicity_hist = defaultdict(int)
    for k in pair_count.values():
        if k >= 2:
            cycles += k * (k - 1) // 2
        multiplicity_hist[k] += 1
    return cycles, dict(multiplicity_hist), pair_count


def gap_distribution(pair_count, top_n=20):
    """Per-pair (var_i, var_j) gap = abs(j-i). Distribution of gaps among
    pairs that participate in 4-cycles (multiplicity >= 2)."""
    gap_hist = defaultdict(int)
    gap_4cycle_hist = defaultdict(int)
    high_mult_pairs = []
    for (v, w), k in pair_count.items():
        if k >= 2:
            gap = abs(w - v)
            gap_hist[gap] += 1
            gap_4cycle_hist[gap] += k * (k - 1) // 2
            if k >= 5:
                high_mult_pairs.append(((v, w), k, gap))
    high_mult_pairs.sort(key=lambda x: -x[1])
    return dict(gap_hist), dict(gap_4cycle_hist), high_mult_pairs[:top_n]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cnf", help="CNF DIMACS path")
    ap.add_argument("--limit", type=int, default=None,
                    help="Process only first N clauses")
    args = ap.parse_args()

    t0 = time.time()
    n_vars, n_clauses_decl, clauses = parse_cnf(args.cnf)
    t_parse = time.time() - t0
    print(f"Parsed: {n_vars} vars, {n_clauses_decl} clauses (decl), "
          f"{len(clauses)} clauses (read), {t_parse:.2f}s")

    sizes = [len(c) for c in clauses]
    print(f"Clause sizes: min={min(sizes)}, max={max(sizes)}, "
          f"mean={sum(sizes)/len(sizes):.2f}")

    t0 = time.time()
    cycles, mult_hist, pair_count = count_4cycles(clauses, args.limit)
    t_cycle = time.time() - t0
    print(f"\n4-cycles: {cycles:,} (counted in {t_cycle:.2f}s)")
    print(f"Distinct var-pairs: {len(pair_count):,}")
    print(f"Var-pairs with multiplicity >= 2 (forming 4-cycles): "
          f"{sum(1 for k in pair_count.values() if k >= 2):,}")

    print("\nVar-pair multiplicity histogram (4-cycle-forming pairs):")
    for k in sorted(mult_hist.keys()):
        if k >= 2 and mult_hist[k] > 0:
            print(f"  multiplicity={k:>3}: {mult_hist[k]:,} pairs "
                  f"=> {k*(k-1)//2 * mult_hist[k]:,} 4-cycles")

    gap_hist, gap_4cycle_hist, top_high_mult = gap_distribution(pair_count)
    print("\nGap distribution (only 4-cycle-forming pairs, top 20 by gap):")
    sorted_gaps = sorted(gap_hist.items(), key=lambda x: x[0])
    for gap, count in sorted_gaps[:20]:
        cycles_at_gap = gap_4cycle_hist.get(gap, 0)
        print(f"  gap={gap:>5}: {count:>6,} pairs, {cycles_at_gap:>8,} 4-cycles")

    print("\nTop 20 high-multiplicity pairs (mult >= 5):")
    for (v, w), k, gap in top_high_mult[:20]:
        print(f"  ({v:>5}, {w:>5}) gap={gap:>5}: mult={k}")


if __name__ == "__main__":
    main()
