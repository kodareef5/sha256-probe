---
date: 2026-04-28
bet: block2_wang
fixture: bit19_HW56_51ca0b34_naive_blocktwo
status: PARTIAL_CONFIRMS_F174
---

# F176: macbook independent radius-1 8x50k continuation — partial confirmation of yale's F174

## Setup

While yale's F174 was running its F135-seeded continuation on the radius-1
top-K, macbook's parallel batch picked the top-10 masks from F172's
3x4000 pass and reran each at **8 restarts × 50000 iterations**. This is
the budget yale identified (and that F172's calibration finding confirmed)
as the right per-mask threshold for definitive local-minimum hits.

The two batches duplicate each other in spirit. They were launched in
parallel without coordination, hence the F-number collision and the
duplicated work. Macbook's run was retained as **independent
cross-confirmation** rather than killed mid-flight.

## Results so far (5 of 10 masks complete)

| Active words | Best score | Best restart |
|---|---:|---:|
| `0,1,2,8,13` | 92 | 2 |
| `0,2,8,9,11` | 92 | 7 |
| `0,2,8,9,12` | 94 | 2 |
| `1,2,7,8,9`  | 92 | 3 |
| `1,2,8,9,13` | 93 | 4 |

(In flight: `0,1,2,4,9`. Pending: 4 more masks.)

## Interpretation

Every completed mask scores **≥ 92** under the 8x50k budget. None reaches
yale's `0,1,3,8,9` floor of 87. None reaches the 91 plateau seen as the
weak runner-up class in the F172/F173 partial scans.

Combined with yale's F174 (full 55-mask 8x50k continuation seeded from
F135 finds only `0,1,3,8,9` below 91), this independent macbook batch
provides cross-confirmation that:

1. The radius-1 family of bit3's `{0,1,2,8,9}` does NOT contain a
   sub-87 mask on bit19_m51ca0b34.
2. `{0,1,3,8,9}@87` is a sharp local winner inside the F135 basin, not
   a member of a broad low-budget plateau.
3. The bit19 fixture-local optimum has measurable structure that is
   localized at radius 1 but does not transfer at radius 1 from bit3.

## Next-step priority (per F156)

Other distinguished cands have **never** had fixture-local scans:

| Cand | Fixture bundle exists | Scanned? |
|---|---|---|
| bit19_m51ca0b34 | yes | yes (chunks 0-8 + 34-45 + radius-1) |
| bit28_md1acca79 | yes (HW=59) | **no** |
| bit4_m39a03c2d  | yes (HW=63) | **no** |
| bit25_m09990bd2 | yes (HW=62) | **no** |
| msb_m9cfea9ce   | yes (HW=62) | **no** |

**Highest-leverage next move**: chunk-0 fixture-local scan on
bit28_md1acca79. This is yale's primary structurally-distinguished
cand (de58_size below median, hardlock_bits) and has never been
probed for fixture-local active-word physics. Either it shows
fixture-local optima ≥ bit19's 87 (transfer fails generally) or it
reveals a sub-87 absorber elsewhere in the cand catalog (genuine
structural-distinction signal).

Macbook will start this scan as the F174 batch finishes, to keep
fleet cores busy without contention.

## Discipline

- 0 SAT compute (heuristic local search only)
- 0 solver runs
- F-number collision with yale (both used F174); macbook's continuation
  memo numbered F176 to disambiguate
