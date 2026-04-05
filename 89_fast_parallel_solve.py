#!/usr/bin/env python3
"""
Script 89: Fast Parallel Solve

Takes candidate CSV from fast_scan (C) and launches parallel Kissat.
Usage: ./fast_scan N 10 | python3 89_fast_parallel_solve.py N [timeout]
"""
import sys, os, csv, time, subprocess, tempfile, signal

sys.path.insert(0, os.path.dirname(__file__) or '.')
spec = __import__('50_precision_homotopy')
MiniSHA256 = spec.MiniSHA256
MiniCNFBuilder = spec.MiniCNFBuilder
K32 = spec.K32


def encode(N, m0, fill, timeout):
    sha = MiniSHA256(N)
    MASK = sha.MASK
    MSB = sha.MSB

    M1 = [m0] + [fill]*15
    M2 = list(M1); M2[0] = m0 ^ MSB; M2[9] = fill ^ MSB
    s1, W1 = sha.compress(M1)
    s2, W2 = sha.compress(M2)
    if s1[0] != s2[0]:
        return None, None

    ops = {'r_Sig0':sha.r_Sig0,'r_Sig1':sha.r_Sig1,'r_sig0':sha.r_sig0,
           's_sig0':sha.s_sig0,'r_sig1':sha.r_sig1,'s_sig1':sha.s_sig1}
    KT = [k & MASK for k in K32]

    cnf = MiniCNFBuilder(N)
    st1 = tuple(cnf.const_word(v) for v in s1)
    st2 = tuple(cnf.const_word(v) for v in s2)
    w1f = [cnf.free_word(f"W1_{57+i}") for i in range(4)]
    w2f = [cnf.free_word(f"W2_{57+i}") for i in range(4)]

    def s1w(x): return cnf.sigma1_w(x, ops['r_sig1'], ops['s_sig1'])
    def s0w(x): return cnf.sigma0_w(x, ops['r_sig0'], ops['s_sig0'])

    w1_61 = cnf.add_word(cnf.add_word(s1w(w1f[2]),cnf.const_word(W1[54])),
                         cnf.add_word(cnf.const_word(sha.sigma0(W1[46])),cnf.const_word(W1[45])))
    w2_61 = cnf.add_word(cnf.add_word(s1w(w2f[2]),cnf.const_word(W2[54])),
                         cnf.add_word(cnf.const_word(sha.sigma0(W2[46])),cnf.const_word(W2[45])))
    w1_62 = cnf.add_word(cnf.add_word(s1w(w1f[3]),cnf.const_word(W1[55])),
                         cnf.add_word(cnf.const_word(sha.sigma0(W1[47])),cnf.const_word(W1[46])))
    w2_62 = cnf.add_word(cnf.add_word(s1w(w2f[3]),cnf.const_word(W2[55])),
                         cnf.add_word(cnf.const_word(sha.sigma0(W2[47])),cnf.const_word(W2[46])))
    w1_63 = cnf.add_word(cnf.add_word(s1w(w1_61),cnf.const_word(W1[56])),
                         cnf.add_word(cnf.const_word(sha.sigma0(W1[48])),cnf.const_word(W1[47])))
    w2_63 = cnf.add_word(cnf.add_word(s1w(w2_61),cnf.const_word(W2[56])),
                         cnf.add_word(cnf.const_word(sha.sigma0(W2[48])),cnf.const_word(W2[47])))

    W1s = list(w1f)+[w1_61,w1_62,w1_63]
    W2s = list(w2f)+[w2_61,w2_62,w2_63]

    for i in range(7):
        st1 = cnf.sha256_round(st1, KT[57+i], W1s[i], ops)
    for i in range(7):
        st2 = cnf.sha256_round(st2, KT[57+i], W2s[i], ops)
    for i in range(8):
        cnf.eq_word(st1[i], st2[i])

    td = tempfile.mkdtemp(prefix=f"solve_N{N}_")
    f = os.path.join(td, f"m0_{m0:x}_fill_{fill:x}.cnf")
    nv, nc = cnf.write_dimacs(f)
    return f, (nv, nc)


if __name__ == "__main__":
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 7200

    # Read candidates from stdin (CSV from fast_scan)
    reader = csv.DictReader(sys.stdin)
    candidates = [(int(r['m0']), int(r['fill'])) for r in reader]

    print(f"N={N}, {len(candidates)} candidates, timeout={timeout}s", flush=True)

    # Encode all CNFs
    cnf_files = []
    for i, (m0, fill) in enumerate(candidates):
        t0 = time.time()
        f, info = encode(N, m0, fill, timeout)
        if f:
            cnf_files.append((i, m0, fill, f, info))
            print(f"  [{i}] M[0]=0x{m0:x} fill=0x{fill:x}: {info[0]} vars, {info[1]} cls ({time.time()-t0:.2f}s)", flush=True)

    # Launch all solvers
    print(f"\nLaunching {len(cnf_files)} solvers...", flush=True)
    procs = []
    for i, m0, fill, cnf_file, info in cnf_files:
        p = subprocess.Popen(["kissat", "-q", cnf_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        procs.append((i, m0, fill, p, time.time()))

    # Race
    while procs:
        for j, (i, m0, fill, p, t0) in enumerate(procs):
            ret = p.poll()
            if ret is not None:
                elapsed = time.time() - t0
                if ret == 10:
                    print(f"\n*** SAT *** [{i}] M[0]=0x{m0:x} fill=0x{fill:x} in {elapsed:.1f}s", flush=True)
                    for k, (_, _, _, p2, _) in enumerate(procs):
                        if k != j: p2.kill()
                    procs = []
                    print(f"RESULT: N={N} SAT in {elapsed:.1f}s")
                    sys.exit(0)
                elif ret == 20:
                    print(f"  [{i}] UNSAT in {elapsed:.1f}s", flush=True)
                else:
                    print(f"  [{i}] rc={ret} in {elapsed:.1f}s", flush=True)
                procs.pop(j)
                break
            elif time.time() - t0 > timeout:
                p.kill(); p.wait()
                print(f"  [{i}] TIMEOUT at {timeout}s", flush=True)
                procs.pop(j)
                break
        else:
            time.sleep(0.5)

    print(f"RESULT: N={N} all UNSAT/TIMEOUT")
