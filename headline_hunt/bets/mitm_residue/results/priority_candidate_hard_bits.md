# Priority MITM Candidate: bit19_m51ca0b34_fill55555555 — Hard-Bit Signature

**Empirical 17-bit hard-residue at round 60** (1M samples, freq within [0.45, 0.55]):

| Register | Hard bits (positions, LSB=0) | Count |
|---|---|---:|
| f60 | 6, 20, 26 | 3 |
| g60 | 1, 5, 8, 11, 13, 19, 20, 25, 27, 28 | 10 |
| h60 | 2, 8, 15, 30 | 4 |
| **Total** | | **17** |

(a, b, c, d, e at round 60: all cascade-zero — 160 deterministic bits)

## Forward-table key spec

The 17-bit hard-residue signature, ordered for table indexing:
```
key = (f60[6], f60[20], f60[26],
       g60[1], g60[5], g60[8], g60[11], g60[13], g60[19], g60[20], g60[25], g60[27], g60[28],
       h60[2], h60[8], h60[15], h60[30])
```

Forward-table size: **2^17 = 131,072 distinct keys**. Each key entry stores a witness `(W1[57], W1[58], W1[59])` triple that produces this signature.

## Build budget

A 1M-sample run (already produced this measurement) yields ~131k distinct signatures with multi-hit averaging. To populate the table densely:
- Random sweep: ~10× target = 10M samples → ~5 min CPU on macbook
- Storage: ~131k entries × 12 bytes (3 × uint32) ≈ **1.5 MB** at 1 byte/key + 12 bytes/value

## Backward-table requirement

For MITM, we also need a backward analyzer: given a target round-63 collision, derive the round-60 17-bit signature it requires. Then match against forward.

The cascade structure (Theorems 1-4) gives:
- de60 = 0 forced by W[60] (cascade-2)
- da, db, dc, dd at round 63 are functions of (W[60], W[61], W[62], W[63])
- W[61..63] are schedule-determined from (W[57..60])
- For a collision target, all 8 register diffs at round 63 are zero

Backward analysis: given the cert structure, what does the round-60 signature have to be? **It's the same 17 bits.** The cascade-2 W[60] choice plus schedule-determined W[61..63] gives a deterministic mapping from round-60 state to round-63 state.

So: **build the forward table → exhaustively check 131k signatures → for each, compute the round-63 state → look for HW=0 (collision)**. That's 131k forward computes after table build, ~seconds of CPU.

## What this enables

If a cascade-DP collision exists at sr=61 for this candidate, this MITM finds it in roughly:
- 5 min: forward sweep
- Seconds: backward enumeration

Compared to the 1800 CPU-h that has been spent on TRUE sr=61 racing without finding any collision. The bet's hypothesis is that the MITM completes meaningfully faster.

By Theorem 5, cascade-DP sr=61 has SAT probability 2^-N = 2^-32 per candidate. With 17 hard bits and 35 candidates, expect ~35 × 2^-32 = 2^-27 chance any candidate has a cascade-DP sr=61 solution.

So: probably no cascade-DP sr=61 collision exists. But the MITM build provides DEFINITIVE evidence — if the table is complete and no signature matches, that's a clean cascade-DP-impossibility result for this candidate. Either outcome is informative.

## Files

- `/tmp/hr35/cand_n32_bit19_m51ca0b34_fill55555555.md` — full 1M-sample report (not committed; regenerable via hard_residue_analyzer.py)
- `final_ranking_35.json` — full 35-candidate ranking
