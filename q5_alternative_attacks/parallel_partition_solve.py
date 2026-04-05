#!/usr/bin/env python3
"""
parallel_partition_solve.py — Parallel partition solver for constrained sr=60

Takes the da57=0 constraint (which we proved is the ONLY viable strategy)
and further partitions the search by fixing bits of W1[58].

Each partition is an independent SAT problem that can run on its own core.
If ANY partition is SAT → collision found.
If ALL are UNSAT → proven impossible for this candidate.

This is cube-and-conquer at the problem level, not the solver level.

Usage: python3 parallel_partition_solve.py [m0] [fill] [n_partition_bits] [timeout]
"""

import sys, os, time, subprocess, tempfile, multiprocessing
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from lib.sha256 import *
from lib.cnf_encoder import CNFBuilder


def encode_partition(m0, fill, dw57, partition_bits, partition_val, timeout):
    """Encode and solve one partition of the da57=0 constrained sr=60 problem.

    Fixes the top `partition_bits` bits of W1[58] to `partition_val`.
    Returns (partition_val, status, elapsed).
    """
    M1 = [m0] + [fill]*15
    M2 = list(M1); M2[0] ^= 0x80000000; M2[9] ^= 0x80000000
    s1, W1_pre = precompute_state(M1)
    s2, W2_pre = precompute_state(M2)

    cnf = CNFBuilder()
    st1 = tuple(cnf.const_word(v) for v in s1)
    st2 = tuple(cnf.const_word(v) for v in s2)

    w1_free = [cnf.free_word(f"W1_{57+i}") for i in range(4)]
    w2_free = [cnf.free_word(f"W2_{57+i}") for i in range(4)]

    # Constraint 1: da57=0 via dW57
    target = cnf.add_word(w2_free[0], cnf.const_word(dw57))
    cnf.eq_word(w1_free[0], target)

    # Constraint 2: fix top bits of W1[58]
    for bit in range(partition_bits):
        bit_pos = 31 - bit  # MSB first
        val = (partition_val >> (partition_bits - 1 - bit)) & 1
        if val:
            cnf.clauses.append([w1_free[1][bit_pos]])
        else:
            cnf.clauses.append([-w1_free[1][bit_pos]])

    # Build schedule tail
    w1_61 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_free[2]), cnf.const_word(W1_pre[54])),
        cnf.add_word(cnf.const_word(sigma0(W1_pre[46])), cnf.const_word(W1_pre[45])))
    w2_61 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_free[2]), cnf.const_word(W2_pre[54])),
        cnf.add_word(cnf.const_word(sigma0(W2_pre[46])), cnf.const_word(W2_pre[45])))
    w1_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_free[3]), cnf.const_word(W1_pre[55])),
        cnf.add_word(cnf.const_word(sigma0(W1_pre[47])), cnf.const_word(W1_pre[46])))
    w2_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_free[3]), cnf.const_word(W2_pre[55])),
        cnf.add_word(cnf.const_word(sigma0(W2_pre[47])), cnf.const_word(W2_pre[46])))
    w1_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_61), cnf.const_word(W1_pre[56])),
        cnf.add_word(cnf.const_word(sigma0(W1_pre[48])), cnf.const_word(W1_pre[47])))
    w2_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_61), cnf.const_word(W2_pre[56])),
        cnf.add_word(cnf.const_word(sigma0(W2_pre[48])), cnf.const_word(W2_pre[47])))

    W1_sched = list(w1_free) + [w1_61, w1_62, w1_63]
    W2_sched = list(w2_free) + [w2_61, w2_62, w2_63]

    for i in range(7):
        st1 = cnf.sha256_round_correct(st1, K[57+i], W1_sched[i])
    for i in range(7):
        st2 = cnf.sha256_round_correct(st2, K[57+i], W2_sched[i])
    for i in range(8):
        cnf.eq_word(st1[i], st2[i])

    # Write and solve
    with tempfile.NamedTemporaryFile(suffix='.cnf', delete=False) as f:
        cnf_file = f.name
    cnf.write_dimacs(cnf_file)

    t0 = time.time()
    try:
        r = subprocess.run(['kissat', '-q', cnf_file],
                          capture_output=True, text=True, timeout=timeout)
        elapsed = time.time() - t0
        if r.returncode == 10:
            status = 'SAT'
        elif r.returncode == 20:
            status = 'UNSAT'
        else:
            status = f'rc{r.returncode}'
    except subprocess.TimeoutExpired:
        elapsed = timeout
        status = 'TIMEOUT'
    finally:
        try:
            os.unlink(cnf_file)
        except:
            pass

    return partition_val, status, elapsed


def solve_worker(args):
    """Worker for multiprocessing pool."""
    return encode_partition(*args)


def main():
    m0 = int(sys.argv[1], 0) if len(sys.argv) > 1 else 0x44b49bc3
    fill = int(sys.argv[2], 0) if len(sys.argv) > 2 else 0x80000000
    n_bits = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    timeout = int(sys.argv[4]) if len(sys.argv) > 4 else 600
    n_workers = int(sys.argv[5]) if len(sys.argv) > 5 else min(24, 2**n_bits)

    # Compute dW57 for da57=0
    M1 = [m0]+[fill]*15; M2 = list(M1); M2[0]^=0x80000000; M2[9]^=0x80000000
    s1, W1 = precompute_state(M1); s2, W2 = precompute_state(M2)
    d_h56=(s1[7]-s2[7])&MASK; d_Sig1=(Sigma1(s1[4])-Sigma1(s2[4]))&MASK
    d_Ch=(Ch(s1[4],s1[5],s1[6])-Ch(s2[4],s2[5],s2[6]))&MASK
    C_T1=(d_h56+d_Sig1+d_Ch)&MASK
    d_Sig0=(Sigma0(s1[0])-Sigma0(s2[0]))&MASK
    d_Maj=(Maj(s1[0],s1[1],s1[2])-Maj(s2[0],s2[1],s2[2]))&MASK
    C_T2=(d_Sig0+d_Maj)&MASK
    dw57=(-(C_T1+C_T2))&MASK

    n_partitions = 2 ** n_bits
    print(f"Parallel Partition Solver: da57=0 constrained sr=60")
    print(f"  M[0]=0x{m0:08x}, fill=0x{fill:08x}")
    print(f"  dW57=0x{dw57:08x} (da57=0 constraint)")
    print(f"  Partitions: {n_partitions} ({n_bits} bits of W1[58] MSBs)")
    print(f"  Workers: {n_workers}, Timeout: {timeout}s per partition")
    print(f"  Total compute: up to {n_partitions * timeout / 3600:.1f} CPU-hours")
    print(f"", flush=True)

    # Build work items
    work = [(m0, fill, dw57, n_bits, pval, timeout)
            for pval in range(n_partitions)]

    t0 = time.time()
    sat_found = False
    n_unsat = 0
    n_timeout = 0

    with multiprocessing.Pool(n_workers) as pool:
        for pval, status, elapsed in pool.imap_unordered(solve_worker, work):
            total_elapsed = time.time() - t0
            print(f"  [{pval:>{len(str(n_partitions-1))}d}/{n_partitions}] "
                  f"{status:>7s} in {elapsed:>7.1f}s  "
                  f"(wall: {total_elapsed:.0f}s)", flush=True)
            if status == 'SAT':
                sat_found = True
                print(f"\n  *** SAT FOUND at partition {pval}! ***", flush=True)
                pool.terminate()
                break
            elif status == 'UNSAT':
                n_unsat += 1
            else:
                n_timeout += 1

    total = time.time() - t0
    print(f"\n{'='*60}")
    print(f"Results: {n_unsat} UNSAT, {n_timeout} TIMEOUT, "
          f"{'SAT FOUND!' if sat_found else 'no SAT'}")
    print(f"Wall time: {total:.1f}s ({total/3600:.2f}h)")
    if n_unsat == n_partitions:
        print(f"ALL {n_partitions} partitions UNSAT → da57=0 is PROVEN UNSAT")
    elif not sat_found and n_timeout > 0:
        print(f"{n_timeout} partitions timed out — inconclusive")


if __name__ == "__main__":
    main()
