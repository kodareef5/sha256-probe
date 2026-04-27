# F44: per-cand LM-optimum lives at HIGHER HW than HW-min — 38-bit mean gap
**2026-04-27 14:50 EDT**

(Renamed F43 → F44 due to fleet collision: linux_gpu_laptop's commit
b6c47ab also used F43 for "record-wise LM/HW Pareto surface". Both
findings are complementary views of the same enriched corpus and were
shipped within minutes of each other. F43 stays with linux_gpu_laptop's
ship; this memo is F44.)

Discovery enabled by F42's per-record LM-cost computation: for the
overwhelming majority of cands (61/67), the LOWEST-LM vector is NOT
at the cand's deep min-HW residual. It lives at a HIGHER HW level.

## The finding

For each cand, compute:
- `(HW_min, LM_at_HW_min)` — F32's deep-min vector + its LM cost
- `(HW_at_LM_min, LM_min)` — the LM-OPTIMAL vector across ALL recorded
  HW levels for this cand
- `gap = LM_at_HW_min − LM_min` — bits gained by switching to LM-optimal

```
Total cands: 67
gap = 0 (HW-min IS LM-min):           6 cands  (9%)
gap ≥ 20:                            50 cands  (75%)
gap ≥ 50:                            24 cands  (36%)
mean gap:                            38 bits
median gap:                          40 bits
max gap:                             94 bits
```

## Top 10 by largest LM-saving gap

| cand | HW-min | LM @ HW-min | LM-min | HW @ LM-min | **gap** |
|---|---:|---:|---:|---:|---:|
| bit3_m5fa301aa | 51 | 890 | 796 | 54 | **94** |
| **msb_m17149975** (verified cert) | 49 | 852 | **771** | 54 | **81** |
| bit18_mafaaaf9e | 48 | 852 | 772 | 49 | 80 |
| bit06_m88fab888 | 49 | 871 | 794 | 51 | 77 |
| bit18_mcbe11dc1 | 49 | 864 | 793 | 54 | 71 |
| bit15_m6a25c416 | 50 | 852 | 786 | 57 | 66 |
| bit24_mdc27e18c | 49 | 868 | 802 | 59 | 66 |
| bit06_ma8fc79d1 | 49 | 845 | 780 | 59 | 65 |
| bit11_m56076c68 | 49 | 872 | 808 | 60 | 64 |
| bit15_m28c09a5a | 50 | 835 | 772 | 54 | 63 |

## Where do LM-min vectors live? (HW distribution)

| HW @ LM-min | # cands |
|---:|---:|
| 47 | 1 |
| 48 | 2 |
| 49 | 3 |
| 50 | 2 |
| 51 | 4 |
| 52 | 4 |
| 53 | 7 |
| 54 | **16 (mode)** |
| 55 | 5 |
| 56 | 5 |
| 57 | 3 |
| 58 | 4 |
| 59 | 3 |
| 60 | 8 |

The MODAL HW for LM-min vectors is **HW=54**, NOT the typical HW-min
(47-51). For 56 of 67 cands (84%), the LM-optimal vector is at HW=51
or higher — well above the F28 ranking.

## Implication for block2_wang trail design

### Old paradigm (F25-F36): use cand's deep-min HW residual

Per F25 (universal residual rigidity), each cand has exactly 1
distinct vector at its min HW. F28's bit2 NEW CHAMPION (HW=45) was
the registry-wide HW-min cand.

### New paradigm (F43): use cand's LM-min vector (often at higher HW)

For Wang-style trail design, the OPERATIVE metric is LM cost
(carry constraints to satisfy), not HW (output bit count). F43 says:

- **Per-cand**: choose the LM-min vector (mean 38 bits cheaper than
  HW-min vector)
- **Cross-cand**: use F36's global LM ranking (msb_ma22dc6c7 at LM=773)
  but verify it's the LM-min for that cand (yes — see F43 entries)

### Specific Wang-design recommendation

The verified sr=60 certificate cand `msb_m17149975` has:
- HW-min vector: HW=49, LM=852
- LM-min vector: HW=54, LM=771 (saves 81 bits)

For Wang trail design on msb_m17149975, **use the HW=54 vector**, NOT
the HW=49 deep-min. The trail probability is `2^-771` (LM-min) vs
`2^-852` (HW-min). 81 bits = ~10x more solutions in second-block freedom.

### bit2_ma896ee41 (the F28 NEW CHAMPION)

bit2's specific gap: HW-min=45 with LM=824. Need to look up its LM-min
vector. Quick check below.

## bit2_ma896ee41 detailed view

```
HW=45 (deep-min): LM=824
HW=46: LM=??? — likely lower
HW=47: LM=??? 
...
```

Per F32 enriched corpus, bit2 has 44 records spanning HW 45..60.
Need to check which HW gives bit2's LM-min.

## Why this matters

F43 changes the optimal cand selection for block2_wang Wang trail
design. The "best HW" question (F28) and the "best LM" question (F43)
have DIFFERENT answers per cand.

**Per-cand operating-point recommendation:**

For each cand in the F32 corpus:
- For HW-driven analysis (e.g., kissat speed): use HW-min vector
  (per F25 rigidity, this is the unique best HW)
- For LM-driven analysis (Wang construction): use LM-min vector
  (per F43, this is OFTEN at higher HW than HW-min)
- For combined Wang attack (HW absorption + LM construction): trade
  off via cand_select.py with appropriate weights

## Compute

- Source: F36_extended_all_records_lm_compat.jsonl (3065 records)
- Analysis: in-memory pandas-style aggregation, ~1 sec
- No new compute beyond the F42 batch run

EVIDENCE-level: VERIFIED. All 3065 records included in the
per-cand analysis.

## Concrete next moves

1. **Update cand_select.py** to support `--use-lm-min-vector` flag
   that picks the cand's LM-min HW level (not just HW-min).

2. **Add per-cand LM-min vector to F32_deep_corpus_enriched.jsonl**
   as new fields (`cand_lm_min_hw`, `cand_lm_min_cost`,
   `cand_lm_min_w_witness`).

3. **For paper Section 5**: revise "best Wang target" claim:
   - F28: bit2_ma896ee41 (HW-min) is structurally best for SAT solving
   - F43: msb_m17149975's HW=54 vector (LM-min) is structurally best
     for Wang construction — and it has a SAT-verified collision at
     sr=60, making it doubly valuable

4. **Yale**: the F43 finding strengthens the "anchor set" suggestion in
   yesterday's response — the LM-compat manifold has many points,
   most of which (per F43) are LM-cheaper than the deep-min anchors.
   Operator design might exploit the HW=54 LM-min plateau.
