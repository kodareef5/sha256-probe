"""
W5-HC3 — Frankl shifting: HW~74 as a compressed-family extremal weight.

CARD CLAIM (CATALOG):
  Combinatorial shifting compresses the collision family without changing size; 74 is the
  shift-invariant extremal weight (structural, not a thermodynamic floor).
PROBE (CATALOG):
  N=8,10 implement S_{ij} (flip iff still a collision), iterate to fixed point; is the
  family even shiftable, and is max-HW preserved at the per-N hard-core fraction?
KILL:
  family is shift-rigid (no admissible shifts -> idea dead), OR max-HW not preserved.
SKEPTIC (card's own): crypto families are notoriously NOT down-closed — this is a go/no-go
  on shiftability.

PRIOR #1/#2: 74 ~ half of 132 + cascade (an OUTPUT-space plateau, Binomial(~k,1/2)); the
  collision family here lives on the 4N free MESSAGE bits, whose HW range is 0..4N, NOT ~74
  (domain mismatch we make explicit).

WHAT THIS PROBE DOES, on the exact sr=60 family at N=4,8,10 (each collision = its 4N-bit
free-word vector):
  (A) STANDARD Frankl (i,j)-compression S_ij (size-preserving: replace A by the down-shift
      iff the shifted vector is not already present). Iterate all pairs to a fixed point.
      Report: did size stay constant (must, by construction); max-HW before vs after.
  (B) CARD's variant "flip iff still a collision": only apply S_ij(x) when the shifted
      vector is ITSELF in the collision family. Count admissible such shifts (shiftability);
      if ~0 => shift-rigid => idea dead (the kill's first clause).
  (C) Max-HW of the MESSAGE-vector family vs the claimed 74 / per-N hard-core fraction
      (132/256 -> for 4N bits that would be 0.516*4N). Make the domain mismatch explicit.
"""
import sys, math
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards')
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import _hc_family as F
import shabridge as sb


def maxhw(bitvecs):
    return max(sb.hw(x) for x in bitvecs), min(sb.hw(x) for x in bitvecs), \
        sum(sb.hw(x) for x in bitvecs) / len(bitvecs)


def standard_compression(bitvecs, m):
    """Frankl (i,j)-shift S_ij over the GROUND SET [m], orienting weight toward low indices.
    S_ij(A) = (A \\ {j}) u {i} if i not in A and j in A and the shift is not already present;
    else A unchanged. Size is preserved. Iterate over all i<j to a fixed point."""
    S = set(bitvecs)
    changed = True
    rounds = 0
    while changed and rounds < 200:
        changed = False
        rounds += 1
        for i in range(m):
            for j in range(m):
                if i >= j:
                    continue
                bi, bj = 1 << i, 1 << j
                newS = set(S)
                moved = 0
                for A in S:
                    # move a set bit from j (high) to i (low) if i is empty, j is set
                    if (A & bi) == 0 and (A & bj) != 0:
                        Ash = (A & ~bj) | bi
                        if Ash not in S:
                            newS.discard(A)
                            newS.add(Ash)
                            moved += 1
                if moved:
                    S = newS
                    changed = True
    return S, rounds


def card_shiftability(bitvecs, m):
    """Card's 'flip iff still a collision': for every collision and every (i,j), is the
    down-shifted vector ALSO a collision? Count admissible (=in-family) shifts."""
    Sset = set(bitvecs)
    admissible = 0; attempts = 0; movable = 0
    for A in bitvecs:
        for i in range(m):
            for j in range(m):
                if i >= j:
                    continue
                bi, bj = 1 << i, 1 << j
                if (A & bi) == 0 and (A & bj) != 0:
                    movable += 1
                    Ash = (A & ~bj) | bi
                    attempts += 1
                    if Ash in Sset and Ash != A:
                        admissible += 1
    return dict(movable=movable, admissible=admissible,
                frac=(admissible / movable if movable else 0.0))


def main():
    print("# W5-HC3 — Frankl shifting: is the collision family shiftable, max-HW preserved?")
    print("# Card: 74 = shift-invariant extremal weight. Prior: 74 is an OUTPUT plateau")
    print("#       (~half of 132); the 4N message-bit family has HW in 0..4N (domain mismatch).\n")

    for N in (4, 8, 10):
        fam = F.load_family(N, with_trace=False)
        bv = fam['bitvecs']; m = 4 * N
        hi0, lo0, mean0 = maxhw(bv)
        print(f"===== N={N}  (|S|={len(bv)}, ground set 4N={m}) =====")
        print(f"  [pre]  max-HW={hi0}  min-HW={lo0}  mean-HW={mean0:.2f}  (claimed 74; "
              f"0.516*4N={0.516*m:.1f})")

        # (A) standard compression
        Sc, rnds = standard_compression(bv, m)
        hi1, lo1, mean1 = maxhw(Sc)
        print(f"  [A standard Frankl] size {len(bv)}->{len(Sc)} (preserved={len(Sc)==len(bv)}), "
              f"{rnds} sweeps; max-HW {hi0}->{hi1}, mean {mean0:.2f}->{mean1:.2f} "
              f"(compression pushes weight DOWN; max-HW {'preserved' if hi1==hi0 else 'CHANGED'}).")

        # (B) card's in-family shiftability
        sh = card_shiftability(bv, m)
        print(f"  [B card 'flip iff still a collision'] movable (i,j) slots = {sh['movable']}, "
              f"admissible (shift stays a collision) = {sh['admissible']} "
              f"=> shiftable fraction = {sh['frac']:.4f}")
        if sh['admissible'] == 0:
            print(f"        => SHIFT-RIGID under the card's operation (no in-family shift).")
        print()

    print("# ADJUDICATION:")
    print("#  - (A) Standard Frankl compression always preserves SIZE (by construction) and")
    print("#    pushes weight toward low coords; max-HW is preserved only if the family already")
    print("#    contains the down-shifts. We report whether max-HW is actually preserved.")
    print("#  - (B) The card's 'flip iff still a collision' is the real test: if the in-family")
    print("#    shiftable fraction ~ 0, the family is SHIFT-RIGID => the angle dies (kill clause 1).")
    print("#  - (C) 'max-HW = 74' is a category mismatch: the message-diff vectors live on 4N")
    print("#    bits with HW 0..4N; 74 is the OUTPUT-difference plateau (~half of 132). No 74")
    print("#    extremal weight exists in this domain.")


if __name__ == '__main__':
    main()
