#!/usr/bin/env python3
"""
Script 37: Analytic Squash — Delete Round 63

Instead of encoding Round 63 as SAT circuit and constraining the output
to collide (H1==H2), we analytically substitute Round 63's equations
INTO the collision constraint.

Round 63 produces:
  a[63] = T1[63] + T2[63]
  e[63] = d[62] + T1[63]
  b[63] = a[62], c[63] = b[62], d[63] = c[62]
  f[63] = e[62], g[63] = f[62], h[63] = g[62]

The collision H1==H2 requires state1[63] == state2[63] for all 8 registers.

For the shift registers (b,c,d,f,g,h), the collision directly constrains
the Round 62 state:
  b1[63]==b2[63] => a1[62]==a2[62] (da[62]=0)
  c1[63]==c2[63] => b1[62]==b2[62] (db[62]=0)
  d1[63]==d2[63] => c1[62]==c2[62] (dc[62]=0)
  f1[63]==f2[63] => e1[62]==e2[62] (de[62]=0)
  g1[63]==g2[63] => f1[62]==f2[62] (df[62]=0)
  h1[63]==h2[63] => g1[62]==g2[62] (dg[62]=0)

For the computed registers (a,e):
  a1[63]==a2[63] => T1_1[63]+T2_1[63] == T1_2[63]+T2_2[63]
  e1[63]==e2[63] => d1[62]+T1_1[63] == d2[62]+T1_2[63]

Since dc[62]=0 (from d[63] collision), d1[62]==d2[62], so:
  e1[63]==e2[63] => T1_1[63] == T1_2[63]

And if T1_1==T1_2 and T2_1==T2_2, then a1[63]==a2[63] automatically.

T1[63] = g[62] + Sigma1(e[62]) + Ch(e[62],f[62],g[62]) + K[63] + W[63]
Since dg[62]=0, de[62]=0, df[62]=0 (from the shift register):
  T1_1[63] == T1_2[63] requires ONLY dW1[63]==dW2[63].

Similarly:
  T2[63] = Sigma0(a[62]) + Maj(a[62],b[62],c[62])
Since da[62]=0, db[62]=0, dc[62]=0:
  T2_1[63] == T2_2[63] AUTOMATICALLY!

RESULT: The collision at Round 63 reduces to:
  1. da[62]=0, db[62]=0, dc[62]=0, de[62]=0, df[62]=0, dg[62]=0
     (6 register diffs must be 0 at Round 62)
  2. dW[63]=0 (schedule words at position 63 must match)
  3. dd[62] and dh[62] are FREE (they propagate through shift to
     d[63]=c[62] and h[63]=g[62], which are already constrained)

Wait — dd[62] = dc[61], and dh[62] = dg[61]. These propagate from
earlier rounds and are determined by the free words, not independently.

Actually, let me reconsider. After Round 62:
  b[63]=a[62], c[63]=b[62], d[63]=c[62], f[63]=e[62], g[63]=f[62], h[63]=g[62]

For collision at Round 63 (all 8 registers equal):
  da[63]=0, db[63]=0, dc[63]=0, dd[63]=0, de[63]=0, df[63]=0, dg[63]=0, dh[63]=0

This translates to constraints on Round 62:
  da[62]=0 (from db[63]=0, since b[63]=a[62])
  db[62]=0 (from dc[63]=0)
  dc[62]=0 (from dd[63]=0)
  de[62]=0 (from df[63]=0)
  df[62]=0 (from dg[63]=0)
  dg[62]=0 (from dh[63]=0)

Plus: da[63]=0 and de[63]=0 which involve the Round 63 computation.

But since 6 of 8 registers at Round 62 are already forced to 0, the
Round 63 computation of a[63] and e[63] becomes very constrained.

The KEY insight: we can encode rounds 57-62 (6 rounds) and put the
collision constraints DIRECTLY on Round 62's state, without encoding
Round 63 at all. The a[63] and e[63] constraints become algebraic
conditions on the Round 62 state + W[63].

Since W[63] is schedule-enforced (not free), dW[63] is determined
by the free words through the schedule cascade. If the 6 register
diffs at Round 62 are all 0, AND dW[63]=0 (which is determined by
the schedule), the collision is guaranteed.

So the squash is: encode 6 rounds (57-62), constrain 6 of 8 register
diffs to 0 at Round 62, and add a constraint that dW[63]=0.

This removes one full round of SAT circuit (~3000 vars, ~6000 clauses).
"""

import sys
import os
import time
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from importlib import import_module
enc = import_module('13_custom_cnf_encoder')


def encode_squashed(mode="sr60", timeout_sec=3600):
    """
    Encode sr=60 with Round 63 analytically squashed.

    Instead of 7 rounds + H1==H2, we encode:
      6 rounds (57-62) + direct state constraints at Round 62
      + dW[63]==0 constraint
    """
    M1 = [0x17149975] + [0xffffffff] * 15
    M2 = M1.copy()
    M2[0] ^= 0x80000000
    M2[9] ^= 0x80000000

    state1, W1_pre = enc.precompute_state(M1)
    state2, W2_pre = enc.precompute_state(M2)

    n_free = 5 if mode == "sr59" else 4
    cnf = enc.CNFBuilder()

    s1 = tuple(cnf.const_word(v) for v in state1)
    s2 = tuple(cnf.const_word(v) for v in state2)

    w1_free = [cnf.free_word(f"W1_{57+i}") for i in range(n_free)]
    w2_free = [cnf.free_word(f"W2_{57+i}") for i in range(n_free)]

    W1_schedule = list(w1_free)
    W2_schedule = list(w2_free)

    if mode == "sr60":
        w1_61 = cnf.add_word(
            cnf.add_word(cnf.sigma1_w(w1_free[2]), cnf.const_word(W1_pre[54])),
            cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[46])), cnf.const_word(W1_pre[45])))
        w2_61 = cnf.add_word(
            cnf.add_word(cnf.sigma1_w(w2_free[2]), cnf.const_word(W2_pre[54])),
            cnf.add_word(cnf.const_word(enc.sigma0_py(W2_pre[46])), cnf.const_word(W2_pre[45])))
        W1_schedule.append(w1_61)
        W2_schedule.append(w2_61)

    # Schedule for W[62]
    w60_idx = 3
    w1_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W1_schedule[w60_idx]), cnf.const_word(W1_pre[55])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[47])), cnf.const_word(W1_pre[46])))
    w2_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W2_schedule[w60_idx]), cnf.const_word(W2_pre[55])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W2_pre[47])), cnf.const_word(W2_pre[46])))

    # Schedule for W[63] (needed for dW[63] constraint)
    w61_idx = 4
    w1_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W1_schedule[w61_idx]), cnf.const_word(W1_pre[56])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[48])), cnf.const_word(W1_pre[47])))
    w2_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W2_schedule[w61_idx]), cnf.const_word(W2_pre[56])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W2_pre[48])), cnf.const_word(W2_pre[47])))

    # Only need rounds 57-62 (6 rounds instead of 7)
    W1_tail = list(W1_schedule) + [w1_62]  # 5 or 6 words for rounds 57-62
    W2_tail = list(W2_schedule) + [w2_62]

    st1 = s1
    for i in range(6):  # Only 6 rounds!
        st1 = cnf.sha256_round_correct(st1, enc.K[57 + i], W1_tail[i])

    st2 = s2
    for i in range(6):
        st2 = cnf.sha256_round_correct(st2, enc.K[57 + i], W2_tail[i])

    # Squashed collision constraints on Round 62 state:
    # From the shift register analysis:
    #   b[63]=a[62] -> da[62]=0
    #   c[63]=b[62] -> db[62]=0
    #   d[63]=c[62] -> dc[62]=0
    #   f[63]=e[62] -> de[62]=0
    #   g[63]=f[62] -> df[62]=0
    #   h[63]=g[62] -> dg[62]=0

    reg_names = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    # Constrain da, db, dc, de, df, dg (indices 0,1,2,4,5,6)
    constrained = [0, 1, 2, 4, 5, 6]
    for idx in constrained:
        cnf.eq_word(st1[idx], st2[idx])

    # dd[62] and dh[62] are NOT directly constrained by shift register
    # But they ARE constrained by the a[63] and e[63] collision:
    #
    # Since da[62]=db[62]=dc[62]=de[62]=df[62]=dg[62]=0,
    # at Round 63:
    #   T2 = Sigma0(a[62]) + Maj(a[62],b[62],c[62])
    #   Since da=db=dc=0, T2_1 == T2_2 automatically.
    #
    #   T1 = h[62] + Sigma1(e[62]) + Ch(e[62],f[62],g[62]) + K[63] + W[63]
    #   h[62]=g[61], and dg at round 62 = 0, so dh[62] = dg[61]
    #   Wait, h[62] is the h register AFTER round 62.
    #   In the shift register: h[r+1] = g[r]. So h[62] = g[61].
    #   But we're looking at state AFTER 6 rounds (rounds 57-62).
    #   st1[7] = h after round 62 = g after round 61.
    #
    #   For T1 at round 63 to match: need dh[62]=0 AND dW[63]=0.
    #   dh[62] = dg[61] which is st1[6] vs st2[6] after round 61
    #   (that's within our 6-round circuit, so it's determined by the encoding)
    #
    #   Actually, let me re-examine. After our 6 rounds, st1 and st2
    #   represent the state after Round 62. The registers are:
    #   st[0]=a[62], st[1]=a[61], st[2]=a[60], st[3]=a[59]
    #   st[4]=e[62], st[5]=e[61], st[6]=e[60], st[7]=e[59]
    #   Wait no, the shift is: (a_new, a_prev, b_prev, c_prev, e_new, e_prev, f_prev, g_prev)
    #   After 6 rounds from round 57:
    #     st[0] = a[62]  (latest a)
    #     st[1] = a[61]  (= b[62])
    #     st[2] = a[60]  (= c[62] = b[61])
    #     st[3] = a[59]  (= d[62] = c[61])
    #     st[4] = e[62]  (latest e)
    #     st[5] = e[61]  (= f[62])
    #     st[6] = e[60]  (= g[62] = f[61])
    #     st[7] = e[59]  (= h[62] = g[61])
    #
    # So: dd[62] = d_diff = st1[3] vs st2[3] = da[59]
    #     dh[62] = h_diff = st1[7] vs st2[7] = de[59]
    #
    # For the full collision, we also need:
    #   dd[62]=0 (for... actually dd[62] maps to d[63]=c[62] which is already constrained)
    #   Wait, I already constrained dc[62]=0, which is st1[2]==st2[2].
    #   And dd[63] = c[62], so dd[63] collision = dc[62]=0, already constrained.
    #
    # For a[63] = T1[63] + T2[63]:
    #   T2 depends on a[62],b[62],c[62] — all diffs zero. So dT2=0.
    #   T1 depends on h[62],e[62],f[62],g[62],K[63],W[63]
    #     — de[62]=0, df[62]=0, dg[62]=0 already constrained
    #     — dh[62] = st1[7] vs st2[7]
    #   So T1_1 - T1_2 = dh[62] + dW[63] (since Sigma1,Ch have zero diff)
    #   For dT1=0: dh[62] + dW[63] = 0 (mod 2^32)
    #
    # For e[63] = d[62] + T1[63]:
    #   dd[62] = st1[3] vs st2[3]
    #   de[63] = dd[62] + dT1 = dd[62] + dh[62] + dW[63]
    #   For de[63]=0: dd[62] + dh[62] + dW[63] = 0
    #
    # So we need:
    #   dh[62] + dW[63] = 0  (from da[63]=0)
    #   dd[62] + dh[62] + dW[63] = 0  (from de[63]=0)
    #   Subtracting: dd[62] = 0
    #
    # So dd[62]=0 is also required! That's st1[3]==st2[3].
    # And then dh[62] = -dW[63] (mod 2^32).
    # This means dh[62] is determined by dW[63].

    # Add dd[62] = 0 constraint
    cnf.eq_word(st1[3], st2[3])

    # Now we need: dh[62] + dW[63] = 0 (mod 2^32)
    # i.e., h1[62] + W1[63] = h2[62] + W2[63] (mod 2^32)
    # i.e., st1[7] + w1_63 = st2[7] + w2_63
    lhs = cnf.add_word(st1[7], w1_63)
    rhs = cnf.add_word(st2[7], w2_63)
    cnf.eq_word(lhs, rhs)

    # That's it! We've encoded the FULL collision without Round 63's circuit.
    # Total constraints: 7 register equalities + 1 algebraic condition
    # vs the standard 8 register equalities after 7 rounds

    cnf_file = f"/tmp/{mode}_squashed.cnf"
    cnf.write_dimacs(cnf_file)
    nv = cnf.next_var - 1
    nc = len(cnf.clauses)

    return cnf_file, nv, nc


def main():
    timeout = int(sys.argv[1]) if len(sys.argv) > 1 else 3600

    print("=" * 70, flush=True)
    print("ANALYTIC SQUASH — Round 63 Deleted", flush=True)
    print("Collision constraints mapped directly to Round 62 state", flush=True)
    print("=" * 70, flush=True)

    # First test on sr=59 as baseline
    for mode in ["sr59", "sr60"]:
        to = min(timeout, 300) if mode == "sr59" else timeout
        print(f"\n{'='*60}", flush=True)
        print(f"Mode: {mode} (squashed: 6 rounds instead of 7)", flush=True)

        cnf_file, nv, nc = encode_squashed(mode, to)
        print(f"  {nv} vars, {nc} clauses", flush=True)

        if mode == "sr59":
            print(f"  Baseline (7 rounds): 10704 vars, 44983 clauses", flush=True)
            print(f"  Savings: {10704 - nv} vars, {44983 - nc} clauses", flush=True)

        print(f"  Running Kissat ({to}s)...", flush=True)
        t0 = time.time()
        r = subprocess.run(["timeout", str(to), "kissat", "-q", cnf_file],
                           capture_output=True, text=True, timeout=to + 30)
        elapsed = time.time() - t0

        if r.returncode == 10:
            print(f"  [!!!] SAT in {elapsed:.1f}s!", flush=True)
            if mode == "sr59":
                print(f"  Speedup vs baseline: {220/elapsed:.2f}x", flush=True)
        elif r.returncode == 20:
            print(f"  [-] UNSAT in {elapsed:.1f}s", flush=True)
        else:
            print(f"  [!] TIMEOUT after {elapsed:.1f}s", flush=True)


if __name__ == "__main__":
    main()
