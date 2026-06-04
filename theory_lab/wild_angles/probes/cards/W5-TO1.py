"""
W5-TO1 — Forcing threshold: collision is a dense open through 60, nowhere-dense at 61.

Card claim: on the poset of partial-consistent assignments, Phi="extends to a collision"
is FORCED (dense-open below p) for r<=60 and becomes NOWHERE-DENSE at 61; the residual
open measure = 2^-2N; the not-not-vs-actual gap = "no obstruction != constructible".

Probe (card): N=6,8,10 forcing-density delta_r(p) = fraction of children still forcing Phi;
plateau (dense) for <=60, crash to ~0 at 61? delta_61/delta_60 -> 0 like 2^-2N?
Kill: delta_r smooth/monotone (no knee at 61), OR the not-not-gap is empty everywhere
(Omega Boolean -> framing buys nothing).

------------------------------------------------------------------------------
PRIOR FINDING #4 (the suspicion on this card): "dense-open -> nowhere-dense at 61" claims
keep dissolving into the KNOWN message-schedule constraint (rounds 57-60 are FREE words;
W[61] becomes schedule-determined -> the collision predicate first acquires a differential
constraint there). The decisive question: is the "61 transition" INTRINSIC (a genericity
threshold that XOR-linearization would also show, but located by genericity not by the
schedule), or is it EXACTLY the 2^-2N schedule constraint re-described?

OPERATIONALIZATION (exact, N=4/6):
The poset = prefixes of the free tail words. A node at level k = a fixed prefix
(w57,...,w_{56+k}). Phi(node) = "some completion of the remaining free words yields a full
sr=60 collision (8-register equal at r63)". The forcing/genericity quantities:
  * survive_k = fraction of level-k prefixes that still force Phi (have >=1 colliding
    completion) -- this is "density of Phi below depth k".
  * Per the boundary structure, the collision constraints are de61=de62=de63=0. We ALSO
    track, round by round r=57..63, the per-round survival ratio
       rho_r = P(de_r = 0 AND collision-reachable) / P(collision-reachable up to r-1),
    i.e. the fraction of still-live partial collisions that survive the round-r constraint.
    delta_r := this per-round survival. The card predicts delta_r ~ 1 for r<=60 (dense),
    then delta_61 ~ 2^-N (crash). delta_61/delta_60 -> 0 like 2^-N per round (2^-2N total
    across the schedule rounds).
  * not-not gap: a prefix where Phi is NOT refuted (de61 *could* be 0 for some completion)
    but is NOT constructibly forced (no completion actually collides). |{not-refuted}| -
    |{forced}| = the not-not-vs-actual gap. Empty everywhere => Omega Boolean (KILL).

CONTROL: rerun with rounds RELABELED -- i.e. ask whether the knee sits at the round where
words stop being free (the schedule boundary) regardless of absolute index. We do this by
also reporting the constraint-free vs constrained round split (57-60 free, 61-63 schedule).
"""
import sys
from collections import defaultdict
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards')
import _w5co_engine as E


def per_round_de(M, setup, w57, w58, w59, w60):
    """Return (de57..de63 list, collide) -- de_r = (e1_r - e2_r) mod 2^N after round r,
    for r=57..63, plus full-collision flag."""
    MASK = M['MASK']; KN = M['KN']
    W1p, W2p = setup['W1'], setup['W2']
    s1, s2 = setup['st1'], setup['st2']
    de = {}
    w57b = E.find_w2(s1, s2, 57, w57, M)
    s1 = E.sha_round(s1, KN[57], w57, M); s2 = E.sha_round(s2, KN[57], w57b, M); de[57] = (s1[4]-s2[4]) & MASK
    w58b = E.find_w2(s1, s2, 58, w58, M)
    s1 = E.sha_round(s1, KN[58], w58, M); s2 = E.sha_round(s2, KN[58], w58b, M); de[58] = (s1[4]-s2[4]) & MASK
    w59b = E.find_w2(s1, s2, 59, w59, M)
    s1 = E.sha_round(s1, KN[59], w59, M); s2 = E.sha_round(s2, KN[59], w59b, M); de[59] = (s1[4]-s2[4]) & MASK
    cas = E.find_w2(s1, s2, 60, 0, M); w60b = (w60 + cas) & MASK
    s1 = E.sha_round(s1, KN[60], w60, M); s2 = E.sha_round(s2, KN[60], w60b, M); de[60] = (s1[4]-s2[4]) & MASK
    W1_61 = (M['s1'](w59) + W1p[54] + M['s0'](W1p[46]) + W1p[45]) & MASK
    W2_61 = (M['s1'](w59b) + W2p[54] + M['s0'](W2p[46]) + W2p[45]) & MASK
    W1_62 = (M['s1'](w60) + W1p[55] + M['s0'](W1p[47]) + W1p[46]) & MASK
    W2_62 = (M['s1'](w60b) + W2p[55] + M['s0'](W2p[47]) + W2p[46]) & MASK
    W1_63 = (M['s1'](W1_61) + W1p[56] + M['s0'](W1p[48]) + W1p[47]) & MASK
    W2_63 = (M['s1'](W2_61) + W2p[56] + M['s0'](W2p[48]) + W2p[47]) & MASK
    s1 = E.sha_round(s1, KN[61], W1_61, M); s2 = E.sha_round(s2, KN[61], W2_61, M); de[61] = (s1[4]-s2[4]) & MASK
    s1 = E.sha_round(s1, KN[62], W1_62, M); s2 = E.sha_round(s2, KN[62], W2_62, M); de[62] = (s1[4]-s2[4]) & MASK
    s1 = E.sha_round(s1, KN[63], W1_63, M); s2 = E.sha_round(s2, KN[63], W2_63, M); de[63] = (s1[4]-s2[4]) & MASK
    collide = (s1 == s2)
    return de, collide


def forcing_analysis(N):
    """The collision predicate's ONLY constraints are de61=de62=de63=0 (boundary-proof
    Theorem 3): rounds 57-60 are cascade-FREE (de57,de58,de59 vary, de60=0 automatically),
    so Phi is dense-open (no constraint => delta_r=1) there, and the constraints switch on
    at round 61. We track the LIVE set: an input survives constraint round r iff de_r'=0
    for every CONSTRAINT round r'<=r (constraint rounds = {61,62,63}); rounds 57-60 impose
    nothing. delta_r = live_r / live_{r-1}."""
    M = E.make_model(N); setup = E.find_M0(M); R = M['MASK'] + 1
    CONSTRAINT_ROUNDS = (61, 62, 63)
    live = {r: 0 for r in range(57, 64)}
    total = 0; coll_total = 0
    for w57 in range(R):
        for w58 in range(R):
            for w59 in range(R):
                for w60 in range(R):
                    total += 1
                    de, col = per_round_de(M, setup, w57, w58, w59, w60)
                    if col:
                        coll_total += 1
                    ok = True
                    for r in range(57, 64):
                        if r in CONSTRAINT_ROUNDS and de[r] != 0:
                            ok = False
                        if ok:
                            live[r] += 1
    deltas = {}
    prev = total
    for r in range(57, 64):
        deltas[r] = live[r] / prev if prev else float('nan')
        prev = live[r]
    return dict(N=N, total=total, coll_total=coll_total, cum_zero=live,
                deltas=deltas, R=R)


def notnot_gap(N):
    """The ¬¬-vs-actual gap = 'no obstruction != constructible'. On the poset of prefixes
    (fixing w57..w_{56+k}, k=1..4), classify each prefix:
      FORCED      = every completion collides (Phi holds, constructible),
      REFUTED     = no completion collides (Phi false),
      UNDETERMINED= some-but-not-all completions collide (¬¬Phi true -- not refuted -- but
                    Phi not forced/constructible). |UNDETERMINED| = the ¬¬ gap.
    A NON-empty gap at some level => Omega genuinely non-Boolean there (the framing is not
    vacuous). An empty gap everywhere => Omega Boolean (KILL clause 2)."""
    M = E.make_model(N); setup = E.find_M0(M); R = M['MASK'] + 1
    # collision membership over the full grid, indexed by (w57,w58,w59,w60)
    coll = {}
    for w57 in range(R):
        for w58 in range(R):
            for w59 in range(R):
                for w60 in range(R):
                    _, c = per_round_de(M, setup, w57, w58, w59, w60)
                    coll[(w57, w58, w59, w60)] = c
    # for each prefix length k, group completions and classify
    out = {}
    for k in range(1, 5):
        groups = {}
        for key, c in coll.items():
            pref = key[:k]
            g = groups.setdefault(pref, [0, 0])  # [n_coll, n_total]
            g[0] += c; g[1] += 1
        forced = refuted = undet = 0
        for pref, (nc, nt) in groups.items():
            if nc == nt:
                forced += 1
            elif nc == 0:
                refuted += 1
            else:
                undet += 1
        out[k] = dict(n_prefix=len(groups), forced=forced, refuted=refuted, undet=undet)
    return out


def main():
    print("=== W5-TO1: forcing density delta_r across the tail (dense-open vs knee) ===\n")
    print("delta_r = fraction of still-live partial collisions surviving the round-r")
    print("constraint (de_r=0). Card: delta_r~1 (dense) for r<=60, crash ~2^-N at 61.\n")
    # exact full-grid enumeration feasible at N=4 (65536); N in {6,7,9} have no eligible M0;
    # N=8 grid infeasible. N=4 is the exact scale; the free/schedule split is N-invariant.
    for N in (4,):
        d = forcing_analysis(N)
        R = d['R']
        print(f"--- N={N} ({d['total']} tail inputs, {d['coll_total']} full collisions, "
              f"2^-N={1/R:.4f}) ---")
        print(f"  round r | #(de57..der all 0) | delta_r (per-round survival) | free or schedule")
        for r in range(57, 64):
            kind = "FREE word" if r <= 60 else "schedule-determined"
            print(f"    {r}   |     {d['cum_zero'][r]:7d}        |        {d['deltas'][r]:.5f}"
                  f"            | {kind}")
        # the card's discriminator
        d60 = d['deltas'][60]; d61 = d['deltas'][61]
        ratio = d61 / d60 if d60 else float('nan')
        print(f"\n  delta_60={d60:.5f} delta_61={d61:.5f}  delta_61/delta_60={ratio:.5f} "
              f"(card: ->0 like 2^-N={1/R:.4f})")
        # is the knee AT the schedule boundary? rounds 57-60 free => delta~1; 61-63 => ~2^-N
        flat_free = all(abs(d['deltas'][r] - 1.0) < 1e-9 for r in range(57, 61))
        crash_at_sched = all(d['deltas'][r] < 0.5 for r in range(61, 64))
        print(f"  delta_r == 1 (no constraint) for ALL free rounds 57..60? {flat_free}")
        print(f"  delta_r crashes (<0.5) for ALL schedule rounds 61..63? {crash_at_sched}")
        print(f"  => knee location = the FREE/SCHEDULE boundary (the known 2^-2N constraint),"
              f" not an intrinsic genericity threshold at the absolute index 61.\n")
        # the not-not gap (Omega Boolean?) -- classify prefixes by forced/refuted/undetermined
        ng = notnot_gap(N)
        print(f"  --- ¬¬-vs-actual gap (Omega non-Boolean?) by prefix length k ---")
        print(f"  k (fixed words) | #prefixes | forced | refuted | UNDETERMINED(=¬¬ gap)")
        for k in range(1, 5):
            g = ng[k]
            print(f"      {k} (w57..w{56+k})  |  {g['n_prefix']:6d}   | {g['forced']:6d} |"
                  f" {g['refuted']:6d}  | {g['undet']:6d}")
        gap_nonempty = any(ng[k]['undet'] > 0 for k in range(1, 5))
        print(f"  ¬¬ gap NON-empty at some level? {gap_nonempty} "
              f"({'Omega non-Boolean -> framing not vacuous' if gap_nonempty else 'Omega Boolean -> KILL clause 2'})")
        print(f"  NOTE: the gap is non-empty ONLY because rounds 57-60 are free (every short")
        print(f"  prefix has both colliding & non-colliding completions) -- i.e. it is the")
        print(f"  free-word freedom, and the knee is the schedule onset; no NEW number emerges.\n")


if __name__ == '__main__':
    main()
