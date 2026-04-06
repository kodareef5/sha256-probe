#!/usr/bin/env python3
"""
gpu_to_sat_pipeline.py — GPU optimization → SAT residual pipeline

Takes optimal W[57] and W[58] values (from GPU exhaustive sweep)
and generates the smallest possible sr=60 CNF for SAT solving.

Pipeline:
1. GPU Phase 1: find W1[57] minimizing de57_err (done, best=9)
2. GPU Phase 2: find W1[58] minimizing total state58 HW (done by laptop)
3. GPU Phase 3: find W2[58] minimizing total state58 HW (TBD)
4. This script: encode residual (W[59]+W[60] free) and solve with Kissat
5. Optional: partition W[59] MSBs for parallelism

Usage: python3 gpu_to_sat_pipeline.py W1_57 W1_58 [W2_58] [timeout] [n_partition_bits]
  If W2_58 is 'free', it's left as a SAT variable.
"""

import sys, os, time, subprocess, tempfile, multiprocessing
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from lib.sha256 import *
from lib.cnf_encoder import CNFBuilder


def encode_residual(m0, fill, W1_57, W2_57, W1_58, W2_58,
                     partition_bits=0, partition_val=0):
    """Encode the minimal sr=60 residual CNF."""
    M1 = [m0]+[fill]*15; M2 = list(M1); M2[0]^=0x80000000; M2[9]^=0x80000000
    s1, W1_pre = precompute_state(M1); s2, W2_pre = precompute_state(M2)

    cnf = CNFBuilder()
    st1 = tuple(cnf.const_word(v) for v in s1)
    st2 = tuple(cnf.const_word(v) for v in s2)

    # W[57] and W[58] are constants
    w1_57 = cnf.const_word(W1_57); w2_57 = cnf.const_word(W2_57)
    w1_58 = cnf.const_word(W1_58)
    w2_58 = cnf.const_word(W2_58) if W2_58 is not None else cnf.free_word("W2_58")

    # W[59] and W[60] are free
    w1_59 = cnf.free_word("W1_59"); w2_59 = cnf.free_word("W2_59")
    w1_60 = cnf.free_word("W1_60"); w2_60 = cnf.free_word("W2_60")

    # Partition: fix MSBs of W1[59]
    if partition_bits > 0:
        for bit in range(partition_bits):
            bit_pos = 31 - bit
            val = (partition_val >> (partition_bits - 1 - bit)) & 1
            if val: cnf.clauses.append([w1_59[bit_pos]])
            else:   cnf.clauses.append([-w1_59[bit_pos]])

    # Schedule tail
    w1_61 = cnf.add_word(cnf.add_word(cnf.sigma1_w(w1_59), cnf.const_word(W1_pre[54])),
                         cnf.add_word(cnf.const_word(sigma0(W1_pre[46])), cnf.const_word(W1_pre[45])))
    w2_61 = cnf.add_word(cnf.add_word(cnf.sigma1_w(w2_59), cnf.const_word(W2_pre[54])),
                         cnf.add_word(cnf.const_word(sigma0(W2_pre[46])), cnf.const_word(W2_pre[45])))
    w1_62 = cnf.add_word(cnf.add_word(cnf.sigma1_w(w1_60), cnf.const_word(W1_pre[55])),
                         cnf.add_word(cnf.const_word(sigma0(W1_pre[47])), cnf.const_word(W1_pre[46])))
    w2_62 = cnf.add_word(cnf.add_word(cnf.sigma1_w(w2_60), cnf.const_word(W2_pre[55])),
                         cnf.add_word(cnf.const_word(sigma0(W2_pre[47])), cnf.const_word(W2_pre[46])))
    w1_63 = cnf.add_word(cnf.add_word(cnf.sigma1_w(w1_61), cnf.const_word(W1_pre[56])),
                         cnf.add_word(cnf.const_word(sigma0(W1_pre[48])), cnf.const_word(W1_pre[47])))
    w2_63 = cnf.add_word(cnf.add_word(cnf.sigma1_w(w2_61), cnf.const_word(W2_pre[56])),
                         cnf.add_word(cnf.const_word(sigma0(W2_pre[48])), cnf.const_word(W2_pre[47])))

    W1s = [w1_57, w1_58, w1_59, w1_60, w1_61, w1_62, w1_63]
    W2s = [w2_57, w2_58, w2_59, w2_60, w2_61, w2_62, w2_63]

    for i in range(7):
        st1 = cnf.sha256_round_correct(st1, K[57+i], W1s[i])
    for i in range(7):
        st2 = cnf.sha256_round_correct(st2, K[57+i], W2s[i])
    for i in range(8):
        cnf.eq_word(st1[i], st2[i])

    return cnf


def solve_one(args):
    m0, fill, W1_57, W2_57, W1_58, W2_58, pbits, pval, timeout = args
    cnf = encode_residual(m0, fill, W1_57, W2_57, W1_58, W2_58, pbits, pval)
    with tempfile.NamedTemporaryFile(suffix='.cnf', delete=False) as f:
        cnf_file = f.name
    cnf.write_dimacs(cnf_file)
    t0 = time.time()
    try:
        r = subprocess.run(['kissat', '-q', cnf_file], capture_output=True, text=True, timeout=timeout)
        elapsed = time.time() - t0
        status = 'SAT' if r.returncode == 10 else 'UNSAT' if r.returncode == 20 else f'rc{r.returncode}'
    except subprocess.TimeoutExpired:
        elapsed = timeout; status = 'TIMEOUT'
    finally:
        try: os.unlink(cnf_file)
        except: pass
    return pval, status, elapsed


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 gpu_to_sat_pipeline.py W1_57 W1_58 [W2_58|free] [timeout] [partition_bits]")
        sys.exit(1)

    W1_57 = int(sys.argv[1], 0)
    W1_58 = int(sys.argv[2], 0)
    W2_58_arg = sys.argv[3] if len(sys.argv) > 3 else 'free'
    timeout = int(sys.argv[4]) if len(sys.argv) > 4 else 3600
    pbits = int(sys.argv[5]) if len(sys.argv) > 5 else 0

    m0 = 0x44b49bc3; fill = 0x80000000
    dw57 = 0xddb49ee1
    W2_57 = (W1_57 - dw57) & MASK
    W2_58 = int(W2_58_arg, 0) if W2_58_arg != 'free' else None

    print(f"GPU→SAT Pipeline")
    print(f"  M[0]=0x{m0:08x}, fill=0x{fill:08x}")
    print(f"  W1[57]=0x{W1_57:08x}, W2[57]=0x{W2_57:08x}")
    print(f"  W1[58]=0x{W1_58:08x}, W2[58]={'FREE' if W2_58 is None else f'0x{W2_58:08x}'}")
    print(f"  Timeout: {timeout}s, Partition bits: {pbits}")

    if pbits == 0:
        # Single solve
        cnf = encode_residual(m0, fill, W1_57, W2_57, W1_58, W2_58)
        nv = cnf.next_var - 1; nc = len(cnf.clauses)
        cf = cnf.stats.get('const_fold', 0); total = sum(cnf.stats.values())
        print(f"  CNF: {nv} vars, {nc} clauses, {cf/total*100:.0f}% const-fold")

        with tempfile.NamedTemporaryFile(suffix='.cnf', delete=False) as f:
            cnf_file = f.name
        cnf.write_dimacs(cnf_file)

        t0 = time.time()
        try:
            r = subprocess.run(['kissat', '-q', cnf_file],
                              capture_output=True, text=True, timeout=timeout)
            elapsed = time.time() - t0
            if r.returncode == 10: print(f"  *** SAT in {elapsed:.1f}s ***")
            elif r.returncode == 20: print(f"  UNSAT in {elapsed:.1f}s")
            else: print(f"  rc={r.returncode} in {elapsed:.1f}s")
        except subprocess.TimeoutExpired:
            print(f"  TIMEOUT at {timeout}s")
        finally:
            os.unlink(cnf_file)
    else:
        # Parallel partition
        n_parts = 2**pbits
        n_workers = min(24, n_parts)
        print(f"  Partitions: {n_parts}, Workers: {n_workers}")

        work = [(m0, fill, W1_57, W2_57, W1_58, W2_58, pbits, pval, timeout)
                for pval in range(n_parts)]

        from collections import Counter
        counts = Counter()
        t0 = time.time()

        with multiprocessing.Pool(n_workers) as pool:
            for i, (pval, status, elapsed) in enumerate(pool.imap_unordered(solve_one, work)):
                counts[status] += 1
                if status == 'SAT':
                    print(f"\n  *** SAT at partition {pval} in {elapsed:.1f}s! ***")
                    pool.terminate(); break
                elif status == 'UNSAT':
                    print(f"  [{i+1}/{n_parts}] UNSAT p={pval} in {elapsed:.1f}s")
                if (i+1) % max(1, n_parts//10) == 0:
                    print(f"  [{i+1}/{n_parts}] {dict(counts)} ({time.time()-t0:.0f}s)")

        print(f"\n  Final: {dict(counts)} in {time.time()-t0:.0f}s")
