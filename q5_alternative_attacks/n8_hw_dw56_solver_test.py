#!/usr/bin/env python3
"""
n8_hw_dw56_solver_test.py — Test the hw_dW56 hypothesis empirically at N=8.

Encodes sr=60 mini-SHA at N=8 for selected (m0, fill) candidates spanning
the hw_dW56 spectrum (0 through 7), runs Kissat on each, records solve time.

Expected:
- If hw_dW56 hypothesis is true: hw=0 candidates solve faster than hw=7
- If false: solve times uncorrelated with hw_dW56

Output: CSV ranking solve times by hw_dW56_mini.
"""

import sys, os, time, subprocess, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
import importlib.util
spec = importlib.util.spec_from_file_location('precision', '/root/sha256_probe/50_precision_homotopy.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
MiniSHA256 = mod.MiniSHA256
MiniCNFBuilder = mod.MiniCNFBuilder
K32 = mod.K32


def encode_n8_sr60(m0, fill, N=8):
    """Encode sr=60 for given (m0, fill) at given N. Returns CNF builder."""
    sha = MiniSHA256(N)
    MASK = sha.MASK
    MSB = sha.MSB

    M1 = [m0] + [fill] * 15
    M2 = list(M1)
    M2[0] ^= MSB
    M2[9] ^= MSB

    # Compute prefix
    K = sha.K
    IV = sha.IV
    rS0, rS1 = sha.r_Sig0, sha.r_Sig1
    rs0, ss0 = sha.r_sig0, sha.s_sig0
    rs1, ss1 = sha.r_sig1, sha.s_sig1

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

    W1 = schedule(M1)
    W2 = schedule(M2)
    s1 = compress(W1)
    s2 = compress(W2)

    assert s1[0] == s2[0], f"da[56] != 0: {s1[0]:#x} vs {s2[0]:#x}"

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

    # W[61] = sigma1(W[59]) + W[54] + sigma0(W[46]) + W[45]
    w1_61 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_free[2], rs1, ss1), cnf.const_word(W1[54])),
        cnf.add_word(cnf.const_word(sha.sigma0(W1[46])), cnf.const_word(W1[45]))
    )
    w2_61 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_free[2], rs1, ss1), cnf.const_word(W2[54])),
        cnf.add_word(cnf.const_word(sha.sigma0(W2[46])), cnf.const_word(W2[45]))
    )

    # W[62] = sigma1(W[60]) + W[55] + sigma0(W[47]) + W[46]
    w1_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_free[3], rs1, ss1), cnf.const_word(W1[55])),
        cnf.add_word(cnf.const_word(sha.sigma0(W1[47])), cnf.const_word(W1[46]))
    )
    w2_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_free[3], rs1, ss1), cnf.const_word(W2[55])),
        cnf.add_word(cnf.const_word(sha.sigma0(W2[47])), cnf.const_word(W2[46]))
    )

    # W[63] = sigma1(W[61]) + W[56] + sigma0(W[48]) + W[47]
    w1_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_61, rs1, ss1), cnf.const_word(W1[56])),
        cnf.add_word(cnf.const_word(sha.sigma0(W1[48])), cnf.const_word(W1[47]))
    )
    w2_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_61, rs1, ss1), cnf.const_word(W2[56])),
        cnf.add_word(cnf.const_word(sha.sigma0(W2[48])), cnf.const_word(W2[47]))
    )

    W1_sched = list(w1_free) + [w1_61, w1_62, w1_63]
    W2_sched = list(w2_free) + [w2_61, w2_62, w2_63]

    for i in range(7):
        st1 = cnf.sha256_round(st1, K_trunc[57+i], W1_sched[i], ops_params)
    for i in range(7):
        st2 = cnf.sha256_round(st2, K_trunc[57+i], W2_sched[i], ops_params)

    for i in range(8):
        cnf.eq_word(st1[i], st2[i])

    return cnf, W1, W2


def hw(x):
    return bin(x).count('1')


def solve_kissat(cnf, seeds=[1, 2, 3], timeout=60):
    """Run kissat with given seeds, return min solve time."""
    tmpdir = tempfile.mkdtemp()
    dimacs = os.path.join(tmpdir, "test.cnf")
    cnf.write_dimacs(dimacs)

    times = []
    results = []
    for seed in seeds:
        t0 = time.time()
        try:
            proc = subprocess.run(
                ['kissat', '--quiet', f'--seed={seed}', dimacs],
                capture_output=True, text=True, timeout=timeout
            )
            t = time.time() - t0
            rc = proc.returncode
            if rc == 10:
                results.append('SAT')
                times.append(t)
            elif rc == 20:
                results.append('UNSAT')
                times.append(t)
            else:
                results.append('UNKNOWN')
                times.append(t)
        except subprocess.TimeoutExpired:
            results.append('TIMEOUT')
            times.append(timeout)
    return results, times


def main():
    # All hw=0 and hw=7 candidates from earlier enumeration, plus hw=4 sample
    test_cases = [
        (0xca, 0x03, 0),
        (0xea, 0xb4, 0),
        (0xca, 0x39, 1),
        (0x83, 0x3b, 1),
        (0x2a, 0x55, 1),
        (0x66, 0x6b, 1),
        (0x51, 0x39, 7),
        (0xfd, 0x51, 7),
        (0xe2, 0x58, 7),
        (0xea, 0x81, 7),
        (0x33, 0xa0, 7),
    ]

    print(f"{'m0':<6} {'fill':<6} {'hw_dw56':<8} {'min_time':<10} {'results'}", flush=True)
    print("-" * 70, flush=True)

    for m0, fill, expected_hw in test_cases:
        try:
            cnf, W1, W2 = encode_n8_sr60(m0, fill)
            actual_hw = hw(W1[56] ^ W2[56])
            results, times = solve_kissat(cnf, seeds=[1, 2, 3], timeout=60)
            min_time = min(times)
            print(f"0x{m0:02x}   0x{fill:02x}   {actual_hw:<8} {min_time:<10.3f} {results}", flush=True)
        except Exception as e:
            print(f"0x{m0:02x}   0x{fill:02x}   ERROR: {e}", flush=True)


if __name__ == "__main__":
    main()
