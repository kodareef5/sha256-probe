"""
W6-FR3 — de58 set-renormalization -> width-(N+1) collisions contain scaled
width-N copies.

CARD CLAIM: If the collision set is self-similar, each de58 class at width N+1,
rescaled (drop one bit), = the full width-N collision set; the growth |de58|(N)
is the renormalization branching, and C(N+1) ~ 2^0.74 * C(N) is its fixed point
(intercept 2.47 = the seed measure). A CONSTRUCTIVE lever (build N+1 from N).

PROBE (card's own): enumerate N=8 and N=10 da=0 collision sets, tag by de58
class; does a FIXED bit-shift map send each N=10 class onto the N=8 set (multiset
overlap >80%)? C ratios vs 2^0.74?
KILL: down-projected classes don't nest (overlap <50%, no consistent scaling map).
SKEPTIC (orchestrator #5): the map must be PRE-SPECIFIED and checked as a multiset,
or it degenerates to "both sets are biggish"; |de58|={2,8,8,16,512,1024} is
IRREGULAR (warns against EXACT nesting). de58 thread CLOSED: |de58|=2^hw(db56) =
carry-collapse/Maj-image count, NON-monotone. CONFIRM only if the renormalization
DERIVES 2^hw(db56) or a real self-similar structure, not restate.

WHAT WE COMPUTE (reads the lab-side C collision dumps, exact full enumeration):
  (1) de58-class structure at N=8,10: #distinct de58 values (= |de58|), class
      sizes; does it match 2^hw(db56)?  [DERIVE vs restate test]
  (2) Self-similarity: a PRE-SPECIFIED bit-shift projection P (drop the top
      (N1-N2) bits OR the bottom) mapping N=10 word-tuples -> N=8 word-tuples,
      and de58 -> projected class. Multiset overlap of P(coll_N10) with coll_N8.
      Test BOTH directions (per-class and global) and BOTH shift choices, and a
      random-baseline overlap so a high number isn't just density.
  (3) Growth ratio C(10)/C(8) vs 2^0.74*(10-8) (the renormalization fixed point).
"""
import sys, math, csv
from collections import Counter, defaultdict
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb


def load(path):
    rows = list(csv.DictReader(open(path)))
    for r in rows:
        for k in r:
            r[k] = int(r[k])
    return rows


def de58_classes(rows):
    cls = defaultdict(list)
    for r in rows:
        cls[r['de58']].append(r)
    return cls


def proj_word(w, drop, mode, N1):
    """Project an N1-bit word to N2 = N1-drop bits.
    mode='hi': drop the top `drop` bits (keep low N2). mode='lo': drop the bottom
    `drop` bits (keep high N2, i.e. w >> drop)."""
    if mode == 'hi':
        return w & ((1 << (N1 - drop)) - 1)
    else:
        return w >> drop


def proj_tuple(r, drop, mode, N1):
    return tuple(proj_word(r[k], drop, mode, N1) for k in ('w57', 'w58', 'w59', 'w60'))


def multiset_overlap(setA, projected_listB):
    """Fraction of projected-B tuples that land in setA (the N=8 collision set).
    setA = set of N=8 word-tuples. Returns (hit_fraction, n_distinct_hit)."""
    hits = sum(1 for t in projected_listB if t in setA)
    distinct_hit = len(set(t for t in projected_listB if t in setA))
    return hits / len(projected_listB), distinct_hit


def random_baseline(setA, N2, n_draw, seed=0):
    """Expected overlap if projected tuples were random N2-bit 4-tuples: |setA| /
    2^(4 N2). This is the null a real nesting must beat."""
    return len(setA) / (1 << (4 * N2))


if __name__ == '__main__':
    print("=" * 74)
    print("W6-FR3 : de58 set-renormalization -> width-(N+1) contains scaled width-N")
    print("=" * 74)

    P8, P10 = '/tmp/coll_n8.csv', '/tmp/coll_n10.csv'
    rows8 = load(P8)
    try:
        rows10 = load(P10)
    except FileNotFoundError:
        rows10 = None
    print("\n[counts] N=8: %d collisions   N=10: %s collisions"
          % (len(rows8), len(rows10) if rows10 else "MISSING (run /tmp/w6fr_dump10)"))

    print("\n[1] de58-class structure (DERIVE 2^hw(db56) vs restate):")
    for tag, rows in (("N=8", rows8), ("N=10", rows10)):
        if not rows:
            continue
        cls = de58_classes(rows)
        db56 = rows[0]['db56']; hw = bin(db56).count('1')
        sizes = sorted((len(v) for v in cls.values()), reverse=True)
        print("    %s: db56=%d hw(db56)=%d => 2^hw=%d ; #distinct de58 classes=%d"
              % (tag, db56, hw, 2 ** hw, len(cls)))
        print("         de58 values=%s" % sorted(cls.keys()))
        print("         class sizes=%s (sum=%d)" % (sizes, sum(sizes)))
        de58_pred = sb.DE_SIZES.get(int(tag.split('=')[1]), ('?',) * 4)[1]
        print("         |de58| pinned (DE_SIZES)=%s  ;  observed #classes=%d  match=%s"
              % (de58_pred, len(cls), len(cls) == de58_pred))

    if rows10 is None:
        print("\n[2,3] SKIPPED -- N=10 dump not ready.")
        sys.exit(0)

    print("\n[2] Self-similarity: PRE-SPECIFIED bit-shift P: N10 -> N8 (drop 2 bits).")
    set8 = set((r['w57'], r['w58'], r['w59'], r['w60']) for r in rows8)
    N1, N2, drop = 10, 8, 2
    base = random_baseline(set8, N2, len(rows10))
    print("    |set8|=%d ; random-baseline overlap = |set8|/2^(4*8) = %.2e" % (len(set8), base))
    for mode in ('hi', 'lo'):
        projB = [proj_tuple(r, drop, mode, N1) for r in rows10]
        frac, dh = multiset_overlap(set8, projB)
        print("    mode=%s (drop %s 2 bits): projected-N10-in-set8 = %.4f (%d/%d), distinct-hit=%d"
              % (mode, 'top' if mode == 'lo' else 'bottom', frac, int(frac * len(projB)), len(projB), dh))
        print("         vs random-baseline %.2e  -> lift x%.1f  (need >0.80 for nesting)"
              % (base, frac / base if base > 0 else float('inf')))

    print("\n[2b] Per-de58-class nesting (each N10 class -> N8 set, best shift):")
    cls10 = de58_classes(rows10)
    for de58v, members in sorted(cls10.items()):
        best = 0.0; bestmode = None
        for mode in ('hi', 'lo'):
            projB = [proj_tuple(r, drop, mode, N1) for r in members]
            frac, _ = multiset_overlap(set8, projB)
            if frac > best:
                best, bestmode = frac, mode
        print("    de58=%4d (%4d members): best-overlap=%.4f (mode=%s)"
              % (de58v, len(members), best, bestmode))

    print("\n[3] Growth ratio C(10)/C(8) vs 2^0.74 fixed point:")
    ratio = len(rows10) / len(rows8)
    print("    C(8)=%d  C(10)=%d  ratio=%.3f" % (len(rows8), len(rows10), ratio))
    print("    predicted 2^(0.74*(10-8)) = %.3f   |   observed = %.3f" % (2 ** (0.74 * 2), ratio))
    print("    (per-N slope here = %.3f ; cf pooled 0.673, NOT 0.74)" % (math.log2(ratio) / 2))
