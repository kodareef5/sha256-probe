#!/usr/bin/env python3
"""
constrained_sr60.py — Trail-constrained sr=60 conforming pair search

Key insight from Li et al.: instead of searching for ANY collision,
constrain the search with a DIFFERENTIAL TRAIL — specific patterns
of which bits are active/inactive at each round. A good trail makes
the conforming pair search much faster.

Strategy:
1. Use Z3 to analyze which structural constraints are compatible
   (instant — algebraic reasoning)
2. Generate CONSTRAINED CNFs for Kissat where additional bits are fixed
   (reducing search space without eliminating solutions)
3. Test multiple constraint strategies to find the fastest

Constraint strategies to test:
A. Fix dW[57] to minimize ||de57|| (even if da57 != 0)
B. Fix dW[57] to minimize ||da57|| (even if de57 != 0)
C. Fix dW[57] to minimize ||da57 + de57||
D. Fix partial bits of W[57] based on the boomerang analysis
E. Progressive: fix dW[57] constraints, then search remaining freedom
"""

import sys, os, time, subprocess, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from lib.sha256 import *
from lib.cnf_encoder import CNFBuilder

MASK32 = 0xFFFFFFFF


def compute_optimal_dw57(s1, s2):
    """Find the dW[57] that minimizes the combined depth-1 error.

    The boomerang gap means we can't zero BOTH da57 and de57.
    But we can choose dW[57] to minimize their COMBINED Hamming weight.

    Returns several candidate dW[57] values with their error metrics.
    """
    d_h56 = (s1[7] - s2[7]) & MASK32
    d_Sig1 = (Sigma1(s1[4]) - Sigma1(s2[4])) & MASK32
    d_Ch = (Ch(s1[4],s1[5],s1[6]) - Ch(s2[4],s2[5],s2[6])) & MASK32
    C_T1 = (d_h56 + d_Sig1 + d_Ch) & MASK32

    d_Sig0 = (Sigma0(s1[0]) - Sigma0(s2[0])) & MASK32  # should be 0
    d_Maj = (Maj(s1[0],s1[1],s1[2]) - Maj(s2[0],s2[1],s2[2])) & MASK32
    C_T2 = (d_Sig0 + d_Maj) & MASK32

    d_d56 = (s1[3] - s2[3]) & MASK32

    # For de57=0: dW57 = -(d_d56 + C_T1) mod 2^32
    dw57_for_e = (-(d_d56 + C_T1)) & MASK32
    # For da57=0: dW57 = -(C_T1 + C_T2) mod 2^32
    dw57_for_a = (-(C_T1 + C_T2)) & MASK32

    # Compute errors for each choice
    results = []

    # Strategy A: optimize for de57=0
    da57_err = hw(((C_T1 + dw57_for_e + C_T2) & MASK32))  # HW of da57
    results.append(('de57=0', dw57_for_e, 0, da57_err, da57_err))

    # Strategy B: optimize for da57=0
    de57_err = hw(((d_d56 + C_T1 + dw57_for_a) & MASK32))  # HW of de57
    results.append(('da57=0', dw57_for_a, de57_err, 0, de57_err))

    # Strategy C: midpoint — minimize combined error
    # Try the arithmetic midpoint of the two required values
    mid = ((dw57_for_e + dw57_for_a) >> 1) & MASK32  # approximate midpoint
    de57_mid = hw(((d_d56 + C_T1 + mid) & MASK32))
    da57_mid = hw(((C_T1 + mid + C_T2) & MASK32))
    results.append(('midpoint', mid, de57_mid, da57_mid, de57_mid + da57_mid))

    # Strategy D: sample random dW57 values, keep best combined error
    import random
    random.seed(42)
    best_random = None
    best_random_err = 256
    for _ in range(100000):
        dw = random.getrandbits(32)
        de = hw(((d_d56 + C_T1 + dw) & MASK32))
        da = hw(((C_T1 + dw + C_T2) & MASK32))
        combined = de + da
        if combined < best_random_err:
            best_random_err = combined
            best_random = (dw, de, da)

    if best_random:
        results.append(('random_best', best_random[0],
                        best_random[1], best_random[2], best_random_err))

    return results


def encode_constrained_collision(m0, fill, dw57_constraint=None,
                                  fix_w57_bits=None):
    """Encode sr=60 with additional constraints on W[57].

    dw57_constraint: if set, add constraint that W1[57] - W2[57] = this value
    fix_w57_bits: dict of {bit_position: (val1, val2)} to fix specific bits
    """
    M1 = [m0] + [fill]*15
    M2 = list(M1); M2[0] ^= 0x80000000; M2[9] ^= 0x80000000

    s1, W1 = precompute_state(M1)
    s2, W2 = precompute_state(M2)
    assert s1[0] == s2[0]

    cnf = CNFBuilder()

    # Create initial states
    st1 = tuple(cnf.const_word(v) for v in s1)
    st2 = tuple(cnf.const_word(v) for v in s2)

    # Free words
    w1_free = [cnf.free_word(f"W1_{57+i}") for i in range(4)]
    w2_free = [cnf.free_word(f"W2_{57+i}") for i in range(4)]

    # Apply dW57 constraint if specified
    if dw57_constraint is not None:
        # Constraint: W1[57] - W2[57] = dw57_constraint (mod 2^32)
        # Encode as: W1[57] = W2[57] + dw57_constraint
        # This means W1[57] is determined by W2[57]
        target = cnf.add_word(w2_free[0], cnf.const_word(dw57_constraint))
        cnf.eq_word(w1_free[0], target)

    # Apply bit fixes if specified
    if fix_w57_bits:
        for bit, (v1, v2) in fix_w57_bits.items():
            if v1 is not None:
                if v1:
                    cnf.clauses.append([w1_free[0][bit]])
                else:
                    cnf.clauses.append([-w1_free[0][bit]])
            if v2 is not None:
                if v2:
                    cnf.clauses.append([w2_free[0][bit]])
                else:
                    cnf.clauses.append([-w2_free[0][bit]])

    # Build schedule tail
    w1_61 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_free[2]), cnf.const_word(W1[54])),
        cnf.add_word(cnf.const_word(sigma0(W1[46])), cnf.const_word(W1[45])))
    w2_61 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_free[2]), cnf.const_word(W2[54])),
        cnf.add_word(cnf.const_word(sigma0(W2[46])), cnf.const_word(W2[45])))
    w1_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_free[3]), cnf.const_word(W1[55])),
        cnf.add_word(cnf.const_word(sigma0(W1[47])), cnf.const_word(W1[46])))
    w2_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_free[3]), cnf.const_word(W2[55])),
        cnf.add_word(cnf.const_word(sigma0(W2[47])), cnf.const_word(W2[46])))
    w1_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_61), cnf.const_word(W1[56])),
        cnf.add_word(cnf.const_word(sigma0(W1[48])), cnf.const_word(W1[47])))
    w2_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_61), cnf.const_word(W2[56])),
        cnf.add_word(cnf.const_word(sigma0(W2[48])), cnf.const_word(W2[47])))

    W1_sched = list(w1_free) + [w1_61, w1_62, w1_63]
    W2_sched = list(w2_free) + [w2_61, w2_62, w2_63]

    # 7 rounds
    for i in range(7):
        st1 = cnf.sha256_round_correct(st1, K[57+i], W1_sched[i])
    for i in range(7):
        st2 = cnf.sha256_round_correct(st2, K[57+i], W2_sched[i])

    # Collision
    for i in range(8):
        cnf.eq_word(st1[i], st2[i])

    return cnf


def test_constrained_strategies(m0=0x17149975, fill=0xffffffff, timeout=600):
    """Test multiple trail-constraining strategies with Kissat."""

    M1 = [m0] + [fill]*15
    M2 = list(M1); M2[0] ^= 0x80000000; M2[9] ^= 0x80000000
    s1, W1 = precompute_state(M1)
    s2, W2 = precompute_state(M2)

    print(f"Constrained sr=60 Search")
    print(f"M[0]=0x{m0:08x}, fill=0x{fill:08x}")
    print(f"{'='*60}")

    # Compute optimal dW57 strategies
    strategies = compute_optimal_dw57(s1, s2)
    print(f"\ndW[57] strategies:")
    print(f"{'Strategy':>15s} {'dW57':>12s} {'de57_hw':>8s} {'da57_hw':>8s} {'total':>6s}")
    for name, dw, de_hw, da_hw, total in strategies:
        print(f"{name:>15s} 0x{dw:08x} {de_hw:>8d} {da_hw:>8d} {total:>6d}")

    # Test each strategy: encode + solve
    print(f"\nSolving constrained instances (timeout={timeout}s):")
    print(f"{'='*60}")

    results = []
    for name, dw57, _, _, combined_err in strategies:
        print(f"\n  Strategy: {name} (dW57=0x{dw57:08x}, combined_err={combined_err})")

        cnf = encode_constrained_collision(m0, fill, dw57_constraint=dw57)
        nv, nc = cnf.next_var - 1, len(cnf.clauses)
        print(f"  CNF: {nv} vars, {nc} clauses")

        with tempfile.NamedTemporaryFile(suffix='.cnf', delete=False) as f:
            cnf_file = f.name
        cnf.write_dimacs(cnf_file)

        t0 = time.time()
        try:
            r = subprocess.run(["kissat", "-q", cnf_file],
                              capture_output=True, text=True, timeout=timeout)
            elapsed = time.time() - t0
            if r.returncode == 10:
                print(f"  *** SAT in {elapsed:.1f}s ***")
                results.append((name, 'SAT', elapsed))
            elif r.returncode == 20:
                print(f"  UNSAT in {elapsed:.1f}s")
                results.append((name, 'UNSAT', elapsed))
            else:
                print(f"  Unknown (rc={r.returncode}) in {elapsed:.1f}s")
                results.append((name, 'UNKNOWN', elapsed))
        except subprocess.TimeoutExpired:
            print(f"  TIMEOUT at {timeout}s")
            results.append((name, 'TIMEOUT', timeout))
        finally:
            os.unlink(cnf_file)

    # Also test unconstrained as baseline
    print(f"\n  Strategy: UNCONSTRAINED (baseline)")
    cnf = encode_constrained_collision(m0, fill)
    nv, nc = cnf.next_var - 1, len(cnf.clauses)
    print(f"  CNF: {nv} vars, {nc} clauses")

    with tempfile.NamedTemporaryFile(suffix='.cnf', delete=False) as f:
        cnf_file = f.name
    cnf.write_dimacs(cnf_file)

    t0 = time.time()
    try:
        r = subprocess.run(["kissat", "-q", cnf_file],
                          capture_output=True, text=True, timeout=timeout)
        elapsed = time.time() - t0
        if r.returncode == 10:
            print(f"  *** SAT in {elapsed:.1f}s ***")
            results.append(('unconstrained', 'SAT', elapsed))
        elif r.returncode == 20:
            print(f"  UNSAT in {elapsed:.1f}s")
            results.append(('unconstrained', 'UNSAT', elapsed))
        else:
            print(f"  Unknown in {elapsed:.1f}s")
            results.append(('unconstrained', 'UNKNOWN', elapsed))
    except subprocess.TimeoutExpired:
        print(f"  TIMEOUT at {timeout}s")
        results.append(('unconstrained', 'TIMEOUT', timeout))
    finally:
        os.unlink(cnf_file)

    print(f"\n{'='*60}")
    print(f"Summary:")
    for name, status, t in results:
        print(f"  {name:>15s}: {status} ({t:.1f}s)")


if __name__ == "__main__":
    m0 = int(sys.argv[1], 0) if len(sys.argv) > 1 else 0x17149975
    fill = int(sys.argv[2], 0) if len(sys.argv) > 2 else 0xffffffff
    timeout = int(sys.argv[3]) if len(sys.argv) > 3 else 600

    test_constrained_strategies(m0, fill, timeout)
