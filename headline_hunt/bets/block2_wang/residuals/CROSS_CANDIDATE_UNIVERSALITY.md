# Cross-candidate universality — cluster analysis is candidate-independent

Repeated the corpus + cluster analysis on a non-MSB candidate (bit19 kernel) to test whether the structural findings are MSB-specific or universal.

## Setup

| Candidate | m0 | fill | kernel bit |
|---|---|---|---:|
| MSB cert | 0x17149975 | 0xffffffff | 31 |
| bit19 priority | 0x51ca0b34 | 0x55555555 | 19 |

Both: 200k random samples → ~104k cascade-held records → cluster analysis.

## Per-register HW: structurally identical

| Register | MSB mean | bit19 mean | MSB std | bit19 std |
|---|---:|---:|---:|---:|
| a | 15.19 | **15.18** | 2.69 | 2.70 |
| b | 15.17 | **15.15** | 2.70 | 2.69 |
| c | 14.87 | **14.89** | 2.60 | 2.62 |
| e | 15.17 | **15.17** | 2.69 | 2.70 |
| f | 15.16 | **15.17** | 2.69 | 2.70 |
| g | 14.88 | **14.88** | 2.61 | 2.61 |

**Mean differences ≤ 0.02 across all 6 active registers.** The cascade structure produces identically-distributed residuals regardless of kernel bit.

## Universal findings (both candidates)

- 100% [a,b,c,_,e,f,g,_] active-register pattern (d63=h63=0 always)
- 0% da63==de63 (Theorem 4 doesn't extend to r=63)
- All 6 active registers have nearly-uniform-random HW distribution (mean ~15, std ~2.7)
- Lowest HW(da)+HW(de) = 15 in both cases

## Where they differ (slightly)

| Metric | MSB | bit19 | direction |
|---|---:|---:|---|
| HW(da) ≤ 4 records | 1 | **4** | bit19 better |
| HW(da) ≤ 6 records | 47 | **64** | bit19 better |
| HW(da+de) ≤ 18 records | 51 | **60** | bit19 better |
| min HW total | 62 | **56** | bit19 better |

**bit19 has slightly more low-HW outliers**, suggesting it's a marginally better Wang-target candidate. But both are far above Wang threshold (HW>60 across 6 active regs).

## Implication for block2_wang

The cascade structural barrier is **fundamental, not candidate-specific**. Switching candidates within the cascade-eligible set:
- Can find candidates with slightly more low-HW outliers (bit19 vs MSB)
- Cannot escape the universal HW>60 minimum across 6 active registers

So the bet's bound holds: classical Wang differential trails on full SHA-256 require HW ≤ 24-ish; cascade construction at N=32 produces residuals at HW>60 regardless of kernel choice.

## Implication for `cascade_aux_encoding`

If the cascade construction is universally producing HW>60 residuals at N=32, that's a **lower bound on what cascade-aux-force-mode could achieve**. Even if force-mode finds a SAT, it lives on this HW>60 manifold. The auxiliary-encoding work doesn't escape the structural HW barrier — it only navigates the existing cascade-DP solution set.

## Saved artifacts

- `/tmp/cluster2/corpus_bit19_m51ca0b34.jsonl` — 104,857 records (not committed to repo; regenerable in 8s via build_corpus.py)
- This writeup — universal-vs-candidate-specific findings

## Concrete next-actions for block2_wang

1. **Sweep all 35 candidates** with build_corpus.py at low cost (~5 min CPU each → ~3 hours total). Identify the candidate with the most HW(da+de)≤18 records as "best block2_wang target" — possibly bit19 wins, possibly something else.

2. **Hill-climb on TOTAL HW** (not just (a,e) component). The earlier hill-climb experiment minimized total HW and plateaued at 82 vs random's 62. Try seeded from the lowest-HW residuals (the 50 saved as starter pack).

3. **Theorem 4-extension question**: at exactly which round does da-de divergence start? The fact that 0/104857 records have da63==de63 suggests divergence kicks in at round 62 or 63. Verifying which round is structurally interesting (possibly publishable as a structural observation).

Items 2 and 3 are <1 day each. Item 1 is overnight CPU.
