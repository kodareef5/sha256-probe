"""
W5-TO5 — Geometric morphism: MITM as a functor that loses faithfulness at the wall.

Card claim: the cascade/MITM join is a geometric morphism Sh(B)->Sh(F); an EMBEDDING
(f* full+faithful) through round 60 (each backward residue pins a UNIQUE forward
continuation) that LOSES FAITHFULNESS at 61 (distinct backward states share a forward
image); the generic fiber size = the MITM blow-up = reciprocal 2^-2N.

Probe (card): sweep the split round m; mean |f*-fiber| (backward preimages per forward
image) = 1 (faithful) for <=60, jumps to exp ~2^(2*width) at 61? control: a linear toy
stays size-1.
Kill: fibers fat well before 61, OR grow smoothly (no faithful->unfaithful transition),
OR stay size-1 past the wall.

------------------------------------------------------------------------------
What "fiber" means operationally here.

f* = inverse image of the geometric morphism = the map from a FORWARD object (the
state/diff reached by going IV->m) back to the set of BACKWARD continuations (tail words
m+1..63) that land on a collision through that forward state. "Faithful" <=> that fiber
is a singleton (each forward image has a unique backward witness); "loses faithfulness"
<=> fibers fatten.

Concretely, on the canonical cascade-DP tail (the real wall lives at round 61):
  - We enumerate ALL tail inputs (w57,w58,w59,w60) exhaustively (N=4, exact).
  - For a split at round m, the FORWARD image = the diff-state ds_m reached after round m
    (what a forward MITM pass would expose at the cut), restricted to the COLLIDING
    inputs (those that complete to a full sr=60 collision at r63).
  - The BACKWARD fiber over ds_m = the set of full tail-input tuples that (a) collide and
    (b) pass through that same ds_m at round m.
  - mean fiber size F(m) = (#colliding inputs) / (#distinct colliding ds_m). F(m)=1 means
    faithful (the cut ds pins the rest); F(m)>1 means the cut LOSES information.

The card's prediction: F(m) ~ 1 for m up to 60 (the split is faithful = an embedding),
then jumps to an exponential ~2^(2N) at m=61. We compute F(m) for EVERY split m in the
tail (rounds 57..63) and ask whether the JUMP is at 61 specifically, or whether the cut
is information-losing throughout / monotone / located elsewhere.

Linear control: rerun with the *carry-killed* model (modular add replaced by XOR) and ask
whether F(m) stays 1 (the card says the linear toy is faithful everywhere).
"""
import sys
from collections import defaultdict, Counter
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards')
import _w5co_engine as E


def trace_cutstate_per_round(M, setup, w57, w58, w59, w60, linear=False):
    """Replay one tail input. Returns (dict round-> path1 FORWARD STATE after that round)
    and whether the pair fully collides at r63.

    The MITM 'forward image' at split m is the path-1 forward state at the cut. The card's
    f* fiber over that image = the set of colliding tail-inputs sharing it. We track the
    real (non-diff) path-1 state so the cut carries genuine MITM information (a backward
    residue at m+1 must meet this forward state).

    linear=True swaps modular '+' for XOR everywhere in the round + cascade (the carry-free
    'linear toy' control the card asks for) so we can check faithfulness without carries.
    """
    MASK = M['MASK']; KN = M['KN']
    W1p, W2p = setup['W1'], setup['W2']
    s1, s2 = setup['st1'], setup['st2']

    if linear:
        def addv(a, b):
            return (a ^ b) & MASK
        def rnd(s, k, w):
            a, b, c, d, e, f, g, h = s
            T1 = h ^ M['S1'](e) ^ M['Ch'](e, f, g) ^ k ^ w
            T2 = M['S0'](a) ^ M['Mj'](a, b, c)
            return ((T1 ^ T2) & MASK, a, b, c, (d ^ T1) & MASK, e, f, g)
        def w2for(s1, s2, rnd_, w1):
            # linear cascade offset keeping da=0 under XOR arithmetic
            r1 = (s1[7] ^ M['S1'](s1[4]) ^ M['Ch'](s1[4], s1[5], s1[6]) ^ KN[rnd_]) & MASK
            r2 = (s2[7] ^ M['S1'](s2[4]) ^ M['Ch'](s2[4], s2[5], s2[6]) ^ KN[rnd_]) & MASK
            T21 = (M['S0'](s1[0]) ^ M['Mj'](s1[0], s1[1], s1[2])) & MASK
            T22 = (M['S0'](s2[0]) ^ M['Mj'](s2[0], s2[1], s2[2])) & MASK
            return (w1 ^ r1 ^ r2 ^ T21 ^ T22) & MASK
    else:
        def addv(a, b):
            return (a + b) & MASK
        rnd = lambda s, k, w: E.sha_round(s, k, w, M)
        w2for = lambda s1, s2, rnd_, w1: E.find_w2(s1, s2, rnd_, w1, M)

    def sch(s1_, c54, c46, c45):
        # schedule word with arithmetic matching the model
        return addv(addv(addv(M['s1'](s1_), c54), M['s0'](c46)), c45)

    out = {}
    # r57,58 cascade
    w57b = w2for(s1, s2, 57, w57)
    s1 = rnd(s1, KN[57], w57); s2 = rnd(s2, KN[57], w57b); out[57] = s1
    w58b = w2for(s1, s2, 58, w58)
    s1 = rnd(s1, KN[58], w58); s2 = rnd(s2, KN[58], w58b); out[58] = s1
    # r59
    w59b = w2for(s1, s2, 59, w59)
    s1 = rnd(s1, KN[59], w59); s2 = rnd(s2, KN[59], w59b); out[59] = s1
    # r60
    if linear:
        cas = w2for(s1, s2, 60, 0); w60b = (w60 ^ cas) & MASK
    else:
        cas = E.find_w2(s1, s2, 60, 0, M); w60b = (w60 + cas) & MASK
    s1 = rnd(s1, KN[60], w60); s2 = rnd(s2, KN[60], w60b); out[60] = s1
    # schedule-fixed 61..63 (W[61] is schedule-determined -- the wall)
    W1_61 = sch(w59,  W1p[54], W1p[46], W1p[45]); W2_61 = sch(w59b, W2p[54], W2p[46], W2p[45])
    W1_62 = sch(w60,  W1p[55], W1p[47], W1p[46]); W2_62 = sch(w60b, W2p[55], W2p[47], W2p[46])
    W1_63 = sch(W1_61, W1p[56], W1p[48], W1p[47]); W2_63 = sch(W2_61, W2p[56], W2p[48], W2p[47])
    s1 = rnd(s1, KN[61], W1_61); s2 = rnd(s2, KN[61], W2_61); out[61] = s1
    s1 = rnd(s1, KN[62], W1_62); s2 = rnd(s2, KN[62], W2_62); out[62] = s1
    s1 = rnd(s1, KN[63], W1_63); s2 = rnd(s2, KN[63], W2_63); out[63] = s1
    collide = (s1 == s2)
    return out, collide


def fiber_profile(N, linear=False):
    """For each split round m in 57..63, the mean f*-fiber size over COLLIDING inputs =
    (#colliding) / (#distinct colliding FORWARD cut-states at m). Faithful <=> ~1."""
    M = E.make_model(N); setup = E.find_M0(M); R = M['MASK'] + 1
    if setup is None:
        return None, None, None
    coll_traces = []
    n_total = 0
    for w57 in range(R):
        for w58 in range(R):
            for w59 in range(R):
                for w60 in range(R):
                    n_total += 1
                    tr, col = trace_cutstate_per_round(M, setup, w57, w58, w59, w60, linear)
                    if col:
                        coll_traces.append(tr)
    n_coll = len(coll_traces)
    profile = {}
    for m in range(57, 64):
        dsset = Counter(tr[m] for tr in coll_traces)
        n_distinct = len(dsset)
        mean_fiber = n_coll / n_distinct if n_distinct else float('nan')
        max_fiber = max(dsset.values()) if dsset else 0
        profile[m] = (n_distinct, mean_fiber, max_fiber)
    return n_total, n_coll, profile


def report(N, linear):
    tag = "LINEAR (XOR, carry-free control)" if linear else "REAL (modular, carries on)"
    n_total, n_coll, prof = fiber_profile(N, linear)
    if prof is None:
        print(f"N={N}  [{tag}]: NO cascade-eligible M0 (degenerate width) -- skipped\n")
        return None, None
    print(f"N={N}  [{tag}]: {n_total} tail inputs, {n_coll} full collisions\n")
    print(f"  split m | #distinct colliding cut-states | mean fiber |f*| | max fiber")
    prev = None
    for m in range(57, 64):
        nd, mf, mx = prof[m]
        flag = ""
        if prev is not None and prev > 0 and mf / prev > 1.5:
            flag = f"   <== jump x{mf/prev:.2f} vs r{m-1}"
        print(f"     {m}   |          {nd:5d}              |   {mf:8.3f}    |   {mx}{flag}")
        prev = mf
    faithful_through_60 = all(abs(prof[m][1] - 1.0) < 1e-9 for m in range(57, 61))
    first_fat = next((m for m in range(57, 64) if prof[m][1] > 1.0 + 1e-9), None)
    print(f"  faithful(==1) for all m in 57..60? {faithful_through_60}"
          f" | first split with mean fiber>1: m={first_fat}"
          f" | f(60)={prof[60][1]:.3f} f(61)={prof[61][1]:.3f}"
          f" | 2^(2N)={2**(2*N)}\n")
    return prof, first_fat


def main():
    print("=== W5-TO5: MITM split-fiber (loss of faithfulness) across the tail ===\n")
    print("MITM f*-fiber = #colliding inputs sharing the same path-1 FORWARD state at the")
    print("cut. Faithful (embedding) <=> mean fiber == 1. Card: ~1 through 60, jump at 61.\n")
    # exact full-grid enumeration is only feasible at N=4 (65536 inputs); N in {6,7,9}
    # have NO cascade-eligible M0 (degenerate); N=8 grid (256^4) is infeasible to enumerate.
    # N=4 (49 collisions) is the exact probe scale; the free/schedule round split it reveals
    # is N-invariant (boundary-proof Theorems 1-4 hold at all N).
    report(4, linear=False)
    print("--- carry-free control (same N) ---")
    report(4, linear=True)


if __name__ == '__main__':
    main()
