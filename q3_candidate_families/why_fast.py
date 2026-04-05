#!/usr/bin/env python3
"""
why_fast.py — Investigate why some candidates solve faster at reduced widths.

Compares the fast candidate (0x44b49bc3, fill=0x80000000) against the slow
candidate (0x7a9cbbf8, fill=0x7fffffff) and the published candidate
(0x17149975, fill=0xffffffff) at reduced word widths.

Analyzes:
1. Round-56 state differential structure (which registers are zero/small)
2. dW[61] at reduced widths (not the 32-bit constant — the actual N-bit value)
3. Schedule word differentials (how much the schedule diverges)
4. Carry chain properties at N bits
5. CNF instance structure (vars, clauses, constant-fold ratio)
"""

import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
spec = __import__('50_precision_homotopy')
MiniSHA256 = spec.MiniSHA256
MiniCNFBuilder = spec.MiniCNFBuilder
K32 = spec.K32

MASK32 = 0xFFFFFFFF


def hw(x, N=32):
    return bin(x & ((1 << N) - 1)).count('1')


def find_candidate_at_N(N, fill_32):
    """Find all da[56]=0 candidates at width N with given fill."""
    sha = MiniSHA256(N)
    MASK = sha.MASK
    MSB = sha.MSB
    fill = fill_32 & MASK

    candidates = []
    for m0 in range(1 << min(N, 20)):  # cap at 2^20 for speed
        M1 = [m0] + [fill]*15
        M2 = list(M1); M2[0] = m0 ^ MSB; M2[9] = fill ^ MSB
        s1, W1 = sha.compress(M1)
        s2, W2 = sha.compress(M2)
        if s1[0] == s2[0]:
            candidates.append((m0, fill, s1, s2, W1, W2))
    return candidates


def analyze_state56(N, s1, s2, label=""):
    """Analyze the round-56 state differential."""
    sha = MiniSHA256(N)
    MASK = sha.MASK
    regs = ['a','b','c','d','e','f','g','h']

    print(f"  Round-56 state diff ({label}):")
    total_hw = 0
    zero_regs = 0
    for i in range(8):
        d = s1[i] ^ s2[i]
        h = hw(d, N)
        total_hw += h
        if d == 0:
            zero_regs += 1
            print(f"    d{regs[i]}[56] = 0  ** ZERO **")
        else:
            print(f"    d{regs[i]}[56] = {d:#0{N//4+3}x} (hw={h}/{N})")
    print(f"    Total HW = {total_hw}, Zero registers = {zero_regs}/8")
    return total_hw, zero_regs


def analyze_schedule_diff(N, W1, W2, label=""):
    """Analyze schedule word differentials."""
    sha = MiniSHA256(N)
    MASK = sha.MASK

    print(f"  Schedule differentials ({label}):")
    # Focus on the words that feed into the tail rounds
    key_words = [45, 46, 47, 48, 54, 55, 56]
    for i in key_words:
        d = (W1[i] ^ W2[i]) & MASK
        h = hw(d, N)
        print(f"    dW[{i:2d}] = {d:#0{N//4+3}x} (hw={h}/{N})")

    # Compute dW[61] constant at this width
    C = ((W1[54] - W2[54]) + (sha.sigma0(W1[46]) - sha.sigma0(W2[46])) + (W1[45] - W2[45])) & MASK
    print(f"    dW[61] constant C = {C:#0{N//4+3}x} (hw={hw(C, N)}/{N})")
    return hw(C, N)


def analyze_cnf_structure(N, m0, fill, s1, s2, W1, W2, label=""):
    """Encode and analyze CNF instance structure."""
    sha = MiniSHA256(N)
    MASK = sha.MASK
    ops = {'r_Sig0': sha.r_Sig0, 'r_Sig1': sha.r_Sig1,
           'r_sig0': sha.r_sig0, 's_sig0': sha.s_sig0,
           'r_sig1': sha.r_sig1, 's_sig1': sha.s_sig1}
    KT = [k & MASK for k in K32]

    cnf = MiniCNFBuilder(N)
    st1 = tuple(cnf.const_word(v) for v in s1)
    st2 = tuple(cnf.const_word(v) for v in s2)
    w1f = [cnf.free_word(f"W1_{57+i}") for i in range(4)]
    w2f = [cnf.free_word(f"W2_{57+i}") for i in range(4)]

    def s1w(x): return cnf.sigma1_w(x, ops['r_sig1'], ops['s_sig1'])

    w1_61 = cnf.add_word(cnf.add_word(s1w(w1f[2]), cnf.const_word(W1[54])),
                         cnf.add_word(cnf.const_word(sha.sigma0(W1[46])), cnf.const_word(W1[45])))
    w2_61 = cnf.add_word(cnf.add_word(s1w(w2f[2]), cnf.const_word(W2[54])),
                         cnf.add_word(cnf.const_word(sha.sigma0(W2[46])), cnf.const_word(W2[45])))
    w1_62 = cnf.add_word(cnf.add_word(s1w(w1f[3]), cnf.const_word(W1[55])),
                         cnf.add_word(cnf.const_word(sha.sigma0(W1[47])), cnf.const_word(W1[46])))
    w2_62 = cnf.add_word(cnf.add_word(s1w(w2f[3]), cnf.const_word(W2[55])),
                         cnf.add_word(cnf.const_word(sha.sigma0(W2[47])), cnf.const_word(W2[46])))
    w1_63 = cnf.add_word(cnf.add_word(s1w(w1_61), cnf.const_word(W1[56])),
                         cnf.add_word(cnf.const_word(sha.sigma0(W1[48])), cnf.const_word(W1[47])))
    w2_63 = cnf.add_word(cnf.add_word(s1w(w2_61), cnf.const_word(W2[56])),
                         cnf.add_word(cnf.const_word(sha.sigma0(W2[48])), cnf.const_word(W2[47])))

    W1s = list(w1f) + [w1_61, w1_62, w1_63]
    W2s = list(w2f) + [w2_61, w2_62, w2_63]

    for i in range(7):
        st1 = cnf.sha256_round(st1, KT[57+i], W1s[i], ops)
    for i in range(7):
        st2 = cnf.sha256_round(st2, KT[57+i], W2s[i], ops)
    for i in range(8):
        cnf.eq_word(st1[i], st2[i])

    nv = cnf.next_var - 1
    nc = len(cnf.clauses)
    cf = cnf.stats.get('const_fold', 0)
    total_gates = sum(cnf.stats.values())
    cf_ratio = cf / total_gates if total_gates > 0 else 0

    print(f"  CNF structure ({label}):")
    print(f"    Variables: {nv}, Clauses: {nc}")
    print(f"    Constant folds: {cf}/{total_gates} ({cf_ratio:.1%})")
    print(f"    Gate stats: {cnf.stats}")
    return nv, nc, cf_ratio


def compare_candidates(N):
    """Compare fast vs slow candidates at width N."""
    print(f"\n{'='*70}")
    print(f"COMPARISON AT N={N}")
    print(f"{'='*70}")

    test_cases = [
        (0x44b49bc3, 0x80000000, "FAST (dW61=18, N10=25s, N12=66s)"),
        (0x3f239926, 0xaaaaaaaa, "FAST (dW61=16, N10=24s)"),
        (0x9cfea9ce, 0x00000000, "MODERATE (dW61=15, N10=41s, N12=109s)"),
        (0x17149975, 0xffffffff, "PUBLISHED (dW61=16, N10=72s)"),
        (0x7a9cbbf8, 0x7fffffff, "SLOW (dW61=12, N10=123s)"),
    ]

    sha = MiniSHA256(N)
    MASK = sha.MASK
    MSB = sha.MSB

    results = []

    for m0_32, fill_32, label in test_cases:
        fill = fill_32 & MASK
        print(f"\n--- Candidate 0x{m0_32:08x} (fill=0x{fill_32:08x}) ---")
        print(f"    {label}")

        # Find candidate at this N
        cands = find_candidate_at_N(N, fill_32)
        if not cands:
            print(f"  NO da[56]=0 candidate found at N={N} with this fill")
            continue

        # Use first candidate found
        m0, fill_n, s1, s2, W1, W2 = cands[0]
        print(f"  Using mini-candidate: m0=0x{m0:x}, fill=0x{fill_n:x}")
        print(f"  ({len(cands)} total candidates found at this N)")

        hw56, zero_regs = analyze_state56(N, s1, s2, label)
        dw61_C_hw = analyze_schedule_diff(N, W1, W2, label)
        nv, nc, cf_ratio = analyze_cnf_structure(N, m0, fill_n, s1, s2, W1, W2, label)

        results.append({
            'label': label, 'm0': m0, 'fill': fill_n,
            'hw56': hw56, 'zero_regs': zero_regs,
            'dw61_C_hw': dw61_C_hw, 'n_cands': len(cands),
            'nv': nv, 'nc': nc, 'cf_ratio': cf_ratio
        })

    # Summary table
    print(f"\n{'='*70}")
    print(f"SUMMARY AT N={N}")
    print(f"{'='*70}")
    print(f"{'Label':>45s} | hw56 | zero | dW61 | cands | vars  | cls   | cf%")
    print("-" * 110)
    for r in results:
        print(f"{r['label']:>45s} | {r['hw56']:4d} | {r['zero_regs']:4d} | {r['dw61_C_hw']:4d} | {r['n_cands']:5d} | {r['nv']:5d} | {r['nc']:5d} | {r['cf_ratio']:.1%}")


if __name__ == "__main__":
    for N in [10, 12]:
        compare_candidates(N)
