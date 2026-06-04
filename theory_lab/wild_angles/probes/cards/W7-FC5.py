#!/usr/bin/env python3
"""
W7-FC5 — Arrow relations -> localize the wall to one (object,attribute) cell.
[SUSPECT per #4]

Card claim: arrow relations (down/up/double) mark the irreducible "load-bearing
absences"; conjecture they CONCENTRATE on the W[60]-schedule-match / dT1_61=0 column at
near-collision objects -- the FCA fingerprint of "the 7-round problem collapses to ONE
equation"; double-arrow count tracks the 24-bit residue (~2^-N).

PROBE (honored): N=8 (N=6 has no cascade kernel); attributes {de61=0, de62=0, de63=0,
dT1_61=0, W[60]-match(=g1=0)}; compute the down/up/double arrow table; do double-arrows
pile on the schedule/dT1 columns + HW-1 near-collision objects, count ~2^-N?

KILL: arrows spread uniformly over all columns (no localization).

Skeptic (card): arrows live on the REDUCED context and are sample-sensitive -- oversample
HW<=2 pairs / exact near-collision sets.  So we (a) build a clarified+reduced context,
(b) heavily oversample low-output-Hamming-weight objects.

Arrow relations (standard FCA), for g NOT having m (g,m) not in I:
  g ↓ m  iff  for every object h with extent-row strictly ⊃ row(g) (h has all of g's
              attributes and more), h HAS m.   [m is 'just missing' at g]
  g ↑ m  iff  for every attribute n with column strictly ⊃ column(m), g HAS n.
  g ↕ m  iff  g↓m AND g↑m  (double arrow -- the irreducible load-bearing cell).
We compute the per-COLUMN double-arrow totals and test concentration on {dT1_61, g1}.
"""
import sys, random, importlib.util
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards')
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import _minisha as m
import shabridge as sb
_spec = importlib.util.spec_from_file_location(
    'fc2', '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards/W7-FC2.py')
fc2 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(fc2)


def build_objects(N, n_obj, seed, near_bias=0.6):
    S = m.setup(N)
    if S is None:
        return None
    P, O = S['P'], S['O']; MASK = P['MASK']; KN = P['KN']
    st1, W1p = m.precompute(S['M1'], P, O)
    st2, W2p = m.precompute(S['M2'], P, O)
    rng = 1 << N
    random.seed(seed)
    objs = []
    attempts = 0
    while len(objs) < n_obj and attempts < n_obj * 60:
        attempts += 1
        # oversample structured / small free words to get near-collisions (low de HW)
        if random.random() < near_bias:
            free4 = [random.choice([0, 1, 2, MASK, rng - 1, rng - 2]) for _ in range(4)]
        else:
            free4 = [random.randrange(rng) for _ in range(4)]
        diffs, g1, h = fc2.cascade_full(P, O, st1, list(W1p), st2, list(W2p), free4)
        # run rounds 61,62,63 (schedule-determined W) to get de61,de62,de63 and dT1_61
        W1 = list(W1p); W2 = list(W2p); s1 = list(st1); s2 = list(st2)
        for k, rnd in enumerate(range(57, 61)):
            w1 = free4[k] & MASK; w2 = m.find_w2(s1, s2, rnd, w1, P, O)
            W1.append(w1); W2.append(w2)
            s1 = list(m.sha_round(s1, KN[rnd], w1, P, O)); s2 = list(m.sha_round(s2, KN[rnd], w2, P, O))
        de = {}
        dT1_61 = None
        for rnd in range(61, 64):
            w1 = (O['s1'](W1[rnd - 2]) + W1[rnd - 7] + O['s0'](W1[rnd - 15]) + W1[rnd - 16]) & MASK
            w2 = (O['s1'](W2[rnd - 2]) + W2[rnd - 7] + O['s0'](W2[rnd - 15]) + W2[rnd - 16]) & MASK
            W1.append(w1); W2.append(w2)
            if rnd == 61:
                # T1 for each message at round 61 (pre-update e-line)
                a1, b1, c1, d1, e1, f1, g1_, h1 = s1
                a2, b2, c2, d2, e2, f2, g2_, h2 = s2
                T1_1 = (h1 + O['S1'](e1) + O['Ch'](e1, f1, g1_) + KN[61] + w1) & MASK
                T1_2 = (h2 + O['S1'](e2) + O['Ch'](e2, f2, g2_) + KN[61] + w2) & MASK
                dT1_61 = (T1_1 - T1_2) & MASK
            s1 = list(m.sha_round(s1, KN[rnd], w1, P, O)); s2 = list(m.sha_round(s2, KN[rnd], w2, P, O))
            de[rnd] = (s1[4] - s2[4]) & MASK
        # output Hamming weight of full round-63 XOR diff (for near-collision ranking)
        outhw = sum(sb.hw(s1[i] ^ s2[i]) for i in range(8))
        objs.append(dict(de61=de[61], de62=de[62], de63=de[63], dT1_61=dT1_61,
                         g1=g1, outhw=outhw))
    return dict(objs=objs)


# attribute order (columns):
ATTRS = [
    ('de61=0', lambda o: o['de61'] == 0),
    ('de62=0', lambda o: o['de62'] == 0),
    ('de63=0', lambda o: o['de63'] == 0),
    ('dT1_61=0', lambda o: o['dT1_61'] == 0),
    ('Wmatch(g1=0)', lambda o: o['g1'] == 0),
]
TARGET_COLS = {'dT1_61=0', 'Wmatch(g1=0)'}   # the card's conjectured load-bearing columns


def context(objs):
    rows = []
    for o in objs:
        mask = 0
        for j, (_, fn) in enumerate(ATTRS):
            if fn(o):
                mask |= (1 << j)
        rows.append(mask)
    return rows


def clarify_reduce(rows, n_attr):
    """Clarify objects (dedupe rows) and attributes (dedupe columns).  Return reduced
    object rows + the surviving attribute indices, for arrow computation."""
    # clarify objects
    rows_u = list(set(rows))
    # columns as object-extent bitmasks over rows_u
    cols = [0] * n_attr
    for oi, r in enumerate(rows_u):
        for j in range(n_attr):
            if (r >> j) & 1:
                cols[j] |= (1 << oi)
    return rows_u, cols


def arrows(rows_u, cols, n_attr):
    """Compute down/up/double arrows on the (clarified) context.
    Returns per-attribute double-arrow counts and totals."""
    n_obj = len(rows_u)
    full_obj = (1 << n_obj) - 1
    # precompute object rows and attribute columns
    dbl_by_attr = {j: 0 for j in range(n_attr)}
    down_by_attr = {j: 0 for j in range(n_attr)}
    up_by_attr = {j: 0 for j in range(n_attr)}
    for gi in range(n_obj):
        rg = rows_u[gi]
        for j in range(n_attr):
            bit = 1 << j
            if rg & bit:
                continue  # g HAS m -> no arrow
            # down arrow g↓m: every object h with row(h) ⊋ row(g) has m.
            down = True
            for hi in range(n_obj):
                if hi == gi:
                    continue
                rh = rows_u[hi]
                if (rh & rg) == rg and rh != rg:   # rh ⊋ rg (h has all of g's attrs + more)
                    if not (rh & bit):
                        down = False; break
            # up arrow g↑m: every attribute n with col(n) ⊋ col(m) is had by g.
            cm = cols[j]
            up = True
            for k in range(n_attr):
                if k == j:
                    continue
                ck = cols[k]
                if (ck & cm) == cm and ck != cm:   # col(k) ⊋ col(m)
                    if not (rg & (1 << k)):
                        up = False; break
            if down:
                down_by_attr[j] += 1
            if up:
                up_by_attr[j] += 1
            if down and up:
                dbl_by_attr[j] += 1
    return down_by_attr, up_by_attr, dbl_by_attr


def run_N(N, n_obj, seed):
    B = build_objects(N, n_obj, seed)
    if B is None:
        return None
    objs = B['objs']
    n_attr = len(ATTRS)
    rows = context(objs)
    rows_u, cols = clarify_reduce(rows, n_attr)
    down, up, dbl = arrows(rows_u, cols, n_attr)
    names = [a[0] for a in ATTRS]
    # attribute densities (over all objects)
    dens = {names[j]: sum(1 for r in rows if (r >> j) & 1) for j in range(n_attr)}
    # near-collision objects (low outhw) -- where do double arrows sit?
    return dict(N=N, n_obj=len(objs), n_clarified=len(rows_u), names=names,
                down={names[j]: down[j] for j in range(n_attr)},
                up={names[j]: up[j] for j in range(n_attr)},
                dbl={names[j]: dbl[j] for j in range(n_attr)},
                dens=dens)


if __name__ == '__main__':
    print("W7-FC5 — FCA arrow relations: do double-arrows LOCALIZE on {dT1_61=0, Wmatch}?")
    print("=" * 80)
    print("SUSPECT #4: real localization to one cell, or arrows spread over all columns?\n")
    for N in (8, 10):
        r = run_N(N, n_obj=3000, seed=0)
        if r is None:
            print(f"N={N}: no kernel"); continue
        print(f"--- N={N} (objects={r['n_obj']}, clarified rows={r['n_clarified']}) ---")
        print(f"  attribute densities       : {r['dens']}")
        print(f"  DOWN-arrows per column     : {r['down']}")
        print(f"  UP-arrows per column       : {r['up']}")
        print(f"  DOUBLE-arrows per column   : {r['dbl']}")
        tot = sum(r['dbl'].values())
        ontarget = sum(v for k, v in r['dbl'].items() if k in TARGET_COLS)
        offtarget = tot - ontarget
        print(f"  double-arrows on TARGET {{dT1_61, Wmatch}}: {ontarget}   off-target: {offtarget}   "
              f"total: {tot}")
        if tot:
            print(f"  -> target share = {ontarget/tot:.2f}  "
                  f"{'LOCALIZED' if offtarget == 0 and ontarget > 0 else 'SPREAD over other columns'}")
        print()
    print("KILL fires iff arrows spread (double-arrows appear on non-target columns too).")
