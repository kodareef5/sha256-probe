#!/usr/bin/env python3
"""
Encode sr=61: 3 free words (W[57..59]), W[60..63] schedule-determined.

One more step beyond sr=60 toward full schedule compliance.
"""
import sys, os, tempfile
sys.path.insert(0, '.')
enc = __import__('13_custom_cnf_encoder')
sigma0_py = enc.sigma0_py
sigma1_py = enc.sigma1_py
K = enc.K


def encode_sr61(m0=0x17149975, fill=0xffffffff):
    M1 = [m0] + [fill] * 15
    M2 = list(M1)
    M2[0] ^= 0x80000000
    M2[9] ^= 0x80000000

    state1, W1_pre = enc.precompute_state(M1)
    state2, W2_pre = enc.precompute_state(M2)
    assert state1[0] == state2[0], f"da[56] != 0: {state1[0]:#x} vs {state2[0]:#x}"

    cnf = enc.CNFBuilder()

    s1 = tuple(cnf.const_word(v) for v in state1)
    s2 = tuple(cnf.const_word(v) for v in state2)

    # Only 3 free words: W[57], W[58], W[59]
    w1_free = [cnf.free_word(f"W1_{57+i}") for i in range(3)]
    w2_free = [cnf.free_word(f"W2_{57+i}") for i in range(3)]

    W1s = list(w1_free)
    W2s = list(w2_free)

    # W[60] = sigma1(W[58]) + W[53] + sigma0(W[45]) + W[44]
    # W[58] is free (index 1 in free array)
    w1_60 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_free[1]), cnf.const_word(W1_pre[53])),
        cnf.add_word(cnf.const_word(sigma0_py(W1_pre[45])), cnf.const_word(W1_pre[44]))
    )
    w2_60 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_free[1]), cnf.const_word(W2_pre[53])),
        cnf.add_word(cnf.const_word(sigma0_py(W2_pre[45])), cnf.const_word(W2_pre[44]))
    )
    W1s.append(w1_60)
    W2s.append(w2_60)

    # W[61] = sigma1(W[59]) + W[54] + sigma0(W[46]) + W[45]
    # W[59] is free (index 2 in free array)
    w1_61 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_free[2]), cnf.const_word(W1_pre[54])),
        cnf.add_word(cnf.const_word(sigma0_py(W1_pre[46])), cnf.const_word(W1_pre[45]))
    )
    w2_61 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_free[2]), cnf.const_word(W2_pre[54])),
        cnf.add_word(cnf.const_word(sigma0_py(W2_pre[46])), cnf.const_word(W2_pre[45]))
    )
    W1s.append(w1_61)
    W2s.append(w2_61)

    # W[62] = sigma1(W[60]) + W[55] + sigma0(W[47]) + W[46]
    # W[60] is the computed word (index 3 in W1s)
    w1_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W1s[3]), cnf.const_word(W1_pre[55])),
        cnf.add_word(cnf.const_word(sigma0_py(W1_pre[47])), cnf.const_word(W1_pre[46]))
    )
    w2_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W2s[3]), cnf.const_word(W2_pre[55])),
        cnf.add_word(cnf.const_word(sigma0_py(W2_pre[47])), cnf.const_word(W2_pre[46]))
    )
    W1s.append(w1_62)
    W2s.append(w2_62)

    # W[63] = sigma1(W[61]) + W[56] + sigma0(W[48]) + W[47]
    # W[61] is computed (index 4 in W1s)
    w1_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W1s[4]), cnf.const_word(W1_pre[56])),
        cnf.add_word(cnf.const_word(sigma0_py(W1_pre[48])), cnf.const_word(W1_pre[47]))
    )
    w2_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W2s[4]), cnf.const_word(W2_pre[56])),
        cnf.add_word(cnf.const_word(sigma0_py(W2_pre[48])), cnf.const_word(W2_pre[47]))
    )
    W1s.append(w1_63)
    W2s.append(w2_63)

    # Run 7 rounds for both messages
    st1 = s1
    for i in range(7):
        st1 = cnf.sha256_round_correct(st1, K[57 + i], W1s[i])
    st2 = s2
    for i in range(7):
        st2 = cnf.sha256_round_correct(st2, K[57 + i], W2s[i])

    for i in range(8):
        cnf.eq_word(st1[i], st2[i])

    return cnf


if __name__ == "__main__":
    m0 = int(sys.argv[1], 0) if len(sys.argv) > 1 else 0x17149975
    fill = int(sys.argv[2], 0) if len(sys.argv) > 2 else 0xffffffff

    cnf = encode_sr61(m0, fill)
    outf = f"/tmp/sr61_m{m0:08x}_f{fill:08x}.cnf"
    nv, nc = cnf.write_dimacs(outf)
    print(f"sr=61 CNF: {nv} vars, {nc} clauses -> {outf}")
