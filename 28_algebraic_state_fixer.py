#!/usr/bin/env python3
"""
Script 28: Algebraic State Fixing — Consume Round 57 via Linear Algebra

At round 57, the state update is:
  T1 = h[56] + Sigma1(e[56]) + Ch(e[56],f[56],g[56]) + K[57] + W[57]
  T2 = Sigma0(a[56]) + Maj(a[56],b[56],c[56])
  a[57] = T1 + T2
  e[57] = d[56] + T1

Since da[56]=0 (precomputed), and b,c,d,f,g,h at round 56 are known
constants from precomputation, T2 is FULLY DETERMINED (no free variables).
T1 = CONSTANT + W[57], so:
  a[57] = C_T2 + C_partial + W[57]
  e[57] = C_d + C_partial + W[57]

This means W[57] has DIRECT LINEAR CONTROL over a[57] and e[57].
We can CHOOSE W[57] to force ANY value of a[57] (or e[57]).

If we force da[57]=0 (a1[57] = a2[57]), we algebraically consume
Round 57's complexity. The SAT solver then only needs to handle
rounds 58-63 (6 rounds), which is effectively sr=59 difficulty!

Key question: can we simultaneously force da[57]=0 for BOTH messages
by choosing W1[57] and W2[57] independently?
"""

import sys
import os
import time
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from importlib import import_module
enc = import_module('13_custom_cnf_encoder')

# SHA-256 primitives
ROR = enc.ROR
Ch = enc.Ch_py
Maj = enc.Maj_py
Sigma0 = enc.Sigma0_py
Sigma1 = enc.Sigma1_py
M32 = 0xFFFFFFFF


def analyze_round57_control():
    """
    Analyze how W[57] controls the round 57 state.

    At round 57:
      T1 = h + Sigma1(e) + Ch(e,f,g) + K[57] + W[57]
      T2 = Sigma0(a) + Maj(a,b,c)
      a_new = T1 + T2
      e_new = d + T1

    All register values (a,b,c,d,e,f,g,h) at round 56 are precomputed.
    T2 is entirely constant (no free variables at round 57).
    T1 = const + W[57], so a_new and e_new are linear functions of W[57].
    """

    M1 = [0x17149975] + [0xffffffff] * 15
    M2 = M1.copy()
    M2[0] ^= 0x80000000
    M2[9] ^= 0x80000000

    state1, W1_pre = enc.precompute_state(M1)
    state2, W2_pre = enc.precompute_state(M2)

    a1, b1, c1, d1, e1, f1, g1, h1 = state1
    a2, b2, c2, d2, e2, f2, g2, h2 = state2

    print("=" * 60, flush=True)
    print("Round 57 Algebraic Analysis", flush=True)
    print("=" * 60, flush=True)

    # Verify da[56] = 0
    print(f"\nState at round 56:", flush=True)
    print(f"  da[56] = {a1 ^ a2:#010x} (must be 0)", flush=True)
    assert a1 == a2, "da[56] != 0!"

    # Compute constants for round 57
    # T2 is fully constant (depends only on a,b,c which are precomputed)
    T2_1 = (Sigma0(a1) + Maj(a1, b1, c1)) & M32
    T2_2 = (Sigma0(a2) + Maj(a2, b2, c2)) & M32

    # T1_partial = h + Sigma1(e) + Ch(e,f,g) + K[57]
    # (everything except W[57])
    T1_partial_1 = (h1 + Sigma1(e1) + Ch(e1, f1, g1) + enc.K[57]) & M32
    T1_partial_2 = (h2 + Sigma1(e2) + Ch(e2, f2, g2) + enc.K[57]) & M32

    print(f"\nRound 57 constants:", flush=True)
    print(f"  T1_partial_M1 = {T1_partial_1:#010x} (h + Sig1(e) + Ch(e,f,g) + K[57])", flush=True)
    print(f"  T1_partial_M2 = {T1_partial_2:#010x}", flush=True)
    print(f"  T2_M1 = {T2_1:#010x} (Sig0(a) + Maj(a,b,c))", flush=True)
    print(f"  T2_M2 = {T2_2:#010x}", flush=True)
    print(f"  d_M1 = {d1:#010x}", flush=True)
    print(f"  d_M2 = {d2:#010x}", flush=True)

    # The key relationships:
    # a1[57] = T1_partial_1 + W1[57] + T2_1
    # a2[57] = T1_partial_2 + W2[57] + T2_2
    # e1[57] = d1 + T1_partial_1 + W1[57]
    # e2[57] = d2 + T1_partial_2 + W2[57]

    # For da[57] = 0: a1[57] = a2[57]
    # => T1_partial_1 + W1[57] + T2_1 = T1_partial_2 + W2[57] + T2_2  (mod 2^32)
    # => W1[57] - W2[57] = (T1_partial_2 + T2_2) - (T1_partial_1 + T2_1)  (mod 2^32)

    rhs_a = ((T1_partial_2 + T2_2) - (T1_partial_1 + T2_1)) & M32
    print(f"\n  For da[57]=0: W1[57] - W2[57] = {rhs_a:#010x} (mod 2^32)", flush=True)
    print(f"  => W2[57] = W1[57] - {rhs_a:#010x} (mod 2^32)", flush=True)

    # For de[57] = 0: e1[57] = e2[57]
    # => d1 + T1_partial_1 + W1[57] = d2 + T1_partial_2 + W2[57]
    # => W1[57] - W2[57] = (d2 + T1_partial_2) - (d1 + T1_partial_1)

    rhs_e = ((d2 + T1_partial_2) - (d1 + T1_partial_1)) & M32
    print(f"\n  For de[57]=0: W1[57] - W2[57] = {rhs_e:#010x} (mod 2^32)", flush=True)

    # Can we satisfy BOTH da[57]=0 AND de[57]=0?
    if rhs_a == rhs_e:
        print(f"\n  [!!!] BOTH da[57]=0 AND de[57]=0 with the SAME constraint!", flush=True)
        print(f"  This means we can force BOTH register diffs to zero!", flush=True)
    else:
        print(f"\n  da[57]=0 and de[57]=0 require DIFFERENT W constraints.", flush=True)
        print(f"  Difference: {(rhs_a - rhs_e) & M32:#010x}", flush=True)
        print(f"  We must choose: force da[57]=0 OR de[57]=0, not both.", flush=True)

    # The shift register also gives us:
    # db[57] = da[56] = 0 (FREE!)
    # dc[57] = db[56] = da[55] (precomputed, generally nonzero)
    # dd[57] = dc[56] = da[54]
    # df[57] = de[56]
    # dg[57] = df[56]
    # dh[57] = dg[56]

    print(f"\n  Shift register at round 57:", flush=True)
    print(f"  db[57] = da[56] = 0 (FREE!)", flush=True)
    dc57 = b1 ^ b2; print(f"  dc[57] = db[56] = {dc57:#010x} (hw={bin(dc57).count('1')})", flush=True)
    dd57 = c1 ^ c2; print(f"  dd[57] = dc[56] = {dd57:#010x} (hw={bin(dd57).count('1')})", flush=True)
    df57 = e1 ^ e2; print(f"  df[57] = de[56] = {df57:#010x} (hw={bin(df57).count('1')})", flush=True)
    dg57 = f1 ^ f2; print(f"  dg[57] = df[56] = {dg57:#010x} (hw={bin(dg57).count('1')})", flush=True)
    dh57 = g1 ^ g2; print(f"  dh[57] = dg[56] = {dh57:#010x} (hw={bin(dh57).count('1')})", flush=True)

    # If we force da[57]=0:
    # After round 57, the state diffs are:
    # da=0, db=0, dc=dc57, dd=dd57, de=de57(depends on W), df=df57, dg=dg57, dh=dh57
    # That's 2 zeros out of 8 registers, vs 1 zero (just da=0) without fixing.

    print(f"\n{'='*60}", flush=True)
    print(f"STRATEGY: Force da[57]=0 via W2[57] = W1[57] - {rhs_a:#010x}", flush=True)
    print(f"{'='*60}", flush=True)
    print(f"This gives us da[57]=0 AND db[57]=0 (2 zero diffs instead of 1).", flush=True)
    print(f"The SAT solver for rounds 58-63 starts with a CLEANER state.", flush=True)
    print(f"Effectively: W2[57] is no longer free — it's determined by W1[57].", flush=True)
    print(f"We lose 32 bits of freedom but gain 32 bits of constraint satisfaction.", flush=True)

    return rhs_a, rhs_e, state1, state2, W1_pre, W2_pre


def encode_sr60_with_da57_fixed(rhs_a, timeout_sec=3600):
    """
    Encode sr=60 with the algebraic constraint W2[57] = W1[57] - rhs_a.
    This forces da[57]=0, consuming Round 57 algebraically.
    """
    M1 = [0x17149975] + [0xffffffff] * 15
    M2 = M1.copy()
    M2[0] ^= 0x80000000
    M2[9] ^= 0x80000000

    state1, W1_pre = enc.precompute_state(M1)
    state2, W2_pre = enc.precompute_state(M2)

    cnf = enc.CNFBuilder()
    s1 = tuple(cnf.const_word(v) for v in state1)
    s2 = tuple(cnf.const_word(v) for v in state2)

    # Free variables: W1[57..60] as before
    w1_free = [cnf.free_word(f"W1_{57+i}") for i in range(4)]

    # W2[57] is DETERMINED: W2[57] = W1[57] - rhs_a (mod 2^32)
    # We compute this as: W2[57] = W1[57] + (2^32 - rhs_a) mod 2^32
    neg_rhs = (0x100000000 - rhs_a) & M32
    w2_57 = cnf.add_word(w1_free[0], cnf.const_word(neg_rhs))

    # W2[58..60] are still free
    w2_free_58 = cnf.free_word("W2_58")
    w2_free_59 = cnf.free_word("W2_59")
    w2_free_60 = cnf.free_word("W2_60")

    w2_free = [w2_57, w2_free_58, w2_free_59, w2_free_60]

    # Build schedules
    W1_schedule = list(w1_free)
    W2_schedule = list(w2_free)

    # W[61] enforced
    w1_61 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_free[2]), cnf.const_word(W1_pre[54])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[46])), cnf.const_word(W1_pre[45])))
    w2_61 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_free[2]), cnf.const_word(W2_pre[54])),
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

    # Compression rounds
    st1 = s1
    for i in range(7):
        st1 = cnf.sha256_round_correct(st1, enc.K[57+i], W1_schedule[i])
    st2 = s2
    for i in range(7):
        st2 = cnf.sha256_round_correct(st2, enc.K[57+i], W2_schedule[i])

    # Collision constraint
    for i in range(8):
        cnf.eq_word(st1[i], st2[i])

    cnf_file = "/tmp/sr60_da57fixed.cnf"
    cnf.write_dimacs(cnf_file)
    nv = cnf.next_var - 1
    nc = len(cnf.clauses)

    print(f"\nsr=60 with da[57]=0 algebraically forced:", flush=True)
    print(f"  {nv} vars, {nc} clauses", flush=True)
    print(f"  Free: W1[57..60] + W2[58..60] = 7 words x 32 = 224 bits", flush=True)
    print(f"  (W2[57] determined from W1[57], not free)", flush=True)
    print(f"  Collision: 256 bits. Slack: 224 - 256 = -32 bits (NEGATIVE)", flush=True)
    print(f"  But da[57]=0 AND db[57]=0 provides 64 bits of implicit constraint satisfaction", flush=True)
    print(f"  Net effective slack: ~32 bits (similar to k=16 progressive)", flush=True)

    print(f"\nRunning Kissat ({timeout_sec}s)...", flush=True)
    t0 = time.time()
    r = subprocess.run(["timeout", str(timeout_sec), "kissat", "-q", cnf_file],
                       capture_output=True, text=True, timeout=timeout_sec + 30)
    elapsed = time.time() - t0

    if r.returncode == 10:
        print(f"[!!!] SAT in {elapsed:.1f}s — da[57]=0 algebraic fix WORKS!", flush=True)
        return "SAT", elapsed
    elif r.returncode == 20:
        print(f"[-] UNSAT in {elapsed:.1f}s — forcing da[57]=0 is incompatible with sr=60", flush=True)
        return "UNSAT", elapsed
    else:
        print(f"[!] TIMEOUT after {elapsed:.1f}s", flush=True)
        return "TIMEOUT", elapsed


def main():
    timeout = int(sys.argv[1]) if len(sys.argv) > 1 else 3600

    rhs_a, rhs_e, _, _, _, _ = analyze_round57_control()

    print(f"\n{'='*60}", flush=True)
    print("Testing sr=60 with da[57]=0 forced algebraically", flush=True)
    print(f"{'='*60}", flush=True)

    result, elapsed = encode_sr60_with_da57_fixed(rhs_a, timeout)

    if result == "UNSAT":
        print(f"\nda[57]=0 is incompatible. Trying de[57]=0 instead...", flush=True)
        # If da[57]=0 fails, try de[57]=0
        # de[57]=0 means: W2[57] = W1[57] - rhs_e
        encode_sr60_with_da57_fixed(rhs_e, timeout)


if __name__ == "__main__":
    main()
