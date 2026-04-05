#!/usr/bin/env python3
"""
Script 86: Parallel Precision Homotopy

For a given word width N, find multiple da[56]=0 candidates and solve
them ALL in parallel. First SAT wins. Uses all CPU cores.

Usage: python3 86_parallel_homotopy.py N [timeout] [max_candidates]
"""
import sys, os, time, subprocess, tempfile, signal

sys.path.insert(0, os.path.dirname(__file__) or '.')
spec = __import__('50_precision_homotopy')
MiniSHA256 = spec.MiniSHA256
MiniCNFBuilder = spec.MiniCNFBuilder
K32 = spec.K32


def find_all_candidates(N, max_candidates=20):
    """Find multiple da[56]=0 candidates at word width N."""
    sha = MiniSHA256(N)
    MASK = sha.MASK
    MSB = sha.MSB

    fills = [MASK, 0, MASK >> 1, MSB, 0x55 & MASK, 0xAA & MASK,
             0x33 & MASK, 0xCC & MASK, 0x0F & MASK, 0xF0 & MASK]

    candidates = []
    for fill in fills:
        for m0 in range(min(1 << N, 1 << 20)):
            M1 = [m0] + [fill] * 15
            M2 = list(M1)
            M2[0] = m0 ^ MSB
            M2[9] = fill ^ MSB

            s1, W1 = sha.compress(M1)
            s2, W2 = sha.compress(M2)

            if s1[0] == s2[0]:
                hw56 = sum(bin(s1[i] ^ s2[i]).count('1') for i in range(8))
                candidates.append((m0, fill, hw56, s1, s2, W1, W2))
                if len(candidates) >= max_candidates:
                    return candidates
    return candidates


def encode_candidate(N, s1, s2, W1, W2, cnf_file):
    """Encode sr=60 CNF for a candidate. Returns (n_vars, n_clauses)."""
    sha = MiniSHA256(N)
    MASK = sha.MASK

    ops_params = {
        'r_Sig0': sha.r_Sig0, 'r_Sig1': sha.r_Sig1,
        'r_sig0': sha.r_sig0, 's_sig0': sha.s_sig0,
        'r_sig1': sha.r_sig1, 's_sig1': sha.s_sig1,
    }
    K_trunc = [k & MASK for k in K32]

    cnf = MiniCNFBuilder(N)
    st1 = tuple(cnf.const_word(v) for v in s1)
    st2 = tuple(cnf.const_word(v) for v in s2)

    w1_free = [cnf.free_word(f"W1_{57 + i}") for i in range(4)]
    w2_free = [cnf.free_word(f"W2_{57 + i}") for i in range(4)]

    w1_61 = cnf.add_word(cnf.add_word(
        cnf.sigma1_w(w1_free[2], ops_params['r_sig1'], ops_params['s_sig1']),
        cnf.const_word(W1[54])),
        cnf.add_word(cnf.const_word(sha.sigma0(W1[46])), cnf.const_word(W1[45])))
    w2_61 = cnf.add_word(cnf.add_word(
        cnf.sigma1_w(w2_free[2], ops_params['r_sig1'], ops_params['s_sig1']),
        cnf.const_word(W2[54])),
        cnf.add_word(cnf.const_word(sha.sigma0(W2[46])), cnf.const_word(W2[45])))
    w1_62 = cnf.add_word(cnf.add_word(
        cnf.sigma1_w(w1_free[3], ops_params['r_sig1'], ops_params['s_sig1']),
        cnf.const_word(W1[55])),
        cnf.add_word(cnf.const_word(sha.sigma0(W1[47])), cnf.const_word(W1[46])))
    w2_62 = cnf.add_word(cnf.add_word(
        cnf.sigma1_w(w2_free[3], ops_params['r_sig1'], ops_params['s_sig1']),
        cnf.const_word(W2[55])),
        cnf.add_word(cnf.const_word(sha.sigma0(W2[47])), cnf.const_word(W2[46])))
    w1_63 = cnf.add_word(cnf.add_word(
        cnf.sigma1_w(w1_61, ops_params['r_sig1'], ops_params['s_sig1']),
        cnf.const_word(W1[56])),
        cnf.add_word(cnf.const_word(sha.sigma0(W1[48])), cnf.const_word(W1[47])))
    w2_63 = cnf.add_word(cnf.add_word(
        cnf.sigma1_w(w2_61, ops_params['r_sig1'], ops_params['s_sig1']),
        cnf.const_word(W2[56])),
        cnf.add_word(cnf.const_word(sha.sigma0(W2[48])), cnf.const_word(W2[47])))

    W1_sched = list(w1_free) + [w1_61, w1_62, w1_63]
    W2_sched = list(w2_free) + [w2_61, w2_62, w2_63]

    for i in range(7):
        st1 = cnf.sha256_round(st1, K_trunc[57 + i], W1_sched[i], ops_params)
    for i in range(7):
        st2 = cnf.sha256_round(st2, K_trunc[57 + i], W2_sched[i], ops_params)

    for i in range(8):
        cnf.eq_word(st1[i], st2[i])

    return cnf.write_dimacs(cnf_file)


if __name__ == "__main__":
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 19
    timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 3600
    max_cand = int(sys.argv[3]) if len(sys.argv) > 3 else 10

    print(f"Parallel Homotopy: N={N}, timeout={timeout}s, max_candidates={max_cand}", flush=True)

    # Step 1: Find candidates
    print(f"\nFinding candidates...", flush=True)
    t0 = time.time()
    candidates = find_all_candidates(N, max_cand)
    print(f"Found {len(candidates)} candidates in {time.time() - t0:.1f}s", flush=True)

    for i, (m0, fill, hw56, s1, s2, W1, W2) in enumerate(candidates):
        print(f"  [{i}] M[0]=0x{m0:x} fill=0x{fill:x} hw56={hw56}", flush=True)

    if not candidates:
        print("No candidates found!")
        sys.exit(1)

    # Step 2: Encode all CNFs
    tmpdir = tempfile.mkdtemp(prefix=f"par_N{N}_")
    cnf_files = []
    for i, (m0, fill, hw56, s1, s2, W1, W2) in enumerate(candidates):
        cnf_file = os.path.join(tmpdir, f"cand_{i}.cnf")
        nv, nc = encode_candidate(N, s1, s2, W1, W2, cnf_file)
        cnf_files.append(cnf_file)
        print(f"  [{i}] Encoded: {nv} vars, {nc} clauses", flush=True)

    # Step 3: Launch all solvers in parallel
    print(f"\nLaunching {len(candidates)} Kissat instances in parallel...", flush=True)
    procs = []
    for i, cnf_file in enumerate(cnf_files):
        p = subprocess.Popen(
            ["kissat", "-q", cnf_file],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        procs.append((i, p, time.time()))

    # Step 4: Wait for first SAT or all to finish
    winner = None
    while procs:
        for i, (idx, p, start) in enumerate(procs):
            ret = p.poll()
            if ret is not None:
                elapsed = time.time() - start
                m0, fill, hw56 = candidates[idx][:3]
                if ret == 10:
                    print(f"\n*** SAT *** Candidate [{idx}] M[0]=0x{m0:x} "
                          f"fill=0x{fill:x} in {elapsed:.1f}s", flush=True)
                    winner = (idx, elapsed)
                    # Kill remaining
                    for j, (jidx, jp, _) in enumerate(procs):
                        if j != i:
                            jp.kill()
                    procs = []
                    break
                elif ret == 20:
                    print(f"  [{idx}] UNSAT in {elapsed:.1f}s (M[0]=0x{m0:x})", flush=True)
                    procs.pop(i)
                    break
                else:
                    print(f"  [{idx}] ERROR rc={ret} in {elapsed:.1f}s", flush=True)
                    procs.pop(i)
                    break
            elif time.time() - start > timeout:
                p.kill()
                p.wait()
                m0 = candidates[idx][0]
                print(f"  [{idx}] TIMEOUT at {timeout}s (M[0]=0x{m0:x})", flush=True)
                procs.pop(i)
                break
        else:
            time.sleep(0.5)

    if winner:
        idx, elapsed = winner
        m0, fill, hw56 = candidates[idx][:3]
        print(f"\nRESULT: N={N} SAT in {elapsed:.1f}s "
              f"(candidate [{idx}] M[0]=0x{m0:x} fill=0x{fill:x} hw56={hw56})")
    else:
        print(f"\nRESULT: N={N} — all candidates UNSAT or TIMEOUT")
