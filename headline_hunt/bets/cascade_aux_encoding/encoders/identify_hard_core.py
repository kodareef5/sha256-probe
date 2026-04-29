#!/usr/bin/env python3
"""
identify_hard_core.py — track variable elimination order, identify hard-core vars.

Same min-degree elimination as tanner_treewidth_bound.py, but records
which variable is eliminated at each step. The "hard core" is the set
of variables eliminated AFTER max-fill exceeds a threshold (default 14,
matching F211's shell-vs-core boundary).

Cross-references the hard core against F209's variable semantics:
- vars 2..129: M1 free schedule (W1_57..W1_60 for sr=60, n_free=4)
- vars 130..257: M2 free schedule (W2_57..W2_60)
- vars 258+: Tseitin auxiliaries

Reports:
- Hard-core size
- Hard-core vars in schedule range vs aux range
- Top 20 vars eliminated last (the deepest core)
"""

import argparse
import heapq
import json
import sys
import time
from collections import defaultdict
from pathlib import Path


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
    adj = defaultdict(set)
    for clause in clauses:
        cl = list(clause)
        for i in range(len(cl)):
            for j in range(i + 1, len(cl)):
                adj[cl[i]].add(cl[j])
                adj[cl[j]].add(cl[i])
    return adj


def min_degree_eliminate_with_trajectory(adj, threshold=14):
    """Run min-degree elimination, record (step, var, fill_size) trajectory."""
    adj = {v: set(nb) for v, nb in adj.items()}
    heap = []
    for v, nb in adj.items():
        heapq.heappush(heap, (len(nb), v))

    eliminated_order = []
    eliminated = set()
    iteration = 0
    while heap:
        deg, v = heapq.heappop(heap)
        if v in eliminated:
            continue
        actual_nb = adj[v] - eliminated
        actual_deg = len(actual_nb)
        if actual_deg > deg:
            heapq.heappush(heap, (actual_deg, v))
            continue
        eliminated.add(v)
        eliminated_order.append((iteration, v, actual_deg))
        nb_list = list(actual_nb)
        for i in range(len(nb_list)):
            for j in range(i + 1, len(nb_list)):
                a, b = nb_list[i], nb_list[j]
                if b not in adj[a]:
                    adj[a].add(b)
                    adj[b].add(a)
                    heapq.heappush(heap, (len(adj[a] - eliminated), a))
                    heapq.heappush(heap, (len(adj[b] - eliminated), b))
        iteration += 1

    return eliminated_order


def categorize_var(v, n_free=4):
    """Map var index to encoder semantics (per F209)."""
    if v == 1:
        return ("CONST_TRUE", 0)
    elif 2 <= v <= 1 + n_free * 32:
        word_idx = (v - 2) // 32
        bit = (v - 2) % 32
        return (f"W1_{57 + word_idx}", bit)
    elif 1 + n_free * 32 < v <= 1 + 2 * n_free * 32:
        offset = v - 2 - n_free * 32
        word_idx = offset // 32
        bit = offset % 32
        return (f"W2_{57 + word_idx}", bit)
    else:
        return ("AUX", v)


def semantic_entry(v, n_free=4):
    cat, info = categorize_var(v, n_free)
    entry = {"var": v, "category": cat}
    if cat in ("CONST_TRUE", "AUX"):
        entry["index"] = info
        return entry
    word, round_s = cat.split("_", 1)
    entry.update({
        "word": word.lower(),
        "round": int(round_s),
        "bit": info,
    })
    return entry


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cnf")
    ap.add_argument("--threshold", type=int, default=14,
                    help="Fill threshold above which a var is hard-core")
    ap.add_argument("--n-free", type=int, default=4,
                    help="n_free for cascade_aux semantic mapping")
    ap.add_argument("--out-json", type=Path,
                    help="optional machine-readable hard-core summary")
    args = ap.parse_args()

    t0 = time.time()
    n_vars, clauses = parse_cnf(args.cnf)
    adj = build_primal_graph(clauses)
    n_nodes = len(adj)
    print(f"Parsed: {n_vars} vars, {len(clauses)} clauses, "
          f"{n_nodes} primal-graph nodes ({time.time()-t0:.2f}s)")

    print("\nRunning min-degree elimination (hard-core identification)...",
          file=sys.stderr)
    t0 = time.time()
    trajectory = min_degree_eliminate_with_trajectory(adj, args.threshold)
    print(f"Done ({time.time()-t0:.2f}s)", file=sys.stderr)

    # Find shell/core boundary: first index where fill > threshold persists
    shell_size = 0
    for i, (step, v, fill) in enumerate(trajectory):
        if fill > args.threshold:
            shell_size = i
            break
    else:
        shell_size = len(trajectory)

    core_size = len(trajectory) - shell_size
    print(f"\nThreshold fill > {args.threshold}:")
    print(f"  Shell: {shell_size} vars ({100*shell_size/len(trajectory):.1f}%)")
    print(f"  Core:  {core_size} vars ({100*core_size/len(trajectory):.1f}%)")

    # Categorize core vars semantically
    core_vars = [v for (_, v, _) in trajectory[shell_size:]]
    cat_counts = defaultdict(int)
    for v in core_vars:
        cat, _ = categorize_var(v, args.n_free)
        if cat == "AUX":
            cat_counts["AUX"] += 1
        elif cat == "CONST_TRUE":
            cat_counts["CONST_TRUE"] += 1
        else:
            cat_counts["SCHEDULE"] += 1
    print(f"\nHard-core var categorization:")
    print(f"  M1/M2 schedule (vars 2..{1+2*args.n_free*32}): "
          f"{cat_counts['SCHEDULE']} vars")
    print(f"  Tseitin AUX (vars {2+2*args.n_free*32}+): "
          f"{cat_counts['AUX']} vars")
    if cat_counts["CONST_TRUE"]:
        print(f"  CONST_TRUE: {cat_counts['CONST_TRUE']} var")

    # Top 20 deepest-core vars (eliminated last)
    print(f"\nTop 20 deepest-core vars (eliminated last):")
    for (step, v, fill) in trajectory[-20:]:
        cat, info = categorize_var(v, args.n_free)
        print(f"  step {step:>5}: var {v:>5} fill={fill:>4} → {cat}[{info}]")

    # Schedule vars NOT in core (potentially trivial schedule bits)
    schedule_in_core = set()
    for v in core_vars:
        cat, _ = categorize_var(v, args.n_free)
        if cat not in ("AUX", "CONST_TRUE"):
            schedule_in_core.add(v)

    schedule_total = set(range(2, 2 + 2 * args.n_free * 32))
    schedule_outside_core = schedule_total - schedule_in_core
    print(f"\nSchedule vars OUTSIDE core (eliminated in shell): "
          f"{len(schedule_outside_core)}/{len(schedule_total)}")
    if len(schedule_outside_core) <= 20:
        for v in sorted(schedule_outside_core):
            cat, info = categorize_var(v, args.n_free)
            print(f"  var {v:>5}: {cat}[{info}]")

    if args.out_json:
        schedule_core = [
            semantic_entry(v, args.n_free)
            for v in sorted(schedule_in_core)
        ]
        schedule_shell = [
            semantic_entry(v, args.n_free)
            for v in sorted(schedule_outside_core)
        ]
        deepest_core = [
            {
                "step": step,
                "var": v,
                "fill": fill,
                "semantic": semantic_entry(v, args.n_free),
            }
            for step, v, fill in trajectory[-50:]
        ]
        summary = {
            "cnf": args.cnf,
            "threshold": args.threshold,
            "n_free": args.n_free,
            "n_vars": n_vars,
            "n_clauses": len(clauses),
            "n_primal_nodes": n_nodes,
            "shell_size": shell_size,
            "core_size": core_size,
            "schedule_total": len(schedule_total),
            "schedule_core_count": len(schedule_core),
            "schedule_shell_count": len(schedule_shell),
            "aux_core_count": cat_counts["AUX"],
            "const_true_core_count": cat_counts["CONST_TRUE"],
            "core_vars": core_vars,
            "schedule_core": schedule_core,
            "schedule_shell": schedule_shell,
            "deepest_core": deepest_core,
        }
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        with args.out_json.open("w") as f:
            json.dump(summary, f, indent=2, sort_keys=True)
            f.write("\n")
        print(f"\nWrote JSON summary: {args.out_json}")


if __name__ == "__main__":
    main()
