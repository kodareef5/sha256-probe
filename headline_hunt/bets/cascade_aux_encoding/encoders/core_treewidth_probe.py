#!/usr/bin/env python3
"""
core_treewidth_probe.py — decisive treewidth bracket on a CNF primal graph.

Motivation (Direction A, 2026-06-09):
  F211/F212 measured cascade_aux=699 and TRUE-sr61=480 as treewidth UPPER
  bounds via the min-degree heuristic (tanner_treewidth_bound.py). An upper
  bound alone cannot decide whether a top-down knowledge-compiler (d4 /
  d-DNNF / AND-OR + component caching) is feasible: a min-degree UB of 480
  is consistent with a TRUE treewidth of 30 (compilable -> GO) OR 150
  (infeasible -> NO-GO). The deciding quantity that was never measured is a
  treewidth LOWER bound.

  This tool computes a BRACKET:
    - min-fill upper bound      (tighter than min-degree)
    - min-degree upper bound    (reproduces F211/F212 for cross-check)
    - minor-min-width (MMD+) lower bound   <-- the decisive new number

  GO/NO-GO logic (d4 practical ceiling on these instances ~ tw <= 40-60):
    - LB >= ~80           -> treewidth genuinely large -> decomposition
                             compilation INFEASIBLE at N=32 -> NO-GO (rigorous).
    - min-fill UB <= ~50  -> compilation FEASIBLE -> GO (try d4).
    - otherwise            -> inconclusive; report the bracket.

  Lower bound is a valid lower bound on the full instance's treewidth (it is
  a graph minor argument), hence directly bounds any tree-decomposition based
  compiler's width. Deterministic (id tie-breaks); no randomness.

Usage:
    python3 core_treewidth_probe.py <path/to.cnf> [--no-minfill] [--json OUT]
"""
import argparse
import heapq
import json
import sys
import time
from collections import defaultdict


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
            lits = [int(t) for t in s.split() if t]
            if lits and lits[-1] == 0:
                lits = lits[:-1]
            if lits:
                clauses.append(set(abs(l) for l in lits))
    return n_vars, clauses


def build_primal_graph(clauses):
    adj = defaultdict(set)
    for clause in clauses:
        cl = list(clause)
        for i in range(len(cl)):
            a = cl[i]
            for j in range(i + 1, len(cl)):
                b = cl[j]
                adj[a].add(b)
                adj[b].add(a)
    return {v: set(nb) for v, nb in adj.items()}


def min_degree_ub(adj):
    """Standard min-degree elimination upper bound (matches F211/F212 tool)."""
    adj = {v: set(nb) for v, nb in adj.items()}
    alive = set(adj.keys())
    max_w = 0
    heap = [(len(nb), v) for v, nb in adj.items()]
    heapq.heapify(heap)
    while heap:
        deg, v = heapq.heappop(heap)
        if v not in alive:
            continue
        nb = adj[v] & alive
        if len(nb) != deg:
            heapq.heappush(heap, (len(nb), v))
            continue
        alive.discard(v)
        max_w = max(max_w, len(nb))
        nb_list = list(nb)
        for i in range(len(nb_list)):
            a = nb_list[i]
            for j in range(i + 1, len(nb_list)):
                b = nb_list[j]
                if b not in adj[a]:
                    adj[a].add(b)
                    adj[b].add(a)
        for a in nb_list:
            heapq.heappush(heap, (len(adj[a] & alive), a))
    return max_w


def min_fill_ub(adj, report_every=2000):
    """Min-fill elimination heuristic (lazy recomputation). Tighter UB.

    Eliminates the vertex introducing the fewest fill edges; the width is the
    max elimination-time degree. Lazy: fill counts are recomputed on pop if the
    neighborhood changed since the heap entry was pushed.
    """
    adj = {v: set(nb) for v, nb in adj.items()}
    alive = set(adj.keys())
    max_w = 0
    t0 = time.time()

    def fill_of(v):
        nb = list(adj[v] & alive)
        d = len(nb)
        missing = 0
        nbset = set(nb)
        for i in range(d):
            ai = nb[i]
            arow = adj[ai]
            for j in range(i + 1, d):
                if nb[j] not in arow:
                    missing += 1
        return missing, d

    heap = []
    for v in alive:
        f, d = fill_of(v)
        heap.append((f, d, v))
    heapq.heapify(heap)

    # version stamp so stale entries are skipped
    ver = {v: 0 for v in alive}
    n0 = len(alive)
    done = 0
    while heap:
        f, d, v = heapq.heappop(heap)
        if v not in alive:
            continue
        cf, cd = fill_of(v)
        if cf != f or cd != d:
            heapq.heappush(heap, (cf, cd, v))
            continue
        # eliminate v
        alive.discard(v)
        nb = list(adj[v] & alive)
        max_w = max(max_w, len(nb))
        for i in range(len(nb)):
            a = nb[i]
            for j in range(i + 1, len(nb)):
                b = nb[j]
                if b not in adj[a]:
                    adj[a].add(b)
                    adj[b].add(a)
        # neighbors' fill changed -> push fresh entries (lazy)
        for a in nb:
            ca, da = fill_of(a)
            heapq.heappush(heap, (ca, da, a))
        done += 1
        if done % report_every == 0:
            print(f"  [min-fill] {done}/{n0} eliminated, max_w={max_w}, "
                  f"{time.time()-t0:.1f}s", file=sys.stderr)
    return max_w


def minor_min_width_lb(adj):
    """Minor-min-width (MMD+) treewidth LOWER bound.

    Repeatedly: take min-degree vertex v, lb = max(lb, deg(v)); contract v into
    its lowest-degree neighbor (least-c heuristic). Contraction keeps the result
    a minor, so deg(v) is a valid tw lower bound at every step.
    """
    adj = {v: set(nb) for v, nb in adj.items()}
    alive = set(adj.keys())
    lb = 0
    while alive:
        # min-degree alive vertex (id tie-break for determinism)
        v = min(alive, key=lambda x: (len(adj[x] & alive), x))
        nb = adj[v] & alive
        d = len(nb)
        if d == 0:
            alive.discard(v)
            continue
        lb = max(lb, d)
        # contract v into lowest-degree neighbor u
        u = min(nb, key=lambda x: (len(adj[x] & alive), x))
        nb.discard(u)
        for w in nb:
            if w != u:
                adj[u].add(w)
                adj[w].add(u)
        alive.discard(v)
    return lb


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cnf")
    ap.add_argument("--no-minfill", action="store_true",
                    help="skip the (slower) min-fill upper bound")
    ap.add_argument("--json", default=None, help="write result JSON here")
    args = ap.parse_args()

    t0 = time.time()
    n_vars, clauses = parse_cnf(args.cnf)
    adj = build_primal_graph(clauses)
    n_nodes = len(adj)
    n_edges = sum(len(nb) for nb in adj.values()) // 2
    degs = [len(nb) for nb in adj.values()]
    print(f"{args.cnf}")
    print(f"  primal graph: {n_nodes} nodes, {n_edges} edges, "
          f"deg min/mean/max = {min(degs)}/{sum(degs)/len(degs):.1f}/{max(degs)}")

    print("  computing minor-min-width LOWER bound (decisive)...")
    tlb = time.time()
    lb = minor_min_width_lb(adj)
    print(f"  >>> treewidth LOWER bound (MMD+): {lb}   ({time.time()-tlb:.1f}s)")

    tmd = time.time()
    md_ub = min_degree_ub(adj)
    print(f"  min-degree UPPER bound: {md_ub}   ({time.time()-tmd:.1f}s)")

    mf_ub = None
    if not args.no_minfill:
        print("  computing min-fill UPPER bound (slower)...")
        tmf = time.time()
        mf_ub = min_fill_ub(adj)
        print(f"  min-fill   UPPER bound: {mf_ub}   ({time.time()-tmf:.1f}s)")

    ub = mf_ub if mf_ub is not None else md_ub
    print(f"\n  BRACKET: {lb} <= treewidth <= {ub}")
    # verdict
    if lb >= 80:
        verdict = ("NO-GO: lower bound >= 80 -> decomposition compilation "
                   "(d4/d-DNNF/AND-OR) infeasible at this scale")
    elif ub <= 50:
        verdict = ("GO: upper bound <= 50 -> compilation feasible; try d4")
    else:
        verdict = (f"INCONCLUSIVE: bracket [{lb}, {ub}] straddles the d4 "
                   f"feasibility threshold (~40-60)")
    print(f"  VERDICT: {verdict}")
    print(f"  total wall: {time.time()-t0:.1f}s")

    out = {
        "cnf": args.cnf,
        "nodes": n_nodes,
        "edges": n_edges,
        "deg_max": max(degs),
        "tw_lower_bound_mmdplus": lb,
        "tw_upper_bound_mindegree": md_ub,
        "tw_upper_bound_minfill": mf_ub,
        "verdict": verdict,
    }
    if args.json:
        with open(args.json, "w") as f:
            json.dump(out, f, indent=2)
        print(f"  wrote {args.json}")


if __name__ == "__main__":
    main()
