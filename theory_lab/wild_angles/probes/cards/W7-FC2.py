#!/usr/bin/env python3
"""
W7-FC2 — Concept-count explosion -> the sr=60->61 wall.  [HEADLINE / SUSPECT per #4]

Card claim: below 60 the cascade is single-DOF -> a near-CHAIN concept lattice (few
concepts); the two INDEPENDENT sr=61 attributes (g1=0 ⊥ h=0) turn the chain into a
Boolean SQUARE, so |B(K)| jumps multiplicatively (×k) -- the same independence that
gives 2^-2N -- appearing as an independent 2×2 sublattice.

PROBE (honored): N=8,10 exhaustively/largely enumerate W[57..60]; accumulate per-round
zero-diff attributes; compute |B(K)| vs round-depth r (next-closure); then ADD the two
sr=61 attributes (g1=0, h=0) -> a ~×k jump vs the tame growth, as an independent 2×2?

KILL: |B(K)| grows AS FAST across tame rounds 57->60 as adding the sr=61 pair (no kink).

Skeptic (card): must use EXHAUSTIVE small-N (|B| is sample-dependent); CONTROL by adding
two CORRELATED dummy attributes -- they shouldn't cause the jump.
Adversarial control (prior #4): also add ONE generic first-condition attribute (a single
g1=0) and a single UNRELATED coordinate condition.  If ANY first independent condition
gives the same ×2 (chain->2 incomparable->square), the "jump" is the generic
free-cascade -> first-condition step, NOT a 60->61-specific complexity explosion.

ground truth (gap_rows.csv, N=10): g1 = W1[60]-sched1[60]; h = casoff-(sched2-sched1);
sr=61 ⟺ g1=0 AND h=0; g1 ⊥ h (ratio 1.005).
N small: N=8 exhaustive in (W57,W58) and sampled W59,W60; N=10 sampled.
"""
import sys, random, itertools
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards')
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import _minisha as m
import shabridge as sb


def cascade_full(P, O, st1_56, W1pre, st2_56, W2pre, free4):
    """Run cascade rounds 57..60 (W2 picked so da=0).  Return per-round state diffs and
    the g1, h coincidence scalars used by sr=61.
    de_r (modular e-diff) for r=57..60; da_r is pinned 0 by construction; also dd/dc/db/df.
    g1 = W1[60]-sched1[60]; h = casoff - (sched2[60]-sched1[60]) with casoff=W2[60]-W1[60].
    """
    MASK, KN = P['MASK'], P['KN']
    W1 = list(W1pre); W2 = list(W2pre)
    s1 = list(st1_56); s2 = list(st2_56)
    diffs = {}   # (reg_index, round) -> modular diff
    for k, rnd in enumerate(range(57, 61)):
        w1 = free4[k] & MASK
        w2 = m.find_w2(s1, s2, rnd, w1, P, O)
        W1.append(w1); W2.append(w2)
        s1 = list(m.sha_round(s1, KN[rnd], w1, P, O))
        s2 = list(m.sha_round(s2, KN[rnd], w2, P, O))
        for ri in range(8):
            diffs[(ri, rnd)] = (s1[ri] - s2[ri]) & MASK
    # schedule value for index 60: sigma1(W[58]) + W[53] + sigma0(W[45]) + W[44]
    sched1 = (O['s1'](W1[58]) + W1[53] + O['s0'](W1[45]) + W1[44]) & MASK
    sched2 = (O['s1'](W2[58]) + W2[53] + O['s0'](W2[45]) + W2[44]) & MASK
    casoff = (W2[60] - W1[60]) & MASK
    g1 = (W1[60] - sched1) & MASK
    h = (casoff - ((sched2 - sched1) & MASK)) & MASK
    return diffs, g1, h


# ---------------- next-closure concept count on a SMALL attribute set ----------------

def n_concepts(obj_rows, n_attr):
    """|B(K)| = number of intents (closed attribute sets) via next-closure.
    obj_rows = object->attribute bitmasks.  Small n_attr only."""
    full = (1 << n_attr) - 1

    def cl(A):
        ext = [r for r in obj_rows if (r & A) == A]
        if not ext:
            return full
        c = full
        for r in ext:
            c &= r
        return c

    count = 0
    A = cl(0)
    count += 1
    while A != full:
        nxt = None
        for i in range(n_attr - 1, -1, -1):
            bit = 1 << i
            if A & bit:
                continue
            B = (A & ((1 << i) - 1)) | bit
            C = cl(B)
            low = (1 << i) - 1
            if (C & low) == (B & low):
                nxt = C
                break
        if nxt is None:
            break
        A = nxt
        count += 1
    return count


def build_objects(N, n_obj, seed):
    """Sample free-word vectors; compute, per object, the boolean attributes used for the
    concept lattice.  Returns dict of named boolean columns (object-indexed)."""
    S = m.setup(N)
    if S is None:
        return None
    P, O = S['P'], S['O']
    st1_56, W1pre = m.precompute(S['M1'], P, O)
    st2_56, W2pre = m.precompute(S['M2'], P, O)
    rng = 1 << N
    random.seed(seed)
    objs = []
    for _ in range(n_obj):
        free4 = [random.randrange(rng) for _ in range(4)]
        diffs, g1, h = cascade_full(P, O, st1_56, list(W1pre), st2_56, list(W2pre), free4)
        rec = dict(free4=free4, diffs=diffs, g1=g1, h=h)
        objs.append(rec)
    return dict(objs=objs, S=S)


# attribute generators (each: object -> bool "this fact holds")
def attr_de_zero(rnd):
    return ('de%d=0' % rnd, lambda o: o['diffs'][(4, rnd)] == 0)      # e-register diff


def attr_dd_zero(rnd):
    return ('dd%d=0' % rnd, lambda o: o['diffs'][(3, rnd)] == 0)


def attr_db_zero(rnd):
    return ('db%d=0' % rnd, lambda o: o['diffs'][(1, rnd)] == 0)


def attr_g1():
    return ('g1=0', lambda o: o['g1'] == 0)


def attr_h():
    return ('h=0', lambda o: o['h'] == 0)


def make_context(objs, attr_specs):
    """attr_specs = list of (name, fn).  Returns (obj_rows, names)."""
    names = [a[0] for a in attr_specs]
    rows = []
    for o in objs:
        mask = 0
        for j, (_, fn) in enumerate(attr_specs):
            if fn(o):
                mask |= (1 << j)
        rows.append(mask)
    return rows, names


def col_density(objs, fn):
    c = sum(1 for o in objs if fn(o))
    return c, len(objs)


def run_N(N, n_obj, seed):
    B = build_objects(N, n_obj, seed)
    if B is None:
        return None
    objs = B['objs']
    # per-round attribute pool below 61: de57..60 (+ dd, db at 60 as extra below-wall facts)
    # We add attributes in ROUND ORDER and record |B(K)| after each addition.
    pool = []
    seq = []
    # tame below-wall facts, round by round (these are what's available pre-61):
    for rnd in (57, 58, 59, 60):
        pool.append(attr_de_zero(rnd))
        seq.append(('add de%d=0' % rnd, attr_de_zero(rnd)))
    # extra below-wall coordinate facts at the boundary round (more tame attributes):
    pool.append(attr_dd_zero(60)); seq.append(('add dd60=0', attr_dd_zero(60)))
    pool.append(attr_db_zero(60)); seq.append(('add db60=0', attr_db_zero(60)))
    # the two sr=61 attributes (the wall):
    g1a = attr_g1(); ha = attr_h()

    # densities (which below-wall attrs are degenerate / constant?)
    dens = {}
    for name, fn in pool + [g1a, ha]:
        dens[name] = col_density(objs, fn)

    # |B(K)| as we add tame below-wall attributes one at a time:
    growth = []
    cur = []
    for label, spec in seq:
        cur.append(spec)
        rows, names = make_context(objs, cur)
        growth.append((label, len(cur), n_concepts(rows, len(cur))))
    base_attrs = list(cur)              # all tame below-wall attrs
    rows0, _ = make_context(objs, base_attrs)
    B0 = n_concepts(rows0, len(base_attrs))

    # NOW add the sr=61 pair:
    rows_g1, _ = make_context(objs, base_attrs + [g1a])
    B_g1 = n_concepts(rows_g1, len(base_attrs) + 1)
    rows_g1h, _ = make_context(objs, base_attrs + [g1a, ha])
    B_g1h = n_concepts(rows_g1h, len(base_attrs) + 2)

    # CONTROL 1: add two CORRELATED dummy attributes (h=0 and a copy of h=0)
    h_copy = ('h=0_copy', ha[1])
    rows_corr, _ = make_context(objs, base_attrs + [ha, h_copy])
    B_corr = n_concepts(rows_corr, len(base_attrs) + 2)

    # CONTROL 2: add two INDEPENDENT *generic* dummy conditions unrelated to the wall:
    #   "free4[0] low bit = 0" and "free4[1] low bit = 0" -- two independent random-ish
    #   N-bit coincidences with the SAME ~1/2 density, structurally not the wall.
    d1 = ('m0bit=0', lambda o: (o['free4'][0] & 1) == 0)
    d2 = ('m1bit=0', lambda o: (o['free4'][1] & 1) == 0)
    rows_ind2, _ = make_context(objs, base_attrs + [d1, d2])
    B_ind2 = n_concepts(rows_ind2, len(base_attrs) + 2)

    return dict(N=N, n_obj=len(objs), dens=dens, growth=growth,
                B0=B0, B_g1=B_g1, B_g1h=B_g1h, B_corr=B_corr, B_ind2=B_ind2)


if __name__ == '__main__':
    print("W7-FC2 — concept-count |B(K)| vs round-depth; does the sr=61 pair cause the jump?")
    print("=" * 80)
    print("SUSPECT per prior-finding #4: is the explosion AT 60->61, or the generic")
    print("free-cascade -> first-condition step (any independent pair gives chain->square)?\n")
    for N in (8, 10):
        r = run_N(N, n_obj=4000, seed=0)
        if r is None:
            print(f"N={N}: no kernel"); continue
        print(f"--- N={N}  (objects={r['n_obj']}) ---")
        print("  below-wall attribute densities (count/total):")
        for k, v in r['dens'].items():
            tag = ' [CONSTANT/degenerate]' if v[0] in (0, v[1]) else ''
            print(f"     {k:10s}: {v[0]}/{v[1]}{tag}")
        print("  |B(K)| as tame below-wall attrs are added in round order:")
        for label, na, nc in r['growth']:
            print(f"     after {label:14s} ({na} attrs): |B|={nc}")
        print(f"  baseline |B| (all tame below-wall attrs)           : {r['B0']}")
        print(f"  + g1=0                                             : {r['B_g1']}  "
              f"(×{r['B_g1']/r['B0']:.2f})")
        print(f"  + g1=0 AND h=0 (the sr=61 pair)                    : {r['B_g1h']}  "
              f"(×{r['B_g1h']/r['B0']:.2f} vs base)")
        print(f"  CONTROL corr: + h=0 and a COPY of h=0              : {r['B_corr']}  "
              f"(×{r['B_corr']/r['B0']:.2f})")
        print(f"  CONTROL indep: + 2 generic unrelated 1/2 conds     : {r['B_ind2']}  "
              f"(×{r['B_ind2']/r['B0']:.2f})")
        print()
    print("KILL fires iff tame 57->60 growth is as fast as adding the sr=61 pair (no kink),")
    print("OR the generic-independent control reproduces the same jump (=> not 60->61-specific).")
