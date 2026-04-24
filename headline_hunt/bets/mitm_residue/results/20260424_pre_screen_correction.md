# Pre-screen correction — h60+f60 ranking does NOT predict total hard-bit count

The 35-candidate pre-screen (`20260424_pre_screen_35.md`) ranks candidates by total predicted hard bits in h60 + f60 only. With 1M-sample empirical data on 3 of those candidates:

| Candidate | h60 | f60 | predicted h+f | empirical g60 | empirical TOTAL |
|---|---:|---:|---:|---:|---:|
| cand_n32_msb_ma22dc6c7_fillffffffff | 2 | 5 | 7 | 18 | **25** |
| cand_n32_msb_m189b13c7_fill80000000 | 2 | 4 | 6 | 23 | **29** |
| cand_n32_bit11_m45b0a5f6_fill00000000 | 2 | 5 | 7 | 16 | **24** |

The pre-screen ranked these 1, 2, 3 by h60+f60. The actual TOTAL hard-bit count (including g60) ranks them 2, 3, 1.

m189b13c7 has the SMALLEST h60+f60 predicted (6 bits) but the LARGEST g60 (23 bits) and total (29 bits). Pre-screen fails as a total-count proxy on it.

m45b0a5f6 has tied h60+f60 (7 bits) but lowest g60 (16) and lowest total (24). It IS the best target.

## Conclusion

The h60+f60 pre-screen predictor is informative but cannot be used as a sole ranking signal for total hard-bit count. **The ~10x weighting of g60 (~16-23 bits) versus h60+f60 (~5-9 bits) means g60 dominates the total**, and g60 is the un-predicted register.

Until g60 marginal-distribution prediction is derived, full ranking requires a 1M-sample empirical run per candidate (~1 minute CPU each). For all 35 candidates that's ~35 min CPU — still cheap.

## Updated recommendation

For finding the priority MITM target across the candidate set:
1. Run `hard_residue_analyzer.py --samples 1000000` on every candidate (~35 min total CPU).
2. Rank by total uniform bits (lowest = priority MITM target).
3. The h60+f60 pre-screen via `predict_hard_bits.py` remains useful as a fast SANITY check (zero-cost per candidate) to confirm the empirical prediction matches the closed-form for those two registers — discrepancy flags an audit problem.

The bet's economics still work — 24 vs 29 hard bits is 2^5 difference in table size, not a deal-breaker. But the priority target is **m45b0a5f6** (24-bit total) not **m189b13c7** (29-bit total), and the corrected ranking changes which candidate the bet should focus on.
