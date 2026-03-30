#!/usr/bin/env python3
"""
Script 65: SAT-Driven Backward IV Generation

THE BLIND SPOT: We've been using the standard NIST IV the entire time.
But the paper's attack is SEMI-FREE-START — the IV is a free parameter!

This script asks Kissat to FIND an IV that produces a maximally cold
state at Round 56. Instead of scanning M[0] with a fixed IV, we fix
M[0..15] and let the SAT solver choose the optimal IV.

With 256 bits of IV freedom and only 256 bits of state to constrain,
this should be trivially satisfiable — we're just evaluating the
compression function forward with free initial conditions.

We can demand:
  - da[56] = 0 (necessary for the SAT tail)
  - db[56] = 0 (extra coolness)
  - dc[56] = 0 (even more)
  - dd[56] = 0, de[56] = 0, ... (as cold as possible)

The colder the Round 56 state, the easier the sr=60 tail becomes.
"""

import sys
import os
import time
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from importlib import import_module
enc = import_module('13_custom_cnf_encoder')


def encode_iv_search(n_zero_regs=1, m0=0x17149975):
    """
    Encode: find an IV such that after 57 rounds of compression with
    the MSB kernel messages, n_zero_regs register diffs are zero.

    n_zero_regs=1: just da[56]=0 (easiest, should be instant)
    n_zero_regs=4: da=db=dc=dd=0 at round 56 (very cold)
    n_zero_regs=8: ALL register diffs zero at round 56 (maximally cold)
    """
    M1 = [m0] + [0xffffffff] * 15
    M2 = M1[:]
    M2[0] ^= 0x80000000
    M2[9] ^= 0x80000000

    cnf = enc.CNFBuilder()

    # IV is FREE — 8 x 32-bit words = 256 free variables
    iv1 = [cnf.free_word(f"IV_{i}") for i in range(8)]

    # Both messages use the SAME IV (semi-free-start)
    # Build initial state from IV
    s1 = tuple(iv1)  # (a0, b0, c0, d0, e0, f0, g0, h0)
    s2 = tuple(iv1)  # Same IV for both messages

    # Precompute the message schedule (deterministic, no free variables)
    # But we need to encode the FULL 57 rounds as SAT since the IV is free
    # The schedule words W[0..56] are constants (determined by M1/M2)

    # Actually, the schedule is message-dependent and fully determined:
    W1 = [0] * 57
    for i in range(16): W1[i] = M1[i]
    for i in range(16, 57):
        W1[i] = (enc.sigma1_py(W1[i-2]) + W1[i-7] + enc.sigma0_py(W1[i-15]) + W1[i-16]) & 0xFFFFFFFF

    W2 = [0] * 57
    for i in range(16): W2[i] = M2[i]
    for i in range(16, 57):
        W2[i] = (enc.sigma1_py(W2[i-2]) + W2[i-7] + enc.sigma0_py(W2[i-15]) + W2[i-16]) & 0xFFFFFFFF

    # Encode 57 rounds of compression for BOTH messages
    # This is a large circuit but should be solvable since IV has 256 bits
    # of freedom and we're only constraining 32-256 bits at the output

    print(f"  Encoding 57 rounds for message 1...", flush=True)
    st1 = s1
    for r in range(57):
        W_word = cnf.const_word(W1[r])
        st1 = cnf.sha256_round_correct(st1, enc.K[r], W_word)
        if r % 10 == 0:
            print(f"    Round {r}: {cnf.next_var-1} vars, {len(cnf.clauses)} clauses", flush=True)

    print(f"  Encoding 57 rounds for message 2...", flush=True)
    st2 = s2
    for r in range(57):
        W_word = cnf.const_word(W2[r])
        st2 = cnf.sha256_round_correct(st2, enc.K[r], W_word)
        if r % 10 == 0:
            print(f"    Round {r}: {cnf.next_var-1} vars, {len(cnf.clauses)} clauses", flush=True)

    # Constraint: first n_zero_regs register diffs = 0 at round 56
    reg_names = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    for i in range(n_zero_regs):
        cnf.eq_word(st1[i], st2[i])

    return cnf, iv1, st1, st2


def extract_iv(cnf, iv_words, solution_text):
    """Extract IV values from Kissat solution."""
    solution = {}
    for line in solution_text.split('\n'):
        if line.startswith('v '):
            for lit in line[2:].split():
                v = int(lit)
                if v != 0:
                    solution[abs(v)] = (v > 0)

    iv_values = []
    for w in range(8):
        val = 0
        for bit in range(32):
            var_id = iv_words[w][bit]
            if abs(var_id) in solution:
                bit_val = solution[abs(var_id)]
                if var_id < 0:
                    bit_val = not bit_val
                if bit_val:
                    val |= (1 << bit)
        iv_values.append(val)

    return iv_values


def verify_iv(iv_values, m0, n_zero_regs):
    """Verify the found IV in pure Python."""
    M1 = [m0] + [0xffffffff] * 15
    M2 = M1[:]
    M2[0] ^= 0x80000000
    M2[9] ^= 0x80000000

    def compress_57(M, iv):
        W = [0] * 57
        for i in range(16): W[i] = M[i]
        for i in range(16, 57):
            W[i] = (enc.sigma1_py(W[i-2]) + W[i-7] + enc.sigma0_py(W[i-15]) + W[i-16]) & 0xFFFFFFFF
        a, b, c, d, e, f, g, h = iv
        for i in range(57):
            T1 = (h + enc.Sigma1_py(e) + enc.Ch_py(e, f, g) + enc.K[i] + W[i]) & 0xFFFFFFFF
            T2 = (enc.Sigma0_py(a) + enc.Maj_py(a, b, c)) & 0xFFFFFFFF
            h = g; g = f; f = e; e = (d + T1) & 0xFFFFFFFF
            d = c; c = b; b = a; a = (T1 + T2) & 0xFFFFFFFF
        return (a, b, c, d, e, f, g, h)

    s1 = compress_57(M1, iv_values)
    s2 = compress_57(M2, iv_values)

    reg_names = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    total_hw = 0
    for i in range(8):
        diff = s1[i] ^ s2[i]
        hw = bin(diff).count('1')
        total_hw += hw
        status = "ZERO" if diff == 0 else f"hw={hw}"
        print(f"    d{reg_names[i]}[56] = 0x{diff:08x} ({status})", flush=True)

    print(f"    Total HW at round 56: {total_hw}", flush=True)
    return s1, s2, total_hw


def main():
    timeout = int(sys.argv[1]) if len(sys.argv) > 1 else 600

    print("=" * 60, flush=True)
    print("SAT-DRIVEN BACKWARD IV GENERATION", flush=True)
    print("Finding an IV that produces a cold state at Round 56", flush=True)
    print("=" * 60, flush=True)

    # Test increasing coldness demands
    for n_regs in [1, 2, 4, 6, 8]:
        reg_names = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        target = ", ".join(f"d{reg_names[i]}=0" for i in range(n_regs))

        print(f"\n{'='*60}", flush=True)
        print(f"Target: {n_regs}/8 register diffs = 0 at Round 56", flush=True)
        print(f"  ({target})", flush=True)
        print(f"{'='*60}", flush=True)

        cnf, iv_words, st1, st2 = encode_iv_search(n_regs)
        nv = cnf.next_var - 1
        nc = len(cnf.clauses)

        cnf_file = f"/tmp/iv_search_{n_regs}regs.cnf"
        cnf.write_dimacs(cnf_file)

        print(f"  {nv} vars, {nc} clauses", flush=True)
        print(f"  Running Kissat ({timeout}s)...", flush=True)

        t0 = time.time()
        r = subprocess.run(["timeout", str(timeout), "kissat", cnf_file],
                           capture_output=True, text=True, timeout=timeout + 30)
        elapsed = time.time() - t0

        if r.returncode == 10:
            print(f"  [+] SAT in {elapsed:.1f}s!", flush=True)
            iv = extract_iv(cnf, iv_words, r.stdout)
            print(f"  Found IV:", flush=True)
            for i in range(8):
                print(f"    IV[{i}] = 0x{iv[i]:08x}", flush=True)

            print(f"  Verification:", flush=True)
            s1, s2, total_hw = verify_iv(iv, 0x17149975, n_regs)

            if total_hw < 50:
                print(f"\n  [!!!] COLD IV FOUND! Total HW = {total_hw}", flush=True)
                print(f"  This IV is a candidate for sr=60 tail solving!", flush=True)

        elif r.returncode == 20:
            print(f"  [-] UNSAT in {elapsed:.1f}s", flush=True)
            print(f"  No IV exists that produces {n_regs} zero diffs at Round 56", flush=True)
            print(f"  (for this message pair with MSB kernel)", flush=True)
            break
        else:
            print(f"  [!] TIMEOUT after {elapsed:.1f}s", flush=True)
            print(f"  Too many constraints for SAT solver at this demand level", flush=True)


if __name__ == "__main__":
    main()
