#!/usr/bin/env python3
"""
shell_eliminate.py — Stage 1 outer-shell variable elimination.

A minimal implementation of bounded variable elimination targeting the
F211 "outer shell" of cascade_aux Tanner graphs: variables with low
clause-incidence that can be eliminated without explosive clause growth.

This is NOT a complete BVE. It targets only vars satisfying:
- |pos_clauses(v)| × |neg_clauses(v)| ≤ pos+neg (resolution doesn't grow)
- Result has no tautologies

This handles the "Tseitin chain" majority of the F211 shell. More
aggressive elimination (handling tautology pruning, multi-step chains)
is left to follow-up work.

Outputs:
- Reduced CNF (DIMACS format) with renumbered variables.
- A restoration map (.varmap.json) for transferring SAT assignments
  back to original variable space.
- A report (.report.json) with stats.

Usage:
    python3 shell_eliminate.py input.cnf output.cnf [--max-iter N]
"""

import argparse
import json
import sys
import time
from collections import defaultdict


def parse_cnf(path):
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
            lits = [int(t) for t in tokens if t]
            if lits and lits[-1] == 0:
                lits = lits[:-1]
            if not lits:
                continue
            clauses.append(tuple(lits))
    return n_vars, n_clauses_decl, clauses


def resolve(c1, c2, var):
    """Resolve clauses c1 (containing +var) and c2 (containing -var) on var.
    Returns the resolvent clause (or None if tautology)."""
    s1 = set(c1) - {var}
    s2 = set(c2) - {-var}
    out = s1 | s2
    # Check for tautology: same var appears as both +x and -x in result
    for lit in out:
        if -lit in out:
            return None  # tautology
    return tuple(sorted(out, key=lambda l: (abs(l), l < 0)))


def eliminate_one_pass(clauses, n_vars, max_growth=0):
    """One pass of bounded variable elimination.

    For each variable v, check if resolving all (pos, neg) clauses
    produces ≤ |pos| + |neg| + max_growth new clauses (so net change
    is ≤ max_growth). If yes, eliminate v.

    Returns (new_clauses, eliminated_set, n_resolutions).
    """
    # Build var → (pos_clauses, neg_clauses) index
    clauses = list(clauses)
    var_pos = defaultdict(list)
    var_neg = defaultdict(list)
    for i, clause in enumerate(clauses):
        for lit in clause:
            if lit > 0:
                var_pos[lit].append(i)
            else:
                var_neg[-lit].append(i)

    eliminated = set()
    deleted_clauses = set()
    new_clauses = []
    n_resolutions = 0

    # Sort vars by min(|pos|, |neg|) ascending — eliminate cheapest first
    vars_to_check = sorted(set(var_pos.keys()) | set(var_neg.keys()),
                           key=lambda v: (min(len(var_pos[v]), len(var_neg[v])),
                                          len(var_pos[v]) + len(var_neg[v])))
    for v in vars_to_check:
        if v in eliminated:
            continue
        pos_idx = [i for i in var_pos[v] if i not in deleted_clauses]
        neg_idx = [i for i in var_neg[v] if i not in deleted_clauses]
        if not pos_idx and not neg_idx:
            continue
        if not pos_idx or not neg_idx:
            # var is pure (only one polarity); can be set to satisfy all
            for i in pos_idx + neg_idx:
                deleted_clauses.add(i)
            eliminated.add(v)
            continue

        # Check if resolution growth is acceptable
        pos_clauses = [clauses[i] for i in pos_idx]
        neg_clauses = [clauses[i] for i in neg_idx]
        resolvents = []
        for c1 in pos_clauses:
            for c2 in neg_clauses:
                r = resolve(c1, c2, v)
                if r is not None:
                    resolvents.append(r)

        # Bound: resolvents count - (pos + neg) ≤ max_growth
        if len(resolvents) - (len(pos_idx) + len(neg_idx)) > max_growth:
            continue

        # Eliminate
        for i in pos_idx + neg_idx:
            deleted_clauses.add(i)
        new_clauses.extend(resolvents)
        eliminated.add(v)
        n_resolutions += len(resolvents)

    # Build final clause list
    out_clauses = [c for i, c in enumerate(clauses) if i not in deleted_clauses]
    out_clauses.extend(new_clauses)
    return out_clauses, eliminated, n_resolutions


def renumber(clauses, eliminated, n_vars):
    """Map remaining vars to dense range 1..K. Return (new_clauses, varmap)."""
    remaining = sorted(set(range(1, n_vars + 1)) - eliminated)
    old_to_new = {old: new for new, old in enumerate(remaining, start=1)}
    new_to_old = {new: old for old, new in old_to_new.items()}
    new_clauses = []
    for clause in clauses:
        new_clause = tuple(
            (old_to_new[abs(l)] if l > 0 else -old_to_new[abs(l)])
            for l in clause if abs(l) in old_to_new
        )
        new_clauses.append(new_clause)
    return new_clauses, len(remaining), new_to_old


def write_dimacs(out_path, n_vars, clauses, header=None):
    with open(out_path, "w") as f:
        if header:
            for line in header.splitlines():
                f.write(f"c {line}\n")
        f.write(f"p cnf {n_vars} {len(clauses)}\n")
        for clause in clauses:
            f.write(" ".join(str(l) for l in clause) + " 0\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--max-iter", type=int, default=10,
                    help="Max elimination passes")
    ap.add_argument("--max-growth", type=int, default=0,
                    help="Per-var max clause growth allowed")
    args = ap.parse_args()

    t0 = time.time()
    n_vars, n_clauses_decl, clauses = parse_cnf(args.input)
    print(f"Input: {n_vars} vars, {len(clauses)} clauses ({time.time()-t0:.2f}s)")

    total_eliminated = set()
    iter_stats = []
    for it in range(args.max_iter):
        t1 = time.time()
        clauses, elim, n_res = eliminate_one_pass(clauses, n_vars, args.max_growth)
        total_eliminated |= elim
        iter_stats.append({
            "iter": it,
            "eliminated_this_pass": len(elim),
            "n_resolutions": n_res,
            "remaining_vars": n_vars - len(total_eliminated),
            "remaining_clauses": len(clauses),
            "wall": time.time() - t1,
        })
        print(f"  Pass {it}: -{len(elim)} vars, {len(clauses)} clauses, "
              f"{time.time()-t1:.2f}s")
        if len(elim) == 0:
            break

    # Renumber to dense range
    clauses, new_n_vars, new_to_old = renumber(clauses, total_eliminated, n_vars)

    header = (
        f"shell_eliminate v1 — 2026-04-28\n"
        f"input: {args.input}\n"
        f"original vars: {n_vars}, clauses: {n_clauses_decl}\n"
        f"eliminated: {len(total_eliminated)} vars\n"
        f"remaining: {new_n_vars} vars, {len(clauses)} clauses\n"
        f"max_growth: {args.max_growth}\n"
    )
    write_dimacs(args.output, new_n_vars, clauses, header)

    # Write varmap
    varmap_path = args.output + ".varmap.json"
    with open(varmap_path, "w") as f:
        json.dump({"new_to_old": new_to_old}, f)

    # Write report
    report_path = args.output + ".report.json"
    report = {
        "input": args.input,
        "output": args.output,
        "input_vars": n_vars,
        "input_clauses": n_clauses_decl,
        "eliminated_vars": len(total_eliminated),
        "output_vars": new_n_vars,
        "output_clauses": len(clauses),
        "elimination_pct": 100 * len(total_eliminated) / n_vars,
        "iterations": iter_stats,
        "total_wall": time.time() - t0,
    }
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\nFinal: {new_n_vars} vars ({100*len(total_eliminated)/n_vars:.1f}% "
          f"eliminated), {len(clauses)} clauses")
    print(f"Wrote: {args.output}")
    print(f"Wrote: {varmap_path}")
    print(f"Wrote: {report_path}")
    print(f"Total wall: {time.time()-t0:.2f}s")


if __name__ == "__main__":
    main()
