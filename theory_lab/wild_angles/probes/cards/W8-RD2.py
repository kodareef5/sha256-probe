#!/usr/bin/env python3
"""
W8-RD2 — Rate cliff: 2^-2N as a +2N-bit R(0) discontinuity, sr=62 = 2^-4N.

Card claim: holding round 61 adds *two independent* refinement constraints (g1=0, h=0,
each N bits), so R(0) jumps by 2N (successive-refinement chain rule, cross-term=0 by
independence) -> 2^-2N; explains Theorem 5's 2^-N undercount.  Predicts sr=62 -> 4N.
  lens R(D) discontinuity / successive refinement  ·  locus W[60] compliance  ·  mech lower-bound.

PROBE (honored): N=6,8,10  R_61(0)-R_60(0) = -log2 P(g1=0 ^ h=0); is it 2N (not N),
I(g1;h)~=0?  extrapolate/spot-check sr=62 -> 4N.
KILL: the gap is N (g1,h dependent, MI>0.1).

PER PRIOR FINDING #3 (the load-bearing adversarial test):
sr=62 = 2^-4N is the CORRECT forward part (already measured 3x: CG3, CL2, marginal
product).  But the rename rule says: CONFIRM only if the rate-distortion structure ADDS
a mechanism BEYOND restating the two conditions g1,h and their trivial forward product.
So this probe does two things:
  (1) numerically confirm R_61(0)-R_60(0) = 2N and I(g1;h)~=0 and sr=62 -> 4N (the card's
      stated probe), and
  (2) ADVERSARIALLY check whether "successive-refinement R(D) chain rule" is any object
      other than the elementary additivity  -log2 P(A^B) = -log2 P(A) - log2 P(B)  that
      holds for ANY two independent events.  If the only content is "two independent
      2^-N conditions multiply", the RD framing is a RENAME of the already-established
      g1,h mechanism, not a new mechanism -> KILLED-as-rename.

R_60(0): the D=0 codebook of the sr=60 problem already exists (cascade gives a collision
freely); the "rate to also satisfy round 61" is exactly the surprisal of (g1=0 ^ h=0).
There is no extra rate-distortion structure: the distortion D = HW(round-61 difference)
is 0 iff g1=0 ^ h=0, a SINGLE 0/nonzero event, so R(0)'s "frontier" is one point, not a
convex curve.  We demonstrate that.

Data:
 - repo gap_rows.csv (946 N=10 cascade collisions) for the structural identity g2=g1+h.
 - faithful mini-SHA(N) cascade (_minisha) for marginal/joint surprisal at N=6,8,10.
"""
import sys, random, math
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards')
import shabridge as sb
import _minisha as m


def mutual_information_bits(joint_counts, M):
    """I(X;Y) in bits from a 2D count dict {(x,y):c}.  Marginals derived internally."""
    px, py = {}, {}
    for (x, y), c in joint_counts.items():
        px[x] = px.get(x, 0) + c
        py[y] = py.get(y, 0) + c
    I = 0.0
    for (x, y), c in joint_counts.items():
        if c == 0:
            continue
        pxy = c / M
        I += pxy * math.log2(pxy / ((px[x] / M) * (py[y] / M)))
    return I


def part_A_identity():
    """Structural identity sr61 <=> g1=0 ^ h=0 on the measured N=10 collision set."""
    rows = sb.load_gap_rows()
    N = 10
    tot = len(rows)
    ident = sum(1 for r in rows
                if (int(r['g1']) + int(r['h'])) % (1 << N) == int(r['g2']))
    return dict(N=N, tot=tot, ident=ident)


def part_B_rate_gap(N, n_samples, seed=11):
    """
    Measure, over random cascade prefixes:
      R_60(0)               = 0  bits   (cascade gives a D=0 collision for free; the
                                          surplus rate to BE an sr-60 collision among
                                          random free words is the sr=60 density, but the
                                          card's 'rate cliff' is the *increment* at 61.)
      R_61(0) - R_60(0)     = -log2 P(g1_60=0 ^ h_60=0)   <- the +2N jump to test
      decomposition into  -log2 P(g1=0) - log2 P(h=0)  +  (coupling term = log2[P(A^B)/P(A)P(B)])
      I(g1_lsb ; h_lsb)     mutual information of the two gating variables (should be ~0)
    Also stack round 61's two conditions for the sr=62 -> 4N spot check.
    """
    S = m.setup(N)
    if S is None:
        return None
    P, O = S['P'], S['O']
    MASK, KN = P['MASK'], P['KN']
    rng = 1 << N
    random.seed(seed)

    # schedule words W[0..56] for both messages (to get sched[60], sched[61])
    W1 = [x & MASK for x in S['M1']] + [0] * 41
    W2 = [x & MASK for x in S['M2']] + [0] * 41
    for i in range(16, 57):
        W1[i] = (O['s1'](W1[i-2]) + W1[i-7] + O['s0'](W1[i-15]) + W1[i-16]) & MASK
        W2[i] = (O['s1'](W2[i-2]) + W2[i-7] + O['s0'](W2[i-15]) + W2[i-16]) & MASK

    def sched(Wp, w58, w59, idx):
        if idx == 60:
            return (O['s1'](w58) + Wp[53] + O['s0'](Wp[45]) + Wp[44]) & MASK
        return (O['s1'](w59) + Wp[54] + O['s0'](Wp[46]) + Wp[45]) & MASK

    c_g1 = c_h = c_both = 0
    c_g1_61 = c_h_61 = c_all4 = 0
    joint = {}                      # (g1_60==0, h_60==0) -> count, for MI
    M = 0
    for _ in range(n_samples):
        w57 = random.randrange(rng); w58 = random.randrange(rng)
        w59 = random.randrange(rng); w60 = random.randrange(rng)
        s1 = list(S['st1_56']); s2 = list(S['st2_56'])
        free = [w57, w58, w59, w60]
        casoff60 = 0
        for k, rnd in enumerate(range(57, 61)):
            w1 = free[k]
            w2 = m.find_w2(s1, s2, rnd, w1, P, O)
            if rnd == 60:
                casoff60 = (w2 - w1) & MASK
            s1 = list(m.sha_round(s1, KN[rnd], w1, P, O))
            s2 = list(m.sha_round(s2, KN[rnd], w2, P, O))
        # round-61 cascade (sr=62 frees W1[61])
        w1_61 = random.randrange(rng)
        w2_61 = m.find_w2(s1, s2, 61, w1_61, P, O)
        casoff61 = (w2_61 - w1_61) & MASK

        sc1_60 = sched(W1, w58, w59, 60); sc2_60 = sched(W2, w58, w59, 60)
        sc1_61 = sched(W1, w58, w59, 61); sc2_61 = sched(W2, w58, w59, 61)
        g1 = (w60 - sc1_60) & MASK
        h = (casoff60 - ((sc2_60 - sc1_60) & MASK)) & MASK
        g1_61 = (w1_61 - sc1_61) & MASK
        h_61 = (casoff61 - ((sc2_61 - sc1_61) & MASK)) & MASK

        bg, bh = (g1 == 0), (h == 0)
        c_g1 += bg; c_h += bh; c_both += (bg and bh)
        c_g1_61 += (g1_61 == 0); c_h_61 += (h_61 == 0)
        c_all4 += (bg and bh and g1_61 == 0 and h_61 == 0)
        key = (bg, bh)
        joint[key] = joint.get(key, 0) + 1
        M += 1

    # ensure all 4 cells exist for MI (0 counts ok)
    for k in [(True, True), (True, False), (False, True), (False, False)]:
        joint.setdefault(k, 0)
    I_bits = mutual_information_bits(joint, M)

    p_g1 = c_g1 / M; p_h = c_h / M; p_both = c_both / M
    R_g1 = -math.log2(p_g1) if p_g1 > 0 else float('inf')
    R_h = -math.log2(p_h) if p_h > 0 else float('inf')
    R_joint = -math.log2(p_both) if p_both > 0 else float('inf')
    coupling = (R_joint - R_g1 - R_h)   # = log2[P(A)P(B)/P(A^B)]; ~0 if independent
    prod4 = p_g1 * p_h * (c_g1_61 / M) * (c_h_61 / M)
    R_sr62 = -math.log2(prod4) if prod4 > 0 else float('inf')
    return dict(N=N, M=M, p_g1=p_g1, p_h=p_h, p_both=p_both,
                R_g1=R_g1, R_h=R_h, R_joint=R_joint, coupling=coupling,
                I_bits=I_bits, R_sr62=R_sr62,
                p_g1_61=c_g1_61 / M, p_h_61=c_h_61 / M)


if __name__ == '__main__':
    print('=== Part A: sr61 <=> g1=0 ^ h=0 on measured N=10 collisions ===')
    a = part_A_identity()
    print(f'  g2=g1+h holds {a["ident"]}/{a["tot"]} collisions => the D=0 (round-61) test'
          f' IS the single event (g1=0 ^ h=0).')
    print()
    print('=== Part B: the "+2N R(0) discontinuity" and sr=62 -> 4N ===')
    print('  R_61(0)-R_60(0) := -log2 P(g1=0 ^ h=0).  Test: ~=2N? coupling~=0? I(g1;h)~=0?')
    for N in (6, 8, 10):
        b = part_B_rate_gap(N, n_samples={6: 600000, 8: 600000, 10: 350000}[N])
        if b is None:
            print(f'  N={N}: no kernel'); continue
        print(f'  N={N}:  R(g1=0)={b["R_g1"]:.2f}  R(h=0)={b["R_h"]:.2f}  '
              f'R(g1=0 ^ h=0)={b["R_joint"]:.2f}  (target 2N={2*N})')
        print(f'         coupling term log2[P(A)P(B)/P(A^B)] = {b["coupling"]:+.3f} bits '
              f'(card needs ~0);  I(g1;h) = {b["I_bits"]:.4f} bits (kill if >0.1)')
        print(f'         sr=62 stacks +2 more (g1_61,h_61): R_sr62(0) = {b["R_sr62"]:.2f}  '
              f'(target 4N={4*N})')
    print()
    print('=== Adversarial: is the RD framing a MECHANISM or a RENAME? ===')
    print('  The "successive-refinement chain rule with cross-term=0" reduces to the')
    print('  elementary identity  -log2 P(A^B) = -log2 P(A) -log2 P(B)  for independent A,B.')
    print('  The distortion D=HW(round-61 diff) is 0 iff the SINGLE event (g1=0 ^ h=0) holds')
    print('  => R(0) is one point, not a convex R(D) frontier; no Blahut-Arimoto codebook,')
    print('  no reconstruction alphabet beyond {collide, not}.  This RESTATES g1,h.')
