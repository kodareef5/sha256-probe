#!/usr/bin/env python3
"""
Script 66b: Backward Anchor Validation (Rounds 60->63)

Validates the backward half of the MITM anchor approach for sr=60.
Encodes rounds 61-63 from a free anchor at Round 60 to collision at Round 63.

Structure:
  - Free anchor state at Round 60 for both messages (256 bits each = 512 bits total)
  - Free W[61], W[62], W[63] for both messages (approach (a): pure geometry test,
    no schedule coupling to the forward half)
  - Collision constraint: final state1 == final state2 after Round 63

Freedom analysis:
  - 512 bits (anchor) + 192 bits (3 free W words x 2 messages) = 704 bits of freedom
  - 256 bits of collision constraints (8 x 32-bit state words must match)
  - Net slack: 704 - 256 = 448 bits
  - Should be easily SAT

This tests pure backward reachability from anchor to collision, without
schedule coupling between forward and backward halves.
"""

import sys
import os
import time
import subprocess

sys.path.insert(0, '/root/bounties/sha256_scripts')
enc = __import__('13_custom_cnf_encoder')

def main():
    print("=" * 70)
    print("66b: Backward Anchor Validation (Rounds 60 -> 63)")
    print("=" * 70)

    # --- Build CNF ---
    t0 = time.time()
    cnf = enc.CNFBuilder()

    labels = ['a','b','c','d','e','f','g','h']

    # --- Free anchor state at Round 60 for both messages ---
    print(f"\nCreating free anchor state at Round 60...")
    anchor1 = tuple(cnf.free_word(f"anc1_{labels[i]}60") for i in range(8))
    anchor2 = tuple(cnf.free_word(f"anc2_{labels[i]}60") for i in range(8))
    print(f"  Anchor bits: 2 x 256 = 512 free variables")

    # --- Free schedule words W[61..63] for both messages ---
    # Approach (a): all free, no schedule coupling
    print(f"Creating free schedule words W[61..63] for both messages...")
    w1_free = [cnf.free_word(f"W1_{61+i}") for i in range(3)]
    w2_free = [cnf.free_word(f"W2_{61+i}") for i in range(3)]
    print(f"  Schedule bits: 2 x 3 x 32 = 192 free variables")
    print(f"  Total freedom: 512 + 192 = 704 bits")

    # --- Encode rounds 61-63 for both messages ---
    print(f"\nEncoding rounds 61-63 for message 1...")
    st1 = anchor1
    for i in range(3):
        st1 = cnf.sha256_round_correct(st1, enc.K[61 + i], w1_free[i])
        n = cnf.next_var - 1
        nc = len(cnf.clauses)
        print(f"  Round {61+i}: {n} vars, {nc} clauses")

    print(f"Encoding rounds 61-63 for message 2...")
    st2 = anchor2
    for i in range(3):
        st2 = cnf.sha256_round_correct(st2, enc.K[61 + i], w2_free[i])
        n = cnf.next_var - 1
        nc = len(cnf.clauses)
        print(f"  Round {61+i}: {n} vars, {nc} clauses")

    # --- Collision constraint: final state1 == final state2 ---
    print(f"\nAdding collision constraints (state after Round 63)...")
    n_eq_clauses_before = len(cnf.clauses)
    for i in range(8):
        cnf.eq_word(st1[i], st2[i])
    n_eq_clauses_after = len(cnf.clauses)
    print(f"  Equality clauses added: {n_eq_clauses_after - n_eq_clauses_before}")
    print(f"  Collision constraint: 8 x 32 = 256 bits must match")
    print(f"  Net slack: 704 - 256 = 448 bits")

    t_encode = time.time() - t0

    # --- Write DIMACS ---
    cnf_file = "/tmp/66b_backward_anchor.cnf"
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
            # Extract solution
            solution = {}
            for line in lines:
                if line.startswith('v '):
                    for lit in line[2:].split():
                        lit_val = int(lit)
                        if lit_val != 0:
                            solution[abs(lit_val)] = (lit_val > 0)

            # Show anchor state
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

            # Show schedule words
            print("\nSample solution (free schedule words):")
            for word_idx in range(3):
                for msg in [1, 2]:
                    val = 0
                    for bit in range(32):
                        name = f"W{msg}_{61+word_idx}[{bit}]"
                        for var_id, var_name in cnf.free_var_names.items():
                            if var_name == name and var_id in solution:
                                if solution[var_id]:
                                    val |= (1 << bit)
                    print(f"  W{msg}[{61+word_idx}] = 0x{val:08x}")

            # Verify collision: compute final states natively
            print("\nVerifying collision natively...")
            def extract_word(word_bits, solution):
                val = 0
                for bit in range(32):
                    var_id = word_bits[bit]
                    if abs(var_id) in solution:
                        bval = solution[abs(var_id)]
                        if var_id < 0:
                            bval = not bval
                        if bval:
                            val |= (1 << bit)
                return val

            # Extract final states
            match_count = 0
            for i in range(8):
                v1 = extract_word(st1[i], solution)
                v2 = extract_word(st2[i], solution)
                match = "MATCH" if v1 == v2 else "DIFFER"
                if v1 == v2:
                    match_count += 1
                print(f"  {labels[i]}63: msg1=0x{v1:08x} msg2=0x{v2:08x} [{match}]")
            print(f"  Collision: {match_count}/8 words match")

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
