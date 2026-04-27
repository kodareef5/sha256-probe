# F43: Record-wise LM/HW Pareto surface

**2026-04-27 08:55 EDT**

F42 established that every one of the 3,065 F28 cascade-1 records is
Lipmaa-Moriai compatible. This pass asks a different selection question:
among compatible records, which witnesses are nondominated when residual
HW and LM cost are both minimized?

The scan joins:

- `residuals/F28_deep_corpus_enriched.jsonl`: witness words and residuals,
- `trails/F36_extended_all_records_lm_compat.jsonl`: per-record LM costs.

Command:

```text
python3 headline_hunt/bets/block2_wang/trails/scan_record_lm.py --top 15
```

## Summary

```text
records scanned: 3065
global Pareto points on (HW, LM): 5
exact a61=e61 records: 235
LM-incompatible records: 0
```

The global nondominated records are:

| rank | LM | HW | exact a61=e61 | candidate | W57 W58 W59 W60 |
|---:|---:|---:|:---:|---|---|
| 1 | 824 | 45 | yes | `bit2_ma896ee41_fillffffffff` | `0x91e0726f 0x6a166a99 0x4fe63e5b 0x8d8e53ed` |
| 2 | 780 | 47 | yes | `bit13_m4e560940_fillaaaaaaaa` | `0xaffb9373 0x6f262a99 0xe4deabc3 0x057cb110` |
| 3 | 773 | 48 | no | `msb_ma22dc6c7_fillffffffff` | `0xf40af50f 0xffc34b1a 0x42a8490a 0x3aacb50e` |
| 4 | 765 | 49 | no | `bit28_md1acca79_fillffffffff` | `0xe5b71d27 0xc46c3bee 0x212a96a6 0x0c338479` |
| 5 | 757 | 53 | no | `bit4_m39a03c2d_fillffffffff` | `0x34cbddf6 0xa1d273cc 0x1adb0739 0x3dbf5ec7` |

The record-wise LM champion is not the F36 min-HW-record LM champion:

```text
bit4_m39a03c2d_fillffffffff
HW = 53
LM = 757
exact a61=e61 = no
```

This improves the previous min-HW-record LM champion (`msb_ma22dc6c7`,
LM 773) by 16 LM bits, at the cost of 5 more residual HW bits and losing
the exact `a61=e61` symmetry.

## Exact-symmetry records

The lowest-LM exact `a61=e61` records are:

| rank | LM | HW | candidate | W57 W58 W59 W60 |
|---:|---:|---:|---|---|
| 1 | 772 | 52 | `bit4_m39a03c2d_fillffffffff` | `0xd6b9e8b6 0x9e44f141 0x0df6ff97 0x928aa435` |
| 2 | 774 | 53 | `bit28_md1acca79_fillffffffff` | `0x644966ad 0x5b00be83 0xd6cfe58b 0x65ac8634` |
| 3 | 776 | 54 | `bit4_m39a03c2d_fillffffffff` | `0x77caf5ac 0x06934373 0xb15f95ad 0x3ea89f58` |
| 4 | 780 | 47 | `bit13_m4e560940_fillaaaaaaaa` | `0xaffb9373 0x6f262a99 0xe4deabc3 0x057cb110` |
| 5 | 783 | 58 | `bit4_m39a03c2d_fillffffffff` | `0x27be3329 0xdab71b44 0x022f72cb 0x62bafaf0` |

This is important because bit4 is not just a non-symmetric LM outlier.
It also has the lowest-LM exact-symmetry record seen so far.

## HW-level LM minima

LM cost is not monotone in residual HW:

```text
HW  count  minLM
45      1    824
46      2    839
47      5    780
48     14    773
49     37    765
50     52    784
51    109    773
52    197    772
53    305    757
54    333    771
55    335    776
56    335    788
57    335    771
58    335    781
59    335    780
60    335    776
```

The best LM point occurs at HW53, not near the minimum residual HW. That
means "lowest residual HW" and "easiest modular-add trail" are different
axes.

## Interpretation

The block2 target surface is at least three-dimensional:

- residual HW,
- LM cost,
- exact `a61=e61` symmetry.

Candidate selection should not collapse to a single min-HW representative
per candidate. A sensible short list now has four different archetypes:

| archetype | candidate | reason |
|---|---|---|
| min residual | `bit2_ma896ee41` | HW45 and exact symmetry, but LM824 |
| balanced symmetric | `bit13_m4e560940` | HW47, exact symmetry, LM780 |
| low-LM min-HW record | `msb_ma22dc6c7` | HW48, LM773 |
| raw LM champion | `bit4_m39a03c2d` | LM757; exact-symmetry variants at LM772/776 |

This does not make direct random second-block absorption plausible. Even
the best observed raw LM cost is 757 bits, far beyond the 256-bit freedom
of one SHA-256 message block. The value is trail-design guidance: it
identifies which cascade residuals are likely to have cheaper local
condition systems once Wang-style message modification is built.

## Next

- Keep `bit2`, `bit13`, `msb_ma22dc6c7`, `bit28`, and `bit4` as separate
  block2 trail-design targets.
- Extend corpus search around the Pareto champions with a score that
  includes LM, not just residual HW.
- Build the next residual sampler so it tracks a Pareto frontier online
  instead of saving only min-HW records.
