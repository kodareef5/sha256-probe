#!/usr/bin/env python3
"""
sequential_modification.py — Wang-style sequential register zeroing for sr=60

Key insight: we have 4 free words (W[57..60]). Each can be used to
deterministically zero ONE register at the corresponding round.

The question: if we use dW[57] to zero da57 and dW[58] to zero da58,
how much error remains in de57 and de58? And can the remaining 2 free
words (W[59], W[60]) + schedule-determined W[61..63] absorb it?

This test:
1. Fix dW[57] for da57=0 (depth 1 — already proven viable)
2. Fix dW[58] for da58=0 (depth 2 — new, uses second free word)
3. Measure remaining error in e-registers
4. Encode the doubly-constrained problem and run Kissat

If da57=0 + da58=0 constraining makes the problem FASTER, we've found
the right decomposition. If it makes it UNSAT, the a-register zeroing
strategy hits a wall at depth 2.
"""

import sys, os, time, subprocess, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from lib.sha256 import *
from lib.cnf_encoder import CNFBuilder


def compute_round57_state(s1, s2, W1_57, W2_57):
    """Compute state after round 57 given specific W[57] values."""
    T1_1 = add(s1[7], Sigma1(s1[4]), Ch(s1[4],s1[5],s1[6]), K[57], W1_57)
    T2_1 = add(Sigma0(s1[0]), Maj(s1[0],s1[1],s1[2]))
    T1_2 = add(s2[7], Sigma1(s2[4]), Ch(s2[4],s2[5],s2[6]), K[57], W2_57)
    T2_2 = add(Sigma0(s2[0]), Maj(s2[0],s2[1],s2[2]))

    a1 = add(T1_1, T2_1); e1 = add(s1[3], T1_1)
    a2 = add(T1_2, T2_2); e2 = add(s2[3], T1_2)

    st1_57 = (a1, s1[0], s1[1], s1[2], e1, s1[4], s1[5], s1[6])
    st2_57 = (a2, s2[0], s2[1], s2[2], e2, s2[4], s2[5], s2[6])
    return st1_57, st2_57


def compute_dw_for_da_zero(s1, s2):
    """Compute dW that makes da=0 at the next round."""
    d_h = (s1[7] - s2[7]) & MASK
    d_Sig1 = (Sigma1(s1[4]) - Sigma1(s2[4])) & MASK
    d_Ch = (Ch(s1[4],s1[5],s1[6]) - Ch(s2[4],s2[5],s2[6])) & MASK
    C_T1 = add(d_h, d_Sig1, d_Ch)
    d_Sig0 = (Sigma0(s1[0]) - Sigma0(s2[0])) & MASK
    d_Maj = (Maj(s1[0],s1[1],s1[2]) - Maj(s2[0],s2[1],s2[2])) & MASK
    C_T2 = add(d_Sig0, d_Maj)
    return (-add(C_T1, C_T2)) & MASK


def compute_dw_for_de_zero(s1, s2):
    """Compute dW that makes de=0 at the next round."""
    d_h = (s1[7] - s2[7]) & MASK
    d_Sig1 = (Sigma1(s1[4]) - Sigma1(s2[4])) & MASK
    d_Ch = (Ch(s1[4],s1[5],s1[6]) - Ch(s2[4],s2[5],s2[6])) & MASK
    C_T1 = add(d_h, d_Sig1, d_Ch)
    d_d = (s1[3] - s2[3]) & MASK
    return (-add(d_d, C_T1)) & MASK


def analyze_sequential(m0, fill):
    """Analyze sequential register zeroing for a candidate."""
    M1 = [m0]+[fill]*15; M2 = list(M1); M2[0]^=0x80000000; M2[9]^=0x80000000
    s1, W1 = precompute_state(M1); s2, W2 = precompute_state(M2)
    assert s1[0] == s2[0]

    regs = ['a','b','c','d','e','f','g','h']

    print(f"Sequential Modification Analysis: M[0]=0x{m0:08x} fill=0x{fill:08x}")
    print(f"{'='*70}")

    # Round 57: fix dW[57] for da57=0
    dw57 = compute_dw_for_da_zero(s1, s2)
    W1_57, W2_57 = 0, (0 - dw57) & MASK  # pick W1=0 for concreteness
    st1_57, st2_57 = compute_round57_state(s1, s2, W1_57, W2_57)

    print(f"\nRound 57 (dW57=0x{dw57:08x}, da57=0):")
    for i in range(8):
        d = st1_57[i] ^ st2_57[i]
        print(f"  d{regs[i]}[57] = 0x{d:08x} (hw={hw(d)})")
    print(f"  Total: {sum(hw(st1_57[i]^st2_57[i]) for i in range(8))} active bits")

    # Round 58: fix dW[58] for da58=0
    dw58 = compute_dw_for_da_zero(st1_57, st2_57)
    W1_58, W2_58 = 0, (0 - dw58) & MASK

    T1_1 = add(st1_57[7], Sigma1(st1_57[4]), Ch(st1_57[4],st1_57[5],st1_57[6]), K[58], W1_58)
    T2_1 = add(Sigma0(st1_57[0]), Maj(st1_57[0],st1_57[1],st1_57[2]))
    T1_2 = add(st2_57[7], Sigma1(st2_57[4]), Ch(st2_57[4],st2_57[5],st2_57[6]), K[58], W2_58)
    T2_2 = add(Sigma0(st2_57[0]), Maj(st2_57[0],st2_57[1],st2_57[2]))

    a1_58 = add(T1_1, T2_1); e1_58 = add(st1_57[3], T1_1)
    a2_58 = add(T1_2, T2_2); e2_58 = add(st2_57[3], T1_2)

    st1_58 = (a1_58, st1_57[0], st1_57[1], st1_57[2], e1_58, st1_57[4], st1_57[5], st1_57[6])
    st2_58 = (a2_58, st2_57[0], st2_57[1], st2_57[2], e2_58, st2_57[4], st2_57[5], st2_57[6])

    print(f"\nRound 58 (dW58=0x{dw58:08x}, da58=0):")
    for i in range(8):
        d = st1_58[i] ^ st2_58[i]
        print(f"  d{regs[i]}[58] = 0x{d:08x} (hw={hw(d)})")
    total_58 = sum(hw(st1_58[i]^st2_58[i]) for i in range(8))
    print(f"  Total: {total_58} active bits")

    # Also try: da57=0 + de58=0 instead of da57=0 + da58=0
    dw58_e = compute_dw_for_de_zero(st1_57, st2_57)
    W1_58e, W2_58e = 0, (0 - dw58_e) & MASK

    T1_1e = add(st1_57[7], Sigma1(st1_57[4]), Ch(st1_57[4],st1_57[5],st1_57[6]), K[58], W1_58e)
    T2_1e = add(Sigma0(st1_57[0]), Maj(st1_57[0],st1_57[1],st1_57[2]))
    T1_2e = add(st2_57[7], Sigma1(st2_57[4]), Ch(st2_57[4],st2_57[5],st2_57[6]), K[58], W2_58e)
    T2_2e = add(Sigma0(st2_57[0]), Maj(st2_57[0],st2_57[1],st2_57[2]))

    a1_58e = add(T1_1e, T2_1e); e1_58e = add(st1_57[3], T1_1e)
    a2_58e = add(T1_2e, T2_2e); e2_58e = add(st2_57[3], T1_2e)

    st1_58e = (a1_58e, st1_57[0], st1_57[1], st1_57[2], e1_58e, st1_57[4], st1_57[5], st1_57[6])
    st2_58e = (a2_58e, st2_57[0], st2_57[1], st2_57[2], e2_58e, st2_57[4], st2_57[5], st2_57[6])

    print(f"\nRound 58 ALT (dW58=0x{dw58_e:08x}, de58=0):")
    for i in range(8):
        d = st1_58e[i] ^ st2_58e[i]
        print(f"  d{regs[i]}[58] = 0x{d:08x} (hw={hw(d)})")
    total_58e = sum(hw(st1_58e[i]^st2_58e[i]) for i in range(8))
    print(f"  Total: {total_58e} active bits")

    # Compute the boomerang at depth 2
    gap58 = (dw58 ^ dw58_e) & MASK
    print(f"\n  Depth-2 boomerang: dW58_for_a - dW58_for_e = 0x{gap58:08x} (hw={hw(gap58)})")

    return dw57, dw58, dw58_e, st1_57, st2_57, st1_58, st2_58, W1, W2


def encode_doubly_constrained(m0, fill, dw57, dw58, timeout=600):
    """Encode sr=60 with BOTH da57=0 AND da58=0 constraints."""
    M1 = [m0]+[fill]*15; M2 = list(M1); M2[0]^=0x80000000; M2[9]^=0x80000000
    s1, W1_pre = precompute_state(M1); s2, W2_pre = precompute_state(M2)

    cnf = CNFBuilder()
    st1 = tuple(cnf.const_word(v) for v in s1)
    st2 = tuple(cnf.const_word(v) for v in s2)

    w1_free = [cnf.free_word(f"W1_{57+i}") for i in range(4)]
    w2_free = [cnf.free_word(f"W2_{57+i}") for i in range(4)]

    # Constraint 1: da57=0 via dW57
    cnf.eq_word(w1_free[0], cnf.add_word(w2_free[0], cnf.const_word(dw57)))
    # Constraint 2: da58=0 via dW58
    cnf.eq_word(w1_free[1], cnf.add_word(w2_free[1], cnf.const_word(dw58)))

    # Schedule tail
    w1_61 = cnf.add_word(cnf.add_word(cnf.sigma1_w(w1_free[2]), cnf.const_word(W1_pre[54])),
                         cnf.add_word(cnf.const_word(sigma0(W1_pre[46])), cnf.const_word(W1_pre[45])))
    w2_61 = cnf.add_word(cnf.add_word(cnf.sigma1_w(w2_free[2]), cnf.const_word(W2_pre[54])),
                         cnf.add_word(cnf.const_word(sigma0(W2_pre[46])), cnf.const_word(W2_pre[45])))
    w1_62 = cnf.add_word(cnf.add_word(cnf.sigma1_w(w1_free[3]), cnf.const_word(W1_pre[55])),
                         cnf.add_word(cnf.const_word(sigma0(W1_pre[47])), cnf.const_word(W1_pre[46])))
    w2_62 = cnf.add_word(cnf.add_word(cnf.sigma1_w(w2_free[3]), cnf.const_word(W2_pre[55])),
                         cnf.add_word(cnf.const_word(sigma0(W2_pre[47])), cnf.const_word(W2_pre[46])))
    w1_63 = cnf.add_word(cnf.add_word(cnf.sigma1_w(w1_61), cnf.const_word(W1_pre[56])),
                         cnf.add_word(cnf.const_word(sigma0(W1_pre[48])), cnf.const_word(W1_pre[47])))
    w2_63 = cnf.add_word(cnf.add_word(cnf.sigma1_w(w2_61), cnf.const_word(W2_pre[56])),
                         cnf.add_word(cnf.const_word(sigma0(W2_pre[48])), cnf.const_word(W2_pre[47])))

    W1s = list(w1_free) + [w1_61, w1_62, w1_63]
    W2s = list(w2_free) + [w2_61, w2_62, w2_63]

    for i in range(7):
        st1 = cnf.sha256_round_correct(st1, K[57+i], W1s[i])
    for i in range(7):
        st2 = cnf.sha256_round_correct(st2, K[57+i], W2s[i])
    for i in range(8):
        cnf.eq_word(st1[i], st2[i])

    nv, nc = cnf.next_var - 1, len(cnf.clauses)
    print(f"  Doubly constrained CNF: {nv} vars, {nc} clauses")

    with tempfile.NamedTemporaryFile(suffix='.cnf', delete=False) as f:
        cnf_file = f.name
    cnf.write_dimacs(cnf_file)

    t0 = time.time()
    try:
        r = subprocess.run(['kissat', '-q', cnf_file],
                          capture_output=True, text=True, timeout=timeout)
        elapsed = time.time() - t0
        if r.returncode == 10: return 'SAT', elapsed
        elif r.returncode == 20: return 'UNSAT', elapsed
        return f'rc{r.returncode}', elapsed
    except subprocess.TimeoutExpired:
        return 'TIMEOUT', timeout
    finally:
        os.unlink(cnf_file)


if __name__ == "__main__":
    candidates = [
        (0x44b49bc3, 0x80000000, "BEST"),
        (0x17149975, 0xffffffff, "PUBLISHED"),
        (0x9cfea9ce, 0x00000000, "fill_00"),
    ]

    timeout = int(sys.argv[1]) if len(sys.argv) > 1 else 300

    for m0, fill, label in candidates:
        print(f"\n{'#'*70}")
        print(f"# {label}")
        print(f"{'#'*70}")

        result = analyze_sequential(m0, fill)
        dw57, dw58, dw58_e = result[0], result[1], result[2]

        # Test 1: da57=0 + da58=0
        print(f"\n  TEST: da57=0 + da58=0 (timeout={timeout}s)")
        status, t = encode_doubly_constrained(m0, fill, dw57, dw58, timeout)
        print(f"  Result: {status} in {t:.1f}s")

        # Test 2: da57=0 + de58=0
        print(f"\n  TEST: da57=0 + de58=0 (timeout={timeout}s)")
        status2, t2 = encode_doubly_constrained(m0, fill, dw57, dw58_e, timeout)
        print(f"  Result: {status2} in {t2:.1f}s")
