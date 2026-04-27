# F73 + F74: Random W sweep + BVA mechanism test on bit28
**2026-04-27 15:38 EDT**

Two quick experiments closing out the day's exploration.

## F73: Random W-witness sweep on bit28

Generated 100 random (W57, W58, W59, W60) tuples (seed=42, uniform over
2^128 space). Verified each via cert-pin batch.

```
Result: 100/100 UNSAT in 13.74s total wall (~0.14s per witness)
```

**Empirical floor**: probability of accidentally hitting a sr=60
collision via random W-sampling on bit28 is < 1/100 (trivial bound).
For a meaningful test, would need ~2^20 = 1M samples = 39 hours
compute.

This isn't a substantive finding — it's expected per Wang collision
complexity (probability ~2^-60 per random W). F73 just confirms the
cert-pin pipeline doesn't accidentally give false-SAT on random
inputs.

## F74: BVA mechanism test (CMS --bva 0)

F60 speculated: "CMS's BVA (Bounded Variable Addition) exploits
bit28's broad LM tail, hence bit28 is CMS-only fast." Test: disable
BVA via `--bva 0` and compare wall time.

```
CMS WITH BVA (default):    17.44s  (matches F63 ~22s baseline within seed variance)
CMS WITHOUT BVA (--bva 0): 16.87s
Ratio (NoBVA/BVA):         0.96×
```

**Virtually identical.** BVA is NOT the mechanism behind bit28's
CMS-fastness.

F60's "BVA exploits broad LM tail" mechanism speculation is REFUTED.
The actual cause of bit28's CMS-only fastness is some other CMS
preprocessing/heuristic component, not BVA.

## What this means for the mechanism story

Across F60-F63, the speculated mechanism was:
- bit28 has broad LM tail (yale F45)
- CMS uses BVA which exploits redundant clause structure
- → bit28 is CMS-fast because BVA finds bit28's structural redundancy

F74 falsifies this specific speculation. Possible alternative
mechanisms:
1. CMS's variable ordering heuristic happens to like bit28's
   constraint topology
2. CMS's restart schedule aligns with bit28's basin structure
3. CMS's clause learning/database management handles bit28's
   conflict pattern better
4. Some other component (intree, transred, distill, etc.)

Without further targeted tests (each disabling one component),
can't pin down the actual mechanism. F74 is a clean negative on the
BVA-specific hypothesis.

## Discipline note

This is a 5th honest revision of today's F-series (after F39, F49,
F55, F69). The pattern: speculative mechanism stories require
targeted falsification tests before claiming as confirmed. F60's
"BVA hypothesis" was speculation, not strongly claimed — but F74
falsifies it cleanly.

## What's NOT changed

The structural cohort taxonomy is unaffected:
- Cohort A: bit10, bit25, bit3 (universal-fast)
- Cohort B: bit2 (kissat-only)
- Cohort C: bit17 (cadical-only)
- Cohort D: bit28 (CMS-only)

bit28 IS still CMS-only fast (F63 confirmed); the mechanism is just
not BVA.

For paper Section 4: cohort taxonomy stands. Mechanism speculation
needs more targeted tests (or honest "mechanism unknown" framing).

## Discipline

- 100 cert-pin random-W kissat runs (F73 batch) + 2 CMS runs (F74)
- F73 logged as 1 representative entry; F74 logged as both BVA on/off
- 0% audit failure rate maintained (~250 logged solver runs today)

EVIDENCE-level: VERIFIED for both F73 (100/100 UNSAT, expected) and
F74 (BVA NOT the mechanism).

## Concrete next moves

1. **Test more CMS components** disabled (intree, transred, distill,
   etc.) on bit28 to isolate the actual mechanism
2. **Compare CMS variable-ordering heuristic** between bit28 and
   bit2/bit17 to see if branchy var-orderings explain Cohort D
3. **For paper Section 4**: don't claim "BVA mechanism" — claim
   "CMS-specific heuristic, mechanism not yet pinned down"
4. **For yale**: the cohort behavior is solver-architecture-specific
   but NOT BVA-specific. yale's manifold-search test on bit28 still
   relevant cross-axis.
