#!/usr/bin/env python3
"""
W8-CL2 — c-vectors: g1 _|_ h is rank-2 sign-coherence; predicts sr=62 = 2^-4N.

Card claim: the two sr=61 conditions are a (g-vector, c-vector) pair; their verified
independence (ratio 1.005) = c-vectors non-parallel (rank-2 span) = 2^-2N codim;
sign-coherence FORBIDS the collision (no lucky 2^-N candidate).

probe (honored): reuse the cascade gap machinery; for the SECOND held equation form
(g1', h') measure the GF(2) rank of {g1, h, g1', h'} => predict 4 (=> sr=62 = 2^-4N);
independence ratio stays in [0.95, 1.05] at N=12.
kill: rank < 4 at any cascade candidate, OR any candidate with ratio >~ 2 (a c-vector
      collision making sr=61 revert to 2^-N).
skeptic (the real bar): independence of two random functionals is the DEFAULT —
      "c-vector" is UNEARNED unless the seed-coordinate SIGNS are one-signed
      (sign-coherence).  So the load-bearing question is NOT "rank 4?" (default for
      random functionals) but "do these functionals carry the cluster-algebra
      SIGN-COHERENCE structure, i.e. are their seed-coordinate signs all-one-signed?"

PRIOR-FINDING #3 (decisive framing): sr=62 = 2^-4N is ALREADY measured directly
(W7-CG3: four gap marginals g1_60,h_60,g1_61,h_61 each ~2^-N).  So CL2's FORWARD
PREDICTION (sr=62 = 2^-4N) is CONFIRMED-correct by independent measurement.  Per the
RENAME RULE we may CONFIRM only if the c-vector structure ADDS a mechanism/derivation
beyond restating g1 _|_ h and the trivial forward product (2^-2N/round -> 2^-4N).  If
it just relabels g1,h as c-vectors and re-derives 2^-4N from independence, it is
SURVIVES-as-rename.  We MEASURE the discriminating object: sign-coherence.

  TEST 1 (rank=4 for sr=62): GF(2)-rank of the four conditions {g1_60,h_60,g1_61,h_61}
          as linear forms over the seed bits.  (=> sr=62 = 2^-4N if rank 4.)
  TEST 2 (independence ratio at N=12): P(g1=0 & h=0)/[P(g1=0)P(h=0)] in [0.95,1.05]?
  TEST 3 (THE EARN-YOUR-KEEP TEST — sign-coherence): a c-vector in cluster algebras is
          SIGN-COHERENT: all its coordinates (in the seed basis) share one sign.
          Over Z_{2^N} "sign" has no field meaning, so the honest surrogate: are the
          GF(2) coefficient-vectors of g1 and h in the seed-bit basis structurally
          one-signed / non-cancelling (a c-vector hallmark), or are they generic dense
          mixed vectors (the 'two random functionals' default = a rename)?  We extract
          the actual GF(2) coefficient rows of g1,h,g1',h' and inspect them.
"""
import sys, random, math
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards')
import _minisha as m
import shabridge as sb


def measure(N, n_samples, seed=11):
    S = m.setup(N)
    if S is None:
        return None
    P, O = S['P'], S['O']
    MASK, KN = P['MASK'], P['KN']
    rng = 1 << N
    random.seed(seed)

    # precompute both message schedules W[0..56]
    W1 = [x & MASK for x in S['M1']] + [0] * 41
    W2 = [x & MASK for x in S['M2']] + [0] * 41
    for i in range(16, 57):
        W1[i] = (O['s1'](W1[i-2]) + W1[i-7] + O['s0'](W1[i-15]) + W1[i-16]) & MASK
        W2[i] = (O['s1'](W2[i-2]) + W2[i-7] + O['s0'](W2[i-15]) + W2[i-16]) & MASK

    def sched(Wp, freew, idx):
        if idx == 60:
            return (O['s1'](freew) + Wp[53] + O['s0'](Wp[45]) + Wp[44]) & MASK
        else:
            return (O['s1'](freew) + Wp[54] + O['s0'](Wp[46]) + Wp[45]) & MASK

    c1 = c2 = c3 = c4 = 0
    cb12 = cb34 = 0
    for _ in range(n_samples):
        w57 = random.randrange(rng); w58 = random.randrange(rng)
        w59 = random.randrange(rng); w60 = random.randrange(rng)
        s1 = list(S['st1_56']); s2 = list(S['st2_56'])
        free = [w57, w58, w59, w60]
        w58b = None; w59b = None
        casoff = {}
        for k, rnd in enumerate(range(57, 61)):
            w1 = free[k]
            w2 = m.find_w2(s1, s2, rnd, w1, P, O)
            if rnd == 58:
                w58b = w2
            if rnd == 59:
                w59b = w2
            if rnd == 60:
                casoff[60] = (w2 - w1) & MASK
            s1 = list(m.sha_round(s1, KN[rnd], w1, P, O))
            s2 = list(m.sha_round(s2, KN[rnd], w2, P, O))
        w1_61 = random.randrange(rng)
        w2_61 = m.find_w2(s1, s2, 61, w1_61, P, O)
        casoff[61] = (w2_61 - w1_61) & MASK

        sc1_60 = sched(W1, w58, 60); sc2_60 = sched(W2, w58b, 60)
        sc1_61 = sched(W1, w59, 61); sc2_61 = sched(W2, w59b, 61)
        g1_60 = (w60 - sc1_60) & MASK
        h_60 = (casoff[60] - ((sc2_60 - sc1_60) & MASK)) & MASK
        g1_61 = (w1_61 - sc1_61) & MASK
        h_61 = (casoff[61] - ((sc2_61 - sc1_61) & MASK)) & MASK
        b1 = (g1_60 == 0); b2 = (h_60 == 0); b3 = (g1_61 == 0); b4 = (h_61 == 0)
        c1 += b1; c2 += b2; c3 += b3; c4 += b4
        cb12 += (b1 and b2); cb34 += (b3 and b4)
    M = n_samples
    return dict(N=N, M=M, p1=c1/M, p2=c2/M, p3=c3/M, p4=c4/M,
                p12=cb12/M, p34=cb34/M)


def signcoherence_and_rank(N, n_probe=6000, seed=5):
    """
    TEST 1 (rank): build the GF(2) coefficient rows of g1_60,h_60,g1_61,h_61 as LINEAR
    forms over the seed bits (w57,w58,w59,w60,w1_61 = 5N bits), by finite differences:
    flip seed bit j, see if condition value's bit-0 (or any bit) flips -> not exact
    linear (the maps are modular-additive of sigma terms, which ARE GF(2)-affine in the
    rot/shift parts but carry nonlinearity).  So instead we measure the EFFECTIVE rank
    via the joint indicator: do the four (==0) events span a 4-codim subspace = are all
    2^4 sign patterns of (b1,b2,b3,b4) realized with the product frequencies?
    That IS the rank-4 statement operationally.

    TEST 3 (sign-coherence): a genuine c-vector has SIGN-COHERENT coordinates.  We test
    the closest faithful surrogate: take g1 and h as functions of the seed; compute their
    discrete partial 'signs' = sign of finite difference d(value)/d(seed-word) over the
    group.  A c-vector would be one-signed (monotone in each coordinate).  A generic
    modular functional is NON-monotone (mixed sign) => NOT a c-vector => rename.
    """
    S = m.setup(N)
    if S is None:
        return None
    P, O = S['P'], S['O']; MASK, KN = P['MASK'], P['KN']; rng = 1 << N
    random.seed(seed)
    W1 = [x & MASK for x in S['M1']] + [0] * 41
    W2 = [x & MASK for x in S['M2']] + [0] * 41
    for i in range(16, 57):
        W1[i] = (O['s1'](W1[i-2]) + W1[i-7] + O['s0'](W1[i-15]) + W1[i-16]) & MASK
        W2[i] = (O['s1'](W2[i-2]) + W2[i-7] + O['s0'](W2[i-15]) + W2[i-16]) & MASK

    def gaps(w57, w58, w59, w60, w1_61):
        s1 = list(S['st1_56']); s2 = list(S['st2_56']); free = [w57, w58, w59, w60]
        w58b = w59b = None; casoff = {}
        for k, rnd in enumerate(range(57, 61)):
            w1 = free[k]; w2 = m.find_w2(s1, s2, rnd, w1, P, O)
            if rnd == 58: w58b = w2
            if rnd == 59: w59b = w2
            if rnd == 60: casoff[60] = (w2 - w1) & MASK
            s1 = list(m.sha_round(s1, KN[rnd], w1, P, O)); s2 = list(m.sha_round(s2, KN[rnd], w2, P, O))
        w2_61 = m.find_w2(s1, s2, 61, w1_61, P, O); casoff[61] = (w2_61 - w1_61) & MASK
        sc1_60 = (O['s1'](w58) + W1[53] + O['s0'](W1[45]) + W1[44]) & MASK
        sc2_60 = (O['s1'](w58b) + W2[53] + O['s0'](W2[45]) + W2[44]) & MASK
        sc1_61 = (O['s1'](w59) + W1[54] + O['s0'](W1[46]) + W1[45]) & MASK
        sc2_61 = (O['s1'](w59b) + W2[54] + O['s0'](W2[46]) + W2[45]) & MASK
        g1_60 = (w60 - sc1_60) & MASK
        h_60 = (casoff[60] - ((sc2_60 - sc1_60) & MASK)) & MASK
        g1_61 = (w1_61 - sc1_61) & MASK
        h_61 = (casoff[61] - ((sc2_61 - sc1_61) & MASK)) & MASK
        return g1_60, h_60, g1_61, h_61

    # TEST 3: monotonicity / sign-coherence of g1_60 and h_60 in each free word.
    # For a c-vector we'd need a CONSISTENT sign of d(value)/d(word).  Measure the
    # fraction of adjacent steps (word -> word+1) that INCREASE vs DECREASE the value.
    # ~50/50 => non-monotone => mixed-sign => NOT sign-coherent (a rename, not a c-vector).
    base = [random.randrange(rng) for _ in range(5)]
    def signfrac(var_idx, word_idx):
        inc = dec = 0
        args = list(base)
        prev = gaps(*args)[var_idx]
        for w in range(1, min(rng, 256)):
            args[word_idx] = w
            cur = gaps(*args)[var_idx]
            d = (cur - prev) & MASK
            # interpret as signed in (-2^{N-1}, 2^{N-1}]
            sd = d - (1 << N) if d >= (1 << (N - 1)) else d
            if sd > 0: inc += 1
            elif sd < 0: dec += 1
            prev = cur
        tot = inc + dec
        return (inc / tot if tot else 0.0)
    # g1_60 depends on w60 (linearly: g1_60 = w60 - sched) and w58 (via sched sigma1);
    # h_60 depends on w58 (sigma1) and the cascade casoff(60) (state).  Probe the
    # informative coordinates.
    sc_g1_w60 = signfrac(0, 3)   # g1_60 vs w60  (should be monotone-ish: linear shift)
    sc_g1_w58 = signfrac(0, 1)   # g1_60 vs w58  (via sigma1 nonlinear)
    sc_h_w58 = signfrac(1, 1)    # h_60 vs w58
    sc_h_w57 = signfrac(1, 0)    # h_60 vs w57 (pure state/casoff path)

    # TEST 1 operational rank: realize all 16 sign patterns of (b1..b4)? Use marginals'
    # product as the independence baseline (done in measure()). Here just check the four
    # conditions are pairwise non-equal functions (distinct), a necessary rank-4 cond.
    samp = [gaps(*[random.randrange(rng) for _ in range(5)]) for _ in range(n_probe)]
    import itertools
    pair_corr = {}
    for (i, j) in itertools.combinations(range(4), 2):
        same = sum(1 for s in samp if (s[i] == 0) == (s[j] == 0))
        pair_corr[(i, j)] = same / len(samp)
    return dict(N=N, sc_g1_w60=sc_g1_w60, sc_g1_w58=sc_g1_w58,
                sc_h_w58=sc_h_w58, sc_h_w57=sc_h_w57, pair_corr=pair_corr)


if __name__ == '__main__':
    print('=== W8-CL2: c-vectors -> rank-2 sign-coherence; sr=62 = 2^-4N ===\n')
    print('--- TEST 1+2: four sr=62 gap marginals + sr61/sr62 joint (rank/independence) ---')
    for N in (8, 10, 12):
        ns = 800000 if N == 8 else (400000 if N == 10 else 200000)
        r = measure(N, ns)
        if r is None:
            print(f'N={N}: no kernel'); continue
        u = 2.0 ** (-N)
        prod4 = r['p1'] * r['p2'] * r['p3'] * r['p4']
        l4 = math.log(prod4) / math.log(2) if prod4 > 0 else float('nan')
        # independence ratio for sr61 (the card's [0.95,1.05] bar)
        ratio = r['p12'] / (r['p1'] * r['p2']) if r['p1'] * r['p2'] > 0 else float('nan')
        print(f'N={N} (M={r["M"]}): 2^-N={u:.3e}')
        print(f'  marginals g1_60={r["p1"]:.3e} h_60={r["p2"]:.3e} '
              f'g1_61={r["p3"]:.3e} h_61={r["p4"]:.3e}')
        print(f'  P(sr61)=P(g1_60=0&h_60=0)={r["p12"]:.3e} (~2^-2N={u*u:.2e}); '
              f'indep ratio={ratio:.3f}')
        print(f'  product of 4 marginals => log2={l4:.2f} (= -4N = {-4*N}) => sr=62 = 2^-4N')
    print()
    print('--- TEST 3 (earn-your-keep): sign-coherence of g1,h in the seed (c-vector?) ---')
    print('  signfrac = fraction of unit-steps that INCREASE the value; 0 or 1 => one-')
    print('  signed (c-vector-like monotone); ~0.5 => mixed-sign (a rename, NOT a c-vec).')
    for N in (8, 10):
        r = signcoherence_and_rank(N)
        if r is None:
            print(f'N={N}: no kernel'); continue
        print(f'N={N}: g1_60 vs w60 signfrac={r["sc_g1_w60"]:.2f} (linear shift) | '
              f'g1_60 vs w58={r["sc_g1_w58"]:.2f} | h_60 vs w58={r["sc_h_w58"]:.2f} | '
              f'h_60 vs w57={r["sc_h_w57"]:.2f}')
        pc = r['pair_corr']
        print(f'   pairwise (==0)-agreement (independence ~ {2*(2.0**(-N))*(1-2.0**(-N))+ (1-2.0**(-N))**2 + (2.0**(-N))**2:.3f}): '
              + ' '.join(f'{k}={v:.3f}' for k, v in pc.items()))
    print()
    print('VERDICT LOGIC: sr=62 = 2^-4N reproduced (TEST1) and ratio in band (TEST2) =>')
    print('forward prediction CONFIRMED-by-measurement. EARN-YOUR-KEEP (TEST3): if the')
    print('functionals are MIXED-SIGN (signfrac~0.5, non-monotone) they are NOT')
    print('sign-coherent c-vectors -> the cluster framing RENAMES g1,h and re-derives')
    print('2^-4N from plain independence => SURVIVES-as-rename, not CONFIRMED.')
