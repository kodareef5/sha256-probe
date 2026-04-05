#!/usr/bin/env python3
"""
candidate_crossval.py — Cross-validate candidate quality at reduced widths.

For each candidate, tests sr=60 SAT at N=10,12,14 using the same fill pattern.
If dW[61] constant HW actually predicts difficulty, candidates with lower
dW[61]_C should solve faster or more reliably.

Usage: python3 candidate_crossval.py [timeout_per_instance]
"""

import sys, os, time, subprocess, tempfile, csv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
spec = __import__('50_precision_homotopy')
MiniSHA256 = spec.MiniSHA256
MiniCNFBuilder = spec.MiniCNFBuilder
K32 = spec.K32


# Candidates from the MITM scan, ranked by dW[61] constant
CANDIDATES = [
    (0x7a9cbbf8, 0x7fffffff, "dW61=12, NEW BEST"),
    (0x189b13c7, 0x80000000, "dW61=14"),
    (0x23b8329b, 0x0f0f0f0f, "dW61=14"),
    (0x2e05fe70, 0xf0f0f0f0, "dW61=14"),
    (0x9cfea9ce, 0x00000000, "dW61=15"),
    (0x17149975, 0xffffffff, "dW61=16, PUBLISHED"),
    (0x3f239926, 0xaaaaaaaa, "dW61=16"),
    (0x44b49bc3, 0x80000000, "dW61=18"),
]


def find_mini_candidate(N, m0_32, fill_32):
    """Find a da[56]=0 candidate at word width N matching the 32-bit candidate.
    Truncates M[0] and fill to N bits and scans nearby if exact truncation
    doesn't produce da[56]=0."""
    sha = MiniSHA256(N)
    MASK = sha.MASK
    MSB = sha.MSB

    fill = fill_32 & MASK
    m0_base = m0_32 & MASK

    # Try exact truncation first
    M1 = [m0_base] + [fill]*15
    M2 = list(M1); M2[0] = m0_base ^ MSB; M2[9] = fill ^ MSB
    s1, W1 = sha.compress(M1)
    s2, W2 = sha.compress(M2)
    if s1[0] == s2[0]:
        return m0_base, fill, s1, s2, W1, W2

    # Scan all M[0] with this fill
    for m0 in range(1 << N):
        M1 = [m0] + [fill]*15
        M2 = list(M1); M2[0] = m0 ^ MSB; M2[9] = fill ^ MSB
        s1, W1 = sha.compress(M1)
        s2, W2 = sha.compress(M2)
        if s1[0] == s2[0]:
            return m0, fill, s1, s2, W1, W2

    return None, None, None, None, None, None


def encode_and_solve(N, m0, fill, s1, s2, W1, W2, timeout=300):
    """Encode sr=60 at width N and solve with Kissat."""
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
    def s0w(x): return cnf.sigma0_w(x, ops['r_sig0'], ops['s_sig0'])

    # Build schedule tail
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

    with tempfile.NamedTemporaryFile(suffix='.cnf', delete=False) as f:
        cnf_file = f.name
    nv, nc = cnf.write_dimacs(cnf_file)

    t0 = time.time()
    try:
        r = subprocess.run(["kissat", "-q", cnf_file],
                          capture_output=True, text=True, timeout=timeout)
        elapsed = time.time() - t0
        if r.returncode == 10:
            return "SAT", elapsed, nv, nc
        elif r.returncode == 20:
            return "UNSAT", elapsed, nv, nc
        return "UNKNOWN", elapsed, nv, nc
    except subprocess.TimeoutExpired:
        return "TIMEOUT", timeout, nv, nc
    finally:
        os.unlink(cnf_file)


if __name__ == "__main__":
    timeout = int(sys.argv[1]) if len(sys.argv) > 1 else 120
    widths = [10, 12, 14]

    print(f"Candidate Cross-Validation at N={widths}, timeout={timeout}s")
    print(f"{'='*80}")
    print(f"{'M[0]':>12s} {'Fill':>12s} {'Label':>20s} | ", end="")
    for N in widths:
        print(f"{'N='+str(N):>12s} ", end="")
    print()
    print("-" * 80)

    for m0_32, fill_32, label in CANDIDATES:
        print(f"0x{m0_32:08x} 0x{fill_32:08x} {label:>20s} | ", end="", flush=True)
        for N in widths:
            m0, fill, s1, s2, W1, W2 = find_mini_candidate(N, m0_32, fill_32)
            if m0 is None:
                print(f"{'NO CAND':>12s} ", end="", flush=True)
                continue
            result, elapsed, nv, nc = encode_and_solve(N, m0, fill, s1, s2, W1, W2, timeout)
            if result == "SAT":
                print(f"{'SAT '+f'{elapsed:.1f}s':>12s} ", end="", flush=True)
            elif result == "TIMEOUT":
                print(f"{'TIMEOUT':>12s} ", end="", flush=True)
            else:
                print(f"{result+f' {elapsed:.1f}s':>12s} ", end="", flush=True)
        print()

    print(f"\n{'='*80}")
    print("If dW[61]_C predicts difficulty, top-ranked candidates should solve faster.")
