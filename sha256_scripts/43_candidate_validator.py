#!/usr/bin/env python3
"""
Script 43: Constant-Folded Candidate Validator

For any M[0] candidate, quickly determine if sr=60 is "alive" or "dead"
by running the dual constant-folded 4-bit partition test.

Dead candidate: >80% UNSAT at Level 1 (like 0x17149975 at 88%)
Live candidate: <30% UNSAT at Level 1 (solution space is open)

Usage: python3 43_candidate_validator.py <m0_hex> [timeout_per_cell]
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


def encode_with_fixed_msb(m0, w1_msb, w2_msb, n_bits=4):
    """Encode sr=60 with constant-folded MSBs for a given M[0]."""
    M1 = [m0] + [0xffffffff] * 15
    M2 = M1[:]
    M2[0] ^= 0x80000000
    M2[9] ^= 0x80000000

    state1, W1_pre = enc.precompute_state(M1)
    state2, W2_pre = enc.precompute_state(M2)

    if state1[0] != state2[0]:
        return None  # da[56] != 0

    cnf = enc.CNFBuilder()
    s1 = tuple(cnf.const_word(v) for v in state1)
    s2 = tuple(cnf.const_word(v) for v in state2)

    w1_57 = []
    for bit in range(32):
        if bit >= (32 - n_bits):
            w1_57.append(cnf._const(bool((w1_msb >> (bit - (32 - n_bits))) & 1)))
        else:
            w1_57.append(cnf.new_var())
    w2_57 = []
    for bit in range(32):
        if bit >= (32 - n_bits):
            w2_57.append(cnf._const(bool((w2_msb >> (bit - (32 - n_bits))) & 1)))
        else:
            w2_57.append(cnf.new_var())

    w1_58 = cnf.free_word('a'); w1_59 = cnf.free_word('b'); w1_60 = cnf.free_word('c')
    w2_58 = cnf.free_word('d'); w2_59 = cnf.free_word('e'); w2_60 = cnf.free_word('f')

    w1_free = [w1_57, w1_58, w1_59, w1_60]
    w2_free = [w2_57, w2_58, w2_59, w2_60]

    W1_s = list(w1_free); W2_s = list(w2_free)

    w1_61 = cnf.add_word(cnf.add_word(cnf.sigma1_w(w1_free[2]), cnf.const_word(W1_pre[54])),
                         cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[46])), cnf.const_word(W1_pre[45])))
    w2_61 = cnf.add_word(cnf.add_word(cnf.sigma1_w(w2_free[2]), cnf.const_word(W2_pre[54])),
                         cnf.add_word(cnf.const_word(enc.sigma0_py(W2_pre[46])), cnf.const_word(W2_pre[45])))
    W1_s.append(w1_61); W2_s.append(w2_61)

    w1_62 = cnf.add_word(cnf.add_word(cnf.sigma1_w(W1_s[3]), cnf.const_word(W1_pre[55])),
                         cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[47])), cnf.const_word(W1_pre[46])))
    w2_62 = cnf.add_word(cnf.add_word(cnf.sigma1_w(W2_s[3]), cnf.const_word(W2_pre[55])),
                         cnf.add_word(cnf.const_word(enc.sigma0_py(W2_pre[47])), cnf.const_word(W2_pre[46])))
    w1_63 = cnf.add_word(cnf.add_word(cnf.sigma1_w(W1_s[4]), cnf.const_word(W1_pre[56])),
                         cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[48])), cnf.const_word(W1_pre[47])))
    w2_63 = cnf.add_word(cnf.add_word(cnf.sigma1_w(W2_s[4]), cnf.const_word(W2_pre[56])),
                         cnf.add_word(cnf.const_word(enc.sigma0_py(W2_pre[48])), cnf.const_word(W2_pre[47])))
    W1_s.extend([w1_62, w1_63]); W2_s.extend([w2_62, w2_63])

    st1 = s1
    for i in range(7):
        st1 = cnf.sha256_round_correct(st1, enc.K[57+i], W1_s[i])
    st2 = s2
    for i in range(7):
        st2 = cnf.sha256_round_correct(st2, enc.K[57+i], W2_s[i])

    for i in range(8):
        cnf.eq_word(st1[i], st2[i])

    return cnf


def solve_cell(args):
    """Encode and solve one cell."""
    m0, w1v, w2v, timeout, work_dir = args
    cnf = encode_with_fixed_msb(m0, w1v, w2v, 4)
    if cnf is None:
        return "SKIP", w1v, w2v

    f = os.path.join(work_dir, f"c_{w1v}_{w2v}.cnf")
    cnf.write_dimacs(f)
    try:
        r = subprocess.run(["kissat", "-q", f], capture_output=True, text=True, timeout=timeout)
        os.unlink(f)
        if r.returncode == 10: return "SAT", w1v, w2v
        elif r.returncode == 20: return "UNSAT", w1v, w2v
        else: return "TO", w1v, w2v
    except:
        try: os.unlink(f)
        except: pass
        return "TO", w1v, w2v


def validate_candidate(m0, timeout_per=30, n_workers=16):
    """Run Level 1 dual-MSB validation on a candidate."""
    work_dir = tempfile.mkdtemp(prefix=f"val_{m0:08x}_")
    tasks = [(m0, w1, w2, timeout_per, work_dir) for w1 in range(16) for w2 in range(16)]

    n_sat = n_unsat = n_to = 0
    t0 = time.time()

    with multiprocessing.Pool(n_workers) as pool:
        for status, w1v, w2v in pool.imap_unordered(solve_cell, tasks):
            if status == "SAT":
                n_sat += 1
                print(f"  [!!!] SAT at W1={w1v} W2={w2v}!", flush=True)
                pool.terminate()
                break
            elif status == "UNSAT":
                n_unsat += 1
            else:
                n_to += 1

    shutil.rmtree(work_dir, ignore_errors=True)
    elapsed = time.time() - t0
    total = n_sat + n_unsat + n_to

    unsat_rate = n_unsat / max(1, total) * 100
    return n_sat, n_unsat, n_to, unsat_rate, elapsed


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 43_candidate_validator.py <m0_hex> [timeout]", flush=True)
        print("  Validates an M[0] candidate for sr=60 viability.", flush=True)
        print("  Low UNSAT rate (<30%) = alive. High (>80%) = dead.", flush=True)
        # Default: validate the paper's candidate
        candidates = [0x17149975]
    else:
        candidates = [int(sys.argv[1], 16)]

    timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 30

    for m0 in candidates:
        print(f"\n{'='*60}", flush=True)
        print(f"Validating M[0] = 0x{m0:08x}", flush=True)
        print(f"  Timeout per cell: {timeout}s", flush=True)
        print(f"{'='*60}", flush=True)

        n_sat, n_unsat, n_to, rate, elapsed = validate_candidate(m0, timeout)

        print(f"\n  SAT: {n_sat}, UNSAT: {n_unsat}, TIMEOUT: {n_to}", flush=True)
        print(f"  UNSAT rate: {rate:.0f}%", flush=True)
        print(f"  Time: {elapsed:.0f}s", flush=True)

        if n_sat > 0:
            print(f"  [!!!] CANDIDATE IS SAT — sr=60 collision exists!", flush=True)
        elif rate > 80:
            print(f"  DEAD — {rate:.0f}% UNSAT, candidate cannot achieve sr=60.", flush=True)
        elif rate > 50:
            print(f"  LIKELY DEAD — {rate:.0f}% UNSAT, most of space is empty.", flush=True)
        elif rate > 20:
            print(f"  MAYBE ALIVE — {rate:.0f}% UNSAT, worth investigating.", flush=True)
        else:
            print(f"  ALIVE — only {rate:.0f}% UNSAT, solution space is open!", flush=True)
            print(f"  [!!!] This is a GOLDEN CANDIDATE for sr=60!", flush=True)


if __name__ == "__main__":
    main()
