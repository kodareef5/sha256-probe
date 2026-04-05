#!/usr/bin/env python3
"""
Script 19: Compressor Support Clauses

Adds redundant clauses that directly couple full-adder sum and carry
outputs to their inputs, bypassing the intermediate XOR variable.

Current encoding:
  t = XOR(a, b)       [4 clauses, 1 var]
  sum = XOR(t, cin)    [4 clauses, 1 var]
  cout = MAJ(a,b,cin)  [6 clauses, 1 var]
  Total: 14 clauses, 3 vars per FA — but sum/cout have no direct link

Support clauses (redundant but accelerate backward propagation):
  If sum=0 and cout=0: none of {a,b,cin} true     → (-s ∨ c ∨ -a)(-s ∨ c ∨ -b)(-s ∨ c ∨ -cin)
  If sum=0 and cout=1: all of {a,b,cin} true       → (-s ∨ -c ∨ a)(-s ∨ -c ∨ b)(-s ∨ -c ∨ cin)
  Wait — let me derive these properly.

For a full adder (a, b, cin) → (sum, cout):
  sum = a ⊕ b ⊕ cin
  cout = MAJ(a, b, cin)

The truth table has 8 rows. Key derived implications:

When we know sum AND cout, we can deduce input constraints:
  sum=0,cout=0 → a=b=cin=0:       clause: (sum ∨ cout ∨ ¬a), (sum ∨ cout ∨ ¬b), (sum ∨ cout ∨ ¬cin)
  sum=1,cout=1 → a=b=cin=1:       clause: (¬sum ∨ ¬cout ∨ a), (¬sum ∨ ¬cout ∨ b), (¬sum ∨ ¬cout ∨ cin)

When we know cout and one input:
  cout=0,a=1 → b=0,cin=0:         clause: (cout ∨ ¬a ∨ ¬b), (cout ∨ ¬a ∨ ¬cin)
  cout=1,a=0 → b=1,cin=1:         clause: (¬cout ∨ a ∨ b), (¬cout ∨ a ∨ cin)
  (and symmetric for b, cin)

These are all valid redundant clauses derivable from the FA truth table.
"""

import sys
import os
import time
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from importlib import import_module
enc = import_module('13_custom_cnf_encoder')


class CompressorCNFBuilder(enc.CNFBuilder):
    """Extended CNF builder with full-adder support clauses."""

    def __init__(self):
        super().__init__()
        self.stats['support'] = 0

    def full_adder(self, a, b, cin):
        """Full adder with support clauses for direct sum↔carry↔input coupling."""
        self.stats['fa'] += 1
        # Standard encoding
        t = self.xor2(a, b)
        s = self.xor2(t, cin)
        cout = self.maj(a, b, cin)

        # Skip support clauses if all inputs are known (nothing to propagate)
        n_known = sum(1 for x in [a, b, cin] if self._is_known(x))
        if n_known >= 2 or (self._is_known(s) and self._is_known(cout)):
            return s, cout

        # Support clauses: direct sum+carry → input implications
        # These are redundant but allow the solver to propagate backward
        # from (sum, cout) directly to (a, b, cin) without going through t.

        if not self._is_known(s) and not self._is_known(cout):
            # Case sum=0,cout=0 → all inputs 0
            for x in [a, b, cin]:
                if not self._is_known(x):
                    self.clauses.append([s, cout, -x])
                    self.stats['support'] += 1

            # Case sum=1,cout=1 → all inputs 1
            for x in [a, b, cin]:
                if not self._is_known(x):
                    self.clauses.append([-s, -cout, x])
                    self.stats['support'] += 1

        # Input+carry → other input implications
        # cout=0,a=1 → b=0 AND cin=0
        inputs = [a, b, cin]
        for i in range(3):
            if self._is_known(inputs[i]):
                continue
            others = [inputs[j] for j in range(3) if j != i]
            for o in others:
                if not self._is_known(o) and not self._is_known(cout):
                    # cout=0 AND input_i=1 → other=0
                    self.clauses.append([cout, -inputs[i], -o])
                    self.stats['support'] += 1
                    # cout=1 AND input_i=0 → other=1
                    self.clauses.append([-cout, inputs[i], o])
                    self.stats['support'] += 1

        return s, cout


def encode_with_compressor(mode="sr59"):
    """Encode using the compressor-enhanced builder."""
    M1 = [0x17149975] + [0xffffffff] * 15
    M2 = M1.copy()
    M2[0] ^= 0x80000000
    M2[9] ^= 0x80000000

    state1, W1_pre = enc.precompute_state(M1)
    state2, W2_pre = enc.precompute_state(M2)

    n_free = 5 if mode == "sr59" else 4

    # Use enhanced builder
    cnf = CompressorCNFBuilder()

    s1 = tuple(cnf.const_word(v) for v in state1)
    s2 = tuple(cnf.const_word(v) for v in state2)

    w1_free = [cnf.free_word(f"W1_{57+i}") for i in range(n_free)]
    w2_free = [cnf.free_word(f"W2_{57+i}") for i in range(n_free)]

    W1_schedule = list(w1_free)
    W2_schedule = list(w2_free)

    if mode == "sr60":
        w1_61 = cnf.add_word(
            cnf.add_word(cnf.sigma1_w(w1_free[2]), cnf.const_word(W1_pre[54])),
            cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[46])), cnf.const_word(W1_pre[45]))
        )
        w2_61 = cnf.add_word(
            cnf.add_word(cnf.sigma1_w(w2_free[2]), cnf.const_word(W2_pre[54])),
            cnf.add_word(cnf.const_word(enc.sigma0_py(W2_pre[46])), cnf.const_word(W2_pre[45]))
        )
        W1_schedule.append(w1_61)
        W2_schedule.append(w2_61)

    w60_idx = 3
    w1_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W1_schedule[w60_idx]), cnf.const_word(W1_pre[55])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[47])), cnf.const_word(W1_pre[46]))
    )
    w2_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W2_schedule[w60_idx]), cnf.const_word(W2_pre[55])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W2_pre[47])), cnf.const_word(W2_pre[46]))
    )
    w61_idx = 4
    w1_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W1_schedule[w61_idx]), cnf.const_word(W1_pre[56])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[48])), cnf.const_word(W1_pre[47]))
    )
    w2_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W2_schedule[w61_idx]), cnf.const_word(W2_pre[56])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W2_pre[48])), cnf.const_word(W2_pre[47]))
    )

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


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "sr59"
    timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 300

    print(f"{'='*60}", flush=True)
    print(f"Compressor Support Clauses — {mode}", flush=True)
    print(f"{'='*60}", flush=True)

    cnf = encode_with_compressor(mode)
    nv = cnf.next_var - 1
    nc = len(cnf.clauses)

    print(f"Vars: {nv}, Clauses: {nc}", flush=True)
    print(f"Stats: {cnf.stats}", flush=True)
    print(f"Support clauses added: {cnf.stats['support']}", flush=True)
    print(f"Baseline (no support): ~45K clauses", flush=True)
    print(f"Overhead: +{nc - 45000} clauses ({(nc-45000)/45000*100:.1f}%)", flush=True)

    cnf_file = f"/tmp/{mode}_compressor.cnf"
    cnf.write_dimacs(cnf_file)

    print(f"\nRunning kissat ({timeout}s timeout)...", flush=True)
    t0 = time.time()
    r = subprocess.run(["timeout", str(timeout), "kissat", "-q", cnf_file],
                       capture_output=True, text=True, timeout=timeout + 30)
    elapsed = time.time() - t0

    if r.returncode == 10:
        print(f"[+] SAT in {elapsed:.1f}s (baseline: 220s)", flush=True)
        speedup = 220.0 / elapsed
        print(f"    Speedup: {speedup:.2f}x", flush=True)
    elif r.returncode == 20:
        print(f"[-] UNSAT in {elapsed:.1f}s", flush=True)
    else:
        print(f"[!] TIMEOUT after {elapsed:.1f}s", flush=True)


if __name__ == "__main__":
    main()
