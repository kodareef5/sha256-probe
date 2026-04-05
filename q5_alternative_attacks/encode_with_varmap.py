#!/usr/bin/env python3
"""
encode_with_varmap.py — Generate sr=60 CNF + variable map for Programmatic SAT

Produces two files:
  1. <name>.cnf — Standard DIMACS CNF (same as our encoder)
  2. <name>.varmap — JSON mapping variable IDs to semantic roles

The varmap tells the Programmatic SAT propagator which variables
to watch and what SHA-256 operations they correspond to.

Usage: python3 encode_with_varmap.py [m0] [fill] [output_prefix]
"""

import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from lib.sha256 import *
from lib.cnf_encoder import CNFBuilder


def encode_sr60_with_varmap(m0=0x44b49bc3, fill=0x80000000,
                             dw57_constraint=None, output_prefix="/tmp/sr60"):
    """Encode sr=60 and output CNF + variable map."""

    M1 = [m0] + [fill]*15
    M2 = list(M1); M2[0] ^= 0x80000000; M2[9] ^= 0x80000000
    s1, W1_pre = precompute_state(M1)
    s2, W2_pre = precompute_state(M2)
    assert s1[0] == s2[0]

    cnf = CNFBuilder()
    varmap = {
        'candidate': {'m0': hex(m0), 'fill': hex(fill)},
        'free_words': {},
        'state56': {},
        'schedule_constants': {},
        'additions': [],  # track each addition's carry chain
    }

    # State56 as constants
    st1 = tuple(cnf.const_word(v) for v in s1)
    st2 = tuple(cnf.const_word(v) for v in s2)

    # Record state56 values
    regs = ['a','b','c','d','e','f','g','h']
    for i in range(8):
        varmap['state56'][f's1_{regs[i]}56'] = hex(s1[i])
        varmap['state56'][f's2_{regs[i]}56'] = hex(s2[i])

    # Free words
    w1_free = [cnf.free_word(f"W1_{57+i}") for i in range(4)]
    w2_free = [cnf.free_word(f"W2_{57+i}") for i in range(4)]

    for i in range(4):
        varmap['free_words'][f'W1_{57+i}'] = [v for v in w1_free[i]]
        varmap['free_words'][f'W2_{57+i}'] = [v for v in w2_free[i]]

    # Apply da57=0 constraint if specified
    if dw57_constraint is not None:
        target = cnf.add_word(w2_free[0], cnf.const_word(dw57_constraint))
        cnf.eq_word(w1_free[0], target)
        varmap['constraints'] = {'da57_zero': True, 'dw57': hex(dw57_constraint)}

    # Build schedule tail with carry tracking
    def tracked_add(A, B, name):
        """Add with carry tracking for the varmap."""
        result, carries = cnf.add_word(A, B, track_carries=True)
        # Only record non-constant carries
        carry_vars = []
        for c in carries:
            if isinstance(c, int) and abs(c) > 1:
                carry_vars.append(c)
            else:
                carry_vars.append(None)
        varmap['additions'].append({
            'name': name,
            'carry_vars': carry_vars,
            'result_vars': [v for v in result]
        })
        return result

    # Schedule tail
    w1_61 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_free[2]), cnf.const_word(W1_pre[54])),
        cnf.add_word(cnf.const_word(sigma0(W1_pre[46])), cnf.const_word(W1_pre[45])))
    w2_61 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_free[2]), cnf.const_word(W2_pre[54])),
        cnf.add_word(cnf.const_word(sigma0(W2_pre[46])), cnf.const_word(W2_pre[45])))
    w1_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_free[3]), cnf.const_word(W1_pre[55])),
        cnf.add_word(cnf.const_word(sigma0(W1_pre[47])), cnf.const_word(W1_pre[46])))
    w2_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_free[3]), cnf.const_word(W2_pre[55])),
        cnf.add_word(cnf.const_word(sigma0(W2_pre[47])), cnf.const_word(W2_pre[46])))
    w1_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_61), cnf.const_word(W1_pre[56])),
        cnf.add_word(cnf.const_word(sigma0(W1_pre[48])), cnf.const_word(W1_pre[47])))
    w2_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_61), cnf.const_word(W2_pre[56])),
        cnf.add_word(cnf.const_word(sigma0(W2_pre[48])), cnf.const_word(W2_pre[47])))

    W1_sched = list(w1_free) + [w1_61, w1_62, w1_63]
    W2_sched = list(w2_free) + [w2_61, w2_62, w2_63]

    # 7 rounds with carry-tracked additions for T1
    for i in range(7):
        st1 = cnf.sha256_round_correct(st1, K[57+i], W1_sched[i])
    for i in range(7):
        st2 = cnf.sha256_round_correct(st2, K[57+i], W2_sched[i])

    # Collision
    for i in range(8):
        cnf.eq_word(st1[i], st2[i])

    # Write CNF
    cnf_file = f"{output_prefix}.cnf"
    nv, nc = cnf.write_dimacs(cnf_file)

    # Write varmap
    varmap['cnf_stats'] = {'vars': nv, 'clauses': nc}
    varmap['encoder_stats'] = dict(cnf.stats)
    varmap_file = f"{output_prefix}.varmap.json"
    with open(varmap_file, 'w') as f:
        json.dump(varmap, f, indent=2)

    print(f"Generated: {cnf_file} ({nv} vars, {nc} clauses)")
    print(f"Varmap: {varmap_file}")
    print(f"  Free words: {len(varmap['free_words'])} ({sum(len(v) for v in varmap['free_words'].values())} vars)")
    print(f"  Additions tracked: {len(varmap['additions'])}")

    return cnf_file, varmap_file


if __name__ == "__main__":
    m0 = int(sys.argv[1], 0) if len(sys.argv) > 1 else 0x44b49bc3
    fill = int(sys.argv[2], 0) if len(sys.argv) > 2 else 0x80000000
    prefix = sys.argv[3] if len(sys.argv) > 3 else "/tmp/sr60_progsat"

    # Compute dw57 for da57=0
    M1 = [m0]+[fill]*15; M2 = list(M1); M2[0]^=0x80000000; M2[9]^=0x80000000
    s1, W1 = precompute_state(M1); s2, W2 = precompute_state(M2)
    d_h56=(s1[7]-s2[7])&MASK; d_Sig1=(Sigma1(s1[4])-Sigma1(s2[4]))&MASK
    d_Ch=(Ch(s1[4],s1[5],s1[6])-Ch(s2[4],s2[5],s2[6]))&MASK
    C_T1=(d_h56+d_Sig1+d_Ch)&MASK
    d_Sig0=(Sigma0(s1[0])-Sigma0(s2[0]))&MASK
    d_Maj=(Maj(s1[0],s1[1],s1[2])-Maj(s2[0],s2[1],s2[2]))&MASK
    C_T2=(d_Sig0+d_Maj)&MASK
    dw57=(-(C_T1+C_T2))&MASK

    encode_sr60_with_varmap(m0, fill, dw57_constraint=dw57, output_prefix=prefix)
