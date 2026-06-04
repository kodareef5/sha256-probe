#!/usr/bin/env python3
"""
W7-FC3 — Duquenne-Guigues base -> the wall is the one irreducible 2-premise rule.
[SUSPECT per #4]

Card claim: canonical implication base is all UNARY through 60 (single-equation
propagation); sr=61 is the FIRST 2-element pseudo-intent (g1=0 ∧ h=0 jointly).  Max
premise size ticks 1->2 AT the wall.  Control: the 9-step local collision is all-unary.

PROBE (honored): N=8,10; compute the DG stem base; premise-size histogram by round-depth;
all size-1 <=60, a size-2 premise at 61?  KILL: 2-premise implications already below 60.

Skeptic (card+#4): premise size is granularity-dependent; the base may flood with size-2
everywhere, a modeling choice doing the work.

DESIGN.  We measured the ground truth:
  * below-wall coordinate diffs de57,de59,de60 are CONSTANT, de58 varies, de61=0 is a
    single ~2^-N condition, and the FULL sr=61 event = (g1=0 AND h=0) ~ 2^-2N.
Attributes for the context (objects = free-word vectors):
  A_r := "de_r = 0"  for r in 57..61   (the round-by-round e-collisions)
  G   := "g1=0",  H := "h=0"           (the two sr=61 sub-conditions)
  SR61:= "g1=0 AND h=0"                (the wall event itself)
We compute the DG base and read the premise-size of the stem that PRODUCES SR61, and
whether any size-2 stem exists strictly below 61 (kill).
ADVERSARIAL CONTROL (#4): a synthetic 2^-2N event TT := (P0=0 AND P1=0) built from two
unrelated independent ~2^-N message-bit conditions P0,P1.  If TT *also* gets a size-2
stem {P0,P1}=>TT, then "max premise ticks 1->2 at the wall" is generic to '2^-2N = two
independent conditions' (= prior finding #3), NOT a 60->61 localization -> rename/kill.
"""
import sys, random, importlib.util
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards')
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import _minisha as m
import shabridge as sb
_spec = importlib.util.spec_from_file_location(
    'fc2', '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards/W7-FC2.py')
fc2 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(fc2)


def popcount(x):
    return bin(x).count('1')


def derive(A, implications, n_attr):
    cur = A; changed = True
    while changed:
        changed = False
        for prem, concl in implications:
            if (cur & prem) == prem and (cur | concl) != cur:
                cur |= concl; changed = True
    return cur


def ctx_closure(A, obj_rows, n_attr):
    full = (1 << n_attr) - 1
    ext = [r for r in obj_rows if (r & A) == A]
    if not ext:
        return full
    c = full
    for r in ext:
        c &= r
    return c


def dg_base(obj_rows, n_attr):
    """Duquenne-Guigues stem base via Ganter next-closure over L-closed sets."""
    implications = []
    full = (1 << n_attr) - 1
    A = derive(0, implications, n_attr)
    while True:
        clA = ctx_closure(A, obj_rows, n_attr)
        if clA != A:
            implications.append((A, clA & ~A))
        nxt = None
        for i in range(n_attr - 1, -1, -1):
            bit = 1 << i
            if A & bit:
                continue
            B = (A & ((1 << i) - 1)) | bit
            C = derive(B, implications, n_attr)
            low = (1 << i) - 1
            if (C & low) == (B & low):
                nxt = C; break
        if nxt is None:
            break
        A = nxt
        if A == full:
            clA = ctx_closure(A, obj_rows, n_attr)
            if clA != A:
                implications.append((A, clA & ~A))
            break
    return implications


def build_objects_ext(N, n_obj, seed):
    """Like fc2.build_objects but also carries de61 and two synthetic independent
    ~2^-N message-bit conditions P0,P1 for the adversarial control."""
    S = m.setup(N)
    if S is None:
        return None
    P, O = S['P'], S['O']; MASK = P['MASK']; KN = P['KN']
    st1, W1p = m.precompute(S['M1'], P, O)
    st2, W2p = m.precompute(S['M2'], P, O)
    rng = 1 << N
    random.seed(seed)
    objs = []
    for _ in range(n_obj):
        free4 = [random.randrange(rng) for _ in range(4)]
        diffs, g1, h = fc2.cascade_full(P, O, st1, list(W1p), st2, list(W2p), free4)
        # de61: round 61, schedule-determined W[61]
        W1 = list(W1p); W2 = list(W2p); s1 = list(st1); s2 = list(st2)
        for k, rnd in enumerate(range(57, 61)):
            w1 = free4[k] & MASK; w2 = m.find_w2(s1, s2, rnd, w1, P, O)
            W1.append(w1); W2.append(w2)
            s1 = list(m.sha_round(s1, KN[rnd], w1, P, O)); s2 = list(m.sha_round(s2, KN[rnd], w2, P, O))
        w1 = (O['s1'](W1[59]) + W1[54] + O['s0'](W1[46]) + W1[45]) & MASK
        w2 = (O['s1'](W2[59]) + W2[54] + O['s0'](W2[46]) + W2[45]) & MASK
        s1 = list(m.sha_round(s1, KN[61], w1, P, O)); s2 = list(m.sha_round(s2, KN[61], w2, P, O))
        de61 = (s1[4] - s2[4]) & MASK
        # two INDEPENDENT synthetic ~2^-N conditions: top N bits of free4[0], free4[1]
        P0 = (free4[0] == 0)        # ~2^-N
        P1 = (free4[1] == 0)        # ~2^-N, independent
        objs.append(dict(free4=free4, diffs=diffs, g1=g1, h=h, de61=de61, P0=P0, P1=P1))
    return dict(objs=objs)


def build_ctx(objs, specs):
    rows = []
    for o in objs:
        mask = 0
        for j, (_, fn) in enumerate(specs):
            if fn(o):
                mask |= (1 << j)
        rows.append(mask)
    return rows


def run_N(N, n_obj, seed):
    B = build_objects_ext(N, n_obj, seed)
    if B is None:
        return None
    objs = B['objs']
    # attribute specs (named); ROUND ORDER then the wall pair then the SR61 target
    specs = []
    names = []
    for rnd in (57, 58, 59, 60, 61):
        specs.append(('de%d=0' % rnd, (lambda rr: (lambda o: o['diffs'][(4, rr)] == 0 if rr <= 60 else o['de61'] == 0))(rnd)))
        names.append('de%d=0' % rnd)
    specs.append(('g1=0', lambda o: o['g1'] == 0)); names.append('g1=0')
    specs.append(('h=0', lambda o: o['h'] == 0)); names.append('h=0')
    specs.append(('SR61', lambda o: o['g1'] == 0 and o['h'] == 0)); names.append('SR61')

    rows = build_ctx(objs, specs)
    imp = dg_base(rows, len(specs))
    # premise-size histogram and the stems producing SR61, de61, etc.
    name_of = {i: names[i] for i in range(len(names))}
    sr61_idx = names.index('SR61')
    de61_idx = names.index('de61=0')
    g1_idx = names.index('g1=0'); h_idx = names.index('h=0')

    hist = {}
    stems_by_target = []
    for prem, concl in imp:
        s = popcount(prem)
        hist[s] = hist.get(s, 0) + 1
        pr = [name_of[i] for i in range(len(names)) if (prem >> i) & 1]
        cc = [name_of[i] for i in range(len(names)) if (concl >> i) & 1]
        stems_by_target.append((s, pr, cc))
    maxp = max(hist) if hist else 0

    # find the minimal premise that forces SR61, and minimal that forces de61=0
    def min_premise_for(target_idx):
        best = None
        for prem, concl in imp:
            if (concl >> target_idx) & 1 or ((ctx_closure(prem, rows, len(specs)) >> target_idx) & 1):
                ps = popcount(prem)
                if best is None or ps < best[0]:
                    best = (ps, [name_of[i] for i in range(len(names)) if (prem >> i) & 1])
        return best
    sr61_prem = min_premise_for(sr61_idx)
    de61_prem = min_premise_for(de61_idx)

    # does any size-2 stem exist using ONLY below-61 attributes (indices < de61_idx)?
    below_mask = (1 << de61_idx) - 1   # de57..de60 only (de61 excluded)
    size2_below = [(popcount(prem), [name_of[i] for i in range(len(names)) if (prem >> i) & 1])
                   for prem, concl in imp
                   if popcount(prem) >= 2 and (prem & ~below_mask) == 0]

    # ADVERSARIAL CONTROL: synthetic 2^-2N target TT=(P0 and P1) from two indep ~2^-N conds
    cspecs = [('P0=0', lambda o: o['P0']), ('P1=0', lambda o: o['P1']),
              ('TT', lambda o: o['P0'] and o['P1'])]
    crows = build_ctx(objs, cspecs)
    cimp = dg_base(crows, len(cspecs))
    cnames = ['P0=0', 'P1=0', 'TT']
    chist = {}
    tt_stem = None
    for prem, concl in cimp:
        chist[popcount(prem)] = chist.get(popcount(prem), 0) + 1
        if (concl >> 2) & 1 and tt_stem is None:
            tt_stem = (popcount(prem), [cnames[i] for i in range(3) if (prem >> i) & 1])
    cmaxp = max(chist) if chist else 0

    return dict(N=N, n_obj=len(objs), names=names, hist=hist, maxp=maxp,
                sr61_prem=sr61_prem, de61_prem=de61_prem, size2_below=size2_below,
                stems=stems_by_target, ctrl_hist=chist, ctrl_maxp=cmaxp, ctrl_tt=tt_stem,
                dens=dict((nm, sum(1 for o in objs if fn(o))) for nm, fn in specs))


if __name__ == '__main__':
    print("W7-FC3 — DG stem base: does max premise size tick 1->2 AT the wall (60->61)?")
    print("=" * 80)
    print("SUSPECT #4: or is the size-2 premise generic to '2^-2N = two indep conditions'?\n")
    for N in (8, 10):
        r = run_N(N, n_obj=20000, seed=0)
        if r is None:
            print(f"N={N}: no kernel"); continue
        print(f"--- N={N} (objects={r['n_obj']}) ---")
        print(f"  attribute densities: {r['dens']}")
        print(f"  DG base premise-size histogram: {r['hist']}  (max premise size = {r['maxp']})")
        print(f"  minimal premise forcing de61=0 (the ~2^-N e-collision): {r['de61_prem']}")
        print(f"  minimal premise forcing SR61 (g1=0 AND h=0, ~2^-2N)   : {r['sr61_prem']}")
        print(f"  size-2 stems using ONLY below-61 (de57..60) attrs     : {r['size2_below']}  "
              f"{'(KILL: 2-premise below 60)' if r['size2_below'] else '(none below 60)'}")
        print(f"  ADV CONTROL synthetic 2^-2N target TT=(P0 and P1):")
        print(f"     control premise-size hist: {r['ctrl_hist']} (max {r['ctrl_maxp']}); stem for TT: {r['ctrl_tt']}")
        print()
    print("KILL fires iff 2-premise implications already appear below 60 (size2_below nonempty),")
    print("OR (adversarial #4) the synthetic 2^-2N control ALSO needs a size-2 stem => the")
    print("1->2 tick is the generic '2^-2N = two independent conditions', not a 60->61 wall.")
