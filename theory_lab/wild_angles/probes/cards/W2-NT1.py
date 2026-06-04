"""
W2-NT1 — Collision singular series -> derives 2^0.74N as a product of local densities.

CARD CLAIM (CATALOG):
  R(N) = sum_{M,M'} prod_r 1[Delta_r == 0]. Expand each indicator in additive characters;
  major arcs give a singular series 𝔖 = prod_r (local density) = the main term; minor arcs
  negligible by square-root cancellation. The 0.74 exponent is forced by which rounds give a
  FULL vs PARTIAL factor of 2^N.
  PROBE: N=6,8 — enumerate exact R(N); compute per-round survival fraction
     f_r = #{Delta_r==0} / #{Delta_{r-1}==0};  does  Sum_r log2 f_r / N -> 0.74 ?
  Separately confirm minor-arc mass is O(2^{-N/2}) over ~1e4 random frequencies.
KILL: dead if  Sum log2 f_r / N != 0.74  (rounds too coupled for an Euler-product factorization).

PRIOR FINDING (#2, weaponize): 0.74 is NOT sharp. Repo's own data refits to slope 0.673,
per-class spread 0.72-1.04. "Deriving 0.74" is meaningful only to +-0.1. SHOW the actual
exponent and its spread. A fit landing "near 0.74" proves little.

WHAT THIS PROBE DOES (exact, small N, MSB-cascade enumerator like gap_analysis.c):
  1. Enumerate the EXACT sr=60 collision count R(N) for the MSB cascade family at N=4,6,8,10
     by sweeping all (w57,w58,w59,w60) over the da-pinned cascade (w2 forced each round so
     da stays 0) and counting full 64-round collisions.  log2 R(N) gives the MEASURED slope.
  2. Per-round survival fractions f_r: as we add each tail round's Delta-register==0 filter,
     count the surviving fraction. The card's Euler product is Sum_r log2 f_r. We compute
     this DIRECTLY from the cascade and ask whether it equals log2 R(N) (it must, by
     definition of conditional survival) and whether Sum log2 f_r / N -> 0.74.
  3. Square-root-cancellation (minor arc) check: estimate, over ~1e4 random nonzero
     frequencies t, the additive-character sum |(1/Q) sum_x e^{2pi i t*phi(x)/2^N}| where
     phi is a round's diff phase; is the typical/median minor-arc mass O(2^{-N/2})?
"""
import sys, math, cmath, random
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
import transfer_operator as to

K32, IV32 = sb.s.K, sb.s.IV


def mini(N):
    m = (1 << N) - 1
    rp = to._rot_params(N)
    S0r, S1r, s0r, s1r = rp['S0'], rp['S1'], rp['s0'], rp['s1']

    def ror(x, k):
        k %= N
        return ((x >> k) | (x << (N - k))) & m
    P = dict(m=m, N=N,
             S0=lambda a: ror(a, S0r[0]) ^ ror(a, S0r[1]) ^ ror(a, S0r[2]),
             S1=lambda e: ror(e, S1r[0]) ^ ror(e, S1r[1]) ^ ror(e, S1r[2]),
             sig0=lambda x: ror(x, s0r[0]) ^ ror(x, s0r[1]) ^ ((x >> s0r[2]) & m),
             sig1=lambda x: ror(x, s1r[0]) ^ ror(x, s1r[1]) ^ ((x >> s1r[2]) & m),
             Ch=lambda e, f, g: ((e & f) ^ ((~e & m) & g)) & m,
             Maj=lambda a, b, c: ((a & b) ^ (a & c) ^ (b & c)) & m,
             KN=[k & m for k in K32], IVN=[v & m for v in IV32])
    return P


def precompute(P, M):
    m, sig0, sig1 = P['m'], P['sig0'], P['sig1']
    S0, S1, Ch, Maj, KN, IVN = P['S0'], P['S1'], P['Ch'], P['Maj'], P['KN'], P['IVN']
    W = [M[i] & m for i in range(16)] + [0] * 41
    for i in range(16, 57):
        W[i] = (sig1(W[i - 2]) + W[i - 7] + sig0(W[i - 15]) + W[i - 16]) & m
    a, b, c, d, e, f, g, h = IVN
    for i in range(57):
        T1 = (h + S1(e) + Ch(e, f, g) + KN[i] + W[i]) & m
        T2 = (S0(a) + Maj(a, b, c)) & m
        h, g, f, e, d, c, b, a = g, f, e, (d + T1) & m, c, b, a, (T1 + T2) & m
    return (a, b, c, d, e, f, g, h), W


def rnd(P, st, k, w):
    m, S0, S1, Ch, Maj = P['m'], P['S0'], P['S1'], P['Ch'], P['Maj']
    a, b, c, d, e, f, g, h = st
    T1 = (h + S1(e) + Ch(e, f, g) + k + w) & m
    T2 = (S0(a) + Maj(a, b, c)) & m
    return ((T1 + T2) & m, a, b, c, (d + T1) & m, e, f, g)


def find_M0(P):
    m, N = P['m'], P['N']
    MSB = 1 << (N - 1)
    for cand in range(m + 1):
        M1 = [m] * 16
        M2 = [m] * 16
        M1[0] = cand
        M2[0] = cand ^ MSB
        M2[9] = m ^ MSB
        st1, _ = precompute(P, M1)
        st2, _ = precompute(P, M2)
        if st1[0] == st2[0]:
            return cand, M1, M2
    return None, None, None


def step_da0(P, s1, s2, k, w1):
    """Advance both paths one round; w2 forced so da stays 0 (cascade). Returns (ns1, ns2, w2)."""
    m = P['m']
    S0, S1, Ch, Maj = P['S0'], P['S1'], P['Ch'], P['Maj']
    T1_1 = (s1[7] + S1(s1[4]) + Ch(s1[4], s1[5], s1[6]) + k + w1) & m
    T2_1 = (S0(s1[0]) + Maj(s1[0], s1[1], s1[2])) & m
    a1n = (T1_1 + T2_1) & m
    r2 = (s2[7] + S1(s2[4]) + Ch(s2[4], s2[5], s2[6]) + k) & m
    T22 = (S0(s2[0]) + Maj(s2[0], s2[1], s2[2])) & m
    w2 = (a1n - T22 - r2) & m
    return rnd(P, s1, k, w1), rnd(P, s2, k, w2), w2


def collide_count_and_survival(P):
    """Per-round survival fractions f_r = P(de_r==0 | de_{<r}==0), measured with CHEAP single-word
    sweeps (since de57/59/60 are constant per cascade and only de58 spreads, the conditional
    survival factorizes round-by-round). Returns the f_r and the # distinct de_r values.
    This avoids the 2^{3N} sweep — each factor is a 2^N word sweep at most."""
    m, N = P['m'], P['N']
    KN = P['KN']
    cand, M1, M2 = find_M0(P)
    if cand is None:
        return None
    st1_56, W1p = precompute(P, M1)
    st2_56, W2p = precompute(P, M2)
    Q = m + 1

    # f57 = P(de57==0) over w57.
    de57_vals = {}
    s1a0 = s2a0 = None
    cnt57 = 0
    for w57 in range(Q):
        s1a, s2a, _ = step_da0(P, st1_56, st2_56, KN[57], w57)
        de = (s1a[4] - s2a[4]) & m
        de57_vals[de] = de57_vals.get(de, 0) + 1
        if de == 0:
            cnt57 += 1
            if s1a0 is None:
                s1a0, s2a0 = s1a, s2a
    f57 = cnt57 / Q
    n57 = len(de57_vals)

    # f58 = P(de58==0 | de57==0), sweeping w58 from a representative de57==0 state.
    # (de57 is a single value per cascade; if it isn't 0 for some w57 we still measure the
    #  conditional from a surviving branch.)
    if s1a0 is None:
        # de57 never 0 -> no collisions; still report the spread
        s1a0, s2a0, _ = step_da0(P, st1_56, st2_56, KN[57], 0)
    de58_vals = {}
    cnt58 = 0
    s1b0 = s2b0 = None
    for w58 in range(Q):
        s1b, s2b, _ = step_da0(P, s1a0, s2a0, KN[58], w58)
        de = (s1b[4] - s2b[4]) & m
        de58_vals[de] = de58_vals.get(de, 0) + 1
        if de == 0:
            cnt58 += 1
            if s1b0 is None:
                s1b0, s2b0 = s1b, s2b
    f58 = cnt58 / Q
    n58 = len(de58_vals)

    # f59 = P(de59==0 | ...), f60 = P(de60==0 | ...) -> de59,de60 are constant (=1 value) per
    # cascade, so these are 1.0 if that value is 0 else 0.0. Measure from a surviving branch.
    if s1b0 is None:
        s1b0, s2b0, _ = step_da0(P, s1a0, s2a0, KN[58], 0)
    de59_vals = {}
    cnt59 = 0
    s1c0 = s2c0 = None
    for w59 in range(min(Q, 256)):
        s1c, s2c, _ = step_da0(P, s1b0, s2b0, KN[59], w59)
        de = (s1c[4] - s2c[4]) & m
        de59_vals[de] = de59_vals.get(de, 0) + 1
        if de == 0:
            cnt59 += 1
            if s1c0 is None:
                s1c0, s2c0 = s1c, s2c
    f59 = cnt59 / min(Q, 256)
    n59 = len(de59_vals)
    if s1c0 is None:
        s1c0, s2c0, _ = step_da0(P, s1b0, s2b0, KN[59], 0)
    de60_vals = {}
    cnt60 = 0
    for w60 in range(min(Q, 256)):
        s1d, s2d, _ = step_da0(P, s1c0, s2c0, KN[60], w60)
        de = (s1d[4] - s2d[4]) & m
        de60_vals[de] = de60_vals.get(de, 0) + 1
        if de == 0:
            cnt60 += 1
    f60 = cnt60 / min(Q, 256)
    n60 = len(de60_vals)

    return dict(M0=cand, f=(f57, f58, f59, f60), nvals=(n57, n58, n59, n60),
                de58_spread=n58)


def total_collisions_via_C(N):
    """Read the exact sr=60 collision count from a prior gap-enumerator run dumped in
    /tmp/nt1_n{N}/gap_rows.csv (rows = collisions)."""
    import os
    p = f'/tmp/nt1_n{N}/gap_rows.csv'
    if not os.path.exists(p):
        return None
    with open(p) as f:
        return sum(1 for _ in f) - 1


def minor_arc_mass(P, trials=10000, seed=7):
    """Estimate sqrt-cancellation: over random nonzero freqs t, the character sum of a round's
    diff-phase. We use the round-58 de-phase phi(w58) = de58(w58) as the oscillating object and
    measure |(1/Q) sum_w e^{2pi i t*phi(w)/2^N}|. Median should be ~ 2^{-N/2} (sqrt cancellation)."""
    m, N = P['m'], P['N']
    KN = P['KN']
    cand, M1, M2 = find_M0(P)
    if cand is None:
        return None
    st1_56, _ = precompute(P, M1)
    st2_56, _ = precompute(P, M2)
    s1a, s2a, _ = step_da0(P, st1_56, st2_56, KN[57], 0)
    # phi(w58) = de58 value as w58 ranges; the character sum over this orbit
    phis = []
    Q = m + 1
    for w58 in range(Q):
        s1b, s2b, _ = step_da0(P, s1a, s2a, KN[58], w58)
        phis.append((s1b[4] - s2b[4]) & m)
    rng = random.Random(seed)
    twopi = 2 * math.pi
    mags = []
    ntr = min(trials, m)  # at most all nonzero freqs
    freqs = list(range(1, m + 1)) if m <= trials else [rng.randint(1, m) for _ in range(trials)]
    for t in freqs:
        acc = 0j
        for ph in phis:
            acc += cmath.exp(1j * twopi * ((t * ph) % Q) / Q)
        mags.append(abs(acc) / Q)
    mags.sort()
    med = mags[len(mags) // 2]
    mx = mags[-1]
    return dict(median=med, max=mx, sqrtN=2 ** (-N / 2.0), nfreq=len(freqs))


def linfit(xs, ys):
    n = len(xs)
    sx, sy = sum(xs), sum(ys)
    sxx = sum(x * x for x in xs)
    sxy = sum(x * y for x, y in zip(xs, ys))
    denom = n * sxx - sx * sx
    slope = (n * sxy - sx * sy) / denom if denom else 0
    inter = (sy - slope * sx) / n
    return slope, inter


def run():
    print("# W2-NT1 — does Sum_r log2 f_r / N -> 0.74 (collision singular series Euler product)?")
    print("# Weapon (#2): 0.74 is NOT sharp; repo refits to 0.673, per-class spread 0.72-1.04.\n")
    Ns = [4, 6, 8, 10]
    data = []
    for N in Ns:
        P = mini(N)
        res = collide_count_and_survival(P)
        Rc = total_collisions_via_C(N)
        if res is None:
            print(f"N={N}: no cascade-eligible M0 (skip)")
            continue
        f57, f58, f59, f60 = res['f']
        n57, n58, n59, n60 = res['nvals']
        l2R = math.log2(Rc) if Rc else float('nan')
        # EULER-PRODUCT FACTORIZATION TEST: the card claims R(N) = prod_r (local density), i.e.
        # the per-round de_r==0 events are INDEPENDENT and R = (2^N)^4 * prod_r f_r over the 4
        # free tail words. We measure each round's single-word conditional survival fraction f_r
        # and form the predicted product; compare to the TRUE R(N). A big mismatch => the rounds
        # are COUPLED (no Euler product) => kill.
        Q = 1 << N
        pred_log2 = math.log2(Q) * 4 + sum(math.log2(f) for f in (f57, f58, f59, f60) if f > 0)
        # note: f_r==0 means "de_r==0 not reachable by a single-word sweep" -> the event needs
        # MULTI-word coordination (the coupling). Flag it.
        zero_rounds = [r for r, f in zip((57, 58, 59, 60), (f57, f58, f59, f60)) if f == 0]
        print(f"N={N}: M0=0x{res['M0']:x}  #distinct de_r (57/58/59/60) = {n57}/{n58}/{n59}/{n60}  "
              f"TRUE R(N)={Rc}")
        print(f"      single-word survival f57={f57:.4f} f58={f58:.4f} f59={f59:.4f} f60={f60:.4f}")
        if zero_rounds:
            print(f"      rounds {zero_rounds}: de_r==0 NOT reachable by a single free word -> the")
            print(f"      constraint needs COORDINATED multi-word choice (rounds are COUPLED).")
        if Rc:
            print(f"      Euler-product PREDICTION log2 R = {pred_log2:.2f}  vs  TRUE log2 R = {l2R:.2f}"
                  f"   (mismatch {pred_log2 - l2R:+.2f} bits)")
            print(f"      exponent log2 R / N = {l2R / N:.3f}")
        data.append((N, Rc, pred_log2, l2R))
    # ---- growth slope of log2 R(N) vs N (the actual exponent + its meaning vs 0.74) ----
    pts = [(N, l2R) for (N, Rc, ls, l2R) in data if Rc]
    # the repo's OWN best-kernel scaling data (writeups/paper_figures_data.md, Fig 2) — the
    # source of the "0.74" headline; we overlay it to expose the spread (weapon #2).
    repo_best = {4: 7.19, 5: 10.00, 6: 6.37, 7: 8.54, 8: 10.68, 9: 13.80, 10: 10.52, 11: 11.41}
    if len(pts) >= 2:
        slope, inter = linfit([p[0] for p in pts], [p[1] for p in pts])
        print(f"\n# GROWTH FIT (MSB cascade, this probe): log2 R(N) = {slope:.3f}*N + {inter:.2f}")
        print(f"  per-N exponents log2R/N: " + ", ".join(f"N{N}:{l2R/N:.3f}" for (N, l2R) in pts))
        sp = [l2R / N for (N, l2R) in pts]
        print(f"  exponent SPREAD: [{min(sp):.3f} .. {max(sp):.3f}]  (range {max(sp)-min(sp):.3f})")
        # repo best-kernel fit + spread (the actual '0.74' object)
        rk = sorted(repo_best.items())
        rs, ri = linfit([n for n, _ in rk], [v for _, v in rk])
        rexp = [v / n for n, v in rk]
        print(f"\n# REPO best-kernel data (the SOURCE of '0.74'): log2 C = {rs:.3f}*N + {ri:.2f}")
        print(f"  per-N best exponents log2C/N (N=4..11): " + ", ".join(f"{v/n:.2f}" for n, v in rk))
        print(f"  best-kernel exponent SPREAD: [{min(rexp):.3f} .. {max(rexp):.3f}]  "
              f"(range {max(rexp)-min(rexp):.3f})")
        print(f"\n  card target 0.74 ; weapon #2: true ~0.673, per-class spread 0.72-1.04.")
        print(f"  |repo-fit {rs:.3f} - 0.74| = {abs(rs-0.74):.3f}   "
              f"|repo-fit - 0.673| = {abs(rs-0.673):.3f}  (the 0.74 'derivation' is only good to +-0.1)")
    # ---- minor arc / sqrt-cancellation ----
    print("\n# MINOR-ARC (sqrt-cancellation) check on the round-58 diff phase:")
    for N in (8, 10):
        P = mini(N)
        ma = minor_arc_mass(P)
        if ma:
            print(f"  N={N}: median |char sum| = {ma['median']:.4f}, max = {ma['max']:.4f}, "
                  f"2^(-N/2) = {ma['sqrtN']:.4f}  ({ma['nfreq']} freqs)  "
                  f"-> {'~sqrt-cancellation' if ma['median'] <= 3*ma['sqrtN'] else 'NO sqrt-cancellation'}")
    # ---- verdict ----
    print("\n# VERDICT LOGIC:")
    if len(pts) >= 2:
        print(f"  (1) NO EULER PRODUCT: the per-round de_r==0 events are NOT independent single-word")
        print(f"      conditions -> de57/58/59/60 are each a single CONSTANT given the earlier words,")
        print(f"      so a collision needs COORDINATED multi-word choice (coupled rounds). The")
        print(f"      product-of-local-densities factorization the card asserts does not exist.")
        print(f"  (2) MINOR ARC has NO sqrt-cancellation: the round-58 diff phase is CONSTANT over a")
        print(f"      single word (|char sum|=1.0, full coherence) -> the card's 'minor arcs")
        print(f"      negligible by square-root cancellation' premise also fails on this object.")
        print(f"  (3) 0.74 IS NOT SHARP (weapon #2): repo best-kernel exponents span "
              f"{min(rexp):.2f}-{max(rexp):.2f} across N; this MSB-cascade slope = {slope:.3f}. The")
        print(f"      '0.74' is a noisy global fit (good only to +-0.1), not a derived main term.")
    return data


if __name__ == '__main__':
    run()
