#!/usr/bin/env python3
"""
W8-WE2 -- Reverse-math calibration: WKL_0 at sr<=60, ACA_0 at sr=61.

CLAIM (CATALOG): sr<=60 existence = a WKL_0 fact (the cascade tree is extendible
at every node -- Thm2 de60=0 for ALL words -> Koenig gives a path, no
set-formation); sr=61 needs ACA_0 (you must *comprehend* the compatible-W[60] set
and intersect two independent ranges before choosing). The 3x ceiling = the
WKL-locality payoff.

PROBE (finite surrogate, per CATALOG): two witness-finders at small N --
  (A) a depth-first Koenig search: O(rounds) live-set (extend a partial path word
      by word; at each round pick the next free word, never materialize a set);
  (B) a comprehension search: materialize the compatible set (O(2^N) live-set),
      intersect two ranges, then choose.
Does the *minimal-memory successful* finder's peak live-set step from
O(1)-in-2^N (<=60) to Theta(2^N) at 61?

KILL_CRITERION: "the Koenig finder also certifies 61 with O(rounds) memory (still
WKL_0), or even <=60 needs comprehension (ladder placement wrong)."

ADVERSARIAL READING (prior finding #2): the repo says the wall is a counting/DOF
boundary, not a logical-strength jump. sr<=60 is the FREE cascade (enforcement:
set a free lever, depth-first, O(rounds)); sr=61 is ONE counting condition
(coincidence). The decisive question is whether sr=61 STILL admits a depth-first
*enforcement* of W[60]=sched (O(rounds) memory, no set) -- if it does, there is no
WKL->ACA jump and WE2 is KILLED/renamed. We test by running BOTH finders and
reporting the MINIMAL-memory finder that succeeds at each sr level.

This is a FINITE memory surrogate ONLY -- NOT a claim about literal provability
(reverse math needs infinite objects; a fixed-N collision has none). Stated as
witness-finder peak-live-set, per the card's explicit instruction.

Re-uses the repo cascade-DP tail (lib.sha256 via shabridge). Small N.
"""
import sys
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
s = sb.s
# reuse the exact scaled-N cascade context from the WE1 probe
import importlib.util
spec = importlib.util.spec_from_file_location(
    "we1mod", "/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards/W8-WE1.py")
we1 = importlib.util.module_from_spec(spec); spec.loader.exec_module(we1)

make_ctx = we1.make_ctx; precompute = we1.precompute
sha_round2 = we1.sha_round2; find_w2 = we1.find_w2; find_M0 = we1.find_M0


def finders(N, sr_target):
    """Two witness-finders for a cascade collision through round sr_target.
    Returns dict with each finder's success + PEAK LIVE-SET (memory surrogate).

    Live-set = the number of partial candidates the finder holds simultaneously.
      Depth-first Koenig: extends ONE partial path; at each round it sets the next
        free word by SOLVING (find_w2 gives W2; W1 is the free choice). For the
        free rounds 57..60 there is NO branching/filtering -> live-set = O(1) (a
        single path, depth=#rounds). To pass a SCHEDULE-determined round it must
        ENFORCE W[r]=sched via a free lever if one exists (still O(1) path), else
        it must FILTER -> which forces materialization (counts as comprehension).
      Comprehension: materializes the full compatible W[60] set (size up to 2^N),
        intersects the g1=0 and h=0 ranges, then picks -> live-set = Theta(2^N).
    """
    ctx = make_ctx(N); MASK = ctx['MASK']
    M0, M1, M2 = find_M0(ctx)
    if M0 is None:
        return None
    st1, W1p = precompute(M1, ctx); st2, W2p = precompute(M2, ctx)

    # ---------- Finder A: depth-first Koenig (O(rounds) live-set) ----------
    # Walk rounds 57..sr_target. At each FREE round (57..60) pick W1[r]=0 (any
    # value works -- the tree is extendible at every node: Thm2 => de60=0 for ALL
    # words), solve W2[r]=find_w2. Live-set stays 1 (one partial path). When we
    # reach a round r where de_r=0 is REQUIRED but W[r] is schedule-FORCED (no free
    # lever), the depth-first finder cannot enforce -- it would have to backtrack /
    # filter over choices made earlier, i.e. search. We detect this: is the
    # required de_r=0 reachable by a LOCAL free choice at this node (O(1)), or only
    # by selecting among the 2^N already-fixed upstream triples (comprehension)?
    def koenig():
        # Honest WKL_0 surrogate: BACKTRACKING depth-first search over the choice
        # tree (w57,w58,w59,w60), holding exactly ONE partial path at a time.
        # WKL_0 = bounded König's lemma: an extendible path through a finitely-
        # branching tree, found by following/backtracking nodes -- NEVER forming a
        # set. We track peak_live = max simultaneous partial-path states held.
        #
        # For sr<=60: pick free words = 0, descend; the tree is extendible at every
        # node (Thm2: de60=0 for ALL words) -> the FIRST path (no backtrack) wins.
        #   peak_live = 1 (one path), depth = #rounds.
        # For sr=61: descend; at the leaf test de61=0. If it fails, BACKTRACK to the
        # last branch and try the next word value (DFS). We bound the search to keep
        # it cheap, but the key invariant is peak_live = O(rounds), NOT Theta(2^N):
        # the finder holds one path + a tiny stack of branch indices.
        peak_live = 1
        if sr_target <= 60:
            a, b = st1[:], st2[:]
            depth = 0
            for r in (57, 58, 59, 60):
                w1 = 0; w2 = find_w2(a, b, r, w1, ctx)
                a = sha_round2(a, ctx['KN'][r], w1, ctx); b = sha_round2(b, ctx['KN'][r], w2, ctx)
                depth += 1
            ok = (((a[4]-b[4]) & MASK) == 0) and (((a[0]-b[0]) & MASK) == 0)
            return dict(success=ok, peak_live=1, depth=depth,
                        backtracks=0, mode="depth-first path, free words, O(rounds) live-set")
        # sr_target == 61 : backtracking DFS over (w57,w58,w59,w60).
        # peak_live = the path stack depth (<=4 partial states) -- explicitly O(1)
        # in 2^N. We CAP the number of leaf-tests so the probe stays cheap; if a
        # witness is found within the cap, O(rounds)-memory DFS certifies sr=61.
        # CAP leaf-tests so the probe stays cheap. Strong sr=61 ~ 2^-2N over tuples
        # => expected first-hit ~2^2N leaf-tests; cap at ~50x that (bounded).
        CAP = min((MASK + 1) ** 3, max(2_000_000, 50 * (MASK + 1) ** 2))
        tests = 0; backtracks = 0
        # path-stack states: we descend w57, w58, w59, w60. Hold <=5 states.
        for w57 in range(MASK + 1):
            a57 = st1[:]; b57 = st2[:]
            w57b = find_w2(a57, b57, 57, w57, ctx)
            a57 = sha_round2(a57, ctx['KN'][57], w57, ctx); b57 = sha_round2(b57, ctx['KN'][57], w57b, ctx)
            for w58 in range(MASK + 1):
                a58 = a57[:]; b58 = b57[:]
                w58b = find_w2(a58, b58, 58, w58, ctx)
                a58 = sha_round2(a58, ctx['KN'][58], w58, ctx); b58 = sha_round2(b58, ctx['KN'][58], w58b, ctx)
                sched1_60 = (ctx['s1'](w58) + W1p[53] + ctx['s0'](W1p[45]) + W1p[44]) & MASK
                sched2_60 = (ctx['s1'](w58b) + W2p[53] + ctx['s0'](W2p[45]) + W2p[44]) & MASK
                for w59 in range(MASK + 1):
                    a59 = a58[:]; b59 = b58[:]
                    w59b = find_w2(a59, b59, 59, w59, ctx)
                    a59 = sha_round2(a59, ctx['KN'][59], w59, ctx); b59 = sha_round2(b59, ctx['KN'][59], w59b, ctx)
                    casoff = find_w2(a59, b59, 60, 0, ctx)
                    for w60 in range(MASK + 1):
                        tests += 1
                        w60b = (w60 + casoff) & MASK
                        # STRONG sr=61 (the card's reading): W[60] matches its
                        # schedule for BOTH messages -> g1=0 AND g2=0 (the 2^-2N
                        # event, "intersect the two independent ranges"). A
                        # depth-first finder tests this POINTWISE per (triple,w60),
                        # holding only the current path -- no set materialized.
                        g1 = (w60 - sched1_60) & MASK
                        g2 = (w60b - sched2_60) & MASK
                        if g1 == 0 and g2 == 0:
                            return dict(success=True, peak_live=5, depth=5,
                                        leaf_tests=tests,
                                        mode="backtracking DFS over (w57..w60), tests g1=0&g2=0 pointwise, path-stack <=5 states, O(rounds) live-set")
                        if tests >= CAP:
                            return dict(success=False, peak_live=5, depth=5,
                                        leaf_tests=tests, capped=True,
                                        mode="backtracking DFS (CAPPED before witness), O(rounds) live-set")
                    backtracks += 1
        return dict(success=False, peak_live=5, depth=5, leaf_tests=tests,
                    mode="backtracking DFS exhausted (no strong sr=61 at this N), O(rounds) live-set")

    # ---------- Finder B: comprehension (materialize set, Theta(2^N)) ----------
    # The card's ACA_0 model: "comprehend the compatible-W[60] set and INTERSECT
    # two independent ranges (g1=0, g2=0)". For each upstream triple we MATERIALIZE
    # the set R1={w60: g1=0} and R2={w60: g2=0} (each held in memory, up to 2^N),
    # then form R1 ∩ R2. peak live-set = Theta(2^N) (the materialized sets). We scan
    # triples until the intersection is non-empty (a strong sr=61 witness).
    def comprehension():
        peak_live = 0; max_compat = 0; triples_scanned = 0
        CAP_TRIPLES = min((MASK + 1) ** 3, max(200_000, 50 * (MASK + 1) ** 2))
        for w57 in range(MASK + 1):
            a = st1[:]; b = st2[:]
            w57b = find_w2(a, b, 57, w57, ctx)
            a = sha_round2(a, ctx['KN'][57], w57, ctx); b = sha_round2(b, ctx['KN'][57], w57b, ctx)
            for w58 in range(MASK + 1):
                a2 = a[:]; b2 = b[:]
                w58b = find_w2(a2, b2, 58, w58, ctx)
                a2 = sha_round2(a2, ctx['KN'][58], w58, ctx); b2 = sha_round2(b2, ctx['KN'][58], w58b, ctx)
                sched1_60 = (ctx['s1'](w58) + W1p[53] + ctx['s0'](W1p[45]) + W1p[44]) & MASK
                sched2_60 = (ctx['s1'](w58b) + W2p[53] + ctx['s0'](W2p[45]) + W2p[44]) & MASK
                for w59 in range(MASK + 1):
                    a3 = a2[:]; b3 = b2[:]
                    w59b = find_w2(a3, b3, 59, w59, ctx)
                    a3 = sha_round2(a3, ctx['KN'][59], w59, ctx); b3 = sha_round2(b3, ctx['KN'][59], w59b, ctx)
                    casoff = find_w2(a3, b3, 60, 0, ctx)
                    # MATERIALIZE the two ranges over w60 (sets in memory):
                    R1 = set(); R2 = set()
                    for w60 in range(MASK + 1):
                        w60b = (w60 + casoff) & MASK
                        if (w60 - sched1_60) & MASK == 0: R1.add(w60)
                        if (w60b - sched2_60) & MASK == 0: R2.add(w60)
                    # peak memory = the two materialized sets (Theta(2^N) capacity)
                    peak_live = max(peak_live, len(R1) + len(R2), (MASK + 1))
                    inter = R1 & R2
                    max_compat = max(max_compat, len(inter))
                    triples_scanned += 1
                    if inter:
                        return dict(success=True, peak_live=(MASK + 1),
                                    compat_size=len(inter), triples=triples_scanned,
                                    mode="materialize R1,R2 ranges over 2^N w60, intersect, Theta(2^N) live-set")
                    if triples_scanned >= CAP_TRIPLES:
                        return dict(success=False, peak_live=(MASK + 1), compat_size=max_compat,
                                    triples=triples_scanned, capped=True,
                                    mode="materialize R1,R2 over 2^N, intersect (CAPPED), Theta(2^N) live-set")
        return dict(success=False, peak_live=(MASK + 1), compat_size=max_compat,
                    triples=triples_scanned,
                    mode="materialize R1,R2 over 2^N, intersect (none non-empty), Theta(2^N) live-set")

    A = koenig(); B = comprehension()
    # The card's question is STRUCTURAL: what peak live-set does the search METHOD
    # need, independent of whether a witness exists at this (small) N. (At N<=10
    # sr=61 has NO witness -- it is 2^-2N rare -- so success-gating would just
    # measure witness starvation, not the WKL/ACA question.) We therefore report
    # the structural peak_live of the MINIMAL-MEMORY method that *covers* the
    # search space: Koenig (DFS, O(rounds)) always covers it; comprehension's 2^N
    # materialization is sufficient but NOT necessary. Minimal-memory = Koenig
    # whenever Koenig's DFS is complete over the space (it is: it enumerates all
    # leaves), so min-mem peak_live = Koenig's peak_live.
    koenig_complete = (A.get('mode','').startswith('depth-first path')  # sr<=60: first path
                       or (sr_target >= 61 and not A.get('capped', False)))
    min_mem_live = A['peak_live'] if koenig_complete else B['peak_live']
    min_mem_finder = "koenig" if koenig_complete else "comprehension"
    witness_exists = A.get('success') or B.get('success')
    return dict(N=N, sr_target=sr_target, MASK=MASK, koenig=A, comprehension=B,
                koenig_complete=koenig_complete, witness_exists=witness_exists,
                min_mem_finder=min_mem_finder, min_mem_live=min_mem_live)


def report(N):
    print(f"=== W8-WE2 witness-finder memory surrogate  N={N} ===")
    out = {}
    for sr in (59, 60, 61):
        r = finders(N, sr)
        if r is None:
            print(f"  sr={sr}: no cascade-eligible M0 at N={N}"); return None
        out[sr] = r
        k = r['koenig']; c = r['comprehension']
        print(f"\n-- sr_target = {sr} --")
        print(f"  Koenig (depth-first DFS)   : success={k['success']}  peak_live={k['peak_live']}  "
              f"depth={k.get('depth')}  leaf_tests={k.get('leaf_tests','-')}")
        print(f"     mode: {k['mode']}")
        print(f"  Comprehension (materialize): success={c['success']}  peak_live={c['peak_live']}  "
              f"compat_size={c.get('compat_size')}")
        print(f"     mode: {c['mode']}")
        print(f"  witness exists at N={N}? {r['witness_exists']}   "
              f"Koenig DFS complete over space? {r['koenig_complete']}")
        print(f"  => STRUCTURAL minimal-memory method: {r['min_mem_finder']}  "
              f"(peak_live={r['min_mem_live']})")
    # The ladder test: does the minimal-memory METHOD's peak live-set jump
    # O(rounds)->Theta(2^N) at 61?  (Structural; witness-existence-independent.)
    print("\n=== LADDER (structural minimal-memory peak live-set per sr) ===")
    for sr in (59, 60, 61):
        r = out[sr]
        print(f"  sr={sr}: min-mem method = {r['min_mem_finder']:14s}  peak_live = {r['min_mem_live']}  "
              f"(2^N={1<<N})")
    lvl = {sr: out[sr]['min_mem_live'] for sr in (59, 60, 61)}
    jump = (lvl[60] <= 8 and lvl[61] >= (1 << (N-1)))
    koenig61_method = (out[61]['min_mem_finder'] == 'koenig')   # O(rounds) covers 61
    print(f"\n  sr=61 (strong: g1=0 AND g2=0) witness exists at N={N}? {out[61]['witness_exists']} "
          f"(found by Koenig DFS; note FULL 8-reg collision is rarer/2^-3N)")
    print(f"  Koenig DFS (O(rounds) live-set) COVERS the sr=61 search space? {koenig61_method}")
    print(f"  min-mem peak live-set jumps O(rounds)->Theta(2^N) at 61?       {jump}")
    print(f"  => KILL clause 'Koenig also certifies 61 with O(rounds) memory' FIRES: {koenig61_method}")
    return out


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument('--N', type=int, default=8)
    a = ap.parse_args()
    report(a.N)
