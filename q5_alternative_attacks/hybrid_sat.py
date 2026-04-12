#!/usr/bin/env python3
"""
Hybrid Cascade + SAT Collision Finder

Enumerate W1[57] (2^N values). For each:
  1. Compute cascade W2[57]
  2. Run round 57 for both messages → state57
  3. Encode rounds 58-63 as a SAT problem with 3N free bits (W1[58..60])
  4. Call Kissat to solve
  5. If SAT: extract collision

At N=8: 256 SAT instances × ~1s each = ~4 minutes
At N=10: 1024 × ~2s = ~30 minutes
At N=12: 4096 × ~5s = ~6 hours

Compare: cascade DP at N=12 = 19 days.

Usage: python3 hybrid_sat.py [N] [timeout_per_instance]
"""
import sys, os, time, subprocess, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

N = int(sys.argv[1]) if len(sys.argv) > 1 else 8
timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 60

if N == 32:
    enc = __import__('13_custom_cnf_encoder')
    M1 = [0x17149975] + [0xffffffff]*15
    M2 = list(M1); M2[0] ^= 0x80000000; M2[9] ^= 0x80000000
    state1_init, W1_pre = enc.precompute_state(M1)
    state2_init, W2_pre = enc.precompute_state(M2)
    Builder = enc.CNFBuilder
    sigma0_fn = enc.sigma0_py
    K_vals = enc.K
    def make_round(s, k, w):
        T1 = (s[7]+enc.Sigma1_py(s[4])+enc.Ch_py(s[4],s[5],s[6])+k+w) & 0xffffffff
        T2 = (enc.Sigma0_py(s[0])+enc.Maj_py(s[0],s[1],s[2])) & 0xffffffff
        return ((T1+T2)&0xffffffff, s[0],s[1],s[2], (s[3]+T1)&0xffffffff, s[4],s[5],s[6])
    def find_w2(s1, s2, rnd, w1):
        r1=(s1[7]+enc.Sigma1_py(s1[4])+enc.Ch_py(s1[4],s1[5],s1[6])+K_vals[rnd])&0xffffffff
        r2=(s2[7]+enc.Sigma1_py(s2[4])+enc.Ch_py(s2[4],s2[5],s2[6])+K_vals[rnd])&0xffffffff
        t21=(enc.Sigma0_py(s1[0])+enc.Maj_py(s1[0],s1[1],s1[2]))&0xffffffff
        t22=(enc.Sigma0_py(s2[0])+enc.Maj_py(s2[0],s2[1],s2[2]))&0xffffffff
        return (w1+r1-r2+t21-t22)&0xffffffff
else:
    spec = __import__('50_precision_homotopy')
    sha = spec.MiniSHA256(N)
    MASK = sha.MASK; MSB = sha.MSB
    K_vals = sha.K
    result = sha.find_m0()
    if result[0] is None:
        print(f"No candidate at N={N}"); sys.exit(1)
    m0, s1_init, s2_init, W1_pre, W2_pre = result
    state1_init, state2_init = s1_init, s2_init
    ops = {'r_Sig0': sha.r_Sig0, 'r_Sig1': sha.r_Sig1, 'r_sig0': sha.r_sig0,
           's_sig0': sha.s_sig0, 'r_sig1': sha.r_sig1, 's_sig1': sha.s_sig1}
    Builder = lambda: spec.MiniCNFBuilder(N)

    def make_round(s, k, w):
        MASK_L = sha.MASK
        T1 = (s[7]+sha.Sigma1(s[4])+sha.ch(s[4],s[5],s[6])+k+w) & MASK_L
        T2 = (sha.Sigma0(s[0])+sha.maj(s[0],s[1],s[2])) & MASK_L
        return ((T1+T2)&MASK_L, s[0],s[1],s[2], (s[3]+T1)&MASK_L, s[4],s[5],s[6])

    def find_w2(s1, s2, rnd, w1):
        MASK_L = sha.MASK
        r1=(s1[7]+sha.Sigma1(s1[4])+sha.ch(s1[4],s1[5],s1[6])+K_vals[rnd])&MASK_L
        r2=(s2[7]+sha.Sigma1(s2[4])+sha.ch(s2[4],s2[5],s2[6])+K_vals[rnd])&MASK_L
        t21=(sha.Sigma0(s1[0])+sha.maj(s1[0],s1[1],s1[2]))&MASK_L
        t22=(sha.Sigma0(s2[0])+sha.maj(s2[0],s2[1],s2[2]))&MASK_L
        return (w1+r1-r2+t21-t22)&MASK_L

MASK_N = (1 << N) - 1 if N < 32 else 0xFFFFFFFF

print(f"Hybrid Cascade + SAT at N={N}")
print(f"Outer loop: W1[57] = 0..{(1<<N)-1} ({1<<N} values)")
print(f"Inner: SAT with {3*N} free bits (W1[58..60])")
print(f"Timeout per instance: {timeout}s")
print(flush=True)

t0 = time.time()
n_collisions = 0
n_sat = 0
n_unsat = 0
n_timeout = 0

for w1_57 in range(1 << N):
    # Compute state after round 57 for both messages
    s1 = tuple(state1_init)
    s2 = tuple(state2_init)
    w2_57 = find_w2(s1, s2, 57, w1_57)
    s1 = make_round(s1, K_vals[57], w1_57)
    s2 = make_round(s2, K_vals[57], w2_57)

    # Encode rounds 58-63 as SAT with W1[58..60] free
    # State57 is now constant for this W1[57] value
    if N < 32:
        cnf = spec.MiniCNFBuilder(N)
        # Standard sr=60 encoding from initial state, but W1[57] fixed
        st1 = tuple(cnf.const_word(v) for v in state1_init)
        st2 = tuple(cnf.const_word(v) for v in state2_init)

        # W[57] = constant, W[58..60] = free
        w1_57c = cnf.const_word(w1_57)
        w2_57c = cnf.const_word(w2_57)
        w1f = [cnf.free_word(f"W1_{58+i}") for i in range(3)]
        w2f = [cnf.free_word(f"W2_{58+i}") for i in range(3)]
        W1s = [w1_57c] + list(w1f)
        W2s = [w2_57c] + list(w2f)

        def sw(x): return cnf.sigma1_w(x, ops['r_sig1'], ops['s_sig1'])
        # Schedule
        W1s.append(cnf.add_word(cnf.add_word(sw(W1s[2]),cnf.const_word(W1_pre[54])),
                   cnf.add_word(cnf.const_word(sha.sigma0(W1_pre[46])),cnf.const_word(W1_pre[45]))))
        W2s.append(cnf.add_word(cnf.add_word(sw(W2s[2]),cnf.const_word(W2_pre[54])),
                   cnf.add_word(cnf.const_word(sha.sigma0(W2_pre[46])),cnf.const_word(W2_pre[45]))))
        W1s.append(cnf.add_word(cnf.add_word(sw(W1s[3]),cnf.const_word(W1_pre[55])),
                   cnf.add_word(cnf.const_word(sha.sigma0(W1_pre[47])),cnf.const_word(W1_pre[46]))))
        W2s.append(cnf.add_word(cnf.add_word(sw(W2s[3]),cnf.const_word(W2_pre[55])),
                   cnf.add_word(cnf.const_word(sha.sigma0(W2_pre[47])),cnf.const_word(W2_pre[46]))))
        W1s.append(cnf.add_word(cnf.add_word(sw(W1s[4]),cnf.const_word(W1_pre[56])),
                   cnf.add_word(cnf.const_word(sha.sigma0(W1_pre[48])),cnf.const_word(W1_pre[47]))))
        W2s.append(cnf.add_word(cnf.add_word(sw(W2s[4]),cnf.const_word(W2_pre[56])),
                   cnf.add_word(cnf.const_word(sha.sigma0(W2_pre[48])),cnf.const_word(W2_pre[47]))))

        # 7 rounds from initial state
        for i in range(7):
            st1 = cnf.sha256_round(st1, K_vals[57+i] & MASK_N, W1s[i], ops)
            st2 = cnf.sha256_round(st2, K_vals[57+i] & MASK_N, W2s[i], ops)
        for i in range(8):
            cnf.eq_word(st1[i], st2[i])

        td = tempfile.mkdtemp(prefix=f'hyb_N{N}_w{w1_57:x}_')
        cf = os.path.join(td, 'sr60.cnf')
        nv, nc = cnf.write_dimacs(cf)

        try:
            r = subprocess.run(['kissat', '-q', f'--seed=1', cf],
                               capture_output=True, timeout=timeout)
            if r.returncode == 10:
                n_sat += 1
                # Extract W1[58..60] from solution
                lits = []
                for line in r.stdout.decode().split('\n'):
                    if line.startswith('v '):
                        lits.extend(int(x) for x in line[2:].split() if x != '0')
                w1_vals = [0]*3
                w2_vals = [0]*3
                for lit in lits:
                    var = abs(lit); val = 1 if lit > 0 else 0
                    for wi in range(3):
                        for bit in range(N):
                            if var == w1f[wi][bit]: w1_vals[wi] |= (val << bit)
                            if var == w2f[wi][bit]: w2_vals[wi] |= (val << bit)

                # Verify: run brute force from INITIAL state
                W1_full = [w1_57, w1_vals[0], w1_vals[1], w1_vals[2]]
                W2_full = [w2_57, w2_vals[0], w2_vals[1], w2_vals[2]]
                W1s_v = list(W1_full)
                W2s_v = list(W2_full)
                W1s_v.append((sha.sigma1(W1s_v[2])+W1_pre[54]+sha.sigma0(W1_pre[46])+W1_pre[45])&MASK_N)
                W2s_v.append((sha.sigma1(W2s_v[2])+W2_pre[54]+sha.sigma0(W2_pre[46])+W2_pre[45])&MASK_N)
                W1s_v.append((sha.sigma1(W1s_v[3])+W1_pre[55]+sha.sigma0(W1_pre[47])+W1_pre[46])&MASK_N)
                W2s_v.append((sha.sigma1(W2s_v[3])+W2_pre[55]+sha.sigma0(W2_pre[47])+W2_pre[46])&MASK_N)
                W1s_v.append((sha.sigma1(W1s_v[4])+W1_pre[56]+sha.sigma0(W1_pre[48])+W1_pre[47])&MASK_N)
                W2s_v.append((sha.sigma1(W2s_v[4])+W2_pre[56]+sha.sigma0(W2_pre[48])+W2_pre[47])&MASK_N)

                a1,b1,c1,d1,e1,f1,g1,h1 = state1_init
                a2,b2,c2,d2,e2,f2,g2,h2 = state2_init
                for i in range(7):
                    T1a=(h1+sha.Sigma1(e1)+sha.ch(e1,f1,g1)+K_vals[57+i]+W1s_v[i])&MASK_N
                    T2a=(sha.Sigma0(a1)+sha.maj(a1,b1,c1))&MASK_N
                    h1,g1,f1,e1,d1,c1,b1,a1=g1,f1,e1,(d1+T1a)&MASK_N,c1,b1,a1,(T1a+T2a)&MASK_N
                    T1b=(h2+sha.Sigma1(e2)+sha.ch(e2,f2,g2)+K_vals[57+i]+W2s_v[i])&MASK_N
                    T2b=(sha.Sigma0(a2)+sha.maj(a2,b2,c2))&MASK_N
                    h2,g2,f2,e2,d2,c2,b2,a2=g2,f2,e2,(d2+T1b)&MASK_N,c2,b2,a2,(T1b+T2b)&MASK_N

                ok = all(v1==v2 for v1,v2 in zip([a1,b1,c1,d1,e1,f1,g1,h1],[a2,b2,c2,d2,e2,f2,g2,h2]))
                if ok:
                    n_collisions += 1
                    if n_collisions <= 5:
                        print(f"  COLLISION #{n_collisions}: W1[57..60]="
                              f"[{w1_57:x},{w1_vals[0]:x},{w1_vals[1]:x},{w1_vals[2]:x}]", flush=True)
                else:
                    print(f"  WARNING: SAT but verification failed for W1[57]=0x{w1_57:x}", flush=True)

            elif r.returncode == 20:
                n_unsat += 1
            else:
                n_timeout += 1
        except subprocess.TimeoutExpired:
            n_timeout += 1

    if w1_57 > 0 and (w1_57 & 0xF) == 0xF:
        elapsed = time.time() - t0
        pct = 100 * (w1_57+1) / (1<<N)
        print(f"  [{pct:.0f}%] w57=0x{w1_57:x} sat={n_sat} unsat={n_unsat} "
              f"timeout={n_timeout} collisions={n_collisions} {elapsed:.0f}s", flush=True)

elapsed = time.time() - t0
print(f"\n=== N={N} Hybrid Results ===")
print(f"W1[57] values tested: {1<<N}")
print(f"SAT: {n_sat}, UNSAT: {n_unsat}, TIMEOUT: {n_timeout}")
print(f"Collisions: {n_collisions}")
print(f"Time: {elapsed:.1f}s")
print(f"Done.", flush=True)
