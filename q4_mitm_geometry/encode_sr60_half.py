#!/usr/bin/env python3
"""
encode_sr60_half.py — sr=60.5 encoder: enforce MOST bits of W[60] via schedule,
leave specific bits free (partial schedule enforcement).

Tests macbook's critical pair hypothesis: at N=8, bits (4,5) are the critical
pair. At N=32, the predicted critical positions are near sigma1 rotations
(17, 19, >>10).

Usage: python3 encode_sr60_half.py <free_bits> [output.cnf]
  free_bits: comma-separated bit positions to leave free (e.g., "17,19")

The encoding is sr=60 PLUS partial enforcement of W[60]:
- W1[57..59] fully free (3 × 32 = 96 bits)
- W1[60] schedule-constrained EXCEPT for specified free bits
- W2[57..60] coupled via cascade chain
- W[61..63] fully schedule-constrained
- Equal final state required
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
enc = __import__('13_custom_cnf_encoder')
sigma0_py = enc.sigma0_py
sigma1_py = enc.sigma1_py
K = enc.K
MASK = 0xFFFFFFFF

def encode_sr60_half(m0, fill, kernel, free_bit_positions):
    """Encode sr=60 + partial W[60] schedule enforcement."""
    M1 = [m0] + [fill] * 15
    M2 = list(M1)
    M2[0] ^= kernel
    M2[9] ^= kernel

    state1, W1_pre = enc.precompute_state(M1)
    state2, W2_pre = enc.precompute_state(M2)
    assert state1[0] == state2[0], f"da[56] != 0"

    cnf = enc.CNFBuilder()
    s1 = tuple(cnf.const_word(v) for v in state1)
    s2 = tuple(cnf.const_word(v) for v in state2)

    # W1[57..59] fully free
    w1_57 = cnf.free_word("W1_57")
    w1_58 = cnf.free_word("W1_58")
    w1_59 = cnf.free_word("W1_59")
    w2_57 = cnf.free_word("W2_57")
    w2_58 = cnf.free_word("W2_58")
    w2_59 = cnf.free_word("W2_59")

    # W1[60]: schedule-computed with free bits at specified positions
    # Schedule: W[60] = sigma1(W[58]) + W[53] + sigma0(W[45]) + W[44]
    w1_60_sched = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_58), cnf.const_word(W1_pre[53])),
        cnf.add_word(cnf.const_word(sigma0_py(W1_pre[45])), cnf.const_word(W1_pre[44]))
    )
    w2_60_sched = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_58), cnf.const_word(W2_pre[53])),
        cnf.add_word(cnf.const_word(sigma0_py(W2_pre[45])), cnf.const_word(W2_pre[44]))
    )

    # Create W1[60] as schedule + error at free positions
    w1_60 = cnf.free_word("W1_60")
    w2_60 = cnf.free_word("W2_60")

    # Enforce non-free bits to match schedule using direct clause injection
    for bit in range(32):
        if bit not in free_bit_positions:
            # a <-> b: add clauses (-a, b) and (a, -b)
            a1, b1 = w1_60[bit], w1_60_sched[bit]
            a2, b2 = w2_60[bit], w2_60_sched[bit]
            # For M1 side
            if cnf._is_known(b1):
                val = cnf._get_val(b1)
                cnf.clauses.append([a1 if val else -a1])
            elif cnf._is_known(a1):
                val = cnf._get_val(a1)
                cnf.clauses.append([b1 if val else -b1])
            else:
                cnf.clauses.append([-a1, b1])
                cnf.clauses.append([a1, -b1])
            # For M2 side
            if cnf._is_known(b2):
                val = cnf._get_val(b2)
                cnf.clauses.append([a2 if val else -a2])
            elif cnf._is_known(a2):
                val = cnf._get_val(a2)
                cnf.clauses.append([b2 if val else -b2])
            else:
                cnf.clauses.append([-a2, b2])
                cnf.clauses.append([a2, -b2])

    # Build W[61..63] from schedule (fully constrained)
    w1_61 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_59), cnf.const_word(W1_pre[54])),
        cnf.add_word(cnf.const_word(sigma0_py(W1_pre[46])), cnf.const_word(W1_pre[45]))
    )
    w2_61 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_59), cnf.const_word(W2_pre[54])),
        cnf.add_word(cnf.const_word(sigma0_py(W2_pre[46])), cnf.const_word(W2_pre[45]))
    )
    w1_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_60), cnf.const_word(W1_pre[55])),
        cnf.add_word(cnf.const_word(sigma0_py(W1_pre[47])), cnf.const_word(W1_pre[46]))
    )
    w2_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_60), cnf.const_word(W2_pre[55])),
        cnf.add_word(cnf.const_word(sigma0_py(W2_pre[47])), cnf.const_word(W2_pre[46]))
    )
    w1_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_61), cnf.const_word(W1_pre[56])),
        cnf.add_word(cnf.const_word(sigma0_py(W1_pre[48])), cnf.const_word(W1_pre[47]))
    )
    w2_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_61), cnf.const_word(W2_pre[56])),
        cnf.add_word(cnf.const_word(sigma0_py(W2_pre[48])), cnf.const_word(W2_pre[47]))
    )

    W1s = [w1_57, w1_58, w1_59, w1_60, w1_61, w1_62, w1_63]
    W2s = [w2_57, w2_58, w2_59, w2_60, w2_61, w2_62, w2_63]

    # Run 7 rounds (57..63)
    st1 = s1
    for i in range(7):
        st1 = cnf.sha256_round_correct(st1, K[57+i], W1s[i])
    st2 = s2
    for i in range(7):
        st2 = cnf.sha256_round_correct(st2, K[57+i], W2s[i])

    # Equal final state
    for i in range(8):
        cnf.eq_word(st1[i], st2[i])

    return cnf


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: encode_sr60_half.py <free_bits> [output.cnf]")
        print("  free_bits: comma-separated, e.g., '17,19'")
        sys.exit(1)

    free_bits = [int(x) for x in sys.argv[1].split(",")]
    outf = sys.argv[2] if len(sys.argv) > 2 else f"/tmp/sr60half_free{'_'.join(map(str,free_bits))}.cnf"

    m0 = 0x17149975
    fill = 0xffffffff
    kernel = 0x80000000

    print(f"Encoding sr=60.5: free bits in W[60] = {free_bits}")
    print(f"  M[0]=0x{m0:08x}, fill=0x{fill:08x}, kernel=0x{kernel:08x}")
    cnf = encode_sr60_half(m0, fill, kernel, free_bits)
    nv, nc = cnf.write_dimacs(outf)
    print(f"CNF: {nv} vars, {nc} clauses -> {outf}")
