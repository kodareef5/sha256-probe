#!/usr/bin/env python3
"""
W7-FC1 — The 132 = the meet-irreducibles of the output-agreement lattice.

Card claim: Objects = message pairs, attributes = "output bit b agrees" (XOR diff bit
b == 0 at round 63).  A *controlled* bit (dd,dg,dh — deterministic single-flip
controllers) agrees as the MEET of upstream agreements -> meet-REDUCIBLE.  A hard-core
bit (da,db,de,df, +4 scattered dc; zero controllers) is meet-IRREDUCIBLE.  So
132 = the meet-irreducible rank of the output-agreement (Galois) lattice, NOT a
correlation count; the irreducibles should be exactly the {da,db,de,df}[*]+4dc columns,
fraction -> 132/256.

PROBE (honored): N=4,6,8.  Build the 8N-column round-63 agreement cross-table over a
sample of same-kernel message pairs (cascade near-collisions + random free-word pairs).
CLARIFY + REDUCE the context, count & NAME the meet-irreducible ATTRIBUTES (= columns
surviving attribute reduction: an attribute m is REDUCIBLE iff its object-extent equals
the intersection of the strictly-larger extents that contain it -- i.e. m is the MEET
of other attributes).  Are the irreducibles concentrated on {da,db,de,df}?  Does the
count track 4N+4 (the census), fraction -> 0.5 (=132/256)?

KILL: meet-irreducibles NOT concentrated on {da,db,de,df} (spread, or dd/dg/dh appear).

Skeptic (card + prior-finding #1): "zero single-flip controller" (LINEAR) and
"meet-irreducible" (LATTICE) may merely correlate -- check sample-size stability.  And
a real meet-irreducible count will NOT be a stable basis-independent 132 if it is really
just the 4N+4 control census wearing an FCA hat.

NOTE on method: counting meet-irreducible ATTRIBUTES (attribute reduction) is the
standard, tractable FCA operation and is exactly what the card names ("clarify+reduce,
count the meet-irreducibles").  Enumerating the full concept lattice by next-closure is
unnecessary (and on 8N agreement columns it blows up); the meet-irreducible attributes
are precisely the join-irreducible columns of the closure system and decide the card.
"""
import sys, random
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards')
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import _minisha as m
import shabridge as sb

REG = ('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h')
HARDCORE_REGS = {'a', 'b', 'e', 'f'}   # zero deterministic control (ground truth)


def full_tail_states(P, O, M1, M2, free4):
    """Round-63 states for both messages: cascade 57..60 (W2 s.t. da=0) + schedule tail 61..63."""
    MASK, KN = P['MASK'], P['KN']
    st1, W1 = m.precompute(M1, P, O)
    st2, W2 = m.precompute(M2, P, O)
    W1 = list(W1); W2 = list(W2)
    s1 = list(st1); s2 = list(st2)
    for k, rnd in enumerate(range(57, 61)):
        w1 = free4[k] & MASK
        w2 = m.find_w2(s1, s2, rnd, w1, P, O)
        W1.append(w1); W2.append(w2)
        s1 = list(m.sha_round(s1, KN[rnd], w1, P, O))
        s2 = list(m.sha_round(s2, KN[rnd], w2, P, O))
    for rnd in range(61, 64):
        w1 = (O['s1'](W1[rnd - 2]) + W1[rnd - 7] + O['s0'](W1[rnd - 15]) + W1[rnd - 16]) & MASK
        w2 = (O['s1'](W2[rnd - 2]) + W2[rnd - 7] + O['s0'](W2[rnd - 15]) + W2[rnd - 16]) & MASK
        W1.append(w1); W2.append(w2)
        s1 = list(m.sha_round(s1, KN[rnd], w1, P, O))
        s2 = list(m.sha_round(s2, KN[rnd], w2, P, O))
    return tuple(s1), tuple(s2)


def build_columns(N, n_near, n_rand, seed):
    """Return per-attribute object-extent bitmasks (column j = set of objects agreeing on
    output bit j) plus n_obj.  Attribute j -> register REG[j//N], bit j%N."""
    S = m.setup(N)
    if S is None:
        return None
    P, O, M1, M2 = S['P'], S['O'], S['M1'], S['M2']
    MASK = P['MASK']
    rng = 1 << N
    n_attr = 8 * N
    random.seed(seed)
    samples = [[random.randrange(rng) for _ in range(4)] for _ in range(n_rand)]
    for _ in range(n_near):
        samples.append([random.choice([0, 1, MASK, rng - 1]) if random.random() < 0.5
                        else random.randrange(rng) for _ in range(4)])
    # dedupe objects -> object rows (attribute set per object)
    obj_rows = []
    seen = set()
    for f in samples:
        s1, s2 = full_tail_states(P, O, M1, M2, f)
        xordiff = [s1[r] ^ s2[r] for r in range(8)]
        mask = 0
        for r in range(8):
            for b in range(N):
                if not ((xordiff[r] >> b) & 1):
                    mask |= (1 << (r * N + b))
        if mask not in seen:
            seen.add(mask); obj_rows.append(mask)
    n_obj = len(obj_rows)
    # columns: extent of attribute j = bitmask over objects that have attribute j
    cols = [0] * n_attr
    for oi, row in enumerate(obj_rows):
        for j in range(n_attr):
            if (row >> j) & 1:
                cols[j] |= (1 << oi)
    return dict(cols=cols, n_obj=n_obj, n_attr=n_attr, N=N)


def reduce_attributes(cols, n_obj, n_attr):
    """Standard FCA attribute clarification + reduction over the columns (extents).
    - clarify: attributes with identical extent are merged.
    - reduce:  attribute m is REDUCIBLE (meet-of-others) iff extent(m) == intersection of
      { extent(k) : extent(m) subset extent(k), k != m }.  The full object set is the
      'empty meet' (top), so an extent equal to all objects is reducible (trivial).
    Returns (irreducible_attr_indices, trivial_full, trivial_empty, clarified_classes)."""
    full = (1 << n_obj) - 1
    # clarify: group attrs by extent
    by_ext = {}
    for j in range(n_attr):
        by_ext.setdefault(cols[j], []).append(j)
    reps = {ext: members[0] for ext, members in by_ext.items()}
    rep_exts = list(reps.keys())
    irr = []
    trivial_full = []
    trivial_empty = []
    for ext, rep in reps.items():
        if ext == full:
            trivial_full.append(rep); continue       # always-agree -> top, reducible
        if ext == 0:
            trivial_empty.append(rep); continue       # never-agree -> not a real attr
        # intersection of all strictly-larger-or-equal OTHER extents containing ext
        sup = full
        any_super = False
        for ext2 in rep_exts:
            if ext2 == ext:
                continue
            if (ext & ext2) == ext:   # ext subset ext2
                sup &= ext2
                any_super = True
        # m is meet-irreducible iff the meet of its proper supersets is STRICTLY larger
        # than ext (i.e. ext is not recoverable as a meet of other attributes)
        if (any_super and sup == ext):
            pass  # reducible (meet of others reproduces it)
        else:
            irr.append(rep)
    # map clarified classes to register tags
    return irr, trivial_full, trivial_empty, by_ext


def analyze(N, n_near=120, n_rand=120, seed=0):
    B = build_columns(N, n_near, n_rand, seed)
    if B is None:
        return None
    cols, n_obj, n_attr = B['cols'], B['n_obj'], B['n_attr']
    irr, tfull, tempty, by_ext = reduce_attributes(cols, n_obj, n_attr)
    by_reg = {r: 0 for r in REG}
    for j in irr:
        by_reg[REG[j // N]] += 1
    full_full = {r: 0 for r in REG}
    for j in tfull:
        full_full[REG[j // N]] += 1
    empty_reg = {r: 0 for r in REG}
    for j in tempty:
        empty_reg[REG[j // N]] += 1
    return dict(N=N, n_obj=n_obj, n_attr=n_attr, n_irr=len(irr),
                by_reg=by_reg, n_full=len(tfull), full_by_reg=full_full,
                n_empty=len(tempty), empty_by_reg=empty_reg,
                census_4Np4=4 * N + 4, irr_idx=sorted(irr))


if __name__ == '__main__':
    print("W7-FC1 — meet-irreducible ATTRIBUTES of the round-63 output-agreement lattice")
    print("=" * 76)
    print("Ground truth: hard-core = {a,b,e,f}@63 (4N) + 4 scattered dc => 4N+4 (=132 @N=32);")
    print(f"              fraction (4N+4)/8N -> 0.5 (=132/256). hard-core regs={sorted(HARDCORE_REGS)}\n")
    for N in (4, 6, 8):
        rows = []
        for seed in (0, 1, 2):
            r = analyze(N, n_near=140, n_rand=140, seed=seed)
            if r is None:
                print(f"N={N}: no cascade kernel"); break
            hc = sum(r['by_reg'][x] for x in HARDCORE_REGS)
            other = sum(r['by_reg'][x] for x in REG if x not in HARDCORE_REGS)
            print(f"N={N} seed={seed}: objs={r['n_obj']:3d} 8N={r['n_attr']} "
                  f"meet-IRR-attrs={r['n_irr']:3d}  always-agree(top)={r['n_full']:3d}  "
                  f"never-agree={r['n_empty']:3d}   (census 4N+4={r['census_4Np4']})")
            print(f"     IRR per register : {r['by_reg']}")
            print(f"     always-agree(top): {r['full_by_reg']}")
            print(f"     -> IRR on {{a,b,e,f}}: {hc}   on {{c,d,g,h}}: {other}   "
                  f"{'CONCENTRATED' if hc > 0 and other == 0 else 'SPREAD / non-hardcore present'}")
            rows.append((hc, other, r['n_irr']))
        print()
    print("KILL fires iff meet-irreducibles NOT concentrated on {a,b,e,f} (spread / dd,dg,dh appear).")
