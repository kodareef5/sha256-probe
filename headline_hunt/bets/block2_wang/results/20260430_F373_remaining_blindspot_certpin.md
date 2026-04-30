---
date: 2026-04-30
bet: block2_wang
status: F371 BLIND_SPOT FULLY CLOSED — direct cert-pin coverage now 67/67 = 100%
parent: F372 (closed the 4 sub-floor witnesses)
follow_up_to_f100: yes — completes full registry direct cert-pin coverage
---

# F373: cert-pin verify the 9 remaining blind-spot cands → all UNSAT (100% direct coverage)

## Setup

F371 (this same date, ~07:50 EDT) found F100's cert-pin sweep covered
54 cands (not the documented 67), with 13 cands in the blind spot.
F372 (~08:10 EDT) verified the 4 sub-floor witnesses (HW 55-61) — all
UNSAT. F373 closes the loop on the remaining 9 cands at HW≥62.

The 9 remaining blind-spot cands:

| cand                                       | min HW | corpus records |
|--------------------------------------------|-------:|---------------:|
| cand_n32_bit18_m99bf552b_fillffffffff      |   61   |     3,634      |
| cand_n32_bit11_m45b0a5f6_fill00000000      |   62   |     3,643      |
| cand_n32_bit25_m09990bd2_fill80000000      |   62   |     3,745      |
| cand_n32_msb_m9cfea9ce_fill00000000        |   62   |     3,735      |
| cand_n32_bit4_m39a03c2d_fillffffffff       |   63   |     3,638      |
| cand_n32_msb_m189b13c7_fill80000000        |   63   |     3,787      |
| cand_n32_msb_ma22dc6c7_fillffffffff        |   63   |     3,704      |
| cand_n32_bit10_m075cb3b9_fill00000000      |   65   |     3,761      |
| cand_n32_msb_m17149975_fillffffffff        |   69   |    10,000      |

(`cand_n32_msb_m17149975_fillffffffff` is the verified-sr60-collision
cand. Its sr=60 collision is at a specific W-vector with HW=0 register
diffs (per `datasets/certificates/sr60_n32_m17149975.yaml`). The HW=69
W-witness here is from random sampling at NON-collision points; cert-pin
on it returns UNSAT (near-residual), as expected.)

## Method

Identical pipeline to F372:
1. `cascade_aux_encoder.py --sr 60 --mode expose --varmap auto`
2. `build_certpin.py --w57..60 ...`
3. kissat 4.0.4 + cadical 3.0.0 at 5s budget each
4. `append_run.py` per (cand, solver) pair

Persisted CNFs: `/tmp/F373_*_certpin.cnf` (13179-13255 vars, 54746-55075
clauses + 128 unit pins each).

## Result

```
cand                          kissat        cadical       verdict
bit18_m99bf552b (HW=61)       UNSAT 0.01s   UNSAT 0.01s   near-residual
bit11_m45b0a5f6 (HW=62)       UNSAT 0.01s   UNSAT 0.01s   near-residual
bit25_m09990bd2 (HW=62)       UNSAT 0.01s   UNSAT 0.01s   near-residual  ← F235 cand
m9cfea9ce      (HW=62)       UNSAT 0.01s   UNSAT 0.03s   near-residual
bit4_m39a03c2d (HW=63)       UNSAT 0.01s   UNSAT 0.01s   near-residual
m189b13c7      (HW=63)       UNSAT 0.01s   UNSAT 0.02s   near-residual
ma22dc6c7      (HW=63)       UNSAT 0.01s   UNSAT 0.01s   near-residual
bit10_m075cb3b9 (HW=65)       UNSAT 0.01s   UNSAT 0.02s   near-residual
msb_m17149975  (HW=69)       UNSAT 0.01s   UNSAT 0.01s   near-residual
```

**Total: 18/18 UNSAT, 2-solver agreement on all 9 cands. 0 SAT.**

## Findings

### Finding 1 — F371 blind spot fully closed; F100's conclusion stands at 100% coverage

After F100 + F372 + F373: **all 67 registered cands have direct cert-pin
verification**. 54 from F100, 4 sub-floor from F372, 9 from F373.

The negatives.yaml `single_block_cascade1_sat_at_compute_scale` claim is
now empirically grounded at full registry coverage:

  - 67/67 cands directly cert-pin verified (was 54/67 effective per F100)
  - 0 SAT across direct cert-pin verifications
  - HW range tested (per-cand lowest-HW witness): [55, 69]
  - 2-solver agreement (kissat + cadical) on every verification

### Finding 2 — bit25_m09990bd2 (F235's cand) is in the blind spot

`cand_n32_bit25_m09990bd2_fill80000000` is the cand the F235 hard
instance is built on. The blind spot included this cand; F373 has
now cert-pin verified its lowest-HW W-witness (HW=62) → UNSAT. F235's
sr=61 cascade-1 difficulty isn't going away — the cand's residuals
are near-residual at sr=60, consistent with the broader pattern.

### Finding 3 — Cert-pin instances are uniformly UP-derivable UNSAT

Across all 18 F373 runs (9 cands × 2 solvers): every instance returned
UNSAT in 0.01-0.03s. Combined with F372's 8 runs and F100's 540
verifications, this is a strong empirical fingerprint: **cert-pin'd
near-residuals at HW range [44, 120] are UP-decidable UNSAT**, not
deep-search hard. The cascade-1 hardlock + W-pin combination either
admits a model trivially (collision) or unit propagation derives
contradiction in <100ms.

This is methodology-relevant for the broader project: cert-pin can
batch-verify thousands of W-witnesses per minute. **Throughput is not
the bottleneck.** The bottleneck is generating the right W-witnesses
to test (i.e., which W-vectors are most likely to admit collision
under cert-pin).

### Finding 4 — F371's would_change_my_mind trigger is fully NOT_FIRED

The trigger I added in F371: "An existing-registry cand whose corpus
contains a W-witness below F100's covered min_hw floor (61) admits
single-block SAT under cert-pin." After F372 + F373, this trigger
is empirically NOT_FIRED at all 13 blind-spot cands' lowest-HW
witnesses (HW range [55, 69]). The single-block sr=60 cascade-1
collision invariant holds at 100% registry coverage.

## Negatives.yaml soft revision

Update `single_block_cascade1_sat_at_compute_scale` `why_closed` to
reflect 100% coverage:

  Before: "67 distinct cands (full registry coverage) — see F371
    (2026-04-30) caveat below"
  After:  "67 distinct cands directly cert-pin verified — F100 (54
    cands) + F372 (4 sub-floor cands) + F373 (9 remaining blind-spot
    cands). 100% direct registry coverage."

The F371 caveat in `why_closed` should be updated from "F100 was
actually 54 cands" to "F100 + F372 + F373 = 67 cands now directly
verified; the gap surfaced by F371 is closed."

## Compute discipline

- 9 base CNFs + varmaps generated via cascade_aux_encoder.py
- 9 cert-pin CNFs persisted in /tmp/F373_*_certpin.cnf
- 18 solver runs (9 × 2), all UNSAT, all logged via append_run.py
- Total wall: ~45s for CNF generation + ~0.3s solver runs ≈ 1 min
- All runs logged with --allow-audit-failure (transient /tmp paths)
- sr61_n32 bet kill criterion: not tripped (0/83 audit failures
  unaffected)

## What's shipped

- `20260430_F373_remaining_blindspot_certpin.json` (raw stats)
- This memo
- 18 entries in `headline_hunt/registry/runs.jsonl`
- 9 transient cert-pin CNFs in /tmp (not committed)

## F371 → F372 → F373 chain summary

The 3-memo chain demonstrates the project's discipline pattern:

1. **F371 (~07:50)**: Used `extract_top_residuals.py` (shipped 1 hour
   prior at 31f902f) to surface F100's 13-cand blind spot. Produced
   the bit3 HW=55 lead — strongest single residual in the corpus.

2. **F372 (~08:10)**: Cert-pin verified the 4 sub-floor witnesses
   (HW 55-61). All UNSAT. The HW=55 lead is a near-residual.

3. **F373 (~08:30)**: Cert-pin verified the 9 remaining blind-spot
   witnesses (HW 61-69). All UNSAT. **Direct cert-pin coverage now
   67/67 = 100%.**

Total session compute: ~3 minutes wall, 26 cert-pin runs logged.
Direct registry coverage went from 54/67 (~80%) to 67/67 (100%) in
one session via 3 commits. F100's headline conclusion stands at
strict registry-wide coverage.

## Cumulative cert-pin coverage state (after F373)

| Source       | n_cands | runs                     | verdict   |
|--------------|--------:|--------------------------|-----------|
| F70-F100     | 54      | ~540                     | All UNSAT |
| F372         | 4       | 8 (4 cands × 2 solvers)  | All UNSAT |
| F373         | 9       | 18 (9 cands × 2 solvers) | All UNSAT |
| **Total direct** | **67/67** | **~566** | **All UNSAT** |

The empirical foundation under
`negatives.yaml#single_block_cascade1_sat_at_compute_scale` is now
both broader (registry-complete) and deeper (lowest-HW witnesses
including the previously-unverified bit3 HW=55).

## Next moves

(a) **Soft-update negatives.yaml** with F373's 100% coverage finding.

(b) **The next-headline move stays** the cluster-analysis follow-up
    on `extract_top_residuals.py --hw-max 60 --top-k 1000` — find
    structural patterns in the lowest-HW residuals that random
    sampling missed. Pure data-exploration, no compute.

(c) **Sanity check**: F235 cand bit25_m09990bd2 is now confirmed
    cert-pin UNSAT at HW=62. F235's sr=61 cascade-1 difficulty
    isn't related to "we haven't checked the obvious cert-pin yet"
    — it's a deep search problem on the basic-cascade encoder.
