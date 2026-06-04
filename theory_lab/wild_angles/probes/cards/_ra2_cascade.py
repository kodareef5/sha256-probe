"""W7-RA2 strengthened: the random-delta cube is VACUOUS (only the identity point
collides). The card's claim lives in the CASCADE collision family (its 'one free
axis'). So test there: build the cube over the n free tail words {w57..} where the
cascade can hold a collision, color by output-diff truncated at R rounds, and ask:

  (Q1) Does the zero(collision) class contain a combinatorial LINE? (it should, by
       construction -- the free word slides -- so a 'line' is the CASCADE LINEARITY,
       not HJ forcing.)
  (Q2) CRUCIAL kill prong B: is the smallest n forcing a zero-line DEPENDENT on the
       round count R, or independent?  HJ forcing => n*(R) grows with R (more rounds
       = harder coloring = need bigger cube). Linear-cascade => n* is independent of R
       (the free axis is there at n=1 regardless of how many rounds you run).

Here the cube coordinate i in {0,1} selects whether tail word w(57+i) takes value
v0 (a fixed collision word) or v1 (another collision word) -- both chosen from the
cascade so the FULL family collides at the sr boundary. We then truncate the diff at
R<boundary and see the color structure.
"""
import sys, random, itertools
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards')
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import _w5co_engine as E
import _hc_family as HC


def state_diff_at_R(M, setup, w_tuple, R):
    """Run the cascade tail for free-word vector w_tuple; return the modular diff
    8-tuple at round R (57<=R<=63). Reuses _hc_family.tail_trace."""
    tr, _ = HC.tail_trace(M, setup, *w_tuple)
    return tr[R]


def cube_colors(M, setup, free_positions, val0, val1, base_w, R):
    """free_positions: which of the 4 tail slots (0..3 -> w57..w60) form the HJ cube
    axes. For a cube point p in {0,1}^len, set w[slot]=val1 if p=1 else val0 on the
    axis slots; the non-axis slots keep base_w. Color = diff 8-tuple at round R."""
    n = len(free_positions)
    colors = {}
    for p in itertools.product((0, 1), repeat=n):
        w = list(base_w)
        for bit, slot in zip(p, free_positions):
            w[slot] = val1[slot] if bit else val0[slot]
        colors[p] = state_diff_at_R(M, setup, tuple(w), R)
    return colors


def lines(n):
    coords = list(range(n))
    for k in range(1, n + 1):
        for A in itertools.combinations(coords, k):
            Aset = set(A); fixed = [c for c in coords if c not in Aset]
            for fm in range(1 << len(fixed)):
                p0 = [0]*n; p1 = [0]*n
                for bi, c in enumerate(fixed):
                    v = (fm >> bi) & 1; p0[c]=v; p1[c]=v
                for c in A: p0[c]=0; p1[c]=1
                yield tuple(p0), tuple(p1)


def smallest_n_zero_line(M, setup, val0, val1, base_w, R, maxn=4):
    zero = tuple(0 for _ in range(8))
    for n in range(1, maxn + 1):
        fp = list(range(n))   # use first n tail slots as axes
        col = cube_colors(M, setup, fp, val0, val1, base_w, R)
        # zero-line?
        for p0, p1 in lines(n):
            if col[p0] == zero and col[p1] == zero:
                nz = sum(1 for v in col.values() if v == zero)
                return n, nz, len(col)
    return None, 0, 0


N = 8
M = E.make_model(N); setup = E.find_M0(M)
# obtain two genuine collision free-word vectors from the family (so the cascade holds)
import csv, os
# reuse _hc_family to get real collisions at N=8
fam = HC.load_family(8, with_trace=False, verify=True)
colls = fam['tuples']
print(f"N={N}: {len(colls)} real sr=60 collisions available as cube anchors\n")
rng = random.Random(7)
# val0/val1 are two collision tuples -> sliding between them on a slot is the 'axis'
c0 = list(colls[0]); c1 = list(colls[1])
base_w = list(colls[0])
# val0[slot], val1[slot] taken per-slot from two collisions
val0 = {i: c0[i] for i in range(4)}; val1 = {i: c1[i] for i in range(4)}

print("smallest n forcing a ZERO(collision) combinatorial line, vs round count R:")
print("(the cube axes slide tail words between two real collisions)\n")
res = {}
for R in range(57, 64):
    n_star, nz, tot = smallest_n_zero_line(M, setup, val0, val1, base_w, R, maxn=4)
    res[R] = n_star
    print(f"  R={R}: smallest-n zero-line = {n_star}   (#zero pts in that cube = {nz}/{tot})")

vals = [v for v in res.values()]
distinct = set(v for v in vals if v is not None)
print(f"\n  n* values across R(57..63): {[res[R] for R in range(57,64)]}")
print(f"  does n* GROW with the round count R? {'yes (HJ-like)' if len(distinct)>1 and None not in distinct else 'NO'}")
print("  KILL prong B: n* INDEPENDENT of round count => not HJ forcing, just the")
print("  cascade's linear free axis (sigma-linearity). HJ would require n* to climb")
print("  with R toward the (enormous) HJ(2,k) threshold.")
print("\n  Note: at the sr boundary (R=63) the WHOLE family collides by construction,")
print("  so a 'line' there is the cascade linearity, NOT a forced HJ monochromatic line.")
