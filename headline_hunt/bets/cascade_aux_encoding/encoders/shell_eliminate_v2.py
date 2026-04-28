#!/usr/bin/env python3
"""
shell_eliminate_v2.py — F232 corrected version.

Stage 1 outer-shell variable elimination, with eager index updates
after each elimination. Replaces the buggy v1 (shell_eliminate.py)
which produced false-SAT verdicts on UNSAT inputs (F232).

Soundness contract:
  - reduced CNF is SAT iff original is SAT
  - reduced CNF is UNSAT iff original is UNSAT
  - empty clause derivation → original is UNSAT (UNSAT proof)

Algorithm:
  Repeatedly find ONE eliminable variable (lowest min(|pos|,|neg|))
  and eliminate it correctly. After each elimination, the var_pos/
  var_neg indices are updated to reflect the new clause set (deletions
  and resolvent additions). Iterate until no more eliminable vars.

Slower than v1 (O(n²) per overall computation) but sound.

Usage:
    python3 shell_eliminate_v2.py input.cnf output.cnf [--max-growth N]
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
    """Resolve c1 (with +var) and c2 (with -var). Return resolvent
    or None if tautology."""
    s1 = set(c1) - {var}
    s2 = set(c2) - {-var}
    out = s1 | s2
    for lit in out:
        if -lit in out:
            return None  # tautology
    return tuple(sorted(out, key=lambda l: (abs(l), l < 0)))


def build_indices(clauses_dict):
    """Given dict {clause_id: clause}, return var_pos, var_neg dicts."""
    var_pos = defaultdict(set)
    var_neg = defaultdict(set)
    for cid, clause in clauses_dict.items():
        for lit in clause:
            if lit > 0:
                var_pos[lit].add(cid)
            else:
                var_neg[-lit].add(cid)
    return var_pos, var_neg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--max-growth", type=int, default=0,
                    help="Per-var max clause growth allowed")
    args = ap.parse_args()

    t0 = time.time()
    n_vars, n_clauses_decl, raw_clauses = parse_cnf(args.input)
    print(f"Input: {n_vars} vars, {len(raw_clauses)} clauses ({time.time()-t0:.2f}s)")

    # Maintain clauses as dict (id → clause) for O(1) deletion
    clauses_dict = {i: c for i, c in enumerate(raw_clauses)}
    next_id = len(raw_clauses)
    var_pos, var_neg = build_indices(clauses_dict)
    eliminated = set()
    n_eliminations = 0
    n_resolutions = 0

    # Check for empty clause early
    for cid, c in clauses_dict.items():
        if len(c) == 0:
            print("Original CNF contains empty clause — UNSAT")
            sys.exit(0)

    # Iteratively eliminate
    while True:
        # Find best elim candidate: var v with smallest min(|pos|,|neg|)
        # that hasn't been eliminated yet and exists in var_pos or var_neg
        candidates = []
        for v in set(var_pos.keys()) | set(var_neg.keys()):
            if v in eliminated:
                continue
            n_pos = len(var_pos[v])
            n_neg = len(var_neg[v])
            if n_pos == 0 and n_neg == 0:
                continue
            # priority: pure literal (one side = 0) first, then min(p,n)
            if n_pos == 0 or n_neg == 0:
                priority = -1  # pure
            else:
                priority = min(n_pos, n_neg)
            candidates.append((priority, n_pos + n_neg, v))

        if not candidates:
            break
        candidates.sort()
        best_priority = candidates[0][0]
        if best_priority > 0 and best_priority > 8:
            # No cheap eliminations left — stop (further would expand too much)
            # Allow up to min(p,n)=8 with bounded growth check
            break

        # Try elimination on the best candidate
        progress = False
        for priority, _, v in candidates:
            if v in eliminated:
                continue
            pos_set = var_pos[v]
            neg_set = var_neg[v]

            # Pure literal: just delete all clauses
            if not pos_set or not neg_set:
                to_delete = set(pos_set) | set(neg_set)
                # Update indices: remove these clauses' literals
                for cid in to_delete:
                    if cid in clauses_dict:
                        clause = clauses_dict[cid]
                        for lit in clause:
                            if lit > 0:
                                var_pos[lit].discard(cid)
                            else:
                                var_neg[-lit].discard(cid)
                        del clauses_dict[cid]
                eliminated.add(v)
                n_eliminations += 1
                progress = True
                break

            # Bounded BVE: try to resolve and check growth
            pos_clauses = [clauses_dict[cid] for cid in pos_set]
            neg_clauses = [clauses_dict[cid] for cid in neg_set]
            resolvents = []
            for c1 in pos_clauses:
                for c2 in neg_clauses:
                    r = resolve(c1, c2, v)
                    if r is not None:
                        resolvents.append(r)

            n_orig = len(pos_set) + len(neg_set)
            if len(resolvents) - n_orig > args.max_growth:
                continue  # would grow too much

            # Check for empty-clause resolvent → UNSAT
            for r in resolvents:
                if len(r) == 0:
                    print(f"Empty clause derived during elimination of var {v} — UNSAT")
                    print(f"After {n_eliminations} eliminations, "
                          f"{len(clauses_dict)} clauses remain, "
                          f"{time.time()-t0:.2f}s wall")
                    sys.exit(0)

            # Eliminate: delete original clauses, add resolvents
            to_delete = set(pos_set) | set(neg_set)
            for cid in to_delete:
                if cid in clauses_dict:
                    clause = clauses_dict[cid]
                    for lit in clause:
                        if lit > 0:
                            var_pos[lit].discard(cid)
                        else:
                            var_neg[-lit].discard(cid)
                    del clauses_dict[cid]

            for r in resolvents:
                cid = next_id
                next_id += 1
                clauses_dict[cid] = r
                for lit in r:
                    if lit > 0:
                        var_pos[lit].add(cid)
                    else:
                        var_neg[-lit].add(cid)

            n_resolutions += len(resolvents)
            eliminated.add(v)
            n_eliminations += 1
            progress = True
            break

        if not progress:
            break

        if n_eliminations % 1000 == 0 and n_eliminations > 0:
            print(f"  ... {n_eliminations} eliminations, "
                  f"{len(clauses_dict)} clauses, "
                  f"{time.time()-t0:.2f}s",
                  file=sys.stderr)

    # Renumber surviving vars
    surviving_vars = sorted(set(range(1, n_vars + 1)) - eliminated)
    old_to_new = {old: new for new, old in enumerate(surviving_vars, start=1)}
    new_to_old = {new: old for old, new in old_to_new.items()}

    out_clauses = []
    for clause in clauses_dict.values():
        new_clause = tuple(
            (old_to_new[abs(l)] if l > 0 else -old_to_new[abs(l)])
            for l in clause if abs(l) in old_to_new
        )
        out_clauses.append(new_clause)

    new_n_vars = len(surviving_vars)

    # Write output
    header = (
        f"shell_eliminate_v2 — 2026-04-28 (F232 fix)\n"
        f"input: {args.input}\n"
        f"original vars: {n_vars}, clauses: {n_clauses_decl}\n"
        f"eliminated: {n_eliminations} vars, resolutions: {n_resolutions}\n"
        f"output: {new_n_vars} vars, {len(out_clauses)} clauses\n"
        f"max_growth: {args.max_growth}\n"
    )
    with open(args.output, "w") as f:
        for line in header.splitlines():
            f.write(f"c {line}\n")
        f.write(f"p cnf {new_n_vars} {len(out_clauses)}\n")
        for clause in out_clauses:
            f.write(" ".join(str(l) for l in clause) + " 0\n")

    with open(args.output + ".varmap.json", "w") as f:
        json.dump({"new_to_old": new_to_old}, f)

    report = {
        "input": args.input,
        "output": args.output,
        "input_vars": n_vars,
        "input_clauses": n_clauses_decl,
        "eliminated_vars": n_eliminations,
        "n_resolutions": n_resolutions,
        "output_vars": new_n_vars,
        "output_clauses": len(out_clauses),
        "elimination_pct": 100 * n_eliminations / n_vars,
        "wall_seconds": time.time() - t0,
    }
    with open(args.output + ".report.json", "w") as f:
        json.dump(report, f, indent=2)

    print(f"\nFinal: {new_n_vars} vars ({100*n_eliminations/n_vars:.1f}% eliminated), "
          f"{len(out_clauses)} clauses")
    print(f"Total wall: {time.time()-t0:.2f}s")


if __name__ == "__main__":
    main()
