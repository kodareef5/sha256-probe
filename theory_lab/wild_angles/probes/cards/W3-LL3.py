#!/usr/bin/env python3
"""
W3-LL3 — Lopsided / cluster-expansion -> derives 2^-2N as a Shearer sign change.

Card: the cascade's NEGATIVE round-correlations put it in the lopsided regime;
the independent-set (Shearer) polynomial Z's sign = existence. The two-condition
round SQUARES a vertex weight (p -> p^2 ~ 2^-2N), flipping Z through zero at sr=61.

Probe (honoring the card):
  (A) measure pairwise joints Pr[B_i & B_j] vs p_i p_j  -> confirm NEGATIVE
      correlation (lopsided regime), else KILL.
  (B) build a local Shearer independent-set polynomial Z over a ~5-round window;
      slide it. Z>0 through sr=60; Z<=0 once the SQUARED-weight sr=61 vertex enters.

Kill: positive correlations (wrong regime), OR Z's sign is truncation-dependent.

PRIOR (lead #3): 2^-2N is GENUINELY rank-2 — g2=g1+h exact for all 946 collisions,
TWO independent N-bit conditions (g1,h), independence ratio 1.005. We may CONFIRM
ONLY IF the Shearer machinery DERIVES the "2" (the weight is a true square p^2 from
two independent conditions), not merely allows 2^-2N. A bound that just *permits*
2^-2N without producing the square is a rename -> SURVIVES at best.
"""
import sys, random, itertools, csv
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
import transfer_operator as to

TAPS = (2, 7, 15, 16)

# ----- (A) measure per-round bad events and their PAIRWISE correlations -------
def measure_correlations(N, samples=4000, seed=5):
    """Bad event B_r = 'de(r) != 0' under the cascade-conditioned measure (msg-2
    = MSB cascade kernel, random free words). Returns p[r] and joint[r1][r2]."""
    rp = to._rot_params(N); m = (1 << N) - 1
    rnd = to._make_round(N)
    def rorr(x, k): k %= N; return ((x >> k) | (x << (N - k))) & m
    s0r, s1r = rp['s0'], rp['s1']
    s0 = lambda x: (rorr(x, s0r[0]) ^ rorr(x, s0r[1]) ^ ((x >> s0r[2]) & m)) & m
    s1 = lambda x: (rorr(x, s1r[0]) ^ rorr(x, s1r[1]) ^ ((x >> s1r[2]) & m)) & m
    K = [(sb.K[i] & m) for i in range(64)]
    IVn = tuple(sb.IV[i] & m for i in range(8))
    rng = random.Random(seed)
    MSB = 1 << (N - 1)
    rounds = list(range(57, 64))
    cnt = {r: 0 for r in rounds}
    joint = {(a, b): 0 for a in rounds for b in rounds}
    tot = 0
    for _ in range(samples):
        M1 = [rng.randrange(1 << N) for _ in range(16)]
        M2 = list(M1); M2[0] ^= MSB
        def sched(M):
            W = [v & m for v in M] + [0] * 41
            for i in range(16, 57):
                W[i] = (s1(W[i-2]) + W[i-7] + s0(W[i-15]) + W[i-16]) & m
            return W
        W1, W2 = sched(M1), sched(M2)
        a1, a2 = IVn, IVn
        for i in range(57):
            a1 = rnd(a1, K[i], W1[i]); a2 = rnd(a2, K[i], W2[i])
        free = [rng.randrange(1 << N) for _ in range(4)]
        Wt1, Wt2 = list(W1), list(W2)
        for j in range(4):
            Wt1.append(free[j]); Wt2.append(free[j])
        for i in range(61, 64):
            Wt1.append((s1(Wt1[i-2]) + Wt1[i-7] + s0(Wt1[i-15]) + Wt1[i-16]) & m)
            Wt2.append((s1(Wt2[i-2]) + Wt2[i-7] + s0(Wt2[i-15]) + Wt2[i-16]) & m)
        bad = {}
        for r in rounds:
            a1 = rnd(a1, K[r], Wt1[r]); a2 = rnd(a2, K[r], Wt2[r])
            bad[r] = 1 if (a1[4] - a2[4]) & m else 0
        for r in rounds:
            cnt[r] += bad[r]
        for a in rounds:
            for b in rounds:
                if bad[a] and bad[b]:
                    joint[(a, b)] += 1
        tot += 1
    p = {r: cnt[r] / tot for r in rounds}
    J = {k: joint[k] / tot for k in joint}
    return p, J, tot, rounds

# ----- (B) Shearer independent-set polynomial over a window ---------------------
def dep_graph(rounds):
    """edges between rounds sharing a free variable via the taps {2,7,15,16}."""
    E = set()
    for a in rounds:
        for b in rounds:
            if a < b and (b - a) in TAPS:
                E.add((a, b))
    return E

def shearer_Z(rounds, weights, edges):
    """Z = sum over INDEPENDENT subsets I of prod_{i in I} (-w_i).
    (independent-set polynomial with negative weights -w; Shearer existence <=>
    Z(restricted to every tail) > 0). Brute force over subsets (window <= ~7)."""
    adj = {r: set() for r in rounds}
    for (a, b) in edges:
        adj[a].add(b); adj[b].add(a)
    Z = 0.0
    rl = list(rounds)
    for k in range(len(rl) + 1):
        for I in itertools.combinations(rl, k):
            # independent?
            ok = True
            for x in range(len(I)):
                for y in range(x + 1, len(I)):
                    if I[y] in adj[I[x]]:
                        ok = False; break
                if not ok: break
            if not ok:
                continue
            term = 1.0
            for i in I:
                term *= (-weights[i])
            Z += term
    return Z

def run(N):
    print(f"\n===== N={N}  W3-LL3 lopsided/Shearer =====")
    p, J, tot, rounds = measure_correlations(N, samples=4000, seed=9)
    print(f"  per-round bad-prob p[r] (de!=0), {tot} conditioned samples:")
    for r in rounds:
        print(f"    r={r}: p={p[r]:.4f}")
    # (A) negative correlation test on ADJACENT (tap-linked) pairs.
    # Report the RELATIVE deviation (joint - pi*pj)/(pi*pj): only a deviation many
    # times the 1/sqrt(samples) sampling noise counts as a real negative correlation.
    import math
    noise = 1.0 / math.sqrt(tot)
    print(f"  pairwise correlation on tap-linked pairs  (sampling noise ~ {noise:.4f}):")
    neg_sig, pos_sig, null = 0, 0, 0
    for (a, b) in sorted(dep_graph(rounds)):
        joint_ab = J[(a, b)]; prod = p[a] * p[b]
        rel = (joint_ab - prod) / prod if prod else 0.0
        sig = abs(rel) > 3 * noise / max(prod, 1e-9)
        tag = ('NEG' if rel < 0 else 'POS') if sig else 'NULL(noise)'
        if not sig: null += 1
        elif rel < 0: neg_sig += 1
        else: pos_sig += 1
        print(f"    ({a},{b}): joint={joint_ab:.5f}  pi*pj={prod:.5f}  rel.dev={rel:+.2e}  -> {tag}")
    lopsided = (neg_sig > 0 and pos_sig == 0)
    print(f"  SIGNIFICANT negative-correlation (lopsided)? neg={neg_sig} pos={pos_sig} "
          f"null={null} -> {lopsided}  (NULL = corr indistinguishable from 0)")

    # (B) Shearer Z over a 5-round window 57..61. Compare the sr=61 vertex weight:
    #     (i)  single condition  w61 = 2^-N      (the Theorem-5 undercount)
    #     (ii) squared/two-cond  w61 = 2^-2N     (the verified rank-2 reality)
    # The window 57..60 are FREE (the cascade absorbs them: p~0); 61 is the held
    # vertex. We use IDEALIZED weights to isolate the SIGN mechanism cleanly.
    win = list(range(57, 62))
    edges = dep_graph(win)
    print(f"  window {win}, tap-edges={sorted(edges)}")
    base = {r: (2.0 ** (-N)) for r in range(57, 61)}  # free rounds: tiny residual
    for wlabel, w61 in (("single 2^-N", 2.0 ** (-N)), ("squared 2^-2N", 2.0 ** (-2 * N))):
        wts = dict(base); wts[61] = w61
        Z = shearer_Z(win, wts, edges)
        # truncation check: same Z on a wider window 56..62 (extra free vertices)
        win2 = list(range(56, 63))
        wts2 = {r: 2.0 ** (-N) for r in win2}; wts2[61] = w61
        Z2 = shearer_Z(win2, wts2, dep_graph(win2))
        print(f"    sr=61 vertex = {wlabel:>14}:  Z(win5)={Z:.6e}  Z(win7)={Z2:.6e}  "
              f"sign={'+' if Z>0 else '-' if Z<0 else '0'}  trunc-stable={ (Z>0)==(Z2>0) }")

    # DECISIVE: does SQUARING the sr=61 vertex EVER flip Z through zero? Sweep the
    # base free-round weight; for each, compare Z with w61=p vs w61=p^2. A genuine
    # "Shearer sign change deriving the 2" requires Z>0 at single-weight and Z<=0
    # at squared-weight for SOME physical weight regime.
    print("  sign-flip sweep: does w61: p -> p^2 ever cross Z through 0?")
    flip_found = False
    for pbase in (2.0**(-N), 0.1, 0.3, 0.5, 0.9, 0.99):
        w = {r: pbase for r in range(57, 61)}
        w[61] = pbase; Zs = shearer_Z(win, w, edges)
        w[61] = pbase * pbase; Zq = shearer_Z(win, w, edges)
        flip = (Zs > 0) and (Zq <= 0)
        flip_found = flip_found or flip
        print(f"    p_base={pbase:<6}: Z(w61=p)={Zs:+.4e}  Z(w61=p^2)={Zq:+.4e}  flip? {flip}")
    print(f"  squaring the vertex EVER flips Z sign? {flip_found}  "
          f"(the card's claimed mechanism)")

    # rank-2 re-confirmation (NOT a Shearer derivation — already known via NT4/RG1-B)
    rank2 = check_squared_weight(N)
    print(f"  [aside] rank-2 g2=g1+h re-confirmed on data? {rank2} "
          f"(this is the KNOWN structure, NOT produced BY Shearer)")
    return p, J, lopsided, flip_found

def check_squared_weight(N):
    """The sr=61 vertex weight is a TRUE square iff it factors into two independent
    N-bit conditions. Use the verified N=10 gap data (g2=g1+h; g1,h independent).
    Confirms the '2' is p_g1 * p_h, not a single coupled p."""
    try:
        rows = sb.load_gap_rows()
    except Exception:
        return None
    M = len(rows)
    if M == 0:
        return None
    mod = 1
    while mod < max(int(r['g1']) for r in rows) + 1:
        mod <<= 1
    # rank-2: g2 == g1 + h
    rank2 = all((int(r['g1']) + int(r['h'])) % mod == int(r['g2']) % mod for r in rows)
    # the two conditions g1=0 and h=0 are on DISJOINT coordinates (already verified
    # independent at ratio 1.005). The weight of the held vertex is thus
    #   P(g1=0 AND h=0) = P(g1=0)*P(h=0) = 2^-N * 2^-N = 2^-2N  (a genuine SQUARE).
    return rank2

if __name__ == '__main__':
    for N in (8, 10):
        run(N)
