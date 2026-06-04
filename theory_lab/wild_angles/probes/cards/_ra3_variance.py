"""W7-RA3 — the LOAD-BEARING new-prediction test (done right, large-sample).

The card's only genuinely NEW prediction over the known two-condition counting is:
  a spike in inter-bucket density VARIANCE (a Szemeredi 'irregular pair' / regularity
  breakdown) at the wall round.

The two-condition CONFIRMATION (exponent doubling, independence ratio ~1) is read
from gap_analysis.c's OWN stdout over the FULL triple space (16M/1B samples) — see
W7-RA3.py / the ground-truth writeup. THIS file measures, over a LARGE sample (not
the 260/946-row CSV which is far too small for a 2^-N density), whether the h=0
condition's density is UNIFORM across buckets (regular pair => var ~ binomial null)
or SPIKES (irregular => var >> null).

h = cas_off60 - (sched2[60] - sched1[60]).  We reuse _w5co_engine.run_tail which
returns cas_off60 and the per-message W_61; and recompute sched*[60] from sigma1(w58)
exactly as gap_analysis.c does:
  sched1[60] = sigma1(w58)  + W1p[53] + sigma0(W1p[45]) + W1p[44]
  sched2[60] = sigma1(w58b) + W2p[53] + sigma0(W2p[45]) + W2p[44]
We bucket by the HIGH bits of w57 and measure inter-bucket density variance of h=0
vs a binomial null at the SAME per-bucket sample sizes. Done at N=8,10 over large
random samples of (w57,w58,w59,w60).
"""
import sys, random, statistics as st
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards')
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import _w5co_engine as E


def compute_h(M, setup, w57, w58, w59, w60):
    """h = cas_off60 - (sched2[60]-sched1[60]) mod 2^N. Reuse run_tail for cas_off60,
    w59b (=> w58b is needed for sched2). Recompute sched*[60] exactly as the C does."""
    MASK = M['MASK']
    W1p, W2p = setup['W1'], setup['W2']
    s1, s2 = setup['st1'], setup['st2']
    KN = M['KN']
    # replay rounds 57,58 to get w58b (path-2 word at round 58)
    w57b = E.find_w2(s1, s2, 57, w57, M)
    s1a = E.sha_round(s1, KN[57], w57, M); s2a = E.sha_round(s2, KN[57], w57b, M)
    w58b = E.find_w2(s1a, s2a, 58, w58, M)
    s1b = E.sha_round(s1a, KN[58], w58, M); s2b = E.sha_round(s2a, KN[58], w58b, M)
    # round 59 cascade, then round 60 cascade offset
    w59b = E.find_w2(s1b, s2b, 59, w59, M)
    s1c = E.sha_round(s1b, KN[59], w59, M); s2c = E.sha_round(s2b, KN[59], w59b, M)
    cas_off60 = E.find_w2(s1c, s2c, 60, 0, M)
    sched1_60 = (M['s1'](w58)  + W1p[53] + M['s0'](W1p[45]) + W1p[44]) & MASK
    sched2_60 = (M['s1'](w58b) + W2p[53] + M['s0'](W2p[45]) + W2p[44]) & MASK
    h = (cas_off60 - (sched2_60 - sched1_60)) & MASK
    return h


def bucketed_variance(N, n_samples, nbuckets=16, seed=1):
    M = E.make_model(N); setup = E.find_M0(M)
    if setup is None:
        return None
    MASK = M['MASK']; rng = random.Random(seed)
    shift = max(0, N - 4)
    cnt = [0] * nbuckets       # h=0 count per bucket
    tot = [0] * nbuckets       # samples per bucket
    for _ in range(n_samples):
        w57 = rng.randint(0, MASK); w58 = rng.randint(0, MASK)
        w59 = rng.randint(0, MASK); w60 = rng.randint(0, MASK)
        b = (w57 >> shift) & (nbuckets - 1)
        h = compute_h(M, setup, w57, w58, w59, w60)
        tot[b] += 1
        if h == 0:
            cnt[b] += 1
    dens = [(cnt[b] / tot[b]) for b in range(nbuckets) if tot[b] > 0]
    sizes = [tot[b] for b in range(nbuckets) if tot[b] > 0]
    if len(dens) < 2:
        return None
    mean_d = st.mean(dens)
    var_d = st.pvariance(dens)
    p = sum(cnt) / sum(tot)
    exp_var = st.mean([p * (1 - p) / nb for nb in sizes]) if p > 0 else 0.0
    return dict(p=p, mean=mean_d, var=var_d, exp_var=exp_var,
                ratio=(var_d / exp_var) if exp_var > 0 else float('nan'),
                total=sum(tot), h0=sum(cnt), nb=len(dens))


if __name__ == '__main__':
    print("W7-RA3 NEW-PREDICTION test: inter-bucket density VARIANCE of the wall")
    print("condition h=0, large-sample, vs binomial null (regular-pair) baseline.\n")
    for N, ns in ((8, 1_500_000), (10, 4_000_000)):
        res = bucketed_variance(N, ns, nbuckets=16, seed=7)
        if res is None:
            print(f"N={N}: skip"); continue
        print(f"N={N}: samples={res['total']:,}  h=0 hits={res['h0']:,}  "
              f"overall P(h=0)={res['p']:.6g} (2^-N={2.0**-N:.6g})")
        print(f"   inter-bucket density: mean={res['mean']:.6g}  VAR={res['var']:.3g}")
        print(f"   binomial-null VAR (regular pair) = {res['exp_var']:.3g}")
        print(f"   VAR / null = {res['ratio']:.3f}   "
              f"=> {'SPIKE (irregular, breakdown)' if res['ratio']>2 else 'NO spike (regular/uniform)'}\n")
    print("Interpretation: P(h=0)~2^-N confirms the condition is the genuine one. If")
    print("VAR/null ~ 1 across N, the wall is a UNIFORM (regular) density drop -> the")
    print("'regularity breakdown / variance spike' prediction is FALSE; the Szemeredi")
    print("framing is then a RENAME of the two-condition counting (finding #3), with no")
    print("new load-bearing object. A VAR/null >> 1 across N would be a genuine new CONFIRM.")
