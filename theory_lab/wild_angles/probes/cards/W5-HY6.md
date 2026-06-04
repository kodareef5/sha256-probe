# W5-HY6 — Special-cube hyperplane osculation → carries as the sole specialness obstruction   ·   VERDICT: SURVIVES

**Card claim:** XOR-only walls are special (clean CAT(0)); *carries* (the only nonlinearity) make walls osculate, localizing nonlinearity to a named pathology with a measurable **osculation depth** (a finer cut than round 61).

**Probe run:** N=4 exhaustive (throttled), with the mandatory **carry-on/off control**. Built a carry-OFF twin of the cascade round (every modular `+` → XOR, Ch/Maj → 0) alongside the exact carry-ON round, sharing identical free words. Per round 57..60 collected the de-image = set of reachable e-register differences in both models; defined osculation = carry image collapsing below the linear (special) image; defined osculation depth = first such round. Checked whether the carry collapse reproduces the repo number |de58| = 2^hw(db56_XOR).

**Result (numbers):** db56 (XOR) = 0x2, hw(db56) = 1.
| round | \|de\| carry-ON | \|de\| carry-OFF | collapse? |
|---|---|---|---|
| 57 | 1 | 4 | yes |
| 58 | **2** | 16 (=2⁴, full) | yes |
| 59 | 1 | 16 | yes |
| 60 | 1 | 16 | yes |

Osculation depth = **57**. **|de58|_carry = 2 = 2^hw(db56) = 2¹** (MATCH — derives the repo law). Carry-OFF image stays at the full 2^N = 16 every round (linear walls embed, never osculate). Ground-truth law cross-check holds N=4/8/10 (2,8,16 = 2^{1,3,4}) and collapses at N=32 (1024 < 2¹⁷).

**Kill_criterion:** "osculation even in the carry-free model, OR none up to the wall, OR depth unrelated to carry length" — **fired? NO** (carry-free model shows NO collapse; carry-on collapses from round 57).

**Verdict reasoning:** The carry-on/off control is clean and directional (finding #5 passes): the linear/special model's de-image stays at full 2^N (walls embed, no osculation) while the exact model collapses immediately — so carries genuinely *are* the sole osculation source, not relabeled adjacency. The collapse magnitude reproduces the repo's measured |de58| = 2^hw(db56_XOR) = 2 at N=4, i.e. it **derives** the number rather than asserting it. **But I stop at SURVIVES, not CONFIRMED**, on the finding-#6/#7 bar: the only *quantitative* content re-derives the **already-closed de58 thread** (|de58| = 2^hw(db56), Maj/AND image-count, group-free); the card's promised genuinely-new quantity — a "measurable osculation depth, a finer cut than round 61" — evaluates to depth = 57, which is simply "carries act from the first cascade round," a trivial early constant, not a new structural cut finer than 61. So: real, falsifiable, correctly-directed control + a re-derivation of a known number, but no *new* number ⇒ SURVIVES, not a fresh CONFIRMED.

**Cross-check / skeptic note:** The single-N derivation (N=4) is backstopped by the repo's DE_SIZES law table (N=4,8,10 all match 2^hw; N=32 carry-collapses), so the |de58| number is solid. The thing the card needed to clear the bar — an osculation depth that cuts *between* the cascade rounds and says something 61 doesn't — did not materialize (depth is just round 57, where carries first enter). Restating "carries are the hardness/obstruction" (already known, finding #7) with cube-complex vocabulary is not a CONFIRMED; the de58 re-derivation keeps it alive but adds nothing past the closed thread.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W5-HY6.py`
