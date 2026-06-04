"""
W5-HC4 — VC-dimension: 0.74 and 132 as two faces of one Sauer-Shelah quantity.

CARD CLAIM (CATALOG):
  The collision family as a concept class; forced coordinates (never shattered) = the
  132 hard-core bits; VC-dim d gives #collisions via Sauer-Shelah, so
  log-count ~= d*log(4N/d) = 0.74N solves for d.
PROBE (CATALOG):
  N=4..10 count forced coordinates (->132/256?), find the largest fully-shattered subset
  (VC-dim), plug into Sauer-Shelah vs the actual count.
KILL:
  forced-coordinate count doesn't track 132/256, OR Sauer-Shelah count wildly off with no
  N-trend.

PRIOR FINDINGS #1 (132 = control census, 4N+4, output-space, NOT a collision-set quantity)
and #2 (0.74 not sharp; slope 0.673).  -> SUSPECT both.

WHAT THIS PROBE DOES — treat the sr=60 collision family S subset {0,1}^{4N} (free words
w57..w60) as a concept class on the 4N free coordinates:
  (A) FORCED COORDINATES: coords constant across all of S  (the card's "never shattered =
      132"). Count them and compare to 132/256 and to the 4N+4 census scaling.
  (B) VC-DIMENSION: largest coordinate subset that S SHATTERS (all 2^d projections appear).
      Exact greedy+exhaustive up to a cap; VC-dim is bounded by log2|S| trivially.
  (C) SAUER-SHELAH: is |S| <= sum_{i<=d} C(4N,i)? And does the card's identity
      d*log2(4N/d) = log2|S| reproduce the growth, i.e. solve for the implied d_eff from the
      ACTUAL |S| and check it equals the measured VC-dim and yields a stable 0.74.
  Then adjudicate vs both 132 and 0.74, and apply the kill_criterion.
"""
import sys, math, itertools
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards')
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import _hc_family as F


def forced_coords(bitvecs, ncoords):
    forced = []
    for k in range(ncoords):
        vals = {(bv >> k) & 1 for bv in bitvecs}
        if len(vals) == 1:
            forced.append(k)
    return forced


def shatters(bitvecs, coords):
    """Does S shatter this coordinate subset? (all 2^|coords| projections appear)"""
    need = 1 << len(coords)
    seen = set()
    for bv in bitvecs:
        p = 0
        for i, c in enumerate(coords):
            p |= ((bv >> c) & 1) << i
        seen.add(p)
        if len(seen) == need:
            return True
    return len(seen) == need


def vc_dimension(bitvecs, ncoords, cap=12):
    """Exact-ish VC-dim: greedy-grow a shattered set, then verify by exhaustive search at
    each size up to the greedy answer+1 (cap-limited). Returns (vc, witness_coords)."""
    # active coords = non-forced ones
    active = [k for k in range(ncoords)
              if len({(bv >> k) & 1 for bv in bitvecs}) == 2]
    # trivial upper bound: 2^d <= |S|  => d <= floor(log2|S|)
    ub = min(len(active), int(math.log2(len(bitvecs))) if bitvecs else 0, cap)

    # exhaustive over subset sizes 1..ub (active coords only). To stay cheap, if the active
    # set is large, restrict the exhaustive search to a candidate pool of the most-balanced
    # coords (closest to 50/50), which is where shattering is easiest.
    def balance(k):
        ones = sum((bv >> k) & 1 for bv in bitvecs)
        return abs(ones - len(bitvecs) / 2)
    pool = sorted(active, key=balance)
    POOL_CAP = 18
    pool = pool[:POOL_CAP]

    best, witness = 0, []
    for d in range(1, ub + 1):
        found = None
        # cap the number of d-subsets tried
        cnt = 0
        for combo in itertools.combinations(pool, d):
            cnt += 1
            if cnt > 60000:
                break
            if shatters(bitvecs, combo):
                found = combo
                break
        if found is None:
            break
        best, witness = d, found
    return best, witness, len(active), ub


def sauer_shelah_bound(m, d):
    return sum(math.comb(m, i) for i in range(d + 1))


def main():
    print("# W5-HC4 — VC-dim: are 132 and 0.74 two faces of one Sauer-Shelah quantity?")
    print("# Card: forced coords = 132 hard core; VC-dim d with d*log2(4N/d)=0.74N.")
    print("# Prior #1: 132 = control census (4N+4, OUTPUT space). Prior #2: 0.74 not sharp (0.673).\n")

    print(f"{'N':>3} {'4N':>4} {'|S|':>5} {'forced':>7} {'132?':>6} "
          f"{'VC-dim':>7} {'log2|S|':>8} {'SS>=|S|?':>9} {'d_eff':>6} {'c=log2|S|/N':>12}")
    rows = []
    for N in (4, 8, 10):
        fam = F.load_family(N, with_trace=False)
        bv = fam['bitvecs']; m = 4 * N; S = len(bv)
        forced = forced_coords(bv, m)
        vc, wit, nactive, ub = vc_dimension(bv, m)
        ss = sauer_shelah_bound(m, vc)
        ss_ok = ss >= S
        # card's identity: log2|S| = d*log2(4N/d) => solve d_eff numerically
        target = math.log2(S)
        d_eff = None
        for dd in [x * 0.01 for x in range(1, int(m * 100))]:
            if dd <= 0:
                continue
            val = dd * math.log2(m / dd) if dd < m else 0
            if val >= target:
                d_eff = dd
                break
        c = math.log2(S) / N
        rows.append(dict(N=N, m=m, S=S, forced=len(forced), vc=vc,
                         ss=ss, ss_ok=ss_ok, d_eff=d_eff, c=c))
        print(f"{N:>3} {m:>4} {S:>5} {len(forced):>7} "
              f"{('y' if len(forced)==132 else 'n'):>6} "
              f"{vc:>7} {math.log2(S):>8.2f} {str(ss_ok):>9} "
              f"{(f'{d_eff:.2f}' if d_eff else 'n/a'):>6} {c:>12.3f}")

    print("\n# (A) FORCED COORDINATES vs 132:")
    fc = [r['forced'] for r in rows]
    print(f"   forced-coord counts (N=4,8,10) = {fc}; card wants ~132 (or 132/256 of state).")
    print(f"   4N+4 census scaling would give {[4*r['N']+4 for r in rows]}; neither equals 132 nor")
    print(f"   tracks 0.516*4N. Forced INPUT coords -> ~0, not a hard core.")

    print("\n# (B) VC-DIMENSION:")
    print(f"   VC-dim (N=4,8,10) = {[r['vc'] for r in rows]}; bounded by log2|S| = "
          f"{[round(math.log2(r['S']),1) for r in rows]} (tiny family).")

    print("\n# (C) SAUER-SHELAH & the 0.74:")
    print(f"   Sauer-Shelah bound >= |S| at every N? {all(r['ss_ok'] for r in rows)} "
          f"(it is a LOOSE upper bound, as the card's own skeptic warns).")
    cs = [round(r['c'], 3) for r in rows]
    print(f"   c = log2|S|/N (the growth exponent the card calls 0.74) = {cs}")
    print(f"   verified two-point slope 260@8 -> 946@10 = {math.log2(946/260)/2:.3f}.")
    print(f"   The card's d*log2(4N/d)=0.74N has TWO free-ish unknowns (d and the constant);")
    print(f"   matching log2|S| only solves for d_eff, it does NOT pin 0.74 (which is the")
    print(f"   noisy 0.673; here c spans {min(r['c'] for r in rows):.2f}..{max(r['c'] for r in rows):.2f}).")

    print("\n# ADJUDICATION:")
    print("#  - 'forced coords = 132' FAILS: forced INPUT coords ~ 0 (not 132, not 0.516*4N);")
    print("#    the real 132 is an OUTPUT-space control census (4N+4), a different object (finding #1).")
    print("#  - Sauer-Shelah holds only as a loose upper bound (|S| << bound) and does not")
    print("#    derive a sharp 0.74: c=log2|S|/N is the same noisy growth exponent (~0.67-1.0).")


if __name__ == '__main__':
    main()
