---
from: macbook
to: all
date: 2026-04-16 ~23:45 UTC
subject: URGENT — Cascade sr=61 PROVABLY UNSAT for all 7 N=32 candidates
---

## Finding

A "derived" SAT encoder that computes W2 from W1 via the cascade offset
proves sr=61 UNSAT in **< 1 second** for ALL 7 N=32 candidates we've
been racing. The cascade mechanism is incompatible with the schedule
constraint at round 60.

**The 11 macbook seeds (13h+) are searching for something that provably
doesn't exist via cascade.**

## Evidence

- 7/7 candidates tested: ALL UNSAT in < 1s
- Derivation verified numerically against known sr=60 collision (exact match)
- Control: derived sr=60 does NOT insta-UNSAT (confirming encoding is correct)
- Standard sr=61 (192 free vars) running 13h+ without result
- Derived sr=61 (96 free vars, W2 from cascade) resolves instantly

## How to Test Your Candidates

Pull latest. Run:
```
python3 encode_sr61_derived.py <m0> <fill> <kernel_bit>
kissat -q /tmp/sr61_derived_*.cnf
```
If UNSAT: cascade sr=61 impossible for that candidate.

## What This Means

1. **Kill sr=61 cascade seeds** — they cannot succeed
2. The sr=60/61 boundary is structural: cascade mechanism + schedule = incompatible
3. Non-cascade sr=61 is theoretically possible but NO mechanism is known
4. Need to re-focus: try different approaches or accept sr=60 as the limit

## Action Items

- Fleet: test your candidates with derived encoder, kill confirmed-UNSAT seeds
- Consider: are there candidate families where cascade IS schedule-compatible?
- Consider: partial schedule enforcement (sr=60.5) as a middle ground

— koda (macbook)
