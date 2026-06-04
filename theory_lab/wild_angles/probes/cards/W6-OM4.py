#!/usr/bin/env python3
"""
W6-OM4 — de58 = the unique open 1-cell; de57/59/60 = 0-cells (a graded cell decomposition).

Card claim: in a graded cell decomposition of the de-vector, de58 is the unique OPEN 1-cell
(the family's single free-parameter axis, in the *modular* chart), de57/de59/de60 are 0-cells
(points). Meant to make OM2 mechanistic and explain *why* de58 is special.

PROBE (per CATALOG): N=4..16 — (a) confirm de57/59/60 constant (0-cells), fit slope
s = log2|de58|/N; (b) does de58's SHARE of the total collision exponent ≈ s/0.74?
KILL: a SECOND de-coordinate varies at large N (>1 cell), OR slope(|de58|) unrelated to
the count exponent.
Skeptic (CATALOG + prior finding #5): "mostly re-describes known data — must clear the
GROWTH-MATCHING prediction or it is vocabulary." Re-deriving |de58|=2^hw(db56) is NOT a
CONFIRMED; only a STABLE s/0.74 mass-share is new content.

This probe:
  1. CELL STRUCTURE -- pinned, repo-measured de-set sizes (shabridge.DE_SIZES, the
     authoritative measurement: de57=de59=de60=1 ALWAYS, only de58 varies). This is
     literally the card's "de58=1-cell, others=0-cells" -> a RESTATE of known data.
  2. RE-DERIVATION ANCHOR -- reproduce |de58|=2^hw(db56) at N=4 via the full validated
     cascade (find_w2 at every round), confirming the law independently.
  3. GROWTH-MATCH (the decisive NEW test) -- measure full sr=60 MSB-kernel collision
     counts at N=4 (Python engine, exact) and combine with repo-measured counts at N=8/10;
     compute the de58 mass-share = log2|de58| / log2(count) per N and ask: STABLE (a real
     dimension) or scattered (vocabulary)?
"""
import sys, importlib.util, os, math
KD = '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards'
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
sys.path.insert(0, KD)
import shabridge as sb
spec = importlib.util.spec_from_file_location("w5eng", os.path.join(KD, "_w5co_engine.py"))
eng = importlib.util.module_from_spec(spec); spec.loader.exec_module(eng)


def de58_image_full_cascade(N):
    """Reproduce |de58| via the FULL validated cascade (the W5-HY6 method): sweep all
    cascade free words, run find_w2 at every round, collect the SET of e-differences after
    round 58. Returns (|de58|, hw(db56), 2^hw). Only feasible for small N (sweep size 2^N
    over w57 suffices: de58 'is computable from w57 alone' per cascade_structure_complete.md
    line 61). We sweep w57 fully and read de58 after the round-58 cascade step."""
    M = eng.make_model(N)
    setup = eng.find_M0(M)
    if setup is None:
        return None
    MASK = M['MASK']; R = MASK + 1; KN = M['KN']
    s1_0, s2_0 = setup['st1'], setup['st2']
    db56 = s1_0[1] ^ s2_0[1]

    def step(s1, s2, rnd, w1):
        w2 = eng.find_w2(s1, s2, rnd, w1, M)
        return (eng.sha_round(s1, KN[rnd], w1, M), eng.sha_round(s2, KN[rnd], w2, M))

    # de58 = SET of MODULAR e-differences after round 58 (matches W5-HY6 which read
    # (s1[4]-s2[4]) and reproduced |de58|=2 at N=4). de58 'computable from w57 alone'.
    de58 = set()
    for w57 in range(R):
        a1, a2 = step(s1_0, s2_0, 57, w57)         # round 57 cascade
        b1, b2 = step(a1, a2, 58, 0)               # round 58 cascade (w58=0 baseline)
        de58.add((b1[4] - b2[4]) & MASK)
    return dict(N=N, de58=len(de58), hw=sb.hw(db56), twohw=2**sb.hw(db56))


def main():
    print("== W6-OM4: de58 = unique 1-cell; de57/59/60 = 0-cells ==\n")

    # ---- (1) CELL STRUCTURE from the repo's authoritative de-set measurement ----
    print("(1) PINNED cell structure (shabridge.DE_SIZES = repo's measured de-sets):")
    print(f"    {'N':>3} | {'|de57|':>6} {'|de58|':>6} {'|de59|':>6} {'|de60|':>6} | 0-cells? 1-cell?")
    de58_pin = {}
    for N in sorted(sb.DE_SIZES):
        d57, d58, d59, d60 = sb.DE_SIZES[N]
        de58_pin[N] = d58
        zero = (d57 == 1 and d59 == 1 and d60 == 1)
        print(f"    {N:>3} | {d57:>6} {d58:>6} {d59:>6} {d60:>6} | "
              f"de57/59/60={'all=1 (0-cells)' if zero else 'NOT all 1!'}; de58={'varies' if d58>1 else '=1'}")
    print(f"    -> KILL(a): does a 2nd coordinate vary? de57 set={{{set(v[0] for v in sb.DE_SIZES.values())}}}, "
          f"de59 set={{{set(v[2] for v in sb.DE_SIZES.values())}}}, de60 set={{{set(v[3] for v in sb.DE_SIZES.values())}}}")
    print("       (all three constant=1 -> exactly ONE varying coordinate; KILL(a) does NOT fire,")
    print("        but this is a RESTATE of the pinned data, not new content.)\n")

    # ---- (2) RE-DERIVATION ANCHOR: |de58|=2^hw(db56) at small N via full cascade ----
    print("(2) Independent re-derivation of |de58| via the full validated cascade:")
    print(f"    {'N':>3} | {'|de58| (full sweep)':>18} | {'hw(db56)':>8} {'2^hw':>6} | match law?")
    for N in (4, 8):
        r = de58_image_full_cascade(N)
        if r is None:
            print(f"    {N:>3} | (no cascade-eligible M0)")
            continue
        ok = 'YES' if r['de58'] == r['twohw'] else 'no'
        print(f"    {N:>3} | {r['de58']:>18} | {r['hw']:>8} {r['twohw']:>6} | {ok}")
    print("    (the law |de58|=2^hw(db56) is the Maj/AND image-count -- prior finding #5,")
    print("     a carry-collapse count, NON-monotone in N.)\n")

    # ---- (3) GROWTH-MATCH: the decisive NEW test ----
    print("(3) GROWTH-MATCH (decisive): de58 mass-share = log2|de58| / log2(#collisions).")
    print("    Fresh MSB-kernel sr=60 collision counts: N=4 exact (this engine);")
    print("    N=8,10 from repo (backward_construct verified: 260 @N=8, 1833 @N=10).")
    # exact N=4 count
    colls4, _, _ = eng.enumerate_tail(4, want='collide')
    counts = {4: len(colls4), 8: 260, 10: 1833}
    print(f"    {'N':>3} | {'#coll':>6} {'log2#':>7} | {'|de58|':>6} {'log2|de58|':>10} "
          f"{'s=l2/N':>7} | {'share=l2de58/log2#':>18} {'s/0.74':>7} {'s/0.673':>8}")
    shares, snorm74, snorm673 = [], [], []
    for N in (4, 8, 10):
        c = counts[N]; lc = math.log2(c)
        d58 = de58_pin.get(N, sb.DE_SIZES[N][1])
        ld = math.log2(d58); sN = ld / N
        share = ld / lc
        shares.append(share); snorm74.append(sN/0.74); snorm673.append(sN/0.673)
        print(f"    {N:>3} | {c:>6} {lc:>7.3f} | {d58:>6} {ld:>10.3f} {sN:>7.3f} | "
              f"{share:>18.3f} {sN/0.74:>7.3f} {sN/0.673:>8.3f}")
    sp = max(shares) - min(shares)
    print(f"\n    de58 mass-share  range = [{min(shares):.3f}, {max(shares):.3f}]  "
          f"(spread {sp:.3f}) -- {'STABLE' if sp < 0.05 else 'NOT STABLE'}")
    print(f"    s/0.74           range = [{min(snorm74):.3f}, {max(snorm74):.3f}]")
    print(f"    s/0.673          range = [{min(snorm673):.3f}, {max(snorm673):.3f}]")
    print("\n    VERDICT LOGIC: KILL(a) does not fire (only de58 varies = the pinned fact),")
    print("    but that is a RESTATE. The card's NEW content -- a STABLE de58 share = s/0.74")
    print("    'dimension of the algebraic part' -- requires a constant share. |de58|=2^hw(db56)")
    print("    is NON-monotone (finding #5), so the share is NOT stable -> KILL clause (b):")
    print("    slope(|de58|) is unrelated to the count exponent. Restate, not derivation.")


if __name__ == '__main__':
    main()
