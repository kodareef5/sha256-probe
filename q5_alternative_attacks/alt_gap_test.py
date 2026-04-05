#!/usr/bin/env python3
"""
alt_gap_test.py — Test alternative gap placements for sr=60

Standard sr=60: free W[57..60], enforce W[61..63] (3 enforced rounds)
Alternative:    free W[58..61], enforce W[62..63] (2 enforced rounds!)

The key question: does having only 2 enforced rounds (instead of 3)
make the problem easier, even though we lose W[57] freedom?

With W[58..61] free:
  - W[57] is schedule-determined (from W[55], W[50], W[42], W[41])
  - W[58..61] are free (4 degrees of freedom)
  - W[62] = sigma1(W[60]) + W[55] + sigma0(W[47]) + W[46]
  - W[63] = sigma1(W[61]) + W[56] + sigma0(W[48]) + W[47]

The dW[62] obstruction (if any) might be different from dW[61].

Usage: python3 alt_gap_test.py [m0] [fill] [timeout]
"""

import sys, os, time, subprocess, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from lib.sha256 import *
from lib.cnf_encoder import CNFBuilder


def encode_alt_gap(m0, fill, timeout=300):
    """Encode sr=60 with alternative gap placement: free W[58..61]."""
    M1 = [m0]+[fill]*15; M2 = list(M1); M2[0]^=0x80000000; M2[9]^=0x80000000
    s1, W1_pre = precompute_state(M1)
    s2, W2_pre = precompute_state(M2)
    assert s1[0] == s2[0]

    cnf = CNFBuilder()
    st1 = tuple(cnf.const_word(v) for v in s1)
    st2 = tuple(cnf.const_word(v) for v in s2)

    # W[57] is schedule-determined (NOT free)
    W1_57 = add(sigma1(W1_pre[55]), W1_pre[50], sigma0(W1_pre[42]), W1_pre[41])
    W2_57 = add(sigma1(W2_pre[55]), W2_pre[50], sigma0(W2_pre[42]), W2_pre[41])
    w1_57 = cnf.const_word(W1_57)
    w2_57 = cnf.const_word(W2_57)

    # Free words: W[58..61]
    w1_free = [cnf.free_word(f"W1_{58+i}") for i in range(4)]
    w2_free = [cnf.free_word(f"W2_{58+i}") for i in range(4)]

    # W[62] = sigma1(W[60]) + W[55] + sigma0(W[47]) + W[46]
    w1_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_free[2]), cnf.const_word(W1_pre[55])),
        cnf.add_word(cnf.const_word(sigma0(W1_pre[47])), cnf.const_word(W1_pre[46])))
    w2_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_free[2]), cnf.const_word(W2_pre[55])),
        cnf.add_word(cnf.const_word(sigma0(W2_pre[47])), cnf.const_word(W2_pre[46])))

    # W[63] = sigma1(W[61]) + W[56] + sigma0(W[48]) + W[47]
    w1_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_free[3]), cnf.const_word(W1_pre[56])),
        cnf.add_word(cnf.const_word(sigma0(W1_pre[48])), cnf.const_word(W1_pre[47])))
    w2_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_free[3]), cnf.const_word(W2_pre[56])),
        cnf.add_word(cnf.const_word(sigma0(W2_pre[48])), cnf.const_word(W2_pre[47])))

    # Schedule: W[57], W[58..61](free), W[62], W[63]
    W1_sched = [w1_57] + list(w1_free) + [w1_62, w1_63]
    W2_sched = [w2_57] + list(w2_free) + [w2_62, w2_63]

    # 7 rounds
    for i in range(7):
        st1 = cnf.sha256_round_correct(st1, K[57+i], W1_sched[i])
    for i in range(7):
        st2 = cnf.sha256_round_correct(st2, K[57+i], W2_sched[i])

    # Collision
    for i in range(8):
        cnf.eq_word(st1[i], st2[i])

    nv, nc = cnf.next_var - 1, len(cnf.clauses)
    cf = cnf.stats.get('const_fold', 0)
    total = sum(cnf.stats.values())

    # Analyze: what is dW[57] under this gap placement?
    dW57 = W1_57 ^ W2_57
    print(f"  dW[57] (enforced) = 0x{dW57:08x} (hw={hw(dW57)})")
    print(f"  CNF: {nv} vars, {nc} clauses, {cf}/{total} const-folded ({cf/total*100:.0f}%)")

    with tempfile.NamedTemporaryFile(suffix='.cnf', delete=False) as f:
        cnf_file = f.name
    cnf.write_dimacs(cnf_file)

    t0 = time.time()
    try:
        r = subprocess.run(['kissat', '-q', cnf_file],
                          capture_output=True, text=True, timeout=timeout)
        elapsed = time.time() - t0
        if r.returncode == 10: return 'SAT', elapsed, nv, nc
        elif r.returncode == 20: return 'UNSAT', elapsed, nv, nc
        return f'rc{r.returncode}', elapsed, nv, nc
    except subprocess.TimeoutExpired:
        return 'TIMEOUT', timeout, nv, nc
    finally:
        os.unlink(cnf_file)


if __name__ == "__main__":
    m0 = int(sys.argv[1], 0) if len(sys.argv) > 1 else 0x17149975
    fill = int(sys.argv[2], 0) if len(sys.argv) > 2 else 0xffffffff
    timeout = int(sys.argv[3]) if len(sys.argv) > 3 else 300

    candidates = [
        (0x17149975, 0xffffffff, "PUBLISHED"),
        (0x44b49bc3, 0x80000000, "BEST"),
        (0x9cfea9ce, 0x00000000, "fill_00"),
    ]

    print(f"Alternative Gap Placement Test: free W[58..61], enforce W[57,62,63]")
    print(f"Timeout: {timeout}s per candidate")
    print(f"{'='*60}")

    for m0, fill, label in candidates:
        print(f"\n{label} (M[0]=0x{m0:08x}, fill=0x{fill:08x}):")
        status, t, nv, nc = encode_alt_gap(m0, fill, timeout)
        print(f"  Result: {status} in {t:.1f}s")

    # Also test standard gap for comparison
    print(f"\n{'='*60}")
    print(f"Comparison: standard gap (free W[57..60]) for PUBLISHED:")
    from q5_alternative_attacks.constrained_sr60 import encode_constrained_collision
    cnf = encode_constrained_collision(0x17149975, 0xffffffff)
    nv, nc = cnf.next_var - 1, len(cnf.clauses)
    print(f"  Standard CNF: {nv} vars, {nc} clauses")
