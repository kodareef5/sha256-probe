#!/usr/bin/env python3
"""
Script 56: Carry-Masked Homotopy for sr=60

HYPOTHESIS: The sr=60 obstruction for M[0]=0x17149975 is dominated by
late-round (61-63) carry-chain length in the final ripple-carry adders.

METHOD: In rounds 61, 62, and 63 ONLY, force the top N carry bits of
every add_word call to constant 0 (False) at encode time. The CSA layers
are untouched -- only the final ripple-carry in add_word gets masking.

For bits >= (32 - mask_bits), the carry is forced to cnf._const(False)
instead of being computed from the full adder. The sum bits still use the
(now-zero) carry, so the additions effectively become truncated-precision
in the upper half.

Rounds 57-60 use normal full-precision carries.

INTERPRETATION:
  - SAT quickly  -> late-round carry depth IS the dominant barrier
  - UNSAT quickly -> obstruction is NOT just late carries, something structural
  - TIMEOUT      -> masking top N is insufficient, try masking more

Tests: mask top 16, top 24, and top 28 carries in rounds 61-63,
plus a baseline (no masking) for comparison.
"""

import sys
import os
import time
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from importlib import import_module
enc = import_module('13_custom_cnf_encoder')


class CarryMaskedCNF(enc.CNFBuilder):
    """
    CNFBuilder subclass that can mask (force to 0) the upper carry bits
    in add_word when instructed.
    """

    def __init__(self):
        super().__init__()
        self._mask_carries = False
        self._mask_from_bit = 16  # force carry=0 for bit positions >= this

    def set_carry_mask(self, enabled, mask_from_bit=16):
        """Enable/disable carry masking. When enabled, carries at bit
        positions >= mask_from_bit are forced to constant 0."""
        self._mask_carries = enabled
        self._mask_from_bit = mask_from_bit

    def add_word(self, A, B, track_carries=False):
        """C = A + B (mod 2^32). Ripple-carry addition.
        When carry masking is active, carries at bit >= mask_from_bit
        are forced to 0 instead of being computed from the full adder."""
        C = []
        carries = []
        carry = self._const(False)
        for i in range(32):
            if self._mask_carries and i >= self._mask_from_bit:
                # Force carry to 0 -- truncate the carry chain
                carry = self._const(False)

            if self._is_known(carry) and not self._get_val(carry):
                s, carry = self.half_adder(A[i], B[i])
            else:
                s, carry = self.full_adder(A[i], B[i], carry)
            C.append(s)
            carries.append(carry)
        if track_carries:
            return C, carries
        return C


def encode_carry_masked(mask_bits, masked_rounds=(61, 62, 63), mode="sr60"):
    """
    Encode sr=60 collision with carry masking in specified rounds.

    mask_bits: number of MSB carry bits to mask (0 = no masking = baseline)
    masked_rounds: tuple of round numbers where masking is applied
    """
    M1 = [0x17149975] + [0xffffffff] * 15
    M2 = M1.copy()
    M2[0] ^= 0x80000000
    M2[9] ^= 0x80000000

    state1, W1_pre = enc.precompute_state(M1)
    state2, W2_pre = enc.precompute_state(M2)

    n_free = 4  # sr=60

    cnf = CarryMaskedCNF()

    s1 = tuple(cnf.const_word(v) for v in state1)
    s2 = tuple(cnf.const_word(v) for v in state2)

    w1_free = [cnf.free_word(f"W1_{57+i}") for i in range(n_free)]
    w2_free = [cnf.free_word(f"W2_{57+i}") for i in range(n_free)]

    W1_schedule = list(w1_free)
    W2_schedule = list(w2_free)

    # W[61] = sigma1(W[59]) + W[54] + sigma0(W[46]) + W[45]
    w1_61 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_free[2]), cnf.const_word(W1_pre[54])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[46])), cnf.const_word(W1_pre[45])))
    w2_61 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_free[2]), cnf.const_word(W2_pre[54])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W2_pre[46])), cnf.const_word(W2_pre[45])))
    W1_schedule.append(w1_61)
    W2_schedule.append(w2_61)

    # W[62] = sigma1(W[60]) + W[55] + sigma0(W[47]) + W[46]
    w60_idx = 3
    w1_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W1_schedule[w60_idx]), cnf.const_word(W1_pre[55])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[47])), cnf.const_word(W1_pre[46])))
    w2_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W2_schedule[w60_idx]), cnf.const_word(W2_pre[55])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W2_pre[47])), cnf.const_word(W2_pre[46])))

    # W[63] = sigma1(W[61]) + W[56] + sigma0(W[48]) + W[47]
    w61_idx = 4
    w1_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W1_schedule[w61_idx]), cnf.const_word(W1_pre[56])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[48])), cnf.const_word(W1_pre[47])))
    w2_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W2_schedule[w61_idx]), cnf.const_word(W2_pre[56])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W2_pre[48])), cnf.const_word(W2_pre[47])))

    W1_schedule.extend([w1_62, w1_63])
    W2_schedule.extend([w2_62, w2_63])

    # Compute mask_from_bit: for mask_bits=16, we mask bits 16..31
    mask_from_bit = 32 - mask_bits if mask_bits > 0 else 32

    # Run 7 rounds for both messages
    st1, st2 = s1, s2
    for r in range(7):
        round_num = 57 + r

        # Enable carry masking only for the specified rounds
        if mask_bits > 0 and round_num in masked_rounds:
            cnf.set_carry_mask(True, mask_from_bit)
        else:
            cnf.set_carry_mask(False)

        # Message 1: manual round (same logic as sha256_round_correct
        # but using our cnf which has the overridden add_word)
        a1, b1, c1, d1, e1, f1, g1, h1 = st1
        K_word = cnf.const_word(enc.K[round_num])
        sig1_1 = cnf.Sigma1(e1)
        ch1 = cnf.Ch(e1, f1, g1)

        # T1 via CSA tree -- CSA layers use the BASE csa_layer (no carry masking)
        # Only the final ripple-carry add_word in the CSA gets masked
        s1_csa, c1_csa = cnf.csa_layer(h1, sig1_1, ch1)
        s2_csa, c2_csa = cnf.csa_layer(s1_csa, K_word, W1_schedule[r])
        s3_csa, c3_csa = cnf.csa_layer(c1_csa, s2_csa, c2_csa)
        t1_m1 = cnf.add_word(s3_csa, c3_csa)

        sig0_1 = cnf.Sigma0(a1)
        mj1 = cnf.Maj(a1, b1, c1)
        t2_m1 = cnf.add_word(sig0_1, mj1)
        a_new1 = cnf.add_word(t1_m1, t2_m1)
        e_new1 = cnf.add_word(d1, t1_m1)
        st1 = (a_new1, a1, b1, c1, e_new1, e1, f1, g1)

        # Message 2
        a2, b2, c2, d2, e2, f2, g2, h2 = st2
        sig1_2 = cnf.Sigma1(e2)
        ch2 = cnf.Ch(e2, f2, g2)

        s1_csa2, c1_csa2 = cnf.csa_layer(h2, sig1_2, ch2)
        s2_csa2, c2_csa2 = cnf.csa_layer(s1_csa2, K_word, W2_schedule[r])
        s3_csa2, c3_csa2 = cnf.csa_layer(c1_csa2, s2_csa2, c2_csa2)
        t1_m2 = cnf.add_word(s3_csa2, c3_csa2)

        sig0_2 = cnf.Sigma0(a2)
        mj2 = cnf.Maj(a2, b2, c2)
        t2_m2 = cnf.add_word(sig0_2, mj2)
        a_new2 = cnf.add_word(t1_m2, t2_m2)
        e_new2 = cnf.add_word(d2, t1_m2)
        st2 = (a_new2, a2, b2, c2, e_new2, e2, f2, g2)

    # Disable masking before collision constraints (no add_word here anyway)
    cnf.set_carry_mask(False)

    # Collision constraint
    for i in range(8):
        cnf.eq_word(st1[i], st2[i])

    label = f"mask{mask_bits}_r{'_'.join(str(x) for x in sorted(masked_rounds))}"
    cnf_file = f"/tmp/sr60_carry_{label}.cnf"
    nv, nc = cnf.write_dimacs(cnf_file)
    return cnf_file, nv, nc


def run_kissat(cnf_file, timeout):
    """Run Kissat and return (status, elapsed)."""
    t0 = time.time()
    try:
        r = subprocess.run(
            ["timeout", str(timeout), "kissat", "-q", cnf_file],
            capture_output=True, text=True, timeout=timeout + 30)
        elapsed = time.time() - t0
        if r.returncode == 10:
            return "SAT", elapsed
        elif r.returncode == 20:
            return "UNSAT", elapsed
        else:
            return "TIMEOUT", elapsed
    except subprocess.TimeoutExpired:
        return "TIMEOUT", time.time() - t0


def main():
    timeout = 600

    print("=" * 70, flush=True)
    print("CARRY-MASKED HOMOTOPY FOR SR=60", flush=True)
    print("Forcing top-N carry bits to 0 in rounds 61-63 only", flush=True)
    print(f"Candidate: M[0]=0x17149975, MSB kernel", flush=True)
    print(f"Timeout per test: {timeout}s", flush=True)
    print("=" * 70, flush=True)

    configs = [
        # (mask_bits, masked_rounds, label)
        (0,  (),             "baseline (no masking)"),
        (16, (61, 62, 63),   "mask top 16 carries, rounds 61-63"),
        (24, (61, 62, 63),   "mask top 24 carries, rounds 61-63"),
        (28, (61, 62, 63),   "mask top 28 carries, rounds 61-63"),
    ]

    results = []

    for mask_bits, masked_rounds, label in configs:
        print(f"\n{'='*60}", flush=True)
        print(f"TEST: {label}", flush=True)
        print(f"{'='*60}", flush=True)

        t_enc_start = time.time()
        cnf_file, nv, nc = encode_carry_masked(mask_bits, masked_rounds)
        t_enc = time.time() - t_enc_start

        print(f"  Encoding: {t_enc:.1f}s", flush=True)
        print(f"  Variables: {nv}", flush=True)
        print(f"  Clauses:   {nc}", flush=True)
        print(f"  CNF file:  {cnf_file}", flush=True)
        print(f"  Running Kissat ({timeout}s)...", flush=True)

        status, elapsed = run_kissat(cnf_file, timeout)

        if status == "SAT":
            print(f"  >>> SAT in {elapsed:.1f}s", flush=True)
        elif status == "UNSAT":
            print(f"  >>> UNSAT in {elapsed:.1f}s", flush=True)
        else:
            print(f"  >>> TIMEOUT after {elapsed:.1f}s", flush=True)

        results.append((label, mask_bits, nv, nc, status, elapsed))

    # Summary table
    print(f"\n{'='*70}", flush=True)
    print("RESULTS SUMMARY", flush=True)
    print(f"{'='*70}", flush=True)
    print(f"{'Mask Bits':>10}  {'Rounds Masked':>15}  {'Vars':>8}  {'Clauses':>8}  {'Result':>8}  {'Time':>8}", flush=True)
    print(f"{'-'*10}  {'-'*15}  {'-'*8}  {'-'*8}  {'-'*8}  {'-'*8}", flush=True)
    for label, mask_bits, nv, nc, status, elapsed in results:
        rounds_str = "61-63" if mask_bits > 0 else "none"
        print(f"{mask_bits:>10}  {rounds_str:>15}  {nv:>8}  {nc:>8}  {status:>8}  {elapsed:>7.1f}s", flush=True)

    # Interpretation
    print(f"\n{'='*70}", flush=True)
    print("INTERPRETATION (for the tested candidate and MSB kernel)", flush=True)
    print(f"{'='*70}", flush=True)

    sat_results = [r for r in results if r[4] == "SAT" and r[1] > 0]
    unsat_results = [r for r in results if r[4] == "UNSAT" and r[1] > 0]
    timeout_results = [r for r in results if r[4] == "TIMEOUT" and r[1] > 0]

    if sat_results:
        fastest = min(sat_results, key=lambda x: x[5])
        print(f"  SAT found with mask={fastest[1]} in {fastest[5]:.1f}s", flush=True)
        print(f"  -> Late-round carry depth IS a dominant barrier.", flush=True)
        print(f"  -> Masking {fastest[1]} MSB carries in rounds 61-63 makes sr=60 tractable.", flush=True)
        print(f"  -> The relaxed problem has solutions, suggesting the obstruction", flush=True)
        print(f"     is specifically the long carry chains, not the algebraic structure.", flush=True)
    elif unsat_results:
        print(f"  UNSAT for all mask levels tested.", flush=True)
        print(f"  -> The sr=60 obstruction is NOT just late-round carry depth.", flush=True)
        print(f"  -> Something structural (beyond carry-chain length) blocks solutions.", flush=True)
        print(f"  -> Carry masking creates inconsistency: the relaxed problem has no solutions.", flush=True)
    elif timeout_results:
        print(f"  All masked tests timed out.", flush=True)
        print(f"  -> Masking up to {max(r[1] for r in timeout_results)} MSB carries is insufficient.", flush=True)
        print(f"  -> Either the carry chains are not the bottleneck, or more aggressive", flush=True)
        print(f"     masking (e.g., mask all 32 bits) is needed.", flush=True)
    else:
        print(f"  No masked tests ran.", flush=True)


if __name__ == "__main__":
    main()
