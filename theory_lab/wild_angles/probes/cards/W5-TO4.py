"""
W5-TO4 — Sheafification gap: locally-consistent fragments that fail to glue, blowing up
at 61.   [catalog calls this the best fan-out]

Card claim: on a round-window site, local sections = collision fragments (presheaf F); the
sheaf F+ keeps only those that GLUE to a global collision; the gap |F|-|F+| is small
through 60 and BLOWS UP at 61 (many locally-consistent fragments disagree on the g1^h
overlap); 2^-2N = the gluing-success rate there.

Probe (card): enumerate local sections per round-window, count matching adjacent pairs and
the fraction that extend to a global collision (gluing rate g_i); does g_i drop sharply at
the 61-window, un-gluable count ~2^-2*width? control: a linear toy has g_i ~ 1 throughout.
Kill: g_i smooth/featureless across rounds, OR un-gluable count doesn't scale like 2^-2N.

------------------------------------------------------------------------------
PRIOR FINDING #4 (the suspicion): "fails to glue at 61" claims keep dissolving into the
KNOWN message-schedule constraint (free words 57-60 -> schedule-determined 61). Decisive
question: is the gluing-rate drop INTRINSIC, or is it EXACTLY the 2^-2N schedule constraint
re-described as a sheaf gap?

OPERATIONALIZATION (exact, N=4/6):
A "round-window" site W_r = the local data needed to take the round-r step. A LOCAL SECTION
over W_r = a partial cascade fragment that is LOCALLY CONSISTENT at r, i.e. its round-r
difference constraint is satisfiable (de_r = 0 *can* hold). The presheaf restriction maps
glue adjacent windows. The SHEAFIFICATION keeps only fragments that extend to a GLOBAL
collision (full 8-register equality at r63).

We measure, for each round r in the tail:
  * L_r = # locally-consistent fragments at window r  (here: # tail inputs whose de up to r
          is all zero -- the ones a local observer would accept as "still a collision").
  * G_r = # of those that GLUE to a global collision.
  * gluing rate g_r = G_r / L_r.
  * the SHEAF GAP |F|-|F+| at r = L_r - G_r (locally-consistent but NOT globally gluable).
Card predicts g_r ~ 1 (small gap) through 60, then a sharp drop at the 61-window with the
un-gluable count scaling ~ 2^-2N. Control: the XOR-linear model should keep g_r ~ 1.

The de-constraint per round is exactly the boundary-proof object: rounds 57-60 impose NO
constraint (cascade da=0 free, de60=0 automatic -> every fragment locally consistent), the
schedule rounds 61-63 impose de61=de62=de63=0. So "the gap blows up at 61" is testable
against "the gap blows up exactly at the FREE->SCHEDULE boundary = the known constraint".
"""
import sys
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards')
import _w5co_engine as E


def per_round_de(M, setup, w57, w58, w59, w60, linear=False):
    """de_r for r=57..63 + full-collision flag. linear=True => XOR arithmetic."""
    MASK = M['MASK']; KN = M['KN']
    W1p, W2p = setup['W1'], setup['W2']
    s1, s2 = setup['st1'], setup['st2']

    if linear:
        def rnd(s, k, w):
            a, b, c, d, e, f, g, h = s
            T1 = h ^ M['S1'](e) ^ M['Ch'](e, f, g) ^ k ^ w
            T2 = M['S0'](a) ^ M['Mj'](a, b, c)
            return ((T1 ^ T2) & MASK, a, b, c, (d ^ T1) & MASK, e, f, g)
        def w2for(s1, s2, rr, w1):
            r1 = (s1[7] ^ M['S1'](s1[4]) ^ M['Ch'](s1[4], s1[5], s1[6]) ^ KN[rr]) & MASK
            r2 = (s2[7] ^ M['S1'](s2[4]) ^ M['Ch'](s2[4], s2[5], s2[6]) ^ KN[rr]) & MASK
            T21 = (M['S0'](s1[0]) ^ M['Mj'](s1[0], s1[1], s1[2])) & MASK
            T22 = (M['S0'](s2[0]) ^ M['Mj'](s2[0], s2[1], s2[2])) & MASK
            return (w1 ^ r1 ^ r2 ^ T21 ^ T22) & MASK
        def comb(*xs):
            v = 0
            for x in xs: v ^= x
            return v & MASK
    else:
        rnd = lambda s, k, w: E.sha_round(s, k, w, M)
        w2for = lambda s1, s2, rr, w1: E.find_w2(s1, s2, rr, w1, M)
        def comb(*xs):
            v = 0
            for x in xs: v += x
            return v & MASK

    de = {}
    w57b = w2for(s1, s2, 57, w57)
    s1 = rnd(s1, KN[57], w57); s2 = rnd(s2, KN[57], w57b); de[57] = (s1[4]-s2[4]) & MASK
    w58b = w2for(s1, s2, 58, w58)
    s1 = rnd(s1, KN[58], w58); s2 = rnd(s2, KN[58], w58b); de[58] = (s1[4]-s2[4]) & MASK
    w59b = w2for(s1, s2, 59, w59)
    s1 = rnd(s1, KN[59], w59); s2 = rnd(s2, KN[59], w59b); de[59] = (s1[4]-s2[4]) & MASK
    if linear:
        cas = w2for(s1, s2, 60, 0); w60b = (w60 ^ cas) & MASK
    else:
        cas = E.find_w2(s1, s2, 60, 0, M); w60b = (w60 + cas) & MASK
    s1 = rnd(s1, KN[60], w60); s2 = rnd(s2, KN[60], w60b); de[60] = (s1[4]-s2[4]) & MASK
    W1_61 = comb(M['s1'](w59),  W1p[54], M['s0'](W1p[46]), W1p[45])
    W2_61 = comb(M['s1'](w59b), W2p[54], M['s0'](W2p[46]), W2p[45])
    W1_62 = comb(M['s1'](w60),  W1p[55], M['s0'](W1p[47]), W1p[46])
    W2_62 = comb(M['s1'](w60b), W2p[55], M['s0'](W2p[47]), W2p[46])
    W1_63 = comb(M['s1'](W1_61), W1p[56], M['s0'](W1p[48]), W1p[47])
    W2_63 = comb(M['s1'](W2_61), W2p[56], M['s0'](W2p[48]), W2p[47])
    s1 = rnd(s1, KN[61], W1_61); s2 = rnd(s2, KN[61], W2_61); de[61] = (s1[4]-s2[4]) & MASK
    s1 = rnd(s1, KN[62], W1_62); s2 = rnd(s2, KN[62], W2_62); de[62] = (s1[4]-s2[4]) & MASK
    s1 = rnd(s1, KN[63], W1_63); s2 = rnd(s2, KN[63], W2_63); de[63] = (s1[4]-s2[4]) & MASK
    collide = (s1 == s2)
    return de, collide


def sheaf_gap(N, linear=False):
    """Local section over window r = a fragment LOCALLY CONSISTENT through r. The collision
    predicate's constraints are de61=de62=de63=0 (boundary-proof Thm 3); rounds 57-60 impose
    nothing (cascade-free, de60=0 automatic). So 'locally consistent through r' = de_r'=0 for
    all CONSTRAINT rounds r'<=r (= {61,62,63}); through round 60 every fragment is consistent.
    L_r = # locally-consistent; G_r = # that glue to a global collision; gap = L_r - G_r."""
    M = E.make_model(N); setup = E.find_M0(M); R = M['MASK'] + 1
    if setup is None:
        return None
    CONSTRAINT_ROUNDS = (61, 62, 63)
    L = {r: 0 for r in range(57, 64)}
    Gg = {r: 0 for r in range(57, 64)}
    total = 0; coll = 0
    for w57 in range(R):
        for w58 in range(R):
            for w59 in range(R):
                for w60 in range(R):
                    total += 1
                    de, col = per_round_de(M, setup, w57, w58, w59, w60, linear)
                    if col: coll += 1
                    ok = True
                    for r in range(57, 64):
                        if r in CONSTRAINT_ROUNDS and de[r] != 0:
                            ok = False
                        if ok:
                            L[r] += 1
                            if col:
                                Gg[r] += 1
    return dict(N=N, total=total, coll=coll, L=L, G=Gg, R=R)


def report(N, linear):
    tag = "LINEAR (XOR control)" if linear else "REAL (modular)"
    d = sheaf_gap(N, linear)
    if d is None:
        print(f"--- N={N} [{tag}]: no cascade-eligible M0 (degenerate width) -- skipped ---")
        return None
    R = d['R']
    print(f"--- N={N} [{tag}] ({d['total']} inputs, {d['coll']} global collisions, 2^-N={1/R:.4f}) ---")
    print(f"  window r | L_r (locally-consistent) | G_r (glue global) | g_r=G/L | gap=L-G | kind")
    prev_g = None
    for r in range(57, 64):
        Lr, Gr = d['L'][r], d['G'][r]
        gr = Gr / Lr if Lr else float('nan')
        gap = Lr - Gr
        kind = "free" if r <= 60 else "schedule"
        flag = ""
        if prev_g is not None and prev_g > 0 and gr / prev_g < 0.5:
            flag = f"  <== g drops x{gr/prev_g:.3f}"
        print(f"    {r}    |       {Lr:7d}            |     {Gr:6d}        | {gr:.5f} | {gap:7d} | {kind}{flag}")
        prev_g = gr
    g60 = d['G'][60] / d['L'][60] if d['L'][60] else float('nan')
    g61 = d['G'][61] / d['L'][61] if d['L'][61] else float('nan')
    print(f"  g_60={g60:.5f} g_61={g61:.5f}  ratio g61/g60={g61/g60 if g60 else float('nan'):.5f}"
          f"  (2^-N={1/R:.4f}, 2^-2N={1/R**2:.6f})")
    # is the gap blow-up exactly at the free->schedule boundary?
    gap60 = d['L'][60]-d['G'][60]; gap_open = d['L'][57]-d['G'][57]
    print(f"  sheaf gap |F|-|F+| at r=57 (widest window)={gap_open}, at r=60={gap60},"
          f" at r=61={d['L'][61]-d['G'][61]}")
    return d


def main():
    print("=== W5-TO4: sheafification gap g_r = (glue-global)/(locally-consistent) ===\n")
    print("Local section = fragment with de=0 through r; glues iff full collision. Card:")
    print("g_r~1 through 60, sharp drop at 61-window, un-gluable ~2^-2N. Control: linear g~1.\n")
    # exact full-grid enumeration feasible at N=4 (65536); N in {6,7,9} have no eligible M0;
    # N=8 grid infeasible. N=4 is the exact scale; the free/schedule split is N-invariant.
    report(4, linear=False)
    print()
    print("--- carry-free control ---")
    report(4, linear=True)


if __name__ == '__main__':
    main()
