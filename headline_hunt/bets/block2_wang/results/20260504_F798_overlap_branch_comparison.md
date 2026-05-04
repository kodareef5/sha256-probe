---
date: 2026-05-04
bet: block2_wang
status: OVERLAP_BRANCH_COMPARISON
parent: F788/F793/F795/F796
evidence_level: VERIFIED_JSON_ARTIFACT
author: yale-codex
---

# F798: overlap branch comparison

## Setup

F798 adds `summarize_m2_combo_branches.py`, a reusable comparison script for
M2 combo-search artifacts. It reconstructs selected pair sources from each
pair atlas and reports branch rates, best records, word-pair motifs, and source
mixes.

Compared branches:

```text
F788: bit24/F760 HW82 overlap selector, successful side basin
F793: bit24/F789 HW78 unfiltered side-basin sample
F795: bit13 HW82 overlap selector, negative transfer
F796: bit24/F763 HW82 overlap selector, weak detour then closed by F797
```

## Main Table

```text
label                                                evals       HW<=init target<init target/M bestHW bestHW_target bestTarget bestTarget_HW
F788_bit24_f760_hw82_overlap_pair6_sample20m        16,647,332  0        8,860       532.22   86     16            9          89
F793_bit24_f789_hw78_unfiltered_pair6_sample5m       4,999,571  0        3             0.60   84     22           12          94
F795_bit13_hw82_overlap_pair6_sample5m               4,094,143  0        0             0.00   90     14           12          92
F796_bit24_f763_hw82_overlap_pair6_sample5m          4,242,428  0        49           11.55   87     15           10          92
```

## Interpretation

The discriminating feature is not merely "large nonlinear cancellation." All
branches can produce cancellation. The strong signal is target-lane density:
F788 produced hundreds of target improvements per million evaluations, while
F796 produced only tens, F793 about one per million, and F795 none.

The motif split also matters. The F788 best-HW detour had:

```text
late-touch pairs: 2
late-late pairs: 1
early-late pairs: 1
source mix: target + repair-heavy + cg
```

F795 and F796 best-HW detours had only one late-touch pair and no early-late
bridge. F796's best target record was repair-only and did not repair under
F797.

## New Selector

F798 suggests a second-generation selector for the original F760 parent:

```text
keep F788 overlap filter:
  pair removed-bit union >= 80
  pair added-bit union <= 170
  pair added-bit repeat excess >= 250

add motif gate:
  min late-touch pairs >= 2
  min early-late pairs >= 1
```

This keeps the F788 best-HW motif, excludes the F795/F796 best-HW motif, and
still allows the F788 best-target late/early bridge geometry.

## Artifacts

```text
headline_hunt/bets/block2_wang/encoders/summarize_m2_combo_branches.py
headline_hunt/bets/block2_wang/results/search_artifacts/20260504_F798_overlap_branch_comparison.json
headline_hunt/bets/block2_wang/results/search_artifacts/20260504_F798_overlap_branch_comparison.md
```

## Next

Run F799: a bounded F760 overlap sample using the new motif gate. Promote it to
a repair beam only if it finds an HW86-HW90 detour with target-lane structure
comparable to F788.
