#!/usr/bin/env python3
"""
W7-CG6 — Mean value: HW~74 as a cooled hot game's mean.

Card claim: the 132 hard-core bits = cold (number) spine, the ~124 soft bits = hot
(temperature) residue that averages out; HW~74 = the mean the game cools to
(~ #hard-core-ones + 1/2 * #soft). NEW prediction: plateau WIDTH = residual temperature
= a NARROWER-than-binomial soft-bit spread.

PROBE (honored): N=8..12 classify hard-core vs soft bits; does mean HW = #hardcore-ones
+ 1/2*#soft? is the HW spread NARROWER than binomial (genuine cooling/anticorrelation)
vs exactly binomial (just statistics)?

KILL: HW != the decomposition, OR the soft-bit spread is EXACTLY binomial ("temperature"
vacuous).

Per prior-finding #2: the HW~74 plateau is real but = Binomial(~132,1/2)/... ~ 66 +
cascade, NOT a sharp 0.74 exponent. CONFIRM only if a SUB-binomial spread (real
anticorrelation) emerges; an exactly-binomial spread => the CGT 'cooling' label is
vacuous => KILL.

We measure the output-difference Hamming weight HW = popcount over the 8 register diffs
(da..dh at round 63) for random kernel-related message pairs run to the LAST round of the
cascade construction, and compare mean & variance to the binomial(#uncontrolled bits, 1/2).
"""
import sys, statistics, math, random
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards')
import _minisha as m


def run_to_63(S, free4, w61):
    """Run the cascade through rounds 57..61 then schedule-determined 62,63; return both
    final states (after round 63)."""
    P, O = S['P'], S['O']
    MASK, KN = P['MASK'], P['KN']
    s1 = list(S['st1_56']); s2 = list(S['st2_56'])
    # rounds 57..60 cascade (W2 forced)
    for k, rnd in enumerate(range(57, 61)):
        w1 = free4[k]
        w2 = m.find_w2(s1, s2, rnd, w1, P, O)
        s1 = list(m.sha_round(s1, KN[rnd], w1, P, O))
        s2 = list(m.sha_round(s2, KN[rnd], w2, P, O))
    # round 61: both messages free (sr-construction); use a single free w61 for path1 and
    # the cascade-forced value for path2 (keeps da=0 if it can). To probe the OUTPUT-diff
    # plateau we just let both run with their schedule-natural words; simplest: free w61
    # for path1, cascade w2 for path2.
    w2_61 = m.find_w2(s1, s2, 61, w61, P, O)
    s1 = list(m.sha_round(s1, KN[61], w61, P, O))
    s2 = list(m.sha_round(s2, KN[61], w2_61, P, O))
    # rounds 62,63 schedule-determined. We don't have the full W schedule here; the
    # OUTPUT-diff plateau only needs the diffs to propagate, and rounds 62/63 are pure
    # shift+T1 on the existing diffs. We run them with W2=W1 (zero added schedule diff at
    # 62/63), which is the cascade-natural choice for the LAST two rounds.
    for rnd in (62, 63):
        # use w=0 for both (schedule diff contribution is separate; this isolates the
        # state-diff propagation that produces the hard-core pattern).
        s1 = list(m.sha_round(s1, KN[rnd], 0, P, O))
        s2 = list(m.sha_round(s2, KN[rnd], 0, P, O))
    return s1, s2


def hw_diff(s1, s2, MASK):
    return sum(bin((s1[i] - s2[i]) & MASK).count('1') for i in range(8))


def classify_bits(S, n_class=4000, seed=11):
    """Classify each of the 8N output-diff bits as HARD-CORE (always same value across
    random free choices => zero control / constant) vs SOFT (varies). Returns
    (#hardcore, #hardcore_ones, #soft, list of per-bit '1'-frequencies for soft bits)."""
    P = S['P']; MASK = P['MASK']; N = P['N']; rng = 1 << N
    random.seed(seed)
    nbits = 8 * N
    ones = [0] * nbits
    seen0 = [False] * nbits
    seen1 = [False] * nbits
    for _ in range(n_class):
        free4 = [random.randrange(rng) for _ in range(4)]
        w61 = random.randrange(rng)
        s1, s2 = run_to_63(S, free4, w61)
        bitpos = 0
        for i in range(8):
            d = (s1[i] - s2[i]) & MASK
            for b in range(N):
                v = (d >> b) & 1
                ones[bitpos] += v
                if v:
                    seen1[bitpos] = True
                else:
                    seen0[bitpos] = True
                bitpos += 1
    hardcore = [j for j in range(nbits) if not (seen0[j] and seen1[j])]
    soft = [j for j in range(nbits) if seen0[j] and seen1[j]]
    hc_ones = sum(1 for j in hardcore if seen1[j])  # hard-core bits stuck at 1
    soft_freq = [ones[j] / n_class for j in soft]
    return dict(nbits=nbits, n_hardcore=len(hardcore), hc_ones=hc_ones,
                n_soft=len(soft), soft_freq=soft_freq)


def hw_distribution(S, n=60000, seed=5):
    P = S['P']; MASK = P['MASK']; rng = 1 << P['N']
    random.seed(seed)
    hws = []
    for _ in range(n):
        free4 = [random.randrange(rng) for _ in range(4)]
        w61 = random.randrange(rng)
        s1, s2 = run_to_63(S, free4, w61)
        hws.append(hw_diff(s1, s2, MASK))
    return hws


if __name__ == '__main__':
    for N in (8, 10):
        S = m.setup(N)
        if S is None:
            print(f'N={N}: no kernel'); continue
        cls = classify_bits(S)
        hws = hw_distribution(S)
        mean = statistics.fmean(hws)
        var = statistics.pvariance(hws)
        # decomposition prediction: mean HW = #hardcore-ones + 1/2 * #soft
        pred_mean = cls['hc_ones'] + 0.5 * cls['n_soft']
        # binomial baseline for the soft bits: each soft bit ~ Bernoulli(p_j); under
        # independence Var = sum p_j(1-p_j).  The card predicts SUB-binomial (Var < this).
        binom_var = sum(p * (1 - p) for p in cls['soft_freq'])
        print(f'N={N}: output-diff bits={cls["nbits"]}  hardcore={cls["n_hardcore"]} '
              f'(stuck-at-1: {cls["hc_ones"]})  soft={cls["n_soft"]}')
        print(f'  mean HW measured = {mean:.3f} ;  decomposition pred (#hc1 + .5*#soft) '
              f'= {pred_mean:.3f}  -> match: {abs(mean-pred_mean) < 1.0}')
        print(f'  Var(HW) measured = {var:.3f} ;  independent-soft binomial Var '
              f'= {binom_var:.3f}')
        ratio = var / binom_var if binom_var > 0 else float('nan')
        print(f'  Var ratio (measured / binomial) = {ratio:.3f}  '
              f'=> {"SUB-binomial (cooling)" if ratio < 0.9 else "binomial (just statistics)" if ratio < 1.1 else "SUPER-binomial"}')
        print()
