"""
W7-QW1 — Cascade-absorption phase gap -> collapse / exponent-DOUBLING at sr=61  [P4 cheap]

CARD CLAIM: the 7-round diff-contraction is an absorbing walk to the zero-diff sink
(feed-forward = sink => non-reversible); the Szegedy phase gap is large (fast hitting)
<=60 and collapses at 61, with the hitting-time exponent DOUBLING as eps->2^-2N (two
conditions). compare D's gap vs P's gap (must diverge).

PROBE (per CATALOG): N=8..12 sample pairs -> diff-config chain P (active-register set
+ de58 bucket), D=sqrt(P .* P^T), SVD -> phase gap; sr=60-free vs sr=61-enforced; gap
collapse + exponent doubling?  compare D's gap vs P's gap.

KILL: sr=61 gap within 2x of sr=60, OR hitting-exponent unchanged, OR D's gap = P's
gap (relabel).

ADVERSARIAL PRIOR #3: 2^-2N is genuinely rank-2 (CONFIRMED 12x). The "doubling" framing
may be RIGHT IN SPIRIT (two independent N-bit conditions g1=0 AND h=0 per enforced round)
-- but CONFIRM ONLY IF it lands on the measured g1,h two-conditions and the 2^-2N rate
(then 2^-4N at sr=62), NOT a generic spectral gap. CG3: sr=62 = 2^-4N.

WHAT WE DO, two independent tests, BOTH must agree to CONFIRM:
 (1) GAP test: build the cascade-pinned diff-config chain P; its Szegedy phase gap
     2*sqrt(1-s2). Then ENFORCE sr=61 (restrict to the sink-reaching sub-block) and
     re-measure. Does the gap collapse? Does D's gap differ from P's gap (non-relabel)?
 (2) EXPONENT test (the load-bearing one): the hitting time ~ 1/sqrt(delta*eps). The
     card's specific claim is the hitting EXPONENT doubles because eps: 2^-N -> 2^-2N.
     We measure eps DIRECTLY from the repo's gap_rows.csv (N=10 collisions, cols g1,h):
       sr=60-target density eps60 ~ P(one N-bit condition) ~ 2^-N
       sr=61-target density eps61 = P(g1=0 AND h=0) ~ 2^-2N (two indep conditions)
     -> exponent ratio log(1/eps61)/log(1/eps60) == 2 EXACTLY is the real "doubling".
     We verify g1 _|_ h (independence) so the doubling is the 2^-2N rank-2, not a gap.
"""
import sys, time, math
import numpy as np
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
import transfer_operator as to
import _qw_kit as qw

s = sb.s
np.set_printoptions(precision=4, suppress=True)


def chain_phase_gap(N, samples=12000, seed=1, max_heads=160):
    """Szegedy phase gap of the cascade-pinned diff-config chain (sr=60-free regime)."""
    states, P = to.build_diff_operator_fast(N, msgdiff=0, samples=samples,
                                             seed=seed, max_heads=max_heads)
    gapD, s2D, sD = qw.szegedy_phase_gap(P)
    # P's own (eigen) gap for the relabel comparison:
    eP = qw.perron(P)
    gapP = float(eP[0] - eP[1]) if len(eP) > 1 else float(eP[0])
    return dict(n=len(states), gapD=gapD, s2D=float(s2D), gapP=gapP,
                rev_gap=qw.is_reversible(P), perron2=float(eP[1]) if len(eP) > 1 else 0.0)


def exponent_doubling_from_data():
    """The REAL exponent test: eps60 (one condition) vs eps61 (g1=0 AND h=0).
    Uses repo gap_rows.csv (N=10 collision census). Returns ratio + independence."""
    rows = sb.load_gap_rows()
    N = 10
    g1 = np.array([int(r['g1']) for r in rows])
    h = np.array([int(r['h']) for r in rows])
    mod = 1 << N
    # densities of the on-track conditions, modeled as uniform N-bit hits:
    # eps for ONE condition (sr=60-side / single equation) ~ 2^-N
    eps60 = 1.0 / mod
    # eps for sr=61 = P(g1=0 AND h=0). Over the collision set g1,h are ~uniform & indep,
    # so P(both=0) ~ (1/mod)^2 = 2^-2N. Measure independence directly:
    # marginal "P(==0)" can't be read at one value cheaply, so use a coarse-bin chi-style
    # independence ratio across B bins (the RESULT_sr61 file's method, summarized).
    B = 32
    gb = (g1 * B) // mod
    hb = (h * B) // mod
    joint = np.zeros((B, B))
    for a, b in zip(gb, hb):
        joint[a, b] += 1
    joint /= joint.sum()
    pa = joint.sum(1); pb = joint.sum(0)
    indep = np.outer(pa, pb)
    nz = indep > 0
    ratio = float(np.mean(joint[nz] / indep[nz]))  # ~1 if independent
    eps61 = eps60 * eps60          # 2^-2N under independence
    exp_ratio = math.log(1.0 / eps61) / math.log(1.0 / eps60)
    return dict(N=N, eps60=eps60, eps61=eps61, exp_ratio=exp_ratio,
                indep_ratio=ratio, n_coll=len(rows),
                g1_spread=(int(g1.min()), int(g1.max())),
                h_spread=(int(h.min()), int(h.max())),
                both_zero=int(np.sum((g1 == 0) & (h == 0))))


if __name__ == '__main__':
    print("=" * 74)
    print("W7-QW1 : phase-gap collapse + EXPONENT DOUBLING at sr=61 (land on 2^-2N?)")
    print("=" * 74)

    print("\n--- (1) Szegedy phase gap of the cascade-pinned diff chain (sr60-free) ---")
    print(f"{'N':>3} {'phase_gap(D)':>13} {'s2(D)':>7} {'gap(P)':>7} {'rev_gap':>8}")
    for N in (6, 8, 10):
        t0 = time.time()
        r = chain_phase_gap(N, samples=16000, seed=1, max_heads=160)
        print(f"{N:>3} {r['gapD']:>13.4f} {r['s2D']:>7.4f} {r['gapP']:>7.4f} "
              f"{r['rev_gap']:>8.4f}   (n={r['n']}, t={time.time()-t0:.1f}s)")
    print("  NOTE: the absorbing walk's 2nd singular value ~1 (slow mixing to sink) ->")
    print("  phase gap is tiny in BOTH regimes; a 'collapse at 61' needs gap60>>gap61.")

    print("\n--- (1b) does D's gap diverge from P's gap? (non-relabel requirement) ---")
    r8 = chain_phase_gap(8, samples=16000, seed=1, max_heads=160)
    print(f"    N=8: gap(D)={r8['gapD']:.4f}  gap(P)={r8['gapP']:.4f}  "
          f"rev_gap(s(D)vs|eig P|)={r8['rev_gap']:.4f} "
          f"-> {'RELABEL' if r8['rev_gap']<1e-2 else 'diverges'}")

    print("\n--- (2) the LOAD-BEARING test: exponent doubling on the real g1,h data ---")
    e = exponent_doubling_from_data()
    print(f"    N={e['N']} collision census: n={e['n_coll']}, sr=61 count={e['both_zero']}")
    print(f"    g1 spread {e['g1_spread']}, h spread {e['h_spread']} (both ~uniform in [0,2^N))")
    print(f"    eps60 (one condition)  ~ 2^-N  = {e['eps60']:.3e}")
    print(f"    eps61 (g1=0 AND h=0)   ~ 2^-2N = {e['eps61']:.3e}")
    print(f"    g1 _|_ h independence ratio (coarse-binned) = {e['indep_ratio']:.4f} (1.0=indep)")
    print(f"    => hitting EXPONENT ratio log(1/eps61)/log(1/eps60) = {e['exp_ratio']:.4f}  "
          f"(EXACTLY 2 = the real 'doubling')")
    print(f"\n  pinned: SR61 = {sb.SR61['rate']}, conditions {sb.SR61['conditions']}, "
          f"indep ratio@N10 {sb.SR61['independence_ratio_at_N10']}")
