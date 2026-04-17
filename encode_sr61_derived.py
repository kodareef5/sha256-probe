#!/usr/bin/env python3
"""
Derived sr=61 encoder: W2 computed from W1 via cascade offset.

KEY IMPROVEMENT: Instead of creating W2[57..59] as 96 free variables
and letting the solver discover the cascade relationship, this encoder
DERIVES W2 from W1 using the cascade offset at each round.

Free variables: only W1[57..59] = 96 bits (vs 192 in standard encoder)
Extra cost: ~384 auxiliary variables for offset computation

The solver's search space is halved: 2^96 instead of 2^192.
"""
import sys, os
sys.path.insert(0, '.')
enc = __import__('13_custom_cnf_encoder')
sigma0_py = enc.sigma0_py
sigma1_py = enc.sigma1_py
K = enc.K


def encode_sr61_derived(m0=0x17149975, fill=0xffffffff, kernel_bit=31):
    M1 = [m0] + [fill] * 15
    M2 = list(M1)
    M2[0] ^= (1 << kernel_bit)
    M2[9] ^= (1 << kernel_bit)

    state1, W1_pre = enc.precompute_state(M1)
    state2, W2_pre = enc.precompute_state(M2)
    assert state1[0] == state2[0], f"da[56] != 0"

    cnf = enc.CNFBuilder()

    s1 = tuple(cnf.const_word(v) for v in state1)
    s2 = tuple(cnf.const_word(v) for v in state2)

    # Only W1 is free (3 words × 32 bits = 96 free variables)
    w1_free = [cnf.free_word(f"W1_{57+i}") for i in range(3)]

    # Helper: compute a - b in the CNF (mod 2^32)
    def sub_word(A, B):
        """A - B = A + NOT(B) + 1."""
        not_B = [cnf.xor2(B[k], 1) for k in range(32)]
        neg_B = cnf.add_word(not_B, cnf.const_word(1))
        return cnf.add_word(A, neg_B)

    # Custom round function that separates T1_no_w from T1
    def round_split(state, Ki, Wi):
        """Run one round. Returns (new_state, t1_no_w).
        Uses correct shift register (a_new, a, b, c, e_new, e, f, g).
        T1 is computed as T1_no_w + Wi (sequential, not CSA)."""
        a, b, c, d, e, f, g, h = state
        K_word = cnf.const_word(Ki)

        sig1 = cnf.Sigma1(e)
        ch = cnf.Ch(e, f, g)

        # T1_no_w = h + Sigma1(e) + Ch(e,f,g) + K (4 sequential additions)
        t1_nw = cnf.add_word(h, sig1)
        t1_nw = cnf.add_word(t1_nw, ch)
        t1_nw = cnf.add_word(t1_nw, K_word)

        # T1 = T1_no_w + W
        t1 = cnf.add_word(t1_nw, Wi)

        # T2 = Sigma0(a) + Maj(a,b,c)
        sig0 = cnf.Sigma0(a)
        mj = cnf.Maj(a, b, c)
        t2 = cnf.add_word(sig0, mj)

        # New state with correct shift register
        a_new = cnf.add_word(t1, t2)
        e_new = cnf.add_word(d, t1)

        return (a_new, a, b, c, e_new, e, f, g), t1_nw

    # Standard round (for rounds where we don't need T1_no_w)
    def round_std(state, Ki, Wi):
        return cnf.sha256_round_correct(state, Ki, Wi)

    # === Process cascade rounds (57, 58, 59) with W2 derivation ===
    st1 = s1
    st2 = s2
    W2_derived = []

    for i in range(3):  # Rounds 57, 58, 59
        r = 57 + i

        # Compute T1_no_w for both messages
        _, t1_nw_1 = round_split(st1, K[r], cnf.const_word(0))  # dummy Wi
        _, t1_nw_2 = round_split(st2, K[r], cnf.const_word(0))  # dummy Wi

        # Actually, round_split with dummy Wi messes up the state.
        # I need T1_no_w WITHOUT advancing the state.
        # Let me compute T1_no_w directly instead.

        a1, b1, c1, d1, e1, f1, g1, h1 = st1
        a2, b2, c2, d2, e2, f2, g2, h2 = st2

        sig1_1 = cnf.Sigma1(e1); ch_1 = cnf.Ch(e1, f1, g1)
        sig1_2 = cnf.Sigma1(e2); ch_2 = cnf.Ch(e2, f2, g2)

        K_word = cnf.const_word(K[r])

        t1_nw_1 = cnf.add_word(cnf.add_word(cnf.add_word(h1, sig1_1), ch_1), K_word)
        t1_nw_2 = cnf.add_word(cnf.add_word(cnf.add_word(h2, sig1_2), ch_2), K_word)

        # T2 for each message (depends on a, b, c — may differ!)
        sig0_1 = cnf.Sigma0(a1); maj_1 = cnf.Maj(a1, b1, c1)
        t2_1 = cnf.add_word(sig0_1, maj_1)
        sig0_2 = cnf.Sigma0(a2); maj_2 = cnf.Maj(a2, b2, c2)
        t2_2 = cnf.add_word(sig0_2, maj_2)

        # Cascade: a_new_1 = a_new_2  →  T1_1 + T2_1 = T1_2 + T2_2
        # W2[r] = W1[r] + (T1_nw_1 - T1_nw_2) + (T2_1 - T2_2)
        offset_t1 = sub_word(t1_nw_1, t1_nw_2)
        offset_t2 = sub_word(t2_1, t2_2)
        full_offset = cnf.add_word(offset_t1, offset_t2)
        W2_r = cnf.add_word(w1_free[i], full_offset)
        W2_derived.append(W2_r)

        # Now compute full T1 for each message
        t1_1 = cnf.add_word(t1_nw_1, w1_free[i])
        t1_2 = cnf.add_word(t1_nw_2, W2_r)

        # T2 already computed above for cascade offset
        # Update states
        a_new_1 = cnf.add_word(t1_1, t2_1)
        e_new_1 = cnf.add_word(d1, t1_1)
        st1 = (a_new_1, a1, b1, c1, e_new_1, e1, f1, g1)

        a_new_2 = cnf.add_word(t1_2, t2_2)
        e_new_2 = cnf.add_word(d2, t1_2)
        st2 = (a_new_2, a2, b2, c2, e_new_2, e2, f2, g2)

    # === Schedule words (same structure as standard encoder) ===
    # W1[60] = sigma1(W1[58]) + W1_pre[53] + sigma0(W1_pre[45]) + W1_pre[44]
    w1_60 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_free[1]), cnf.const_word(W1_pre[53])),
        cnf.add_word(cnf.const_word(sigma0_py(W1_pre[45])), cnf.const_word(W1_pre[44]))
    )
    w2_60 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W2_derived[1]), cnf.const_word(W2_pre[53])),
        cnf.add_word(cnf.const_word(sigma0_py(W2_pre[45])), cnf.const_word(W2_pre[44]))
    )

    # W[61] = sigma1(W[59]) + ...
    w1_61 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_free[2]), cnf.const_word(W1_pre[54])),
        cnf.add_word(cnf.const_word(sigma0_py(W1_pre[46])), cnf.const_word(W1_pre[45]))
    )
    w2_61 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W2_derived[2]), cnf.const_word(W2_pre[54])),
        cnf.add_word(cnf.const_word(sigma0_py(W2_pre[46])), cnf.const_word(W2_pre[45]))
    )

    # W[62] = sigma1(W[60]) + ...
    w1_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_60), cnf.const_word(W1_pre[55])),
        cnf.add_word(cnf.const_word(sigma0_py(W1_pre[47])), cnf.const_word(W1_pre[46]))
    )
    w2_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_60), cnf.const_word(W2_pre[55])),
        cnf.add_word(cnf.const_word(sigma0_py(W2_pre[47])), cnf.const_word(W2_pre[46]))
    )

    # W[63] = sigma1(W[61]) + ...
    w1_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_61), cnf.const_word(W1_pre[56])),
        cnf.add_word(cnf.const_word(sigma0_py(W1_pre[48])), cnf.const_word(W1_pre[47]))
    )
    w2_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_61), cnf.const_word(W2_pre[56])),
        cnf.add_word(cnf.const_word(sigma0_py(W2_pre[48])), cnf.const_word(W2_pre[47]))
    )

    # Remaining schedule words as lists
    W1_sched = [w1_60, w1_61, w1_62, w1_63]
    W2_sched = [w2_60, w2_61, w2_62, w2_63]

    # === Rounds 60-63 (schedule-determined, standard processing) ===
    for i in range(4):
        st1 = round_std(st1, K[60 + i], W1_sched[i])
        st2 = round_std(st2, K[60 + i], W2_sched[i])

    # === Collision constraint ===
    for i in range(8):
        cnf.eq_word(st1[i], st2[i])

    return cnf


if __name__ == "__main__":
    m0 = int(sys.argv[1], 0) if len(sys.argv) > 1 else 0x17149975
    fill = int(sys.argv[2], 0) if len(sys.argv) > 2 else 0xffffffff
    kernel_bit = int(sys.argv[3]) if len(sys.argv) > 3 else 31

    print(f"Derived sr=61 encoder (W2 from W1)")
    print(f"  m0=0x{m0:08x}, fill=0x{fill:08x}, kernel_bit={kernel_bit}")

    cnf = encode_sr61_derived(m0, fill, kernel_bit)
    outf = f"/tmp/sr61_derived_m{m0:08x}_f{fill:08x}_bit{kernel_bit}.cnf"
    nv, nc = cnf.write_dimacs(outf)
    print(f"  CNF: {nv} vars, {nc} clauses -> {outf}")
    print(f"  Free variables: 96 (W1[57..59] only)")

    # Compare with standard
    from encode_sr61 import encode_sr61 as std_encode
    try:
        cnf_std = std_encode(m0, fill)
        nv_s, nc_s = cnf_std.write_dimacs("/dev/null")
        print(f"\nStandard: {nv_s} vars, {nc_s} clauses, 192 free vars")
        print(f"Derived:  {nv} vars, {nc} clauses, 96 free vars")
        print(f"Delta: {nv-nv_s:+d} vars, {nc-nc_s:+d} clauses, -96 free vars")
    except:
        pass
