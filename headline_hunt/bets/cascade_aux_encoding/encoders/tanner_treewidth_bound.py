#!/usr/bin/env python3
"""
tanner_treewidth_bound.py — fast treewidth upper bound on a CNF's primal graph.

The PRIMAL graph (variable graph) has variables as nodes; edge if two
variables co-appear in some clause. Treewidth of the primal graph
upper-bounds the complexity of variable-elimination decoding.

We compute an upper bound via min-degree elimination heuristic
(O(n^2) standard implementation). Returns the maximum size-of-fill
during elimination, which is a tight upper bound for the primal-graph
treewidth.

Usage:
    python3 tanner_treewidth_bound.py <path/to.cnf>
"""

import argparse
import sys
import time
from collections import defaultdict
import heapq


def parse_cnf(path):
    n_vars = 0
    clauses = []
    with open(path) as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("c"):
                continue
            if s.startswith("p"):
                n_vars = int(s.split()[2])
                continue
            tokens = s.split()
            lits = [int(t) for t in tokens if t]
            if lits and lits[-1] == 0:
                lits = lits[:-1]
            if not lits:
                continue
            clauses.append(set(abs(l) for l in lits))
    return n_vars, clauses


def build_primal_graph(clauses):
    """Adjacency dict: var -> set of neighbor vars."""
    adj = defaultdict(set)
    for clause in clauses:
        cl = list(clause)
        for i in range(len(cl)):
            for j in range(i + 1, len(cl)):
                adj[cl[i]].add(cl[j])
                adj[cl[j]].add(cl[i])
    return adj


def min_degree_elimination_bound(adj, sample_only=None):
    """
    Min-degree heuristic: repeatedly eliminate min-degree vertex,
    fill in its neighbors, track max-fill-size as treewidth upper bound.

    sample_only: if not None, run on a random sample of `sample_only`
    vertices (for huge graphs).
    """
    adj = {v: set(nb) for v, nb in adj.items()}
    if sample_only is not None and len(adj) > sample_only:
        import random
        keep = set(random.sample(list(adj.keys()), sample_only))
        adj = {v: nb & keep for v, nb in adj.items() if v in keep}

    max_fill = 0
    n_remaining = len(adj)
    n_initial = n_remaining
    progress_step = max(1, n_initial // 20)

    # Use a degree-priority queue
    heap = []
    for v, nb in adj.items():
        heapq.heappush(heap, (len(nb), v))

    eliminated = set()
    iteration = 0
    while heap:
        deg, v = heapq.heappop(heap)
        if v in eliminated:
            continue
        # Real degree might be lower than recorded; recheck
        actual_nb = adj[v] - eliminated
        actual_deg = len(actual_nb)
        if actual_deg > deg:
            heapq.heappush(heap, (actual_deg, v))
            continue
        # Eliminate v
        eliminated.add(v)
        max_fill = max(max_fill, actual_deg)
        # Connect all neighbors
        nb_list = list(actual_nb)
        for i in range(len(nb_list)):
            for j in range(i + 1, len(nb_list)):
                a, b = nb_list[i], nb_list[j]
                if b not in adj[a]:
                    adj[a].add(b)
                    adj[b].add(a)
                    heapq.heappush(heap, (len(adj[a]) - len(adj[a] & eliminated), a))
                    heapq.heappush(heap, (len(adj[b]) - len(adj[b] & eliminated), b))
        # progress
        iteration += 1
        if iteration % progress_step == 0:
            print(f"  eliminated {iteration}/{n_initial}, max_fill so far: {max_fill}",
                  file=sys.stderr)

    return max_fill


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cnf")
    ap.add_argument("--sample", type=int, default=None,
                    help="Run min-degree on random sample of N vertices "
                         "(for huge graphs)")
    args = ap.parse_args()

    t0 = time.time()
    n_vars, clauses = parse_cnf(args.cnf)
    print(f"Parsed: {n_vars} vars, {len(clauses)} clauses ({time.time()-t0:.2f}s)")

    adj = build_primal_graph(clauses)
    n_nodes = len(adj)
    n_edges = sum(len(nb) for nb in adj.values()) // 2
    degrees = [len(nb) for nb in adj.values()]
    print(f"Primal graph: {n_nodes} nodes, {n_edges} edges, "
          f"min/mean/max degree = {min(degrees)}/{sum(degrees)/len(degrees):.1f}/{max(degrees)}")

    print("\nRunning min-degree elimination (treewidth upper bound)...")
    t0 = time.time()
    bound = min_degree_elimination_bound(adj, sample_only=args.sample)
    print(f"Treewidth upper bound: {bound} ({time.time()-t0:.2f}s)")


if __name__ == "__main__":
    main()
