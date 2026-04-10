#!/usr/bin/env python3
"""
encode_sr60_kernel.py — Parameterized sr=60 encoder with arbitrary kernel.

Default uses MSB (0x80000000) but accepts any kernel diff.
For non-MSB candidates discovered by the NMK scanner.

Usage: python3 encode_sr60_kernel.py <m0_hex> <fill_hex> <kernel_hex> [out_path]
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
enc = __import__('13_custom_cnf_encoder')
sigma0_py = enc.sigma0_py
sigma1_py = enc.sigma1_py
K = enc.K


def encode_sr60_kernel(m0, fill, kernel):
    """Encode sr=60 with custom kernel (XOR diff at M[0] and M[9])."""
    M1 = [m0] + [fill] * 15
    M2 = list(M1)
    M2[0] ^= kernel
    M2[9] ^= kernel

    state1, W1_pre = enc.precompute_state(M1)
    state2, W2_pre = enc.precompute_state(M2)
    assert state1[0] == state2[0], (
        f"da[56] != 0 for m0=0x{m0:08x}, fill=0x{fill:08x}, kernel=0x{kernel:08x}: "
        f"a1=0x{state1[0]:08x} vs a2=0x{state2[0]:08x}"
    )

    cnf = enc.CNFBuilder()
    s1 = tuple(cnf.const_word(v) for v in state1)
    s2 = tuple(cnf.const_word(v) for v in state2)

    w1_free = [cnf.free_word(f"W1_{57+i}") for i in range(4)]
    w2_free = [cnf.free_word(f"W2_{57+i}") for i in range(4)]

    W1s = list(w1_free)
    W2s = list(w2_free)

    w1_61 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_free[2]), cnf.const_word(W1_pre[54])),
        cnf.add_word(cnf.const_word(sigma0_py(W1_pre[46])), cnf.const_word(W1_pre[45]))
    )
    w2_61 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_free[2]), cnf.const_word(W2_pre[54])),
        cnf.add_word(cnf.const_word(sigma0_py(W2_pre[46])), cnf.const_word(W2_pre[45]))
    )
    W1s.append(w1_61); W2s.append(w2_61)

    w1_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W1s[3]), cnf.const_word(W1_pre[55])),
        cnf.add_word(cnf.const_word(sigma0_py(W1_pre[47])), cnf.const_word(W1_pre[46]))
    )
    w2_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W2s[3]), cnf.const_word(W2_pre[55])),
        cnf.add_word(cnf.const_word(sigma0_py(W2_pre[47])), cnf.const_word(W2_pre[46]))
    )
    W1s.append(w1_62); W2s.append(w2_62)

    w1_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W1s[4]), cnf.const_word(W1_pre[56])),
        cnf.add_word(cnf.const_word(sigma0_py(W1_pre[48])), cnf.const_word(W1_pre[47]))
    )
    w2_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W2s[4]), cnf.const_word(W2_pre[56])),
        cnf.add_word(cnf.const_word(sigma0_py(W2_pre[48])), cnf.const_word(W2_pre[47]))
    )
    W1s.append(w1_63); W2s.append(w2_63)

    st1 = s1
    for i in range(7):
        st1 = cnf.sha256_round_correct(st1, K[57+i], W1s[i])
    st2 = s2
    for i in range(7):
        st2 = cnf.sha256_round_correct(st2, K[57+i], W2s[i])

    for i in range(8):
        cnf.eq_word(st1[i], st2[i])

    return cnf


if __name__ == "__main__":
    m0 = int(sys.argv[1], 0)
    fill = int(sys.argv[2], 0)
    kernel = int(sys.argv[3], 0)
    outf = sys.argv[4] if len(sys.argv) > 4 else f"/tmp/sr60_m{m0:08x}_f{fill:08x}_k{kernel:08x}.cnf"

    print(f"Encoding sr=60 for m0=0x{m0:08x}, fill=0x{fill:08x}, kernel=0x{kernel:08x}")
    cnf = encode_sr60_kernel(m0, fill, kernel)
    nv, nc = cnf.write_dimacs(outf)
    print(f"sr=60 CNF: {nv} vars, {nc} clauses -> {outf}")
