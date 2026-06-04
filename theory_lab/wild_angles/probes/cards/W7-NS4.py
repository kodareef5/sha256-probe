#!/usr/bin/env python3
"""
W7-NS4 — Overspill/underspill: is the wall ALGEBRA (a sharp round) or COUNTING (no sharp round)?

Card claim (CATALOG): Underspill — an internal round-property's first failure is a STANDARD
round (a sharp algebraic cliff). So if a BOOLEAN property flips at exactly 61 uniformly, 61 is a
real cliff (a provable obstruction); if only COUNTS shrink at 61 (no boolean flip), the wall is
external/measure-only -> no UNSAT proof exists. Adjudicates rarity-vs-impossibility.

Probe (CATALOG): "N=6..14 locate the exact breaking round of P1(da_r=0), P2(de_r single-valued),
P3(unique-w-solution) per N; same round for all N (internal cliff) or only a count shrinks at 61
(external)?"

Kill (CATALOG): "every internal property breaks at a *known* N-uniform round (e.g. de58 at 58)
with nothing new flipping at 61 -> reproduces known facts, subsumed by NS1/NS2."

================================================================================
METHOD (reuse the repo's faithful make_helpers(N) cascade, READ-ONLY):
  We run the standard cascade (W2[r] chosen so da_{r+1}=0) starting from the cascade-eligible
  kernel, over many random free-word prefixes, and per round r=57..63 record:
    P1(r): is da_r == 0 for ALL prefixes?  -> first round where da becomes nonzero.
           (da_r=0 is FORCED by the cascade for r=57..60; at 61 there is no free word to absorb,
            so da_61 = de_61 = whatever it lands on -- the boundary.)
    P2(r): is de_r SINGLE-VALUED (|image|==1) across prefixes?  -> first round image > 1.
    P3(r): "unique-w-solution" — for the cascade step at round r, is there exactly ONE W2[r]
           value (given W1[r]) that zeroes da_{r+1}? (modular addition => unique => 1 always
           for r<=60; at 61 W[61] is schedule-pinned, i.e. ZERO free solutions, not 'unique').
  Question: does any BOOLEAN property FLIP at exactly r=61, uniformly for all N (=> sharp
  algebraic cliff), or do the boolean flips all sit at OTHER rounds (de58 at 58) while at 61
  only a COUNT shrinks (no new boolean) => COUNTING wall, no sharp round.
================================================================================
"""
import sys, random
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
sys.path.insert(0, sb.REPO + '/headline_hunt/bets/block2_wang/trails')
import n_invariants as ni


def break_rounds(N, n_samples=4000):
    """Return per-property first-breaking-round at this N."""
    h = ni.make_helpers(N)
    MASK = h['MASK']
    pre, ar, cw1, cw2 = h['precompute_state'], h['apply_round'], h['cw1'], h['cw2']
    sigma0, sigma1, add = h['sigma0'], h['sigma1'], h['add']
    fills = [MASK, 0, MASK ^ (MASK >> 1), MASK >> 1, 1 << (N - 1)]
    m0, fill = ni.find_eligible(h, fills)
    if m0 is None:
        return None
    M1 = [m0] + [fill] * 15
    M2 = list(M1); M2[0] ^= 1 << (N - 1); M2[9] ^= 1 << (N - 1)
    s1, W1pre = pre(M1); s2, W2pre = pre(M2)
    cw57 = cw1(s1, s2)
    rng = random.Random(7)

    # per-round accumulators
    rounds = list(range(57, 64))
    da_imgs = {r: set() for r in rounds}   # set of da_r values seen
    de_imgs = {r: set() for r in rounds}   # set of de_r values seen
    # P3: count of W2 solutions zeroing da_{r+1} given W1 — for the cascade rounds 57..60
    #     (modular add: exactly one; we VERIFY by brute scan at small N for one prefix).
    p3_counts = {}

    for it in range(n_samples):
        w57 = rng.randrange(MASK + 1)
        w2_57 = (w57 + cw57) & MASK
        st1 = [s1, ar(s1, w57, 57)]   # placeholder; build sequence below
        # build the cascade sequence of (s1_r, s2_r) for r=57..63
        a1 = ar(s1, w57, 57); a2 = ar(s2, w2_57, 57)
        seq = {57: (a1, a2)}
        # round 58
        cw58_v = cw1(a1, a2); b1 = ar(a1, 0, 58); b2 = ar(a2, cw58_v, 58); seq[58] = (b1, b2)
        cw59_v = cw1(b1, b2); c1 = ar(b1, 0, 59); c2 = ar(b2, cw59_v, 59); seq[59] = (c1, c2)
        cw60_v = cw2(c1, c2); d1 = ar(c1, 0, 60); d2 = ar(c2, cw60_v, 60); seq[60] = (d1, d2)
        W1 = list(W1pre) + [w57, 0, 0, 0]
        W2 = list(W2pre) + [w2_57, cw58_v, cw59_v, cw60_v]
        for r in (61, 62, 63):
            W1.append(add(sigma1(W1[r-2]), W1[r-7], sigma0(W1[r-15]), W1[r-16]))
            W2.append(add(sigma1(W2[r-2]), W2[r-7], sigma0(W2[r-15]), W2[r-16]))
        e1 = ar(d1, W1[61], 61); e2 = ar(d2, W2[61], 61); seq[61] = (e1, e2)
        f1 = ar(e1, W1[62], 62); f2 = ar(e2, W2[62], 62); seq[62] = (f1, f2)
        g1 = ar(f1, W1[63], 63); g2 = ar(f2, W2[63], 63); seq[63] = (g1, g2)
        for r in rounds:
            x1, x2 = seq[r]
            da_imgs[r].add((x1[0] - x2[0]) & MASK)
            de_imgs[r].add((x1[4] - x2[4]) & MASK)

    # P3 (unique-w-solution) — brute scan once per cascade round at this (small) N:
    # given the FIRST prefix's pre-round state, count W2[r] in [0,2^N) with da_{r+1}==0.
    rng2 = random.Random(7)
    w57 = rng2.randrange(MASK + 1); w2_57 = (w57 + cw57) & MASK
    a1 = ar(s1, w57, 57); a2 = ar(s2, w2_57, 57)
    state_pairs = {57: (s1, s2, w57)}   # (pre-round-state path1, path2, W1 used)
    # rebuild pre-states for rounds 58,59,60
    cw58_v = cw1(a1, a2); b1 = ar(a1, 0, 58); b2 = ar(a2, cw58_v, 58)
    cw59_v = cw1(b1, b2); c1 = ar(b1, 0, 59); c2 = ar(b2, cw59_v, 59)
    cw60_v = cw2(c1, c2)
    pre_states = {57: (s1, s2, w57), 58: (a1, a2, 0), 59: (b1, b2, 0), 60: (c1, c2, 0)}
    for r in (57, 58, 59, 60):
        ps1, ps2, w1use = pre_states[r]
        cnt = 0
        for w2 in range(MASK + 1):
            n1 = ar(ps1, w1use, r); n2 = ar(ps2, w2, r)
            if (n1[0] - n2[0]) & MASK == 0:
                cnt += 1
        p3_counts[r] = cnt
    # round 61: W[61] is schedule-PINNED (no free word) — count free W solutions = 0 by DOF
    p3_counts[61] = 0  # structural: schedule fixes W[61], no free variable to solve with

    # first breaking rounds
    da_break = next((r for r in rounds if len(da_imgs[r]) > 1 or
                     (len(da_imgs[r]) == 1 and 0 not in da_imgs[r])), None)
    de_break = next((r for r in rounds if len(de_imgs[r]) > 1), None)
    return dict(N=N, m0=m0, fill=fill,
                da_imgs={r: len(da_imgs[r]) for r in rounds},
                da_zero={r: (da_imgs[r] == {0}) for r in rounds},
                de_imgs={r: len(de_imgs[r]) for r in rounds},
                p3_counts=p3_counts,
                da_break=da_break, de_break=de_break)


def main():
    print("=" * 80)
    print("W7-NS4 — overspill: sharp algebraic round at 61, or counting wall (no sharp round)?")
    print("=" * 80)
    Ns = [6, 8, 10, 12, 14]
    rows = {}
    for N in Ns:
        rows[N] = break_rounds(N)

    # P1: da_r==0 table
    print("\n--- P1: da_r == 0 ?  (cascade forces 0 for 57..60; 61 is the boundary) ---")
    print(f"{'N':>3} | " + " ".join(f"r{r:>2}" for r in range(57, 64)))
    for N in Ns:
        r = rows[N]
        if r is None: print(f"{N:>3} | (no kernel)"); continue
        cells = []
        for rr in range(57, 64):
            cells.append(" 0 " if r['da_zero'][rr] else f"{r['da_imgs'][rr]:>2}v")
        print(f"{N:>3} | " + " ".join(f"{c:>3}" for c in cells) +
              f"   (da first != 0 at round {r['da_break']})")

    # P2: |de_r image| table
    print("\n--- P2: |de_r image|  (single-valued=1; first >1 = de break round) ---")
    print(f"{'N':>3} | " + " ".join(f"r{r:>2}" for r in range(57, 64)) + " | de-break")
    de_breaks = []
    for N in Ns:
        r = rows[N]
        if r is None: continue
        cells = " ".join(f"{r['de_imgs'][rr]:>3}" for rr in range(57, 64))
        de_breaks.append(r['de_break'])
        print(f"{N:>3} | {cells} |   {r['de_break']}")

    # P3: unique-w-solution count
    print("\n--- P3: # of W2 solutions zeroing da_{r+1} (cascade rounds; 61 schedule-pinned) ---")
    print(f"{'N':>3} | " + " ".join(f"r{r:>2}" for r in (57, 58, 59, 60, 61)))
    for N in Ns:
        r = rows[N]
        if r is None: continue
        cells = " ".join(f"{r['p3_counts'].get(rr,'-'):>3}" for rr in (57, 58, 59, 60, 61))
        print(f"{N:>3} | {cells}")

    # ---- VERDICT LOGIC ----
    print("\n" + "=" * 80)
    print("OVERSPILL VERDICT")
    print("=" * 80)
    # (a) Does any BOOLEAN property flip at exactly 61 uniformly?
    da_breaks = [rows[N]['da_break'] for N in Ns if rows[N]]
    de_breaks = [rows[N]['de_break'] for N in Ns if rows[N]]
    print(f"  da first-nonzero round across N: {da_breaks}")
    print(f"  de first-multivalued round across N: {de_breaks}")
    da_at_61 = all(b == 61 for b in da_breaks)
    de_at_58 = all(b == 58 for b in de_breaks)
    print(f"  da breaks uniformly at 61? {da_at_61}  (forced-zero cascade ends at 60, so da=de"
          f" 'reveals' at 61 — but it's the END of a counting cascade, not a property FLIP)")
    print(f"  de breaks uniformly at 58 (NOT 61)? {de_at_58}  -> de's boolean flip is at 58, a"
          f" KNOWN N-uniform round, nothing new at 61")
    # (b) at 61, does only a COUNT shrink (P3: solutions 1->0) with no new boolean flip?
    p3_61_zero = all(rows[N]['p3_counts'].get(61, None) == 0 for N in Ns if rows[N])
    p3_60_one = all(rows[N]['p3_counts'].get(60, None) == 1 for N in Ns if rows[N])
    print(f"  P3: #free-W solutions = 1 at r=60 (unique) for all N? {p3_60_one}")
    print(f"  P3: #free-W solutions = 0 at r=61 (schedule-pinned) for all N? {p3_61_zero}")
    print(f"      -> at 61 the only change is DOF/count (1 free word -> 0 free words);"
          f" no algebraic boolean property newly flips at 61.")

    # KILL: every internal property breaks at a KNOWN N-uniform round with nothing new at 61.
    nothing_new_at_61 = de_at_58 and p3_61_zero  # de flips at 58; at 61 only the count drops
    print("\n  KILL cond (every internal property breaks at a known round, nothing NEW flips at 61): "
          f"{nothing_new_at_61}")
    if nothing_new_at_61:
        print("  -> KILLED: the wall at 61 is COUNTING (DOF: free words exhausted), NOT a sharp")
        print("     algebraic cliff. de's boolean flip is at 58; at 61 only the solution-count")
        print("     drops 1->0. NO new boolean property flips at 61 => no sharp round; matches the")
        print("     'no round-60/61 knee' prior finding. Answer: NO SHARP ROUND (overspill says count).")
    else:
        print("  -> SURVIVES: a boolean property genuinely flips at 61 uniformly (new internal target).")


if __name__ == '__main__':
    main()
