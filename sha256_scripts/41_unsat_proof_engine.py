#!/usr/bin/env python3
"""
Script 41: Constant-Folded UNSAT Proof Engine

THE DISCOVERY: Fixing bits at ENCODE TIME (constant-folded through the
circuit) kills 88% of the search space instantly. Appending unit clauses
kills 0%. The SAT solver CANNOT propagate structural constants on the fly.

THIS SCRIPT: Fix the top 8 bits of W1[57] via constant folding (256 combos).
Each combo generates a MASSIVELY SIMPLIFIED DIMACS where thousands of
variables are eliminated before Kissat sees them.

If 100% return UNSAT: sr=60 is IMPOSSIBLE for M[0]=0x17149975.
If any return SAT: we just solved sr=60.
If some timeout: refine those partitions with more fixed bits.
"""

import sys
import os
import time
import subprocess
import multiprocessing
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from importlib import import_module
enc = import_module('13_custom_cnf_encoder')


def encode_sr60_with_fixed_w57_bits(fixed_msb_value, n_fixed_bits=8):
    """
    Encode sr=60 with the top n_fixed_bits of W1[57] constant-folded.

    This is NOT unit clause injection. The fixed bits are baked into the
    encoder as constants, so the CNFBuilder's constant propagation cascades
    through all downstream XOR/MUX/MAJ/adder gates, eliminating variables
    and simplifying the circuit BEFORE DIMACS generation.
    """
    M1 = [0x17149975] + [0xffffffff] * 15
    M2 = M1.copy()
    M2[0] ^= 0x80000000
    M2[9] ^= 0x80000000

    state1, W1_pre = enc.precompute_state(M1)
    state2, W2_pre = enc.precompute_state(M2)

    cnf = enc.CNFBuilder()
    s1 = tuple(cnf.const_word(v) for v in state1)
    s2 = tuple(cnf.const_word(v) for v in state2)

    # W1[57]: top n_fixed_bits are CONSTANTS, rest are free variables
    w1_57 = []
    for bit in range(32):
        if bit >= (32 - n_fixed_bits):
            # This bit is fixed — constant-fold it
            bit_val = bool((fixed_msb_value >> (bit - (32 - n_fixed_bits))) & 1)
            w1_57.append(cnf._const(bit_val))
        else:
            # This bit is free
            v = cnf.new_var()
            cnf.free_var_names[v] = f"W1_57[{bit}]"
            w1_57.append(v)

    # All other free words are fully free
    w1_58 = cnf.free_word("W1_58")
    w1_59 = cnf.free_word("W1_59")
    w1_60 = cnf.free_word("W1_60")
    w2_57 = cnf.free_word("W2_57")
    w2_58 = cnf.free_word("W2_58")
    w2_59 = cnf.free_word("W2_59")
    w2_60 = cnf.free_word("W2_60")

    w1_free = [w1_57, w1_58, w1_59, w1_60]
    w2_free = [w2_57, w2_58, w2_59, w2_60]

    W1_schedule = list(w1_free)
    W2_schedule = list(w2_free)

    # W[61] enforced
    w1_61 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_free[2]), cnf.const_word(W1_pre[54])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[46])), cnf.const_word(W1_pre[45])))
    w2_61 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_free[2]), cnf.const_word(W2_pre[54])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W2_pre[46])), cnf.const_word(W2_pre[45])))
    W1_schedule.append(w1_61)
    W2_schedule.append(w2_61)

    w1_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W1_schedule[3]), cnf.const_word(W1_pre[55])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[47])), cnf.const_word(W1_pre[46])))
    w2_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W2_schedule[3]), cnf.const_word(W2_pre[55])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W2_pre[47])), cnf.const_word(W2_pre[46])))
    w1_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W1_schedule[4]), cnf.const_word(W1_pre[56])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[48])), cnf.const_word(W1_pre[47])))
    w2_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W2_schedule[4]), cnf.const_word(W2_pre[56])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W2_pre[48])), cnf.const_word(W2_pre[47])))

    W1_schedule.extend([w1_62, w1_63])
    W2_schedule.extend([w2_62, w2_63])

    st1 = s1
    for i in range(7):
        st1 = cnf.sha256_round_correct(st1, enc.K[57+i], W1_schedule[i])
    st2 = s2
    for i in range(7):
        st2 = cnf.sha256_round_correct(st2, enc.K[57+i], W2_schedule[i])

    for i in range(8):
        cnf.eq_word(st1[i], st2[i])

    return cnf


def solve_partition(args):
    """Encode and solve one partition."""
    msb_val, n_bits, timeout_sec, work_dir = args

    try:
        cnf = encode_sr60_with_fixed_w57_bits(msb_val, n_bits)
        nv = cnf.next_var - 1
        nc = len(cnf.clauses)
        cf = cnf.stats['const_fold']

        cnf_file = os.path.join(work_dir, f"p_{msb_val:03d}.cnf")
        cnf.write_dimacs(cnf_file)

        t0 = time.time()
        r = subprocess.run(
            ["kissat", "-q", cnf_file],
            capture_output=True, text=True,
            timeout=timeout_sec
        )
        elapsed = time.time() - t0

        try:
            os.unlink(cnf_file)
        except:
            pass

        if r.returncode == 10:
            return "SAT", msb_val, elapsed, nv, nc, cf
        elif r.returncode == 20:
            return "UNSAT", msb_val, elapsed, nv, nc, cf
        else:
            return "TIMEOUT", msb_val, elapsed, nv, nc, cf

    except subprocess.TimeoutExpired:
        try:
            os.unlink(os.path.join(work_dir, f"p_{msb_val:03d}.cnf"))
        except:
            pass
        return "TIMEOUT", msb_val, timeout_sec, 0, 0, 0
    except Exception as e:
        return "ERROR", msb_val, 0, 0, 0, 0


def main():
    n_bits = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 60
    n_workers = int(sys.argv[3]) if len(sys.argv) > 3 else 16

    n_partitions = 2 ** n_bits

    print("=" * 70, flush=True)
    print("CONSTANT-FOLDED UNSAT PROOF ENGINE", flush=True)
    print(f"Fixing top {n_bits} bits of W1[57] via constant folding", flush=True)
    print(f"  Partitions: {n_partitions}", flush=True)
    print(f"  Timeout per partition: {timeout}s", flush=True)
    print(f"  Workers: {n_workers}", flush=True)
    print(f"  Estimated time: {n_partitions * timeout / n_workers / 60:.0f} min", flush=True)
    print("=" * 70, flush=True)

    # Quick preview: encode partition 0 to show size reduction
    preview = encode_sr60_with_fixed_w57_bits(0, n_bits)
    base_vars, base_clauses = 10988, 46255
    prev_vars = preview.next_var - 1
    prev_clauses = len(preview.clauses)
    prev_folds = preview.stats['const_fold']

    print(f"\n  Base sr=60: {base_vars} vars, {base_clauses} clauses", flush=True)
    print(f"  With {n_bits} bits folded: {prev_vars} vars, {prev_clauses} clauses", flush=True)
    print(f"  Reduction: {base_vars - prev_vars} vars ({(base_vars-prev_vars)/base_vars*100:.1f}%), "
          f"{base_clauses - prev_clauses} clauses ({(base_clauses-prev_clauses)/base_clauses*100:.1f}%)", flush=True)
    print(f"  Constant folds: {prev_folds} (vs ~4694 base)", flush=True)

    work_dir = tempfile.mkdtemp(prefix="unsat_proof_")
    tasks = [(msb, n_bits, timeout, work_dir) for msb in range(n_partitions)]

    print(f"\nLaunching {n_partitions} constant-folded partitions...\n", flush=True)
    t_start = time.time()

    n_sat = n_unsat = n_timeout = n_error = 0
    sat_partitions = []
    timeout_partitions = []

    with multiprocessing.Pool(n_workers) as pool:
        for status, msb_val, elapsed, nv, nc, cf in pool.imap_unordered(solve_partition, tasks):
            if status == "SAT":
                n_sat += 1
                sat_partitions.append(msb_val)
                t_total = time.time() - t_start
                print(f"  [!!!] PARTITION {msb_val:3d} (0x{msb_val:02x}): SAT in {elapsed:.1f}s "
                      f"({nv} vars, {nc} clauses)", flush=True)
                pool.terminate()
                break
            elif status == "UNSAT":
                n_unsat += 1
            elif status == "TIMEOUT":
                n_timeout += 1
                timeout_partitions.append(msb_val)
            else:
                n_error += 1

            done = n_sat + n_unsat + n_timeout + n_error
            if done % max(1, n_partitions // 10) == 0:
                t_total = time.time() - t_start
                rate = done / t_total if t_total > 0 else 0
                eta = (n_partitions - done) / rate if rate > 0 else 0
                print(f"  [{done}/{n_partitions}] UNSAT={n_unsat} TO={n_timeout} SAT={n_sat} "
                      f"({t_total:.0f}s, ETA {eta:.0f}s)", flush=True)

    t_total = time.time() - t_start
    shutil.rmtree(work_dir, ignore_errors=True)

    # Final report
    total = n_sat + n_unsat + n_timeout + n_error
    print(f"\n{'='*70}", flush=True)
    print("FINAL RESULTS", flush=True)
    print(f"{'='*70}", flush=True)
    print(f"  Partitions tested: {total}/{n_partitions}", flush=True)
    print(f"  UNSAT:   {n_unsat:5d} ({n_unsat/max(1,total)*100:.1f}%)", flush=True)
    print(f"  TIMEOUT: {n_timeout:5d} ({n_timeout/max(1,total)*100:.1f}%)", flush=True)
    print(f"  SAT:     {n_sat:5d}", flush=True)
    print(f"  ERROR:   {n_error:5d}", flush=True)
    print(f"  Time:    {t_total:.1f}s ({t_total/3600:.2f}h)", flush=True)

    if n_sat > 0:
        print(f"\n  [!!!] SR=60 COLLISION FOUND!", flush=True)
        print(f"  SAT partitions: {sat_partitions}", flush=True)
    elif n_unsat == n_partitions:
        print(f"\n  [!!!] SR=60 IS PROVABLY UNSATISFIABLE for M[0]=0x17149975!", flush=True)
        print(f"  All {n_partitions} constant-folded partitions returned UNSAT.", flush=True)
        print(f"  The paper's candidate is a mathematical dead end.", flush=True)
    else:
        print(f"\n  Partial result: {n_unsat/total*100:.1f}% proven UNSAT.", flush=True)
        if timeout_partitions:
            print(f"  Surviving partitions ({len(timeout_partitions)}): {timeout_partitions[:20]}{'...' if len(timeout_partitions) > 20 else ''}", flush=True)
            print(f"  Next: re-run survivors with longer timeout or more fixed bits.", flush=True)


if __name__ == "__main__":
    main()
