#!/usr/bin/env python3
"""
Near-Collision Relaxation: Skip Register h

Both Gemini 3.1 Pro and GPT-5.4 independently rated this the #1 priority.

Encode sr=60 requiring only registers a-g to match (skip h, the weakest register).
This should find hundreds of solutions in minutes instead of 12 hours for full collision.

Then analyze h's residual on those solutions:
- What values does dh take?
- Is dh always in a small subspace?
- Can we interpolate a correction function?

Usage: python3 near_collision_skip_h.py [N] [n_solutions] [timeout]
"""
import sys, os, time, subprocess, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

N = int(sys.argv[1]) if len(sys.argv) > 1 else 8
n_target = int(sys.argv[2]) if len(sys.argv) > 2 else 200
timeout = int(sys.argv[3]) if len(sys.argv) > 3 else 300

if N == 32:
    enc = __import__('13_custom_cnf_encoder')
    M1 = [0x17149975] + [0xffffffff]*15
    M2 = list(M1); M2[0] ^= 0x80000000; M2[9] ^= 0x80000000
    state1, W1_pre = enc.precompute_state(M1)
    state2, W2_pre = enc.precompute_state(M2)

    def make_cnf_skip_h():
        cnf = enc.CNFBuilder()
        s1 = tuple(cnf.const_word(v) for v in state1)
        s2 = tuple(cnf.const_word(v) for v in state2)
        w1f = [cnf.free_word(f"W1_{57+i}") for i in range(4)]
        w2f = [cnf.free_word(f"W2_{57+i}") for i in range(4)]
        W1s, W2s = list(w1f), list(w2f)
        # Schedule-determined W[61..63]
        w1_61 = cnf.add_word(cnf.add_word(cnf.sigma1_w(w1f[2]), cnf.const_word(W1_pre[54])),
                             cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[46])), cnf.const_word(W1_pre[45])))
        w2_61 = cnf.add_word(cnf.add_word(cnf.sigma1_w(w2f[2]), cnf.const_word(W2_pre[54])),
                             cnf.add_word(cnf.const_word(enc.sigma0_py(W2_pre[46])), cnf.const_word(W2_pre[45])))
        w1_62 = cnf.add_word(cnf.add_word(cnf.sigma1_w(w1f[3]), cnf.const_word(W1_pre[55])),
                             cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[47])), cnf.const_word(W1_pre[46])))
        w2_62 = cnf.add_word(cnf.add_word(cnf.sigma1_w(w2f[3]), cnf.const_word(W2_pre[55])),
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
        # Enforce equality on registers a-g ONLY (skip h = index 7)
        for i in range(7):  # a=0, b=1, c=2, d=3, e=4, f=5, g=6
            cnf.eq_word(st1[i], st2[i])
        # Return h words for extraction
        return cnf, st1[7], st2[7], w1f, w2f

else:
    spec = __import__('50_precision_homotopy')
    sha = spec.MiniSHA256(N)
    MASK_N = sha.MASK; MSB = sha.MSB
    K32 = spec.K32; KT = [k & MASK_N for k in K32]
    m0, s1_state, s2_state, W1_pre, W2_pre = sha.find_m0()
    if m0 is None:
        print(f"No candidate at N={N}"); sys.exit(1)
    ops = {'r_Sig0': sha.r_Sig0, 'r_Sig1': sha.r_Sig1, 'r_sig0': sha.r_sig0,
           's_sig0': sha.s_sig0, 'r_sig1': sha.r_sig1, 's_sig1': sha.s_sig1}

    def make_cnf_skip_h():
        cnf = spec.MiniCNFBuilder(N)
        st1 = tuple(cnf.const_word(v) for v in s1_state)
        st2 = tuple(cnf.const_word(v) for v in s2_state)
        w1f = [cnf.free_word(f"W1_{57+i}") for i in range(4)]
        w2f = [cnf.free_word(f"W2_{57+i}") for i in range(4)]
        def sw(x): return cnf.sigma1_w(x, ops['r_sig1'], ops['s_sig1'])
        W1s, W2s = list(w1f), list(w2f)
        w1_61 = cnf.add_word(cnf.add_word(sw(w1f[2]), cnf.const_word(W1_pre[54])),
                             cnf.add_word(cnf.const_word(sha.sigma0(W1_pre[46])), cnf.const_word(W1_pre[45])))
        w2_61 = cnf.add_word(cnf.add_word(sw(w2f[2]), cnf.const_word(W2_pre[54])),
                             cnf.add_word(cnf.const_word(sha.sigma0(W2_pre[46])), cnf.const_word(W2_pre[45])))
        w1_62 = cnf.add_word(cnf.add_word(sw(w1f[3]), cnf.const_word(W1_pre[55])),
                             cnf.add_word(cnf.const_word(sha.sigma0(W1_pre[47])), cnf.const_word(W1_pre[46])))
        w2_62 = cnf.add_word(cnf.add_word(sw(w2f[3]), cnf.const_word(W2_pre[55])),
                             cnf.add_word(cnf.const_word(sha.sigma0(W2_pre[47])), cnf.const_word(W2_pre[46])))
        w1_63 = cnf.add_word(cnf.add_word(sw(w1_61), cnf.const_word(W1_pre[56])),
                             cnf.add_word(cnf.const_word(sha.sigma0(W1_pre[48])), cnf.const_word(W1_pre[47])))
        w2_63 = cnf.add_word(cnf.add_word(sw(w2_61), cnf.const_word(W2_pre[56])),
                             cnf.add_word(cnf.const_word(sha.sigma0(W2_pre[48])), cnf.const_word(W2_pre[47])))
        W1s.extend([w1_61, w1_62, w1_63]); W2s.extend([w2_61, w2_62, w2_63])
        for i in range(7):
            st1 = cnf.sha256_round(st1, KT[57+i], W1s[i], ops)
            st2 = cnf.sha256_round(st2, KT[57+i], W2s[i], ops)
        # Skip h (register 7) — enforce only a-g
        for i in range(7):
            cnf.eq_word(st1[i], st2[i])
        return cnf, st1[7], st2[7], w1f, w2f

print(f"Near-Collision Relaxation: Skip h Register (N={N})")
print(f"Encoding sr=60 with 7/8 register equality (a=b=c=d=e=f=g, h free)")
print(f"Target: {n_target} solutions, timeout={timeout}s per solve")
print(flush=True)

solutions = []
total_time = 0
seed = 1

while len(solutions) < n_target and total_time < timeout * 10:
    cnf, h1_word, h2_word, w1f, w2f = make_cnf_skip_h()

    # Add blocking clauses for previous solutions
    for sol_assumptions in solutions:
        # Block this exact assignment
        block_clause = []
        for lit in sol_assumptions:
            block_clause.append(-lit)
        cnf.clauses.append(block_clause)

    td = tempfile.mkdtemp(prefix=f"nc_skiph_N{N}_")
    cf = os.path.join(td, "near_collision.cnf")
    nv, nc = cnf.write_dimacs(cf)

    if len(solutions) == 0:
        print(f"  CNF: {nv} vars, {nc} clauses", flush=True)

    t0 = time.time()
    try:
        r = subprocess.run(["kissat", "-q", f"--seed={seed}", cf],
                           capture_output=True, timeout=timeout)
        elapsed = time.time() - t0
        total_time += elapsed

        if r.returncode == 10:  # SAT
            # Parse solution
            sol_lits = []
            for line in r.stdout.decode().split('\n'):
                if line.startswith('v '):
                    sol_lits.extend(int(x) for x in line[2:].split() if x != '0')

            # Extract free word values
            # For mini-SHA, we need to extract from the variable assignments
            w_vals = {}
            for lit in sol_lits:
                var = abs(lit)
                val = 1 if lit > 0 else 0
                w_vals[var] = val

            solutions.append(sol_lits[:min(len(sol_lits), 256)])  # store first 256 lits for blocking

            if len(solutions) <= 20 or len(solutions) % 50 == 0:
                print(f"  Solution #{len(solutions):4d}: SAT in {elapsed:.1f}s "
                      f"(total: {total_time:.0f}s, seed={seed})", flush=True)

        elif r.returncode == 20:  # UNSAT
            print(f"  UNSAT after {len(solutions)} solutions ({elapsed:.1f}s)", flush=True)
            break
        else:
            print(f"  rc={r.returncode} in {elapsed:.1f}s", flush=True)

    except subprocess.TimeoutExpired:
        elapsed = timeout
        total_time += elapsed
        print(f"  TIMEOUT after {len(solutions)} solutions", flush=True)
        break

    seed += 1

print(f"\n=== Results ===")
print(f"Near-collisions found: {len(solutions)}")
print(f"Total time: {total_time:.1f}s")
if solutions:
    print(f"Average time per solution: {total_time/len(solutions):.2f}s")
print(f"\nThese are inputs where registers a-g all match between msg1 and msg2,")
print(f"but register h may differ. The residual dh characterizes what's left to solve.")
print(flush=True)

# If we have solutions, we could analyze dh distribution
# (requires extracting W values from SAT solutions and re-evaluating)

print("Done.", flush=True)
