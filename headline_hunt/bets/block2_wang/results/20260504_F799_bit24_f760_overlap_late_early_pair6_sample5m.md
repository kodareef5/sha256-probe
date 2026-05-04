---
date: 2026-05-04
bet: block2_wang
status: BIT24_F760_OVERLAP_LATE_EARLY_PAIR6_DETOUR
parent: F798 overlap branch comparison
evidence_level: VERIFIED_JSON_ARTIFACT
author: yale-codex
---

# F799: bit24 F760 overlap plus late/early motif gate

## Setup

F799 tests the second-generation selector suggested by F798. It returns to the
original F760 bit24 HW82 parent, keeps the F788 overlap filter, and adds a
word-pair motif gate that the F788 repairable branch satisfied while the F795
and F796 best-HW branches did not.

```text
candidate: bit24_mdc27e18c
seed JSONL: F547_pathC_absorber_seeds.jsonl
seed rank: 1
init HW: 82
init lane: [9, 10, 11, 10, 10, 13, 13, 6]
pair atlas: F767 top-80
selected pairs: 236
pair_count = 6
radius = 10..12
sampled combos = 5,000,000
rng seed = 799

overlap filter:
  pair removed-bit union >= 80
  pair added-bit union <= 170
  pair added-bit repeat excess >= 250

motif gate:
  late-touch pairs >= 2
  early-late pairs >= 1
```

## Result

```text
candidate combos: 5,000,000
skipped radius/duplicate: 498
skipped by late-pair count: 456,667
skipped by pair-graph motif: 246,556
skipped by overlap signature: 723,776
evaluated: 3,572,503
HW < 82: 0
HW <= 82: 0
c/g-improving: 8
target-L1-improving: 1,916
wall seconds: 707.2
```

Best raw-HW sample:

```text
HW 87
target L1 19
c/g objective 119, delta -11
lane [12, 12, 7, 8, 13, 10, 9, 16]
standalone net-delta sum 160
nonlinear HW gain 155
motif: late-touch 4, late-late 2, early-late 1
sources: target + hw + repair + repair + repair + repair_h
```

Best target-L1 sample:

```text
HW 89
target L1 13
c/g objective 131, delta +1
lane [12, 12, 9, 15, 10, 8, 12, 11]
standalone net-delta sum 130
nonlinear HW gain 123
motif: late-touch 2, late-late 0, early-late 2
sources: target/hw/cg + target/hw + target + cg + repair + repair_a
```

Best-HW M2:

```text
0x00001000,0x00100000,0x00006014,0x40105002,
0x40000000,0x10001000,0x00000000,0x00200000,
0x08002001,0x20020040,0x09808108,0x00400000,
0x000c0080,0x00040000,0x1201c402,0x00000040
```

## Interpretation

The motif gate did what it was meant to do for target density:

```text
F788 raw overlap: 8,860 target improvements / 16.65M evals = 532 per M
F799 motif gate: 1,916 target improvements / 3.57M evals = 536 per M
```

However, it did not improve the direct HW tail. F788 found HW86 in 16.65M
evaluations; F799 found HW87 in 3.57M and no HW<=82. The best-HW detour is
still worth one repair beam because it has a strong c/g improvement and a
late-heavy motif, unlike the closed F796 HW87 detour.

## Artifacts

```text
headline_hunt/bets/block2_wang/results/search_artifacts/20260504_F799_bit24_f760_hw82_overlap_late_early_pair6_sample5m_combo6.json
headline_hunt/bets/block2_wang/results/search_artifacts/20260504_F799_bit24_f760_hw82_overlap_late_early_pair6_sample5m_source_analysis.json
headline_hunt/bets/block2_wang/results/search_artifacts/20260504_F799_m2_combo_cancellation.json
headline_hunt/bets/block2_wang/results/search_artifacts/20260504_F799_m2_combo_bit_overlap.json
headline_hunt/bets/block2_wang/results/search_artifacts/20260504_F799_m2_combo_graph_motifs.json
```

## Next

Run F800: standard pure-HW pair-beam repair from the F799 HW87 best-HW detour.
