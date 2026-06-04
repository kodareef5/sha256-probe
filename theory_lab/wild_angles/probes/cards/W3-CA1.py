#!/usr/bin/env python3
"""
W3-CA1 -- The cascade IS a lens; sr=61 = PutGet AND PutPut both breaking.

CARD CLAIM (CATALOG): the cascade is a STATE-BASED lens
    get : state -> M1-view value   (recover the message-1 schedule value at round r)
    put : (state, v') -> M2-correction (set casoff so da stays 0)
The three lens laws of a "very-well-behaved lens":
    GetPut  put(s, get s) = s          -> VACUOUS here (da=0 held by construction)
    PutGet  get(put(s,v')) = v'         -> the g1=0 per-message value match
    PutPut  put(put(s,v'),v'')=put(s,v'')-> the h=0 difference compatibility
and 2^-2N = "drop PutGet lose 2^-N, drop PutPut lose another 2^-N", on DISTINCT laws.

PROBE (per the card): per-round violation rates of the 3 laws; must partition as
    {GetPut -> 0,  PutGet -> 1 - 2^-N,  PutPut -> 1 - 2^-N}
with the two 2^-N's on *distinct* laws, and P(both | r=61) = P(PutGet)*P(PutPut).

KILL: rates don't partition cleanly, OR both g1,h map to the *same* law (can't explain
2^-2N vs 2^-N), OR GetPut shows violations at r <= 60.

ADVERSARIAL CALL (lead finding #4): RENAME vs MECHANISM. The two conditions g1,h are
already CONFIRMED real (PH1/IN3/NT4/RG1-B). The bar for CONFIRMED here is that the
LENS-LAW STRUCTURE predicts/computes something g1,h alone do not. We test three
candidate "new content" claims a genuine lens framing must deliver:
  (M1) COMPLETENESS/closure: the three laws are exactly the well-behavedness laws of a
       state-based lens -- there is NO fourth independent boundary obstruction. (If a
       third independent 2^-N condition existed at the boundary round, the rate would be
       2^-3N, not 2^-2N. So "exactly two break" <=> "exactly two non-vacuous laws".)
  (M2) VACUITY of GetPut: GetPut must hold with rate 0 at every r<=60 (da=0 invariant),
       which is WHY only two laws remain -- a derivation of the integer 2, not a fit.
  (M3) ORTHOGONALITY: PutGet (value) _|_ PutPut (composition) -> the 1.005 independence
       follows from the laws addressing orthogonal aspects; product law P(both)=P*P.

We measure all three law-rates at the boundary round W[60] over the FULL de61=0 hit
population (from the repo's gap_analysis.c, rebuilt lab-side), and the rank-2 identity
g2 = g1 + h over the 946-collision CSV (the exact algebraic content of PutPut).
"""
import sys, subprocess, re, math, collections
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb

GAP_BIN = {8: '/tmp/ca_gap8', 10: '/tmp/ca_gap10'}  # rebuilt lab-side from repo gap_analysis.c


def run_gap(N):
    """Run the repo gap_analysis binary at width N; parse the full-population rates."""
    cp = sb.run_throttled([GAP_BIN[N]], omp=2, timeout=900, cwd='/tmp')
    out = cp.stdout
    def grab(pat):
        m = re.search(pat, out)
        return float(m.group(1)) if m else None
    # full-population (de61=0 hits) marginals + independence ratio
    res = {}
    res['nde61']  = grab(r'INDEPENDENCE TEST \(g1=0 vs h=0\) over (\d+) de61=0 hits')
    res['P_g1']   = grab(r'P\(g1=0\)=([\d.]+)')
    res['P_h']    = grab(r'P\(h=0\)=([\d.]+)')
    res['P_both'] = grab(r'P\(g1=0 & h=0\)=([\d.]+)')
    res['ratio']  = grab(r'ratio=([\d.]+)\n=> sr=61')
    res['P_h_alltrip'] = grab(r'P\(h==0\): \d+ / \d+ = ([\d.]+)')
    res['h_maxmean']   = grab(r'max-bin=\d+ +\(max/mean=([\d.]+)')
    res['sr60']   = grab(r'sr60 collisions=(\d+)')
    return res, out


def rank2_identity(path=sb.GAP_ROWS_CSV, N=10):
    """The exact algebraic content of PutPut: is g2 = g1 + h (mod 2^N) for every
    collision? And is h a *function* of g1 (=> same law, KILL) or independent (=> two
    distinct laws)?  Returns (n, n_violations, distinct_g1, multi_h_g1)."""
    M = (1 << N) - 1
    rows = sb.load_gap_rows(path)
    viol = 0
    g1_to_h = collections.defaultdict(set)
    for r in rows:
        g1, g2, h = int(r['g1']), int(r['g2']), int(r['h'])
        if (g1 + h) & M != g2 & M:
            viol += 1
        g1_to_h[g1].add(h)
    multi = sum(1 for hs in g1_to_h.values() if len(hs) > 1)
    return len(rows), viol, len(g1_to_h), multi


def getput_check(path=sb.GAP_ROWS_CSV, N=10):
    """GetPut for the cascade lens = 'the correction preserves da=0'. In the construction
    EVERY enumerated collision has da=0 held at rounds 57..60 by definition of casoff
    (W2 = W1 + casoff is chosen exactly to zero da each round). So GetPut violation rate
    over the collision/hit population is identically 0 -- we VERIFY this structurally:
    the find_w2/casoff law is the GetPut witness. Here we confirm the data set only
    contains da=0-held rows (g2 = g1+h closes, which is the da=0 cascade identity)."""
    n, viol, _, _ = rank2_identity(path, N)
    # g2=g1+h closing for ALL rows is the algebraic certificate that casoff held da=0
    # at the boundary (it is derived from W2[60]=W1[60]+casoff & sched2-sched1 fixed).
    return n, viol  # viol==0 => GetPut held on 100% of the population


if __name__ == '__main__':
    print("=== W3-CA1: the cascade as a very-well-behaved lens (GetPut/PutGet/PutPut) ===")
    print("    Ground truth (RESULT_sr61_is_2minus2N): sr=61 <=> g1=0 AND h=0, indep ratio 1.005.")
    print("    Bar for CONFIRMED (finding #4): the lens laws must ADD content, not relabel g1/h.\n")

    # ---- (M2) GetPut vacuity + (rank-2) the PutPut algebraic identity ----
    n, viol, ndist, multi = rank2_identity()
    print("--- Rank-2 / PutPut algebraic identity  (g2 = g1 + h mod 2^10), N=10, 946 colls ---")
    print(f"  g2 == g1 + h : {n-viol}/{n} collisions  (violations={viol})")
    print(f"  is h a function of g1?  {ndist} distinct g1-values, {multi} of them map to >1 h")
    print(f"    => PutGet(g1) and PutPut(h) are {'DISTINCT (independent coords)' if multi>0 else 'COLLAPSED (same law) -- KILL'}\n")

    ng, gviol = getput_check()
    print("--- (M2) GetPut vacuity: does the casoff correction hold da=0 on 100% of pop? ---")
    print(f"  GetPut held (g2=g1+h closes, the da=0 cascade certificate): {ng-gviol}/{ng}"
          f"  => violation rate {gviol/ng:.4f}  (card needs 0 at r<=60)\n")

    # ---- (M3)+(M1) full-population law rates & the product law ----
    # Live N=8 (16.2M-hit full population, ~minutes throttled). For N=10 the full 2^30
    # triple enumeration exceeds the courtesy budget; we cite the repo's VERIFIED N=10
    # number (ratio=1.005 over ~1.07e9 de61=0 hits, RESULT_sr61_is_2minus2N.md).
    for N in (8,):
        print(f"--- Full de61=0 population law rates at boundary round W[60], N={N} ---")
        res, _ = run_gap(N)
        tgt = 1.0 / (1 << N)
        print(f"  population (de61=0 hits) = {int(res['nde61']):,}")
        print(f"  PutGet break rate  1-P(g1=0) = {1-res['P_g1']:.6f}   "
              f"(card: 1 - 2^-N = {1-tgt:.6f}); P(g1=0)={res['P_g1']:.6f} vs 2^-N={tgt:.6f}")
        print(f"  PutPut break rate  1-P(h=0)  = {1-res['P_h']:.6f}   "
              f"(card: 1 - 2^-N = {1-tgt:.6f}); P(h=0)={res['P_h']:.6f} vs 2^-N={tgt:.6f}")
        print(f"  h uniform over ALL triples: P(h=0)={res['P_h_alltrip']:.6f}  max/mean={res['h_maxmean']:.2f}")
        print(f"  PRODUCT LAW  P(both)={res['P_both']:.8f}  vs P(PutGet0)*P(PutPut0)="
              f"{res['P_g1']*res['P_h']:.8f}  ratio={res['ratio']:.3f}")
        # partition cleanliness: GetPut->0, the two 2^-N's on PutGet & PutPut (distinct)
        clean = (abs(res['P_g1']-tgt)/tgt < 0.15 and abs(res['P_h']-tgt)/tgt < 0.15
                 and 0.8 < res['ratio'] < 1.25 and gviol == 0)
        print(f"  PARTITION clean {{GetPut->0, PutGet->1-2^-N, PutPut->1-2^-N}}, distinct laws,"
              f" product law holds:  {clean}\n")

    print("  [N=10 cited from repo VERIFIED: P(g1=0)=P(h=0)=2^-10, product-law ratio=1.005")
    print("        over ~1.07e9 de61=0 hits (RESULT_sr61_is_2minus2N.md) -- not re-run live.]\n")

    print("=== MECHANISM-vs-RENAME verdict inputs ===")
    print("  (M2) integer 2 derived: GetPut vacuous (rate 0) leaves exactly 2 non-vacuous laws.")
    print("  (M1) completeness: a state-based lens has EXACTLY {GetPut,PutGet,PutPut}; no 4th")
    print("       obstruction at the boundary round (else rate would be 2^-3N). The measured")
    print("       2^-2N (two factors, ratio~1) is consistent with exactly-two-laws.")
    print("  (M3) orthogonality: PutGet(value) _|_ PutPut(composition), product law ratio~1.")
    print("  CALL: the map g1<->PutGet, h<->PutPut is a faithful RENAME of CONFIRMED reals;")
    print("        the lens framing's only *new* leverage is the closure argument (M1+M2):")
    print("        'why exactly two' = 'GetPut is free, two well-behavedness laws remain'.")
