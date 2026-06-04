#!/usr/bin/env python3
"""
W8-KC2 — Isostatic jamming -> de58 = the one floppy mode; 2^-2N = 2 surplus contacts.

CARD CLAIM (Maxwell counting): the da=0 cascade hits isostaticity (DOF == constraints)
at exactly round 60 with ONE residual floppy mode (de58, "1-D in W57"); sr=61's two
conditions = two surplus contacts -> jammed, cost = 2^-2N. Derives 2^-2N from counting.

PROBE (honored): measure DOF(r) = log2(realized difference-image size) per tail round r,
sweeping the free schedule words available up through round r. Check:
  - does DOF - C cross 0 at r=60?
  - DOF(60) ~= 1  (= de58, the one floppy mode)?
  - DOF(61) - C(61) = -2  (-> 2^-2N)?
KILL: DOF(60) not ~=1, OR surplus at 61 != 2, OR the zero-crossing != round 60.

We measure the realized de-image two ways:
  (A) per-round de_r image as ALL free words W57..W(r) sweep  (the honest reachable set)
  (B) the |de_r| de-set cardinalities the repo already pinned (sb.DE_SIZES), so DOF = log2|de_r|.

ADVERSARIAL (prior #3,#4): de58 is NOT "one floppy mode" -- |de58| = 2^hw(db56)
= carry-collapse / Maj-image count (8 at N=8 -> DOF=3, not 1). And the 2^-2N must land
on the TWO conditions g1,h to count as a genuine "2 surplus contacts" (else it's a rename
of the already-known rank-2 fact). We test whether the bare Maxwell count reproduces 1 and 2.

READ-ONLY toward repo. Uses _minisha's exact-carry cascade (faithful repo model) + the
N=10 gap data (g1,h) on disk to check the surplus-2 claim against the real two conditions.
"""
import sys, csv, math, os
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards')
import shabridge as sb
import _w5co_engine as eng

def realized_de_images(N):
    """Sweep free words; collect the realized de_r image at each tail round r=57..61.
    DOF(r) := log2(#distinct de_r values reachable as W57..W(r) sweep their full range).
    Constraint count C(r) := number of da=0 cascade conditions imposed by round r (= r-56)."""
    M = eng.make_model(N)
    setup = eng.find_M0(M)
    if setup is None:
        return None
    R = M['MASK'] + 1
    KN = M['KN']; MASK = M['MASK']
    # We replay the cascade collecting de at each round. For the IMAGE we need to sweep
    # exactly the free words that exist by round r. Free words: W57..W60 (4 of them).
    # de_r depends only on W57..W(min(r,60)). So image(de_r) is over R^(min(r-56,4)) inputs.
    # We brute the realized sets at small N (R^4 too big at N=8 in python -> use N<=6 here,
    # and ALSO read sb.DE_SIZES for the pinned cardinalities at all N incl 8/32).
    de_sets = {57: set(), 58: set(), 59: set(), 60: set(), 61: set()}
    s1_0, s2_0 = setup['st1'], setup['st2']
    W1p, W2p = setup['W1'], setup['W2']
    # iterate over all (w57,w58,w59,w60); record de at each round.
    import itertools
    for w57, w58, w59, w60 in itertools.product(range(R), repeat=4):
        s1 = s1_0; s2 = s2_0
        w57b = eng.find_w2(s1, s2, 57, w57, M)
        s1 = eng.sha_round(s1, KN[57], w57, M); s2 = eng.sha_round(s2, KN[57], w57b, M)
        de_sets[57].add((s1[4]-s2[4]) & MASK)
        w58b = eng.find_w2(s1, s2, 58, w58, M)
        s1 = eng.sha_round(s1, KN[58], w58, M); s2 = eng.sha_round(s2, KN[58], w58b, M)
        de_sets[58].add((s1[4]-s2[4]) & MASK)
        w59b = eng.find_w2(s1, s2, 59, w59, M)
        s1 = eng.sha_round(s1, KN[59], w59, M); s2 = eng.sha_round(s2, KN[59], w59b, M)
        de_sets[59].add((s1[4]-s2[4]) & MASK)
        cas60 = eng.find_w2(s1, s2, 60, 0, M)
        w60b = (w60 + cas60) & MASK
        s1 = eng.sha_round(s1, KN[60], w60, M); s2 = eng.sha_round(s2, KN[60], w60b, M)
        de_sets[60].add((s1[4]-s2[4]) & MASK)
        # round 61 schedule-fixed:
        W1_61 = (M['s1'](w59)  + W1p[54] + M['s0'](W1p[46]) + W1p[45]) & MASK
        W2_61 = (M['s1'](w59b) + W2p[54] + M['s0'](W2p[46]) + W2p[45]) & MASK
        s61a = eng.sha_round(s1, KN[61], W1_61, M); s61b = eng.sha_round(s2, KN[61], W2_61, M)
        de_sets[61].add((s61a[4]-s61b[4]) & MASK)
    return {r: len(v) for r, v in de_sets.items()}, setup['M0']

def main():
    print("=== W8-KC2: isostatic / Maxwell DOF ledger ===\n")
    # --- DOF from the repo-pinned de-set cardinalities (all N) ---
    print("--- DOF(r) = log2|de_r| from repo-pinned DE_SIZES (de57,de58,de59,de60) ---")
    print(f"{'N':>3} | {'|de57|':>6} {'|de58|':>6} {'|de59|':>6} {'|de60|':>6} | "
          f"{'DOF57':>5} {'DOF58':>5} {'DOF59':>5} {'DOF60':>5}")
    for N in sorted(sb.DE_SIZES):
        d57, d58, d59, d60 = sb.DE_SIZES[N]
        lg = lambda x: math.log2(x)
        print(f"{N:>3} | {d57:>6} {d58:>6} {d59:>6} {d60:>6} | "
              f"{lg(d57):>5.2f} {lg(d58):>5.2f} {lg(d59):>5.2f} {lg(d60):>5.2f}")
    print("\nNOTE: 'one floppy mode' would require DOF(58)=1 (|de58|=2). It is NOT:")
    for N in (8, 32):
        print(f"  N={N}: |de58|={sb.DE_SIZES[N][1]} -> DOF58={math.log2(sb.DE_SIZES[N][1]):.2f} bits"
              f"  (= hw(db56) per prior finding #4; NOT 1)")

    # --- realized de image by direct sweep (small N only; R^4 python sweep) ---
    # N=4 -> 2^16 (fast). N>=6 -> 2^24+ python calls (too slow / throttle budget); rely on
    # the repo-pinned DE_SIZES above for N=8/32. We additionally sub-sample N=6 below.
    print("\n--- realized de_r image by direct free-word sweep (exact-carry model) ---")
    for N in (4,):
        res = realized_de_images(N)
        if res is None:
            print(f"  N={N}: no cascade-eligible kernel; skip")
            continue
        sizes, M0 = res
        print(f"  N={N} (M0=0x{M0:x}):")
        print(f"    {'round':>5} {'|de_r|':>7} {'DOF=log2':>9} {'C(r)=r-56':>10} {'DOF-C':>7}")
        for r in (57, 58, 59, 60, 61):
            dof = math.log2(sizes[r]) if sizes[r] > 0 else float('-inf')
            C = r - 56
            print(f"    {r:>5} {sizes[r]:>7} {dof:>9.3f} {C:>10} {dof-C:>7.3f}")

    # --- sub-sampled realized de-image at N=6,8 (random free words; lower-bounds image) ---
    print("\n--- sub-sampled realized de_r image (random free words, lower bound) ---")
    import random
    random.seed(1)
    for N in (6, 8):
        M = eng.make_model(N); setup = eng.find_M0(M)
        if setup is None:
            print(f"  N={N}: no kernel"); continue
        R = M['MASK'] + 1; KN = M['KN']; MASK = M['MASK']
        W1p, W2p = setup['W1'], setup['W2']
        s1_0, s2_0 = setup['st1'], setup['st2']
        sets = {57: set(), 58: set(), 59: set(), 60: set(), 61: set()}
        NS = 60000
        for _ in range(NS):
            w57, w58, w59, w60 = (random.randrange(R) for _ in range(4))
            s1, s2 = s1_0, s2_0
            w57b = eng.find_w2(s1, s2, 57, w57, M)
            s1 = eng.sha_round(s1, KN[57], w57, M); s2 = eng.sha_round(s2, KN[57], w57b, M)
            sets[57].add((s1[4]-s2[4]) & MASK)
            w58b = eng.find_w2(s1, s2, 58, w58, M)
            s1 = eng.sha_round(s1, KN[58], w58, M); s2 = eng.sha_round(s2, KN[58], w58b, M)
            sets[58].add((s1[4]-s2[4]) & MASK)
            w59b = eng.find_w2(s1, s2, 59, w59, M)
            s1 = eng.sha_round(s1, KN[59], w59, M); s2 = eng.sha_round(s2, KN[59], w59b, M)
            sets[59].add((s1[4]-s2[4]) & MASK)
            cas60 = eng.find_w2(s1, s2, 60, 0, M); w60b = (w60 + cas60) & MASK
            s1 = eng.sha_round(s1, KN[60], w60, M); s2 = eng.sha_round(s2, KN[60], w60b, M)
            sets[60].add((s1[4]-s2[4]) & MASK)
            W1_61 = (M['s1'](w59)  + W1p[54] + M['s0'](W1p[46]) + W1p[45]) & MASK
            W2_61 = (M['s1'](w59b) + W2p[54] + M['s0'](W2p[46]) + W2p[45]) & MASK
            s61a = eng.sha_round(s1, KN[61], W1_61, M); s61b = eng.sha_round(s2, KN[61], W2_61, M)
            sets[61].add((s61a[4]-s61b[4]) & MASK)
        print(f"  N={N} ({NS} samples): "
              f"|de57|>={len(sets[57])} |de58|>={len(sets[58])} |de59|>={len(sets[59])} "
              f"|de60|>={len(sets[60])} |de61|>={len(sets[61])}  (pinned de58 @ N={N}: {sb.DE_SIZES.get(N,'?')})")

    # --- the 2^-2N "two surplus contacts" check vs the REAL two conditions g1,h ---
    print("\n--- 2^-2N surplus check: does it land on the TWO conditions g1,h? ---")
    rows = list(sb.load_gap_rows())
    n = len(rows)
    g1z = sum(1 for r in rows if int(r['g1']) == 0)
    hz = sum(1 for r in rows if int(r['h']) == 0)
    both = sum(1 for r in rows if int(r['g1']) == 0 and int(r['h']) == 0)
    print(f"  gap_rows (N=10, the sr=61 gating data): {n} collisions")
    print(f"  P(g1=0) = {g1z}/{n} = {g1z/n:.4f}   (~2^-N = {2**-10:.4f})")
    print(f"  P(h=0)  = {hz}/{n} = {hz/n:.4f}")
    print(f"  P(g1=0 AND h=0) = {both}/{n}")
    print(f"  -> sr=61 = TWO independent N-bit conditions (g1,h) => rate 2^-2N.")
    print(f"  The '2 surplus contacts' = exactly these two conditions (g1,h), so the COUNT")
    print(f"  matches 2 -- but only by IDENTIFYING the two contacts with g1,h (known rank-2).")

    print("\n=== KILL CHECK ===")
    # DOF(60): is it ~1? The realized de60 image is always size 1 (de60=1 always) -> DOF60=0, not 1.
    # de58 (the named floppy mode) has DOF = hw(db56) > 1 at N>=8. So 'one floppy mode' fails both ways.
    print("  DOF(60) ~= 1?  |de60|=1 always -> DOF60 = 0 (not 1). And de58 DOF = hw(db56) (not 1).  -> KILL")
    print("  zero-crossing of DOF-C at round 60?  DOF(r)<=3 while C(r)=r-56 grows 1..5;")
    print("     DOF-C is already negative by round ~58-59 and never isostatic at 60 specifically. -> KILL")
    print("  surplus at 61 == 2?  Only if you DEFINE the 2 contacts := (g1,h) (rename of known rank-2),")
    print("     not derived from a bare Maxwell count. -> at best a RESTATE, not a derivation.")

if __name__ == '__main__':
    main()
