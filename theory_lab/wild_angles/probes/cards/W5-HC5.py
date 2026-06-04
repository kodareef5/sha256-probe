"""
W5-HC5 — de58 single-petal: why only de58 grows, and the count decomposition.

CARD CLAIM (CATALOG):
  de57/59/60 constant = a frozen 3-coordinate sunflower CORE; de58 = the unique
  PETAL coordinate; |de58| ~ 2^{0.31N} is the petal exponent, and
  petal-exponent + fiber-exponent should ~= 0.74 (the collision growth slope).
  Mostly NAMES an observed fact + tests the count split.

PROBE (CATALOG):
  N=8..14 confirm de57/59/60 single-valued; tabulate the de58 petal set
  (log/N -> petal exponent) and fiber sizes (-> fiber exponent); does the sum
  ~= 0.74?
KILL:
  core leaks (de57/59/60 not constant), OR petal+fiber exponents don't sum to
  the slope (+-0.1).

PRIOR FINDING #5 (de58 thread CLOSED): |de58| = 2^hw(db56) = a Maj/AND image-count,
  non-monotone, group-free, no deeper invariant. CONFIRM only if the sunflower-petal
  decomposition DERIVES 2^hw(db56). Otherwise it RESTATES a known fact = not a CONFIRMED.
PRIOR FINDING #2: 0.74 is NOT sharp; slope = 0.673, spread 0.72-1.04.

What this probe does:
  (A) Compute de57..de60 sizes exactly at N=4,5,8,10,11,12,13,14 (the reachable,
      cascade-eligible widths), reproducing the de-set law. Confirm core = {57,59,60}=1.
  (B) The de58 "petal exponent": is log2|de58|/N a STABLE 0.31? Show it is NOT
      (it tracks hw(db56)/N, which is non-monotone). DERIVE-test: does the
      petal-count equal 2^hw(db56)?  (the real law)
  (C) The "fiber exponent": the card wants #collisions ~= 2^(petal+fiber)N.
      Fiber = collisions per de58 value = #collisions / |de58|. Compute fiber
      exponent = log2(fiber)/N and petal exponent = log2|de58|/N, sum them, and
      compare to BOTH the card's 0.74 and the real slope 0.673.
  (D) Adjudicate: does the petal/fiber split DERIVE anything new (2^hw(db56) or a
      sharp 0.74), or merely re-partition known numbers?
"""
import sys, math
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards')
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import _w5co_engine as E
import shabridge as sb

# ----- exact de-set sizes via the engine's faithful mini-SHA (matches gap_analysis.c) -----
def de_sets(N):
    """Return (sizes dict {57,58,59,60}, db56, hw_db56) by sweeping the cascade tail.
    de_r = (e1 - e2) mod 2^N after round r, over the free tail words (path-2 cascaded)."""
    M = E.make_model(N)
    setup = E.find_M0(M)
    if setup is None:
        return None
    MASK = M['MASK']
    s1_56, s2_56 = setup['st1'], setup['st2']
    db56 = (s1_56[1] ^ s2_56[1]) & MASK          # XOR diff of register b at round 56
    KN = M['KN']

    def step(s1, s2, rnd, w1):
        # path-2 free word forced so da stays 0 (cascade), exactly as run_tail/find_w2.
        # NOTE: find_w2 takes the ROUND NUMBER (it looks up K internally).
        w2 = E.find_w2(s1, s2, rnd, w1, M)
        return E.sha_round(s1, KN[rnd], w1, M), E.sha_round(s2, KN[rnd], w2, M)

    de = {57: set(), 58: set(), 59: set(), 60: set()}
    R = MASK + 1
    # de57 depends on w57; de58 on (w57,w58); de59/de60 are constant (sample a ray).
    w57_iter = range(R) if R <= 4096 else range(0, R, max(1, R // 4096))
    w58_iter = range(R) if R <= 4096 else range(0, R, max(1, R // 4096))
    for w57 in w57_iter:
        s1a, s2a = step(s1_56, s2_56, 57, w57)
        de[57].add((s1a[4] - s2a[4]) & MASK)
        for w58 in w58_iter:
            s1b, s2b = step(s1a, s2a, 58, w58)
            de[58].add((s1b[4] - s2b[4]) & MASK)
            if w58 < 8:  # de59/de60 constant: a small ray suffices
                for w59 in range(min(R, 64)):
                    s1c, s2c = step(s1b, s2b, 59, w59)
                    de[59].add((s1c[4] - s2c[4]) & MASK)
                    s1d, s2d = step(s1c, s2c, 60, 0)
                    de[60].add((s1d[4] - s2d[4]) & MASK)
    return {r: len(de[r]) for r in de}, db56, sb.hw(db56)


# collision counts (the terminal sr=60 family size) for the fiber computation.
# Pure-Python exhaustive enumeration is only feasible at N<=5; for N=8,10 use the
# repo's verified counts (260, 946) — read-only ground truth.
KNOWN_COLL = {4: 49, 8: 260, 10: 946}   # verified counts; N=5 full-enum too slow, not needed

def count_collisions(N):
    if KNOWN_COLL.get(N):
        return KNOWN_COLL[N]
    if N <= 4:
        colls, _, _ = E.enumerate_tail(N, want='collide')
        return len(colls)
    return None   # de-set still computed; fiber row just skipped where count unavailable


def main():
    print("# W5-HC5 — de58 single-petal decomposition")
    print("# Card: core={de57,de59,de60}=1; petal=de58~2^0.31N; petal+fiber~=0.74")
    print("# Prior #5: |de58|=2^hw(db56) (Maj/AND image). Prior #2: slope=0.673 not 0.74.\n")

    # Live exact recompute at the fast, cascade-eligible widths; the larger-N de-set
    # sweep is exponential, so for N>=11 we cite the repo's published exact table
    # (paper_figures_data.md Fig 3, read-only) to show the petal-exponent's behaviour.
    Ns = [4, 5, 8, 10]
    # repo Fig 3 (exact for N<=14): (N -> (|de58|, hw(db56)))
    PUBLISHED_DE58 = {11: (32, 5), 12: (512, 9), 13: (32, 5), 14: (32, 5),
                      16: (256, 8), 32: (1024, 17)}
    rows = []
    print(f"{'N':>3} {'de57':>5} {'de58':>6} {'de59':>5} {'de60':>5} "
          f"{'hw(db56)':>8} {'2^hw':>6} {'match':>6} {'log2|de58|/N':>13}  src")
    core_ok = True
    for N in Ns:
        r = de_sets(N)
        if r is None:
            print(f"{N:>3}   (no cascade-eligible M0)")
            continue
        sizes, db56, hwd = r
        d57, d58, d59, d60 = sizes[57], sizes[58], sizes[59], sizes[60]
        two_hw = 1 << hwd
        match = (d58 == two_hw)
        petal_exp = math.log2(d58) / N if d58 > 0 else 0.0
        rows.append(dict(N=N, d57=d57, d58=d58, d59=d59, d60=d60,
                         hwd=hwd, two_hw=two_hw, match=match, petal_exp=petal_exp))
        if not (d57 == 1 and d59 == 1 and d60 == 1):
            core_ok = False
        print(f"{N:>3} {d57:>5} {d58:>6} {d59:>5} {d60:>5} {hwd:>8} {two_hw:>6} "
              f"{str(match):>6} {petal_exp:>13.3f}  live")

    print(f"# --- published exact table (repo Fig 3, read-only; de57/59/60=1 there) ---")
    pub_rows = []
    for N in sorted(PUBLISHED_DE58):
        d58, hwd = PUBLISHED_DE58[N]
        two_hw = 1 << hwd
        match = (d58 == two_hw)            # NO at N=32 (carry collapse), YES otherwise
        petal_exp = math.log2(d58) / N
        pub_rows.append(dict(N=N, d58=d58, hwd=hwd, two_hw=two_hw, match=match,
                             petal_exp=petal_exp))
        print(f"{N:>3} {'1':>5} {d58:>6} {'1':>5} {'1':>5} {hwd:>8} {two_hw:>6} "
              f"{str(match):>6} {petal_exp:>13.3f}  pub")

    print(f"\n[CORE] de57=de59=de60=1 at every reachable LIVE N? {core_ok} "
          f"(published table also has them =1).")
    all_match = all(x['match'] for x in rows) and all(
        p['match'] for p in pub_rows if p['N'] <= 14)
    print(f"[DERIVE-TEST] |de58| == 2^hw(db56) for N<=14 (live+pub)? {all_match} "
          f"(breaks at N=32: 1024 != 2^17 = carry collapse).")
    pe = [x['petal_exp'] for x in rows] + [p['petal_exp'] for p in pub_rows]
    pe_N = [(x['N'], round(x['petal_exp'], 2)) for x in rows] + \
           [(p['N'], round(p['petal_exp'], 2)) for p in pub_rows]
    print(f"[PETAL EXP] log2|de58|/N spans {min(pe):.3f}..{max(pe):.3f} "
          f"(card claims a stable 0.31).")
    print(f"   NON-MONOTONE in N: {pe_N}")
    print(f"   (e.g. N=11->0.45, N=12->0.75, N=13->0.38: a jagged hw(db56)/N, not 0.31.)")

    # ----- petal + fiber sum vs the slope -----
    print("\n# (C) petal-exponent + fiber-exponent vs the slope")
    print(f"{'N':>3} {'#coll':>6} {'|de58|':>6} {'fiber=coll/de58':>16} "
          f"{'petal_exp':>9} {'fiber_exp':>9} {'SUM':>6}")
    sums = []
    for x in rows:
        N = x['N']
        nc = count_collisions(N)
        if nc is None:
            print(f"{N:>3}   (collision count not available at this N)")
            continue
        fiber = nc / x['d58']
        fiber_exp = math.log2(fiber) / N if fiber > 0 else 0.0
        s = x['petal_exp'] + fiber_exp
        sums.append((N, s))
        print(f"{N:>3} {nc:>6} {x['d58']:>6} {fiber:>16.3f} "
              f"{x['petal_exp']:>9.3f} {fiber_exp:>9.3f} {s:>6.3f}")

    print(f"\n# Note: petal_exp + fiber_exp = log2(|de58|)/N + log2(#coll/|de58|)/N")
    print(f"#       = log2(#coll)/N  IDENTICALLY (the |de58| cancels).")
    print(f"#       So the 'sum' is just the raw collision-growth exponent log2(#coll)/N,")
    print(f"#       which the repo measures as a NOISY 0.673 (spread 0.72-1.04), not 0.74.")
    if sums:
        ss = [s for _, s in sums]
        print(f"[SUM] petal+fiber spans {min(ss):.3f}..{max(ss):.3f}; "
              f"card target 0.74, real slope 0.673.")
        # two-point slope from the cleanest verified anchors N=8->10 (260->946)
        if 8 in dict(sums) and 10 in dict(sums):
            slope_810 = math.log2(946 / 260) / (10 - 8)
            print(f"[ANCHOR] verified two-point slope 260@8 -> 946@10 = {slope_810:.3f} "
                  f"(NOT 0.74, NOT 0.31+anything sharp).")

    print("\n# VERDICT LOGIC:")
    print("#  - CORE confirmed (de57/59/60=1): TRUE structural fact, but RESTATEMENT.")
    print("#  - DERIVE-TEST: the petal partition does NOT derive 2^hw(db56); the real")
    print("#    law |de58|=2^hw(db56) is INPUT here, the card's '0.31N' is just a")
    print("#    re-description and is non-monotone (not a real exponent).")
    print("#  - petal+fiber 'sum' = log2(#coll)/N identically => it CANNOT be a new")
    print("#    prediction; it reproduces the noisy 0.673, and the card's 0.74 is not sharp.")


if __name__ == '__main__':
    main()
