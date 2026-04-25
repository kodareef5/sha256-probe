# Phase 2C-Rule4 500k confirmation — firing is FRONT-LOADED, slowdown PERSISTS

## Setup

Repeated the WITH/WITHOUT propagator comparison at **10× higher conflict budget** (500k instead of 50k) on the 3 highest-firing kernels (bit-19, bit-25, bit-31). Same v3 sr=61 force CNFs. cadical 3.0.0.

## Results

| kernel | 50k ratio | 500k ratio | 50k Rule 4 fires | 500k Rule 4 fires |
|---|---:|---:|---:|---:|
| bit-19 | 2.18× slower | **1.70×** | 209 | **209** |
| bit-25 | 1.94× | 2.02× | 249 | **249** |
| bit-31 | 1.89× | 1.88× | 201 | **201** |

(All runs UNKNOWN at budget.)

## Two important findings

### 1. Slowdown ratio doesn't significantly improve at higher budget

| kernel | 50k → 500k slowdown trajectory |
|---|---|
| bit-19 | 2.18× → 1.70× (slight improvement) |
| bit-25 | 1.94× → 2.02× (slight degradation) |
| bit-31 | 1.89× → 1.88× (unchanged) |

**Mean ratio stays ~1.9×.** The propagator's per-conflict overhead is approximately constant; it doesn't get amortized away by more conflicts.

### 2. Rule 4 fires THE SAME NUMBER of times at 50k and 500k

This is the more important finding. **All Rule 4@r=62 firings happen in the first ~50k conflicts.** After that, ZERO additional fires across conflicts 50k-500k.

What this means:
- The partial-bit Rule 4 trigger condition (enough input bits of `a_61`, `a_60`, `a_59`, `a_62` decided in BOTH pairs to compute a bit of dT2_62 + dA[62]) is met during EARLY CDCL — likely during preprocessing when cascade-zero unit clauses massively propagate.
- After CDCL warms up and starts navigating the residual search space, the input bits are RARELY all decided simultaneously at any sample point.
- So Rule 4 is empirically **a preprocessing-phase constraint**, not a deep-search accelerator.

## Implication for the bet

This **refines the bet's hypothesis empirically**:

The original SPEC ("≥10× conflict-count reduction at full budget via cascade-aware propagation") implicitly assumed Rule 4 would fire continuously throughout the search. **It doesn't.** It fires ~200 times during preprocessing/early CDCL and then goes silent.

In that respect, Rule 4 is **structurally the same as Mode B's static unit clauses** — preprocessing-phase constraint injection. Different mechanism (dynamic vs static), similar effect (early pruning that doesn't compound).

This is consistent with the cascade_aux_encoding bet's prior finding: Mode B's 2-3.4× wall-time speedup is FRONT-LOADED, eroding to ~1× at 500k+ conflicts. Rule 4 follows the SAME pattern.

## Honest assessment of the bet

The bet's value-add hypothesis is **empirically refined to**: "modular-arithmetic constraints inject extra structure during preprocessing/early CDCL, equivalent to Mode B's preprocessing speedup but via a different mechanism."

**The bet does NOT yet show value-add over Mode B.** Mode B is simpler (static CNF unit clauses, no propagator overhead) and achieves similar early pruning. The propagator's added complexity (~750 LOC + dependency on CaDiCaL IPASIR-UP) is justified only if it provides MORE constraint-injection than Mode B can.

## What WOULD validate the bet

For Rule 4 to deliver on the SPEC's hypothesis, ONE of:
- **Find a way to keep Rule 4 firing during deep search.** Currently the trigger condition (all relevant input bits decided simultaneously) only fires early. Maybe a smarter trigger that fires on PARTIAL knowledge (e.g., when bit i of dT2_62 is determinable, force the modular relation directly without waiting for full input decisions).
- **Add Rule 6 at r=63 plus more rules.** Each new rule adds early-phase fires; if collectively enough to dominate Mode B, the bet wins.
- **Find a cascade-DP CNF where Rule 4 is essential to find SAT.** I.e., one where vanilla cadical can't solve in any reasonable budget but propagator can.

The third is what would actually be a headline. The first two are incremental improvements over Mode B.

## Decision-gate update

Per kill_criteria.md: ≥10× conflict-count reduction at N=8 OR kill.

This experiment doesn't directly measure conflict-count-to-SAT (both runs hit UNKNOWN at budget), but the firing-rate finding strongly suggests the propagator won't reach 10×. **Recommend conditional kill**: if Rule 4 firings remain front-loaded (verified across all kernels), the bet's value-add hypothesis is empirically equivalent to Mode B preprocessing. Continue only if a new mechanism (smarter trigger, more rules) emerges.

## Build artifact

Same propagator binary. Run logs in this directory.

## What this gives the fleet

A real diagnostic: when a future worker considers running the multi-hour decision-gate experiment, this 500k data plus the front-loaded firing finding strongly predict the outcome. **Save the multi-hour CPU-h until either the propagator changes (smarter triggers / more rules) OR a specific candidate is identified that vanilla cadical genuinely can't solve.**
