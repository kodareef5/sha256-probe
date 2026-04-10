#!/usr/bin/env python3
"""Single-bit enforcement map at N=32: test each W[60] bit individually."""
import sys, os, time, subprocess, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
enc = __import__('13_custom_cnf_encoder')

M1 = [0x17149975] + [0xffffffff]*15
M2 = list(M1); M2[0] ^= 0x80000000; M2[9] ^= 0x80000000
state1, W1_pre = enc.precompute_state(M1)
state2, W2_pre = enc.precompute_state(M2)

timeout = int(sys.argv[1]) if len(sys.argv) > 1 else 3600
seed = int(sys.argv[2]) if len(sys.argv) > 2 else 5

print(f"Single-Bit Enforcement Map at N=32 (timeout={timeout}s, seed={seed})", flush=True)

for enforce_bit in range(32):
    cnf = enc.CNFBuilder()
    s1 = tuple(cnf.const_word(v) for v in state1)
    s2 = tuple(cnf.const_word(v) for v in state2)
    w1f = [cnf.free_word(f"W1_{57+i}") for i in range(3)]
    w2f = [cnf.free_word(f"W2_{57+i}") for i in range(3)]

    # W[60] schedule-determined version
    w1_60s = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1f[1]), cnf.const_word(W1_pre[53])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[45])), cnf.const_word(W1_pre[44])))
    w2_60s = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2f[1]), cnf.const_word(W2_pre[53])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W2_pre[45])), cnf.const_word(W2_pre[44])))

    w1_60, w2_60 = [], []
    for bit in range(32):
        if bit == enforce_bit:
            w1_60.append(w1_60s[bit]); w2_60.append(w2_60s[bit])
        else:
            v1 = cnf.new_var(); cnf.free_var_names[v1] = f"W1_60[{bit}]"; w1_60.append(v1)
            v2 = cnf.new_var(); cnf.free_var_names[v2] = f"W2_60[{bit}]"; w2_60.append(v2)

    W1s = list(w1f) + [w1_60]; W2s = list(w2f) + [w2_60]
    w1_61 = cnf.add_word(cnf.add_word(cnf.sigma1_w(w1f[2]), cnf.const_word(W1_pre[54])),
                         cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[46])), cnf.const_word(W1_pre[45])))
    w2_61 = cnf.add_word(cnf.add_word(cnf.sigma1_w(w2f[2]), cnf.const_word(W2_pre[54])),
                         cnf.add_word(cnf.const_word(enc.sigma0_py(W2_pre[46])), cnf.const_word(W2_pre[45])))
    w1_62 = cnf.add_word(cnf.add_word(cnf.sigma1_w(w1_60), cnf.const_word(W1_pre[55])),
                         cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[47])), cnf.const_word(W1_pre[46])))
    w2_62 = cnf.add_word(cnf.add_word(cnf.sigma1_w(w2_60), cnf.const_word(W2_pre[55])),
                         cnf.add_word(cnf.const_word(enc.sigma0_py(W2_pre[47])), cnf.const_word(W2_pre[46])))
    w1_63 = cnf.add_word(cnf.add_word(cnf.sigma1_w(w1_61), cnf.const_word(W1_pre[56])),
                         cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[48])), cnf.const_word(W1_pre[47])))
    w2_63 = cnf.add_word(cnf.add_word(cnf.sigma1_w(w2_61), cnf.const_word(W2_pre[56])),
                         cnf.add_word(cnf.const_word(enc.sigma0_py(W2_pre[48])), cnf.const_word(W2_pre[47])))
    W1s.extend([w1_61, w1_62, w1_63]); W2s.extend([w2_61, w2_62, w2_63])

    st1, st2 = s1, s2
    for i in range(7):
        st1 = cnf.sha256_round_correct(st1, enc.K[57+i], W1s[i])
        st2 = cnf.sha256_round_correct(st2, enc.K[57+i], W2s[i])
    for i in range(8):
        cnf.eq_word(st1[i], st2[i])

    td = tempfile.mkdtemp(prefix=f"n32_bit{enforce_bit}_")
    cf = os.path.join(td, "sr60.5.cnf")
    nv, nc = cnf.write_dimacs(cf)

    t0 = time.time()
    try:
        r = subprocess.run(["kissat", "-q", f"--seed={seed}", cf],
                           capture_output=True, timeout=timeout)
        elapsed = time.time() - t0
        status = "SAT" if r.returncode == 10 else ("UNSAT" if r.returncode == 20 else f"rc={r.returncode}")
    except subprocess.TimeoutExpired:
        elapsed = timeout; status = "TIMEOUT"
    print(f"  Bit {enforce_bit:2d}: {status} in {elapsed:.0f}s", flush=True)

print("Done.", flush=True)
