"""
W2-NT5 — Canonical height -> collisions as height-zero preperiodic coincidences.

CARD CLAIM (CATALOG):
  Give the schedule a canonical height h_hat(M) = lim (bit-spread/depth) a la Call-Silverman.
  Preperiodic (h_hat=0) points = messages whose carry-orbit COLLAPSES = the low-HW structured
  fills the repo keeps rediscovering (0x55, 0x15). A collision = a height-zero coincidence (two
  h_hat=0 messages with equal feed-forward image); equidistribution-of-small-height predicts
  collisions concentrate there.
  PROBE: N=8,10 — compute a PROXY h_hat (normalized carry/state bit-spread after rounds); do
  colliding pairs have systematically LOWER h_hat? do 0x55/0x15 sit at h_hat~0? is the da=0
  cascade family the h_hat~0 set?
KILL: dead if colliding pairs have the SAME h_hat distribution as random pairs, OR structured
fills aren't low-height.

SKEPTIC (card's own): "canonical height" over Z/2^N is a stretch (no projective variety, the
limit may not converge); the PROXY may just re-measure Hamming weight. -> We must (a) test the
collision-vs-random h_hat separation AND (b) check whether h_hat is merely HW in disguise
(correlate h_hat with input HW; if r~1 the card is just HW re-skinned -> weak even if it
"passes").

WHAT THIS PROBE DOES (exact-ish, small N):
  1. Define a height proxy h_hat(M): iterate the SHA-256 round map (N-bit) for D depths on the
     state seeded by M; track the average state bit-spread (popcount over the 8 registers,
     normalized by 8N) and average over depth -> a [0,1] "bit-spread height". A carry-orbit that
     COLLAPSES to a low-spread fixed pattern has small h_hat; a scrambling orbit has h_hat~0.5.
  2. Collision vs random: take the measured sr=60 collisions (gap_rows N=10 -> the (w57..w60)
     freedoms) and matched RANDOM (non-colliding) tail choices; compute h_hat for each path's
     full message and compare the DISTRIBUTIONS (mean, KS-style separation).
  3. Structured fills: compute h_hat for fills 0x55, 0x15, 0xAA, and the all-ones / MSB fills the
     repo uses; are 0x55/0x15 at the LOW end (h_hat ~ 0)?
  4. HW confounder: correlate h_hat with hw(M) across random messages; if |corr| ~ 1, h_hat is
     just Hamming weight wearing a height costume (the skeptic's worry).
"""
import sys, math, random
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


def schedule(P, M, R):
    m, sig0, sig1 = P['m'], P['sig0'], P['sig1']
    W = [M[i] & m for i in range(16)] + [0] * (R - 16)
    for i in range(16, R):
        W[i] = (sig1(W[i - 2]) + W[i - 7] + sig0(W[i - 15]) + W[i - 16]) & m
    return W


def rnd(P, st, k, w):
    m, S0, S1, Ch, Maj = P['m'], P['S0'], P['S1'], P['Ch'], P['Maj']
    a, b, c, d, e, f, g, h = st
    T1 = (h + S1(e) + Ch(e, f, g) + k + w) & m
    T2 = (S0(a) + Maj(a, b, c)) & m
    return ((T1 + T2) & m, a, b, c, (d + T1) & m, e, f, g)


def h_hat(P, M, R=48):
    """Height proxy: run R rounds, track the per-round state bit-spread (popcount over 8 regs /
    (8N)) and average. A collapsing/preperiodic orbit -> low spread; a scrambling one -> ~0.5.
    Also returns the LATE-orbit spread (last 8 rounds), the 'asymptotic' height."""
    m, N = P['m'], P['N']
    W = schedule(P, M, R)
    st = tuple(P['IVN'])
    spreads = []
    for i in range(R):
        st = rnd(P, st, P['KN'][i], W[i])
        pc = sum(sb.hw(x) for x in st)
        spreads.append(pc / (8 * N))
    avg = sum(spreads) / len(spreads)
    late = sum(spreads[-8:]) / 8
    return avg, late


def fill_msg(N, m0, fill):
    M = [fill & ((1 << N) - 1)] * 16
    M[0] = m0 & ((1 << N) - 1)
    return M


def find_M0_msb(P):
    m, N = P['m'], P['N']
    MSB = 1 << (N - 1)
    for cand in range(m + 1):
        M1 = fill_msg(N, cand, m)
        M2 = fill_msg(N, cand ^ MSB, m)
        M2[9] = m ^ MSB
        st1 = run57(P, M1)
        st2 = run57(P, M2)
        if st1[0] == st2[0]:
            return cand
    return None


def run57(P, M):
    W = schedule(P, M, 57)
    st = tuple(P['IVN'])
    for i in range(57):
        st = rnd(P, st, P['KN'][i], W[i])
    return st


def load_collision_msgs_n10(P):
    """From gap_rows.csv (N=10), rebuild the colliding messages' tails. Each row gives
    (w57,w58,w59,w60) for path1. We compute h_hat on the FULL message built from MSB-cascade
    M0 + those free tail words (treating W57..W60 as appended schedule words)."""
    m, N = P['m'], P['N']
    rows = sb.load_gap_rows()
    M0 = find_M0_msb(P)
    if M0 is None:
        return [], None
    msgs = []
    for r in rows:
        # the 'message' whose height we score: base MSB-cascade fill, with the tail freedoms as
        # the round-57..60 schedule values. We approximate the height by the 16-word base message
        # plus the realized tail — but h_hat is defined on the 16-word M, so we score the base
        # message and separately the realized tail-energy via the W57..60 popcounts.
        w = [int(r['w57']), int(r['w58']), int(r['w59']), int(r['w60'])]
        msgs.append(w)
    return msgs, M0


def run():
    print("# W2-NT5 — do collisions sit at LOW canonical height (h_hat~0) and is h_hat != HW?")
    print("# Skeptic weapon: h_hat may just re-measure Hamming weight -> correlate it.\n")
    for N in (8, 10):
        P = mini(N)
        print(f"=== N={N} ===")
        # ---- 1+4: height of random messages, and HW confounder ----
        rng = random.Random(13 + N)
        rand_h, rand_hw = [], []
        for _ in range(400):
            M = [rng.randint(0, P['m']) for _ in range(16)]
            avg, late = h_hat(P, M)
            rand_h.append(avg)
            rand_hw.append(sum(sb.hw(x) for x in M) / (16 * N))
        mh = sum(rand_h) / len(rand_h)
        # correlation h_hat vs input HW
        mhw = sum(rand_hw) / len(rand_hw)
        cov = sum((a - mh) * (b - mhw) for a, b in zip(rand_h, rand_hw)) / len(rand_h)
        sa = (sum((a - mh) ** 2 for a in rand_h) / len(rand_h)) ** 0.5
        sb_ = (sum((b - mhw) ** 2 for b in rand_hw) / len(rand_hw)) ** 0.5
        corr = cov / (sa * sb_) if sa * sb_ else 0
        print(f"  random msgs: mean h_hat = {mh:.4f} (sd {sa:.4f})  |  corr(h_hat, input HW) = {corr:+.3f}")

        # ---- 3: structured fills ----
        print(f"  structured fills (m0 fixed=1):")
        for fill in [0x55, 0x15, 0xAA, 0x00, P['m'], (1 << (N - 1))]:
            M = fill_msg(N, 1, fill)
            avg, late = h_hat(P, M)
            tag = {0x55: '0x55', 0x15: '0x15', 0xAA: '0xAA', 0x00: 'zero',
                   P['m']: 'all-ones', (1 << (N - 1)): 'MSB'}.get(fill, hex(fill))
            # percentile of this fill's h_hat within the random distribution
            pct = sum(1 for x in rand_h if x < avg) / len(rand_h)
            lowflag = 'LOW' if pct < 0.25 else ('high' if pct > 0.75 else 'mid')
            print(f"    fill {tag:9s} (0x{fill & P['m']:0{(N+3)//4}x}): h_hat={avg:.4f}  late={late:.4f}  "
                  f"percentile={pct:.2f} [{lowflag}]")

        # ---- 2: collision vs random tail (N=10 only, where we have measured collisions) ----
        if N == 10:
            msgs, M0 = load_collision_msgs_n10(P)
            if msgs:
                # height of the colliding tails: build 16-word msg as MSB cascade base, then the
                # 4 tail words pushed into positions 12..15 (a fair, fixed embedding for all rows).
                coll_h = []
                for w in msgs[:400]:
                    M = fill_msg(N, M0, P['m'])
                    M[12], M[13], M[14], M[15] = w[0], w[1], w[2], w[3]
                    avg, _ = h_hat(P, M)
                    coll_h.append(avg)
                # matched random: same base, random 4 tail words
                ctrl_h = []
                for _ in range(400):
                    M = fill_msg(N, M0, P['m'])
                    M[12], M[13], M[14], M[15] = [rng.randint(0, P['m']) for _ in range(4)]
                    avg, _ = h_hat(P, M)
                    ctrl_h.append(avg)
                mc = sum(coll_h) / len(coll_h)
                mr = sum(ctrl_h) / len(ctrl_h)
                sc = (sum((a - mc) ** 2 for a in coll_h) / len(coll_h)) ** 0.5
                # KS-style separation
                allv = sorted(set(coll_h + ctrl_h))
                ks = 0.0
                for v in allv:
                    fc = sum(1 for a in coll_h if a <= v) / len(coll_h)
                    fr = sum(1 for a in ctrl_h if a <= v) / len(ctrl_h)
                    ks = max(ks, abs(fc - fr))
                print(f"  COLLISION vs RANDOM tail (MSB cascade base, 4 free tail words):")
                print(f"    collision mean h_hat = {mc:.4f} (sd {sc:.4f})   random mean = {mr:.4f}")
                print(f"    mean difference = {mc - mr:+.4f}   KS separation = {ks:.3f}  "
                      f"(small => SAME distribution => KILL)")
        print()

    print("# VERDICT LOGIC:")
    print("  - card needs (a) collisions LOWER h_hat than random AND (b) 0x55/0x15 at h_hat~0.")
    print("  - if collision/random distributions coincide (small KS) -> kill fires.")
    print("  - if corr(h_hat, input HW) ~ 1 -> h_hat is just Hamming weight re-skinned (even a")
    print("    'low-fill' pass would be the HW finding the repo already has, not a new height).")


if __name__ == '__main__':
    run()
