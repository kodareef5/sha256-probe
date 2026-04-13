#!/usr/bin/env python3
"""
carry_conditioned_sat.py — SAT encoder with carry invariance constraints

Encodes the sr=60 collision problem with ADDITIONAL constraints from the
carry automaton analysis:
- 608 carry-diff bits are structurally invariant
- These are encoded as equality/inequality constraints on carry variables
- This reduces the effective search space from ~10K to ~960 free variables

The key insight: 42% of carry-diffs are constant across ALL sr=60 collisions
for a given candidate. By fixing them, we guide the SAT solver to the solution
manifold much faster.

Usage: python3 carry_conditioned_sat.py [--baseline] [--seed N]
  --baseline: generate standard encoding without carry constraints (for comparison)
  --seed N: Kissat random seed (default 5)
"""
import sys, os, time, subprocess, tempfile
_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in dir() else os.getcwd()
sys.path.insert(0, os.path.join(_dir, '..'))
from lib.sha256 import K, IV, Sigma0, Sigma1, sigma0 as sigma0_py, sigma1 as sigma1_py, Ch, Maj, MASK, precompute_state
from lib.cnf_encoder import CNFBuilder

# Known N=32 sr=60 collision certificate
M0_VAL = 0x17149975
FILL = 0xFFFFFFFF

def extract_invariant_carry_diffs():
    """
    Extract the carry-diff values for structurally invariant additions.
    Returns dict: (round, add_name) -> list of 32 carry-diff bits (0 or 1).
    """
    M1 = [M0_VAL] + [FILL]*15
    M2 = list(M1)
    M2[0] ^= 0x80000000
    M2[9] ^= 0x80000000

    state1, W1pre = precompute_state(M1)
    state2, W2pre = precompute_state(M2)

    W1_FREE = [0x9ccfa55e, 0xd9d64416, 0x9e3ffb08, 0xb6befe82]
    W2_FREE = [0x72e6c8cd, 0x4b96ca51, 0x587ffaa6, 0xea3ce26b]

    W1 = list(W1_FREE)
    W2 = list(W2_FREE)
    W1.append((sigma1_py(W1[2]) + W1pre[54] + sigma0_py(W1pre[46]) + W1pre[45]) & MASK)
    W2.append((sigma1_py(W2[2]) + W2pre[54] + sigma0_py(W2pre[46]) + W2pre[45]) & MASK)
    W1.append((sigma1_py(W1[3]) + W1pre[55] + sigma0_py(W1pre[47]) + W1pre[46]) & MASK)
    W2.append((sigma1_py(W2[3]) + W2pre[55] + sigma0_py(W2pre[47]) + W2pre[46]) & MASK)
    W1.append((sigma1_py(W1[4]) + W1pre[56] + sigma0_py(W1pre[48]) + W1pre[47]) & MASK)
    W2.append((sigma1_py(W2[4]) + W2pre[56] + sigma0_py(W2pre[48]) + W2pre[47]) & MASK)

    ADD_NAMES = ['h+Sig1', '+Ch', '+K', '+W', 'S0+Maj', 'd+T1', 'T1+T2']

    def extract_carries(a, b):
        carries = []
        c = 0
        for k in range(32):
            s = ((a >> k) & 1) + ((b >> k) & 1) + c
            c = s >> 1
            carries.append(c)
        return carries

    def add_mod(a, b):
        return (a + b) & MASK

    invariants = {}
    s1 = list(state1)
    s2 = list(state2)

    for r in range(7):
        rnd = 57 + r
        a1,b1,c1,d1,e1,f1,g1,h1 = s1
        a2,b2,c2,d2,e2,f2,g2,h2 = s2

        sig1_1, sig1_2 = Sigma1(e1), Sigma1(e2)
        ch1, ch2 = Ch(e1,f1,g1), Ch(e2,f2,g2)
        sig0_1, sig0_2 = Sigma0(a1), Sigma0(a2)
        maj1, maj2 = Maj(a1,b1,c1), Maj(a2,b2,c2)

        # T1 chain (sequential)
        t0_1 = add_mod(h1, sig1_1); t0_2 = add_mod(h2, sig1_2)
        c_hsig1_1 = extract_carries(h1, sig1_1)
        c_hsig1_2 = extract_carries(h2, sig1_2)

        t1_1 = add_mod(t0_1, ch1); t1_2 = add_mod(t0_2, ch2)
        c_ch_1 = extract_carries(t0_1, ch1)
        c_ch_2 = extract_carries(t0_2, ch2)

        t2_1 = add_mod(t1_1, K[rnd]); t2_2 = add_mod(t1_2, K[rnd])
        c_k_1 = extract_carries(t1_1, K[rnd])
        c_k_2 = extract_carries(t1_2, K[rnd])

        T1_1 = add_mod(t2_1, W1[r]); T1_2 = add_mod(t2_2, W2[r])
        c_w_1 = extract_carries(t2_1, W1[r])
        c_w_2 = extract_carries(t2_2, W2[r])

        T2_1 = add_mod(sig0_1, maj1); T2_2 = add_mod(sig0_2, maj2)
        c_sm_1 = extract_carries(sig0_1, maj1)
        c_sm_2 = extract_carries(sig0_2, maj2)

        ne_1 = add_mod(d1, T1_1); ne_2 = add_mod(d2, T1_2)
        c_dt1_1 = extract_carries(d1, T1_1)
        c_dt1_2 = extract_carries(d2, T1_2)

        na_1 = add_mod(T1_1, T2_1); na_2 = add_mod(T1_2, T2_2)
        c_t1t2_1 = extract_carries(T1_1, T2_1)
        c_t1t2_2 = extract_carries(T1_2, T2_2)

        all_c = {
            'h+Sig1': (c_hsig1_1, c_hsig1_2),
            '+Ch': (c_ch_1, c_ch_2),
            '+K': (c_k_1, c_k_2),
            '+W': (c_w_1, c_w_2),
            'S0+Maj': (c_sm_1, c_sm_2),
            'd+T1': (c_dt1_1, c_dt1_2),
            'T1+T2': (c_t1t2_1, c_t1t2_2),
        }

        # Structural invariance pattern
        for add_name in ADD_NAMES:
            is_inv = False
            if rnd == 57 and add_name in ['h+Sig1', '+Ch', '+K', 'S0+Maj']:
                is_inv = True
            if rnd >= 59 and add_name in ['S0+Maj', 'd+T1', 'T1+T2']:
                is_inv = True
            if is_inv:
                c1_arr, c2_arr = all_c[add_name]
                cdiff = [c1_arr[k] ^ c2_arr[k] for k in range(32)]
                invariants[(rnd, add_name)] = cdiff

        # Advance state
        s1 = [na_1, a1, b1, c1, ne_1, e1, f1, g1]
        s2 = [na_2, a2, b2, c2, ne_2, e2, f2, g2]

    return invariants


def encode_sr60_with_carries(carry_conditioned=True):
    """
    Encode sr=60 collision problem with optional carry conditioning.
    Returns (cnf_builder, carry_vars_dict) where carry_vars_dict maps
    (round, add_name, path, bit) -> SAT variable ID.
    """
    M1 = [M0_VAL] + [FILL]*15
    M2 = list(M1)
    M2[0] ^= 0x80000000
    M2[9] ^= 0x80000000

    state1, W1_pre = precompute_state(M1)
    state2, W2_pre = precompute_state(M2)

    assert state1[0] == state2[0], f"da[56] != 0"

    cnf = CNFBuilder()
    carry_vars = {}  # (round, add_name, path, bit) -> var_id

    # Build initial states as constant words
    s1 = [cnf.const_word(v) for v in state1]
    s2 = [cnf.const_word(v) for v in state2]

    # Free variables for W[57..60]
    w1_free = [cnf.free_word(f"W1_{57+i}") for i in range(4)]
    w2_free = [cnf.free_word(f"W2_{57+i}") for i in range(4)]

    # Build schedule words
    # W[61] = sigma1(W[59]) + W[54] + sigma0(W[46]) + W[45]
    w1_61 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_free[2]), cnf.const_word(W1_pre[54])),
        cnf.add_word(cnf.const_word(sigma0_py(W1_pre[46])), cnf.const_word(W1_pre[45])))
    w2_61 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_free[2]), cnf.const_word(W2_pre[54])),
        cnf.add_word(cnf.const_word(sigma0_py(W2_pre[46])), cnf.const_word(W2_pre[45])))

    # W[62] = sigma1(W[60]) + W[55] + sigma0(W[47]) + W[46]
    w1_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_free[3]), cnf.const_word(W1_pre[55])),
        cnf.add_word(cnf.const_word(sigma0_py(W1_pre[47])), cnf.const_word(W1_pre[46])))
    w2_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_free[3]), cnf.const_word(W2_pre[55])),
        cnf.add_word(cnf.const_word(sigma0_py(W2_pre[47])), cnf.const_word(W2_pre[46])))

    # W[63] = sigma1(W[61]) + W[56] + sigma0(W[48]) + W[47]
    w1_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_61), cnf.const_word(W1_pre[56])),
        cnf.add_word(cnf.const_word(sigma0_py(W1_pre[48])), cnf.const_word(W1_pre[47])))
    w2_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_61), cnf.const_word(W2_pre[56])),
        cnf.add_word(cnf.const_word(sigma0_py(W2_pre[48])), cnf.const_word(W2_pre[47])))

    W1_sched = list(w1_free) + [w1_61, w1_62, w1_63]
    W2_sched = list(w2_free) + [w2_61, w2_62, w2_63]

    ADD_NAMES = ['h+Sig1', '+Ch', '+K', '+W', 'S0+Maj', 'd+T1', 'T1+T2']

    # Run 7 rounds with carry tracking
    for r in range(7):
        rnd = 57 + r
        for path, (s, W_sched) in enumerate([(s1, W1_sched), (s2, W2_sched)]):
            a, b, c, d, e, f, g, h = s

            sig1 = cnf.Sigma1(e)
            ch = cnf.Ch(e, f, g)
            sig0 = cnf.Sigma0(a)
            mj = cnf.Maj(a, b, c)
            K_word = cnf.const_word(K[rnd])

            # T1 chain — sequential with carry tracking
            t1, c_hsig1 = cnf.add_word(h, sig1, track_carries=True)
            for bit in range(32):
                carry_vars[(rnd, 'h+Sig1', path, bit)] = c_hsig1[bit]

            t1, c_ch = cnf.add_word(t1, ch, track_carries=True)
            for bit in range(32):
                carry_vars[(rnd, '+Ch', path, bit)] = c_ch[bit]

            t1, c_k = cnf.add_word(t1, K_word, track_carries=True)
            for bit in range(32):
                carry_vars[(rnd, '+K', path, bit)] = c_k[bit]

            t1, c_w = cnf.add_word(t1, W_sched[r], track_carries=True)
            for bit in range(32):
                carry_vars[(rnd, '+W', path, bit)] = c_w[bit]

            # T2 = Sig0(a) + Maj(a,b,c)
            t2, c_sm = cnf.add_word(sig0, mj, track_carries=True)
            for bit in range(32):
                carry_vars[(rnd, 'S0+Maj', path, bit)] = c_sm[bit]

            # new_e = d + T1
            e_new, c_dt1 = cnf.add_word(d, t1, track_carries=True)
            for bit in range(32):
                carry_vars[(rnd, 'd+T1', path, bit)] = c_dt1[bit]

            # new_a = T1 + T2
            a_new, c_t1t2 = cnf.add_word(t1, t2, track_carries=True)
            for bit in range(32):
                carry_vars[(rnd, 'T1+T2', path, bit)] = c_t1t2[bit]

            # Update state (correct shift register)
            new_state = [a_new, a, b, c, e_new, e, f, g]
            if path == 0:
                s1 = new_state
            else:
                s2 = new_state

    # Collision constraint: all output register diffs = 0
    for reg in range(8):
        cnf.eq_word(s1[reg], s2[reg])

    # Add carry invariance constraints
    if carry_conditioned:
        invariants = extract_invariant_carry_diffs()
        n_carry_clauses = 0
        for (rnd, add_name), cdiff in invariants.items():
            for bit in range(32):
                c1_var = carry_vars.get((rnd, add_name, 0, bit))
                c2_var = carry_vars.get((rnd, add_name, 1, bit))
                if c1_var is None or c2_var is None:
                    continue
                # Both might be constants (folded)
                c1_known = cnf._is_known(c1_var)
                c2_known = cnf._is_known(c2_var)
                if c1_known and c2_known:
                    continue  # Both constant, constraint is automatic

                if cdiff[bit] == 0:
                    # carry-diff = 0: c1 == c2
                    if c1_known:
                        val = cnf._get_val(c1_var)
                        cnf.clauses.append([c2_var if val else -c2_var])
                    elif c2_known:
                        val = cnf._get_val(c2_var)
                        cnf.clauses.append([c1_var if val else -c1_var])
                    else:
                        cnf.clauses.append([-c1_var, c2_var])
                        cnf.clauses.append([c1_var, -c2_var])
                        n_carry_clauses += 2
                else:
                    # carry-diff = 1: c1 != c2
                    if c1_known:
                        val = cnf._get_val(c1_var)
                        cnf.clauses.append([-c2_var if val else c2_var])
                    elif c2_known:
                        val = cnf._get_val(c2_var)
                        cnf.clauses.append([-c1_var if val else c1_var])
                    else:
                        cnf.clauses.append([-c1_var, -c2_var])
                        cnf.clauses.append([c1_var, c2_var])
                        n_carry_clauses += 2

        print(f"  Added {n_carry_clauses} carry invariance clauses")

    return cnf, carry_vars


def main():
    baseline = '--baseline' in sys.argv
    seed = 5
    for i, arg in enumerate(sys.argv):
        if arg == '--seed' and i+1 < len(sys.argv):
            seed = int(sys.argv[i+1])

    mode = "BASELINE (no carry constraints)" if baseline else "CARRY-CONDITIONED"
    print(f"=== sr=60 SAT Encoder — {mode} ===\n")
    print(f"Candidate: M[0]=0x{M0_VAL:08x}, fill=0x{FILL:08x}")
    print(f"Kissat seed: {seed}\n")

    t0 = time.time()
    print("Encoding...")
    cnf, carry_vars = encode_sr60_with_carries(carry_conditioned=not baseline)
    t_encode = time.time() - t0

    n_carry_tracked = sum(1 for k in carry_vars if not cnf._is_known(carry_vars[k]))
    n_carry_const = sum(1 for k in carry_vars if cnf._is_known(carry_vars[k]))

    print(f"  Encoding time: {t_encode:.1f}s")
    print(f"  Carry variables tracked: {len(carry_vars)} ({n_carry_tracked} free, {n_carry_const} constant-folded)")
    print(f"  Stats: {cnf.stats}")

    # Write CNF
    tmpdir = tempfile.mkdtemp()
    suffix = "baseline" if baseline else "carry_cond"
    cnf_path = os.path.join(tmpdir, f"sr60_{suffix}.cnf")
    n_vars, n_clauses = cnf.write_dimacs(cnf_path)
    print(f"\n  CNF: {n_vars} variables, {n_clauses} clauses")
    print(f"  File: {cnf_path}")

    # Run Kissat
    print(f"\nRunning Kissat (seed={seed})...")
    t0 = time.time()
    result = subprocess.run(
        ['kissat', '-q', f'--seed={seed}', cnf_path],
        capture_output=True, text=True, timeout=7200  # 2h timeout
    )
    t_solve = time.time() - t0

    if result.returncode == 10:
        print(f"  SATISFIABLE in {t_solve:.1f}s!")
        # Extract solution
        sol = {}
        for line in result.stdout.splitlines():
            if line.startswith('v '):
                for lit in line[2:].split():
                    v = int(lit)
                    if v != 0:
                        sol[abs(v)] = v > 0

        # Extract W1 values
        print("\n  Solution:")
        for i in range(4):
            name = f"W1_{57+i}"
            val = 0
            for bit in range(32):
                var_name = f"{name}_b{bit}"
                for vid, vname in cnf.free_var_names.items():
                    if vname == var_name and vid in sol:
                        if sol[vid]:
                            val |= (1 << bit)
            print(f"    W1[{57+i}] = 0x{val:08x}")

    elif result.returncode == 20:
        print(f"  UNSATISFIABLE in {t_solve:.1f}s")
    else:
        print(f"  Timeout or error (rc={result.returncode}) after {t_solve:.1f}s")

    print(f"\n=== Summary ===")
    print(f"Mode: {mode}")
    print(f"Variables: {n_vars}, Clauses: {n_clauses}")
    print(f"Encode time: {t_encode:.1f}s, Solve time: {t_solve:.1f}s")
    print(f"Total: {t_encode + t_solve:.1f}s")

if __name__ == '__main__':
    main()
