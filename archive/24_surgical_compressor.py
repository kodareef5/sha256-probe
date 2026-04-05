#!/usr/bin/env python3
"""
Script 24: Surgical Compressor Clauses

Round 2 showed: 28K support clauses = 1.33x speedup at sr=59, but
timeout at k=4 (overhead dominates at the phase transition).

Fix: Only add support clauses to the FINAL ripple-carry addition
in add5_csa — the deepest, longest dependency chain. Skip the
parallel CSA layers (they're already shallow).

Expected: ~3K extra clauses (vs 28K), targeting exactly the carry
chain bottleneck without blowing up per-conflict cost.
"""

import sys
import os
import time
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from importlib import import_module
enc = import_module('13_custom_cnf_encoder')


class SurgicalCNFBuilder(enc.CNFBuilder):
    """CNF builder with support clauses ONLY for tagged additions."""

    def __init__(self):
        super().__init__()
        self.stats['support'] = 0
        self._support_mode = False  # Only add support when this is True

    def full_adder(self, a, b, cin):
        """Full adder with optional support clauses."""
        self.stats['fa'] += 1
        t = self.xor2(a, b)
        s = self.xor2(t, cin)
        cout = self.maj(a, b, cin)

        if self._support_mode:
            n_known = sum(1 for x in [a, b, cin] if self._is_known(x))
            if n_known < 2 and not (self._is_known(s) and self._is_known(cout)):
                # Add targeted support clauses
                if not self._is_known(s) and not self._is_known(cout):
                    for x in [a, b, cin]:
                        if not self._is_known(x):
                            self.clauses.append([s, cout, -x])
                            self.clauses.append([-s, -cout, x])
                            self.stats['support'] += 2

        return s, cout

    def add_word_supported(self, A, B):
        """Ripple-carry addition WITH support clauses."""
        old_mode = self._support_mode
        self._support_mode = True
        result = self.add_word(A, B)
        self._support_mode = old_mode
        return result

    def add5_csa_surgical(self, A, B, C, D, E):
        """
        CSA tree with support clauses ONLY on the final ripple-carry.

        CSA layers: parallel, shallow — no support needed.
        Final add_word: sequential carry chain — support clauses help.
        """
        # CSA layers: no support (already shallow)
        s1, c1 = self.csa_layer(A, B, C)
        s2, c2 = self.csa_layer(s1, D, E)
        s3, c3 = self.csa_layer(c1, s2, c2)

        # Final ripple-carry: WITH support clauses
        return self.add_word_supported(s3, c3)

    def sha256_round_correct(self, state, Ki, Wi):
        """Round function using surgical CSA."""
        a, b, c, d, e, f, g, h = state
        K_word = self.const_word(Ki)

        sig1 = self.Sigma1(e)
        ch = self.Ch(e, f, g)

        # T1 via surgical CSA (support on final ripple only)
        t1 = self.add5_csa_surgical(h, sig1, ch, K_word, Wi)

        sig0 = self.Sigma0(a)
        mj = self.Maj(a, b, c)
        # T2: also add support to this ripple-carry
        t2 = self.add_word_supported(sig0, mj)

        # a_new and e_new: support these too (final outputs)
        a_new = self.add_word_supported(t1, t2)
        e_new = self.add_word_supported(d, t1)

        return (a_new, a, b, c, e_new, e, f, g)


def encode_surgical(mode="sr59", k_bits=0):
    """Encode with surgical support clauses."""
    M1 = [0x17149975] + [0xffffffff] * 15
    M2 = M1.copy()
    M2[0] ^= 0x80000000
    M2[9] ^= 0x80000000

    state1, W1_pre = enc.precompute_state(M1)
    state2, W2_pre = enc.precompute_state(M2)

    n_free = 5 if mode == "sr59" else 4
    cnf = SurgicalCNFBuilder()

    s1 = tuple(cnf.const_word(v) for v in state1)
    s2 = tuple(cnf.const_word(v) for v in state2)

    w1_free = [cnf.free_word(f"W1_{57+i}") for i in range(n_free)]
    w2_free = [cnf.free_word(f"W2_{57+i}") for i in range(n_free)]

    W1_schedule = list(w1_free)
    W2_schedule = list(w2_free)

    if mode == "sr60":
        w1_61 = cnf.add_word(
            cnf.add_word(cnf.sigma1_w(w1_free[2]), cnf.const_word(W1_pre[54])),
            cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[46])), cnf.const_word(W1_pre[45])))
        w2_61 = cnf.add_word(
            cnf.add_word(cnf.sigma1_w(w2_free[2]), cnf.const_word(W2_pre[54])),
            cnf.add_word(cnf.const_word(enc.sigma0_py(W2_pre[46])), cnf.const_word(W2_pre[45])))
        W1_schedule.append(w1_61)
        W2_schedule.append(w2_61)

    w60_idx = 3
    w1_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W1_schedule[w60_idx]), cnf.const_word(W1_pre[55])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[47])), cnf.const_word(W1_pre[46])))
    w2_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W2_schedule[w60_idx]), cnf.const_word(W2_pre[55])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W2_pre[47])), cnf.const_word(W2_pre[46])))
    w61_idx = 4
    w1_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W1_schedule[w61_idx]), cnf.const_word(W1_pre[56])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[48])), cnf.const_word(W1_pre[47])))
    w2_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W2_schedule[w61_idx]), cnf.const_word(W2_pre[56])),
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

    # Optional k-bit schedule compliance
    if k_bits > 0 and mode == "sr59":
        w1_61_sched = cnf.add_word(
            cnf.add_word(cnf.sigma1_w(w1_free[2]), cnf.const_word(W1_pre[54])),
            cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[46])), cnf.const_word(W1_pre[45])))
        w2_61_sched = cnf.add_word(
            cnf.add_word(cnf.sigma1_w(w2_free[2]), cnf.const_word(W2_pre[54])),
            cnf.add_word(cnf.const_word(enc.sigma0_py(W2_pre[46])), cnf.const_word(W2_pre[45])))
        for bit in range(k_bits):
            for a, b in [(w1_free[4][bit], w1_61_sched[bit]),
                         (w2_free[4][bit], w2_61_sched[bit])]:
                if cnf._is_known(a) and cnf._is_known(b):
                    if cnf._get_val(a) != cnf._get_val(b):
                        cnf.clauses.append([])
                elif cnf._is_known(a):
                    cnf.clauses.append([b] if cnf._get_val(a) else [-b])
                elif cnf._is_known(b):
                    cnf.clauses.append([a] if cnf._get_val(b) else [-a])
                else:
                    cnf.clauses.append([-a, b])
                    cnf.clauses.append([a, -b])

    return cnf


def main():
    timeout = int(sys.argv[1]) if len(sys.argv) > 1 else 600

    print("=" * 60, flush=True)
    print("Surgical Compressor Clauses", flush=True)
    print("=" * 60, flush=True)

    tests = [
        ("sr59", 0, 300, "sr=59 baseline"),
        ("sr59", 3, 300, "k=3 (baseline: 109s)"),
        ("sr59", 4, timeout, "k=4 (baseline: 1776s)"),
    ]

    for mode, k, to, label in tests:
        cnf = encode_surgical(mode, k_bits=k)
        nv = cnf.next_var - 1
        nc = len(cnf.clauses)
        support = cnf.stats['support']

        cnf_file = f"/tmp/surgical_{mode}_k{k}.cnf"
        cnf.write_dimacs(cnf_file)

        print(f"\n{label}:", flush=True)
        print(f"  {nv} vars, {nc} clauses, {support} support clauses", flush=True)

        t0 = time.time()
        r = subprocess.run(["timeout", str(to), "kissat", "-q", cnf_file],
                           capture_output=True, text=True, timeout=to + 30)
        elapsed = time.time() - t0

        if r.returncode == 10:
            print(f"  [+] SAT in {elapsed:.1f}s", flush=True)
        elif r.returncode == 20:
            print(f"  [-] UNSAT in {elapsed:.1f}s", flush=True)
        else:
            print(f"  [!] TIMEOUT after {elapsed:.1f}s", flush=True)


if __name__ == "__main__":
    main()
