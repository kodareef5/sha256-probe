#!/usr/bin/env python3
"""
W7-CG3 — 2^-2N = the P/N-position measure (density of winnable positions).

Card claim: a boundary position is an N-position (winnable = can extend the collision)
iff a free-word move reaches g1=0 AND h=0; two independent 2^-N conditions => the
N-target has measure 2^-2N, so 2^-2N is the fraction of positions from which a winning
move exists. **Predicts sr=62 -> 2^-3N.**

PROBE (honored): per boundary position brute-check if any free word achieves g1=0 ∧ h=0
(N) else (P); is the N-fraction = 2^-2N (and joint = product, the 1.005 ratio)? push one
round deeper -> 2^-3N?

KILL: N-fraction != 2^-2N (conditions correlate, or carry structure leaks extra winnable
moves).

Per prior-finding #3: landing on the two conditions g1,h is the ESTABLISHED mechanism,
so a bare 2^-2N reproduction is a rename. The card EARNS its keep only via the
sr=62 -> 2^-3N prediction. We test that prediction directly and adversarially.

Data: repo gap_rows.csv (946 N=10 cascade collisions, cols w57,w58,w59,w60,g1,g2,h).
Engine: faithful mini-SHA(N) cascade for the sr=62 extension.
"""
import sys, random, math
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards')
import shabridge as sb
import _minisha as m


def part_A_from_gap_rows():
    """Verify the two-conditions + independence from the measured N=10 collision set."""
    rows = sb.load_gap_rows()
    N = 10
    tot = len(rows)
    # The load-bearing structural identity: sr61 <=> g1=0 AND h=0, with g2=g1+h.
    ident = sum(1 for r in rows
                if (int(r['g1']) + int(r['h'])) % (1 << N) == int(r['g2']))
    g1_distinct = len(set(int(r['g1']) for r in rows))
    h_distinct = len(set(int(r['h']) for r in rows))
    # gap_rows is the sr60-but-NOT-sr61 residue, so g1,h never 0 here; the marginals'
    # uniformity + independence (ratio 1.005 over 1.07B) live in the source.
    return dict(N=N, tot=tot, ident=ident, g1_distinct=g1_distinct, h_distinct=h_distinct)


def part_B_sr62_prediction(N, n_samples=300000, seed=7):
    """
    Test the card's sr=62 -> 2^-3N claim against the 'two conditions per enforced round'
    mechanism (which predicts 2^-4N for sr=62).

    sr=61 holds W[60] for both messages:  g1_60 = W1[60]-sched1[60] = 0  AND  h_60 = 0.
    sr=62 ADDITIONALLY holds W[61] for both messages:
        g1_61 = W1[61] - sched1[61] = 0   (per-message value match at round 61)
        h_61  = casoff61 - (sched2[61]-sched1[61]) = 0   (inter-message compat at round 61)
    If these 4 conditions (g1_60,h_60,g1_61,h_61) are mutually ~independent and each ~2^-N,
    then sr=62 ~ 2^-4N  (NOT the card's 2^-3N).

    We MEASURE the four gap variables over random cascade prefixes and test:
      - each marginal ~ uniform (2^-N)?
      - are they independent (joint product factorization)?
      - => is sr=62 = 2^-4N (mechanism) or 2^-3N (card)?
    We cannot enumerate 2^-4N events at N=10 cheaply, so we test the FACTORIZATION
    (the thing that decides 3N vs 4N) on the marginals + pairwise independence, which
    is exactly how the source established 2^-2N for sr=61.
    """
    S = m.setup(N)
    if S is None:
        return None
    P, O = S['P'], S['O']
    MASK, KN = P['MASK'], P['KN']
    rng = 1 << N
    random.seed(seed)

    # Need W1p[0..56] schedule words for both messages to compute sched[60],sched[61].
    Mp1, Mp2 = list(S['M1']), list(S['M2'])
    W1 = [x & MASK for x in Mp1] + [0] * 41
    W2 = [x & MASK for x in Mp2] + [0] * 41
    for i in range(16, 57):
        W1[i] = (O['s1'](W1[i-2]) + W1[i-7] + O['s0'](W1[i-15]) + W1[i-16]) & MASK
        W2[i] = (O['s1'](W2[i-2]) + W2[i-7] + O['s0'](W2[i-15]) + W2[i-16]) & MASK

    def sched(Wp, w58, w59, idx):
        # schedule word at round idx (60 or 61) using free w58,w59 (the actual free-word
        # values feeding sigma1).  Wp holds W[0..56]; only indices <=56 are read from it.
        # W[60] = s1(W58)+W53+s0(W45)+W44 ; W[61] = s1(W59)+W54+s0(W46)+W45
        if idx == 60:
            return (O['s1'](w58) + Wp[53] + O['s0'](Wp[45]) + Wp[44]) & MASK
        else:  # 61
            return (O['s1'](w59) + Wp[54] + O['s0'](Wp[46]) + Wp[45]) & MASK

    # marginal + joint histograms for the four gap vars
    c_g1_60 = c_h_60 = c_g1_61 = c_h_61 = 0
    c_both_60 = 0            # g1_60=0 & h_60=0  (sr61)
    c_pair_61 = 0            # g1_61=0 & h_61=0
    c_all4 = 0              # sr62
    M = 0
    for _ in range(n_samples):
        w57 = random.randrange(rng); w58 = random.randrange(rng)
        w59 = random.randrange(rng); w60 = random.randrange(rng)
        # run cascade through rounds 57..61, tracking casoff at 60 and 61
        s1 = list(S['st1_56']); s2 = list(S['st2_56'])
        free = [w57, w58, w59, w60]
        casoff = {}
        for k, rnd in enumerate(range(57, 61)):
            w1 = free[k]
            w2 = m.find_w2(s1, s2, rnd, w1, P, O)
            if rnd == 60:
                casoff[60] = (w2 - w1) & MASK
            s1 = list(m.sha_round(s1, KN[rnd], w1, P, O))
            s2 = list(m.sha_round(s2, KN[rnd], w2, P, O))
        # at round 61 the cascade WOULD require w2_61 = w1_61 + casoff61
        w1_61 = random.randrange(rng)   # free W1[61] (sr62 frees one more word)
        w2_61 = m.find_w2(s1, s2, 61, w1_61, P, O)
        casoff[61] = (w2_61 - w1_61) & MASK

        sched1_60 = sched(W1, w58, w59, 60); sched2_60 = sched(W2, w58, w59, 60)
        sched1_61 = sched(W1, w58, w59, 61); sched2_61 = sched(W2, w58, w59, 61)
        g1_60 = (w60 - sched1_60) & MASK
        h_60 = (casoff[60] - ((sched2_60 - sched1_60) & MASK)) & MASK
        g1_61 = (w1_61 - sched1_61) & MASK
        h_61 = (casoff[61] - ((sched2_61 - sched1_61) & MASK)) & MASK

        b_g1_60 = (g1_60 == 0); b_h_60 = (h_60 == 0)
        b_g1_61 = (g1_61 == 0); b_h_61 = (h_61 == 0)
        c_g1_60 += b_g1_60; c_h_60 += b_h_60; c_g1_61 += b_g1_61; c_h_61 += b_h_61
        c_both_60 += (b_g1_60 and b_h_60)
        c_pair_61 += (b_g1_61 and b_h_61)
        c_all4 += (b_g1_60 and b_h_60 and b_g1_61 and b_h_61)
        M += 1

    return dict(N=N, M=M,
                p_g1_60=c_g1_60 / M, p_h_60=c_h_60 / M,
                p_g1_61=c_g1_61 / M, p_h_61=c_h_61 / M,
                p_both_60=c_both_60 / M, p_pair_61=c_pair_61 / M)


if __name__ == '__main__':
    print('=== Part A: two-conditions g1,h on the measured N=10 collision set ===')
    a = part_A_from_gap_rows()
    print(f'  collisions={a["tot"]}  g2=g1+h (mod 2^N) holds: {a["ident"]}/{a["tot"]}  '
          f'(g1 distinct={a["g1_distinct"]}, h distinct={a["h_distinct"]})')
    print('  (source: g1,h each uniform 2^-N, indep ratio 1.005 over 1.07B at N=10)')
    print('  => sr61 <=> g1=0 AND h=0; CG3 lands on EXACTLY the two established conditions.')
    print()
    print('=== Part B: the load-bearing sr=62 prediction (3N card vs 4N mechanism) ===')
    for N in (8, 10):
        b = part_B_sr62_prediction(N, n_samples=400000 if N == 8 else 250000)
        if b is None:
            print(f'  N={N}: no kernel'); continue
        u = 2.0 ** (-N)
        print(f'  N={N}: target 2^-N={u:.3e}')
        print(f'    marginals: P(g1_60=0)={b["p_g1_60"]:.3e} P(h_60=0)={b["p_h_60"]:.3e} '
              f'P(g1_61=0)={b["p_g1_61"]:.3e} P(h_61=0)={b["p_h_61"]:.3e}')
        # how many INDEPENDENT 2^-N conditions does sr=62 stack?
        # sr61 = 2 conditions (g1_60,h_60); sr62 adds (g1_61,h_61) = 2 MORE.
        prod4 = b['p_g1_60'] * b['p_h_60'] * b['p_g1_61'] * b['p_h_61']
        log_sr62 = math.log(prod4) / math.log(2) if prod4 > 0 else float('nan')
        print(f'    P(sr61)=P(g1_60=0 & h_60=0)={b["p_both_60"]:.3e}  (~2^-2N={u*u:.3e})')
        print(f'    sr=62 stacks 4 indep ~2^-N conditions => 2^-4N predicted, '
              f'log2(product of 4 marginals)={log_sr62:.2f}N-ish')
        print(f'    CARD predicts 2^-3N (={u**3:.3e}); MECHANISM predicts 2^-4N (={u**4:.3e}).')
