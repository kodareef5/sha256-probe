#!/usr/bin/env python3
"""
Analyze the hard-core clauses of sr=61 SLS.

Approach: re-encode sr=61 with checkpoints to map clause index ranges
to SHA-256 operations. Then evaluate the SLS best assignment to identify
which operations resist satisfaction.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collections import defaultdict

enc = __import__('13_custom_cnf_encoder')
sigma0_py = enc.sigma0_py
sigma1_py = enc.sigma1_py
K = enc.K


def encode_sr61_with_map(m0=0x17149975, fill=0xffffffff):
    """Re-encode sr=61, returning (cnf, clause_map).

    clause_map: list of (start_idx, end_idx, operation_name)
    """
    M1 = [m0] + [fill] * 15
    M2 = list(M1)
    M2[0] ^= 0x80000000
    M2[9] ^= 0x80000000

    state1, W1_pre = enc.precompute_state(M1)
    state2, W2_pre = enc.precompute_state(M2)

    cnf = enc.CNFBuilder()
    clause_map = []

    def checkpoint(name):
        """Record clause range for the NEXT operation."""
        return len(cnf.clauses), name

    def finish(cp):
        start, name = cp
        end = len(cnf.clauses)
        if end > start:
            clause_map.append((start, end, name))

    cp = checkpoint("init")
    s1 = tuple(cnf.const_word(v) for v in state1)
    s2 = tuple(cnf.const_word(v) for v in state2)
    finish(cp)

    cp = checkpoint("free_words")
    w1_free = [cnf.free_word(f"W1_{57+i}") for i in range(3)]
    w2_free = [cnf.free_word(f"W2_{57+i}") for i in range(3)]
    finish(cp)

    W1s = list(w1_free)
    W2s = list(w2_free)

    # W[60]
    cp = checkpoint("sched_W60_m1")
    w1_60 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_free[1]), cnf.const_word(W1_pre[53])),
        cnf.add_word(cnf.const_word(sigma0_py(W1_pre[45])), cnf.const_word(W1_pre[44]))
    )
    finish(cp)
    cp = checkpoint("sched_W60_m2")
    w2_60 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_free[1]), cnf.const_word(W2_pre[53])),
        cnf.add_word(cnf.const_word(sigma0_py(W2_pre[45])), cnf.const_word(W2_pre[44]))
    )
    finish(cp)
    W1s.append(w1_60); W2s.append(w2_60)

    # W[61]
    cp = checkpoint("sched_W61_m1")
    w1_61 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_free[2]), cnf.const_word(W1_pre[54])),
        cnf.add_word(cnf.const_word(sigma0_py(W1_pre[46])), cnf.const_word(W1_pre[45]))
    )
    finish(cp)
    cp = checkpoint("sched_W61_m2")
    w2_61 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_free[2]), cnf.const_word(W2_pre[54])),
        cnf.add_word(cnf.const_word(sigma0_py(W2_pre[46])), cnf.const_word(W2_pre[45]))
    )
    finish(cp)
    W1s.append(w1_61); W2s.append(w2_61)

    # W[62]
    cp = checkpoint("sched_W62_m1")
    w1_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W1s[3]), cnf.const_word(W1_pre[55])),
        cnf.add_word(cnf.const_word(sigma0_py(W1_pre[47])), cnf.const_word(W1_pre[46]))
    )
    finish(cp)
    cp = checkpoint("sched_W62_m2")
    w2_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W2s[3]), cnf.const_word(W2_pre[55])),
        cnf.add_word(cnf.const_word(sigma0_py(W2_pre[47])), cnf.const_word(W2_pre[46]))
    )
    finish(cp)
    W1s.append(w1_62); W2s.append(w2_62)

    # W[63]
    cp = checkpoint("sched_W63_m1")
    w1_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W1s[4]), cnf.const_word(W1_pre[56])),
        cnf.add_word(cnf.const_word(sigma0_py(W1_pre[48])), cnf.const_word(W1_pre[47]))
    )
    finish(cp)
    cp = checkpoint("sched_W63_m2")
    w2_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W2s[4]), cnf.const_word(W2_pre[56])),
        cnf.add_word(cnf.const_word(sigma0_py(W2_pre[48])), cnf.const_word(W2_pre[47]))
    )
    finish(cp)
    W1s.append(w1_63); W2s.append(w2_63)

    # Rounds 57-63 for message 1
    st1 = s1
    for i in range(7):
        cp = checkpoint(f"round{57+i}_m1")
        st1 = cnf.sha256_round_correct(st1, K[57 + i], W1s[i])
        finish(cp)

    # Rounds 57-63 for message 2
    st2 = s2
    for i in range(7):
        cp = checkpoint(f"round{57+i}_m2")
        st2 = cnf.sha256_round_correct(st2, K[57 + i], W2s[i])
        finish(cp)

    # Collision constraint
    cp = checkpoint("collision_eq")
    for i in range(8):
        cnf.eq_word(st1[i], st2[i])
    finish(cp)

    return cnf, clause_map


def get_op_for_clause(clause_idx, clause_map):
    for start, end, name in clause_map:
        if start <= clause_idx < end:
            return name
    return "unmapped"


def analyze(cnf, clause_map, assignment_file):
    # Parse assignment
    assign = {}
    with open(assignment_file) as f:
        for line in f:
            parts = line.strip().split()
            if not parts:
                continue
            lit = int(parts[0])
            assign[abs(lit)] = lit > 0

    # Evaluate each clause
    unsat_by_op = defaultdict(int)
    total_by_op = defaultdict(int)

    for ci, clause in enumerate(cnf.clauses):
        op = get_op_for_clause(ci, clause_map)
        total_by_op[op] += 1

        satisfied = False
        for lit in clause:
            var = abs(lit)
            val = assign.get(var, True)
            if (lit > 0 and val) or (lit < 0 and not val):
                satisfied = True
                break

        if not satisfied:
            unsat_by_op[op] += 1

    return total_by_op, unsat_by_op


def main():
    print("=" * 60)
    print("SR=61 Hard-Core Clause Analysis")
    print("=" * 60)

    cnf, clause_map = encode_sr61_with_map()
    print(f"\nEncoded: {cnf.next_var - 1} vars, {len(cnf.clauses)} clauses")

    # Show clause distribution
    print(f"\n{'Operation':<22} {'Clause Range':<18} {'Count':>6} {'%':>6}")
    print("-" * 54)
    for start, end, name in clause_map:
        count = end - start
        pct = 100 * count / len(cnf.clauses)
        print(f"  {name:<20} {start:>6}-{end-1:<8} {count:>6} {pct:>5.1f}%")

    # Group by category
    sched_total = sum(e-s for s, e, n in clause_map if n.startswith("sched"))
    round_m1 = sum(e-s for s, e, n in clause_map if n.endswith("_m1") and n.startswith("round"))
    round_m2 = sum(e-s for s, e, n in clause_map if n.endswith("_m2") and n.startswith("round"))
    collision = sum(e-s for s, e, n in clause_map if n.startswith("collision"))
    print(f"\n  Schedule clauses:     {sched_total:>6} ({100*sched_total/len(cnf.clauses):.1f}%)")
    print(f"  Round clauses (m1):   {round_m1:>6} ({100*round_m1/len(cnf.clauses):.1f}%)")
    print(f"  Round clauses (m2):   {round_m2:>6} ({100*round_m2/len(cnf.clauses):.1f}%)")
    print(f"  Collision clauses:    {collision:>6} ({100*collision/len(cnf.clauses):.1f}%)")

    # Analyze assignment
    assign_file = sys.argv[1] if len(sys.argv) > 1 else '/tmp/sls_v4_best.txt'
    if not os.path.exists(assign_file):
        print(f"\nNo assignment at {assign_file} — run SLS v4 first.")
        return

    print(f"\n{'='*60}")
    print(f"Analyzing assignment: {assign_file}")
    print(f"{'='*60}")

    total_by_op, unsat_by_op = analyze(cnf, clause_map, assign_file)
    total_unsat = sum(unsat_by_op.values())
    total_clauses = len(cnf.clauses)
    print(f"\nTotal unsatisfied: {total_unsat}/{total_clauses} "
          f"({100*(1-total_unsat/total_clauses):.2f}% satisfied)")

    print(f"\n{'Operation':<22} {'Unsat':>6} {'Total':>6} {'Unsat%':>7} {'Contribution':>12}")
    print("-" * 55)
    for start, end, name in clause_map:
        u = unsat_by_op.get(name, 0)
        t = total_by_op.get(name, 0)
        rate = 100 * u / t if t > 0 else 0
        contrib = 100 * u / total_unsat if total_unsat > 0 else 0
        marker = " ***" if rate > 15 else ""
        print(f"  {name:<20} {u:>6} {t:>6} {rate:>6.1f}% {contrib:>10.1f}%{marker}")

    # Summary by category
    print(f"\n--- By Category ---")
    cats = {
        "Schedule": [n for _, _, n in clause_map if n.startswith("sched")],
        "Rounds (m1)": [n for _, _, n in clause_map if n.startswith("round") and n.endswith("_m1")],
        "Rounds (m2)": [n for _, _, n in clause_map if n.startswith("round") and n.endswith("_m2")],
        "Collision": [n for _, _, n in clause_map if n.startswith("collision")],
    }
    for cat, ops in cats.items():
        u = sum(unsat_by_op.get(op, 0) for op in ops)
        t = sum(total_by_op.get(op, 0) for op in ops)
        rate = 100 * u / t if t > 0 else 0
        contrib = 100 * u / total_unsat if total_unsat > 0 else 0
        print(f"  {cat:<20} {u:>6}/{t:<6} ({rate:.1f}% unsat, {contrib:.1f}% of hard core)")

    # Identify the hardest rounds
    print(f"\n--- Hardest Rounds ---")
    round_data = []
    for start, end, name in clause_map:
        if name.startswith("round"):
            u = unsat_by_op.get(name, 0)
            t = total_by_op.get(name, 0)
            round_data.append((name, u, t))
    round_data.sort(key=lambda x: -x[1])
    for name, u, t in round_data[:6]:
        rate = 100 * u / t if t > 0 else 0
        print(f"  {name}: {u}/{t} unsat ({rate:.1f}%)")

    print(f"\n{'='*60}")


if __name__ == "__main__":
    main()
