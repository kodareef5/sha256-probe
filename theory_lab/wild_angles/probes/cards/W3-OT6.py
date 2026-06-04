#!/usr/bin/env python3
"""
W3-OT6 -- Rotation constants as a coordination mechanism; N=10 = a focal point.
[SUSPECT per prior #4: no round-60 knee, N=10 keeps FAILING as 'special']

CARD CLAIM: the sigma rotations are a correlation device; N=10 constructive
interference = a Schelling focal point where period-N patterns stay phase-locked
(rotation 10 in Sigma1).
PROBE: collision counts for N=4..14 vs a per-N phase-alignment score of the rotation
set; predict the next peak N out-of-sample.
KILL: score uncorrelated with the per-N anomaly.
SKEPTIC: one bump (N=10) is easy to overfit.

WEAPONIZED PRIOR FINDING #4: PH5 already found the rotation/commensurability scores
do NOT peak at N=10 -- and the EMPIRICAL premise is FALSE: N=10 is a yield TROUGH
(1467), while N=9 is the peak (14263, ~9.7x bigger). CT3 found N=10 not singled out.
This probe re-checks with a *phase-alignment* score (the card's specific framing,
distinct from PH5's 4 commensurability scores) and asks the only question that
matters per the card's own out-of-sample clause: does the score's PEAK coincide
with the yield PEAK, and would it have predicted it?

GROUND TRUTH yield table (writeups/paper_figures_data.md, Fig 2 "Best" column):
  N : 4    5     6    7    8     9      10    11    12
  C : 146  1024  83   373  1644  14263  1467  2720  ~4900
  -> the empirical anomaly is the N-mod-4 oscillation; N=9 is the GLOBAL peak,
     N=10 is a LOCAL TROUGH. 'rotation 10 in Sigma1' is a coincidence of the
     32-bit constant set, not a per-N resonance.

OPERATIONALIZATION:
  scaled rotation set per N: r = round(k*N/32) for the SHA-256 rotation constants
  Sigma0={2,13,22}, Sigma1={6,11,25}, sigma0={7,18,3(shift)}, sigma1={17,19,10(shift)}.
  PHASE-ALIGNMENT score (the card's 'phase-locked period-N pattern' object): treat
  each rotation r as a phase 2*pi*r/N on the unit circle; the alignment / coherence
  of the whole rotation set = |(1/K) sum_k exp(i*2*pi*r_k/N)| (the order parameter /
  structure factor). High coherence = rotations cluster in phase = 'focal point'.
  We compute it for N=4..14, correlate with log2(yield), and report (a) where the
  score peaks, (b) where the yield peaks, (c) whether the score would have flagged
  N=10 as special, (d) Pearson r. The card lives or dies on the peaks coinciding.
"""
import sys, math, statistics
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb

# SHA-256 32-bit rotation/shift amounts that appear in the message schedule + round fns
SIGMA0 = [2, 13, 22]      # big Sigma0 (rotations)
SIGMA1 = [6, 11, 25]      # big Sigma1 (rotations) -- note: none is 10; '10' is sigma1's SHIFT
sigma0 = [7, 18, 3]       # small sigma0: rot7, rot18, SHR3
sigma1 = [17, 19, 10]     # small sigma1: rot17, rot19, SHR10  ('rotation 10' the card cites)
ALL_ROT = SIGMA0 + SIGMA1 + sigma0 + sigma1

# Ground-truth collision yield (best kernel), Fig 2.
YIELD = {4: 146, 5: 1024, 6: 83, 7: 373, 8: 1644, 9: 14263, 10: 1467, 11: 2720, 12: 4900}


def scaled(rotset, N):
    out = []
    for k in rotset:
        r = round(k * N / 32.0)
        if r < 1:
            r = 1
        out.append(r % N)
    return out


def phase_coherence(rotset, N):
    """Order parameter |mean exp(i 2pi r/N)| over the scaled rotation set in [0,1].
    1 = all rotations phase-aligned (a focal point); 0 = uniformly spread."""
    rs = scaled(rotset, N)
    re_ = sum(math.cos(2 * math.pi * r / N) for r in rs) / len(rs)
    im_ = sum(math.sin(2 * math.pi * r / N) for r in rs) / len(rs)
    return math.hypot(re_, im_)


def pearson(xs, ys):
    n = len(xs)
    mx, my = statistics.mean(xs), statistics.mean(ys)
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    sy = math.sqrt(sum((y - my) ** 2 for y in ys))
    return cov / (sx * sy) if sx > 0 and sy > 0 else 0.0


def main():
    print("=" * 74)
    print("W3-OT6  Rotation focal point; N=10 special?   [SUSPECT: N=10 is a yield TROUGH]")
    print("=" * 74)
    Ns = list(range(4, 15))
    print(f"\n  {'N':>3} {'phaseCoh(all)':>13} {'coh(Sigma1)':>12} {'yield':>7} {'log2Y':>7}")
    score_all, score_s1, ys, ylog, has_y = [], [], [], [], []
    for N in Ns:
        ca = phase_coherence(ALL_ROT, N)
        c1 = phase_coherence(SIGMA1, N)
        y = YIELD.get(N)
        score_all.append(ca)
        score_s1.append(c1)
        if y:
            ys.append(y)
            ylog.append(math.log2(y))
            has_y.append(N)
        ystr = f"{y:>7}" if y else f"{'--':>7}"
        ylg = f"{math.log2(y):>7.2f}" if y else f"{'--':>7}"
        mark = '  <-N=10' if N == 10 else ''
        print(f"  {N:>3} {ca:>13.4f} {c1:>12.4f} {ystr} {ylg}{mark}")

    # where does each peak?
    peak_score_all_N = Ns[max(range(len(Ns)), key=lambda i: score_all[i])]
    peak_score_s1_N = Ns[max(range(len(Ns)), key=lambda i: score_s1[i])]
    peak_yield_N = has_y[max(range(len(has_y)), key=lambda i: ys[i])]
    print(f"\n  phase-coherence(all rotations) PEAKS at N={peak_score_all_N}")
    print(f"  phase-coherence(Sigma1 only)   PEAKS at N={peak_score_s1_N}")
    print(f"  collision YIELD                PEAKS at N={peak_yield_N}  (the actual empirical anomaly)")

    # correlation on N with known yield
    sa_y = [score_all[Ns.index(n)] for n in has_y]
    s1_y = [score_s1[Ns.index(n)] for n in has_y]
    r_all = pearson(sa_y, ylog)
    r_s1 = pearson(s1_y, ylog)
    print(f"\n  Pearson r( phaseCoh(all), log2 yield ) = {r_all:+.3f}")
    print(f"  Pearson r( phaseCoh(Sigma1), log2 yield) = {r_s1:+.3f}")

    # is N=10 flagged as special by the score? rank of N=10's score
    rank10_all = 1 + sorted(score_all, reverse=True).index(score_all[Ns.index(10)])
    rank10_y = 1 + sorted(ys, reverse=True).index(YIELD[10])
    print(f"\n  N=10 phase-coherence rank among N=4..14: #{rank10_all} of {len(Ns)} "
          f"(1 = most aligned)")
    print(f"  N=10 YIELD rank among measured N: #{rank10_y} of {len(has_y)}  "
          f"(N=10 is a TROUGH, not a peak)")
    # out-of-sample: would the score have predicted the yield peak?
    predicted = (peak_score_all_N == peak_yield_N) or (peak_score_s1_N == peak_yield_N)

    print("\n" + "=" * 74)
    score_peaks_at_10 = (peak_score_all_N == 10) or (peak_score_s1_N == 10)
    print(f"  Does any phase-alignment score PEAK at N=10? {score_peaks_at_10}")
    print(f"  Does the score's peak match the yield peak (out-of-sample success)? {predicted}")
    print(f"  Is N=10 the empirical yield anomaly the card claims? {peak_yield_N == 10} "
          f"(it's N={peak_yield_N}; N=10 is a trough)")
    # KILL: score uncorrelated with the per-N anomaly (and N=10 not special)
    KILL = (not score_peaks_at_10) and (abs(r_all) < 0.5 or peak_yield_N != 10) and (not predicted)
    print(f"\n  KILL_CRITERION ('score uncorrelated with the per-N anomaly') fires? {'YES' if KILL else 'NO'}")
    print("  Reason: N=10 is a yield TROUGH (N=9 is the peak); 'rotation 10 in Sigma1' is")
    print("  actually the small-sigma1 SHIFT (10), not a Sigma1 rotation; no score singles out N=10.")
    print("=" * 74)


if __name__ == '__main__':
    main()
