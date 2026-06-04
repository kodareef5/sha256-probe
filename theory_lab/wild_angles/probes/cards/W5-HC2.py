"""
W5-HC2 — Sunflower core: the 132 as the bits common to all collisions.

CARD CLAIM (CATALOG):
  The Sunflower Lemma forces a common core; conjecture the 132 hard-core bits =
  the carry-difference core shared by ~all collisions (petals = the free 124).
  Anchored to the measured 42% carry-invariance (0.42*256 ~= 108, a near-miss to 132).
PROBE (CATALOG):
  N=8,10,12 intersect all collisions' carry-diff supports (= empirical core); is it a
  stable fraction -> 132/256? are residual petals low-overlap (disjoint-ish)?
KILL:
  core fraction unstable across N, petals high-overlap, OR extrapolated core misses
  132/256 by >15%.

PRIOR FINDING #1 (category error, 11x): "132" = the deterministic-control census =
  4 nonlinearly-mixed registers (a,b,e,f) + 4 dc @ round 63, which tracks WORD WIDTH
  (4N+4), NOT a basis-independent invariant. The 132 comes from a SINGLE-BIT-FLIP
  sensitivity matrix (hard_core_132_bits.md), NOT from the collision family.
  -> TEST: do the "bits common to all collisions" actually = {a,b,e,f}@63 + 4dc, and
     is the count a stable 132 or width-scaling (4N+4)? Is it a genuine sunflower CORE
     or the census re-counted?

WHAT THIS PROBE DOES — three precise readings of "the bits common to all collisions",
each over the EXACT collision family at N=4,8,10:

  (R1) FORCED OUTPUT BITS: across all collisions, which of the 256 hash bits
       (registers a..h @ round 63, 32-bit each = 8N bits at width N) take the SAME
       value in every collision?  (the literal "bits common to all collisions").
       Compare count, support, and N-scaling to 132 and to {a,b,e,f}.
  (R2) COMMON INTERNAL-DIFFERENCE CORE (the card's "carry-difference core"): over the
       per-round modular-difference trace (rounds 57..62; r63 is all-zero by collision),
       which (round,register,bit) positions are NONZERO in EVERY collision (= core),
       which VARY (= petals)? Measure petal pairwise overlap (disjoint-ish?).
  (R3) FORCED FREE-INPUT BITS: which of the 4N free message bits (w57..w60) are
       constant across all collisions?  (the "sunflower core" in the natural domain.)

  Then adjudicate vs the card's 132/256 = 0.516 fraction and the {a,b,e,f}+4dc claim,
  and apply the kill_criterion.
"""
import sys, math
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards')
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import _hc_family as F
import _w5co_engine as E
import shabridge as sb

REG = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']


def final_states(fam):
    """Recompute each collision's final 8-register state (path-1 == path-2 since collide)."""
    M, setup = fam['M'], fam['setup']
    states = []
    for w in fam['tuples']:
        # replay path-1 to round 63
        KN = M['KN']; W1p = setup['W1']; MASK = M['MASK']
        s1 = setup['st1']
        w57, w58, w59, w60 = w
        s1 = E.sha_round(s1, KN[57], w57, M)
        s1 = E.sha_round(s1, KN[58], w58, M)
        s1 = E.sha_round(s1, KN[59], w59, M)
        s1 = E.sha_round(s1, KN[60], w60, M)
        W1_61 = (M['s1'](w59) + W1p[54] + M['s0'](W1p[46]) + W1p[45]) & MASK
        W1_62 = (M['s1'](w60) + W1p[55] + M['s0'](W1p[47]) + W1p[46]) & MASK
        W1_63 = (M['s1'](W1_61) + W1p[56] + M['s0'](W1p[48]) + W1p[47]) & MASK
        s1 = E.sha_round(s1, KN[61], W1_61, M)
        s1 = E.sha_round(s1, KN[62], W1_62, M)
        s1 = E.sha_round(s1, KN[63], W1_63, M)
        states.append(s1)
    return states


def forced_output_bits(fam):
    """R1: which (register,bit) of the final hash are constant across all collisions?"""
    N = fam['N']
    states = final_states(fam)
    forced = {}            # (reg_idx, bit) -> the constant value
    for ri in range(8):
        for b in range(N):
            vals = {(s[ri] >> b) & 1 for s in states}
            if len(vals) == 1:
                forced[(ri, b)] = vals.pop()
    return forced, len(states)


def common_diff_core(fam):
    """R2: over rounds 57..62 diff-trace, which (round,reg,bit) is NONZERO in EVERY
    collision (core) and which varies (petal). Returns (core_set, petal_set)."""
    N = fam['N']
    traces = fam['traces']
    positions = [(r, ri, b) for r in range(57, 63) for ri in range(8) for b in range(N)]
    core, petal = set(), set()
    for (r, ri, b) in positions:
        bits = [(t[r][ri] >> b) & 1 for t in traces]
        if all(bits):
            core.add((r, ri, b))
        elif any(bits):
            petal.add((r, ri, b))
    return core, petal


def forced_input_bits(fam):
    """R3: which of the 4N free message bits are constant across all collisions?"""
    N = fam['N']
    forced = {}
    for k in range(4 * N):
        vals = {(bv >> k) & 1 for bv in fam['bitvecs']}
        if len(vals) == 1:
            forced[k] = vals.pop()
    return forced


def petal_overlap(fam, petal):
    """Mean pairwise Jaccard overlap of petal supports across collisions (disjoint-ish=>~0)."""
    if not petal:
        return None
    traces = fam['traces']
    plist = sorted(petal)
    supports = []
    for t in traces:
        s = frozenset((r, ri, b) for (r, ri, b) in plist if (t[r][ri] >> b) & 1)
        supports.append(s)
    import random
    random.seed(0)
    pairs = 0; tot = 0.0
    idx = list(range(len(supports)))
    sample = idx if len(idx) <= 60 else random.sample(idx, 60)
    for i in range(len(sample)):
        for j in range(i + 1, len(sample)):
            A, B = supports[sample[i]], supports[sample[j]]
            if not A and not B:
                continue
            jac = len(A & B) / max(1, len(A | B))
            tot += jac; pairs += 1
    return tot / pairs if pairs else None


def main():
    print("# W5-HC2 — is the '132' the bits common to all collisions (a sunflower core)?")
    print("# Card: core = 132/256 = 0.516 = {a,b,e,f}@63 + 4dc; petals = free 124.")
    print("# Prior #1: 132 is the single-bit-flip CONTROL CENSUS (4N+4), not a collision-set core.\n")

    for N in (4, 8, 10):
        fam = F.load_family(N, with_trace=True)
        tot8 = 8 * N      # bits in the full 8-register state
        nc = fam['count']
        print(f"===== N={N}  ({nc} collisions; full state = 8N = {tot8} bits) =====")

        # R1
        forced_out, _ = forced_output_bits(fam)
        by_reg = {ri: sum(1 for (r, b) in forced_out if r == ri) for ri in range(8)}
        nfo = len(forced_out)
        print(f"[R1 forced OUTPUT bits] {nfo}/{tot8} hash bits constant across all collisions"
              f"  ({nfo/tot8:.3f} of state)")
        print(f"     per-register (a..h): "
              + ' '.join(f"{REG[ri]}={by_reg[ri]}" for ri in range(8)))

        # R2
        core, petal = common_diff_core(fam)
        ncore, npet = len(core), len(petal)
        core_reg = {}
        for (r, ri, b) in core:
            core_reg.setdefault(ri, 0)
            core_reg[ri] += 1
        print(f"[R2 common DIFF core] rounds57-62: core(nonzero in ALL)={ncore}, "
              f"petal(varies)={npet}  of {6*8*N} positions")
        if core:
            print(f"     core register spread: "
                  + ' '.join(f"{REG[ri]}={core_reg.get(ri,0)}" for ri in range(8)))
        ov = petal_overlap(fam, petal)
        print(f"     petal mean pairwise Jaccard overlap = "
              f"{ov:.3f}" if ov is not None else "     (no petals)")

        # R3
        forced_in = forced_input_bits(fam)
        print(f"[R3 forced INPUT bits] {len(forced_in)}/{4*N} free message bits constant "
              f"across all collisions")

        # adjudication vs 132 and {a,b,e,f}
        # {a,b,e,f} fully + 4 dc would be 4N + 4 at width N (the census scaling).
        census_pred = 4 * N + 4
        print(f"[vs CENSUS] 'a,b,e,f fully + 4dc' at width N would be 4N+4 = {census_pred}; "
              f"the literal 132 only at N=32.")
        # how close is R1 to 132/256 fraction?
        frac = nfo / tot8
        print(f"[vs CARD] R1 forced-output fraction {frac:.3f} vs card's 132/256=0.516; "
              f"R1 count {nfo} vs 132.")
        print()

    print("# ADJUDICATION:")
    print("#  - The '132' from hard_core_132_bits.md is a SINGLE-BIT-FLIP sensitivity census")
    print("#    (which output bits no input lever deterministically moves) = {a,b,e,f}@63+4dc,")
    print("#    scaling as ~4N+4 (=132 only at N=32). It is NOT computed from the collision set.")
    print("#  - The card asserts 132 = 'bits common to all collisions'. R1/R2/R3 measure that")
    print("#    literal object directly. Check: is it a STABLE 0.516 fraction, and is its count")
    print("#    132 (constant) or width-scaling? Does its support equal {a,b,e,f}?")


if __name__ == '__main__':
    main()
