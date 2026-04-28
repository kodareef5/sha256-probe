# F111/F112: active-word subset scan finds compact absorbers below dense score 94
**2026-04-28**

## Summary

F110 showed that direct block-2 message search can reduce the final
chain-output target distance from the zero/zero baseline 119 to 94, but
the best point was dense. This follow-up turns the sparse-biased result
into an active-word scan.

The main result is stronger than F110:

```
Best target distance: 90
Active message words: 0, 1, 8, 14
Message diff HW:      75
Nonzero W diffs:      52
```

A cleaner low-HW lane is close behind:

```
Best target distance: 91
Active message words: 0, 1, 11
Message diff HW:      26
Nonzero W diffs:      51
```

Both beat or match the old dense score-94 region while using only 3-4
message words.

## New scan tool

New script:

```
headline_hunt/bets/block2_wang/encoders/active_subset_scan.py
```

It enumerates active message-word masks, calls the existing block-2
absorption search under each mask, and writes a ranked JSON summary.

The analyzer also now accepts both normal search JSONs and subset-scan
JSONs:

```
headline_hunt/bets/block2_wang/encoders/analyze_absorption_search.py
```

It also supports `--dedupe` to collapse duplicate M1/M2 candidates across
scan and continuation artifacts, and `--pareto` to show non-dominated
score/sparsity tradeoffs.

The main search loader now accepts subset-scan JSONs as `--init-json` and
chooses the best candidate compatible with the requested active-word mask.

## Scan command

```
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/active_subset_scan.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit3_HW55_naive_blocktwo.json \
  --pool 0,1,2,5,6,7,8,9,10,11,12,13,14 \
  --include 0,1 \
  --sizes 3-4 \
  --restarts 3 --iterations 4000 --seed 404 \
  --init-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F110_bit3_absorb_search_sparse_12x10k.json \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F111_active_subset_scan_include01_3to4_3x4k.json \
  --top 16
```

Archived artifact:

```
results/search_artifacts/20260428_F111_active_subset_scan_include01_3to4_3x4k.json
```

Top scan results:

```
rank  score  msgHW  words  sched  active
   1     90     75      4     52  0,1,8,14
   2     91     26      3     51  0,1,2,11
   3     93     58      4     52  0,1,5,6
   4     94     29      2     46  0,1,7,12
   5     94     48      3     51  0,1,9
   6     95     57      4     52  0,1,2,12
```

The rank-2 entry allowed word 2, but the best candidate did not use it;
its actual active set is 0, 1, 11.

## Continuations

The score-90 mask was continued for 8 x 50k iterations:

```
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/search_block2_absorption.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit3_HW55_naive_blocktwo.json \
  --restarts 8 --iterations 50000 --seed 515 \
  --active-words 0,1,8,14 \
  --init-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F111_active_subset_scan_include01_3to4_3x4k.json \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F112_bit3_active_01814_continue_8x50k.json
```

It did not improve beyond score 90.

The cleaner score-91 mask was continued for 8 x 50k iterations:

```
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/search_block2_absorption.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit3_HW55_naive_blocktwo.json \
  --restarts 8 --iterations 50000 --seed 616 \
  --active-words 0,1,11 \
  --init-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F111_active_subset_scan_include01_3to4_3x4k.json \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F112_bit3_active_011_continue_8x50k.json
```

It did not improve beyond score 91.

## Size-5 probe around 0,1,8

After the continuations, a targeted size-5 scan tested all masks containing
0, 1, and 8:

```
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/active_subset_scan.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit3_HW55_naive_blocktwo.json \
  --pool 0,1,2,5,6,7,8,9,10,11,12,13,14 \
  --include 0,1,8 \
  --sizes 5 \
  --restarts 3 --iterations 5000 --seed 707 \
  --init-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F111_active_subset_scan_include01_3to4_3x4k.json \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F113_active_subset_scan_include018_size5_3x5k.json \
  --top 16
```

Archived artifact:

```
results/search_artifacts/20260428_F113_active_subset_scan_include018_size5_3x5k.json
```

This did not beat score 90. Most top rows simply inherited the same
0,1,8,14 candidate inside larger allowed masks. The best actual 5-word
candidate in this run was:

```
Target distance: 92
Allowed words:   0, 1, 2, 8, 10
Message diff HW: 77
Nonzero W diffs: 53
```

That is useful as a negative control: adding one allowed word around the
current best mask is not automatically helpful.

## Strict size-5 probe and new best

The first size-5 probe exposed a ranking artifact: seeded lower-dimensional
candidates can dominate larger allowed masks. `active_subset_scan.py` now
supports `--require-all-used`, which ranks candidates that actually use
every allowed word when such candidates exist.

Strict rerun:

```
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/active_subset_scan.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit3_HW55_naive_blocktwo.json \
  --pool 0,1,2,5,6,7,8,9,10,11,12,13,14 \
  --include 0,1,8 \
  --sizes 5 \
  --restarts 3 --iterations 5000 --seed 808 \
  --init-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F111_active_subset_scan_include01_3to4_3x4k.json \
  --require-all-used \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F114_active_subset_scan_include018_size5_strict_3x5k.json \
  --top 16
```

Archived artifact:

```
results/search_artifacts/20260428_F114_active_subset_scan_include018_size5_strict_3x5k.json
```

New best:

```
Target distance: 86
Active words:    0, 1, 2, 8, 9
Message diff HW: 80
Nonzero W diffs: 53
```

The same run also found a score-89 strict candidate on 0,1,8,9,12.

The score-86 mask was continued for 8 x 50k iterations:

```
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/search_block2_absorption.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit3_HW55_naive_blocktwo.json \
  --restarts 8 --iterations 50000 --seed 909 \
  --active-words 0,1,2,8,9 \
  --init-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F114_active_subset_scan_include018_size5_strict_3x5k.json \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F115_bit3_active_01289_continue_8x50k.json
```

Archived artifact:

```
results/search_artifacts/20260428_F115_bit3_active_01289_continue_8x50k.json
```

The continuation did not improve beyond score 86.

## Strict size-6 expansion

To test whether the score-86 basin simply wanted more message freedom, a
small strict size-6 expansion added one extra word to 0,1,2,8,9:

```
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/active_subset_scan.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit3_HW55_naive_blocktwo.json \
  --pool 0,1,2,5,6,7,8,9,10,11,12,13,14 \
  --include 0,1,2,8,9 \
  --sizes 6 \
  --restarts 5 --iterations 10000 --seed 1001 \
  --init-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F115_bit3_active_01289_continue_8x50k.json \
  --require-all-used \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F116_active_subset_scan_include01289_size6_strict_5x10k.json \
  --top 16
```

Archived artifact:

```
results/search_artifacts/20260428_F116_active_subset_scan_include01289_size6_strict_5x10k.json
```

Best size-6 strict result:

```
Target distance: 94
Active words:    0, 1, 2, 8, 9, 10
Message diff HW: 57
Nonzero W diffs: 54
```

This is a useful negative: under this budget, expanding the score-86
mask by one forced-active word made results worse, not better.

## HW-penalized continuation

A light sparsity penalty on the score-86 mask tested whether a cleaner
nearby point could beat the seed under a mixed objective:

```
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/search_block2_absorption.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit3_HW55_naive_blocktwo.json \
  --restarts 8 --iterations 30000 --seed 1112 \
  --active-words 0,1,2,8,9 \
  --init-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F115_bit3_active_01289_continue_8x50k.json \
  --hw-penalty 0.05 \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F117_bit3_active_01289_hwpenalty_8x30k.json
```

Archived artifact:

```
results/search_artifacts/20260428_F117_bit3_active_01289_hwpenalty_8x30k.json
```

No cleaner point beat the score-86 seed's penalized objective:

```
Best target distance: 86
Message diff HW:      80
Objective:            90.0
```

The best fresh penalized restart reached distance 94 with objective 98.15.

## Broad strict size-5 scan

The targeted size-5 scans raised a question: is word 8 really special, or
did the scan only find it because the search was biased there? A broader
strict size-5 scan tested every 5-word mask containing words 0 and 1:

```
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/active_subset_scan.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit3_HW55_naive_blocktwo.json \
  --pool 0,1,2,5,6,7,8,9,10,11,12,13,14 \
  --include 0,1 \
  --sizes 5 \
  --restarts 3 --iterations 5000 --seed 1212 \
  --init-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F115_bit3_active_01289_continue_8x50k.json \
  --require-all-used \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F118_active_subset_scan_include01_size5_strict_3x5k.json \
  --top 20
```

Archived artifact:

```
results/search_artifacts/20260428_F118_active_subset_scan_include01_size5_strict_3x5k.json
```

Top results:

```
rank  score  msgHW  active
   1     86     80  0,1,2,8,9
   2     90     67  0,1,6,10,13
   3     91     76  0,1,5,6,14
   4     92     49  0,1,2,10,13
   5     92     81  0,1,7,9,12
   6     92     81  0,1,7,10,13
```

This scan did not beat 86. It did show a cleaner alternate family:
0,1,2,10,13 reached distance 92 with message diff HW 49 in the scan.

A deduped Pareto view across the 3/4-word scan, the strict 0,1,8 size-5
scan, and the broad strict size-5 scan is:

```
score  msgHW  words  sched  active
   86     80      5     53  0,1,2,8,9
   90     67      5     53  0,1,6,10,13
   90     75      4     52  0,1,8,14
   91     26      3     51  0,1,11
   94     29      2     46  7,12
   99     25      3     51  0,1,13
```

The practical readout is that word 8 remains part of the raw-best basin,
but not all good tradeoffs require it.

The best alternate Pareto family, 0,1,6,10,13, was continued for 8 x 50k
iterations:

```
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/search_block2_absorption.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit3_HW55_naive_blocktwo.json \
  --restarts 8 --iterations 50000 --seed 1313 \
  --active-words 0,1,6,10,13 \
  --init-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F118_active_subset_scan_include01_size5_strict_3x5k.json \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F119_bit3_active_0161013_continue_8x50k.json
```

Archived artifact:

```
results/search_artifacts/20260428_F119_bit3_active_0161013_continue_8x50k.json
```

It did not improve beyond score 90.

The clean 0,1,2,10,13 family was also continued:

```
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/search_block2_absorption.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit3_HW55_naive_blocktwo.json \
  --restarts 8 --iterations 50000 --seed 1414 \
  --active-words 0,1,2,10,13 \
  --init-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F118_active_subset_scan_include01_size5_strict_3x5k.json \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F120_bit3_active_0121013_continue_8x50k.json
```

Archived artifact:

```
results/search_artifacts/20260428_F120_bit3_active_0121013_continue_8x50k.json
```

It improved from score 92 to score 90, with message diff HW 70.

## Seeded continuation controls

`search_block2_absorption.py` now supports two continuation controls:

```
--init-use first|all
--init-kicks N
```

`--init-use all` starts every restart from the loaded seed. `--init-kicks`
applies random mutations to each seeded restart before the search starts.

Exact reseeding of the score-86 candidate:

```
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/search_block2_absorption.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit3_HW55_naive_blocktwo.json \
  --restarts 8 --iterations 50000 --seed 1515 \
  --active-words 0,1,2,8,9 \
  --init-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F115_bit3_active_01289_continue_8x50k.json \
  --init-use all \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F121_bit3_active_01289_initall_8x50k.json
```

Archived artifact:

```
results/search_artifacts/20260428_F121_bit3_active_01289_initall_8x50k.json
```

Every restart returned the same score-86 seed.

One-kick reseeding:

```
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/search_block2_absorption.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit3_HW55_naive_blocktwo.json \
  --restarts 8 --iterations 50000 --seed 1616 \
  --active-words 0,1,2,8,9 \
  --init-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F115_bit3_active_01289_continue_8x50k.json \
  --init-use all --init-kicks 1 \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F122_bit3_active_01289_initall_kick1_8x50k.json
```

Archived artifact:

```
results/search_artifacts/20260428_F122_bit3_active_01289_initall_kick1_8x50k.json
```

The best one-kick restart reached only score 96. A single random mutation
usually exits the score-86 basin, and this annealer does not reliably climb
back under the current budget.

## Replayable candidates

Score 90, active words 0, 1, 8, 14:

```
M1:
0xb55744aa 0x6a43afbe 0xa5bcc862 0x45e5a8ea
0x1773770c 0xa9c08852 0x2459b9f4 0x305739ae
0xf68c9090 0xc6951b9d 0x208ddc45 0x4d4344f4
0x6852a5b0 0xb5eb8b91 0xa0615cc9 0xa2af6147

M2:
0x02a6db70 0x8e19cb43 0xa5bcc862 0x45e5a8ea
0x1773770c 0xa9c08852 0x2459b9f4 0x305739ae
0x20bbe42f 0xc6951b9d 0x208ddc45 0x4d4344f4
0x6852a5b0 0xb5eb8b91 0x45445129 0xa2af6147

Final chain diff:
0x22189d01 0xb828a340 0x454dc240 0xc8c80ace
0x304044f1 0x11c10496 0x630e1126 0x386c9360
```

Score 91, active words 0, 1, 11:

```
M1:
0xded77f2b 0xc1e97f66 0xce5ae5b9 0x6c3a50e8
0xe9653766 0x85e18688 0x006e33f5 0x70fcf2ad
0x0643f5a4 0xa9f8218c 0x5221b3a5 0xbbbfe459
0xcb4ce6b1 0xa68d6e47 0xafc742f9 0xfd2e7550

M2:
0x3290173e 0x49e81f2d 0xce5ae5b9 0x6c3a50e8
0xe9653766 0x85e18688 0x006e33f5 0x70fcf2ad
0x0643f5a4 0xa9f8218c 0x5221b3a5 0xb3afe459
0xcb4ce6b1 0xa68d6e47 0xafc742f9 0xfd2e7550

Final chain diff:
0x4b5d015c 0x60424200 0x0e11a088 0x448e9aac
0x23a64060 0x055d9471 0x85731c0a 0x1a02f061
```

Score 86, active words 0, 1, 2, 8, 9:

```
M1:
0xf0268c20 0x34b9f725 0xab2127c5 0x8bbfa559
0xfc1dae5f 0x5b142d31 0x0713f3ca 0xc61c61a8
0x71fe880c 0xb6be8846 0x54cd3828 0x6c2887a1
0xa6c4d1d6 0x75085133 0xadd05863 0x017220f8

M2:
0x29bb3226 0x049e7889 0x7d80c4e8 0x8bbfa559
0xfc1dae5f 0x5b142d31 0x0713f3ca 0xc61c61a8
0xd9fb2baa 0xf9138d30 0x54cd3828 0x6c2887a1
0xa6c4d1d6 0x75085133 0xadd05863 0x017220f8

Final chain diff:
0xa1544e2c 0x201449b4 0x0201e619 0x80403025
0x22e46a42 0x32610a69 0x4c960803 0x10e88ac6
```

Score 90, active words 0, 1, 6, 10, 13:

```
M1:
0xfaab3c60 0x9a96363b 0x37f1665c 0xc8322da0
0x8a5def6b 0x75cda8d9 0xbdb1bf43 0xd6014339
0xd9210b0e 0xa0c270c4 0x042a36b9 0x50f342e0
0xd839c567 0x7eeeec99 0x6bccb375 0x6c6da1d4

M2:
0x7154fcaf 0xca4c2fb0 0x37f1665c 0xc8322da0
0x8a5def6b 0x75cda8d9 0xb2b655a3 0xd6014339
0xd9210b0e 0xa0c270c4 0x85ea36f7 0x50f342e0
0xd839c567 0xcfa86cf9 0x6bccb375 0x6c6da1d4

Final chain diff:
0x551d5b82 0x9e00d109 0x3c2462c4 0x8f903080
0x224086ce 0xa1020448 0xf218e051 0x38244568
```

Score 90, active words 0, 1, 2, 10, 13:

```
M1:
0xed1ce354 0xba524491 0x6b1a4451 0xde6f2a0a
0xc0305c61 0x5d3bde74 0xd8fe5fbd 0x04ac90fb
0xefd46587 0xf44b44e9 0x852955f6 0x16e6a407
0x25c275d6 0xbe7f3c57 0x493ff076 0x2dd3f5db

M2:
0xa53cc6b9 0xde3bb767 0xbdbb0db1 0xde6f2a0a
0xc0305c61 0x5d3bde74 0xd8fe5fbd 0x04ac90fb
0xefd46587 0xf44b44e9 0xc4072536 0x16e6a407
0x25c275d6 0x8c6c10cc 0x493ff076 0x2dd3f5db

Final chain diff:
0xde080b5e 0x0c4df803 0x05015554 0x208d4680
0x61208368 0x5520621a 0x0024a752 0xe8e22025
```

## Interpretation

This changes the shape of the block-2 absorber work. The useful object is
not the dense score-94 candidate anymore. The better question is why small
masks containing words 0, 1, and 8 can steer the final chain-output
distance into the 86-94 range, and whether the late schedule can be solved
around those compact masks.

Most promising next steps:

- Continue strict subset scans around the Pareto families, especially
  0,1,2,8,9 and 0,1,2,10,13.
- Run sparse/objective-biased continuations from the score-86 mask to
  trade raw score for lower message-diff HW.
- Use strict subset-scan mode for all seeded superset probes, so
  lower-dimensional candidates do not dominate larger masks.
- Replace blind random kicks with structured local moves that preserve
  selected W16-W30 schedule-diff features of the score-86 seed.
- Build a late-schedule targeter around W19-W32, where all top compact
  candidates are active and the target-distance gains appear to accumulate.
