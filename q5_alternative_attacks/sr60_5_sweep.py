#!/usr/bin/env python3
"""sr=60.5 partial schedule compliance sweep. Usage: python3 sr60_5_sweep.py [N] [timeout]"""
import sys, os, time, subprocess, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

N = int(sys.argv[1]) if len(sys.argv) > 1 else 8
timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 600
seed = int(sys.argv[3]) if len(sys.argv) > 3 else 5

if N == 32:
    enc = __import__('13_custom_cnf_encoder')
    M1 = [0x17149975] + [0xffffffff]*15
    M2 = list(M1); M2[0] ^= 0x80000000; M2[9] ^= 0x80000000
    state1, W1_pre = enc.precompute_state(M1)
    state2, W2_pre = enc.precompute_state(M2)
    Builder = enc.CNFBuilder
    sigma0_fn = enc.sigma0_py

    def make_cnf(K):
        cnf = Builder()
        s1 = tuple(cnf.const_word(v) for v in state1)
        s2 = tuple(cnf.const_word(v) for v in state2)
        w1f = [cnf.free_word(f"W1_{57+i}") for i in range(3)]
        w2f = [cnf.free_word(f"W2_{57+i}") for i in range(3)]
        w1_60s = cnf.add_word(cnf.add_word(cnf.sigma1_w(w1f[1]), cnf.const_word(W1_pre[53])),
                              cnf.add_word(cnf.const_word(sigma0_fn(W1_pre[45])), cnf.const_word(W1_pre[44])))
        w2_60s = cnf.add_word(cnf.add_word(cnf.sigma1_w(w2f[1]), cnf.const_word(W2_pre[53])),
                              cnf.add_word(cnf.const_word(sigma0_fn(W2_pre[45])), cnf.const_word(W2_pre[44])))
        w1_60, w2_60 = [], []
        for bit in range(32):
            if bit >= (32 - K):
                w1_60.append(w1_60s[bit]); w2_60.append(w2_60s[bit])
            else:
                v1 = cnf.new_var(); cnf.free_var_names[v1] = f"W1_60[{bit}]"; w1_60.append(v1)
                v2 = cnf.new_var(); cnf.free_var_names[v2] = f"W2_60[{bit}]"; w2_60.append(v2)
        W1s = list(w1f) + [w1_60]; W2s = list(w2f) + [w2_60]
        w1_61 = cnf.add_word(cnf.add_word(cnf.sigma1_w(w1f[2]), cnf.const_word(W1_pre[54])),
                             cnf.add_word(cnf.const_word(sigma0_fn(W1_pre[46])), cnf.const_word(W1_pre[45])))
        w2_61 = cnf.add_word(cnf.add_word(cnf.sigma1_w(w2f[2]), cnf.const_word(W2_pre[54])),
                             cnf.add_word(cnf.const_word(sigma0_fn(W2_pre[46])), cnf.const_word(W2_pre[45])))
        w1_62 = cnf.add_word(cnf.add_word(cnf.sigma1_w(w1_60), cnf.const_word(W1_pre[55])),
                             cnf.add_word(cnf.const_word(sigma0_fn(W1_pre[47])), cnf.const_word(W1_pre[46])))
        w2_62 = cnf.add_word(cnf.add_word(cnf.sigma1_w(w2_60), cnf.const_word(W2_pre[55])),
                             cnf.add_word(cnf.const_word(sigma0_fn(W2_pre[47])), cnf.const_word(W2_pre[46])))
        w1_63 = cnf.add_word(cnf.add_word(cnf.sigma1_w(w1_61), cnf.const_word(W1_pre[56])),
                             cnf.add_word(cnf.const_word(sigma0_fn(W1_pre[48])), cnf.const_word(W1_pre[47])))
        w2_63 = cnf.add_word(cnf.add_word(cnf.sigma1_w(w2_61), cnf.const_word(W2_pre[56])),
                             cnf.add_word(cnf.const_word(sigma0_fn(W2_pre[48])), cnf.const_word(W2_pre[47])))
        W1s.extend([w1_61, w1_62, w1_63]); W2s.extend([w2_61, w2_62, w2_63])
        st1, st2 = s1, s2
        for i in range(7):
            st1 = cnf.sha256_round_correct(st1, enc.K[57+i], W1s[i])
            st2 = cnf.sha256_round_correct(st2, enc.K[57+i], W2s[i])
        for i in range(8):
            cnf.eq_word(st1[i], st2[i])
        return cnf
else:
    spec = __import__('50_precision_homotopy')
    sha = spec.MiniSHA256(N)
    MASK_N = sha.MASK; MSB = sha.MSB
    K32 = spec.K32; KT = [k & MASK_N for k in K32]
    m0, s1, s2, W1_pre, W2_pre = sha.find_m0()
    if m0 is None:
        print(f"No candidate at N={N}"); sys.exit(1)
    ops = {'r_Sig0': sha.r_Sig0, 'r_Sig1': sha.r_Sig1, 'r_sig0': sha.r_sig0,
           's_sig0': sha.s_sig0, 'r_sig1': sha.r_sig1, 's_sig1': sha.s_sig1}

    def make_cnf(K):
        cnf = spec.MiniCNFBuilder(N)
        st1 = tuple(cnf.const_word(v) for v in s1)
        st2 = tuple(cnf.const_word(v) for v in s2)
        w1f = [cnf.free_word(f"W1_{57+i}") for i in range(3)]
        w2f = [cnf.free_word(f"W2_{57+i}") for i in range(3)]
        def sw(x): return cnf.sigma1_w(x, ops['r_sig1'], ops['s_sig1'])
        w1_60s = cnf.add_word(cnf.add_word(sw(w1f[1]), cnf.const_word(W1_pre[53])),
                              cnf.add_word(cnf.const_word(sha.sigma0(W1_pre[45])), cnf.const_word(W1_pre[44])))
        w2_60s = cnf.add_word(cnf.add_word(sw(w2f[1]), cnf.const_word(W2_pre[53])),
                              cnf.add_word(cnf.const_word(sha.sigma0(W2_pre[45])), cnf.const_word(W2_pre[44])))
        w1_60, w2_60 = [], []
        for bit in range(N):
            if bit >= (N - K):
                w1_60.append(w1_60s[bit]); w2_60.append(w2_60s[bit])
            else:
                w1_60.append(cnf.new_var()); w2_60.append(cnf.new_var())
        W1s = list(w1f) + [w1_60]; W2s = list(w2f) + [w2_60]
        w1_61 = cnf.add_word(cnf.add_word(sw(w1f[2]), cnf.const_word(W1_pre[54])),
                             cnf.add_word(cnf.const_word(sha.sigma0(W1_pre[46])), cnf.const_word(W1_pre[45])))
        w2_61 = cnf.add_word(cnf.add_word(sw(w2f[2]), cnf.const_word(W2_pre[54])),
                             cnf.add_word(cnf.const_word(sha.sigma0(W2_pre[46])), cnf.const_word(W2_pre[45])))
        w1_62 = cnf.add_word(cnf.add_word(sw(W1s[3]), cnf.const_word(W1_pre[55])),
                             cnf.add_word(cnf.const_word(sha.sigma0(W1_pre[47])), cnf.const_word(W1_pre[46])))
        w2_62 = cnf.add_word(cnf.add_word(sw(W2s[3]), cnf.const_word(W2_pre[55])),
                             cnf.add_word(cnf.const_word(sha.sigma0(W2_pre[47])), cnf.const_word(W2_pre[46])))
        w1_63 = cnf.add_word(cnf.add_word(sw(w1_61), cnf.const_word(W1_pre[56])),
                             cnf.add_word(cnf.const_word(sha.sigma0(W1_pre[48])), cnf.const_word(W1_pre[47])))
        w2_63 = cnf.add_word(cnf.add_word(sw(w2_61), cnf.const_word(W2_pre[56])),
                             cnf.add_word(cnf.const_word(sha.sigma0(W2_pre[48])), cnf.const_word(W2_pre[47])))
        W1s.extend([w1_61, w1_62, w1_63]); W2s.extend([w2_61, w2_62, w2_63])
        for i in range(7):
            st1 = cnf.sha256_round(st1, KT[57+i], W1s[i], ops)
            st2 = cnf.sha256_round(st2, KT[57+i], W2s[i], ops)
        for i in range(8):
            cnf.eq_word(st1[i], st2[i])
        return cnf

print(f"sr=60.5 Phase Transition at N={N} (timeout={timeout}s, seed={seed})", flush=True)
step = max(1, N // 8) if N <= 10 else 4
for K in range(0, N + 1, step if step > 0 else 1):
    cnf = make_cnf(K)
    td = tempfile.mkdtemp(prefix=f"sr605_N{N}_K{K}_")
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
    print(f"  K={K:2d}/{N}: {nv}v {nc}c -> {status} in {elapsed:.0f}s", flush=True)
print("Done.", flush=True)
