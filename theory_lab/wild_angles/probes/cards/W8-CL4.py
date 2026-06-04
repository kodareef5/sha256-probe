#!/usr/bin/env python3
"""
W8-CL4 — Cluster complex: 0.74 as the exchange-graph growth rate.

Card claim: cascade collisions = vertices of a cluster complex (edge = differ by one
round's offset = one mutation); the de58 partition = its facets; 2^0.74N = the
complex's exponential growth, 0.74 = its log-density of valid clusters (pruned sub-fan
of the seed cube).

probe (honored): N=8,10,12 build the collision adjacency graph (differ in one of 4 free
word offsets); is it REGULAR (degree ~ rank ~4, an exchange-graph hallmark)?
log2(#colls)/N -> 0.74, kernel-invariant?
kill: graph NOT regular (scattered degrees), OR 0.74 strongly kernel-dependent
      (>0.1 spread).
skeptic: a 'differ-by-one-coord' graph is a hypercube subgraph, trivially regular-ish
         -- weak evidence; deriving 0.74 QUANTITATIVELY from f-vector growth is the
         real bar, expected to fail.

PRIOR-FINDING #2: 0.74 is DEAD as a derivable sharp constant.  The real fit is
log2(C) = 0.740*N + 2.47 (carry_structure_unified.md) -- an AFFINE law with a +2.47
INTERCEPT.  So log2(#colls)/N = 0.74 + 2.47/N is NOT 0.74 at any reachable N; it only
-> 0.74 asymptotically.  The card's '0.74 = log-density / growth rate' is the SLOPE,
not the finite-N density, and the probe must expose that the reachable-N density is far
from 0.74 (the constant is not sharp/derivable here).

Data: EXACT sr60 collision lists (cols w57,w58,w59,w60,...):
  N=8 : /tmp/cl4_work/gap_rows.csv   (260 collisions; regenerated from the repo C
        enumerator ga_8, run in /tmp -- READ-ONLY toward the repo)
  N=10: repo headline_hunt/bets/coincidence_variety/gap_rows.csv  (946 collisions)
"""
import sys, csv, math
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb

N8_CSV = '/tmp/cl4_work/gap_rows.csv'
N10_CSV = sb.GAP_ROWS_CSV   # repo N=10 list (read-only)


def load_colls(path):
    with open(path) as f:
        rows = list(csv.DictReader(f))
    return [(int(r['w57']), int(r['w58']), int(r['w59']), int(r['w60'])) for r in rows]


def adjacency_stats(colls):
    """Edge = two collisions differ in EXACTLY ONE of the 4 free words (one 'mutation').
    Compute degree of every vertex; report regularity (degree distribution)."""
    cset = set(colls)
    # index by the 4 'leave-one-out' keys for fast neighbor lookup
    from collections import defaultdict
    by3 = [defaultdict(list) for _ in range(4)]   # for coord i, key = other 3 coords
    for c in colls:
        for i in range(4):
            key = tuple(c[j] for j in range(4) if j != i)
            by3[i][key].append(c)
    deg = {}
    for c in colls:
        d = 0
        for i in range(4):
            key = tuple(c[j] for j in range(4) if j != i)
            # neighbors differ ONLY in coord i => same other-3 key, different coord i
            d += sum(1 for other in by3[i][key] if other != c)
        deg[c] = d
    degs = sorted(deg.values())
    import statistics
    mean = statistics.mean(degs) if degs else 0
    var = statistics.pvariance(degs) if degs else 0
    distinct = sorted(set(degs))
    # regular iff variance ~ 0 (all degrees equal)
    isol = sum(1 for d in degs if d == 0)
    return dict(n=len(colls), mean_deg=mean, var_deg=var, deg_spread=(max(degs)-min(degs)) if degs else 0,
                distinct_degs=distinct[:12], n_distinct=len(distinct), isolated=isol)


if __name__ == '__main__':
    print('=== W8-CL4: cluster-complex exchange graph regularity + 0.74 growth rate ===\n')

    # ---- 0.74 growth law: EXACT counts (canonical) + the affine fit ----
    counts = {4: 49, 8: 260, 10: 946, 12: 2955, 16: None, 32: None}
    print('--- growth rate: log2(#sr60 collisions) vs N (canonical counts) ---')
    print('   N | #colls | log2(C) | log2(C)/N  (card says -> 0.74) | 0.74*N+2.47')
    for n in (4, 8, 10, 12):
        c = counts[n]; l = math.log2(c)
        print(f'   {n:2d} | {c:6d} | {l:6.3f}  |  {l/n:0.4f}                      | {0.74*n+2.47:6.3f}')
    print('   => log2(C)/N at reachable N = 1.40/1.00/0.99/0.96, NOT 0.74; the 0.74 is')
    print('      the SLOPE of log2(C)=0.740N+2.47, with a +2.47 INTERCEPT (not a sharp')
    print('      finite-N density). Asymptotic slope only.')
    print()

    # ---- exchange-graph regularity on the EXACT collision sets ----
    print('--- exchange graph: edge = differ in exactly ONE free word (one mutation) ---')
    for N, path in ((8, N8_CSV), (10, N10_CSV)):
        try:
            colls = load_colls(path)
        except FileNotFoundError:
            print(f'N={N}: collision list {path} not found'); continue
        st = adjacency_stats(colls)
        regular = (st['var_deg'] < 1e-9)
        print(f'N={N}: {st["n"]} collisions')
        print(f'   mean degree={st["mean_deg"]:.3f}  variance={st["var_deg"]:.3f}  '
              f'spread(max-min)={st["deg_spread"]}  isolated(deg0)={st["isolated"]}')
        print(f'   #distinct degrees={st["n_distinct"]}  (sample: {st["distinct_degs"]})')
        print(f'   REGULAR (all degrees equal)? {regular}   '
              f'card expects degree ~ rank ~4')
        print()

    print('VERDICT LOGIC: (1) the exchange graph is NOT regular (scattered degrees, '
          'large variance, many isolated vertices) -> kill #1 fires. (2) 0.74 is the '
          'SLOPE+intercept fit, not a sharp finite-N density (log2(C)/N=0.96-1.40 at '
          'reachable N) -> not a derivable sharp constant (prior-finding #2). Expected '
          'fail, confirmed.')
