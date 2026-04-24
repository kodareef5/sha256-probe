# Pre-screen acted on: 3 minimum-dh60 candidates, kissat 600s sr=60 force — all TIMEOUT

Tested whether the algebraic dh60 pre-screen has predictive power for kissat solve time. Took the 3 candidates predicted to have the smallest dh60 hard-bit count (2 each) and ran kissat on aux-force sr=60 CNFs at 600s budget × 2 seeds.

| Candidate | dh60 hard bits | Seed=1 | Seed=5 |
|---|---:|---|---|
| cand_n32_msb_ma22dc6c7_fillffffffff | 2 | TIMEOUT | TIMEOUT |
| cand_n32_msb_m189b13c7_fill80000000 | 2 | TIMEOUT | TIMEOUT |
| cand_n32_bit11_m45b0a5f6_fill00000000 | 2 | TIMEOUT | TIMEOUT |

All 6 runs timed out at 600s. Reference: the verified sr=60 cert candidate (cand_n32_msb_m17149975, dh60=5) took 12h on STANDARD encoding with seed=5 — 10 min budget is far too short to test "is this candidate easier than 0x17149975?"

## What this means

Cannot conclude anything about pre-screen validity at this budget. Need at least 2-4h budget to differentiate "easier" from "as hard as MSB" candidates. Negative result for now.

The dashboard now shows mitm_residue with 6 runs, all timeouts, 1.0 wall-h. Combined with cascade_aux_encoding's 5 prior runs (0.5 wall-h), the audit-failure rate is 0/11 = 0% — the discipline pipeline holds up at scale.

## Implication: dh60 pre-screen is theoretically sound but operationally unproven

The closed-form algebraic prediction (`20260424_algebraic_prediction.md`) is empirically correct for the bit positions. Whether the BIT COUNT correlates with kissat solve time remains untested — would need a proper compute budget (4h × 6 runs = 24 CPU-h minimum) to settle.

If a fleet machine has 24 CPU-h to spare, this is the experiment to run:
- Pick the 3 minimum-dh60 candidates from `pre_screen_35.md`
- Pick 3 candidates from the median dh60 count (bits 3-4)  
- Pick 1-2 maximum-dh60 candidates (5 bits)
- Run kissat at 4h budget × 1 seed each on aux-force sr=60
- Compare solve times: if smaller dh60 → faster solve, the pre-screen has predictive power

Until then: pre-screen is a clean structural finding, but its operational utility is hypothetical.
