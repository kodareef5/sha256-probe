#!/usr/bin/env python3
"""
timeout_analysis.py — Distinguish "needs more time" from "truly UNSAT"

When all partitions TIMEOUT, we can't distinguish between:
  A) The problem is SAT but needs more time per partition
  B) The problem is UNSAT and would timeout forever

Key diagnostic: if the problem is SAT, fixing more bits should make
SOME partitions faster (the ones containing the solution) and SOME
harder (the ones not containing it). We'd see a SPREAD in solve times
and some early UNSAT results.

If the problem is UNSAT, fixing more bits should make ALL partitions
faster (smaller subproblems → faster UNSAT proofs). We'd see uniform
speedup and eventually all UNSAT.

Test: run with very short timeouts (30s, 60s, 120s) and many partitions
(10-12 bits = 1024-4096 subproblems). Check whether ANY resolve as UNSAT.
Even a single UNSAT in 120s would be informative — it proves that part
of the search space is provably empty.
"""

import sys, os, time, subprocess, tempfile, multiprocessing
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from lib.sha256 import *
from lib.cnf_encoder import CNFBuilder


def make_partition_cnf(m0, fill, dw57, n_bits, pval):
    """Generate a partition CNF (same as parallel_partition_solve.py)."""
    M1 = [m0]+[fill]*15; M2 = list(M1); M2[0]^=0x80000000; M2[9]^=0x80000000
    s1, W1_pre = precompute_state(M1); s2, W2_pre = precompute_state(M2)

    cnf = CNFBuilder()
    st1 = tuple(cnf.const_word(v) for v in s1)
    st2 = tuple(cnf.const_word(v) for v in s2)
    w1_free = [cnf.free_word(f"W1_{57+i}") for i in range(4)]
    w2_free = [cnf.free_word(f"W2_{57+i}") for i in range(4)]

    # da57=0
    cnf.eq_word(w1_free[0], cnf.add_word(w2_free[0], cnf.const_word(dw57)))

    # Fix MSB bits of W1[58]
    for bit in range(n_bits):
        bit_pos = 31 - bit
        val = (pval >> (n_bits - 1 - bit)) & 1
        if val: cnf.clauses.append([w1_free[1][bit_pos]])
        else:   cnf.clauses.append([-w1_free[1][bit_pos]])

    # Schedule tail
    w1_61 = cnf.add_word(cnf.add_word(cnf.sigma1_w(w1_free[2]),cnf.const_word(W1_pre[54])),
                         cnf.add_word(cnf.const_word(sigma0(W1_pre[46])),cnf.const_word(W1_pre[45])))
    w2_61 = cnf.add_word(cnf.add_word(cnf.sigma1_w(w2_free[2]),cnf.const_word(W2_pre[54])),
                         cnf.add_word(cnf.const_word(sigma0(W2_pre[46])),cnf.const_word(W2_pre[45])))
    w1_62 = cnf.add_word(cnf.add_word(cnf.sigma1_w(w1_free[3]),cnf.const_word(W1_pre[55])),
                         cnf.add_word(cnf.const_word(sigma0(W1_pre[47])),cnf.const_word(W1_pre[46])))
    w2_62 = cnf.add_word(cnf.add_word(cnf.sigma1_w(w2_free[3]),cnf.const_word(W2_pre[55])),
                         cnf.add_word(cnf.const_word(sigma0(W2_pre[47])),cnf.const_word(W2_pre[46])))
    w1_63 = cnf.add_word(cnf.add_word(cnf.sigma1_w(w1_61),cnf.const_word(W1_pre[56])),
                         cnf.add_word(cnf.const_word(sigma0(W1_pre[48])),cnf.const_word(W1_pre[47])))
    w2_63 = cnf.add_word(cnf.add_word(cnf.sigma1_w(w2_61),cnf.const_word(W2_pre[56])),
                         cnf.add_word(cnf.const_word(sigma0(W2_pre[48])),cnf.const_word(W2_pre[47])))

    W1s = list(w1_free)+[w1_61,w1_62,w1_63]
    W2s = list(w2_free)+[w2_61,w2_62,w2_63]
    for i in range(7):
        st1 = cnf.sha256_round_correct(st1, K[57+i], W1s[i])
    for i in range(7):
        st2 = cnf.sha256_round_correct(st2, K[57+i], W2s[i])
    for i in range(8):
        cnf.eq_word(st1[i], st2[i])

    return cnf


def test_partition(args):
    m0, fill, dw57, n_bits, pval, timeout = args
    cnf = make_partition_cnf(m0, fill, dw57, n_bits, pval)
    with tempfile.NamedTemporaryFile(suffix='.cnf', delete=False) as f:
        cnf_file = f.name
    cnf.write_dimacs(cnf_file)
    t0 = time.time()
    try:
        r = subprocess.run(['kissat','-q',cnf_file], capture_output=True, text=True, timeout=timeout)
        elapsed = time.time()-t0
        status = 'SAT' if r.returncode==10 else 'UNSAT' if r.returncode==20 else f'rc{r.returncode}'
    except subprocess.TimeoutExpired:
        elapsed = timeout; status = 'TIMEOUT'
    finally:
        try: os.unlink(cnf_file)
        except: pass
    return pval, status, elapsed


if __name__ == "__main__":
    m0 = 0x44b49bc3; fill = 0x80000000

    M1=[m0]+[fill]*15; M2=list(M1); M2[0]^=0x80000000; M2[9]^=0x80000000
    s1,W1=precompute_state(M1); s2,W2=precompute_state(M2)
    d_h56=(s1[7]-s2[7])&MASK; d_Sig1=(Sigma1(s1[4])-Sigma1(s2[4]))&MASK
    d_Ch=(Ch(s1[4],s1[5],s1[6])-Ch(s2[4],s2[5],s2[6]))&MASK; C_T1=(d_h56+d_Sig1+d_Ch)&MASK
    d_Sig0=(Sigma0(s1[0])-Sigma0(s2[0]))&MASK; d_Maj=(Maj(s1[0],s1[1],s1[2])-Maj(s2[0],s2[1],s2[2]))&MASK
    C_T2=(d_Sig0+d_Maj)&MASK; dw57=(-(C_T1+C_T2))&MASK

    # Test: 10-bit partition (1024 subproblems) with 60s timeout
    # This uses all 24 cores efficiently
    n_bits = 10
    timeout = 60
    n_parts = 2**n_bits
    n_workers = 22  # leave 2 cores for system

    print(f"Timeout Diagnostic: {n_parts} partitions × {timeout}s, {n_workers} workers")
    print(f"Looking for ANY UNSAT results (proves part of space is empty)")
    print(f"", flush=True)

    work = [(m0, fill, dw57, n_bits, pval, timeout) for pval in range(n_parts)]

    from collections import Counter
    counts = Counter()
    t0 = time.time()

    with multiprocessing.Pool(n_workers) as pool:
        for i, (pval, status, elapsed) in enumerate(pool.imap_unordered(test_partition, work)):
            counts[status] += 1
            if status == 'SAT':
                print(f"\n*** SAT at partition {pval} in {elapsed:.1f}s! ***", flush=True)
                pool.terminate(); break
            elif status == 'UNSAT':
                print(f"  [{i+1}/{n_parts}] UNSAT at p={pval} in {elapsed:.1f}s!", flush=True)
            if (i+1) % 100 == 0:
                wall = time.time()-t0
                print(f"  [{i+1}/{n_parts}] {dict(counts)} wall={wall:.0f}s", flush=True)

    wall = time.time()-t0
    print(f"\nDone: {dict(counts)} in {wall:.0f}s")
    if counts['UNSAT'] > 0:
        rate = counts['UNSAT']/(counts['UNSAT']+counts['TIMEOUT'])
        print(f"UNSAT rate: {rate:.1%} — some search space is provably empty!")
    else:
        print(f"All timeout — problem is too hard even with {n_bits} fixed bits at {timeout}s")
