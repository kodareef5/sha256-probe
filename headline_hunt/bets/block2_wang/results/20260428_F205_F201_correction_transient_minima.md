---
date: 2026-04-28
bet: block2_wang
status: F201_OVERSTATED — sub-90 chunked-scan results are TRANSIENT minima at 4000 iter
---

# F205: F201 correction — chunked-scan sub-90 basin-init results are transient minima

## What went wrong in F201

F201 reported that F135-init basin propagation reaches sub-90 on every
distinguished cand:
- bit4 → 89 (F195, mask `0,1,2,4,12`)
- bit25 → 88 (F196, mask `0,1,2,3,10`)
- msb → 88 (F197, mask `0,1,2,5,6`)
- bit28 → 89 (F187, mask `0,1,2,10,11`)

**Two separate problems with that interpretation:**

### Problem 1: Some "F135-init" results were lucky random restarts

Each chunk-0 scan runs 3 restarts per mask. With `--init-json`, only
restart 0 starts from F135's M1; restarts 1-2 use random init. A
mask's "best score" can come from any of the 3 restarts.

Re-examining which restart produced each sub-90:

| Test | Cand | Best mask | Best score | Found by restart | Init applied? |
|---|---|---|---:|---:|---|
| F187 | bit28 | `0,1,2,10,11` | 89 | **restart 1** | NO (random init) |
| F195 | bit4 | `0,1,2,4,12` | 89 | **restart 1** | NO (random init) |
| F196 | bit25 | `0,1,2,3,10` | 88 | restart 0 | YES (F135 init) |
| F197 | msb | `0,1,2,5,6` | 88 | restart 0 | YES (F135 init) |

F187 (bit28→89) and F195 (bit4→89) were lucky random-init restarts
that happened to land in good basins. F135 init was attached to
restart 0 of those scans, but restart 0 didn't produce the headline
score. F201's claim "F135 init reaches 89 on bit4 and 89 on bit28"
is technically incorrect — *some* restart reached those scores while
F135 init was attached to *one* of the 3 restarts.

### Problem 2: 8×50k continuation can't reproduce F196/F197

F202-F204 ran 8×50k F135-init continuations on the genuine F196/F197
sub-90 masks (where restart 0 actually used F135 init):

| Mask | F135-init 4000 iter | F135-init 50000 iter (8 restarts) |
|---|---:|---:|
| bit4 `0,1,2,4,12` (F202) | 89 (was random restart anyway) | **95** |
| bit25 `0,1,2,3,10` (F203) | 88 (genuine F135 init) | **91** |
| msb `0,1,2,5,6` (F204) | 88 (genuine F135 init) | **95** |

Longer budget from same init produces *worse* scores. The 88s on
bit25 and msb were **transient local minima** — the 4000-iteration
simulated-annealing schedule stopped mid-search inside a non-basin
local minimum. Longer search (50000 iter) escapes the transient
minimum and finds the true basin floor at 91-95.

## Corrected cross-cand floor table

Using only the **8×50k budget** as the protocol-floor reference (since
4000 iter produces transient minima that don't survive verification):

| Cand | 8×50k random init | 8×50k F135-init | True floor |
|---|---:|---:|---:|
| bit3 | 86 (multi-seed verified) | not retested | **86** |
| bit4 | 94 (F193) | 86 (F194 from F188 init) / 95 (F202 from F135 init) | **86** |
| bit19 | 95 (F176) | 87 (yale F173/F174) | **87** |
| bit25 | not tested | 91 (F203) | **91** |
| bit28 | not tested | 91+ (F200 chunked → 92) | **91** |
| msb | not tested | 95 (F204) | **91** |

**Cross-cand 8×50k protocol floor: 86 (bit3, bit4) – 87 (bit19) – 91+
(bit25/bit28/msb).**

The original F186 picture is closer to right than F201's "all sub-90".
F186 said: bit3=86, bit19=90, msb=91, bit28=91, bit4=93, bit25=94.
The corrected F205 picture says: bit3=86, bit4=86 (with right seed),
bit19=87, bit25/bit28/msb ~= 91.

## What still holds from F201

- **F143 weak form mostly holds**: bit4 finds 86 from random-init
  with the right seed (verified at 8×50k via F188 init in F194).
  bit19 finds 87 via F135 init (verified at 8×50k by yale's F173/F174).
- **Cross-fixture basin propagation works at 87-class level**:
  F135's M1 reaching bit19's 87 is genuine. Whether it propagates
  to a deeper-than-86 basin on any cand is *not* demonstrated.
- **The 86 protocol floor stands**: no method tested today pierces
  it on any cand.

## What does NOT hold from F201

- **bit25/bit28/msb do NOT have demonstrated sub-90 basins** at
  8×50k budget. The F196/F197/F187 "sub-90" results were either
  lucky random restarts (4000 iter) that don't survive longer
  budget, or transient local minima.
- **F135 is not "dominant universal seed" at proper budget.** At
  8×50k, F135 init on bit25/bit28/msb gives 91+, no better than
  random init on those cands.
- **The msgHW=54 hypothesis** (F201's idea that lower-HW source
  basins propagate better) is not supported by 8×50k data. It was
  inferred from chunked-scan transient minima.

## Calibration finding

This is the third calibration finding of the day:
1. F179: chunked-scan budget below per-mask basin-finding threshold.
2. F180: chunked-scan floor is seed-dependent (~5pt uncertainty).
3. **F205: chunked-scan sub-90 results can be transient minima that
   don't survive 8×50k verification**.

Going forward, **8×50k is the minimum budget for any score-claim
on a new mask**. 4000-iteration chunked-scan results should be
treated as candidate-discovery hints, not validated basin floors.

## Implications for fleet protocol

Yale's chunked-scan campaign (chunks 9-33 etc.) returns 4000-iter
top-K masks. Each top-K mask should be **8×50k-verified before being
treated as a real basin**. Single-seed chunked-scan reports a
*candidate basin*, not a *confirmed floor*.

The corrected protocol:
- 4000-iter chunked-scan: candidate-discovery (cheap, broad).
- 8×50k continuation on top-K: verification (expensive, narrow).
- Multi-seed across both: seed-noise mitigation.

## What's NOT changing

- **bit3@86 is still verified** (yale's pre-pause campaign).
- **bit4@86 is still verified** at 8×50k via F188+F194.
- **bit19@87 is still verified** at 8×50k via yale's F173/F174.
- Cross-fixture basin propagation **as a mechanism** still works
  at the 87-class level (F135 → bit19's 87 reproduces).
- 86 protocol floor still stands.

## Honest summary

The session's late-afternoon arc produced real findings (F176, F179,
F180, F186, F191, F193, F194) and one substantially-overstated finding
(F201). F205 corrects F201. The corrected picture is closer to F186's
original conclusion: **bit3 has the deepest robust basin in the cand
catalog. bit4 has a comparable basin findable by lucky seed. bit19's
basin is 1pt shallower. bit25/bit28/msb basins (if they exist) are
not at sub-90 at 8×50k.**

The 86 floor stands. The headline path remains through non-heuristic
methods.

## Discipline

- 0 SAT compute (heuristic local search only)
- 0 solver runs
- This memo retracts F201's strongest claim
- Ship-correction integrity > narrative momentum

This is the kind of correction that's painful to write but
necessary. The chunked-scan transient-minima problem is now
documented; the fleet protocol is sharper.
