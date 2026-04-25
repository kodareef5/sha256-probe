# Structural re-ranking of the residual corpus

## Why

The 6 active registers at r=63 satisfy two cascade-DP modular relations (from `bets/mitm_residue/results/20260425_residual_structure_complete.md`):

- R63.1: `dc_63 = dg_63 (mod 2^32)`
- R63.3: `de_63 = da_63 − dT2_63 (mod 2^32)`

So the *modular* d.o.f. count is 4, not 6. Two of the registers (dg, de) are determined by the others (dc, da + actual a-values).

## The metric

`hw_free4 = HW_modular(da_63) + HW_modular(db_63) + HW_modular(dc_63) + HW_modular(df_63)`

— the Hamming weight of the 4 free moduli only. Distinct from `hw_naive` (sum across all 6 active registers, modular) and from the corpus's `hw_total` (sum across all 6, XOR).

## Top-50 by hw_free4 (104,700-record corpus, MSB family)

```
rank   hw_free4   hw_naive  hw breakdown (da,db,dc,de,df,dg)
   1         34         58  (8, 9, 9, 15, 8, 9)
   2         38         62  (11, 11, 5, 19, 11, 5)
   3         39         65  (8, 13, 8, 18, 10, 8)
  ...
  50         45         71  (10, 12, 13, 13, 10, 13)

Statistics across all 104,700 records:
  hw_naive (modular sum) min=58  median=96  max=129
  hw_free4 (4 free moduli) min=34  median=64  max=89
```

## What this changes

**For block2_wang trail design**: prefer records with low `hw_free4` over records with low XOR `hw_total`. The 4 free moduli are the genuinely-free state; pinning them is what costs the trail.

The re-ranked top-50 (`top50_lowest_hw_free4.jsonl`) gives a structurally-aware starter set for trail engineering.

**For Wang-trail feasibility**: minimum hw_free4 across 104k samples is 34. Wang-style trails for SHA-1 typically need ≤16-24 active bits at the boundary. We're 50%+ above that floor even with structural awareness.

This sharpens the BET.yaml's existing assessment: the residual HW landscape is structurally bounded above the Wang threshold under random sampling. Constructive backward-search from a target low-HW residual remains the necessary path forward (path B in BET.yaml).

## Caveat: modular vs XOR

The corpus's existing `hw_total` field is XOR-based (XOR-Hamming weight per register). My `hw_naive` is modular-based. They differ:
- Modular: HW((a1 - a2) mod 2^32)
- XOR: HW(a1 XOR a2)

A trail engine that works in XOR domain (Wang-style) needs XOR HW. A modular-arithmetic trail engine needs modular HW. The structural relations R63.1 and R63.3 are MODULAR — translating them to XOR domain introduces carry-chain noise.

For now: the structural re-rank uses modular HW because that's what the constraints natively express. Future trail-design work should pick the metric matching the trail engine's diff domain.

## Script

`rerank_structural.py` — single-file, reads corpus_msb_200k_hw96.jsonl, produces top50_lowest_hw_free4.jsonl. ~3s runtime.
