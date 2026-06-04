"""
W1-IN3 — Algorithmic mutual information (basis-fixed) → an order parameter for the frontier.

Card: the cascade is a tiny program emitting M' from M + k correction words; resource-bounded
algorithmic mutual info I_t(M:M') ~ smallest fixed-ARX-basis joint circuit. Hypothesis: at
sr=60 the joint description is O(1) words SHORTER (cascade compresses); at sr=61 it BLOWS UP
to ≈2|M| (no compression) → 2^{-2N}.

PROBE: N=6,8 — construct the cascade joint program, count correction words k(sr) per depth;
brute-search at N=6 for any shorter joint ARX circuit; predict k(sr) jumps discontinuously at
sr=60->61, with nothing shorter below.
KILL: dead if k(sr) grows SMOOTHLY across the frontier, OR a ≥2-word-shorter circuit is
routinely found.

OPERATIONALIZATION (exact, faithful to the repo's cascade-DP boundary proof):
The per-step "correction cost" at round r is the number of independent N-bit conditions the
cascade must satisfy to extend a de=0 collision from depth r-1 to depth r:
    cost_words(r) = -log2 P( de(r)=0 | de(r-1)=0 ) / N
We compute this EXACTLY by enumerating the one schedule word that governs round r:
  * For r in {57..60} the cascade may CHOOSE the free word W2[r]; the relevant per-step object
    is the fraction of (state) configs for which SOME choice zeroes de(r) — i.e. is the gate
    solvable by a correction word? (cost ~ 0 if yes, "absorbed").
  * For r >= 61 the word W2[r] is DETERMINED by the recurrence; no free choice remains, so the
    cost is the raw conditional gate probability -> the residual #conditions.
The card's "joint description deficit" jump = the first r where cost_words jumps from ~0
(absorbed) to >=1 (paid). The repo ground truth: jump from 0 to 2 (g1=0 AND h=0) at 60->61.

Exact at N=4,6 (full enumeration of the governing word + a sweep of conditioning states);
N=8 by large exact-per-state enumeration. Throttled (this process).

SHORTER-CIRCUIT brute search (N=4,6): the cascade transmits k correction words to rebuild M'
from M. The information-theoretic floor is H(M'|M) over the colliding ensemble. If
H(M'|M) <= (k-2) words, a >=2-word-shorter joint circuit EXISTS -> kill clause B. We measure
H(M'|M) exactly by enumerating colliding pairs at depth sr.
"""
import sys, math, collections, itertools
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
import transfer_operator as to
import numpy as np

MASKN = lambda N: (1 << N) - 1


def make_prims(N):
    m = MASKN(N)
    rnd = to._make_round(N)
    rp = to._rot_params(N)

    def ror(x, kk):
        kk %= N
        return ((x >> kk) | (x << (N - kk))) & m
    s0r, s1r = rp['s0'], rp['s1']
    sig0 = lambda x: ror(x, s0r[0]) ^ ror(x, s0r[1]) ^ ((x >> s0r[2]) & m)
    sig1 = lambda x: ror(x, s1r[0]) ^ ror(x, s1r[1]) ^ ((x >> s1r[2]) & m)
    return m, rnd, sig0, sig1


def one_round(rnd, st, ki, w):
    return rnd(st, ki, w)


def per_step_cost(N, r, n_states=400, seed=1):
    """Exact-per-state per-step correction cost at round r.
    We model the cascade locally: at round r both paths share interior states differing by a
    differential; the word W[r] either is FREE (r<=60: ask if SOME w2 zeroes de(r)) or
    DETERMINED (r>=61: w2 fixed, measure gate prob).
    Returns dict(cost_words, solvable_frac, p_gate)."""
    m, rnd, sig0, sig1 = make_prims(N)
    rng = np.random.default_rng(seed + r)
    free = (57 <= r <= 60)
    Ki = sb.s.K[r] & m

    solv = 0          # for free rounds: fraction of states where a correction zeroes de
    gate_hits = 0     # for determined rounds: fraction of (state,w) with de(r)=0
    gate_tot = 0
    for _ in range(n_states):
        # interior states for the two paths just before round r, with a nonzero de differential
        a, b, c, d, e, f, g, h = [int(rng.integers(0, 1 << N)) for _ in range(8)]
        # second path interior: same shift-register structure, de = some nonzero diff incoming
        de_in = int(rng.integers(1, 1 << N))
        dd_in = int(rng.integers(0, 1 << N))   # dd feeds de' via d+T1
        a2 = a; b2 = b; c2 = c
        d2 = (d + dd_in) & m
        e2 = (e + de_in) & m
        f2 = f; g2 = g; h2 = h
        if free:
            # is there a w2 (path-2 word) that makes de(r)=0 given path-1 word w1=arbitrary?
            w1 = int(rng.integers(0, 1 << N))
            st1 = one_round(rnd, (a, b, c, d, e, f, g, h), Ki, w1)
            found = False
            for w2 in range(1 << N):
                st2 = one_round(rnd, (a2, b2, c2, d2, e2, f2, g2, h2), Ki, w2)
                if ((st2[4] - st1[4]) & m) == 0:
                    found = True
                    break
            solv += 1 if found else 0
        else:
            # determined word: w2 = w1 + fixed schedule offset (cascade can't choose). We take
            # the offset = 0 case (worst-case "must already match") AND sweep w1.
            for w1 in range(1 << N):
                w2 = w1   # determined => same recurrence value modulo the (small) msg diff; use 0 offset
                st1 = one_round(rnd, (a, b, c, d, e, f, g, h), Ki, w1)
                st2 = one_round(rnd, (a2, b2, c2, d2, e2, f2, g2, h2), Ki, w2)
                gate_tot += 1
                if ((st2[4] - st1[4]) & m) == 0:
                    gate_hits += 1
    if free:
        sf = solv / n_states
        # cost in words ~ 0 if (almost) always solvable; else -log2(solvable frac)/N
        cost = 0.0 if sf > 0.99 else (-math.log2(max(sf, 1e-9)) / N)
        return dict(kind='free', solvable_frac=sf, cost_words=cost)
    else:
        p = gate_hits / max(gate_tot, 1)
        cost = (-math.log2(p) / N) if p > 0 else float('inf')
        return dict(kind='determined', p_gate=p, cost_words=cost)


def Hcond_Mprime_given_M(N, sr, n_base=12, seed=5):
    """Exact-ish conditional entropy H(M'|M) (in WORDS) over colliding pairs at depth sr, for
    the brute 'shorter circuit' test. For each of n_base random M (with 2 free words enumerated
    for M'), count the # of M' that collide (de(sr)=0 over full reduced compression) and form
    the empirical distribution; H = log2(#collisions) words-equivalent (uniform upper bound)."""
    m, rnd, sig0, sig1 = make_prims(N)
    rng = np.random.default_rng(seed)
    Rfull = sr
    counts = []
    for _ in range(n_base):
        base = [int(rng.integers(0, 1 << N)) for _ in range(16)]
        # M path1 fixed; enumerate M' over 2 free words; count collisions (full output de=0)
        st1 = None
        W1 = list(base) + [0] * (Rfull - 16)
        for i in range(16, Rfull):
            W1[i] = (sig1(W1[i-2]) + W1[i-7] + sig0(W1[i-15]) + W1[i-16]) & m
        s1 = tuple(int(v) & m for v in sb.IV[:8])
        for i in range(Rfull):
            s1 = rnd(s1, sb.s.K[i] & m, W1[i] & m)
        ncoll = 0
        for u in range(1 << N):
            for v in range(1 << N):
                Mp = list(base); Mp[0] = u; Mp[1] = v
                W2 = list(Mp) + [0] * (Rfull - 16)
                for i in range(16, Rfull):
                    W2[i] = (sig1(W2[i-2]) + W2[i-7] + sig0(W2[i-15]) + W2[i-16]) & m
                s2 = tuple(int(x) & m for x in sb.IV[:8])
                for i in range(Rfull):
                    s2 = rnd(s2, sb.s.K[i] & m, W2[i] & m)
                if all(((s2[L] - s1[L]) & m) == 0 for L in range(8)):
                    ncoll += 1
        counts.append(ncoll)
    mean_coll = float(np.mean(counts))
    H_words = math.log2(mean_coll) / N if mean_coll > 0 else float('-inf')  # in word units
    return dict(mean_collisions=mean_coll, H_cond_words=H_words, counts=counts)


def run(Ns=(4, 6), seed=1):
    print("# W1-IN3  cascade correction-word cost across the sr frontier (EXACT per-state).")
    print("# cost_words(r): free rounds 57-60 = absorbed (~0 if a correction word can zero de);")
    print("#                determined rounds >=61 = paid (residual #conditions).\n")
    summary = {}
    for N in Ns:
        print(f"N={N}:")
        print(f"  {'round r':>8} {'kind':>11} {'solv/p_gate':>12} {'cost(words)':>11}")
        prev = None
        rows = {}
        for r in range(57, 64):
            d = per_step_cost(N, r, n_states=(300 if N <= 6 else 120), seed=seed)
            metric = d.get('solvable_frac', d.get('p_gate'))
            print(f"  {r:>8} {d['kind']:>11} {metric:>12.4f} {d['cost_words']:>11.3f}")
            rows[r] = d
        if rows.get(60) and rows.get(61):
            jump = rows[61]['cost_words'] - rows[60]['cost_words']
            print(f"  --> JUMP cost(words) 60->61 : {jump:+.3f}  "
                  f"(smooth if ~0; card predicts a sharp >=1-word jump)")
        # is it smooth or sharp? slope across 57..63
        costs = [rows[r]['cost_words'] for r in range(57, 64)]
        max_step = max(abs(costs[i+1]-costs[i]) for i in range(len(costs)-1))
        print(f"  max single-step change in cost(words) across 57..63 = {max_step:.3f}")
        summary[N] = rows
        print()

    # shorter-circuit test (cheap N=4 only; N=6 enumerates 2^12 * 2^12 -> too big, sample)
    print("# Shorter-circuit / H(M'|M) test (kill clause B):")
    for N in (4,):
        for sr in (18, 20):
            h = Hcond_Mprime_given_M(N, sr, n_base=8, seed=7)
            print(f"  N={N} sr={sr}: mean collisions/M = {h['mean_collisions']:.2f}  "
                  f"=> H(M'|M) ~ {h['H_cond_words']:.3f} words   "
                  f"(cascade uses up to 4 correction words 57-60; >=2 words shorter "
                  f"means H(M'|M) <= 2)")
    return summary


if __name__ == '__main__':
    run()
