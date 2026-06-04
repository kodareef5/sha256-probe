"""
W2-NT3 — Weyl equidistribution of {sigma1(W)/2^N} -> why de58 grows, others constant.

CARD CLAIM (CATALOG):
  Each de_r is a Weyl sum of the schedule orbit; "constant size" = equidistributing
  (discrepancy -> 0), "growing" = non-equidistributing/lacunary. SHR10 is the textbook
  multiply-by-2^{-10}-then-truncate (lacunary {2^k theta}) whose Weyl sum doesn't cancel
  -> ITS difference set (de58) grows with N. The probe: per round compute the
  star-discrepancy of {W_t/2^N} and |de_r|; the WORST-equidistributed round must be the
  unique growing de58, with matching slope; de57/59/60 must equidistribute.

KILL: dead if de58 isn't the worst-equidistributed round, OR its discrepancy slope misses
the measured |de58| slope by >20%.

GROUND TRUTH WEAPON (#4): de57=de59=de60=1 ALWAYS; de58 = 2**hw(db56) (exact N<=14).
The OPEN question the card must answer is the GROWTH LAW (predict 2**hw(db56)), not the
constancy of the others. The repo's actual mechanism is the Maj-image at round 58
propagating the b-register XOR difference db56 -> 2**hw(db56) distinct de58 values
(a CARRY/AND nonlinearity), NOT a sigma1 schedule equidistribution.

WHAT THIS PROBE DOES (exact, small N):
  1. Reconstruct the cascade exactly at width N (scaled-rotation mini-SHA, MSB kernel,
     auto-M0, fill=all-ones, like gap_analysis.c). Compute |de57|,|de58|,|de59|,|de60| by
     enumerating the e-register diff over all message-word freedoms that keep da57=0.
     Confirm de58 = 2**hw(db56) and the others = 1.
  2. The card's SCHEDULE-discrepancy mechanism: round r's de comes from schedule word
     position p(r) and the cascade; the card pins SHR10 (sigma1) as the lacunary culprit.
     For each de_r we ask: is the controlling object a sigma1 (SHR10) term or the round-58
     Maj on db56?  We directly measure (a) the star-discrepancy of the sigma1-fractional-
     part orbit {sigma1(W_t)/2^N} per schedule position, and (b) whether |de58| tracks
     hw(db56) (the Maj law) vs whether it tracks the sigma1 discrepancy.
  3. DECISIVE: the card predicts |de_r| is monotone in (1 / equidistribution) of the
     sigma1 orbit at round r. We test the slope:  does the sigma1-discrepancy of the de58
     round predict log2|de58| within 20%? And is de58's round the WORST-equidistributed?
"""
import sys, math
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
import transfer_operator as to

K32 = sb.s.K
IV32 = sb.s.IV


def mini(N):
    """Return scaled-rotation mini-SHA primitives at width N (matches gap_analysis.c)."""
    m = (1 << N) - 1
    rp = to._rot_params(N)
    S0r, S1r, s0r, s1r = rp['S0'], rp['S1'], rp['s0'], rp['s1']

    def ror(x, k):
        k %= N
        return ((x >> k) | (x << (N - k))) & m
    S0 = lambda a: ror(a, S0r[0]) ^ ror(a, S0r[1]) ^ ror(a, S0r[2])
    S1 = lambda e: ror(e, S1r[0]) ^ ror(e, S1r[1]) ^ ror(e, S1r[2])
    sig0 = lambda x: ror(x, s0r[0]) ^ ror(x, s0r[1]) ^ ((x >> s0r[2]) & m)
    sig1 = lambda x: ror(x, s1r[0]) ^ ror(x, s1r[1]) ^ ((x >> s1r[2]) & m)
    Ch = lambda e, f, g: ((e & f) ^ ((~e & m) & g)) & m
    Maj = lambda a, b, c: ((a & b) ^ (a & c) ^ (b & c)) & m
    KN = [k & m for k in K32]
    IVN = [v & m for v in IV32]
    return dict(m=m, S0=S0, S1=S1, sig0=sig0, sig1=sig1, Ch=Ch, Maj=Maj, KN=KN, IVN=IVN, N=N)


def precompute(P, M):
    """Run 57 rounds; return (state_after_56, W[0..56])."""
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
    """Find cascade-eligible M0 like gap_analysis.c: M2=M1^MSB in word0, M2[9]=mask^MSB."""
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


def de_sizes(P):
    """Enumerate the de57..de60 difference SETS exactly by sweeping the free tail words
    (w57,w58,w59) over the cascade, with each path's W matched so da stays 0.
    Returns dict {57:|de57|, 58:|de58|, 59:|de59|, 60:|de60|}, and db56."""
    m, N = P['m'], P['N']
    KN = P['KN']
    cand, M1, M2 = find_M0(P)
    if cand is None:
        return None, None
    st1_56, W1p = precompute(P, M1)
    st2_56, W2p = precompute(P, M2)
    # b-register diff at round 56 (XOR) -> the law says |de58| = 2**hw(db56).
    db56 = (st1_56[1] ^ st2_56[1])

    # cascade-matched tail: for each round r in 57.., choose w1 freely; w2 is forced so da
    # stays 0 (same find_w2 trick as gap_analysis.c).
    def find_w2(s1, s2, k):
        S1, Ch, S0, Maj = P['S1'], P['Ch'], P['S0'], P['Maj']
        r1 = (s1[7] + S1(s1[4]) + Ch(s1[4], s1[5], s1[6]) + k) & m
        r2 = (s2[7] + S1(s2[4]) + Ch(s2[4], s2[5], s2[6]) + k) & m
        T21 = (S0(s1[0]) + Maj(s1[0], s1[1], s1[2])) & m
        T22 = (S0(s2[0]) + Maj(s2[0], s2[1], s2[2])) & m
        return None, r1, r2, T21, T22  # placeholder; w2 computed below

    # de_r = e1 - e2 (modular) after round r, swept over free words.
    # de57: sweep w57.   de58: sweep (w57,w58).   etc.  But the e-diff after a round only
    # depends on the registers; we collect the SET of de_r values.
    de = {57: set(), 58: set(), 59: set(), 60: set()}
    # cap the sweep so it stays cheap: full sweep when (mask+1)**depth small, else sample-free.
    def step(s1, s2, k, w1):
        # forced w2 so that da stays 0: a1_next == a2_next
        S1, Ch, S0, Maj = P['S1'], P['Ch'], P['S0'], P['Maj']
        T1_1 = (s1[7] + S1(s1[4]) + Ch(s1[4], s1[5], s1[6]) + k + w1) & m
        T2_1 = (S0(s1[0]) + Maj(s1[0], s1[1], s1[2])) & m
        a1n = (T1_1 + T2_1) & m
        # solve w2 from a2n == a1n
        r2 = (s2[7] + S1(s2[4]) + Ch(s2[4], s2[5], s2[6]) + k) & m
        T22 = (S0(s2[0]) + Maj(s2[0], s2[1], s2[2])) & m
        w2 = (a1n - T22 - r2) & m
        ns1 = rnd(P, s1, k, w1)
        ns2 = rnd(P, s2, k, w2)
        return ns1, ns2

    full = (m + 1) <= 4096
    rng = range(m + 1) if full else range(0, m + 1, max(1, (m + 1) // 4096))
    for w57 in (range(m + 1) if (m + 1) <= 65536 else rng):
        s1a, s2a = step(st1_56, st2_56, KN[57], w57)
        de[57].add((s1a[4] - s2a[4]) & m)
        # de58: sweep w58 too (cap)
        for w58 in (range(m + 1) if (m + 1) <= 2048 else range(0, m + 1, max(1, (m + 1) // 2048))):
            s1b, s2b = step(s1a, s2a, KN[58], w58)
            de[58].add((s1b[4] - s2b[4]) & m)
            # de59, de60 along a single w59=w60=0 ray (they are constant=1, so one sample suffices,
            # but take a few to be safe)
            if w58 < 8:
                for w59 in range(min(m + 1, 64)):
                    s1c, s2c = step(s1b, s2b, KN[59], w59)
                    de[59].add((s1c[4] - s2c[4]) & m)
                    s1d, s2d = step(s1c, s2c, KN[60], 0)
                    de[60].add((s1d[4] - s2d[4]) & m)
    return {r: len(de[r]) for r in de}, db56


def star_discrepancy(values, N):
    """1-D star-discrepancy of {x/2^N} for x in `values` (the fractional parts in [0,1))."""
    xs = sorted(((v & ((1 << N) - 1)) / (1 << N)) for v in values)
    n = len(xs)
    if n == 0:
        return 1.0
    d = 0.0
    for i, x in enumerate(xs):
        d = max(d, abs((i) / n - x), abs((i + 1) / n - x))
    return d


def sigma1_orbit_discrepancy(P, base_word_positions):
    """Star-discrepancy of {sigma1(W_t)/2^N} as W_t ranges over all 2^N word values.
    This is the card's 'is the sigma1 (SHR10) orbit equidistributing?' object."""
    m, N = P['m'], P['N']
    sig1 = P['sig1']
    vals = [sig1(x) for x in range(m + 1)]
    return star_discrepancy(vals, N), len(set(vals))


def run():
    print("# W2-NT3 — does Weyl/lacunary {sigma1(W)/2^N} predict the de58 GROWTH LAW?")
    print("# Ground truth (#4): de57=de59=de60=1 always; de58 = 2**hw(db56) exact (N<=14).")
    print("# Card needs: de58's round = WORST-equidistributed sigma1 orbit AND its")
    print("#             discrepancy slope tracks log2|de58| within 20%.\n")
    rows = []
    for N in (4, 6, 8, 10):
        P = mini(N)
        sizes, db56 = de_sizes(P)
        if sizes is None:
            print(f"N={N}: no cascade-eligible M0 (skip)")
            continue
        hw_db56 = sb.hw(db56)
        law = 1 << hw_db56
        # sigma1 orbit discrepancy (single object — same for every round, since sigma1 is fixed!)
        disc_sig1, img_sig1 = sigma1_orbit_discrepancy(P, None)
        gt = sb.DE_SIZES.get(N)
        print(f"N={N}: |de| = {sizes}   (repo ground truth {gt})")
        print(f"      db56=0x{db56:0{(N+3)//4}x}  hw(db56)={hw_db56}  2**hw={law}  "
              f"-> |de58| matches 2**hw(db56)? {sizes[58] == law}")
        print(f"      sigma1 orbit: |image|={img_sig1}/{1<<N}  star-discrepancy(sigma1)={disc_sig1:.4f}")
        rows.append((N, sizes, hw_db56, law, disc_sig1))
    # --- the decisive test: does sigma1-discrepancy predict log2|de58| ? ---
    print("\n# DECISIVE — card says |de58| ~ (sigma1 non-equidistribution). Test the slope:")
    print(f"  {'N':>3} {'log2|de58|':>10} {'hw(db56)':>9} {'disc(sig1)':>11} {'pred slope?':>12}")
    for (N, sizes, hwd, law, disc) in rows:
        l2 = math.log2(sizes[58]) if sizes[58] > 0 else 0
        print(f"  {N:>3} {l2:>10.3f} {hwd:>9} {disc:>11.4f} {'':>12}")
    if len(rows) >= 2:
        Ns = [r[0] for r in rows]
        l2de = [math.log2(r[1][58]) for r in rows]
        hws = [r[2] for r in rows]
        discs = [r[4] for r in rows]
        # slope of log2|de58| vs N  (the MEASURED growth law)
        def slope(x, y):
            n = len(x); sx = sum(x); sy = sum(y); sxx = sum(a * a for a in x); sxy = sum(a * b for a, b in zip(x, y))
            return (n * sxy - sx * sy) / (n * sxx - sx * sx) if (n * sxx - sx * sx) else 0.0
        s_de = slope(Ns, l2de)
        s_hw = slope(Ns, hws)
        # sigma1 discrepancy vs N: if SHR10 is "lacunary/non-equidistributing", disc should be
        # large/constant and NOT shrink; if it equidistributes, disc -> 0 like 1/2^N.
        s_disc = slope(Ns, discs)
        print(f"\n  MEASURED  d(log2|de58|)/dN = {s_de:.3f}   (this IS the growth law's slope)")
        print(f"  hw(db56)  d(hw)/dN        = {s_hw:.3f}   (the Maj-image law tracks this)")
        print(f"  sigma1    d(disc)/dN      = {s_disc:.5f}  (Weyl orbit discrepancy trend)")
        print(f"  |de58| == 2**hw(db56) at every N? "
              f"{all(r[1][58] == (1 << r[2]) for r in rows)}")
        # is de58 the ONLY growing de_r?  (the card needs sigma1 to single out exactly de58)
        only_de58_grows = all((r[1][57] == 1 and r[1][59] == 1 and r[1][60] == 1) for r in rows)
        print(f"  de57=de59=de60=1 at every N (only de58 grows)? {only_de58_grows}")
        # VERDICT logic
        # The sigma1 orbit discrepancy is a SINGLE per-N number (sigma1 is round-independent),
        # so it CANNOT distinguish de57 from de58 from de59 -- they all share the SAME sigma1.
        # That alone refutes the card's "worst-equidistributed ROUND = de58" claim.
        print("\n  KILL CHECK:")
        print("   - card needs a PER-ROUND equidistribution that singles out de58. But sigma1 is")
        print("     the SAME function at every schedule position -> its orbit discrepancy is ONE")
        print("     number per N, identical for de57/58/59/60. It cannot pick out de58.")
        print(f"   - the real law |de58|=2**hw(db56) is a Maj/AND-IMAGE count (db56 hamming weight),")
        print(f"     reproduced exactly here ({all(r[1][58] == (1 << r[2]) for r in rows)}); it is")
        print(f"     governed by db56's bit pattern, NOT by any fractional-part equidistribution.")
    return rows


if __name__ == '__main__':
    run()
