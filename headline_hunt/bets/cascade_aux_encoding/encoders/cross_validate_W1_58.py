#!/usr/bin/env python3
"""
cross_validate_W1_58.py — verify F214's W1_58 shell-elimination universality.

Runs identify_hard_core analysis on multiple cascade_aux CNFs, writing
incremental output as each completes. F214 found that ALL 32 bits of
W1_58 eliminate in shell on the canonical CNF. F215 (this script) tests
whether this holds across a sample of cascade_aux instances.
"""
import sys
import heapq
import os
from collections import defaultdict


def parse_cnf(path):
    clauses = []
    with open(path) as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("c") or s.startswith("p"):
                continue
            lits = [int(t) for t in s.split() if t]
            if lits and lits[-1] == 0:
                lits = lits[:-1]
            if lits:
                clauses.append(set(abs(l) for l in lits))
    return clauses


def primal_graph(clauses):
    adj = defaultdict(set)
    for c in clauses:
        cl = list(c)
        for i in range(len(cl)):
            for j in range(i + 1, len(cl)):
                adj[cl[i]].add(cl[j])
                adj[cl[j]].add(cl[i])
    return adj


def shell_var_set(clauses, threshold=14):
    """Return (shell_vars, total_eliminated, hard_core_size)."""
    adj = {v: set(nb) for v, nb in primal_graph(clauses).items()}
    heap = [(len(nb), v) for v, nb in adj.items()]
    heapq.heapify(heap)
    elim_order = []
    eliminated = set()
    while heap:
        deg, v = heapq.heappop(heap)
        if v in eliminated:
            continue
        actual = adj[v] - eliminated
        if len(actual) > deg:
            heapq.heappush(heap, (len(actual), v))
            continue
        eliminated.add(v)
        elim_order.append((v, len(actual)))
        nb_list = list(actual)
        for i in range(len(nb_list)):
            for j in range(i + 1, len(nb_list)):
                a, b = nb_list[i], nb_list[j]
                if b not in adj[a]:
                    adj[a].add(b)
                    adj[b].add(a)
                    heapq.heappush(heap, (len(adj[a] - eliminated), a))
                    heapq.heappush(heap, (len(adj[b] - eliminated), b))

    shell_size = 0
    for i, (v, fill) in enumerate(elim_order):
        if fill > threshold:
            shell_size = i
            break
    else:
        shell_size = len(elim_order)
    shell_vars = set(v for v, _ in elim_order[:shell_size])
    return shell_vars, len(elim_order), len(elim_order) - shell_size


def main():
    cnf_dir = "headline_hunt/bets/cascade_aux_encoding/cnfs"
    cnfs = sorted(f for f in os.listdir(cnf_dir) if f.endswith(".cnf"))
    sample_size = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    cnfs = cnfs[:sample_size]

    # W1_58 = vars 34..65 for sr=60 n_free=4
    w1_58_vars = set(range(34, 66))
    # W1_57 = vars 2..33
    w1_57_vars = set(range(2, 34))
    # W2_57 = vars 130..161
    w2_57_vars = set(range(130, 162))
    # W2_58 = vars 162..193
    w2_58_vars = set(range(162, 194))

    print("CNF                                                 | tot vars | shell% | W1_58 | W1_57 | W2_57 | W2_58")
    print("-" * 115)
    for cnf in cnfs:
        path = os.path.join(cnf_dir, cnf)
        clauses = parse_cnf(path)
        shell, total, core = shell_var_set(clauses)
        shell_pct = 100 * (total - core) / total
        w1_58_in_shell = len(w1_58_vars & shell)
        w1_57_in_shell = len(w1_57_vars & shell)
        w2_57_in_shell = len(w2_57_vars & shell)
        w2_58_in_shell = len(w2_58_vars & shell)
        name = cnf[:48].ljust(48)
        print(f"{name} | {total:>8} | {shell_pct:>5.1f}% | {w1_58_in_shell:>2}/32 | "
              f"{w1_57_in_shell:>2}/32 | {w2_57_in_shell:>2}/32 | {w2_58_in_shell:>2}/32",
              flush=True)


if __name__ == "__main__":
    main()
