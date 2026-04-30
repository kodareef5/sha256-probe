---
date: 2026-04-30
bet: programmatic_sat_propagator
status: F347_REFUTED — sr=61 bit31 with 32 clauses gives only -0.08%
---

# F364 + F365: F344-style full-row sweep on sr=61 bit31 → F347 13.7% was noise

## Setup

F347 measured -13.7% conflict reduction on aux_force_sr60 bit31 m17149975
with 32 mined clauses (1 unit + 31 pair). F362/F363 found smaller cands
give only ~1% with 2-clause minimal preflight.

To isolate cand-vs-clause-count-vs-sr factors, F364+F365 ran:
1. F364: F344-style full-row sweep on aux_force_sr61 bit31 m17149975
   (same cand as F347, but sr=61 instead of sr=60)
2. F365: cadical 5min comparison with all 32 mined clauses

This is apples-to-apples with F347 except for sr level.

## F364 mining result

```
Single-bit forced: 1 (dW57[0] = 1)        [matches sr=60 bit31 from F344]
Adjacent-pair forbidden: 31 / 31           [matches sr=60 bit31]
Total mined clauses: 32                    [matches F347 setup exactly]
```

Confirms F354/F355's sr-invariance: mining produces SAME clauses at
sr=60 and sr=61 force-mode for the same cand.

## F365 injection result

```
aux_force_sr61 bit31 BASELINE (cadical 5min): 5,253,180 conflicts UNKNOWN
aux_force_sr61 bit31 + 32 clauses:            5,248,930 conflicts UNKNOWN
Δ: -4,250 conflicts (-0.08%)
```

## Findings

### Finding 1 — F347's 13.7% was almost certainly noise

Same cand bit31, same 32 clauses, same encoder mode. Only difference: sr level.

| Probe | sr | Clauses | Speedup |
|---|---:|---:|---:|
| F347 | 60 | 32 | -13.7% |
| **F365** | **61** | **32** | **-0.08%** |

If the speedup were a real structural effect, sr-invariance per F354
should mean similar magnitude at sr=61. F365's -0.08% is essentially
zero — F347's 13.7% must be noise outlier from a single 5-min sample.

### Finding 2 — F343 injection's real envelope is ~0-1%

Updated complete envelope:

| Probe | Mode | Cand | Clauses | Speedup |
|---|---|---|---:|---:|
| F347 | sr60 aux_force | bit31 m17149975 | 32 | -13.7% (NOISE OUTLIER) |
| F348 | sr60 aux_force | 5-cand mean | 2 | -8.8% (suspicious — re-verify) |
| F352 | sr60 aux_expose | bit29 m17454e4b | 2 | -1.06% |
| F360 | sr61 basic_cascade | bit25 m09990bd2 | 130 | -0.79% |
| F362 | sr61 aux_force | bit25 m09990bd2 | 34 | -0.46% |
| F363 | sr61 aux_force | bit31 m17149975 | 2 | -0.72% |
| **F365** | **sr61 aux_force** | **bit31 m17149975** | **32** | **-0.08%** |

EXCEPT F347 and F348 (sr=60, possibly noise), all measurements show
~0.5-1% speedup. The F343 injection mechanism gives essentially
noise-level benefit on ALL tested cands at sr=61.

### Finding 3 — Phase 2D propagator viability seriously compromised

If the real speedup envelope is 0-1% (NOT F347's 13.7%), then:
- CNF-only injection: ~1% on F235-class instances
- Native IPASIR-UP injection: 3-5x amplification → ~3-5%
- F361's 1.16x reopen criterion: NOT met (1.16 = 16% needed)

Phase 2D propagator's empirical case for reopen is now WEAK.

### Finding 4 — F347 / F348 re-verification needed

Concrete next probes:
(a) Re-run F347 (sr=60 bit31 m17149975 with 32 mined clauses, 5min cadical)
    multiple times with different seeds. Estimate noise floor.
(b) Re-run F348 (5 cands, 2 mined clauses) with replicate runs.

If F347 reproduces ~13%, sr-vs-encoder interaction is real and Phase
2D might still be viable for sr=60 specifically. If F347 gives
~1% on re-run, definitive negative on Phase 2D.

## Implications for bet status

programmatic_sat_propagator was BLOCKED awaiting empirical demand.
F347 looked like the demand. F365 reveals F347 was noise.

The bet's reopen criterion was sharpened to F361's 1.16x. F365
strongly suggests this criterion can't be met with current F343
mining + CNF injection approach.

The bet should remain CLOSED unless:
- F347 reproduces under controlled replication (seeds), OR
- A fundamentally different mining strategy produces stronger clauses

## Compute

- F364 mining: 780s wall (full row sweep).
- F365 comparison: 600s wall (5min × 2 cadical).
- Total: ~23 min.

## Discipline

- Honest report: F347 appears to be noise outlier.
- Phase 2D propagator viability seriously diminished.
- 7th retraction-style finding this 2-day arc (F347's 13.7% appears
  to be measurement noise).
- Concrete next: F347 replication with seeds for noise floor estimate.

## What's shipped

- F364 mining JSON (32 clauses on sr=61 bit31).
- F365 baseline + injected logs.
- This memo with refuted-F347 framing.
