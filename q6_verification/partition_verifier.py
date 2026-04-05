#!/usr/bin/env python3
"""
Script 76: Constant-folded partition verification

- Generates constant-folded sr=60 partitions by fixing MSBs of W1[57].
- Runs Kissat with proof output and verifies UNSAT via drat-trim.
- Cross-checks with CaDiCaL and CryptoMiniSat on the same CNFs.

Usage:
  python3 76_partition_verifier.py [n_bits] [timeout] [n_workers] [limit]
"""

import csv
import os
import sys
import time
import tempfile
import subprocess
import multiprocessing

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from importlib import import_module
enc = import_module('13_custom_cnf_encoder')

DRAT_TRIM = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools', 'drat-trim', 'drat-trim')


def encode_sr60_with_fixed_w57_bits(fixed_msb_value, n_fixed_bits=8):
    M1 = [0x17149975] + [0xffffffff] * 15
    M2 = M1.copy()
    M2[0] ^= 0x80000000
    M2[9] ^= 0x80000000

    state1, W1_pre = enc.precompute_state(M1)
    state2, W2_pre = enc.precompute_state(M2)

    cnf = enc.CNFBuilder()
    s1 = tuple(cnf.const_word(v) for v in state1)
    s2 = tuple(cnf.const_word(v) for v in state2)

    w1_57 = []
    for bit in range(32):
        if bit >= (32 - n_fixed_bits):
            bit_val = bool((fixed_msb_value >> (bit - (32 - n_fixed_bits))) & 1)
            w1_57.append(cnf._const(bit_val))
        else:
            v = cnf.new_var()
            cnf.free_var_names[v] = f"W1_57[{bit}]"
            w1_57.append(v)

    w1_58 = cnf.free_word("W1_58")
    w1_59 = cnf.free_word("W1_59")
    w1_60 = cnf.free_word("W1_60")
    w2_57 = cnf.free_word("W2_57")
    w2_58 = cnf.free_word("W2_58")
    w2_59 = cnf.free_word("W2_59")
    w2_60 = cnf.free_word("W2_60")

    W1_schedule = [w1_57, w1_58, w1_59, w1_60]
    W2_schedule = [w2_57, w2_58, w2_59, w2_60]

    w1_61 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W1_schedule[2]), cnf.const_word(W1_pre[54])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[46])), cnf.const_word(W1_pre[45])))
    w2_61 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W2_schedule[2]), cnf.const_word(W2_pre[54])),
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
        st1 = cnf.sha256_round_correct(st1, enc.K[57 + i], W1_schedule[i])
    st2 = s2
    for i in range(7):
        st2 = cnf.sha256_round_correct(st2, enc.K[57 + i], W2_schedule[i])

    for i in range(8):
        cnf.eq_word(st1[i], st2[i])

    return cnf


def encode_sr60_with_fixed_w57_bits_dual(w1_msb_value, w2_msb_value, n_fixed_bits=4):
    M1 = [0x17149975] + [0xffffffff] * 15
    M2 = M1.copy()
    M2[0] ^= 0x80000000
    M2[9] ^= 0x80000000

    state1, W1_pre = enc.precompute_state(M1)
    state2, W2_pre = enc.precompute_state(M2)

    cnf = enc.CNFBuilder()
    s1 = tuple(cnf.const_word(v) for v in state1)
    s2 = tuple(cnf.const_word(v) for v in state2)

    w1_57 = []
    for bit in range(32):
        if bit >= (32 - n_fixed_bits):
            bit_val = bool((w1_msb_value >> (bit - (32 - n_fixed_bits))) & 1)
            w1_57.append(cnf._const(bit_val))
        else:
            v = cnf.new_var()
            cnf.free_var_names[v] = f"W1_57[{bit}]"
            w1_57.append(v)

    w2_57 = []
    for bit in range(32):
        if bit >= (32 - n_fixed_bits):
            bit_val = bool((w2_msb_value >> (bit - (32 - n_fixed_bits))) & 1)
            w2_57.append(cnf._const(bit_val))
        else:
            v = cnf.new_var()
            cnf.free_var_names[v] = f"W2_57[{bit}]"
            w2_57.append(v)

    w1_58 = cnf.free_word("W1_58")
    w1_59 = cnf.free_word("W1_59")
    w1_60 = cnf.free_word("W1_60")
    w2_58 = cnf.free_word("W2_58")
    w2_59 = cnf.free_word("W2_59")
    w2_60 = cnf.free_word("W2_60")

    W1_schedule = [w1_57, w1_58, w1_59, w1_60]
    W2_schedule = [w2_57, w2_58, w2_59, w2_60]

    w1_61 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W1_schedule[2]), cnf.const_word(W1_pre[54])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[46])), cnf.const_word(W1_pre[45])))
    w2_61 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W2_schedule[2]), cnf.const_word(W2_pre[54])),
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
        st1 = cnf.sha256_round_correct(st1, enc.K[57 + i], W1_schedule[i])
    st2 = s2
    for i in range(7):
        st2 = cnf.sha256_round_correct(st2, enc.K[57 + i], W2_schedule[i])

    for i in range(8):
        cnf.eq_word(st1[i], st2[i])

    return cnf


def run_cmd(cmd, timeout):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return None, "", "TIMEOUT"


def run_kissat_with_proof(cnf_file, proof_file, timeout, seed=None):
    cmd = ["kissat", "-q", "-f"]
    if seed is not None:
        cmd.append(f"--seed={seed}")
    cmd.extend([cnf_file, proof_file])
    rc, out, err = run_cmd(cmd, timeout)
    if rc is None:
        return "TIMEOUT"
    if rc == 10:
        return "SAT"
    if rc == 20:
        return "UNSAT"
    return "ERROR"


def verify_drat(cnf_file, proof_file, timeout):
    if not os.path.exists(DRAT_TRIM):
        return "MISSING"
    rc, out, err = run_cmd([DRAT_TRIM, cnf_file, proof_file], timeout)
    if rc is None:
        return "TIMEOUT"
    return "OK" if rc == 0 else "FAIL"


def run_cadical(cnf_file, timeout, seed=None):
    cmd = ["cadical", "-q"]
    if seed is not None:
        cmd.append(f"--seed={seed}")
    cmd.append(cnf_file)
    rc, out, err = run_cmd(cmd, timeout)
    if rc is None:
        return "TIMEOUT"
    if rc == 10:
        return "SAT"
    if rc == 20:
        return "UNSAT"
    return "ERROR"


def run_cryptominisat(cnf_file, timeout, seed=None):
    cmd = ["cryptominisat5"]
    if seed is not None:
        cmd.append(f"--random={seed}")
    cmd.append(cnf_file)
    rc, out, err = run_cmd(cmd, timeout)
    if rc is None:
        return "TIMEOUT"
    if "s UNSATISFIABLE" in out:
        return "UNSAT"
    if "s SATISFIABLE" in out:
        return "SAT"
    return "ERROR"


def solve_partition(args):
    msb_val, n_bits, timeout, work_dir, dual, seed = args
    if dual:
        mask = (1 << n_bits) - 1
        w1_val = msb_val & mask
        w2_val = msb_val >> n_bits
        cnf = encode_sr60_with_fixed_w57_bits_dual(w1_val, w2_val, n_bits)
    else:
        cnf = encode_sr60_with_fixed_w57_bits(msb_val, n_bits)
    cnf_file = os.path.join(work_dir, f"p_{msb_val:03d}.cnf")
    proof_file = os.path.join(work_dir, f"p_{msb_val:03d}.drat")
    cnf.write_dimacs(cnf_file)

    kissat_status = run_kissat_with_proof(cnf_file, proof_file, timeout, seed=seed)
    drat_status = "SKIP"
    if kissat_status == "UNSAT":
        drat_status = verify_drat(cnf_file, proof_file, timeout)

    cadical_status = run_cadical(cnf_file, timeout, seed=seed)
    cms_status = run_cryptominisat(cnf_file, timeout, seed=seed)

    try:
        os.unlink(cnf_file)
    except OSError:
        pass
    try:
        os.unlink(proof_file)
    except OSError:
        pass

    return {
        "partition": msb_val,
        "kissat": kissat_status,
        "drat": drat_status,
        "cadical": cadical_status,
        "cms": cms_status,
        "seed": seed if seed is not None else "",
    }


def main():
    dual = "--dual" in sys.argv
    partitions = None
    seed = None
    out_csv = None
    args = []
    for a in sys.argv[1:]:
        if a == "--dual":
            continue
        if a.startswith("--partitions="):
            parts = a.split("=", 1)[1].strip()
            if parts:
                partitions = [int(p.strip()) for p in parts.split(",") if p.strip()]
            continue
        if a.startswith("--seed="):
            seed = int(a.split("=", 1)[1])
            continue
        if a.startswith("--out="):
            out_csv = a.split("=", 1)[1]
            continue
        if a.startswith("--"):
            continue
        args.append(a)

    n_bits = int(args[0]) if len(args) > 0 else 8
    timeout = int(args[1]) if len(args) > 1 else 60
    n_workers = int(args[2]) if len(args) > 2 else 4
    limit = int(args[3]) if len(args) > 3 else 0

    n_partitions = 2 ** (2 * n_bits) if dual else 2 ** n_bits
    work_dir = tempfile.mkdtemp(prefix="verify_sr60_")

    if partitions is not None:
        tasks = [(msb, n_bits, timeout, work_dir, dual, seed) for msb in partitions]
    else:
        tasks = [(msb, n_bits, timeout, work_dir, dual, seed) for msb in range(n_partitions)]
        if limit > 0:
            tasks = tasks[:limit]

    if out_csv is None:
        out_csv = os.path.join(os.getcwd(), "verification_results.csv")
    with open(out_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["partition", "kissat", "drat", "cadical", "cms", "seed"])
        writer.writeheader()

        if n_workers <= 1:
            for task in tasks:
                result = solve_partition(task)
                writer.writerow(result)
                f.flush()
                print(result, flush=True)
        else:
            with multiprocessing.Pool(n_workers) as pool:
                for result in pool.imap_unordered(solve_partition, tasks):
                    writer.writerow(result)
                    f.flush()
                    print(result, flush=True)

    print(f"Results written to {out_csv}", flush=True)


if __name__ == "__main__":
    main()
