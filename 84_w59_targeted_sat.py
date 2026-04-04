#!/usr/bin/env python3
"""
Script 84: W[59]-Targeted SAT Partitioning

Instead of folding W[57] bits (standard approach), fold W[59] bits.
This directly controls sigma1(W[59]), which determines dW[61] — the
critical bottleneck identified in the differential analysis.

Strategy:
1. Fix top n bits of BOTH W1[59] and W2[59]
2. For each (w1_msb, w2_msb) pair, encode sr=60 with constant folding
3. Run Kissat to test SAT/UNSAT
4. Report which W[59] partitions are easiest (fastest SAT or UNSAT)

This explores a fundamentally different partition of the search space
than the W[57]-based approach, targeting the dW[61] bottleneck directly.
"""
import sys, os, subprocess, tempfile, time, csv

sys.path.insert(0, os.path.dirname(__file__) or '.')
from importlib import import_module
enc = import_module("13_custom_cnf_encoder")


def encode_sr60_w59_folded(w1_59_msb, w2_59_msb, n_bits=4, m0=0x17149975, fill=0xffffffff):
    """
    Encode sr=60 with W1[59] and W2[59] top bits fixed.
    All other free words (W[57], W[58], W[60]) remain fully free.
    """
    M1 = [m0] + [fill] * 15
    M2 = list(M1); M2[0] ^= 0x80000000; M2[9] ^= 0x80000000

    state1, W1_pre = enc.precompute_state(M1)
    state2, W2_pre = enc.precompute_state(M2)

    cnf = enc.CNFBuilder()
    s1 = tuple(cnf.const_word(v) for v in state1)
    s2 = tuple(cnf.const_word(v) for v in state2)

    # W[57], W[58] fully free
    w1_57 = cnf.free_word("W1_57")
    w1_58 = cnf.free_word("W1_58")
    w2_57 = cnf.free_word("W2_57")
    w2_58 = cnf.free_word("W2_58")

    # W[59] with top n_bits fixed
    w1_59 = []
    for bit in range(32):
        if bit >= (32 - n_bits):
            bit_val = bool((w1_59_msb >> (bit - (32 - n_bits))) & 1)
            w1_59.append(cnf._const(bit_val))
        else:
            v = cnf.new_var()
            cnf.free_var_names[v] = f"W1_59[{bit}]"
            w1_59.append(v)

    w2_59 = []
    for bit in range(32):
        if bit >= (32 - n_bits):
            bit_val = bool((w2_59_msb >> (bit - (32 - n_bits))) & 1)
            w2_59.append(cnf._const(bit_val))
        else:
            v = cnf.new_var()
            cnf.free_var_names[v] = f"W2_59[{bit}]"
            w2_59.append(v)

    # W[60] fully free
    w1_60 = cnf.free_word("W1_60")
    w2_60 = cnf.free_word("W2_60")

    W1_schedule = [w1_57, w1_58, w1_59, w1_60]
    W2_schedule = [w2_57, w2_58, w2_59, w2_60]

    # W[61] = sigma1(W[59]) + W_pre[54] + sigma0(W_pre[46]) + W_pre[45]
    w1_61 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_59), cnf.const_word(W1_pre[54])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[46])), cnf.const_word(W1_pre[45])))
    w2_61 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_59), cnf.const_word(W2_pre[54])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W2_pre[46])), cnf.const_word(W2_pre[45])))
    W1_schedule.append(w1_61)
    W2_schedule.append(w2_61)

    # W[62] = sigma1(W[60]) + W_pre[55] + sigma0(W_pre[47]) + W_pre[46]
    w1_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_60), cnf.const_word(W1_pre[55])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[47])), cnf.const_word(W1_pre[46])))
    w2_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_60), cnf.const_word(W2_pre[55])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W2_pre[47])), cnf.const_word(W2_pre[46])))

    # W[63] = sigma1(W[61]) + W_pre[56] + sigma0(W_pre[48]) + W_pre[47]
    w1_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_61), cnf.const_word(W1_pre[56])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[48])), cnf.const_word(W1_pre[47])))
    w2_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_61), cnf.const_word(W2_pre[56])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W2_pre[48])), cnf.const_word(W2_pre[47])))

    W1_schedule.extend([w1_62, w1_63])
    W2_schedule.extend([w2_62, w2_63])

    # 7 rounds for both messages
    st1 = s1
    for i in range(7):
        st1 = cnf.sha256_round_correct(st1, enc.K[57 + i], W1_schedule[i])
    st2 = s2
    for i in range(7):
        st2 = cnf.sha256_round_correct(st2, enc.K[57 + i], W2_schedule[i])

    for i in range(8):
        cnf.eq_word(st1[i], st2[i])

    return cnf


def solve_partition(w1_msb, w2_msb, n_bits, timeout):
    """Encode and solve one partition."""
    cnf = encode_sr60_w59_folded(w1_msb, w2_msb, n_bits)

    with tempfile.TemporaryDirectory() as td:
        cnf_file = os.path.join(td, "partition.cnf")
        n_vars, n_clauses = cnf.write_dimacs(cnf_file)

        t0 = time.time()
        try:
            result = subprocess.run(
                ["kissat", "-q", cnf_file],
                capture_output=True, timeout=timeout)
            elapsed = time.time() - t0

            if result.returncode == 10:
                return "SAT", elapsed, n_vars, n_clauses
            elif result.returncode == 20:
                return "UNSAT", elapsed, n_vars, n_clauses
            else:
                return "UNKNOWN", elapsed, n_vars, n_clauses
        except subprocess.TimeoutExpired:
            return "TIMEOUT", timeout, n_vars, n_clauses


if __name__ == "__main__":
    n_bits = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 60
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 0

    n_partitions = (1 << n_bits) ** 2  # dual grid
    print(f"W[59]-Targeted SAT Partitioning")
    print(f"  n_bits={n_bits}, timeout={timeout}s, partitions={n_partitions}")
    print(f"  Fixing top {n_bits} bits of BOTH W1[59] and W2[59]")
    print()

    results = {"SAT": 0, "UNSAT": 0, "TIMEOUT": 0, "UNKNOWN": 0}
    out_csv = f"results/w59_targeted_{n_bits}bit.csv"
    os.makedirs("results", exist_ok=True)

    with open(out_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["w1_msb", "w2_msb", "result", "time", "vars", "clauses"])
        writer.writeheader()

        count = 0
        for w1_msb in range(1 << n_bits):
            for w2_msb in range(1 << n_bits):
                if limit > 0 and count >= limit:
                    break

                status, elapsed, n_vars, n_clauses = solve_partition(w1_msb, w2_msb, n_bits, timeout)
                results[status] += 1
                count += 1

                row = {"w1_msb": w1_msb, "w2_msb": w2_msb, "result": status,
                       "time": f"{elapsed:.1f}", "vars": n_vars, "clauses": n_clauses}
                writer.writerow(row)
                f.flush()

                marker = ""
                if status == "SAT":
                    marker = " *** COLLISION! ***"
                elif status == "UNSAT" and elapsed < 5:
                    marker = " (fast)"

                print(f"  [{count}/{n_partitions if limit==0 else limit}] "
                      f"W1[59]_msb={w1_msb:0{n_bits}b} W2[59]_msb={w2_msb:0{n_bits}b}: "
                      f"{status} in {elapsed:.1f}s ({n_vars} vars, {n_clauses} cls){marker}",
                      flush=True)

            if limit > 0 and count >= limit:
                break

    print(f"\nSummary: {results}")
    print(f"Results: {out_csv}")
