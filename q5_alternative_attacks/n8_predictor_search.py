#!/usr/bin/env python3
"""
n8_predictor_search.py — Search for a difficulty predictor at N=8.

Compute multiple algebraic metrics for ~50 N=8 candidates and run kissat
to get solve times. Then compute correlations with the metrics to find
which (if any) predicts sr=60 solver difficulty.

Metrics tested:
- hw_dW56_mini (refuted at N=8 but baseline)
- hw56_total (total state HW at round 56)
- hw_e56, hw_h56 (per-register HW)
- de57_err_mini (e-register noise under da57=0 constraint)
- hw_dW54, hw_dW55 (late-round window)
- boomerang_gap (W[57] dual-condition gap)
"""

import sys, os, time, subprocess, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
import importlib.util
spec = importlib.util.spec_from_file_location('precision', '/root/sha256_probe/50_precision_homotopy.py')
precision = importlib.util.module_from_spec(spec)
spec.loader.exec_module(precision)
spec2 = importlib.util.spec_from_file_location('n8_solver', '/root/sha256_probe/q5_alternative_attacks/n8_hw_dw56_solver_test.py')
n8_solver = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(n8_solver)

MiniSHA256 = precision.MiniSHA256
encode_n8_sr60 = n8_solver.encode_n8_sr60
solve_kissat = n8_solver.solve_kissat


def compute_metrics(m0, fill, N=8):
    sha = MiniSHA256(N)
    MASK = sha.MASK
    MSB = sha.MSB

    # Recompute the schedule and compression
    M1 = [m0] + [fill] * 15
    M2 = [m0 ^ MSB] + [fill] * 15
    M2[9] ^= MSB

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

    W1 = schedule(M1); W2 = schedule(M2)
    s1 = compress(W1); s2 = compress(W2)
    if s1[0] != s2[0]:
        return None

    def hw(x):
        return bin(x & MASK).count('1')

    state_hws = [hw(s1[i] ^ s2[i]) for i in range(8)]
    return {
        'm0': m0, 'fill': fill,
        'hw_dW54': hw(W1[54] ^ W2[54]),
        'hw_dW55': hw(W1[55] ^ W2[55]),
        'hw_dW56': hw(W1[56] ^ W2[56]),
        'hw_dW45': hw(W1[45] ^ W2[45]),
        'hw_dW44': hw(W1[44] ^ W2[44]),
        'hw_dW53': hw(W1[53] ^ W2[53]),
        'hw_state_56': sum(state_hws),
        'hw_a56': state_hws[0],
        'hw_b56': state_hws[1],
        'hw_c56': state_hws[2],
        'hw_d56': state_hws[3],
        'hw_e56': state_hws[4],
        'hw_f56': state_hws[5],
        'hw_g56': state_hws[6],
        'hw_h56': state_hws[7],
    }


def main():
    sha = MiniSHA256(8)
    # Find all candidates by enumeration
    cands = []
    for fill in range(256):
        for m0 in range(256):
            m = compute_metrics(m0, fill)
            if m is not None:
                cands.append(m)

    print(f"Found {len(cands)} N=8 da[56]=0 candidates", flush=True)

    # Sample 30 evenly across the cands list
    import random
    random.seed(42)
    sample = random.sample(cands, min(30, len(cands)))

    print(f"Testing {len(sample)} candidates with kissat...", flush=True)
    print(f"{'idx':<4} {'m0':<6} {'fill':<6} {'dW56':<5} {'dW55':<5} "
          f"{'dW54':<5} {'state':<6} {'h56':<5} {'time':<8} {'result'}", flush=True)
    print("-" * 80, flush=True)

    results = []
    for i, m in enumerate(sample):
        try:
            cnf, _, _ = encode_n8_sr60(m['m0'], m['fill'])
            res, times = solve_kissat(cnf, seeds=[1], timeout=20)
            t = times[0]
            r = res[0]
            m['time'] = t
            m['result'] = r
            results.append(m)
            print(f"{i+1:<4} 0x{m['m0']:02x}   0x{m['fill']:02x}   "
                  f"{m['hw_dW56']:<5} {m['hw_dW55']:<5} {m['hw_dW54']:<5} "
                  f"{m['hw_state_56']:<6} {m['hw_h56']:<5} "
                  f"{t:<8.2f} {r}", flush=True)
        except Exception as e:
            print(f"{i+1}: ERROR {e}", flush=True)

    # Compute correlations of each metric with time (excluding timeouts)
    valid = [r for r in results if r['result'] != 'TIMEOUT']
    if len(valid) < 5:
        print("\nToo few valid results for correlation")
        return

    print(f"\n=== Correlations (n={len(valid)}, excluding timeouts) ===")
    times = [r['time'] for r in valid]
    n = len(times)
    mt = sum(times) / n
    st = (sum((x - mt)**2 for x in times) / n) ** 0.5

    for key in ['hw_dW56', 'hw_dW55', 'hw_dW54', 'hw_dW53', 'hw_dW45', 'hw_dW44',
                'hw_state_56', 'hw_a56', 'hw_b56', 'hw_c56', 'hw_d56',
                'hw_e56', 'hw_f56', 'hw_g56', 'hw_h56']:
        vals = [r[key] for r in valid]
        mv = sum(vals) / n
        sv = (sum((v - mv)**2 for v in vals) / n) ** 0.5
        if sv == 0:
            r_corr = 0
        else:
            r_corr = sum((v - mv)*(t - mt) for v, t in zip(vals, times)) / (n * sv * st)
        print(f"  {key:<15} mean={mv:5.2f}  r={r_corr:+.4f}")


if __name__ == "__main__":
    main()
