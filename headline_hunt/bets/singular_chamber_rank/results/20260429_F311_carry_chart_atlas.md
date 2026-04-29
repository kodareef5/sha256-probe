---
date: 2026-04-29
bet: singular_chamber_rank
status: TOOL_SHIPPED — Carry-Chart Atlas v1, structural finding on HW4 brittleness
---

# F311: Carry-Chart Atlas — chamber-vs-absorber coordinate map

## Tool

New script `headline_hunt/bets/singular_chamber_rank/tools/carry_chart_atlas.py`.
Records, for any (M1, M2, schedule) point:

- D60, D61 (defects via cascade1_offset, matches C `singular_defect_rank.c`)
- a57_guard_xor = (s1[0] ^ s2[0]) after round 56 (cascade-1 hardlock check)
- parts decomposition at round 61: dh, dSig1, dCh, dT2 with HW per part
- chart-signature: which two parts dominate (HW-rank top 2)
- per-round tail: cascade_offset, defect, parts, sums, carries, state-diff HW
- (chamber mode only) move enumeration: ±2^j on (W57, W58, W59) for j ∈ 0..31
  + small modular increments, classified as PRESERVES_CHART_AND_CLOSES_GUARD /
  PRESERVES_CHART / CLOSES_GUARD_BUT_DESTROYS_CHART / DESTROYS_CHART / NEUTRAL

Verification against C ground truth (`/tmp/singular_defect_rank tailpoint 0
0x370fef5f 0x6ced4182 0x9af03606`): tail_offsets, tail_defects, w1_tail, w2_tail
match byte-for-byte. D60=0, D61=0x80110200 (HW 4) reproduced.

## Atlas data shipped

JSONL: `20260429_F311_carry_chart_atlas.jsonl` (8 records).

### Chamber HW4 witnesses (all 3 verified cross-cand)

| Cand | W57..W59 | D60 | D61 | a57_xor | Chart top-2 |
|---|---|---:|---:|---:|---|
| idx 0  (msb m17149975) | 0x370fef5f, 0x6ced4182, 0x9af03606 | 0 | 0x80110200 (HW 4) | 0 | (dh, dCh) |
| idx 8  (bit3 m33ec77ca) | 0xaf07f044, 0x63f723cf, 0x10990224 | 0 | 0x41200001 (HW 4) | 0 | (dh, dCh) |
| idx 17 (bit15 m28c09a5a) | 0xa418c4ae, 0x47d3203e, 0x6eb1fa38 | 0 | 0x30201000 (HW 4) | 0 | (dh, dCh) |

**Unifying structural finding**: all three HW4 chambers share the same chart
top-2 (dh, dCh). This was empirically reached on three structurally distinct
cands (HW1, HW2, HW2 off58) — strong evidence the chart is candidate-agnostic.

### Block2 absorber score-86 (F115 bit3)

| Restart | Score | D61 | a57_xor | Chart top-2 | tail63 state diff HW |
|---:|---:|---:|---:|---|---:|
| 0 | 86 | 18 | 18 | (dSig1, dCh) | 128 |
| 3 | 95 | 14 | 18 | (dh, dCh)    | 124 |
| 7 | 95 | 17 | 20 | (dT2, dCh)   | 144 |
| 1 | 96 | 22 | 20 | (dCh, dT2)   | 113 |
| 4 | 96 | 18 | 16 | (dCh, dT2)   | 122 |

## Findings

### Finding 1 — Chamber HW4 lives in a SINGLE chart family

(dh, dCh) dominates in all three HW4 chambers across structurally distinct
cands. This is a coordinate-level explanation for why HW4 reproduces:
the attractor is a chart property, not a candidate property.

### Finding 2 — Absorber search is in a DIFFERENT chart from the chamber

The block2_wang score-86 absorber lives in (dSig1, dCh), and many score-95/96
restarts visit (dCh, dT2). Only one restart (score-95, r=3) accidentally lands
in the chamber chart (dh, dCh) — and even there a57_xor = 18, completely
violating the cascade-1 hardlock that all chamber witnesses satisfy.

**The block2 absorber search has not been finding cascade-compatible points.**
The score-86 floor is in the wrong half-plane of carry-coordinate space.

### Finding 3 — HW4 chamber is BRITTLE in W57/W58/W59 1-bit neighborhood

Move enumeration: 140 single-bit and small-modular moves per chamber, 420 total.

| Cand | DESTROYS_CHART | NEUTRAL | PRESERVES_CHART | HOLY_GRAIL |
|---|---:|---:|---:|---:|
| idx 0  | 71  | 69 | 0 | 0 |
| idx 8  | 99  | 41 | 0 | 0 |
| idx 17 | 119 | 21 | 0 | 0 |

**No 1-bit / small-modular move on (W57, W58, W59) preserves the (dh, dCh)
chart and reduces D61 below the HW4 floor. NONE.** The chamber is an isolated
point in W-space at the resolution of single-bit moves.

This is a structural negative for the "small move on schedule freedom" hypothesis
— if a chart-preserving D60-closing move existed in a 1-bit neighborhood we
would have found it. It does not.

### Finding 4 — Hidden classification: a57_xor IS the discriminator

Chambers: a57_xor = 0 (always). Absorbers: a57_xor ∈ {16, 18, 20}. The
carry-chart atlas reveals that the cascade-1 hardlock and the chart membership
are coupled: the (dh, dCh) chamber chart appears to require a57_xor = 0, while
absorbers in (dSig1, dCh) / (dCh, dT2) charts have substantial state-0
divergence at round 56. This is consistent with the F123 "structured moves
must preserve late-schedule features" memo and the F286 132-bit hard core.

## What this means for Tool 2 (schedule-space absorber search)

The atlas suggests a coordinate-aware loss for Tool 2:

1. **Filter candidates by a57_xor = 0 BEFORE evaluating schedule loss.** The
   block2 absorber search currently mutates raw M0..M15 and accepts any
   reduction in chain-output diff; it never enforces the cascade-1 hardlock.
2. **Score by chart proximity to (dh, dCh).** A score-86 absorber in (dSig1,
   dCh) is fundamentally in a different geometry than a chamber witness;
   even reducing it to score-50 would not produce a chamber-compatible point.
3. **Search in dW[16..23] preimage space** (Tool 2 plan), but bias the
   acceptance: prefer points where the projection at round 61 lands in the
   (dh, dCh) chart with a57_xor near zero.

## What this means for Tool 1 itself

The brittleness in 1-bit (W57, W58, W59) moves means the holy-grail move
operator (PRESERVES_CHART_AND_CLOSES_GUARD), if it exists, is NOT in this
neighborhood. Worth probing:

- 2-bit and 3-bit combined moves on (W57, W58, W59) — combinatorially larger
  but feasible to enumerate ~5000 combos per chamber.
- Moves on the M-side directly (small dM[0..15] perturbations) that propagate
  into the 132-bit universal hard-core space — this couples to Tool 2.
- Moves on the carry-coordinate parts directly (parts[0..3]) — search in
  sums/carries space rather than W-space.

## Discipline

- Tool verified against C `singular_defect_rank.c` ground truth on idx=0 chamber.
- All findings derived from the verified atlas JSONL; no inference beyond what
  the records show.
- Negative on holy-grail move enumeration is honest — the brittleness is real
  evidence, not a tool bug.
- ~3 hours wall.

## Cross-bet

- Tool 2 plan is now coordinate-informed: enforce a57_xor = 0 + chart proximity
  before scoring schedule loss. This is more restrictive than the original
  raw-distance score and addresses why block2_wang plateaus at score 86.
- The HW4 chamber attractor's brittleness shifts emphasis toward Tool 2
  schedule-space search rather than Tool-1-style local W moves.

## Next actions

(a) Extend `carry_chart_atlas.py` to support 2/3-bit combined moves and M-side
    moves (Tool 1 v2).
(b) Begin Tool 2 (`preimage_lift.py` for dW[16..23] only) with the
    coordinate-informed loss.
(c) Use the atlas as the loss function for Tool 2's search loop:
    score = (a57_xor_hw) * 4 + (D61_hw) + 8 * (chart_top != ('dh','dCh')).
