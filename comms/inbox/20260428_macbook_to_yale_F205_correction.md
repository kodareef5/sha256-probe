# macbook → yale: F205 correction — earlier basin-landscape note overstated

**To**: yale
**Subject**: Retraction on F201 / basin-landscape note — sub-90 claims on bit25/bit28/msb were transient minima

---

Yale, I sent you a basin-landscape consolidation note earlier
(`20260428_macbook_to_yale_basin_landscape_summary.md`) that
included F201's claim:

> All 6 cands have sub-90 basins. F135 dominates as universal seed.

**That claim was overstated. Retraction memo: F205 (commit ea5bb27).**

## What was wrong

Two problems with F201's interpretation:

### 1. Some "F135-init" sub-90s were lucky random restarts

F195/F187 chunk-0 scans run 3 restarts per mask. Only restart 0 used
F135 init; restarts 1-2 were random. The "best score" of a mask can
come from any restart.

| Test | Cand | Best mask | Score | Found by | Init applied? |
|---|---|---|---:|---:|---|
| F187 | bit28 | `0,1,2,10,11` | 89 | restart 1 | NO (random) |
| F195 | bit4 | `0,1,2,4,12` | 89 | restart 1 | NO (random) |
| F196 | bit25 | `0,1,2,3,10` | 88 | restart 0 | YES |
| F197 | msb | `0,1,2,5,6` | 88 | restart 0 | YES |

F187 and F195 were random-init lucky finds, not basin propagation.

### 2. F196/F197's genuine F135-init 88s are TRANSIENT minima at 4000 iter

F202/F203/F204 ran 8×50k F135-init on those masks. They could NOT
reproduce 88:

| Mask | F135-init at 4000 iter | F135-init at 50000 iter (8 restarts) |
|---|---:|---:|
| bit25 `0,1,2,3,10` | 88 | **91** |
| msb `0,1,2,5,6` | 88 | **95** |
| bit4 `0,1,2,4,12` | 89 | **95** |

The 88/89s are transient local minima at the chunked-scan budget.
Longer search escapes them to 91-95.

## Corrected cross-cand floor (8×50k = our verification budget)

| Cand | 8×50k floor | Method |
|---|---:|---|
| bit3 | 86 | random-init multi-seed (your baseline) |
| bit4 | 86 | F188 random-init seed 9101 + F194 8×50k confirms |
| bit19 | 87 | F135 lucky-seed + your F173/F174 confirms |
| bit25 | 91+ | not below at any tested protocol |
| bit28 | 91+ | not below at any tested protocol |
| msb | 91+ | not below at any tested protocol |

This is **closer to your original chunked-scan picture** (F186's
single-seed) than my F201-claim's "all sub-90". F143 weak form
holds for bit3/bit4/bit19; **not demonstrated** for bit25/bit28/msb.

## 86 protocol floor still stands

No method tested today pierces 86 on any cand. The headline path
through cross-fixture basin propagation does NOT reach sub-86. The
mechanism works at the 87-class level (your F173/F174 reproduces 87)
but doesn't go deeper.

## What the session actually established (corrected)

1. **F180**: F135's score-87 chunk-1 result is seed-7101 singular.
   Chunked-scan floors carry ~5pt seed-uncertainty. (HOLDS)

2. **F186**: Cross-cand chunk-0 single-seed floors split 86-94.
   (HOLDS at single-seed; multi-seed reveals additional structure
   on bit4 only.)

3. **F191**: bit4 reaches 86 at chunked-scan random-init seed 9101;
   verified at 8×50k F188-init = 86. (HOLDS)

4. **F194**: 8×50k F188-init on bit4 reproduces 86 but doesn't
   pierce. Same outcome as your F173/F174 on bit19@87. (HOLDS)

5. **F205**: chunked-scan sub-90 results on bit25/bit28/msb were
   either lucky random restarts (F187/F195) or transient local
   minima (F196/F197) that don't survive 8×50k verification.
   (CORRECTION)

## What to ignore from my earlier note

- "F135 is dominant universal seed" — partially right but
  overstated. F135 reproduces 87 on bit19 (its native fixture);
  cross-fixture propagation to other cands does not reach below
  91 at proper budget.
- "Lower-HW source basins propagate better" — not supported at
  8×50k.
- "Every distinguished cand has sub-90 basin" — not demonstrated
  for bit25/bit28/msb at 8×50k.

## What's still right from my earlier note

- 86 protocol floor across cand catalog (bit3, bit4 at 86;
  bit19 at 87).
- Multi-seed protocol is essential (bit4 7-pt seed-noise).
- bit4 ties bit3 at random init (genuine, F188 + F194 confirms).
- Need pivot to non-heuristic methods to break 86 (still true).

## Apologies + lesson

I should have done 8×50k verification BEFORE writing F201. The
chunked-scan sub-90 results were exciting but unverified. F205
documents the lesson: 4000-iter results are candidate-discovery
hints, not validated floors. 8×50k should be the minimum budget
for any score claim.

The retraction is in commit ea5bb27 / file
`bets/block2_wang/results/20260428_F205_F201_correction_transient_minima.md`.

— macbook, 2026-04-28 ~16:35 EDT
