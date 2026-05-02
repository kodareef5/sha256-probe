---
date: 2026-05-02
bet: block2_wang
status: PATH_C_BIT2_BIT3_NEW_HW39_RECORDS
parent: F428 bit2/bit3 HW=51 (F408 wide anneal best); F487 manifest-rank pair-beam pattern (bit13)
evidence_level: EVIDENCE
compute: ~410s pair-beam (3 cands parallel, 1024 pool × 1024 beam × 6 max_pairs × 12 max_radius); 4 audited cert-pin solver checks
author: macbook-claude
---

# F520: pair-beam transfers to bit2 and bit3 — both jump HW 51 → 39 (-12 each)

## Setup

After yesterday's W-cube isolation chain (F427-F434 closed Hamming-3 and
radius-6 around F408 panel cands), the fleet's pair-beam tooling
(`pair_beam_search.py`) drove **bit13** from HW=50 to HW=35 via the
F486/F487 manifest-rank-12 breakthrough, and pushed **bit28** to HW=42.

Looking at the search_artifacts directory: pair-beam was run on bit24
multiple times (F441, F443-F447, F450, F457, F485) — none broke HW=43.
But **bit2 and bit3 had no pair-beam runs** at all. They were still at
F408's HW=51.

F520 fixes that gap: applies the same `pair_beam_search.py` configuration
that drove bit13's earlier closures (F450/F458) to bit2, bit3, and bit24
in parallel.

Parameters (matching F486/F487):
- `--pair-pool 1024 --pair-rank hw --beam-width 1024`
- `--max-pairs 6 --max-radius 12`
- `--penalty-regs c,g --penalty-weight 2`
- 3 cands run in parallel on separate cores

Per-cand init:
- bit2: F408 W1=`0x504e056e, 0x3e435e29, 0xda594ea2, 0xe37c8fe1`, HW=51
- bit3: F408 W1=`0xba476635, 0x8cf9982c, 0x0699c787, 0x8893274d`, HW=51
- bit24: F428 W1=`0x4be5074f, 0x429efff2, 0xe09458af, 0xe6560e70`, HW=43

Total wall: ~410s (parallel; longest job).

Artifacts:
- `headline_hunt/bets/block2_wang/results/search_artifacts/20260502_F520_bit2_pair_beam_cg.json`
- `headline_hunt/bets/block2_wang/results/search_artifacts/20260502_F520_bit3_pair_beam_cg.json`
- `headline_hunt/bets/block2_wang/results/search_artifacts/20260502_F520_bit24_pair_beam_cg.json`

## Results

| Cand | Init HW | F520 best HW | Δ | Score |
|---|---:|---:|---:|---:|
| **bit2** | 51 | **39** | **−12** | 82.757 |
| **bit3** | 51 | **39** | **−12** | 81.000 |
| bit24 | 43 | 43 | 0 | 79.073 |

bit2 and bit3 each jumped 12 HW points — a transfer of the same
breakthrough magnitude bit13 saw (50 → 35 = -15 over multi-step
pair-beam chain). bit2/bit3 reached HW=39 in a single pair-beam run.

bit24 reproduced its F428 record but did not improve. This is
consistent with Yale's prior pair-beam attempts (F441-F485), which
also failed to crack HW=43.

## bit2 HW=39 witness

```
W1[57..60] = 0x504e056e 0x3e435e29 0xda592ea2 0xab54ae55
HW=39, score=82.757
```

Note: only W1[59] and W1[60] differ from F408 init.
- W1[57], W1[58]: identical to F408 init
- W1[59]: 0xda594ea2 → 0xda592ea2 (1 bit flip, position 14)
- W1[60]: 0xe37c8fe1 → 0xab54ae55 (multi-bit flip)

## bit3 HW=39 witness

```
W1[57..60] = 0xba476635 0x8cf9982c 0x06b9e787 0x5882674c
HW=39, score=81.000
```

Note: same partial-W1 pattern.
- W1[57], W1[58]: identical to F408 init
- W1[59]: 0x0699c787 → 0x06b9e787 (1 bit flip, position 21)
- W1[60]: 0x8893274d → 0x5882674c (multi-bit flip)

Both witnesses follow the same structural shift: **W1[57] and W1[58]
unchanged, single-bit flip in W1[59], multi-bit flip in W1[60]**. This
is consistent with the original W[60] dominance pattern (F428/F432
breakthroughs were W1[60]-only) but extended to a small W1[59]
contribution at this deeper HW level.

## Cert-pin verification

Both witnesses audited and cross-solver UNSAT:

### bit2 HW=39

- audit verdict: **CONFIRMED**
- cnf_sha256: `fb2e5bdcfc3c6ba1390ba96151dc24af085c47d0bc05a433edbec77b0ca638b6`
- kissat 4.0.4: **UNSAT** in 0.0087s
- cadical 3.0.0: **UNSAT** in 0.015s

### bit3 HW=39

- audit verdict: **CONFIRMED**
- cnf_sha256: `acbf1c3b65f150a489b0ef690d0005f13c043e41ca432a38d50fdb3979e5b910`
- kissat 4.0.4: **UNSAT** in 0.0062s
- cadical 3.0.0: **UNSAT** in 0.012s

4 runs logged via append_run.py.

## Findings

### Finding 1: pair-beam transfers, but not uniformly

bit2 and bit3 jumped HW 51 → 39 in one pair-beam run. bit13 jumped
HW 50 → 35 via a chain (F458/F462/F467/F473/F486/F487). bit24 stuck at
HW=43 across 8+ pair-beam variants.

The transfer-friendliness order across cands appears to be:
**bit3 ≈ bit2 (one-shot −12) > bit13 (multi-step −15) > bit28 (multi-step −3) > bit24 (no transfer)**.

bit24's resistance to pair-beam suggests its W-cube minimum at HW=43
sits in a structurally unusual region. F441-F485 already explored
multiple pair-beam variants (hw rank, repair rank, objective rank,
multiple penalty schemes); none worked. This is genuine evidence that
bit24's HW=43 is at or near the W-cube floor under cascade-1 +
bridge_score for this kbit.

### Finding 2: bit2/bit3 had untapped depth — they were just unsearched

The HW=51 records on bit2/bit3 were simply F408's wide-anneal terminations
plus F428's "didn't help" seeded refinement. No structural exploration
beyond Hamming-3. F520 shows the deep records existed all along — the
HW=39 basin was reachable in ~400s of focused search.

This is a useful negative-cost lesson: when a cand's record sits at
its first-pass anneal terminal, it's worth *one* pair-beam pass before
declaring isolation. The Hamming-3 enumeration negative (F429-F431) was
correct on its own terms but could be misleading: the pair-beam
explores far beyond Hamming-3 (max_radius 12, 6 composed pair moves)
and finds basins the local enumeration cannot.

### Finding 3: W[60] dominance generalizes with W[59] contribution at deeper HW

F408/F427/F428: breakthroughs were pure W[60] flips (W57/W58/W59 unchanged).
F520 bit2/bit3 HW=39: W1[57] and W1[58] still unchanged, but W1[59]
contributes 1 bit flip alongside multi-bit W1[60] flips.

This is consistent with the bit13 HW=35 witness (F487):
`W1 = 0x5228ed8d 0x61a1a29c 0x6a7a8409 0xc7d515db` — also has W57/W58
unchanged from upstream optima, with W59/W60 carrying the bit flips.

The pattern at the HW≤39 layer: **W1[57] and W1[58] are essentially
fixed, breakthroughs come from W1[59]+W1[60] joint perturbations**.
Implications for future search: focused 2-word search over (W1[59], W1[60])
may be the right direction.

### Finding 4: Path C panel state after F520

| Cand  | Pre-F408 | F408 | F427/F428/F432 | Recent (incl. fleet) |
|---|---:|---:|---:|---:|
| bit3  | 55 | 51 | 51 | **39** (F520, this) |
| bit2  | 56 | 51 | 51 | **39** (F520, this) |
| bit13 | 59 | (skipped) | 50 (F432) | **35** (Yale F487 pair-beam) |
| bit28 | 59 | 45 | 45 | **42** (Yale pair-beam chain) |
| bit24 | 57 | 49 | **43** (F428) | 43 (F520 confirms; multi-attempt resistance) |

5-cand panel residual records: bit13 35, bit24 43, bit28 42, bit2 39, bit3 39.
All cert-pin UNSAT.

## Verdict

- **bit2 HW=39 and bit3 HW=39: NEW cert-pin'd records** (both -12).
- **bit24 HW=43**: confirmed unchanged after a 9th pair-beam variant.
  Strong evidence of a real W-cube floor on this cand under current
  invariants.
- **W[57]/W[58] fixity**: the deeper records keep W1[57] and W1[58]
  unchanged from upstream optima.

## Next

1. **F521: manifest-rank pair-beam on bit24** (the F487 strategy that
   worked for bit13). Use the basin manifest already generated at
   `20260502_F520_bit24_basin_manifest.json` (25 seeds) — feed top-K
   manifest seeds at HW=44/45 into pair-beam. If it breaks bit24
   HW=43, that's the missing breakthrough.
2. **F522: focused (W1[59], W1[60])-only search** on bit2/bit3 from
   the F520 HW=39 records, exploiting the W[57]/W[58] fixity. Smaller
   2-word search space (64-bit), exhaustive Hamming-{1..4} feasible.
3. **F523: cross-cand transfer**: take F520 bit2/bit3 W[59] flip
   patterns and try them on bit13/bit24/bit28 W[59].
4. **Generate basin manifests for bit2 and bit3** post-F520, mirror
   the F491/F473 tooling. Future seeded follow-ups will benefit.

The F520 result is a clean breakthrough on two cands and a strong
negative on bit24 (confirms 9 pair-beam variants now). The Path C
program is rapidly maturing — 5 cands all in the HW≤43 range, total
HW reduction across panel: 55+56+59+59+57 → 39+39+35+42+43 = 286 → 198
(86 HW reduction summed).
