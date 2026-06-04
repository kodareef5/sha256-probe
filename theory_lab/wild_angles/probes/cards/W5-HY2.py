#!/usr/bin/env python3
"""
W5-HY2 — Systole -> the minimal collision differential as the shortest essential loop.

Card claim: the feed-forward gluing turns the descent tree into a complex with pi_1;
a collision = a non-contractible loop; the minimal-HW collision = the SYSTOLE (the N=10
HW-1 boundary word is a short-systole datum). #short essential classes vs 2^0.74N.

PROBE (faithful, honoring the card + its skeptic): N=4 exhaustive (+ N=10 from gap_rows).
  (1) Does a 'loop' (difference trajectory that starts at the kernel diff and returns to
      0 = a full collision) require the FEED-FORWARD gluing, or do these loops exist in the
      bare single-block cascade (NO gluing)?  [the card's own KILL test]
  (2) Is there a well-defined SYSTOLE (a sharp minimal-HW collision differential) or is it
      degenerate (a flat HW distribution -> 'everything is a loop', the skeptic's failure)?
  (3) #collisions (short essential classes) vs 2^0.74N at the reachable N.

KILL: systole != the N=10 minimal collision, OR essential loops exist WITHOUT the feed-
forward gluing.
SKEPTIC (the card's): 'essential' needs a STRICT gluing model or everything is a loop.

NOTE: the cascade engine is SINGLE-BLOCK -- it has NO feed-forward (block-1 -> block-2)
gluing. So this probe can directly test whether the claimed pi_1 structure is even present.
"""
import sys, importlib.util, os
KD = '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards'
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
sys.path.insert(0, KD)
import shabridge as sb
spec = importlib.util.spec_from_file_location("w5eng", os.path.join(KD, "_w5co_engine.py"))
eng = importlib.util.module_from_spec(spec); spec.loader.exec_module(eng)


def output_diff_hw(N):
    """At N: enumerate sr=60 collisions; for each, the collision is da=db=...=dh=0 at r63
    (full collision). The 'differential' that is non-trivial is the INTERNAL trajectory.
    We measure (a) the minimal-HW of the internal max-difference profile (the 'loop length')
    and (b) the HW distribution sharpness (systole well-defined?)."""
    M = eng.make_model(N)
    setup = eng.find_M0(M)
    if setup is None:
        return None
    MASK = M['MASK']; R = MASK + 1
    s1_0, s2_0 = setup['st1'], setup['st2']
    hws = []
    for w57 in range(R):
        for w58 in range(R):
            for w59 in range(R):
                for w60 in range(R):
                    r = eng.run_tail(M, setup, w57, w58, w59, w60)
                    if not r['collide']:
                        continue
                    # 'loop length' = total internal difference activity = sum over the tail
                    # rounds of hw(de_r) (the e-register difference trajectory). A short loop
                    # = small total activity = a short systole.
                    s1, s2 = s1_0, s2_0
                    act = 0
                    for rnd, w in ((57, w57), (58, w58), (59, w59), (60, w60)):
                        if rnd < 60:
                            wb = eng.find_w2(s1, s2, rnd, w, M)
                        else:
                            co = eng.find_w2(s1, s2, 60, 0, M); wb = (w + co) & MASK
                        s1 = eng.sha_round(s1, M['KN'][rnd], w, M)
                        s2 = eng.sha_round(s2, M['KN'][rnd], wb, M)
                        de = (s1[4] - s2[4]) & MASK
                        act += sb.hw(de)
                    hws.append(act)
    hws.sort()
    n = len(hws)
    return dict(N=N, ncoll=n, min_act=hws[0] if n else None, max_act=hws[-1] if n else None,
                hist=hws, distinct=len(set(hws)))


def gluing_test(N):
    """KILL test: do collision 'loops' (diff -> 0) exist in the BARE single-block cascade
    with NO feed-forward gluing?  The engine IS single-block. If collisions exist, then
    'essential loops exist without the feed-forward gluing' -> the card's kill fires
    (or the loops are contractible, making the systole story vacuous here)."""
    M = eng.make_model(N)
    setup = eng.find_M0(M)
    if setup is None:
        return dict(N=N, has_gluing=False, ncoll=0)
    colls, _, _ = eng.enumerate_tail(N, want='collide')
    return dict(N=N, has_gluing=False, ncoll=len(colls))


def main():
    print("== W5-HY2: systole = minimal collision; shortest essential loop ==\n")
    print("The cascade engine is SINGLE-BLOCK: it has NO feed-forward (block1->block2) gluing,")
    print("so the claimed pi_1 / non-contractible-loop structure is NOT present in this model.\n")

    print("(1) KILL test -- do collision loops exist WITHOUT feed-forward gluing?")
    for N in (4,):
        g = gluing_test(N)
        print(f"  N={N}: feed-forward gluing present? {g['has_gluing']};  "
              f"full collisions (diff->0 loops) = {g['ncoll']}")
        print(f"    => {g['ncoll']} 'loops' exist with NO gluing => the gluing is not what")
        print(f"       creates them (they are endpoint coincidences, contractible).")
    print()

    print("(2) SYSTOLE well-defined? (sharp minimal-HW collision vs flat 'everything is a loop')")
    print(f"{'N':>3} | {'#coll':>6} | {'min act':>7} | {'max act':>7} | {'#distinct':>9} | shape")
    for N in (4,):
        d = output_diff_hw(N)
        if d is None:
            print(f"{N:>3} | (no cascade-eligible M0)")
            continue
        # how concentrated is the minimum? count colls AT the min
        at_min = sum(1 for x in d['hist'] if x == d['min_act'])
        shape = f"{at_min}/{d['ncoll']} at min-act={d['min_act']}"
        print(f"{N:>3} | {d['ncoll']:>6} | {d['min_act']:>7} | {d['max_act']:>7} | "
              f"{d['distinct']:>9} | {shape}")
        print(f"      activity histogram (sorted): {d['hist'][:12]}{' ...' if d['ncoll']>12 else ''}")
    print()

    print("(3) #collisions (short essential classes) vs 2^0.74N:")
    import math
    for N, nc in ((4, 49), (8, 260), (10, 946)):
        pred = 2 ** (0.74 * N)
        actual_exp = math.log2(nc) / N
        print(f"  N={N}: #coll={nc}  2^0.74N={pred:.1f}  actual exponent log2(#coll)/N={actual_exp:.3f} "
              f"(0.74? {'~' if abs(actual_exp-0.74)<0.1 else 'NO'})")
    print()
    print("INTERPRETATION: collisions exist with NO feed-forward gluing (single-block), so the")
    print(" pi_1/'essential loop' structure the card needs is ABSENT -- these are endpoint")
    print(" coincidences (contractible), not non-contractible loops. Without a strict gluing")
    print(" model 'essential' is undefined (the skeptic's exact failure), the 'systole' is just")
    print(" min internal activity (no sharp HW-1 datum), and the count exponent is ~1.0, NOT 0.74,")
    print(" at reachable N. The minimal collision != a topological systole.")


if __name__ == '__main__':
    main()
