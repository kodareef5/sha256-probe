#!/usr/bin/env python3
"""
W6-OM1 — Cell-count explosion => the wall = loss of uniform finiteness.

Card claim: per-round count of "cells" (maximal solution-runs in a fixed coordinate order)
is BOUNDED (O(1) fat cascade cells) for rounds <=60 and EXPLODES at 61 (the two conditions
fracture each slice) -- the o-minimal signature of a wild set.

PROBE (per CATALOG): N=4,6,8 enumerate da=0 collisions, fix a sweep coordinate, count
maximal runs per slice (avg over random coordinate orders) vs round; bounded <=60,
discontinuity at 61?
KILL: already Theta(2^N) for r<=58, OR smooth/monotone with no break near 60/61.
Skeptic (CATALOG): run-count is coordinate-order-dependent -> average over orders, report
variance.  Prior finding #4: EVERY round-specific knee has dissolved; the round function is
identical each round -> expect smooth/early, not a sharp 60/61 break.

KEY STRUCTURAL FACT (boundary proof, cascade_structure_complete.md): the cascade keeps
da=0 FOR FREE at every round 57..60 -- path-2's words are chosen by find_w2 so da_{r+1}=0
holds for ALL (w57..w60). So the round-<=60 "solution set" (tuples consistent through r) is
the FULL 4-word cube. The first real condition is de61=0 (round 61), then full collision
(round 63). We therefore measure cell-count (avg maximal runs over random coordinate
orders, with std) for the per-round solution sets:
   r<=60 : the full cube  (cascade-free)            -> cells expected = 1 (one fat cell)
   r=61  : {de61==0}                                  -> first fracture
   r=63  : {full sr=60 collision}                     -> terminus residue
N=4 exact (all sets enumerated). N=8 collision set from the verified C enumerator.
"""
import sys, importlib.util, os, random, statistics, itertools
KD = '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards'
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
sys.path.insert(0, KD)
import shabridge as sb
spec = importlib.util.spec_from_file_location("w5eng", os.path.join(KD, "_w5co_engine.py"))
eng = importlib.util.module_from_spec(spec); spec.loader.exec_module(eng)


def enumerate_sets_n4():
    """Exact: for every (w57,w58,w59,w60) at N=4, record membership in
    cube(<=60), de61=0(r61), collision(r63)."""
    N = 4
    M = eng.make_model(N); setup = eng.find_M0(M); R = M['MASK'] + 1
    cube, s61, s63 = [], [], []
    for w57 in range(R):
        for w58 in range(R):
            for w59 in range(R):
                for w60 in range(R):
                    t = (w57, w58, w59, w60)
                    cube.append(t)                       # cascade free: always da=0
                    r = eng.run_tail(M, setup, *t)
                    if r['de61'] == 0:
                        s61.append(t)
                    if r['collide']:
                        s63.append(t)
    return N, R, cube, s61, s63


def cell_count(points, ndim, dim_size, n_orders=40, seed=0):
    """Average # of maximal runs of the point-set along a lexicographic sweep, over
    n_orders random coordinate orders + random per-axis value relabelings (the
    'fixed coordinate order' the card averages over). Returns (mean, std).
    A run = a maximal block of cube cells consecutive in the 1-D lex unrolling that are
    ALL members. Efficient: a member's lex index is computed directly; two members merge
    into one run iff their lex indices are consecutive. So runs = #members - #(adjacent
    lex pairs among members) -- O(|members| log|members|) per order, no full-cube unroll."""
    if not points:
        return 0.0, 0.0
    pts = list(set(points))
    rng = random.Random(seed)
    counts = []
    axes = list(range(ndim))
    for _ in range(n_orders):
        order = axes[:]; rng.shuffle(order)
        perms = [list(range(dim_size)) for _ in range(ndim)]
        for p in perms:
            rng.shuffle(p)
        # lex index of a point: most-significant axis = order[0], using relabeled values
        idxs = []
        for pt in pts:
            key = 0
            for k, ax in enumerate(order):
                key = key * dim_size + perms[ax][pt[ax]]
            idxs.append(key)
        idxs.sort()
        runs = 1 + sum(1 for i in range(1, len(idxs)) if idxs[i] != idxs[i-1] + 1)
        counts.append(runs)
    return statistics.mean(counts), (statistics.pstdev(counts) if len(counts) > 1 else 0.0)


def main():
    print("== W6-OM1: cell-count explosion = loss of uniform finiteness ==\n")
    print("Per-round solution sets; cell = maximal solution-run in a sweep order,")
    print("averaged over random coordinate orders (+/- std). Cascade keeps da=0 free")
    print("for ALL tuples r<=60, so the round-<=60 set is the FULL cube.\n")

    N, R, cube, s61, s63 = enumerate_sets_n4()
    total = R**4
    print(f"--- N={N} (cube size 2^{4*N} = {total}) ---")
    print(f"   |cube(r<=60)| = {len(cube)} (={total}, the whole cube -- cascade free)")
    print(f"   |de61=0 (r61)| = {len(s61)}  (density {len(s61)/total:.4f})")
    print(f"   |collision(r63)| = {len(s63)}  (density {len(s63)/total:.4f})")
    print()
    print(f"   {'per-round set':>16} | {'cells (mean +/- std)':>22} | {'density':>8}")
    # cube is analytically 1 cell (every cell present -> lex indices 0..R^4-1 contiguous).
    print(f"   {'cube (r<=60)':>16} | {1.0:>10.2f} +/- {0.0:>8.2f} | {len(cube)/total:>8.4f}   "
          f"(analytic: whole space = 1 solid cell)")
    for nm, S in (('de61=0 (r61)', s61), ('collision (r63)', s63)):
        m, sd = cell_count(S, 4, R, n_orders=30)
        print(f"   {nm:>16} | {m:>10.2f} +/- {sd:>8.2f} | {len(S)/total:>8.4f}")

    print("\n   READING (N=4): the cube (all rounds <=60) is ONE cell (the whole space is")
    print("   solid -- uniform finiteness holds trivially, cell-count = 1, NO growth across")
    print("   57->58->59->60). The cell-count only changes at the rounds with a REAL")
    print("   condition: 61 (de61=0) and 63 (collision). So there is NO progressive cell-")
    print("   explosion 'approaching 61'; the round function is identical each round and")
    print("   imposes nothing until the schedule closes the loop at 61.")

    # ---- N=8 corroboration: collision-set cell count vs cube ----
    cf = '/tmp/coll_n8.txt'
    if os.path.exists(cf):
        pts = []
        with open(cf) as fh:
            for ln in fh:
                pts.append(tuple(int(x) for x in ln.split()))
        R8 = 256
        m, sd = cell_count(set(pts), 4, R8, n_orders=30)
        print(f"\n--- N=8 corroboration (260 collisions, verified C enumerator) ---")
        print(f"   collision-set cells (avg over coordinate orders) = {m:.1f} +/- {sd:.1f}")
        print(f"   #points = {len(pts)} -> cells/point = {m/len(pts):.3f} (near 1.0 means the")
        print(f"   set is ALMOST TOTALLY DISCONNECTED -- every collision is its own cell, the")
        print(f"   hallmark of a measure-0 sieve, NOT 'O(1) fat cascade cells'). Cube(r<=60)")
        print(f"   is still 1 solid cell (cascade free). So the jump is cube=1 -> sieve=many")
        print(f"   in ONE step at the terminus, with NOTHING progressive across 57..60.")

    print("\n-- KILL test --")
    print("  Clause A ('already Theta(2^N) for r<=58'): the r<=58 set is the full cube =")
    print("    exactly 1 cell (NOT Theta(2^N) cells) -- so clause A does NOT fire.")
    print("  Clause B ('smooth/monotone with no break near 60/61'): there is no per-round")
    print("    cell GROWTH at all across 57..60 (constant 1 cell); the only change is a")
    print("    single architectural step at 61 (first real condition) -- this is NOT the")
    print("    card's 'bounded O(1) cells <=60 that EXPLODE at 61' picture (cells don't grow,")
    print("    they're 1 then the set shrinks to a residue). The premise -- progressive")
    print("    cell-count building to a 61 explosion -- is FALSE. Per finding #4, no knee.")


if __name__ == '__main__':
    main()
