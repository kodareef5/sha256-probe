#!/usr/bin/env python3
"""
Cascade-augmented sr=61 encoder.

Adds intermediate cascade constraints (da=0 at rounds 57-59) that the
standard encoder leaves implicit. These give the SAT solver early pruning:
a branch that violates da=0 at round 57 is detected immediately rather
than after propagating through 7 rounds to the collision constraint.

The solution set is identical to encode_sr61.py — same variables, same
solutions. The only difference is 3*32*2 = 192 additional clauses for
the intermediate a-register equality constraints.

Usage: python3 encode_sr61_cascade.py [m0] [fill] [kernel_bit]
"""
import sys, os
sys.path.insert(0, '.')
enc = __import__('13_custom_cnf_encoder')
sigma0_py = enc.sigma0_py
sigma1_py = enc.sigma1_py
K = enc.K


def encode_sr61_cascade(m0=0x17149975, fill=0xffffffff, kernel_bit=31):
    """Encode sr=61 with intermediate cascade constraints."""
    M1 = [m0] + [fill] * 15
    M2 = list(M1)
    # Apply kernel: flip bit in M[0] and M[9]
    M2[0] ^= (1 << kernel_bit)
    M2[9] ^= (1 << kernel_bit)

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

    # Schedule: W[60] = sigma1(W[58]) + W[53] + sigma0(W[45]) + W[44]
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

    # Run 7 rounds INTERLEAVED for both messages
    # Add cascade constraint da=0 after rounds 57, 58, 59
    st1 = s1
    st2 = s2
    cascade_constraints = 0
    for i in range(7):
        st1 = cnf.sha256_round_correct(st1, K[57 + i], W1s[i])
        st2 = cnf.sha256_round_correct(st2, K[57 + i], W2s[i])
        if i < 3:  # Cascade: da=0 at rounds 57, 58, 59
            cnf.eq_word(st1[0], st2[0])  # a-register equality
            cascade_constraints += 1

    # Final collision constraint (all 8 registers)
    for i in range(8):
        cnf.eq_word(st1[i], st2[i])

    return cnf, cascade_constraints


if __name__ == "__main__":
    m0 = int(sys.argv[1], 0) if len(sys.argv) > 1 else 0x17149975
    fill = int(sys.argv[2], 0) if len(sys.argv) > 2 else 0xffffffff
    kernel_bit = int(sys.argv[3]) if len(sys.argv) > 3 else 31

    print(f"Cascade-augmented sr=61 encoder")
    print(f"  m0=0x{m0:08x}, fill=0x{fill:08x}, kernel_bit={kernel_bit}")

    cnf, n_cascade = encode_sr61_cascade(m0, fill, kernel_bit)
    outf = f"/tmp/sr61_cascade_m{m0:08x}_f{fill:08x}_bit{kernel_bit}.cnf"
    nv, nc = cnf.write_dimacs(outf)
    print(f"  Cascade constraints added: {n_cascade} rounds")
    print(f"  CNF: {nv} vars, {nc} clauses -> {outf}")

    # Also generate standard version for comparison
    from encode_sr61 import encode_sr61
    cnf_std = encode_sr61(m0, fill)
    outf_std = f"/tmp/sr61_standard_m{m0:08x}_f{fill:08x}.cnf"
    nv_std, nc_std = cnf_std.write_dimacs(outf_std)
    print(f"\nStandard sr=61 for comparison:")
    print(f"  CNF: {nv_std} vars, {nc_std} clauses -> {outf_std}")
    print(f"\nDelta: +{nv-nv_std} vars, +{nc-nc_std} clauses")
