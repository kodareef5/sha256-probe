#!/usr/bin/env python3
"""
Script 82: Extract and analyze mini-SHA-256 sr=60 collisions.

Runs the precision homotopy SAT solver at N=8 and N=10, extracts the
collision values, then traces the differential round-by-round to compare
with the N=32 case (where sr=60 is UNSAT for known candidates).

Key question: what does the W[61] differential look like when collision
succeeds vs when it fails?
"""
import sys, os, time, subprocess, tempfile

sys.path.insert(0, os.path.dirname(__file__))
from importlib import import_module

# Import the precision homotopy module
spec = import_module("50_precision_homotopy")
MiniSHA256 = spec.MiniSHA256
MiniCNFBuilder = spec.MiniCNFBuilder
K32 = spec.K32

def solve_and_extract(N, timeout=600):
    """Find sr=60 collision at word width N, return free words."""
    sha = MiniSHA256(N)
    MASK = sha.MASK

    m0, s1, s2, W1, W2 = sha.find_m0()
    if m0 is None:
        print(f"  N={N}: No candidate found")
        return None

    print(f"  N={N}: M[0]=0x{m0:x}, da[56]=0")

    ops_params = {
        'r_Sig0': sha.r_Sig0, 'r_Sig1': sha.r_Sig1,
        'r_sig0': sha.r_sig0, 's_sig0': sha.s_sig0,
        'r_sig1': sha.r_sig1, 's_sig1': sha.s_sig1,
    }
    K_trunc = [k & MASK for k in K32]

    cnf = MiniCNFBuilder(N)
    st1 = tuple(cnf.const_word(v) for v in s1)
    st2 = tuple(cnf.const_word(v) for v in s2)

    w1_free = [cnf.free_word(f"W1_{57+i}") for i in range(4)]
    w2_free = [cnf.free_word(f"W2_{57+i}") for i in range(4)]

    # Build derived schedule words
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

    # 7 rounds for both messages
    for i in range(7):
        st1 = cnf.sha256_round(st1, K_trunc[57+i], W1_sched[i], ops_params)
    for i in range(7):
        st2 = cnf.sha256_round(st2, K_trunc[57+i], W2_sched[i], ops_params)

    for i in range(8):
        cnf.eq_word(st1[i], st2[i])

    with tempfile.TemporaryDirectory() as td:
        cnf_file = os.path.join(td, f"sr60_N{N}.cnf")
        n_vars, n_clauses = cnf.write_dimacs(cnf_file)
        print(f"  CNF: {n_vars} vars, {n_clauses} clauses")

        result = subprocess.run(["kissat", "-q", cnf_file],
                                capture_output=True, text=True, timeout=timeout)

        if result.returncode == 10:  # SAT
            # Parse solution
            assignment = {}
            for line in result.stdout.splitlines():
                if line.startswith('v'):
                    for lit in line[1:].split():
                        v = int(lit)
                        if v != 0:
                            assignment[abs(v)] = (v > 0)

            # Extract free word values
            def extract_word(word_bits):
                val = 0
                for i, bit in enumerate(word_bits):
                    if abs(bit) in cnf.known:
                        bval = cnf.known[abs(bit)] if bit > 0 else not cnf.known[abs(bit)]
                    elif abs(bit) in assignment:
                        bval = assignment[abs(bit)] if bit > 0 else not assignment[abs(bit)]
                    else:
                        bval = False
                    if bval:
                        val |= (1 << i)
                return val

            w1_vals = [extract_word(w) for w in w1_free]
            w2_vals = [extract_word(w) for w in w2_free]
            return {
                'N': N, 'm0': m0, 's1': s1, 's2': s2,
                'W1_pre': W1, 'W2_pre': W2,
                'w1_free': w1_vals, 'w2_free': w2_vals,
                'sha': sha
            }
        elif result.returncode == 20:
            print(f"  UNSAT")
            return None
        else:
            print(f"  TIMEOUT or ERROR (rc={result.returncode})")
            return None


def trace_differential(data):
    """Trace round-by-round differential for a mini-SHA collision."""
    N = data['N']
    sha = data['sha']
    MASK = sha.MASK

    def add(*args):
        s = 0
        for a in args: s = (s + a) & MASK
        return s

    def hw(x): return bin(x & MASK).count('1')

    s1 = list(data['s1'])
    s2 = list(data['s2'])
    W1_pre = data['W1_pre']
    W2_pre = data['W2_pre']
    w1 = data['w1_free']
    w2 = data['w2_free']

    # Build full schedule tails
    W1 = list(w1)
    W2 = list(w2)
    W1.append(add(sha.sigma1(W1[2]), W1_pre[54], sha.sigma0(W1_pre[46]), W1_pre[45]))
    W2.append(add(sha.sigma1(W2[2]), W2_pre[54], sha.sigma0(W2_pre[46]), W2_pre[45]))
    W1.append(add(sha.sigma1(W1[3]), W1_pre[55], sha.sigma0(W1_pre[47]), W1_pre[46]))
    W2.append(add(sha.sigma1(W2[3]), W2_pre[55], sha.sigma0(W2_pre[47]), W2_pre[46]))
    W1.append(add(sha.sigma1(W1[4]), W1_pre[56], sha.sigma0(W1_pre[48]), W1_pre[47]))
    W2.append(add(sha.sigma1(W2[4]), W2_pre[56], sha.sigma0(W2_pre[48]), W2_pre[47]))

    K = [k & MASK for k in K32]
    reg = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']

    print(f"\n{'='*70}")
    print(f"DIFFERENTIAL TRACE: N={N}-bit mini-SHA-256 sr=60 COLLISION")
    print(f"{'='*70}")

    # Run rounds
    a1,b1,c1,d1,e1,f1,g1,h1 = s1
    a2,b2,c2,d2,e2,f2,g2,h2 = s2

    states1 = [(a1,b1,c1,d1,e1,f1,g1,h1)]
    states2 = [(a2,b2,c2,d2,e2,f2,g2,h2)]

    for i in range(7):
        T1a = add(h1, sha.Sigma1(e1), sha.ch(e1,f1,g1), K[57+i], W1[i])
        T2a = add(sha.Sigma0(a1), sha.maj(a1,b1,c1))
        h1,g1,f1,e1,d1,c1,b1,a1 = g1,f1,e1,add(d1,T1a),c1,b1,a1,add(T1a,T2a)
        T1b = add(h2, sha.Sigma1(e2), sha.ch(e2,f2,g2), K[57+i], W2[i])
        T2b = add(sha.Sigma0(a2), sha.maj(a2,b2,c2))
        h2,g2,f2,e2,d2,c2,b2,a2 = g2,f2,e2,add(d2,T1b),c2,b2,a2,add(T1b,T2b)
        states1.append((a1,b1,c1,d1,e1,f1,g1,h1))
        states2.append((a2,b2,c2,d2,e2,f2,g2,h2))

    for r in range(8):
        s1r = states1[r]
        s2r = states2[r]
        total_hw = sum(hw(s1r[i] ^ s2r[i]) for i in range(8))
        n_zero = sum(1 for i in range(8) if s1r[i] == s2r[i])

        if r == 0:
            label = "Entry (r56)"
        else:
            dW = W1[r-1] ^ W2[r-1]
            label = f"Round {56+r} (dW={dW:#0{N//4+3}x} hw={hw(dW)})"

        print(f"\n  {label}")
        print(f"    Total HW={total_hw}, Zero registers={n_zero}/8")

        for i in range(8):
            d = s1r[i] ^ s2r[i]
            if d == 0:
                print(f"    d{reg[i]} = 0  ** ZERO **")
            else:
                print(f"    d{reg[i]} = {d:#0{N//4+3}x} (hw={hw(d)})")

    # Key comparison: what does dW[61] look like?
    dW61 = W1[4] ^ W2[4]
    print(f"\n  KEY: dW[61] = {dW61:#0{N//4+3}x} (hw={hw(dW61)})")
    print(f"  At N=32 (UNSAT), dW[61] had hw=17 and broke the zeroing pattern")
    print(f"  Here at N={N} (SAT), dW[61] hw={hw(dW61)} — {'also nonzero, but solver found a path!' if dW61 != 0 else 'ZERO! That is why it works.'}")


if __name__ == "__main__":
    for N in [8, 10, 11, 12]:
        print(f"\n{'#'*70}")
        print(f"# Solving N={N}")
        print(f"{'#'*70}")
        data = solve_and_extract(N, timeout=600)
        if data:
            trace_differential(data)
            print(f"\n  Free words (collision solution):")
            for i in range(4):
                print(f"    W1[{57+i}] = {data['w1_free'][i]:#0{N//4+3}x}  "
                      f"W2[{57+i}] = {data['w2_free'][i]:#0{N//4+3}x}  "
                      f"dW = {data['w1_free'][i] ^ data['w2_free'][i]:#0{N//4+3}x}")
