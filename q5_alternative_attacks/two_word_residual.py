#!/usr/bin/env python3
"""
two_word_residual.py — sr=60 with W[57]+W[58] fixed, only W[59]+W[60] free

After GPU-exhaustive optimization of W1[57] and W1[58]:
- W1[57] = optimal for da57=0 + min de57_err
- W1[58] = optimal for min state_hw after round 58

This leaves only W[59] and W[60] as free (128 bits total, 64 per message).
The SAT problem becomes MUCH smaller.

This is the deepest decomposition: 2 of 4 free words are fixed by
optimization, 2 remain for SAT. The CNF should be significantly smaller
and more propagation-friendly than the 4-word or 3-word versions.

Usage: python3 two_word_residual.py W1_57 W1_58 [m0] [fill] [timeout]
"""

import sys, os, time, subprocess, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from lib.sha256 import *
from lib.cnf_encoder import CNFBuilder


def encode_two_word_residual(m0, fill, W1_57, W1_58, dw57, dw58=None, timeout=3600):
    """Encode sr=60 with W[57] and W[58] both fixed."""
    M1 = [m0]+[fill]*15; M2 = list(M1); M2[0]^=0x80000000; M2[9]^=0x80000000
    s1, W1_pre = precompute_state(M1); s2, W2_pre = precompute_state(M2)
    assert s1[0] == s2[0]

    W2_57 = (W1_57 - dw57) & MASK

    # If dw58 specified, compute W2_58 from it; otherwise W2_58 is free
    if dw58 is not None:
        W2_58 = (W1_58 - dw58) & MASK
    else:
        W2_58 = None  # W2[58] will be free

    cnf = CNFBuilder()
    st1 = tuple(cnf.const_word(v) for v in s1)
    st2 = tuple(cnf.const_word(v) for v in s2)

    # W[57] fully constant
    w1_57 = cnf.const_word(W1_57)
    w2_57 = cnf.const_word(W2_57)

    # W[58]: W1 constant, W2 may be constant or free
    w1_58 = cnf.const_word(W1_58)
    if W2_58 is not None:
        w2_58 = cnf.const_word(W2_58)
    else:
        w2_58 = cnf.free_word("W2_58")

    # W[59], W[60] free for both messages
    w1_59 = cnf.free_word("W1_59")
    w2_59 = cnf.free_word("W2_59")
    w1_60 = cnf.free_word("W1_60")
    w2_60 = cnf.free_word("W2_60")

    # Build schedule tail
    # W[61] = sigma1(W[59]) + W_pre[54] + sigma0(W_pre[46]) + W_pre[45]
    w1_61 = cnf.add_word(cnf.add_word(cnf.sigma1_w(w1_59), cnf.const_word(W1_pre[54])),
                         cnf.add_word(cnf.const_word(sigma0(W1_pre[46])), cnf.const_word(W1_pre[45])))
    w2_61 = cnf.add_word(cnf.add_word(cnf.sigma1_w(w2_59), cnf.const_word(W2_pre[54])),
                         cnf.add_word(cnf.const_word(sigma0(W2_pre[46])), cnf.const_word(W2_pre[45])))
    # W[62] = sigma1(W[60]) + W_pre[55] + sigma0(W_pre[47]) + W_pre[46]
    w1_62 = cnf.add_word(cnf.add_word(cnf.sigma1_w(w1_60), cnf.const_word(W1_pre[55])),
                         cnf.add_word(cnf.const_word(sigma0(W1_pre[47])), cnf.const_word(W1_pre[46])))
    w2_62 = cnf.add_word(cnf.add_word(cnf.sigma1_w(w2_60), cnf.const_word(W2_pre[55])),
                         cnf.add_word(cnf.const_word(sigma0(W2_pre[47])), cnf.const_word(W2_pre[46])))
    # W[63] = sigma1(W[61]) + W_pre[56] + sigma0(W_pre[48]) + W_pre[47]
    w1_63 = cnf.add_word(cnf.add_word(cnf.sigma1_w(w1_61), cnf.const_word(W1_pre[56])),
                         cnf.add_word(cnf.const_word(sigma0(W1_pre[48])), cnf.const_word(W1_pre[47])))
    w2_63 = cnf.add_word(cnf.add_word(cnf.sigma1_w(w2_61), cnf.const_word(W2_pre[56])),
                         cnf.add_word(cnf.const_word(sigma0(W2_pre[48])), cnf.const_word(W2_pre[47])))

    W1s = [w1_57, w1_58, w1_59, w1_60, w1_61, w1_62, w1_63]
    W2s = [w2_57, w2_58, w2_59, w2_60, w2_61, w2_62, w2_63]

    for i in range(7):
        st1 = cnf.sha256_round_correct(st1, K[57+i], W1s[i])
    for i in range(7):
        st2 = cnf.sha256_round_correct(st2, K[57+i], W2s[i])
    for i in range(8):
        cnf.eq_word(st1[i], st2[i])

    nv = cnf.next_var - 1; nc = len(cnf.clauses)
    cf = cnf.stats.get('const_fold', 0); total = sum(cnf.stats.values())
    n_free = sum(32 for w in [w1_59,w2_59,w1_60,w2_60] if isinstance(w, list))
    if W2_58 is None: n_free += 32

    print(f"Two-word residual CNF: {nv} vars, {nc} clauses, {cf/total*100:.0f}% const-fold")
    print(f"Free bits: {n_free}")

    with tempfile.NamedTemporaryFile(suffix='.cnf', delete=False) as f:
        cnf_file = f.name
    cnf.write_dimacs(cnf_file)

    t0 = time.time()
    try:
        r = subprocess.run(['kissat', '-q', cnf_file],
                          capture_output=True, text=True, timeout=timeout)
        elapsed = time.time() - t0
        if r.returncode == 10: return 'SAT', elapsed
        elif r.returncode == 20: return 'UNSAT', elapsed
        return f'rc{r.returncode}', elapsed
    except subprocess.TimeoutExpired:
        return 'TIMEOUT', timeout
    finally:
        os.unlink(cnf_file)


if __name__ == "__main__":
    m0 = 0x44b49bc3; fill = 0x80000000
    dw57 = 0xddb49ee1  # for da57=0

    # Our best: W1[57]=0x3486 (de57=9)
    W1_57 = 0x00003486

    # Use W1[58]=0 for now (GPU sweep will find optimal)
    W1_58 = 0x00000000

    timeout = int(sys.argv[1]) if len(sys.argv) > 1 else 3600

    print(f"Two-Word Residual Test")
    print(f"M[0]=0x{m0:08x}, fill=0x{fill:08x}")
    print(f"W1[57]=0x{W1_57:08x} (da57=0, de57=9)")
    print(f"W1[58]=0x{W1_58:08x} (W2[58] free)")
    print(f"Timeout: {timeout}s")
    print(f"{'='*50}")

    status, t = encode_two_word_residual(m0, fill, W1_57, W1_58, dw57, timeout=timeout)
    print(f"Result: {status} in {t:.1f}s")
