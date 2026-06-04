#!/usr/bin/env python3
"""
W7-FC4 — Concept stability -> de58 as the unique low-stability (soft) coordinate.
[de58 thread -- per prior-finding #5: CONFIRM only if stability DERIVES 2^hw(db56)]

Card claim: high-stability concepts (intent unshaken by object removal) = the 7/8 constant
register diffs (cascade-rigid); low-stability = the lone varying de58/dh61 (carry-fragile
single DOF).  The de58-grows / de57,59,60-constant split = a stability spectrum.  Probe:
attributes = "(register,round) diff = MODAL value"; compute concept stability sigma; do
de57/59/60 + constant diffs cluster at sigma~1 and de58/dh61 form a distinct low-sigma
cluster GROWING N=8->10 (low-sigma count ~ 2^0.74N)?

KILL: de58 concepts have the SAME stability as de57/59/60 (no separation).

Skeptic (card + #5): "constant diffs -> sigma~1" is near-TAUTOLOGICAL; the ONLY payload
is (a) the de58-vs-others separation AND (b) it must DERIVE 2^hw(db56) / 2^0.74N to be a
CONFIRMED, else it merely RESTATES the known de58-varies fact.

Concept stability (Kuznetsov):  for concept (A,B) with extent A,
  sigma(A,B) = |{ C subset A : C'' = B (i.e. closure(C)=B) }| / 2^|A|.
We compute it exactly for the per-coordinate modal-value concepts at small extent, and a
Monte-Carlo estimate for large extents.  Key derived quantities:
  * separation: sigma(de58 concept) vs sigma(de57/59/60 concept).
  * does the de58 extent / low-sigma structure reproduce 2^hw(db56) (=|de58|) or 2^0.74N?
"""
import sys, random, importlib.util, math
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards')
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import _minisha as m
import shabridge as sb
_spec = importlib.util.spec_from_file_location(
    'fc2', '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards/W7-FC2.py')
fc2 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(fc2)


def build(N, n_obj, seed):
    S = m.setup(N)
    if S is None:
        return None
    P, O = S['P'], S['O']
    st1, W1p = m.precompute(S['M1'], P, O)
    st2, W2p = m.precompute(S['M2'], P, O)
    rng = 1 << N
    random.seed(seed)
    objs = []
    for _ in range(n_obj):
        free4 = [random.randrange(rng) for _ in range(4)]
        diffs, g1, h = fc2.cascade_full(P, O, st1, list(W1p), st2, list(W2p), free4)
        objs.append(diffs)
    # also: db56 for the ground-truth law
    MASK = P['MASK']
    db56 = (st1[1] - st2[1]) & MASK
    return dict(objs=objs, db56=db56, S=S, N=N)


REG = ('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h')


def coord_stats(objs):
    """For each (register,round) coordinate, the distinct-value count and modal fraction."""
    from collections import Counter
    coords = {}
    for ri in range(8):
        for rnd in range(57, 61):
            vals = Counter(o[(ri, rnd)] for o in objs)
            modal_val, modal_ct = vals.most_common(1)[0]
            coords[(ri, rnd)] = dict(distinct=len(vals), modal_val=modal_val,
                                     modal_frac=modal_ct / len(objs), counts=vals)
    return coords


def stability_modal_concept(objs, coord, modal_val):
    """Concept stability of the 'this coordinate = modal_val' attribute concept.
    Extent A = objects with coord==modal_val.  Its intent B = the modal-value attributes
    shared by ALL of A across all coordinates.  sigma = fraction of subsets C of A with
    closure(C)=B.  For a SINGLE-attribute context this is dominated by whether removing
    objects changes the shared-modal set; we estimate via the standard bound:
       sigma >= 1 - sum_over_objects 2^-(stuff) ...
    We instead compute the EXACT Kuznetsov stability on the small multi-coordinate context
    restricted to the modal-value attributes (objects x {coord=modal for each coord}).
    To keep it exact-and-cheap, we estimate sigma by Monte-Carlo subset sampling of A."""
    ri, rnd = coord
    # full modal-attribute context: attribute m_c = '(coord c)=modal_c'
    # Build per-object boolean vector over all coords' modal indicators.
    from collections import Counter
    modal = {}
    for ci in range(8):
        for rr in range(57, 61):
            vals = Counter(o[(ci, rr)] for o in objs)
            modal[(ci, rr)] = vals.most_common(1)[0][0]
    coord_list = [(ci, rr) for ci in range(8) for rr in range(57, 61)]
    cidx = {c: i for i, c in enumerate(coord_list)}
    rows = []
    for o in objs:
        mask = 0
        for c in coord_list:
            if o[c] == modal[c]:
                mask |= (1 << cidx[c])
        rows.append(mask)
    # extent of 'coord=modal_val' : objects whose bit cidx[coord] set (i.e. ==modal)
    target_bit = 1 << cidx[coord]
    A = [i for i, r in enumerate(rows) if r & target_bit]
    if not A:
        return None
    full = (1 << len(coord_list)) - 1

    def closure_of_objset(C_objs):
        if not C_objs:
            return full
        b = full
        for oi in C_objs:
            b &= rows[oi]
        return b

    # intent of the WHOLE extent A:
    B = closure_of_objset(A)
    nA = len(A)
    # Monte-Carlo sigma: P over random C subset A that closure(C)==B
    trials = 4000
    hit = 0
    rnd_ = random.Random(12345)
    for _ in range(trials):
        # random subset
        C = [oi for oi in A if rnd_.random() < 0.5]
        if closure_of_objset(C) == B:
            hit += 1
    sigma = hit / trials
    return dict(sigma=sigma, extent=nA, intent_popcount=bin(B).count('1'))


def run_N(N, n_obj, seed):
    B = build(N, n_obj, seed)
    if B is None:
        return None
    objs = B['objs']
    cs = coord_stats(objs)
    # distinct-value count per e-round coordinate (de57..60) -- the known split
    de_distinct = {rnd: cs[(4, rnd)]['distinct'] for rnd in range(57, 61)}
    de_modalfrac = {rnd: round(cs[(4, rnd)]['modal_frac'], 4) for rnd in range(57, 61)}
    # stability of each de-round modal concept
    sig = {}
    for rnd in range(57, 61):
        r = stability_modal_concept(objs, (4, rnd), cs[(4, rnd)]['modal_val'])
        sig[rnd] = None if r is None else dict(sigma=round(r['sigma'], 4), extent=r['extent'])
    # ground truth: |de58| should be 2^hw(db56)?  measure both.
    hwdb56 = sb.hw(B['db56'])
    return dict(N=N, n_obj=len(objs), db56=B['db56'], hw_db56=hwdb56,
                two_pow_hw=2 ** hwdb56, de_distinct=de_distinct,
                de_modalfrac=de_modalfrac, sig=sig)


if __name__ == '__main__':
    print("W7-FC4 — concept stability: is de58 the unique low-stability coordinate, and")
    print("         does stability DERIVE |de58|=2^hw(db56) / 2^0.74N? (else only RESTATE)")
    print("=" * 80)
    res = {}
    for N in (8, 10):
        r = run_N(N, n_obj=8000, seed=0)
        if r is None:
            print(f"N={N}: no kernel"); continue
        res[N] = r
        print(f"--- N={N} (objects={r['n_obj']}) ---")
        print(f"  de-coordinate DISTINCT values per round: {r['de_distinct']}  "
              f"(ground truth |de57..60| = 1, |de58|, 1, 1)")
        print(f"  de-coordinate modal fraction per round : {r['de_modalfrac']}")
        print(f"  concept stability sigma per de-round   : "
              f"{ {k: (v['sigma'] if v else None) for k,v in r['sig'].items()} }")
        print(f"  extent per de-round modal concept      : "
              f"{ {k: (v['extent'] if v else None) for k,v in r['sig'].items()} }")
        print(f"  db56={r['db56']} hw(db56)={r['hw_db56']} -> 2^hw={r['two_pow_hw']}  "
              f"(claim: |de58| should equal 2^hw(db56))")
        print(f"    MEASURED |de58| (distinct de58) = {r['de_distinct'][58]}  "
              f"{'== 2^hw  (law holds)' if r['de_distinct'][58]==r['two_pow_hw'] else '!= 2^hw (law NOT reproduced by hw(db56) here)'}")
        print()
    # separation + derivation verdict
    if 8 in res and 10 in res:
        s8 = res[8]['sig']; s10 = res[10]['sig']
        # is de58 sigma distinctly lower than de57/59/60?
        def sep(s):
            others = [s[r]['sigma'] for r in (57, 59, 60) if s[r]]
            d58 = s[58]['sigma'] if s[58] else None
            return d58, others
        d58_8, oth8 = sep(s8); d58_10, oth10 = sep(s10)
        print("SEPARATION check (de58 sigma vs de57/59/60 sigma):")
        print(f"  N=8 : de58 sigma={d58_8}  others={oth8}")
        print(f"  N=10: de58 sigma={d58_10} others={oth10}")
        # growth of |de58|
        print(f"GROWTH check: |de58| N=8 -> N=10 : {res[8]['de_distinct'][58]} -> {res[10]['de_distinct'][58]}")
        import math
        if res[8]['de_distinct'][58] > 0 and res[10]['de_distinct'][58] > 0:
            exp = math.log2(res[10]['de_distinct'][58] / res[8]['de_distinct'][58]) / (10 - 8)
            print(f"  implied exponent c in |de58|~2^cN over 8->10: c={exp:.3f}  (card says ~0.74)")
    print("\nKILL fires iff de58 concept has SAME stability as de57/59/60 (no separation).")
    print("Per #5: CONFIRM only if stability DERIVES 2^hw(db56)/2^0.74N; else RESTATE (known).")
