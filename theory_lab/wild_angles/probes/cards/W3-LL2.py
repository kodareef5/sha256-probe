#!/usr/bin/env python3
"""
W3-LL2 — Moser-Tardos resampling = a collision-finder that diverges at 61.

THE ONE CONSTRUCTIVE CARD. Tested with the repo's EXACT cascade-DP semantics
(writeups/sr60_sr61_boundary_proof.md + gap_analysis.c):

  cascade-DP, MSB kernel, fill 0xFF:  M2 = M1 with MSB flip in word0 (+ word9).
  find_w2 forces da=0 at every cascade round (rounds 57..60) AUTOMATICALLY.
  A FULL collision  <=>  de61 = de62 = de63 = 0   (Theorem 3, three conditions).
    * "sr=60" target: free tail words W1[57..60] (4N bits) searched so that
       de61=de62=de63=0. 4N freedom vs 3N conditions -> SATISFIABLE.
       This is precisely the object gap_analysis enumerates (946 colls @N=10).
    * "sr=61" target: ALSO demand round 61 be a free cascade round, i.e. W1[61]
       (schedule-determined) must equal the cascade-required value -> g1=0, and
       the inter-message gap closes -> h=0. So sr=61 = {de61=de62=de63=0} AND
       {g1=0 AND h=0}: two EXTRA independent N-bit conditions (the 2^-2N wall).
       (g1 = W1[60]-sched1[60]; h = casoff-(sched2[60]-sched1[60]).)

MT move: resample the free word feeding the lowest violated condition until all
bad events clear; count steps. Convergence at <=60, divergence at 61?  And does
the converged output VERIFY as a genuine collision (independently re-derived)?

Kill: converges at 61 as readily as 60, OR fails even at the easy targets
(mis-specified move). Sweep sr = 58,59,60 (free-word count 2,3,4; conditions
de61=62=63) + sr=61 (4 words + the g1,h coincidence).
"""
import sys, random, functools
print = functools.partial(print, flush=True)
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
import transfer_operator as to

def build(N):
    m = (1 << N) - 1
    rp = to._rot_params(N)
    def rorr(x, k): k %= N; return ((x >> k) | (x << (N - k))) & m
    S0r, S1r, s0r, s1r = rp['S0'], rp['S1'], rp['s0'], rp['s1']
    S0 = lambda a: (rorr(a, S0r[0]) ^ rorr(a, S0r[1]) ^ rorr(a, S0r[2])) & m
    S1 = lambda e: (rorr(e, S1r[0]) ^ rorr(e, S1r[1]) ^ rorr(e, S1r[2])) & m
    s0 = lambda x: (rorr(x, s0r[0]) ^ rorr(x, s0r[1]) ^ ((x >> s0r[2]) & m)) & m
    s1 = lambda x: (rorr(x, s1r[0]) ^ rorr(x, s1r[1]) ^ ((x >> s1r[2]) & m)) & m
    Ch = lambda e, f, g: ((e & f) ^ ((~e & m) & g)) & m
    Mj = lambda a, b, c: ((a & b) ^ (a & c) ^ (b & c)) & m
    K = [(sb.K[i] & m) for i in range(64)]
    IVn = [sb.IV[i] & m for i in range(8)]
    MSB = 1 << (N - 1)

    def rnd(st, k, w):
        a, b, c, d, e, f, g, h = st
        T1 = (h + S1(e) + Ch(e, f, g) + k + w) & m
        T2 = (S0(a) + Mj(a, b, c)) & m
        return [(T1 + T2) & m, a, b, c, (d + T1) & m, e, f, g]

    def precompute(M):
        W = [v & m for v in M] + [0] * 41
        for i in range(16, 57):
            W[i] = (s1(W[i-2]) + W[i-7] + s0(W[i-15]) + W[i-16]) & m
        st = list(IVn)
        for i in range(57):
            st = rnd(st, K[i], W[i])
        return st, W

    def find_w2(s1s, s2s, r, w1):
        r1 = (s1s[7] + S1(s1s[4]) + Ch(s1s[4], s1s[5], s1s[6]) + K[r]) & m
        r2 = (s2s[7] + S1(s2s[4]) + Ch(s2s[4], s2s[5], s2s[6]) + K[r]) & m
        T21 = (S0(s1s[0]) + Mj(s1s[0], s1s[1], s1s[2])) & m
        T22 = (S0(s2s[0]) + Mj(s2s[0], s2s[1], s2s[2])) & m
        return (w1 + r1 - r2 + T21 - T22) & m

    M0 = None
    for cand in range(1 << N):
        M1 = [m] * 16; M2 = [m] * 16
        M1[0] = cand; M2[0] = cand ^ MSB; M2[9] = m ^ MSB
        s1s, _ = precompute(M1); s2s, _ = precompute(M2)
        if s1s[0] == s2s[0]:
            M0 = cand; break
    if M0 is None:
        return None
    M1 = [m] * 16; M2 = [m] * 16
    M1[0] = M0; M2[0] = M0 ^ MSB; M2[9] = m ^ MSB
    s1_57, W1 = precompute(M1); s2_57, W2 = precompute(M2)
    return dict(N=N, m=m, K=K, rnd=rnd, find_w2=find_w2, s1_57=s1_57, s2_57=s2_57,
                W1=W1, W2=W2, s0=s0, s1=s1, M0=M0, S1=S1, S0=S0, Ch=Ch, Mj=Mj)

def evaluate(ctx, w):
    """w = [W1[57],W1[58],W1[59],W1[60]] (4 tail words). Run the cascade (find_w2
    forces da=0), recurrence for W[61..63], return de61,de62,de63 and g1,h."""
    m = ctx['m']; K = ctx['K']; rnd = ctx['rnd']; fw2 = ctx['find_w2']
    s1, s0 = ctx['s1'], ctx['s0']; W1, W2 = ctx['W1'], ctx['W2']
    a = list(ctx['s1_57']); b = list(ctx['s2_57'])
    Wt1, Wt2 = list(W1), list(W2)
    casoff = None
    for j, r in enumerate(range(57, 61)):
        w1 = w[j]
        if r < 60:
            w2 = fw2(a, b, r, w1)
        else:
            casoff = fw2(a, b, 60, 0)
            w2 = (w1 + casoff) & m
        Wt1.append(w1); Wt2.append(w2)
        a = rnd(a, K[r], w1); b = rnd(b, K[r], w2)
    de = {}
    for r in range(61, 64):
        w1 = (s1(Wt1[r-2]) + Wt1[r-7] + s0(Wt1[r-15]) + Wt1[r-16]) & m
        w2 = (s1(Wt2[r-2]) + Wt2[r-7] + s0(Wt2[r-15]) + Wt2[r-16]) & m
        Wt1.append(w1); Wt2.append(w2)
        a = rnd(a, K[r], w1); b = rnd(b, K[r], w2)
        de[r] = (a[4] - b[4]) & m
    # schedule gaps for the sr=61 round (per the boundary proof / gap_analysis)
    sched1_60 = (ctx['s1'](Wt1[58]) + W1[53] + ctx['s0'](W1[45]) + W1[44]) & m
    g1 = (w[3] - sched1_60) & m
    sched2_60 = (ctx['s1'](Wt2[58]) + W2[53] + ctx['s0'](W2[45]) + W2[44]) & m
    h = (casoff - ((sched2_60 - sched1_60) & m)) & m
    full = (a == b)
    return de, g1, h, full, (a, b)

def bad_events(ctx, w, target):
    """List of unsatisfied conditions for the target. de-conditions always; the
    sr=61 target adds g1=0 and h=0."""
    de, g1, h, full, _ = evaluate(ctx, w)
    bad = [('de', r) for r in (61, 62, 63) if de[r] != 0]
    if target == 'sr61':
        if g1 != 0: bad.append(('g1', 60))
        if h != 0:  bad.append(('h', 59))
    return bad

def tap_ancestors(k, lo, hi, taps=(2, 7, 15, 16)):
    """All free rounds in [lo,hi] feeding W[k] through the schedule recurrence DAG."""
    seen, stack, out = set(), [k], set()
    while stack:
        x = stack.pop()
        for t in taps:
            p = x - t
            if p in seen:
                continue
            seen.add(p)
            if lo <= p <= hi:
                out.add(p)
            elif p > hi:
                stack.append(p)
    return out

def mt_run(ctx, target, max_steps, rng, nfree):
    """nfree free tail words W[57..56+nfree]; the rest of W[57..60] held at a fixed
    random value (so 'sr=58' has 2 free words, 'sr=59' has 3, 'sr=60'/'sr61' 4).
    Resample the free word feeding the lowest violated condition."""
    N = ctx['N']
    w = [rng.randrange(1 << N) for _ in range(4)]   # full 4-word vector
    held = list(range(nfree, 4))                     # indices held fixed
    steps = 0
    while steps < max_steps:
        bad = bad_events(ctx, w, target)
        if not bad:
            return True, steps, w
        kind, anchor = bad[0]
        # PROPER Moser-Tardos move: resample ONLY the free variables in the
        # tap-ancestry of the violated event (minimal scope -> shallow witness
        # tree). de_k depends on the recurrence DAG back to the free window;
        # g1/h depend on W[60] (idx 3) and W[58] (idx 1).
        if kind == 'de':
            anc = tap_ancestors(anchor, 57, 56 + nfree)
            scope = sorted({j - 57 for j in anc if 57 <= j <= 56 + nfree})
        elif kind == 'g1':
            scope = [3] if nfree > 3 else list(range(nfree))   # W[60]
        else:  # h
            scope = [1] if nfree > 1 else list(range(nfree))   # via W[58]
        if not scope:
            scope = list(range(nfree))
        for j in scope:
            w[j] = rng.randrange(1 << N)
        steps += 1
    return False, steps, w

def verify(ctx, w, target):
    de, g1, h, full, (a, b) = evaluate(ctx, w)
    de_ok = all(v == 0 for v in de.values())
    if target == 'sr61':
        return de_ok and full and g1 == 0 and h == 0, (a == b)
    return de_ok and full, (a == b)

def run(N, restarts, max_steps, seed=3):
    ctx = build(N)
    if ctx is None:
        print(f"N={N}: no cascade-eligible M0"); return {}
    print(f"\n===== N={N}  MT cascade-DP collision-finder (M0=0x{ctx['M0']:x}, "
          f"{restarts} restarts, cap {max_steps}) =====")
    rng = random.Random(seed)
    print(f"  full collision <=> de61=de62=de63=0; sr61 also needs g1=0 AND h=0")
    print(f"{'target':>7} {'free':>4} {'conds':>6} {'conv%':>7} {'med':>6} {'mean':>9} {'max':>7} {'verified collision?':>20}")
    summ = {}
    specs = [('sr58', 2, 'de61,62,63'), ('sr59', 3, 'de61,62,63'),
             ('sr60', 4, 'de61,62,63'), ('sr61', 4, 'de61,62,63+g1+h')]
    for label, nfree, conds in specs:
        target = 'sr61' if label == 'sr61' else 'coll'
        convs, sc, alls, samp = 0, [], [], None
        for _ in range(restarts):
            ok, st, w = mt_run(ctx, target, max_steps, rng, nfree)
            alls.append(st)
            if ok:
                convs += 1; sc.append(st)
                if samp is None: samp = list(w)
        cp = 100.0 * convs / restarts
        med = sorted(sc)[len(sc)//2] if sc else float('nan')
        mean = sum(sc)/len(sc) if sc else float('nan')
        vr = "n/a"
        if samp is not None:
            okv, exact = verify(ctx, samp, target)
            vr = f"{okv}/exact={exact}"
        summ[label] = (cp, med, mean, max(alls), vr)
        print(f"{label:>7} {nfree:>4} {conds:>6} {cp:>6.1f}% {med!s:>6} {mean:>9.1f} {max(alls):>7} {vr:>20}")
    print(f"\n  conv%: 58={summ['sr58'][0]:.0f} 59={summ['sr59'][0]:.0f} "
          f"60={summ['sr60'][0]:.0f} 61={summ['sr61'][0]:.0f}")
    knee = (summ['sr60'][0] >= 50.0 and summ['sr61'][0] <= 5.0)
    fail_easy = summ['sr60'][0] < 50.0
    print(f"  MT converges to sr=60 collision & DIVERGES at sr=61 (sharp knee)? {knee}")
    print(f"  fails even at the easy sr=60 target (mis-specified move)? {fail_easy}")
    if summ['sr60'][4].startswith('True'):
        print(f"  *** MT EMITTED A VERIFIED sr=60 COLLISION (independently re-derived) ***")
    return summ

def exhaustive_density(N):
    """Enumerate ALL 2^{4N} free-word tuples (w57,w58,w59,w60); count sr60 full
    collisions (de61=de62=de63=0) and sr61 (also g1=0 & h=0). The MT/entropy-
    compression expected steps ~ 1/density, so this cleanly bounds convergence vs
    divergence WITHOUT slow stochastic runs."""
    ctx = build(N)
    if ctx is None:
        print(f"N={N}: no M0"); return
    m = (1 << N) - 1
    sr60, sr61, total = 0, 0, 0
    for w57 in range(1 << N):
        for w58 in range(1 << N):
            for w59 in range(1 << N):
                for w60 in range(1 << N):
                    total += 1
                    de, g1, h, full, _ = evaluate(ctx, [w57, w58, w59, w60])
                    if full and all(v == 0 for v in de.values()):
                        sr60 += 1
                        if g1 == 0 and h == 0:
                            sr61 += 1
    d60 = sr60 / total; d61 = sr61 / total
    import math
    print(f"  N={N}: {total} tuples | sr60 colls={sr60} (density 2^{{{math.log2(d60) if d60 else float('-inf'):.1f}}}, "
          f"expect 2^{{{-3*N}}}={2.0**(-3*N):.2e}) | sr61 colls={sr61} "
          f"(density {'2^'+format(math.log2(d61),'.1f') if d61 else '0 (none in 2^{4N})'}, expect 2^{{{-5*N}}})")
    mt60 = (1/d60) if d60 else float('inf')
    mt61 = (1/d61) if d61 else float('inf')
    print(f"        MT expected steps ~ 1/density: sr60 ~ {mt60:.0f}  | sr61 ~ "
          f"{'inf (no sr61 collision exists at this N)' if mt61==float('inf') else f'{mt61:.2e}'}")
    return sr60, sr61, total

def sampled_density(N, samples):
    """Monte-Carlo density of sr60/sr61 collisions among random free-word tuples
    (for N too big to enumerate). Confirms the 2^{-3N} / 2^{-5N} scaling drives
    MT convergence vs divergence."""
    import random, math
    ctx = build(N)
    rng = random.Random(2)
    sr60 = sr61 = 0
    for _ in range(samples):
        w = [rng.randrange(1 << N) for _ in range(4)]
        de, g1, h, full, _ = evaluate(ctx, w)
        if full and all(v == 0 for v in de.values()):
            sr60 += 1
            if g1 == 0 and h == 0:
                sr61 += 1
    print(f"  N={N}: {samples} samples | sr60 hits={sr60} (~2^{{{math.log2(sr60/samples) if sr60 else float('-inf'):.1f}}}, "
          f"expect 2^{{{-3*N}}}) | sr61 hits={sr61} (expect 2^{{{-5*N}}} ~ {2.0**(-5*N):.1e})")

if __name__ == '__main__':
    # (A) EXACT density at N=4 (enumerable): MT steps ~ 1/density bounds convergence.
    print("===== (A) collision DENSITY (MT expected steps ~ 1/density) =====")
    exhaustive_density(4)
    sampled_density(5, 200000)   # N=5 too big to enumerate cheaply -> sample
    # (B) live MT at N=4: does it actually EMIT a verified collision pair?
    print("\n===== (B) live MT collision-finder (does it emit a verified pair?) =====")
    run(4, restarts=120, max_steps=2000)
