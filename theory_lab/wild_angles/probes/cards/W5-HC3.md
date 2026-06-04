# W5-HC3 — Frankl shifting: HW~74 as a compressed-family extremal weight   ·   VERDICT: KILLED

**Card claim:** combinatorial shifting compresses the collision family without changing size;
74 is the shift-invariant extremal weight (structural, not a thermodynamic floor).

**Probe run:** the exact sr=60 collision families at N=4 (49), N=8 (260), N=10 (946), each
collision a 4N-bit free-word vector. (A) standard Frankl (i,j)-compression S_ij iterated to a
fixed point (size-preserving); (B) the card's "flip iff still a collision" operation (apply
S_ij only when the shifted vector is itself in the collision family) — the go/no-go
shiftability test; (C) max-HW vs the claimed 74. Pure-python, throttled.

**Result (numbers):**
| N | \|S\| | 4N | max-HW (pre) | mean-HW | std-Frankl: size kept / max-HW pre→post | card shift: admissible / movable |
|---|----|----|----|----|----|----|
| 4 | 49 | 16 | 11 | 8.06 | 49 / 11→11 (kept) | 10 / 1504 = 0.0066 |
| 8 | 260| 32 | 25 | 15.94| 260 / 25→25 (kept) | **0 / 30366 = 0.0000 (RIGID)** |
| 10| 946| 40 | 24 | 15.81| 946 / **24→30 (CHANGED)** | 5 / 185036 = 0.00003 |

- **Shift-rigid under the card's operation:** essentially no down-shift of a collision is
  itself a collision (0.66% at N=4; **exactly 0** at N=8; 0.003% at N=10). The family does not
  shift within itself.
- **Standard compression does not preserve max-HW:** at N=10 the extremal weight moves 24→30
  under (size-preserving) compression — so "shift-invariant extremal weight" fails even for the
  classical operator (and "kept" at N=4,8 is not stable across N either).
- **"74" is a domain mismatch:** the message-diff vectors have max-HW 11/25/24 and mean-HW
  ≈ 8/16/16, tracking ≈ 0.516·4N (8.3/16.5/20.6) — not a fixed 74. The 74 is the *output*-diff
  plateau (~half of 132), a different space.

**Kill_criterion:** "family is shift-rigid (no admissible shifts → idea dead), OR max-HW not
preserved." — **fired? YES, on both clauses.** Under the card's "stay-a-collision" shift the
family is rigid (0 admissible at N=8); and under standard compression max-HW is not preserved
(24→30 at N=10).

**Verdict reasoning:** KILLED. The card's probe is explicitly a go/no-go on shiftability, and
it is NO: the sr=60 collision family is shift-rigid under "flip iff still a collision" (the
operation the card names), confirming the card's own skeptic ("crypto families are notoriously
not down-closed"). The fallback — that classical size-preserving compression at least keeps the
extremal weight — also fails (max-HW jumps 24→30 at N=10). And the target value 74 does not
live in this domain at all: it is the output-difference Hamming plateau (≈ half of the 132
hard-core bits, a Binomial(≈k,½) mean), whereas the message-diff vectors have weight ≈ 0.516·4N
that scales with N. So 74 is neither a shift-invariant nor even an extremal weight of the
shifted family — the angle is a rename of an unrelated output statistic (findings #1/#2).

**Cross-check / skeptic note:** Two independent kill clauses, plus a domain mismatch — robust.
The rigidity result (0/30366 at N=8) is the cleanest: it is the same non-down-closure that
killed HC1's container premise, seen through the shifting operator. A defender might keep only
the classical (always-applicable) S_ij — but then "compresses without changing size" is true by
construction and *content-free*, and the one falsifiable consequence (max-HW invariance) is
violated at N=10. There is no route from this family's message-weight profile (≈0.516·4N) to a
fixed 74.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W5-HC3.py`
