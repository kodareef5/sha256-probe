#!/usr/bin/env python3
"""
Script 77: Candidate mutation scan

Searches for da[56]=0 candidates under random M[1..15] fillings,
then samples constant-folded MSB partitions to estimate UNSAT rate.

Usage:
  python3 77_candidate_mutation_scan.py [trials] [max_m0_scan] [samples] [timeout]
"""

import os
import sys
import time
import random
import subprocess
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from importlib import import_module
enc = import_module('13_custom_cnf_encoder')


def find_m0_for_fill(fill_words, max_scan):
    for m0 in range(max_scan):
        M1 = [m0] + fill_words
        M2 = M1.copy()
        M2[0] ^= 0x80000000
        M2[9] ^= 0x80000000

        state1, W1_pre = enc.precompute_state(M1)
        state2, W2_pre = enc.precompute_state(M2)
        if state1[0] == state2[0]:
            return m0, state1, state2, W1_pre, W2_pre
    return None, None, None, None, None


def encode_with_fixed_msb(state1, state2, W1_pre, W2_pre, w1_msb, w2_msb, n_bits=4):
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

    w1_58 = cnf.free_word('W1_58')
    w1_59 = cnf.free_word('W1_59')
    w1_60 = cnf.free_word('W1_60')
    w2_58 = cnf.free_word('W2_58')
    w2_59 = cnf.free_word('W2_59')
    w2_60 = cnf.free_word('W2_60')

    W1_s = [w1_57, w1_58, w1_59, w1_60]
    W2_s = [w2_57, w2_58, w2_59, w2_60]

    w1_61 = cnf.add_word(cnf.add_word(cnf.sigma1_w(W1_s[2]), cnf.const_word(W1_pre[54])),
                         cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[46])), cnf.const_word(W1_pre[45])))
    w2_61 = cnf.add_word(cnf.add_word(cnf.sigma1_w(W2_s[2]), cnf.const_word(W2_pre[54])),
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


def run_kissat(cnf_file, timeout):
    try:
        r = subprocess.run(["kissat", "-q", cnf_file], capture_output=True, text=True, timeout=timeout)
        if r.returncode == 10:
            return "SAT"
        if r.returncode == 20:
            return "UNSAT"
        return "TIMEOUT"
    except subprocess.TimeoutExpired:
        return "TIMEOUT"


def sample_partitions(state1, state2, W1_pre, W2_pre, samples, timeout):
    rng = random.Random(0xC0FFEE)
    work_dir = tempfile.mkdtemp(prefix="cand_scan_")
    n_unsat = n_sat = n_to = 0

    for _ in range(samples):
        w1 = rng.randrange(16)
        w2 = rng.randrange(16)
        cnf = encode_with_fixed_msb(state1, state2, W1_pre, W2_pre, w1, w2, 4)
        f = os.path.join(work_dir, f"c_{w1}_{w2}.cnf")
        cnf.write_dimacs(f)
        status = run_kissat(f, timeout)
        if status == "UNSAT":
            n_unsat += 1
        elif status == "SAT":
            n_sat += 1
        else:
            n_to += 1
        try:
            os.unlink(f)
        except OSError:
            pass

    try:
        os.rmdir(work_dir)
    except OSError:
        pass

    total = max(1, n_unsat + n_sat + n_to)
    return n_sat, n_unsat, n_to, (n_unsat / total) * 100.0


def main():
    trials = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    max_scan = int(sys.argv[2]) if len(sys.argv) > 2 else 1 << 20
    samples = int(sys.argv[3]) if len(sys.argv) > 3 else 16
    timeout = int(sys.argv[4]) if len(sys.argv) > 4 else 20

    rng = random.Random(0xBEEF)

    for t in range(trials):
        fill_words = [rng.getrandbits(32) for _ in range(15)]
        m0, state1, state2, W1_pre, W2_pre = find_m0_for_fill(fill_words, max_scan)
        if m0 is None:
            print(f"Trial {t}: no da56=0 in scan range", flush=True)
            continue

        n_sat, n_unsat, n_to, rate = sample_partitions(state1, state2, W1_pre, W2_pre, samples, timeout)
        print(f"Trial {t}: m0=0x{m0:08x} unsat_rate={rate:.1f}% sat={n_sat} to={n_to}", flush=True)


if __name__ == "__main__":
    main()
