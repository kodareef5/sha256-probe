#!/usr/bin/env python3
"""
near_collision_skip.py — Test which register is hardest to zero in sr=60 at N=8.

Macbook's near_collision.log showed:
- skip h (require only 7 of a,b,c,d,e,f,g): SAT in 12.7s
- skip d: TIMEOUT at 30s

Test all 8 "skip register X" configurations to rank the registers by
difficulty. The hardest one is the collision bottleneck.
"""

import sys, os, time, subprocess, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
import importlib.util
spec = importlib.util.spec_from_file_location('n8_solver',
    '/root/sha256_probe/q5_alternative_attacks/n8_hw_dw56_solver_test.py')
n8 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(n8)


def encode_n8_sr60_skip(m0, fill, skip_reg):
    """Encode N=8 sr=60 but don't enforce collision on the skip_reg-th register."""
    import importlib.util
    spec2 = importlib.util.spec_from_file_location('precision',
        '/root/sha256_probe/50_precision_homotopy.py')
    precision = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(precision)
    MiniSHA256 = precision.MiniSHA256
    MiniCNFBuilder = precision.MiniCNFBuilder
    K32 = precision.K32

    N = 8
    sha = MiniSHA256(N)
    MASK = sha.MASK
    MSB = sha.MSB
    K = sha.K
    IV = sha.IV
    rS0, rS1 = sha.r_Sig0, sha.r_Sig1
    rs0, ss0 = sha.r_sig0, sha.s_sig0
    rs1, ss1 = sha.r_sig1, sha.s_sig1

    M1 = [m0] + [fill] * 15
    M2 = list(M1); M2[0] ^= MSB; M2[9] ^= MSB

    def schedule(M):
        W = list(M) + [0] * 48
        for i in range(16, 57):
            x = W[i-2]
            s1v = (((x >> rs1[0]) | (x << (N - rs1[0]))) & MASK) ^ \
                  (((x >> rs1[1]) | (x << (N - rs1[1]))) & MASK) ^ \
                  ((x >> ss1) & MASK)
            y = W[i-15]
            s0v = (((y >> rs0[0]) | (y << (N - rs0[0]))) & MASK) ^ \
                  (((y >> rs0[1]) | (y << (N - rs0[1]))) & MASK) ^ \
                  ((y >> ss0) & MASK)
            W[i] = (s1v + W[i-7] + s0v + W[i-16]) & MASK
        return W

    def compress(W):
        a, b, c, d, e, f, g, h = IV
        for i in range(57):
            T1v = (((e >> rS1[0]) | (e << (N - rS1[0]))) & MASK) ^ \
                  (((e >> rS1[1]) | (e << (N - rS1[1]))) & MASK) ^ \
                  (((e >> rS1[2]) | (e << (N - rS1[2]))) & MASK)
            Chv = ((e & f) ^ ((~e & MASK) & g)) & MASK
            T1 = (h + T1v + Chv + K[i] + W[i]) & MASK
            T2v = (((a >> rS0[0]) | (a << (N - rS0[0]))) & MASK) ^ \
                  (((a >> rS0[1]) | (a << (N - rS0[1]))) & MASK) ^ \
                  (((a >> rS0[2]) | (a << (N - rS0[2]))) & MASK)
            Mjv = ((a & b) ^ (a & c) ^ (b & c)) & MASK
            T2 = (T2v + Mjv) & MASK
            h, g, f, e, d, c, b, a = g, f, e, (d + T1) & MASK, c, b, a, (T1 + T2) & MASK
        return (a, b, c, d, e, f, g, h)

    W1 = schedule(M1); W2 = schedule(M2)
    s1 = compress(W1); s2 = compress(W2)
    if s1[0] != s2[0]:
        return None

    K_trunc = [k & MASK for k in K32]
    cnf = MiniCNFBuilder(N)

    st1 = tuple(cnf.const_word(v) for v in s1)
    st2 = tuple(cnf.const_word(v) for v in s2)

    n_free = 4
    w1_free = [cnf.free_word(f"W1_{57+i}") for i in range(n_free)]
    w2_free = [cnf.free_word(f"W2_{57+i}") for i in range(n_free)]

    ops_params = {
        'r_Sig0': rS0, 'r_Sig1': rS1,
        'r_sig0': rs0, 's_sig0': ss0,
        'r_sig1': rs1, 's_sig1': ss1,
    }

    # W[61..63] schedule derived
    w1_61 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_free[2], rs1, ss1), cnf.const_word(W1[54])),
        cnf.add_word(cnf.const_word(sha.sigma0(W1[46])), cnf.const_word(W1[45])))
    w2_61 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_free[2], rs1, ss1), cnf.const_word(W2[54])),
        cnf.add_word(cnf.const_word(sha.sigma0(W2[46])), cnf.const_word(W2[45])))
    w1_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_free[3], rs1, ss1), cnf.const_word(W1[55])),
        cnf.add_word(cnf.const_word(sha.sigma0(W1[47])), cnf.const_word(W1[46])))
    w2_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_free[3], rs1, ss1), cnf.const_word(W2[55])),
        cnf.add_word(cnf.const_word(sha.sigma0(W2[47])), cnf.const_word(W2[46])))
    w1_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_61, rs1, ss1), cnf.const_word(W1[56])),
        cnf.add_word(cnf.const_word(sha.sigma0(W1[48])), cnf.const_word(W1[47])))
    w2_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_61, rs1, ss1), cnf.const_word(W2[56])),
        cnf.add_word(cnf.const_word(sha.sigma0(W2[48])), cnf.const_word(W2[47])))

    W1_sched = list(w1_free) + [w1_61, w1_62, w1_63]
    W2_sched = list(w2_free) + [w2_61, w2_62, w2_63]

    for i in range(7):
        st1 = cnf.sha256_round(st1, K_trunc[57+i], W1_sched[i], ops_params)
    for i in range(7):
        st2 = cnf.sha256_round(st2, K_trunc[57+i], W2_sched[i], ops_params)

    # Collision constraint: all except skip_reg
    for i in range(8):
        if i != skip_reg:
            cnf.eq_word(st1[i], st2[i])

    return cnf


def solve(cnf, timeout=60):
    tmpdir = tempfile.mkdtemp()
    dimacs = os.path.join(tmpdir, "test.cnf")
    cnf.write_dimacs(dimacs)
    t0 = time.time()
    try:
        proc = subprocess.run(['kissat', '--quiet', dimacs],
                              capture_output=True, text=True, timeout=timeout)
        t = time.time() - t0
        if proc.returncode == 10:
            return 'SAT', t
        elif proc.returncode == 20:
            return 'UNSAT', t
        else:
            return 'UNKNOWN', t
    except subprocess.TimeoutExpired:
        return 'TIMEOUT', timeout


def main():
    m0 = 0xca
    fill = 0x03
    regs = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']

    print(f"Near-collision test: skip each register, measure sr=60 N=8 time")
    print(f"Candidate: (m0=0x{m0:02x}, fill=0x{fill:02x})")
    print()
    print(f"{'skip':<8} {'result':<10} {'time':<10}")
    print("-" * 40)

    for skip in range(8):
        cnf = encode_n8_sr60_skip(m0, fill, skip)
        if cnf is None:
            print(f"{regs[skip]:<8} invalid candidate")
            continue
        result, t = solve(cnf, timeout=120)
        print(f"{regs[skip]:<8} {result:<10} {t:<10.2f}", flush=True)


if __name__ == "__main__":
    main()
