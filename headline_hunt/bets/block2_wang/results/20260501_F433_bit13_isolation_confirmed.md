---
date: 2026-05-01
bet: block2_wang
status: PATH_C_BIT13_HW50_HAMMING3_ISOLATED
parent: F432 bit13 wide anneal HW=50; F427-F431 isolation pattern on F408 panel
evidence_level: VERIFIED
compute: 0 solver search; ~125s combined (110s seeded refine + 15.5s Hamming-3 enum); 0 cert-pin runs (no new records)
author: macbook-claude
---

# F433: bit13 HW=50 also Hamming-3 isolated — same structural pattern as F408 panel cands

## Setup

After F432 produced bit13's first sub-floor record at HW=50, the
natural follow-up matched the F408-panel pattern: (a) seeded
refinement at narrow radius around the new record (cf. F427/F428
pattern), (b) deterministic Hamming-{1,2,3} ball enumeration to
classify the local geometry (cf. F429-F431 pattern).

### F433-A: seeded refinement around bit13 HW=50

Same parameters as F428: 12 restarts × 200k iter × max_flips=3 ×
temp 0.5 → 0.01 × tabu 1024, all seeded from F432 seed 4 witness:
`W1[57..60] = 0x3c2de1c6, 0x05e5f5a9, 0x1a6a8f8d, 0x5ab11fc1`.

Result: **all 12/12 seeds stayed at HW=50, score=69.78**. Identical
behavior to F427's bit28 result. No HW < 50 found.

Wall: 110.1s. Artifact:
`headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F433_bit13_seeded_refinement.json`.

### F433-B: full Hamming-{1,2,3} ball over W1[57..60] from bit13 HW=50

Combined enumeration (1-bit, 2-bit, 3-bit flips) over the full
128-bit W1[57..60] vector. **349,632 evaluations**.

Result:

| Filter | Count |
|---|---:|
| Total candidates | 349,632 |
| cascade-1 ok | 349,632 (100%) |
| bridge_score pass | 341,631 (97.7%) |
| HW ≤ 50 | 0 |
| HW < 50 | 0 |

Wall: 15.5s. Artifact:
`headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F433_bit13_hamming3_enumeration.json`.

bit13's bridge_score has 2.3% rejection rate at this radius — between
bit3's ~3-4% (F430+F431) and bit2/bit24/bit28's 0% (F430+F431).
Consistent with bit13's kbit being a "harder" structural setting
than the deep-tail dominators bit2/bit24/bit28.

## Findings

### Finding 1: bit13's HW=50 follows the same isolated-peak pattern

Both F433-A (probabilistic anneal at radius 3) and F433-B (deterministic
enumeration at Hamming-{1,2,3}) confirm zero HW-improvement at radius
≤ 3 from bit13 HW=50. This matches:

- bit28 HW=45 (F427-A + F429+F430+F431 contribution to bit28 portion)
- bit3 HW=51 (F428 stayed + F429+F430+F431 contribution)
- bit2 HW=51 (F428 stayed + F429+F430+F431 contribution)
- bit24 HW=43 (F428 breakthrough + F429+F430+F431 confirmed)

All 5 cands now have Hamming-3 isolated current bests.

### Finding 2: pattern across cands is consistent

Today's full coverage on the panel:

| Cand | F408/F432 best | F427/F428/F433 seeded refine | Hamming-{1,2,3} ball |
|---|---:|---|---|
| bit3 | 51 | F428: stayed at 51 | F429+F430+F431: 0 ≤ 51 |
| bit2 | 51 | F428: stayed at 51 | F429+F430+F431: 0 ≤ 51 |
| bit24 | 49 → 43 | F428: BROKE THROUGH 49→43 | F429+F430+F431: 0 ≤ 43 |
| bit28 | 45 | F427: stayed at 45 | F429+F430+F431: 0 ≤ 45 |
| bit13 | 50 | F433-A: stayed at 50 | F433-B: 0 ≤ 50 |

bit24 was the exception: F428's seeded refinement found a 2-bit
W1[60] perturbation that reached HW=43. After that breakthrough,
even bit24 is fully Hamming-3 isolated.

### Finding 3: bit13 has a wider basin pre-isolation

F432's wide anneal showed bit13 with the widest HW distribution
across seeds (50 to 63). But once anneal converges into the HW=50
basin, F433-A confirms the basin walls are sharp (≤ 3-bit Hamming
neighbors strictly worse).

This may be a feature of bit13 specifically (kbit=13 is structurally
"in between" bit3's deep-tail and bit24's actual-register hotspot)
or it may be a general feature of W-cube minima at higher HW —
shallower wells with wider catchment but same sharp walls.

## Verdict

- bit13 HW=50 is a sharp isolated peak at Hamming radius ≤ 3 over W1[57..60].
- All 5 cands in the current Path C panel are Hamming-3 isolated.
- The "small W-perturbation" attack vector is **fully closed** for
  this 5-cand panel.
- bit13 contributes a 9-point HW reduction (corpus 59 → 50) to Path C.

## Next

1. **F434 wider radius**: try max_flips=8 or 10 anneal seeded from
   each cand's current best. Tests whether radius > 3 finds new
   minima. ~10 min compute. Likely diminishing returns given wide
   anneal already explored 6-flip; but seeded-from-best at radius 8
   is a different exploration mode.
2. **F435: drop cascade-1 c=g=1**. Lift the geometry constraint and
   see if HW < current bests exists in a different cascade-1 fingerprint.
   Risky — produces witnesses in a different residual class — but
   informative.
3. **F436: scan more kbits**. bits 5, 7, 10, 14, etc. — kbits not in
   the current 5-cand panel. Each would give ~2 min compute and a
   potential new sub-floor record. Would build a broader Path C
   corpus.
4. **Pivot**: write a session-summary memo for the day, then pause
   for codex's quota reset (13:22 EDT, ~30 min from now).

The combined characterization (5 cands × Hamming-3 isolation +
2 breakthroughs) is a clean structural unit. Path C residual
dynamics are now well-mapped at radius ≤ 3.
