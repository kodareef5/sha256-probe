#!/usr/bin/env python3
"""
Script 66a: Forward Anchor Validation (Rounds 56->60)

Validates the forward half of the MITM anchor approach for sr=60.
Encodes rounds 57-60 from a fixed Round 56 state to a free anchor at Round 60.

Structure:
  - Fixed Round 56 state (precomputed from M[0]=0x17149975, standard IV, MSB kernel)
  - Free W1[57..60] and W2[57..60] (4 free words per message = 256 bits)
  - Free anchor state variables at Round 60 for both messages (256 bits each)
  - Constraint: anchor == actual Round 60 state from the SHA-256 rounds

This should be trivially SAT: the anchor just adopts whatever value the rounds produce.
"""

import sys
import os
import time
import subprocess

sys.path.insert(0, '/root/bounties/sha256_scripts')
enc = __import__('13_custom_cnf_encoder')

def main():
    print("=" * 70)
    print("66a: Forward Anchor Validation (Rounds 56 -> 60)")
    print("=" * 70)

    # --- Precompute Round 56 state ---
    M1 = [0x17149975] + [0xffffffff] * 15
    M2 = M1[:]; M2[0] ^= 0x80000000; M2[9] ^= 0x80000000

    state1, W1_pre = enc.precompute_state(M1)
    state2, W2_pre = enc.precompute_state(M2)

    print(f"\nRound 56 states (precomputed):")
    labels = ['a','b','c','d','e','f','g','h']
    for i in range(8):
        print(f"  {labels[i]}56_1 = 0x{state1[i]:08x}   {labels[i]}56_2 = 0x{state2[i]:08x}")
    print(f"  da56 = 0x{(state1[0] ^ state2[0]) & 0xFFFFFFFF:08x} (should be 0)")

    # --- Build CNF ---
    t0 = time.time()
    cnf = enc.CNFBuilder()

    # Fixed Round 56 states as constants
    s1 = tuple(cnf.const_word(v) for v in state1)
    s2 = tuple(cnf.const_word(v) for v in state2)

    # Free schedule words W[57..60] for both messages (4 words each)
    w1_free = [cnf.free_word(f"W1_{57+i}") for i in range(4)]
    w2_free = [cnf.free_word(f"W2_{57+i}") for i in range(4)]

    print(f"\nFree schedule words: W[57..60] x 2 messages = {4*2*32} bits")

    # --- Encode rounds 57-60 for both messages ---
    print(f"\nEncoding rounds 57-60 for message 1...")
    st1 = s1
    for i in range(4):
        st1 = cnf.sha256_round_correct(st1, enc.K[57 + i], w1_free[i])
        n = cnf.next_var - 1
        nc = len(cnf.clauses)
        print(f"  Round {57+i}: {n} vars, {nc} clauses")

    print(f"Encoding rounds 57-60 for message 2...")
    st2 = s2
    for i in range(4):
        st2 = cnf.sha256_round_correct(st2, enc.K[57 + i], w2_free[i])
        n = cnf.next_var - 1
        nc = len(cnf.clauses)
        print(f"  Round {57+i}: {n} vars, {nc} clauses")

    # --- Create free anchor variables at Round 60 ---
    print(f"\nCreating free anchor variables at Round 60...")
    anchor1 = tuple(cnf.free_word(f"anc1_{labels[i]}60") for i in range(8))
    anchor2 = tuple(cnf.free_word(f"anc2_{labels[i]}60") for i in range(8))
    print(f"  Anchor bits: {8*32*2} = {8*32*2} free variables (256 per message)")

    # --- Constrain anchor == actual Round 60 state ---
    print(f"Adding anchor equality constraints...")
    for i in range(8):
        cnf.eq_word(anchor1[i], st1[i])
        cnf.eq_word(anchor2[i], st2[i])

    t_encode = time.time() - t0

    # --- Write DIMACS ---
    cnf_file = "/tmp/66a_forward_anchor.cnf"
    n_vars, n_clauses = cnf.write_dimacs(cnf_file)
    file_size = os.path.getsize(cnf_file)

    print(f"\nEncoder statistics:")
    print(f"  XOR gates: {cnf.stats['xor']}")
    print(f"  MUX gates: {cnf.stats['mux']}")
    print(f"  MAJ gates: {cnf.stats['maj']}")
    print(f"  Full adders: {cnf.stats['fa']}")
    print(f"  Constant folds: {cnf.stats['const_fold']}")

    print(f"\nDIMACS output: {cnf_file}")
    print(f"  Variables: {n_vars}")
    print(f"  Clauses:   {n_clauses}")
    print(f"  File size: {file_size // 1024} KB")
    print(f"  Encoding time: {t_encode:.2f}s")

    # --- Run Kissat ---
    timeout = 60
    print(f"\n{'='*70}")
    print(f"Running Kissat (timeout: {timeout}s)")
    print(f"{'='*70}")

    try:
        t0 = time.time()
        result = subprocess.run(
            ["timeout", str(timeout), "kissat", cnf_file],
            capture_output=True, text=True, timeout=timeout + 30
        )
        elapsed = time.time() - t0

        lines = result.stdout.split('\n')
        sat_line = [l for l in lines if l.startswith('s ')]
        stats_lines = [l for l in lines if 'conflicts' in l.lower() or 'decisions' in l.lower()
                       or 'propagations' in l.lower() or 'process-time' in l.lower()]

        if sat_line:
            print(f"Result: {sat_line[0]}")
        else:
            print(f"Result: timeout/unknown (exit code {result.returncode})")

        for sl in stats_lines[-5:]:
            print(f"  {sl.strip()}")

        print(f"Time: {elapsed:.2f}s")

        if result.returncode == 10:
            print("\n>>> SATISFIABLE (as expected)")
            # Extract a sample free word to verify
            solution = {}
            for line in lines:
                if line.startswith('v '):
                    for lit in line[2:].split():
                        lit_val = int(lit)
                        if lit_val != 0:
                            solution[abs(lit_val)] = (lit_val > 0)

            print("\nSample solution (free schedule words):")
            for word_idx in range(4):
                for msg in [1, 2]:
                    val = 0
                    for bit in range(32):
                        name = f"W{msg}_{57+word_idx}[{bit}]"
                        for var_id, var_name in cnf.free_var_names.items():
                            if var_name == name and var_id in solution:
                                if solution[var_id]:
                                    val |= (1 << bit)
                    print(f"  W{msg}[{57+word_idx}] = 0x{val:08x}")

            print("\nSample solution (anchor state at Round 60):")
            for msg_label, anchor in [("msg1", anchor1), ("msg2", anchor2)]:
                for i in range(8):
                    val = 0
                    for bit in range(32):
                        var_id = anchor[i][bit]
                        if abs(var_id) in solution:
                            bval = solution[abs(var_id)]
                            if var_id < 0:
                                bval = not bval
                            if bval:
                                val |= (1 << bit)
                    print(f"  {msg_label} {labels[i]}60 = 0x{val:08x}")

        elif result.returncode == 20:
            print("\n>>> UNSATISFIABLE (unexpected!)")
        else:
            print(f"\n>>> Timeout or error (exit code {result.returncode})")

    except subprocess.TimeoutExpired:
        print(f"Timeout after {timeout}s")
    except FileNotFoundError:
        print("kissat not found")


if __name__ == "__main__":
    main()
