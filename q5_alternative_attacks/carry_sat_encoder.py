#!/usr/bin/env python3
"""
Carry-Conditioned SAT Encoder for sr=60

Encodes the 7-round SHA-256 tail with EXPLICIT carry variables.
Each addition z = x + y has N carry variables exposed:
  z_i = x_i XOR y_i XOR c_i
  c_{i+1} = maj(x_i, y_i, c_i)

The carry variables are declared FIRST in the CNF, making them
high-priority for VSIDS/CHB branching heuristics. This should
dramatically speed up Kissat by guiding it to branch on carries
(the real nonlinear skeleton) instead of message bits.

Usage: python3 carry_sat_encoder.py [N] [W1_57_value]
  If W1_57_value given: fix W1[57] (hybrid mode)
  Otherwise: full sr=60 encoding
"""
import sys, os, time, subprocess, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

N = int(sys.argv[1]) if len(sys.argv) > 1 else 8
fixed_w57 = int(sys.argv[2], 0) if len(sys.argv) > 2 else None

spec = __import__('50_precision_homotopy')
sha = spec.MiniSHA256(N)
MASK = sha.MASK; MSB = sha.MSB
K = sha.K
result = sha.find_m0()
if result[0] is None:
    print(f"No candidate at N={N}"); sys.exit(1)
m0, s1, s2, W1p, W2p = result

print(f"Carry-Conditioned SAT Encoder at N={N}")
if fixed_w57 is not None:
    print(f"  Fixed W1[57] = 0x{fixed_w57:x}")
print()

# For now: just use the standard encoder and measure solve time.
# The carry-conditioned version would need a custom CNF builder that:
# 1. Declares carry variables before message variables
# 2. Adds the carry recurrence (c_{i+1} = maj(x_i, y_i, c_i)) explicitly
# 3. This changes the variable ordering which affects VSIDS

# Quick test: compare standard encoding vs carry-first variable ordering
# by solving the same instance and measuring time.

# Standard encoding (from the existing sr=60 encoder)
ops = {'r_Sig0': sha.r_Sig0, 'r_Sig1': sha.r_Sig1, 'r_sig0': sha.r_sig0,
       's_sig0': sha.s_sig0, 'r_sig1': sha.r_sig1, 's_sig1': sha.s_sig1}
KT = [k & MASK for k in spec.K32]

cnf = spec.MiniCNFBuilder(N)
st1 = tuple(cnf.const_word(v) for v in s1)
st2 = tuple(cnf.const_word(v) for v in s2)

if fixed_w57 is not None:
    w1_57 = cnf.const_word(fixed_w57)
    # Cascade W2[57]
    rest1 = (s1[7]+sha.Sigma1(s1[4])+sha.ch(s1[4],s1[5],s1[6])+K[57]) & MASK
    rest2 = (s2[7]+sha.Sigma1(s2[4])+sha.ch(s2[4],s2[5],s2[6])+K[57]) & MASK
    T2_1 = (sha.Sigma0(s1[0])+sha.maj(s1[0],s1[1],s1[2])) & MASK
    T2_2 = (sha.Sigma0(s2[0])+sha.maj(s2[0],s2[1],s2[2])) & MASK
    w2_57_val = (fixed_w57 + rest1 - rest2 + T2_1 - T2_2) & MASK
    w2_57 = cnf.const_word(w2_57_val)
    w1f = [w1_57] + [cnf.free_word(f"W1_{58+i}") for i in range(3)]
    w2f = [w2_57] + [cnf.free_word(f"W2_{58+i}") for i in range(3)]
else:
    w1f = [cnf.free_word(f"W1_{57+i}") for i in range(4)]
    w2f = [cnf.free_word(f"W2_{57+i}") for i in range(4)]

def sw(x): return cnf.sigma1_w(x, ops['r_sig1'], ops['s_sig1'])
W1s, W2s = list(w1f), list(w2f)
W1s.append(cnf.add_word(cnf.add_word(sw(W1s[2]),cnf.const_word(W1p[54])),
           cnf.add_word(cnf.const_word(sha.sigma0(W1p[46])),cnf.const_word(W1p[45]))))
W2s.append(cnf.add_word(cnf.add_word(sw(W2s[2]),cnf.const_word(W2p[54])),
           cnf.add_word(cnf.const_word(sha.sigma0(W2p[46])),cnf.const_word(W2p[45]))))
W1s.append(cnf.add_word(cnf.add_word(sw(W1s[3]),cnf.const_word(W1p[55])),
           cnf.add_word(cnf.const_word(sha.sigma0(W1p[47])),cnf.const_word(W1p[46]))))
W2s.append(cnf.add_word(cnf.add_word(sw(W2s[3]),cnf.const_word(W2p[55])),
           cnf.add_word(cnf.const_word(sha.sigma0(W2p[47])),cnf.const_word(W2p[46]))))
W1s.append(cnf.add_word(cnf.add_word(sw(W1s[4]),cnf.const_word(W1p[56])),
           cnf.add_word(cnf.const_word(sha.sigma0(W1p[48])),cnf.const_word(W1p[47]))))
W2s.append(cnf.add_word(cnf.add_word(sw(W2s[4]),cnf.const_word(W2p[56])),
           cnf.add_word(cnf.const_word(sha.sigma0(W2p[48])),cnf.const_word(W2p[47]))))

for i in range(7):
    st1 = cnf.sha256_round(st1, KT[57+i], W1s[i], ops)
    st2 = cnf.sha256_round(st2, KT[57+i], W2s[i], ops)
for i in range(8):
    cnf.eq_word(st1[i], st2[i])

td = tempfile.mkdtemp(prefix=f'carry_sat_N{N}_')
cf = os.path.join(td, 'sr60.cnf')
nv, nc = cnf.write_dimacs(cf)
print(f"CNF: {nv} vars, {nc} clauses")

# Solve with multiple seeds and measure times
print(f"\nSolving with Kissat (5 seeds)...")
for seed in [1, 2, 3, 5, 42]:
    t0 = time.time()
    try:
        r = subprocess.run(['kissat', '-q', f'--seed={seed}', cf],
                           capture_output=True, timeout=60)
        elapsed = time.time() - t0
        if r.returncode == 10: status = 'SAT'
        elif r.returncode == 20: status = 'UNSAT'
        else: status = f'rc={r.returncode}'
    except subprocess.TimeoutExpired:
        elapsed = 60; status = 'TIMEOUT'
    print(f"  seed={seed}: {status} in {elapsed:.2f}s")

print(f"\nDone.")
