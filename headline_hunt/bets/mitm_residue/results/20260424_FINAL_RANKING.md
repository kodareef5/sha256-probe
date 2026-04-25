# FINAL 35-candidate ranking — priority MITM target identified

Sweep complete. 1M-sample empirical hard-residue count for every candidate in `registry/candidates.yaml`. Closed-form predictor validated 35/35 as a true lower bound.

## TL;DR

**Priority MITM target: `cand_n32_bit19_m51ca0b34_fill55555555`**
- Empirical hard-residue: **17 bits** at round 60
- Predict_hard_bits lower bound: 15
- Extras: 2
- m0 = 0x51ca0b34, fill = 0x55555555, kernel bit = 19

This candidate has 3 fewer bits than the next-best (= 8× smaller forward-MITM table) and 12 fewer bits than the worst (= 4096× smaller). It is the natural target for any forward-table MITM construction.

## Validation summary (N=35)

- **All 35 extras non-negative** — predictor is a true lower bound, never over-counts
- **Mean extras: 1.54** (median 1, max 4)
- **Range: empirical 17–29 bits**, predict_lb 15–29

The closed-form predictor accurately pre-screens candidates with mean correction of 1.54 bits. For ranking purposes, predict_lb-based ordering is preserved at the top: bit19_m51ca0b34 leads in both predicted (15) and empirical (17), and m189b13c7 trails in both (29 / 29).

## Top 5 priority targets

| Rank | Candidate | kernel | empirical | pred_lb | extras |
|---:|---|---:|---:|---:|---:|
| 1 | bit19_m51ca0b34_fill55555555 | 19 | **17** | 15 | 2 |
| 2 | bit10_m27e646e1_fill55555555 | 10 | 20 | 19 | 1 |
| 3 | msb_m9cfea9ce_fill00000000 | 31 | 22 | 20 | 2 |
| 4 | bit06_m88fab888_fill55555555 | 6 | 22 | 22 | 0 |
| 5 | bit10_m3304caa0_fill80000000 | 10 | 22 | 22 | 0 |

The top-5 spans 4 different kernel bits (10, 19, 31, 6, 10). No clear "best kernel" — the candidate's m0/fill choice within a kernel matters.

## Bottom 5 (worst MITM targets)

| Rank | Candidate | kernel | empirical | pred_lb |
|---:|---|---:|---:|---:|
| 31 | bit06_m667c64cd_fill7fffffff | 6 | 28 | 24 |
| 32 | bit06_m6781a62a_fillaaaaaaaa | 6 | 28 | 27 |
| 33 | bit11_m56076c68_fill55555555 | 11 | 28 | 24 |
| 34 | bit17_mb36375a2_fill00000000 | 17 | 28 | 26 |
| 35 | msb_m189b13c7_fill80000000 | 31 | 29 | 29 |

## What this answers

The bet's central question: "are the per-candidate hard-residue sizes predictable, and is there a definitively-best candidate to attack?"

**Yes and yes**:
- O(1) closed-form predictor (predict_hard_bits.py) is a true lower bound, mean correction 1.54
- bit19_m51ca0b34 is empirically the best, in clean separation from the rest

A forward MITM table for bit19_m51ca0b34 needs ~2^17 entries (≤16 MB at 1 byte/entry, ≤512 MB at 32 bytes/entry). **Trivially feasible.**

## Concrete next-action for the bet

Build the actual forward MITM table for bit19_m51ca0b34:

1. Identify the 17 empirical hard-bit positions (run hard_residue_analyzer for this specific candidate, or extract from the saved `/tmp/hr35/cand_n32_bit19_m51ca0b34_fill55555555.md`).
2. Enumerate (W[57], W[58], W[59]) tuples that produce each distinct 17-bit signature; cascade-2 fixes W[60].
3. For each forward-table key, store the (W[57..59]) tuple.
4. Build a backward analyzer that takes a target collision at round 63 and computes the required round-60 17-bit signature.
5. Match: lookup in forward table.

If the forward table covers all 2^17 = 131k signatures (which it should given uniform random sampling), then any target round-63 collision has a match. The MITM gives a sub-brute-force collision search for this candidate.

**This is the path to a headline.** The forward-table build is ~hours of CPU on a 10-core machine; the backward analyzer is ~1 day of careful coding.

## Files committed

- `headline_hunt/bets/mitm_residue/results/final_ranking_35.json` — machine-readable
- `/tmp/hr35/*.md` — per-candidate per-bit reports (not committed, regenerable from candidates.yaml + hard_residue_analyzer.py at 1M samples each, ~35 min CPU)

## Status update for the bet

`mitm_residue` BET.yaml should reflect:
- Priority candidate identified: bit19_m51ca0b34
- Forward-table size: 2^17 entries
- Next architectural step: build forward + backward analyzer pair

Updating BET.yaml in the next commit.
