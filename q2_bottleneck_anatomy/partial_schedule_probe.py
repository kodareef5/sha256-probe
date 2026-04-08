#!/usr/bin/env python3
"""
Partial schedule enforcement probe: find the exact phase transition
between sr=60 (SAT) and sr=61 (probably UNSAT) at N=32.

Instead of enforcing ALL 32 bits of W[60] via schedule, enforce only
the top k bits. Binary search for the maximum k that's still SAT.

This reveals exactly how much freedom sr=61 needs to be relaxed.
"""
import sys, os, subprocess, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

enc = __import__('13_custom_cnf_encoder')
sigma0_py = enc.sigma0_py
sigma1_py = enc.sigma1_py
K = enc.K


def encode_partial_sr61(m0=0x17149975, fill=0xffffffff, enforce_bits=16):
    """Encode sr=60 + partial W[60] schedule enforcement.

    enforce_bits: number of MSB bits of W[60] constrained to schedule value.
      0 = pure sr=60 (4 free words)
      32 = full sr=61 (3 free words, W[60] fully determined)
    """
    M1 = [m0] + [fill] * 15
    M2 = list(M1)
    M2[0] ^= 0x80000000
    M2[9] ^= 0x80000000

    state1, W1_pre = enc.precompute_state(M1)
    state2, W2_pre = enc.precompute_state(M2)
    assert state1[0] == state2[0], f"da[56] != 0"

    cnf = enc.CNFBuilder()

    s1 = tuple(cnf.const_word(v) for v in state1)
    s2 = tuple(cnf.const_word(v) for v in state2)

    # 4 free words like sr=60: W[57], W[58], W[59], W[60]
    w1_free = [cnf.free_word(f"W1_{57+i}") for i in range(4)]
    w2_free = [cnf.free_word(f"W2_{57+i}") for i in range(4)]

    W1s = list(w1_free)
    W2s = list(w2_free)

    # Build the schedule computation for W[60] (but don't replace the free word)
    # W[60] = sigma1(W[58]) + W[53] + sigma0(W[45]) + W[44]
    w1_60_sched = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_free[1]), cnf.const_word(W1_pre[53])),
        cnf.add_word(cnf.const_word(sigma0_py(W1_pre[45])), cnf.const_word(W1_pre[44]))
    )
    w2_60_sched = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_free[1]), cnf.const_word(W2_pre[53])),
        cnf.add_word(cnf.const_word(sigma0_py(W2_pre[45])), cnf.const_word(W2_pre[44]))
    )

    # Constrain top enforce_bits of free W[60] to match schedule W[60]
    # Bit 31 = MSB, bit 0 = LSB. Enforce from MSB down.
    for bit in range(31, 31 - enforce_bits, -1):
        if bit < 0:
            break
        # w1_free[3] is free W1[60], w1_60_sched is schedule W1[60]
        # Constrain: free_bit == sched_bit via implication clauses
        a1, b1 = w1_free[3][bit], w1_60_sched[bit]
        cnf.clauses.append([-a1, b1])
        cnf.clauses.append([a1, -b1])

        a2, b2 = w2_free[3][bit], w2_60_sched[bit]
        cnf.clauses.append([-a2, b2])
        cnf.clauses.append([a2, -b2])

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
    # Note: uses the FREE W[60] (partially constrained)
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

    # Run 7 rounds
    st1 = s1
    for i in range(7):
        st1 = cnf.sha256_round_correct(st1, K[57 + i], W1s[i])
    st2 = s2
    for i in range(7):
        st2 = cnf.sha256_round_correct(st2, K[57 + i], W2s[i])

    for i in range(8):
        cnf.eq_word(st1[i], st2[i])

    return cnf


def run_probe(enforce_bits, timeout=300, seed=5, m0=0x17149975, fill=0xffffffff):
    """Encode and solve with given enforcement level."""
    cnf = encode_partial_sr61(m0, fill, enforce_bits)
    outf = f"/tmp/partial_sr61_k{enforce_bits}.cnf"
    nv, nc = cnf.write_dimacs(outf)
    print(f"  k={enforce_bits}: {nv} vars, {nc} clauses", flush=True)

    result = subprocess.run(
        ["kissat", "--seed=" + str(seed), "-q", outf],
        capture_output=True, text=True, timeout=timeout
    )
    status = "UNKNOWN"
    for line in result.stdout.splitlines():
        if line.startswith("s "):
            status = line.split()[1]
    return status, nv, nc


def main():
    timeout = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    print(f"Partial Schedule Enforcement Probe (N=32)")
    print(f"Timeout: {timeout}s per solve")
    print(f"=" * 50)

    # Test key enforcement levels
    results = {}
    test_points = [0, 4, 8, 12, 16, 20, 24, 28, 32]

    for k in test_points:
        print(f"\nTesting k={k} (enforce top {k} bits of W[60])...", flush=True)
        t0 = time.time()
        try:
            status, nv, nc = run_probe(k, timeout=timeout)
            elapsed = time.time() - t0
            results[k] = (status, elapsed)
            print(f"  -> {status} in {elapsed:.1f}s", flush=True)

            # If we find UNSAT, try finer grain between last SAT and this
            if status == "UNSATISFIABLE" and k > 0:
                last_sat_k = max((kk for kk in results if results[kk][0] == "SATISFIABLE"), default=-1)
                if last_sat_k >= 0 and k - last_sat_k > 1:
                    print(f"\n  Refining between k={last_sat_k} (SAT) and k={k} (UNSAT)...", flush=True)
                    for kk in range(last_sat_k + 1, k):
                        print(f"\n  Testing k={kk}...", flush=True)
                        t0 = time.time()
                        try:
                            status2, nv2, nc2 = run_probe(kk, timeout=timeout)
                            elapsed2 = time.time() - t0
                            results[kk] = (status2, elapsed2)
                            print(f"  -> {status2} in {elapsed2:.1f}s", flush=True)
                        except subprocess.TimeoutExpired:
                            results[kk] = ("TIMEOUT", timeout)
                            print(f"  -> TIMEOUT ({timeout}s)", flush=True)

        except subprocess.TimeoutExpired:
            results[k] = ("TIMEOUT", timeout)
            elapsed = time.time() - t0
            print(f"  -> TIMEOUT ({timeout}s)", flush=True)

    # Summary
    print(f"\n{'='*50}")
    print(f"Results Summary")
    print(f"{'='*50}")
    print(f"{'k':>4} {'Status':<16} {'Time':>8}")
    print(f"-" * 30)
    for k in sorted(results.keys()):
        status, elapsed = results[k]
        marker = ""
        if status == "SATISFIABLE":
            marker = " <-- SAT"
        elif status == "UNSATISFIABLE":
            marker = " <-- UNSAT"
        print(f"{k:>4} {status:<16} {elapsed:>7.1f}s{marker}")

    # Find transition
    sat_max = max((k for k in results if results[k][0] == "SATISFIABLE"), default=-1)
    unsat_min = min((k for k in results if results[k][0] == "UNSATISFIABLE"), default=33)
    print(f"\nPhase transition: SAT up to k={sat_max}, UNSAT from k={unsat_min}")
    if unsat_min - sat_max <= 1:
        print(f"SHARP transition at k={unsat_min} bits!")
    else:
        print(f"Transition window: k={sat_max+1}..{unsat_min-1} (TIMEOUT zone)")


if __name__ == "__main__":
    main()
