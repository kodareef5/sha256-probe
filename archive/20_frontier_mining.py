#!/usr/bin/env python3
"""
Script 20: k=3/k=4 Frontier Mining

Generates diverse k=3 solutions and mines them for structural invariants
(near-backbones, carry biases, affine relations) that generalize to sr=60.

Method:
  1. Solve k=3 repeatedly with blocking clauses to get diverse solutions
  2. Extract free word values from each solution
  3. Mine for bits that are FIXED across all solutions (backbones)
  4. Mine for bit PAIRS where XOR is constant (affine relations)
  5. Validate any findings against k=4 solutions

Backbone bits = structural invariants of the k=3 manifold.
If they hold at k=4 too, they're likely valid at sr=60.
"""

import sys
import os
import time
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from importlib import import_module
enc = import_module('13_custom_cnf_encoder')


def encode_k3_instance(blocking_clauses=None):
    """Encode sr=59 + k=3 schedule compliance with optional blocking clauses."""
    M1 = [0x17149975] + [0xffffffff] * 15
    M2 = M1.copy()
    M2[0] ^= 0x80000000
    M2[9] ^= 0x80000000

    state1, W1_pre = enc.precompute_state(M1)
    state2, W2_pre = enc.precompute_state(M2)

    cnf = enc.CNFBuilder()
    s1 = tuple(cnf.const_word(v) for v in state1)
    s2 = tuple(cnf.const_word(v) for v in state2)

    # 5 free words (sr=59 base)
    w1_free = [cnf.free_word(f"W1_{57+i}") for i in range(5)]
    w2_free = [cnf.free_word(f"W2_{57+i}") for i in range(5)]

    # Schedule enforcement for W[62], W[63]
    w1_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_free[3]), cnf.const_word(W1_pre[55])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[47])), cnf.const_word(W1_pre[46]))
    )
    w2_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_free[3]), cnf.const_word(W2_pre[55])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W2_pre[47])), cnf.const_word(W2_pre[46]))
    )
    w1_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_free[4]), cnf.const_word(W1_pre[56])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[48])), cnf.const_word(W1_pre[47]))
    )
    w2_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_free[4]), cnf.const_word(W2_pre[56])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W2_pre[48])), cnf.const_word(W2_pre[47]))
    )

    W1_tail = list(w1_free) + [w1_62, w1_63]
    W2_tail = list(w2_free) + [w2_62, w2_63]

    # Compression rounds
    st1 = s1
    for i in range(7):
        st1 = cnf.sha256_round_correct(st1, enc.K[57+i], W1_tail[i])
    st2 = s2
    for i in range(7):
        st2 = cnf.sha256_round_correct(st2, enc.K[57+i], W2_tail[i])

    # Collision constraint
    for i in range(8):
        cnf.eq_word(st1[i], st2[i])

    # k=3 schedule compliance for W[61]
    w1_61_sched = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_free[2]), cnf.const_word(W1_pre[54])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[46])), cnf.const_word(W1_pre[45]))
    )
    w2_61_sched = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_free[2]), cnf.const_word(W2_pre[54])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W2_pre[46])), cnf.const_word(W2_pre[45]))
    )

    # Fix low 3 bits of W[61] to match schedule
    for bit in range(3):
        a1, b1 = w1_free[4][bit], w1_61_sched[bit]
        a2, b2 = w2_free[4][bit], w2_61_sched[bit]
        for a, b in [(a1, b1), (a2, b2)]:
            if cnf._is_known(a) and cnf._is_known(b):
                if cnf._get_val(a) != cnf._get_val(b):
                    cnf.clauses.append([])
            elif cnf._is_known(a):
                cnf.clauses.append([b] if cnf._get_val(a) else [-b])
            elif cnf._is_known(b):
                cnf.clauses.append([a] if cnf._get_val(b) else [-a])
            else:
                cnf.clauses.append([-a, b])
                cnf.clauses.append([a, -b])

    # Add blocking clauses (to get diverse solutions)
    if blocking_clauses:
        for bc in blocking_clauses:
            cnf.clauses.append(bc)

    return cnf, w1_free, w2_free


def extract_solution(cnf, w1_free, w2_free, stdout_text):
    """Extract free word values from kissat output."""
    solution = {}
    for line in stdout_text.split('\n'):
        if line.startswith('v '):
            for lit in line[2:].split():
                v = int(lit)
                if v != 0:
                    solution[abs(v)] = (v > 0)

    words = {}
    for wi in range(5):
        for msg, free_list in [(1, w1_free), (2, w2_free)]:
            val = 0
            for bit in range(32):
                var_id = free_list[wi][bit]
                if abs(var_id) in solution:
                    bit_val = solution[abs(var_id)]
                    if var_id < 0:
                        bit_val = not bit_val
                    if bit_val:
                        val |= (1 << bit)
            words[f"W{msg}_{57+wi}"] = val

    return words, solution


def make_blocking_clause(w1_free, w2_free, solution):
    """Create a blocking clause that excludes the current solution."""
    # Block: at least one free word bit must differ
    clause = []
    for wi in range(5):
        for free_list in [w1_free, w2_free]:
            for bit in range(32):
                var_id = free_list[wi][bit]
                if abs(var_id) in solution:
                    val = solution[abs(var_id)]
                    if var_id < 0:
                        val = not val
                    # Add the negation: if this bit was True, add -var; if False, add +var
                    clause.append(-var_id if val else var_id)
    return clause


def main():
    n_solutions = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    timeout_per = int(sys.argv[2]) if len(sys.argv) > 2 else 300

    print(f"{'='*60}", flush=True)
    print(f"Frontier Mining: k=3 Solution Diversity", flush=True)
    print(f"Target: {n_solutions} diverse solutions", flush=True)
    print(f"{'='*60}", flush=True)

    all_words = []
    blocking_clauses = []

    for sol_idx in range(n_solutions):
        print(f"\nSolution {sol_idx+1}/{n_solutions}...", flush=True)

        cnf, w1_free, w2_free = encode_k3_instance(blocking_clauses if blocking_clauses else None)
        cnf_file = f"/tmp/k3_mine_{sol_idx}.cnf"
        cnf.write_dimacs(cnf_file)

        t0 = time.time()
        r = subprocess.run(["timeout", str(timeout_per), "kissat", cnf_file],
                           capture_output=True, text=True, timeout=timeout_per + 30)
        elapsed = time.time() - t0

        if r.returncode == 10:
            words, solution = extract_solution(cnf, w1_free, w2_free, r.stdout)
            all_words.append(words)
            print(f"  SAT in {elapsed:.1f}s: W1[57]=0x{words['W1_57']:08x}", flush=True)

            # Add blocking clause for next iteration
            bc = make_blocking_clause(w1_free, w2_free, solution)
            blocking_clauses.append(bc)
        elif r.returncode == 20:
            print(f"  UNSAT in {elapsed:.1f}s — no more solutions!", flush=True)
            break
        else:
            print(f"  TIMEOUT after {elapsed:.1f}s", flush=True)
            break

        os.unlink(cnf_file)

    if len(all_words) < 2:
        print("\nNot enough solutions for mining.", flush=True)
        return

    # === MINING PHASE ===
    print(f"\n{'='*60}", flush=True)
    print(f"Mining {len(all_words)} solutions for invariants", flush=True)
    print(f"{'='*60}", flush=True)

    # 1. Near-backbones: bits fixed across ALL solutions
    print("\n--- Near-Backbones (bits fixed across all solutions) ---", flush=True)
    backbone_count = 0
    for key in sorted(all_words[0].keys()):
        for bit in range(32):
            vals = set()
            for sol in all_words:
                vals.add((sol[key] >> bit) & 1)
            if len(vals) == 1:
                backbone_count += 1
                if backbone_count <= 30:
                    print(f"  {key} bit {bit:2d} = {vals.pop()} (FIXED)", flush=True)

    print(f"  Total backbones: {backbone_count} / {len(all_words[0]) * 32} bits", flush=True)

    # 2. Affine relations: pairs where XOR is constant
    print("\n--- Affine Relations (bit_i XOR bit_j = const) ---", flush=True)
    affine_count = 0
    keys = sorted(all_words[0].keys())
    for k1 in keys:
        for b1 in range(32):
            for k2 in keys:
                for b2 in range(b1 + 1 if k1 == k2 else 0, 32):
                    if k1 == k2 and b1 >= b2:
                        continue
                    xor_vals = set()
                    for sol in all_words:
                        v1 = (sol[k1] >> b1) & 1
                        v2 = (sol[k2] >> b2) & 1
                        xor_vals.add(v1 ^ v2)
                    if len(xor_vals) == 1:
                        affine_count += 1
                        if affine_count <= 10:
                            print(f"  {k1}[{b1}] XOR {k2}[{b2}] = {xor_vals.pop()}", flush=True)

    print(f"  Total affine pairs: {affine_count}", flush=True)

    # 3. Word-level statistics
    print("\n--- Word-Level Diversity ---", flush=True)
    for key in sorted(all_words[0].keys()):
        values = [sol[key] for sol in all_words]
        unique = len(set(values))
        # XOR all values to see spread
        xor_all = 0
        for v in values:
            xor_all ^= v
        print(f"  {key}: {unique} unique values, XOR-all = 0x{xor_all:08x}", flush=True)

    # 4. Hamming distance between solutions
    print("\n--- Solution Diversity (pairwise Hamming distance) ---", flush=True)
    for i in range(min(5, len(all_words))):
        for j in range(i+1, min(5, len(all_words))):
            hd = 0
            for key in keys:
                hd += bin(all_words[i][key] ^ all_words[j][key]).count('1')
            print(f"  Sol {i} vs Sol {j}: Hamming distance = {hd} / {len(keys)*32}", flush=True)


if __name__ == "__main__":
    main()
