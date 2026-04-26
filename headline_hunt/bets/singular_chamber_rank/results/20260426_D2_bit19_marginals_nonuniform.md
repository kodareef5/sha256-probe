# D2: bit=19 de58 image marginals — strongly non-uniform
**2026-04-26 14:30 EDT**

Task D2 from the cross-bet task list (#31). Tests `negatives.yaml`'s
`bdd_marginals_uniform` claim ("BDD marginals at N≥10 are uniform —
provide no SAT branching heuristic signal") on the structurally
distinguished cand idx=1 (bit19_m51ca0b34_55, de58_size=256).

## Method

Sampled the de58 image of the candidate at 2^20 random W57 values
(via `de58_disjoint_check.candidate_de58_image`). Image size: 256
(matches registry's `de58_size=256` exactly). Computed per-bit
marginals: P(bit=1 across the 256 image values).

## Results

```text
bit  marginal  note
  0   1.0000   LOCKED at 1
  1   0.0000   LOCKED at 0
  2   0.0000   LOCKED at 0
  3   1.0000   LOCKED at 1
  4   0.0000   LOCKED at 0
  5-12  0.5000   uniform
 13   0.0000   LOCKED at 0
 14   1.0000   LOCKED at 1
 15   0.0000   LOCKED at 0
 16   1.0000   LOCKED at 1
 17   0.0000   LOCKED at 0
 18   1.0000   LOCKED at 1
 19-20  0.5000   uniform
 21   0.7500   non-uniform (75% 1s)
 22   0.2500   non-uniform (25% 1s)
 23   1.0000   LOCKED at 1
 24   0.0000   LOCKED at 0
 25-28  0.5000   uniform
 29   0.8750   non-uniform (87.5% 1s)
 30   0.8750   non-uniform (87.5% 1s)
 31   0.1250   non-uniform (12.5% 1s)
```

## Summary

- **13 fully locked bits**: marginals exactly 0 or 1.
- **5 partial-locked bits**: marginals at 0.125, 0.25, 0.75, 0.875.
- **14 uniform bits**: marginals exactly 0.5.

**18 of 32 bits (56%) are structurally non-uniform.** Image entropy
log₂(256) = 8 bits — drastically reduced from the 32-bit uniform
expectation.

## Cross-check with existing registry data

The registry has `de58_hardlock_mask = 0x0187e01f` for this candidate:
```
0x0187e01f = 0000 0001 1000 0111 1110 0000 0001 1111
Set bits:    23,24       16,17,18 13,14,15        0,1,2,3,4
                       (= 13 locked bits — matches exactly)
```

The hardlock mask correctly captures the 13 fully-locked bits.
**D2 EXTENDS** this with 5 additional partial-locked bits at marginals
0.125 / 0.25 / 0.75 / 0.875 — bits 21, 22, 29, 30, 31. These are
structurally non-uniform but not binary-locked.

## Implication for `bdd_marginals_uniform` negative

The negatives.yaml entry says: "BDD marginals at N≥10 are uniform —
provide no SAT branching heuristic signal."

**This is FALSIFIED on bit=19 cand.** 18 of 32 bits are non-uniform
(13 locked + 5 partial). A SAT branching heuristic that prioritizes
locked-bit assignments would have a non-trivial pruning advantage on
this CNF.

The `would_change_my_mind` reopen criterion in negatives.yaml says:
> "Non-uniform marginals on a structurally distinguished candidate
> (de58_size << median, e.g., bit=19 family)."

**The criterion fires.** The negative should be REOPENED, scoped to
"non-uniform marginals on structurally distinguished cands" rather
than the general "uniform at N≥10" claim.

## Implication for the broader picture (B1 + C1 + D2 trio)

Combined finding from this cross-bet trio:

1. **B1 (b760423)**: bit=19's de58_size=256 doesn't help D61 search.
   greedy-flip walks floor at HW5 on bit=19 (HIGHER than HW4 elsewhere).
2. **C1 (0605195)**: cascade_aux Mode B speedup is highest (2.82-3.18×)
   at singular_chamber HW4 W57 chambers — Mode A wall is the
   ranking function.
3. **D2 (this)**: bit=19's de58 image marginals ARE non-uniform —
   18 of 32 bits structurally distinguished. SAT branching heuristics
   that exploit this could matter.

Synthesis: **bit=19's structure is real but mis-targeted.** Its
non-uniform marginals (D2) and de58 compression (registry) DON'T
help random-flip walks at the round-61 layer (B1). They MIGHT help
SAT solvers with the right branching heuristic — yet vanilla kissat
doesn't extract the signal automatically (predictor closure stands).

The productive path: a **branching heuristic that prefers locked-bit
positions** as decisions. Untested. Cheap to implement: kissat
supports `--phase-saving` and `--decision-priority` knobs.

## Action items

1. ✓ D2 confirmed: marginals non-uniform on bit=19. Memo committed.
2. negatives.yaml `bdd_marginals_uniform` should be REOPENED with
   scoped criterion. Add `evidence` link to this memo.
3. Open-question add to bet: does kissat with custom branching
   priority (forcing locked-bit decisions early) solve faster than
   default? ~10 min implementation if kissat exposes the knob.

## Reproduce

```python
import sys
sys.path.insert(0, '/Users/mac/Desktop/sha256_review')
sys.path.insert(0, '/Users/mac/Desktop/sha256_review/headline_hunt/bets/sr61_n32')
from de58_disjoint_check import candidate_de58_image

m, fill, bit = 0x51ca0b34, 0x55555555, 19
img = candidate_de58_image(m, fill, bit, n_samples=1<<20)
counts = [sum(1 for v in img if (v >> i) & 1) for i in range(32)]
marginals = [c / len(img) for c in counts]
# Expect: 13 marginals ∈ {0,1}, 5 ∈ {0.125, 0.25, 0.75, 0.875}, 14 = 0.5
```

EVIDENCE-level: bit=19 de58 image has 18 of 32 bits structurally
non-uniform. Reopens `bdd_marginals_uniform` negative with scoped
criterion.
