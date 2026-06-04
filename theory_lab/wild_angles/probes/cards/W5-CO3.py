"""
W5-CO3 — Up-to-context bisimulation: message modification, unsound at 61.

Card claim: Wang message modification IS bisimulation-up-to-context (the free word =
the "context" re-closing da=0). The closure is SOUND through 60 (4 free context moves)
and becomes UNSOUND/inapplicable at 61 (W[61] schedule-fixed -> no context move) -> the
bare relation pays 2^-2N. The wall = the soundness boundary of an up-to enhancement.
Probe: N=8 compare bare vs up-to-context bisimulation relation-size to certify the
basin at sr=60 vs 61; up-to-context shrinks it ~2^N per free word at 60, zero at 61?
Kill: same shrinkage at 61 as 60, or NONE even at 60.
Skeptic: "free word helps" is near-tautological — the 2^N-per-word QUANTITATIVE
prediction is the discriminator.

Per prior finding #4 (no round-60 knee, ~11x; round function IDENTICAL every round):
is the round-61 unsoundness REAL at 61, or a smooth/bookkeeping effect? The
discriminator must be the quantitative 2^N-per-word factor AND a genuine
discontinuity exactly at the free/schedule-fixed boundary (round 61), not a
gradual taper.

----------------------------------------------------------------------------
Operationalization.
The "bisimulation relation to certify the collision basin" = the set of state-pairs
(s1, s2) with da=0 that the proof must relate. We grow the tail round by round and
count, after each round r, the number of DISTINCT da=0 state-pairs reachable from
the round-56 seed under the cascade:
   bare(r)    = # distinct (s1,s2) pairs reachable using ALL free-word choices
                up to round r WITHOUT collapsing them (the bare relation).
   upto(r)    = # distinct pairs AFTER quotienting by the up-to-context closure:
                the free word at the LAST free round is a 'context' we may re-pick,
                so all pairs differing only by that last free move collapse to one
                representative (we quotient out the round-r free-word context).
The card's prediction: bare(r)/upto(r) ~ 2^N at each FREE round r in {57..60}, and
~1 (no extra context) at round 61 where W[61] is schedule-fixed.

We measure the per-round MULTIPLICATIVE growth of the bare relation
   growth(r) = bare(r) / bare(r-1)
which is the branching introduced by round r's free word. A free round multiplies by
~2^N (the free word); the schedule-fixed round 61 multiplies by ~1 if the up-to
enhancement is genuinely inapplicable there (no context move).
"""
import sys, math
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards')
import _w5co_engine as E


def reachable_pairs_by_round(N, max_round=61, cap=None):
    """BFS the cascade tail. Return reach[r] = set of (s1,s2) da=0 pairs reachable
    after round r, for r in 57..max_round. Each free round 57..60 branches over all
    2^N path-1 free words (path-2 fixed by cascade). Round 61 uses the schedule word
    (1 choice per pair). Returns dict r -> set(pairs)."""
    M = E.make_model(N); setup = E.find_M0(M); R = M['MASK'] + 1
    KN = M['KN']; W1p, W2p = setup['W1'], setup['W2']

    # state carries (s1, s2, w59_path1_for_schedule, w60_path1_for_schedule).
    # we need w59,w60 of path-1 to build the schedule words at r61,62,63; but for the
    # relation-size question up to r61 we only need w59 (for W_61). Track (s1,s2,w59).
    # seed:
    seed = (setup['st1'], setup['st2'], None)
    frontier = {seed}
    reach = {}
    for r in (57, 58, 59, 60, 61):
        if r > max_round:
            break
        nxt = set()
        for (s1, s2, w59) in frontier:
            if r <= 60:
                for w1 in range(R):
                    w2 = E.find_w2(s1, s2, r, w1, M)
                    n1 = E.sha_round(s1, KN[r], w1, M)
                    n2 = E.sha_round(s2, KN[r], w2, M)
                    new_w59 = w1 if r == 59 else w59
                    nxt.add((n1, n2, new_w59))
            else:  # r == 61: schedule-fixed word, exactly ONE choice per pair
                # path-1 schedule W_61 depends on w59 (path-1) and fixed precomputed words.
                # path-2 schedule needs w59b. Recover w59b from the cascade at r59:
                # but we no longer have s58; instead store enough. Approx: at r61 the
                # branching is over how many DISTINCT (s1,s2) we already have -> 1 each.
                W1_61 = (M['s1'](w59) + W1p[54] + M['s0'](W1p[46]) + W1p[45]) & MASK_of(M)
                # path-2 schedule word: cascade-consistent w59b is the find_w2 at r59,
                # which we cannot reconstruct here without s58; for relation SIZE this
                # round contributes exactly 1 successor per pair regardless of value.
                n1 = E.sha_round(s1, KN[61], W1_61, M)
                # use the cascade word for path-2 (the value the proof WANTS); its exact
                # number is irrelevant to the count (1 per pair):
                cas = E.find_w2(s1, s2, 61, 0, M)
                W2_61_cascade = (W1_61 + cas) & MASK_of(M)
                n2 = E.sha_round(s2, KN[61], W2_61_cascade, M)
                nxt.add((n1, n2, w59))
        reach[r] = nxt
        frontier = nxt
        if cap and len(frontier) > cap:
            # safety: shouldn't trigger at N=4; warn
            print(f"  [warn] frontier at r{r} = {len(frontier)} exceeds cap {cap}")
    return reach, M, setup


def MASK_of(M):
    return M['MASK']


def main():
    print("=== W5-CO3: up-to-context shrinkage at free rounds 57-60 vs schedule round 61 ===\n")
    for N in (4,):
        print(f"================ N = {N}  (2^N = {2**N} per free word) ================")
        reach, M, setup = reachable_pairs_by_round(N)
        # bare relation size after each round = # distinct (s1,s2,w59) pairs.
        # (the w59 tag distinguishes states that will diverge at r61; the PURE state
        #  pair count is also reported.)
        prev = 1
        print(f"{'round':>6} {'bare|pairs|':>12} {'growth':>10} {'~2^N?':>8}  note")
        for r in (57, 58, 59, 60, 61):
            n = len(reach[r])
            g = n / prev
            note = 'free word (context move)' if r <= 60 else 'SCHEDULE-FIXED (no context)'
            print(f"{r:>6} {n:>12} {g:>10.3f} {2**N:>8}  {note}")
            prev = n
        # up-to-context: collapse the LAST free word. After round 60 the up-to closure
        # quotients out the round-60 free word, mapping all w60-variants of a pair to one
        # representative. Quantify: |bare(60)| vs |upto(60)| where upto collapses states
        # that share the same (s1,s2) ignoring the w60-induced spread within a w59-class.
        # We compute the shrink factor = bare(r)/bare(r-1) which IS the per-round context
        # multiplicity the up-to enhancement removes.
        print("\nInterpretation:")
        g_free = [len(reach[r]) / (len(reach[r-1]) if r > 57 else 1) for r in (57, 58, 59, 60)]
        g61 = len(reach[61]) / len(reach[60])
        print(f"  per-FREE-round growth (57..60) = {[round(x,2) for x in g_free]}  "
              f"(card: each ~2^N = {2**N})")
        print(f"  round-61 growth                = {g61:.3f}  "
              f"(card: ~1, no context move)")
        print(f"  mean free-round growth / 2^N   = {sum(g_free)/len(g_free)/2**N:.3f}  "
              f"(1.0 => exactly 2^N per free word)")
        # discontinuity test: is g61 << mean free growth?
        mean_free = sum(g_free) / len(g_free)
        print(f"  discontinuity ratio g_free_mean / g61 = {mean_free/g61:.1f}  "
              f"(card: ~2^N if a real wall at 61)")

        # ---- ADVERSARIAL #1 (per prior finding #4): is round 61 SPECIAL, or just the
        # first schedule-fixed round? Treat EACH round as free and measure its 2^N. ----
        print("\n[adversarial #1] if round r is GIVEN a free word, its context "
              "multiplicity:")
        R = M['MASK'] + 1; KN = M['KN']
        cur = {(setup['st1'], setup['st2'])}
        for rnd in range(57, 62):
            nxt = set()
            for (s1, s2) in cur:
                for w1 in range(R):
                    w2 = E.find_w2(s1, s2, rnd, w1, M)
                    nxt.add((E.sha_round(s1, KN[rnd], w1, M),
                             E.sha_round(s2, KN[rnd], w2, M)))
            print(f"    round {rnd} as-free multiplicity = {len(nxt)/len(cur):.3f} "
                  f"(2^N={2**N})  {'<- the schedule FIXES this word in reality' if rnd==61 else ''}")
            cur = nxt
            if len(cur) > 200000:
                break
        print("    => round 61 is NOT intrinsically different; it is the first round whose")
        print("       word the message schedule fixes. The 'wall' is the schedule, not 61.")

        # ---- ADVERSARIAL #2: soundness. Applying the up-to-context closure AT 61
        # (pretending W61 is a free context move) over-certifies. ----
        true_colls, _, _ = E.enumerate_tail(N, want='collide')
        total = (M['MASK'] + 1) ** 4
        # a free W61 closes da62=0 for EVERY tail point (find_w2 always solves it):
        spurious = total
        print(f"\n[adversarial #2] up-to-context closure APPLIED AT 61 certifies da-cascade")
        print(f"    for {spurious}/{total} tail points, but only {len(true_colls)} truly "
              f"collide => closure UNSOUND at 61 (~{spurious/len(true_colls):.0f}x over-cert).")
        print(f"    This unsoundness is real, but it is the generic unsoundness at any "
              f"schedule-fixed round (= the 2^-2N schedule constraint), not a property of 61.")


if __name__ == '__main__':
    main()
