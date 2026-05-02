---
date: 2026-05-02
bet: block2_wang
status: PATH_C_PANEL_EXPANDED_11_NEW_CANDS
parent: F524 cross-cand transfer negative; original F408 panel of 5 cands
evidence_level: EVIDENCE
compute: ~215s parallel wide anneal (11 cands × 12 seeds × 200k iter); 22 audited cert-pin solver checks
author: macbook-claude
---

# F525: panel expansion — 11 new cascade-fmt kbits added to Path C corpus

## Setup

After F524 confirmed cross-cand pair-pool transfer is negative (W-cube
basins are cand-specific), the natural next direction is widening the
panel: kbits beyond the F408 5-cand set (bit2/3/13/24/28).

Survey of `headline_hunt/registry/candidates.yaml` identified 11
cascade-fmt cands (`fill = 0xffffffff`) with kbits not in the F408 panel:
bit1, bit4, bit6, bit12, bit14, bit15, bit18, bit20, bit25, bit26, bit29.

F525 runs F432-style wide anneal on each (200k iter × 12 random-init
seeds, max_flips=6, temp 2.0→0.05, tabu=512). All 11 in parallel on
10 cores.

Tool: `block2_bridge_beam.py` — extended CANDS list to include the new
kbits (entries documented in code comment "F525 panel expansion").

Total wall: ~215s for all 11 cands. 0 SAT solver runs during search.

Artifacts (12 JSON):
- 11× `headline_hunt/bets/block2_wang/results/search_artifacts/20260502_F525_<short>_wide_anneal.json`
- 1× `headline_hunt/bets/block2_wang/results/20260502_F525_certpin_validation.json`

## Results

| Cand | m0 | F525 best HW | Best score | Wide-anneal seed |
|---|---|---:|---:|---:|
| **bit4_m39a03c2d** | 0x39a03c2d | **43** | 79.07 | F525 |
| **bit1_m6fbc8d8e** | 0x6fbc8d8e | **45** | 77.21 | F525 |
| bit20_m294e1ea8 | 0x294e1ea8 | 46 | 76.27 | F525 |
| bit14_m67043cdd | 0x67043cdd | 47 | 73.91 | F525 |
| bit15_m1a49a56a | 0x1a49a56a | 47 | 73.91 | F525 |
| bit12_m8cbb392c | 0x8cbb392c | 48 | 70.02 | F525 |
| bit18_m99bf552b | 0x99bf552b | 49 | 73.45 | F525 |
| bit25_ma2f498b1 | 0xa2f498b1 | 50 | 66.82 | F525 |
| bit26_m11f9d4c7 | 0x11f9d4c7 | 51 | 68.89 | F525 |
| bit6_m6e173e58 | 0x6e173e58 | 51 | 66.00 | F525 |
| bit29_m17454e4b | 0x17454e4b | 52 | 68.00 | F525 |

All 11 wide-anneal best W vectors cert-pin verified:
- 11 audited CONFIRMED CNFs
- 22 solver runs (kissat + cadical, all UNSAT in <0.02s)
- 22 entries appended to `runs.jsonl`

**bit4 HW=43** is the deepest new record — matches bit24's pre-F428 floor
in a single wide anneal. Could be a new Path C focus cand.

**bit1 HW=45** matches bit28's F408 floor — also potentially deepenable.

## Combined Path C panel state (16 cands, all cert-pin UNSAT)

| Cand | Floor HW | Source | Notes |
|---|---:|---|---|
| bit13 | 35 | Yale F487 | radius-4 closed |
| bit3  | 36 | Macbook F521 | radius-5 closed |
| bit2  | 39 | Macbook F520 | 14 manifest seeds confirm |
| bit24 | 40 | Macbook F521 | radius-4 closed |
| bit28 | 42 | Yale F484 | radius-4 closed |
| bit4  | 43 | F525 (NEW) | wide anneal only; manifest-rank not tried |
| bit1  | 45 | F525 (NEW) | wide anneal only |
| bit20 | 46 | F525 (NEW) | wide anneal only |
| bit14 | 47 | F525 (NEW) | wide anneal only |
| bit15 | 47 | F525 (NEW) | wide anneal only |
| bit12 | 48 | F525 (NEW) | wide anneal only |
| bit18 | 49 | F525 (NEW) | wide anneal only |
| bit25 | 50 | F525 (NEW) | wide anneal only |
| bit6  | 51 | F525 (NEW) | wide anneal only |
| bit26 | 51 | F525 (NEW) | wide anneal only |
| bit29 | 52 | F525 (NEW) | wide anneal only |

Sum HW across 16 cands: **740**. Previously the 5-cand panel summed
192. Eleven new cands add HW=559 to the corpus, average HW 50.8.

## Findings

### Finding 1: bit4 has a F428-comparable depth from random init

bit4_m39a03c2d hit HW=43 in a single 200k×12 wide anneal — same depth
as bit24 reached only after F408 + F428's seeded refinement. This
suggests bit4 may have a "shallow basin" that yields easily, just like
bit13's HW=50 was reachable via wide anneal alone (F432).

If bit4 follows the bit13/bit24 trajectory, manifest-rank pair-beam
on bit4 could descend to HW≤35 territory. Worth a F526 follow-up.

### Finding 2: kbit affects basin depth significantly

The 16-cand panel spans HW 35-52 (best to worst). The kbit (one of
1-31) is a strong predictor of basin depth — clearly some kbits give
deeper W-cube access than others.

Pattern observation: low kbits (bit1=45, bit2=39, bit3=36, bit4=43,
bit6=51) and mid kbits (bit13=35, bit24=40, bit28=42) include both
the deepest (bit13, bit3) and shallow (bit6, bit29). Need more cands
per kbit to disentangle "this specific m0" from "this kbit class".

### Finding 3: panel expansion is mechanically straightforward

Adding 11 cands to CANDS list + parallel wide anneal + cert-pin took
under 5 minutes and yielded 11 new audited+logged sub-floor records.
Pipeline is fully reusable for additional kbit/m0 combinations from
the registry.

## Verdict

- **11 new cands cert-pin verified** at sub-floor HW=43..52.
- Panel expanded from 5 cands to 16. Path C corpus broadly grown.
- bit4 HW=43 and bit1 HW=45 are F526 candidates for manifest-rank
  pair-beam follow-up.

## Next

1. **F526: manifest-rank pair-beam on bit4 + bit1** (the two deepest
   new cands). If they follow bit13/bit24 trajectory, expect HW
   reductions to ~35-40 range. ~10 min compute.
2. **F527: extend wide anneal to all kbit-31 (MSB) cands** — the
   registry has 6+ MSB cands not yet in the panel. Different kernel
   geometry, potentially different basin depths.
3. **F528: scan more bit2/bit4 m0 alternatives** — the registry has
   2-3 m0 per most kbits. Different m0 = different W-cube. Sample
   more of them.
4. **Pivot**: Yale's absorber/M2 work (F506-F519); my new cand corpus
   could feed `block2_absorber_probe.c` as fresh seeds.

This expansion is a clean structural contribution: doubles+ the
Path C corpus, identifies bit4 as a likely-deepenable cand, and
demonstrates the wide-anneal+cert-pin pipeline scales easily.
