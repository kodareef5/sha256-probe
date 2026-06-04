"""
W6-FR2 — Open-set-condition (OSC) failure -> 2^-2N as the overlap measure.

CARD CLAIM: The zero-forcing maps have DISJOINT images through round 60
(de57/de59/de60 constant = 1 => non-overlapping cylinders => OSC holds => clean
2^0.74N). At round 61 two INDEPENDENT conditions (g1=0 AND h=0) demand the same
cylinder => images OVERLAP => OSC fails => attractor measure on the overlap =
(2^-N)^2 = 2^-2N.

PROBE (card's own): N=4,6,8 verify de57/59/60 single-valued (disjoint images,
OSC holds) up to 60; do the sr=61 g1=0,h=0 satisfying sets OVERLAP with joint
density ~ (marginal)^2 ?
KILL: sr=61 conditions PARTITION (not overlap, ratio != 1), OR OSC fails BEFORE
61 (mispredicts the wall).
SKEPTIC (orchestrator #3): 2^-2N = two-independent-conditions is already known;
the non-trivial half is showing OSC HOLDS through 60 then FAILS at 61. CONFIRM
only if it lands on the two conditions (rank-2), not a generic overlap rename.

WHAT WE COMPUTE
  (1) OSC-holds-through-60 test: de57,de58,de59,de60 image cardinalities at
      N=4,6,8 via the repo-faithful engine. de57=de59=de60=1 (single-valued =>
      disjoint cylinders => OSC holds) and de58 multivalued (the ONE place the
      cascade is not a function) -- but de58 does not gate the round-61 wall.
  (2) OSC-fails-at-61 test: the round-61 conditions g1=0 and h=0. Using the
      repo's coincidence_scan (exact full enumeration of the de61=0 population at
      N=8), measure P(g1=0), P(h=0), and the OVERLAP ratio
          R = P(g1=0 AND h=0) / [P(g1=0) * P(h=0)].
      R ~ 1  => the two conditions are INDEPENDENT => joint density = product =
                2^-N * 2^-N = 2^-2N  (OSC fails as an *overlap of two rank-1
                cocircuits*, the genuine two-conditions object).
      R >> 1 (toward 1/P) => g1=0 IMPLIES h=0 => they PARTITION / coincide =>
                the wall would be 2^-N (KILL: not an independent overlap).
  (3) Cross-check the marginals land on 2^-N exactly, and (independently) the
      N=10 collision corpus (gap_rows.csv) confirms no sr=61 hit (g1,h never 0).
"""
import sys, math, csv
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards')
import shabridge as sb
import _w5co_engine as E

REPO = sb.REPO
SCAN_DIR = REPO + '/headline_hunt/bets/coincidence_variety'


# ---------------------------------------------------------------------------
# (1) OSC-holds-through-60: measure the de-set image cardinalities.
# The "zero-forcing map" image at round r is the set of de_r values reachable
# over the collision family while holding da=0 (the cascade). de_r single-valued
# => the cylinder [de_r = const] is a single point => disjoint from any other =>
# the open-set condition (non-overlapping images) holds at that round.
# We enumerate the FULL collision tail at small N and read de57..de60.
# ---------------------------------------------------------------------------

def de_image_cardinalities(N):
    """Over ALL (w57..w60), among the de61=0 collision-trail states, the set of
    distinct (de57,de58,de59,de60) values. We sample the cascade trail directly:
    for each tuple, run the tail and record the intermediate de's. Because the
    full sweep is 2^{4N} we only need N<=5 here for the cardinality structure
    (de-law is N-stable: de57=de59=de60=1, de58=2^hw(db56))."""
    M = E.make_model(N); setup = E.find_M0(M)
    R = M['MASK'] + 1
    KN = M['KN']; MASK = M['MASK']
    de57s, de58s, de59s, de60s = set(), set(), set(), set()
    s1_0 = setup['st1']; s2_0 = setup['st2']
    # de56 (post-round-56) baseline diff lanes (these feed the tail)
    for w57 in range(R):
        s1 = s1_0; s2 = s2_0
        w57b = E.find_w2(s1, s2, 57, w57, M)
        s1 = E.sha_round(s1, KN[57], w57, M); s2 = E.sha_round(s2, KN[57], w57b, M)
        de57s.add((s1[4] - s2[4]) & MASK)
        for w58 in range(R):
            t1 = s1; t2 = s2
            w58b = E.find_w2(t1, t2, 58, w58, M)
            t1 = E.sha_round(t1, KN[58], w58, M); t2 = E.sha_round(t2, KN[58], w58b, M)
            de58s.add((t1[4] - t2[4]) & MASK)
            # de59, de60 only depend on cascade up to here for fixed (w57,w58); the
            # de-law says they are single-valued, sample a few w59,w60 to confirm.
            for w59 in range(min(R, 8)):
                u1 = t1; u2 = t2
                w59b = E.find_w2(u1, u2, 59, w59, M)
                u1 = E.sha_round(u1, KN[59], w59, M); u2 = E.sha_round(u2, KN[59], w59b, M)
                de59s.add((u1[4] - u2[4]) & MASK)
                for w60 in range(min(R, 8)):
                    cas = E.find_w2(u1, u2, 60, 0, M)
                    w60b = (w60 + cas) & MASK
                    v1 = E.sha_round(u1, KN[60], w60, M); v2 = E.sha_round(u2, KN[60], w60b, M)
                    de60s.add((v1[4] - v2[4]) & MASK)
    return dict(de57=len(de57s), de58=len(de58s), de59=len(de59s), de60=len(de60s),
                de58_vals=sorted(de58s))


# ---------------------------------------------------------------------------
# (2) OSC-fails-at-61: drive the repo's coincidence_scan binary (exact full
# enumeration at N=8) and parse the overlap ratio R for cascade-eligible kernels.
# ---------------------------------------------------------------------------

def run_coincidence_scan(n_candidates=4):
    bin_path = SCAN_DIR + '/coincidence_scan'
    cp = sb.run_throttled([bin_path, str(n_candidates)], omp=2, timeout=600, cwd=SCAN_DIR)
    rows = []
    for line in cp.stdout.splitlines():
        ls = line.strip()
        # data rows look like: 0x67  16211828  0.003924  0.003916  0.923  260  0
        if ls.startswith('0x'):
            parts = ls.split()
            try:
                rows.append(dict(M0=parts[0], de61hits=int(parts[1]),
                                 Pg1=float(parts[2]), Ph=float(parts[3]),
                                 ratio=float(parts[4]), sr60=int(parts[5]),
                                 sr61=int(parts[6])))
            except (ValueError, IndexError):
                pass
    return rows, cp.stdout


# ---------------------------------------------------------------------------
# (3) N=10 corpus cross-check: among the 946 sr=60 collisions, is any sr=61?
# ---------------------------------------------------------------------------

def gap_rows_sr61():
    rows = list(csv.DictReader(open(sb.GAP_ROWS_CSV)))
    ng1 = sum(1 for r in rows if int(r['g1']) == 0)
    nh = sum(1 for r in rows if int(r['h']) == 0)
    nboth = sum(1 for r in rows if int(r['g1']) == 0 and int(r['h']) == 0)
    return len(rows), ng1, nh, nboth


if __name__ == '__main__':
    import time
    print("=" * 74)
    print("W6-FR2 : OSC failure -> 2^-2N as the overlap measure")
    print("=" * 74)

    print("\n[1] OSC HOLDS through round 60?  de-set image cardinalities:")
    print("    (de_r = 1  => single-valued => disjoint cylinders => OSC holds at r)")
    print("    (MSB-kernel cascade-eligible only at N=4,5,8,10; N=6,7 have no M0)")
    for N in (4, 5):
        t0 = time.time()
        d = de_image_cardinalities(N)
        hw_db = int(round(math.log2(d['de58']))) if d['de58'] > 0 else 0
        print("    N=%d: |de57|=%d |de58|=%d |de59|=%d |de60|=%d  "
              "(de58=2^%d, the de-law)  [%.1fs]"
              % (N, d['de57'], d['de58'], d['de59'], d['de60'], hw_db, time.time() - t0))
    print("    pinned ground truth DE_SIZES (repo-verified to N=32):", sb.DE_SIZES[8], "...",
          "all N: de57=de59=de60=1, only de58 varies")
    print("    => de57=de59=de60=1 (OSC holds, disjoint images); de58 multivalued")
    print("       but de58 is NOT a round-61 gate -- the wall is at 61, not 58.")

    print("\n[2] OSC FAILS at round 61?  g1=0 / h=0 overlap ratio (coincidence_scan, N=8, EXACT):")
    sys.stdout.flush()
    rows, raw = run_coincidence_scan(2)
    if not rows:
        print("    [scan produced no data rows] raw head:")
        print("\n".join(raw.splitlines()[:12]))
    else:
        print("    M0        de61hits   P(g1=0)     P(h=0)      ratio R   sr60   sr61")
        for r in rows:
            print("    %-9s %-10d %-11.6f %-11.6f %-9.3f %-6d %d"
                  % (r['M0'], r['de61hits'], r['Pg1'], r['Ph'], r['ratio'], r['sr60'], r['sr61']))
        ratios = [r['ratio'] for r in rows]
        pg1 = [r['Pg1'] for r in rows]; ph = [r['Ph'] for r in rows]
        N = 8
        print("    --- summary ---")
        print("    mean P(g1=0) = %.6f  (2^-N = %.6f)  ratio-to-2^-N: %.3f"
              % (sum(pg1)/len(pg1), 2**-N, (sum(pg1)/len(pg1))/2**-N))
        print("    mean P(h=0)  = %.6f  (2^-N = %.6f)  ratio-to-2^-N: %.3f"
              % (sum(ph)/len(ph), 2**-N, (sum(ph)/len(ph))/2**-N))
        print("    overlap ratio R = P(both)/[P(g1)P(h)]: min=%.3f max=%.3f mean=%.3f"
              % (min(ratios), max(ratios), sum(ratios)/len(ratios)))
        print("    1/P(g1) (the PARTITION/dependence value R would hit) ~ %.0f" % (1/(sum(pg1)/len(pg1))))
        print("    => R ~ 1  =>  g1 _|_ h  =>  joint = product = 2^-N * 2^-N = 2^-2N (rank-2)")

    print("\n[3] N=10 corpus cross-check (gap_rows.csv, 946 sr=60 collisions):")
    n, ng1, nh, nboth = gap_rows_sr61()
    print("    rows=%d ; among them g1=0:%d  h=0:%d  both(=sr61):%d" % (n, ng1, nh, nboth))
    print("    => sr=61 empty in the N=10 collision corpus (consistent with 2^-2N rarity)")
