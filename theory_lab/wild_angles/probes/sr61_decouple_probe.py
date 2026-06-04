#!/usr/bin/env python3
"""
sr=61 DECOUPLE probe (lead follow-up, not a catalog card).

Question: can g1 and h be zeroed INDEPENDENTLY (different freedoms), or are they bound to one freedom?
Uses the repo's N=10 collision data (gap_rows.csv: w57,w58,w59,w60,g1,g2,h). All rows are sr=60 collisions.

Tests:
  (A) distributions of g1,h — is 0 even reachable in THIS cascade?
  (B) is w60 a free lever, or is it PINNED by the collision given (w57,w58,w59)? (backward_construct solves w60)
  (C) are g1,h both functions of the SAME freedom (the triple), i.e. not independently controllable?
This decides whether the within-cascade freedom is already spent (=> the 2^-2N), motivating an OUTSIDE
freedom (de58 cross-cascade, or neutral bits).
"""
import sys
from collections import defaultdict
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb

rows = sb.load_gap_rows()
N = 10; MOD = 1 << N
def col(k): return [int(r[k]) % MOD for r in rows]
w57, w58, w59, w60, g1, g2, h = (col(x) for x in ['w57', 'w58', 'w59', 'w60', 'g1', 'g2', 'h'])
n = len(rows)
print(f"N={N}  rows(sr=60 collisions)={n}")

# (A) distributions
print("\n(A) value distributions:")
for name, v in [('g1', g1), ('h', h), ('g2', g2)]:
    s = set(v)
    print(f"   {name}: distinct={len(s):4d}  min={min(v):4d} max={max(v):4d}  contains 0? {0 in s}  count(==0)={v.count(0)}")

# (B) is w60 free, or pinned by the (w57,w58,w59) triple?
by_triple = defaultdict(list)
for i in range(n):
    by_triple[(w57[i], w58[i], w59[i])].append(i)
multi = {t: idx for t, idx in by_triple.items() if len(idx) > 1}
print(f"\n(B) collision coupling: {len(by_triple)} distinct (w57,w58,w59) triples among {n} collisions")
print(f"    triples appearing >1×: {len(multi)}")
if multi:
    w60_spread = [len({w60[i] for i in idx}) for idx in multi.values()]
    g1_spread  = [len({g1[i]  for i in idx}) for idx in multi.values()]
    h_spread   = [len({h[i]   for i in idx}) for idx in multi.values()]
    print(f"    within a repeated triple: max distinct w60={max(w60_spread)}, g1={max(g1_spread)}, h={max(h_spread)}")
    print(f"    => if w60 spread==1, w60 is PINNED by the collision (no free lever); if g1/h spread==1, the triple determines them")
else:
    print("    (triples are unique — collisions too sparse to see within-triple structure at N=10)")

# (C) does (w58,w60) determine g1? does (w57,w58,w59) determine h independent of w60?
def determines(support_cols, target):
    g = defaultdict(set)
    for i in range(n):
        g[tuple(c[i] for c in support_cols)].add(target[i])
    bad = sum(1 for s in g.values() if len(s) > 1)
    return bad, len(g)
for label, sup, tgt in [
    ("g1 by (w58,w60)", [w58, w60], g1),
    ("g1 by (w57,w58,w59)", [w57, w58, w59], g1),
    ("h  by (w57,w58,w59)", [w57, w58, w59], h),
    ("h  by (w57,w58,w59,w60)", [w57, w58, w59, w60], h),
]:
    bad, ngroups = determines(sup, tgt)
    print(f"(C) {label:28s}: {ngroups} groups, {bad} with >1 target value  -> {'DETERMINED' if bad == 0 else 'NOT determined'}")

# the headline: among the 946 collisions, how often is each condition individually near 0?
print(f"\n(D) sr=61 reachability in THIS cascade: P(g1=0)~{g1.count(0)/n:.4f}  P(h=0)~{h.count(0)/n:.4f}  "
      f"(expect ~2^-N={2**-N:.4f}); both=0: {sum(1 for i in range(n) if g1[i]==0 and h[i]==0)}")
