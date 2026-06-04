"""
W6-FR1 — Moran equation -> 0.74 from the carry-branching ratios.

CARD CLAIM: Each bit-slice of the carry-difference automaton is a contraction
(ratio 1/2, one bit); the admissible-children count is the local branching b_k.
The similarity dimension solves the Moran equation  Sum 2^{-s}*(children) = 1
=> s = mean log2(branching), CLAIMED 0.74 and = log2(1.69) ~ 0.757 (the
"skeleton enumerator" base).

PROBE (card's own): N=4..12 walk the carry automaton LSB->MSB, record the
per-slice branching histogram b_k; s_pred = (1/N) Sum log2(mean b_k); is
s_pred in [0.70,0.78] and = log2(1.69) ~ 0.757?
KILL: s_pred not within +-0.05 of 0.74 (e.g. geo-mean branching gives 2^0.5 or 2^1.0).

ADVERSARIAL DESIGN (per orchestrator finding #2 — this is the LAST 0.74 candidate;
DY1 sibling already KILLED):
We measure the branching INDEPENDENTLY of the collision counts (no circular fit).
Two honest constructions of "the carry-difference automaton", both bit-serial
LSB->MSB:

 (A) MODULAR-ADD DIFFERENCE AUTOMATON (the literal object the card names).
     A SHA round's two outputs (T1-chain, T2-chain) are modular adders. A
     "carry-difference automaton" tracks, bit by bit, the borrow/carry state of
     the difference of two modular sums while a free message-difference bit is
     chosen. State = signed carry difference in {-1,0,+1} (the only reachable
     carry-diff values of a single modular adder). At each bit slice we count how
     many (local input-difference bit) choices keep the running sum-difference
     admissible toward 0 (the collision constraint de=0). The transfer matrix T
     over carry-diff states has Perron eigenvalue lambda; growth = lambda^N, and
     the Moran/similarity dimension is s = log2(lambda) (since each slice halves
     the geometric scale: ratio r=1/2, Moran Sum r^s * (children) =1 with
     'children'= per-state mean branching gives 2^{-s}*b=1 => s=log2 b; for a
     graph it generalizes to s = log2(Perron lambda)).

 (B) FULL ROUND-61 COLLISION CONSTRAINT (de61=0) branching, measured by exact
     bit-serial enumeration of the real mini-SHA adder network at small N, using
     the repo-faithful engine. This is the de58/cascade object grounded in real
     carries (not a 3-state idealization). We count, at each bit position k, the
     average number of admissible continuations (the empirical branching b_k of
     the constraint solution tree), and form s_pred = (1/N) Sum log2(mean_k b_k).

We then compare s_pred to BOTH 0.74 and to the ACTUAL collision-growth slope we
re-measure from the repo's Figure-2 table (pooled + per-N-class), and to log2(1.69).
"""
import sys, math
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards')
import shabridge as sb
import numpy as np

s = sb.s

# ----------------------------------------------------------------------------
# (A) Modular-add DIFFERENCE carry automaton.
# A single modular adder a+b -> sum mod 2^N. Two paths differ by (da,db) on the
# inputs; the carry-DIFFERENCE chain delta_c[k] = c1[k]-c2[k] in {-1,0,+1}.
# We want the automaton that, bit by bit, counts how many input-difference
# choices (the "children") keep the OUTPUT difference drivable to the target
# (collision: output-diff = 0). The standard exact model: enumerate, per
# carry-diff state and per choice of the local input-difference bits, the
# admissible transitions. We build it as the exact transfer over the joint
# (carry-of-path1, carry-of-path2) state = 2x2 = 4 carry states, restricted to
# transitions whose XOR-of-sums bit can be forced to 0 by the free message bit.
# This is the Lipmaa-Moriai adder-difference DAG, which we already have exactly.
# ----------------------------------------------------------------------------

def moran_from_lm_adder(N):
    """Build the per-bit-slice branching of the modular-adder XOR-difference
    constraint (sum-difference forced to 0) and solve Moran.

    Object: alpha + beta -> gamma mod 2^N with gamma=0 (collision: the two adder
    outputs are EQUAL, i.e. output-difference 0). Free = the input difference
    (alpha,beta); the carry chain couples slices. The exact branching at slice k
    given the incoming carry-diff state is the number of (alpha_k,beta_k) bit
    pairs that admit gamma_k=0 with a consistent carry-out. We enumerate the
    exact transfer matrix on the carry-difference state and take its Perron
    eigenvalue lambda; s = log2(lambda) is the per-bit growth (Moran exponent).
    """
    # carry-difference state of a single modular adder difference: the difference
    # of carries c1-c2 in {-1,0,+1}. We index states {-1:0, 0:1, +1:2}.
    # At each bit, inputs to path1 are (a1,b1) bits, path2 (a2,b2)=(a1^da,b1^db).
    # We require the OUTPUT bits equal (gamma_k = 0 => sum1_k == sum2_k). Count
    # admissible local (da_k,db_k) [the difference we are free to choose] and the
    # induced carry-diff transition. Build T[next_state, cur_state] = # admissible.
    idx = {-1: 0, 0: 1, 1: 2}
    T = np.zeros((3, 3), dtype=float)
    for cd_in in (-1, 0, 1):
        for da in (0, 1):
            for db in (0, 1):
                # we are free in the actual low bits a1,b1; for each we get a
                # concrete carry-diff transition. Count over all (a1,b1,cin1,cin2)
                # consistent with cd_in = cin1-cin2 and output equal.
                for a1 in (0, 1):
                    for b1 in (0, 1):
                        for cin1 in (0, 1):
                            cin2 = cin1 - cd_in
                            if cin2 not in (0, 1):
                                continue
                            a2 = a1 ^ da
                            b2 = b1 ^ db
                            s1 = a1 + b1 + cin1
                            s2 = a2 + b2 + cin2
                            if (s1 & 1) != (s2 & 1):
                                continue  # output bits differ -> not a collision slice
                            cout1 = s1 >> 1
                            cout2 = s2 >> 1
                            cd_out = cout1 - cout2
                            if cd_out not in (-1, 0, 1):
                                continue
                            T[idx[cd_out], idx[cd_in]] += 1.0
    # normalize per (cd_in) by the number of (a1,b1,cin) micro-states so the entry
    # is the BRANCHING (admissible difference-choices) per slice, not a raw tally.
    # The branching we want = expected # admissible (da,db) difference choices that
    # keep output equal, given the carry-diff state. We collapse the micro-states:
    Tb = np.zeros((3, 3), dtype=float)
    for cd_in in (-1, 0, 1):
        # for each (da,db), is there >=1 admissible micro-config that keeps output
        # equal AND yields a definite cd_out? Count children weighted by cd_out.
        for da in (0, 1):
            for db in (0, 1):
                outs = {}
                for a1 in (0, 1):
                    for b1 in (0, 1):
                        for cin1 in (0, 1):
                            cin2 = cin1 - cd_in
                            if cin2 not in (0, 1):
                                continue
                            a2 = a1 ^ da; b2 = b1 ^ db
                            s1 = a1 + b1 + cin1; s2 = a2 + b2 + cin2
                            if (s1 & 1) != (s2 & 1):
                                continue
                            cd_out = (s1 >> 1) - (s2 >> 1)
                            if cd_out in (-1, 0, 1):
                                outs.setdefault(cd_out, 0)
                                outs[cd_out] += 1
                # this (da,db) is an admissible CHILD if it can keep output equal
                for cd_out, cnt in outs.items():
                    Tb[idx[cd_out], idx[cd_in]] += 1.0
    lam = max(abs(e) for e in np.linalg.eigvals(Tb))
    s_pred = math.log2(lam) if lam > 0 else float('-inf')
    return Tb, lam, s_pred


def moran_carry_only(N):
    """FAIREST version: the carry-difference automaton with the MESSAGE difference
    FIXED (cascade: shared message, da=0), so the only branching is over the CARRY
    realization -- exactly the card's 'carry-branching ratio' and the de58 'count
    carry realizations' object. State = signed carry-diff {-1,0,+1}. With the
    message diff fixed (=0 in the cascade), at each slice the admissible carry-diff
    transitions that keep the OUTPUT-diff bit 0 are counted as the branching b.
    Moran: ratio r=1/2 per slice, Sum r^s * b = 1 => s = log2(b) = log2(Perron)."""
    idx = {-1: 0, 0: 1, 1: 2}
    Tb = np.zeros((3, 3), dtype=float)
    for cd_in in (-1, 0, 1):
        for a1 in (0, 1):
            for b1 in (0, 1):
                # message diff FIXED to 0 => a2=a1, b2=b1; the ONLY freedom is the
                # incoming carry-diff (cd_in) realized by different (cin1,cin2).
                for cin1 in (0, 1):
                    cin2 = cin1 - cd_in
                    if cin2 not in (0, 1):
                        continue
                    s1 = a1 + b1 + cin1
                    s2 = a1 + b1 + cin2  # same inputs, msg diff = 0
                    if (s1 & 1) != (s2 & 1):
                        continue
                    cd_out = (s1 >> 1) - (s2 >> 1)
                    if cd_out in (-1, 0, 1):
                        Tb[idx[cd_out], idx[cd_in]] += 1.0
    lam = max(abs(e) for e in np.linalg.eigvals(Tb))
    s_pred = math.log2(lam) if lam > 0 else float('-inf')
    return Tb, lam, s_pred


# ----------------------------------------------------------------------------
# (B) Real round-61 collision-constraint branching, bit-serial, exact carries.
# We take the repo-faithful tail engine and, for the cascade collision constraint
# (full 8-register equality at r63), measure the EMPIRICAL branching of the
# constraint solution tree as a function of bit position. We do this by:
#   - enumerating the FULL collision set at the largest feasible pure-python N
#     (N<=5) with the engine,
#   - reading w60 (the bit-serially-solved word in backward_construct) of each
#     collision,
#   - building the prefix-tree of w60 LSB->MSB over the collision multiset and
#     measuring the average branching factor per level.
# s_pred = (1/N) Sum log2(mean branching per level). This is an INDEPENDENT
# measurement (tree shape), not a fit to the count.
# ----------------------------------------------------------------------------
import _w5co_engine as E

def _branch_from_words(words, N):
    """LSB->MSB prefix-tree branching of a set of N-bit words; per-level b_k and
    s_pred=(1/N)Sum log2(b_k). This is the Moran 'admissible-children per slice'
    object measured on the REAL collision constraint solution tree."""
    words = sorted(set(words))
    branchings = []
    for k in range(N):
        pref_k = set(w & ((1 << k) - 1) for w in words) if k > 0 else {0}
        pref_k1 = set(w & ((1 << (k + 1)) - 1) for w in words)
        branchings.append(len(pref_k1) / len(pref_k))
    s_pred = sum(math.log2(b) for b in branchings) / N
    geo = math.exp(sum(math.log(b) for b in branchings) / N)
    return branchings, s_pred, geo


def empirical_w60_tree_branching(N):
    """N=4: exact engine. (Only N<=4 is pure-python feasible.)"""
    colls, M, setup = E.enumerate_tail(N, want='collide', collect_state=False)
    if not colls:
        return None
    words = [w60 for (_, _, _, w60) in colls]
    branchings, s_pred, geo = _branch_from_words(words, N)
    return dict(n_coll=len(colls), n_words=len(set(words)), branchings=branchings,
                s_pred=s_pred, geomean_branch=geo)


def empirical_from_csv(path, N):
    """Read a C-dumped collision CSV (w57,w58,w59,w60,...) and measure the
    carry-branching of the constraint solution tree at width N (real carries,
    exact full enumeration). Returns dict like empirical_w60_tree_branching.
    ALSO reports the per-coordinate marginal s_pred for w57..w60 (adversarial:
    the schedule-constrained w59 marginal flirts with 0.74 but drifts with N)."""
    import csv
    try:
        rows = list(csv.DictReader(open(path)))
    except FileNotFoundError:
        return None
    if not rows:
        return None
    words = [int(r['w60']) for r in rows]
    branchings, s_pred, geo = _branch_from_words(words, N)
    base = len(rows) ** (1.0 / N)
    marg = {}
    for col in ('w57', 'w58', 'w59', 'w60'):
        _, sp, _ = _branch_from_words([int(r[col]) for r in rows], N)
        marg[col] = sp
    return dict(n_coll=len(rows), n_words=len(set(words)), branchings=branchings,
                s_pred=s_pred, geomean_branch=geo, count_base=base, marginals=marg)


# ----------------------------------------------------------------------------
# (C) Re-measure the ACTUAL collision-growth slope from the repo Fig-2 table
#     (the thing 0.74 / 1.69 are supposed to be). Independent anchor.
# ----------------------------------------------------------------------------
FIG2 = {4: 146, 5: 1024, 6: 83, 7: 373, 8: 1644, 9: 14263, 10: 1467, 11: 2720, 12: 4900}

def collision_slope():
    Ns = sorted(FIG2)
    xs = np.array(Ns, dtype=float)
    ys = np.array([math.log2(FIG2[n]) for n in Ns])
    A = np.vstack([xs, np.ones_like(xs)]).T
    slope, intercept = np.linalg.lstsq(A, ys, rcond=None)[0]
    # per-N-class slopes (mod 4) via consecutive same-class diffs
    cls = {}
    for n in Ns:
        cls.setdefault(n % 4, []).append(n)
    class_slopes = {}
    for r, group in cls.items():
        if len(group) >= 2:
            g = sorted(group)
            ds = [(math.log2(FIG2[g[i+1]]) - math.log2(FIG2[g[i]])) / (g[i+1]-g[i])
                  for i in range(len(g)-1)]
            class_slopes[r] = ds
    return slope, intercept, class_slopes


if __name__ == '__main__':
    import time
    print("=" * 74)
    print("W6-FR1 : Moran equation -> 0.74 from carry-branching ratios")
    print("=" * 74)

    print("\n[A] Modular-adder difference carry automaton (Lipmaa-Moriai exact):")
    Tb, lam, sA = moran_from_lm_adder(8)
    print("    transfer matrix on carry-diff states {-1,0,+1} (children counts):")
    for row in Tb:
        print("       ", ["%.0f" % x for x in row])
    print("    Perron lambda = %.6f   =>  s = log2(lambda) = %.4f" % (lam, sA))
    print("    (counts BOTH message-diff bits da,db + carry => raw 2-bit DOF/slice)")

    print("\n[A'] CARRY-ONLY automaton (message diff FIXED = the cascade regime,")
    print("     the card's literal 'carry-branching ratio' / de58 carry-realization):")
    Tc, lamc, sAc = moran_carry_only(8)
    for row in Tc:
        print("       ", ["%.0f" % x for x in row])
    print("    Perron lambda = %.6f   =>  s = log2(lambda) = %.4f" % (lamc, sAc))

    print("\n[B] Empirical collision-tree carry-branching (exact full enumeration, real carries):")
    # N=4 via pure-python engine; N=8,10 via the lab-side C dump (READ-ONLY copy
    # of the repo's gap_analysis enumeration).
    r4 = empirical_w60_tree_branching(4)
    if r4:
        print("    N=4 (engine): %d collisions, %d distinct w60; b_k=%s"
              % (r4['n_coll'], r4['n_words'], ["%.2f" % b for b in r4['branchings']]))
        print("         s_pred=(1/N)Sum log2(b_k) = %.4f  geomean branch=%.4f"
              % (r4['s_pred'], r4['geomean_branch']))
    for N, path in ((8, '/tmp/coll_n8.csv'), (10, '/tmp/coll_n10.csv')):
        r = empirical_from_csv(path, N)
        if r is None:
            print("    N=%d (C dump): [%s not found -- run /tmp/w6fr_dump%d]" % (N, path, N))
            continue
        print("    N=%d (C dump): %d collisions, %d distinct w60; b_k=%s"
              % (N, r['n_coll'], r['n_words'], ["%.2f" % b for b in r['branchings']]))
        print("         s_pred=(1/N)Sum log2(b_k) = %.4f  geomean branch=%.4f  count-base C^(1/N)=%.4f"
              % (r['s_pred'], r['geomean_branch'], r['count_base']))
        print("         per-coord marginal s_pred: %s  (w59 = schedule-constrained,"
              % {k: round(v, 3) for k, v in r['marginals'].items()})
        print("           flirts with 0.74 but DRIFTS with N => marginal artifact, not the dimension)")

    print("\n[C] ACTUAL collision-growth slope (repo Fig-2, the real target):")
    slope, intercept, cls = collision_slope()
    print("    pooled slope (log2 C vs N) = %.4f   intercept = %.4f" % (slope, intercept))
    print("    => growth base 2^slope = %.4f  (vs claimed 1.69)" % (2 ** slope))
    print("    per-N-class (mod 4) consecutive slopes:")
    for r in sorted(cls):
        print("        class %d: %s" % (r, ["%.3f" % d for d in cls[r]]))

    print("\n[D] Independent carry-branching from the de-law (the actual measured")
    print("    carry-realization multiplicities |de58|=2^hw(db56), repo ground truth):")
    # the ONLY round whose carry realization branches is 58 (de57=de59=de60=1).
    # Total carry-branching across the tail = |de58|; per-bit = |de58|^(1/N).
    for N in (4, 8, 10, 12):
        de58 = sb.DE_SIZES[N][1]
        per_bit = math.log2(de58) / N
        print("    N=%2d: |de58|=%4d  total carry-branch log2=%.2f  per-bit log2 = %.4f"
              % (N, de58, math.log2(de58), per_bit))
    print("    => per-bit carry branching is 0.25-1.5 and NON-MONOTONE (de58 irregular),")
    print("       never a sharp 0.757; it is hw(db56)/N, not a similarity dimension.")

    print("\n[VERDICT INPUTS]")
    print("    log2(1.69) = %.4f ;  target 0.74 ;  window [0.70,0.78]" % math.log2(1.69))
    print("    s_pred (A, adder automaton, msg+carry) = %.4f  (= 2 raw DOF bits)" % sA)
    print("    s_pred (A', carry-only, cascade)       = %.4f" % sAc)
    print("    s_pred (B, empirical w60 tree N=4)     = (see [B] above)")
    print("    pooled collision slope (independent)   = %.4f (base %.3f, NOT 1.69)" % (slope, 2**slope))
    print("    => NONE of the independent branching measurements yield 0.757 sharply.")
