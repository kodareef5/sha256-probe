#!/usr/bin/env python3
"""
W2-PC3 — Feasible interpolation off the two-block absorber -> proof size from a circuit lower bound.

Card (CATALOG): a short refutation of A(x,z) AND B(y,z) yields (Pudlak) a small circuit C(z)
deciding which side fails. Structure A = "block-1 yields residual with junction signature z",
B = "block-2 absorbs z" (block2_wang frontier), sharing only the junction z (de57/58/59, W58-W59).
A short sr-proof => a small absorbable-z SEPARATOR circuit; but the 128-bit hard core / HW~74
plateau is evidence that separator has NO small circuit -> interpolation converts that into a
refutation-size lower bound.
PROBE: small N -- enumerate the junction interface z (|de58|=2 at N=4, 8 at N=6); label
absorbable/not via the gap algebra; measure the separator's decision-tree depth / DNF size /
sensitivity / monotonicity; does complexity GROW with N?
KILL: dead if the separator has SMALL DT / LOW sensitivity at every N (cheap circuit => short
proof, not a barrier); or if only resolution (not cutting-planes) applies.

FINDING #1 (weaponize): "132 = corank" is a CATEGORY ERROR; the obstruction is the carry
nonlinearity, NOT a basis-independent linear corank. So the separator's hardness, if any, must be
a genuine, growing Boolean-complexity measure -- not a restatement of 132.
FINDING #3: rank-2 / 2^-2N is real -- a separator that decides on the TWO conditions (g1,h) could
legitimately be hard if its complexity provably grows.

------------------------------------------------------------------------------------------------
MODEL (solver-free, the card's own probe), faithful to the gap algebra (gap_analysis.c):
Junction state z = (w57, w58, w59), the cascade-tail triple feeding round 60 (the de57/58/59 +
schedule interface). The block-1 side fixes the cascade base (M0); the block-2 absorber is the
free word choice at round 60. The SEPARATOR is:
    C(z) = 1  iff junction z is ABSORBABLE = there EXISTS a w60 completing an sr>=61 collision.
Per the verified gap algebra: sr=61 at the W[60] level needs g1=0 AND h=0; given a triple z, h is
DETERMINED by z (h = casoff - (sched2-sched1), a function of w58 only via sched and the per-triple
casoff), and g1=0 is achievable by choosing w60 = sched1. So z is absorbable iff h(z)==0 (then the
w60 that zeroes g1 also gives g2=0). Thus C(z) = [h(z) == 0], a Boolean function of the 3N junction
bits. (This is exactly the "absorbable junction" separator; we cross-check its density against
gap_analysis.c's P(h==0).)

We compute, for N=3,4,5, the full truth table of C over all 2^(3N) junctions and measure:
  * density (fraction absorbable) -- cross-check vs 2^-N,
  * average sensitivity  s(C) = avg over z of #neighbours flipping C,
  * max sensitivity      bs proxy,
  * decision-tree depth lower bound via sensitivity (DT >= s_max) and exact DT depth (small N),
  * DNF size (# prime-ish implicants ~ # true points as a crude upper bound; and #minterms),
  * monotonicity (is C monotone in any coordinate? cutting-planes leverage needs structure).
HEADLINE = these GROW with N (separator has no small circuit -> long proofs). KILL = small/flat.
N small (3,4,5). Throttled.
"""
import sys, itertools, math
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
import transfer_operator as to

MASKN = lambda N: (1 << N) - 1

def make_sched(N):
    rp = to._rot_params(N)
    m = MASKN(N)
    def ror(x, k): return to._ror(x, k, N)
    s0r, s1r = rp['s0'], rp['s1']
    sig0 = lambda x: ror(x, s0r[0]) ^ ror(x, s0r[1]) ^ ((x >> s0r[2]) & m)
    sig1 = lambda x: ror(x, s1r[0]) ^ ror(x, s1r[1]) ^ ((x >> s1r[2]) & m)
    return sig0, sig1, m

def separator_truth_table(N, seed=1):
    """C(z) over junction z=(w57,w58,w59), 3N bits. C=1 iff absorbable (h==0).
    h depends on w58 (via sched1/sched2) and casoff. casoff is itself a function of the cascade
    state reached after rounds 57..59, hence of (w57,w58,w59). We compute casoff faithfully via the
    repo's find_w2 relation embedded in the mini-SHA round (the second-message word that keeps the
    paths colliding at round 60). To stay self-contained and cheap we use the gap-algebra closed
    form for h with a fixed (seeded) block-1 schedule tail, matching gap_analysis.c's definition."""
    sig0, sig1, m = make_sched(N)
    import random
    rng = random.Random(seed)
    # fixed block-1 schedule words (the W1p[..]/W2p[..] constants) -- random but fixed per N
    W1p = [rng.randrange(1 << N) for _ in range(57)]
    W2p = [rng.randrange(1 << N) for _ in range(57)]
    # also a per-triple casoff surrogate: casoff is determined by the round-59 state; we model it as
    # the gap-algebra's compatibility term using the two paths' sched offsets at round 60 plus a
    # triple-dependent term. Faithful definition (gap_analysis.c):
    #   sched1_60 = sig1(w58)  + W1p[53] + sig0(W1p[45]) + W1p[44]
    #   sched2_60 = sig1(w58b) + W2p[53] + sig0(W2p[45]) + W2p[44]
    #   h = casoff - (sched2_60 - sched1_60)   mod 2^N
    # casoff = find_w2(state59,...,60,0) depends on the round-59 states of both paths, i.e. on the
    # full triple via the cascade. We compute casoff by running the two cascade paths forward with
    # the mini round (the honest route), using a fixed colliding M0 base.
    rnd = to._make_round(N)
    # find a cascade-eligible M0 (MSB kernel) as gap_analysis.c does
    MSB = 1 << (N - 1)
    M0 = None
    for cand in range(1 << N):
        # build the two block-1 messages, precompute state after 57 rounds, check a-collision
        def pre(msg):
            W = [m] * 16; W[0] = msg
            Wf = list(W) + [0] * (57 - 16)
            for i in range(16, 57):
                Wf[i] = (sig1(Wf[i-2]) + Wf[i-7] + sig0(Wf[i-15]) + Wf[i-16]) & m
            st = tuple(int(x) & m for x in sb.IV[:8])
            for i in range(57):
                st = rnd(st, sb.s.K[i] & m, Wf[i] & m)
            return st, Wf
        s1, W1f = pre(cand)
        s2, W2f = pre((cand ^ MSB))
        # second path also flips W[9]'s MSB (gap_analysis sets M2[9]=MASK^MSB vs M1[9]=MASK)
        if s1[0] == s2[0]:
            M0 = cand; W1p = W1f; W2p = W2f; state1 = s1; state2 = s2; break
    if M0 is None:
        return None  # no cascade base at this N
    def find_w2(s1, s2, rnd_i, w1):
        K = sb.s.K[rnd_i] & m
        def S1(e): r=to._rot_params(N)['S1']; return to._ror(e,r[0],N)^to._ror(e,r[1],N)^to._ror(e,r[2],N)
        def S0(a): r=to._rot_params(N)['S0']; return to._ror(a,r[0],N)^to._ror(a,r[1],N)^to._ror(a,r[2],N)
        def Ch(e,f,g): return ((e&f)^((~e&m)&g))&m
        def Mj(a,b,c): return ((a&b)^(a&c)^(b&c))&m
        r1 = (s1[7] + S1(s1[4]) + Ch(s1[4],s1[5],s1[6]) + K) & m
        r2 = (s2[7] + S1(s2[4]) + Ch(s2[4],s2[5],s2[6]) + K) & m
        T21 = (S0(s1[0]) + Mj(s1[0],s1[1],s1[2])) & m
        T22 = (S0(s2[0]) + Mj(s2[0],s2[1],s2[2])) & m
        return (w1 + r1 - r2 + T21 - T22) & m
    tt = []
    nv = 3 * N
    for z in range(1 << nv):
        w57 = z & m; w58 = (z >> N) & m; w59 = (z >> (2 * N)) & m
        s57a, s57b = list(state1), list(state2)
        w57b = find_w2(s57a, s57b, 57, w57)
        s57a = list(rnd(tuple(s57a), sb.s.K[57] & m, w57)); s57b = list(rnd(tuple(s57b), sb.s.K[57] & m, w57b))
        w58b = find_w2(s57a, s57b, 58, w58)
        s58a = list(rnd(tuple(s57a), sb.s.K[58] & m, w58)); s58b = list(rnd(tuple(s57b), sb.s.K[58] & m, w58b))
        w59b = find_w2(s58a, s58b, 59, w59)
        s59a = list(rnd(tuple(s58a), sb.s.K[59] & m, w59)); s59b = list(rnd(tuple(s58b), sb.s.K[59] & m, w59b))
        casoff = find_w2(s59a, s59b, 60, 0)
        sched1 = (sig1(w58) + W1p[53] + sig0(W1p[45]) + W1p[44]) & m
        sched2 = (sig1(w58b) + W2p[53] + sig0(W2p[45]) + W2p[44]) & m
        h = (casoff - ((sched2 - sched1) & m)) & m
        tt.append(1 if h == 0 else 0)
    return tt, nv

# ---------- Boolean complexity measures ----------
def avg_and_max_sensitivity(tt, nv):
    n = len(tt)
    tot = 0; mx = 0
    for x in range(n):
        s = 0
        for b in range(nv):
            if tt[x] != tt[x ^ (1 << b)]:
                s += 1
        tot += s; mx = max(mx, s)
    return tot / n, mx

def dnf_minterms(tt):
    return sum(tt)

def dt_depth_exact(tt, nv, varset=None):
    """Exact decision-tree depth (min over query orders) — expensive; only for nv<=12.
    Memoized over (subcube). We compute via the standard DP: depth(f restricted) = 0 if constant
    else 1 + min_var max(depth(f|x=0), depth(f|x=1)). Represent f by the tuple of its values over
    the free assignment indices."""
    from functools import lru_cache
    # represent current function as tuple of values over the remaining-free-variable cube
    # to keep it simple and bounded, only call for nv<=9
    if nv > 9:
        return None
    full = tuple(tt)
    import sys as _s
    _s.setrecursionlimit(100000)
    memo = {}
    def depth(values, freevars):
        key = (values, freevars)
        if key in memo:
            return memo[key]
        v0 = values[0]
        if all(v == v0 for v in values):
            memo[key] = 0; return 0
        best = None
        nfv = len(freevars)
        for qi in range(nfv):
            # split values (size 2^nfv) on bit qi of the *local* index
            half = 1 << qi
            lo = []; hi = []
            for idx, val in enumerate(values):
                (hi if (idx & half) else lo).append(val)
            d = 1 + max(depth(tuple(lo), tuple(f for j, f in enumerate(freevars) if j != qi)),
                        depth(tuple(hi), tuple(f for j, f in enumerate(freevars) if j != qi)))
            best = d if best is None else min(best, d)
            if best == 1:
                break
        memo[key] = best; return best
    return depth(full, tuple(range(nv)))

def monotone_in_any(tt, nv):
    """Is C monotone (nondecreasing) in coordinate b for any b? returns set of monotone coords."""
    mono = []
    for b in range(nv):
        ok = True
        for x in range(len(tt)):
            if (x >> b) & 1 == 0:
                if tt[x] > tt[x | (1 << b)]:
                    ok = False; break
        if ok:
            mono.append(b)
    return mono

def run():
    print("=" * 80)
    print("W2-PC3: absorbable-junction SEPARATOR complexity vs N — grows (barrier) or small (KILL)?")
    print("=" * 80)
    rows = []
    for N in (3, 4, 5):
        res = separator_truth_table(N)
        if res is None:
            print(f"  N={N}: no cascade-eligible M0 — skip")
            continue
        tt, nv = res
        dens = sum(tt) / len(tt)
        savg, smax = avg_and_max_sensitivity(tt, nv)
        mt = dnf_minterms(tt)
        dtd = dt_depth_exact(tt, nv)
        mono = monotone_in_any(tt, nv)
        rows.append((N, nv, dens, savg, smax, mt, dtd, len(mono)))
        print(f"\n  N={N}  (junction = 3N = {nv} bits, 2^{nv} = {1<<nv} junctions)")
        print(f"    density (frac absorbable)   = {dens:.4f}   (cross-check 2^-N = {1/(1<<N):.4f})")
        print(f"    avg sensitivity             = {savg:.3f}")
        print(f"    max sensitivity (DT >= this)= {smax}")
        print(f"    exact decision-tree depth   = {dtd}  (out of {nv})")
        print(f"    # absorbable minterms (DNF) = {mt}")
        print(f"    monotone coords             = {len(mono)} of {nv}")
    print("\n  --- scaling across N (does separator complexity GROW?) ---")
    print(f"    {'N':>3} {'nv':>4} {'density':>8} {'avg_sens':>9} {'max_sens':>9} {'DTdepth':>8} {'minterms':>9}")
    for (N, nv, dens, savg, smax, mt, dtd, nmono) in rows:
        print(f"    {N:>3} {nv:>4} {dens:>8.4f} {savg:>9.3f} {smax:>9} {str(dtd):>8} {mt:>9}")
    if len(rows) >= 2:
        # is DT depth ~ full (nv) and rising, or small/flat? is sensitivity bounded?
        dts = [r[6] for r in rows if r[6] is not None]
        smaxes = [r[4] for r in rows]
        print(f"\n  DT depths: {dts}  (full junction width = {[r[1] for r in rows]})")
        print(f"  max-sensitivities: {smaxes}")
        print("  KILL if DT depth small / sensitivity low+flat at every N (cheap separator => short")
        print("  proof, no barrier). HEADLINE if DT depth ~ full width AND sensitivity grows with N.")

if __name__ == '__main__':
    run()
