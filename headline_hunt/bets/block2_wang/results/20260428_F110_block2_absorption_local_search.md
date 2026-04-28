# F110: block-2 absorption local search - dense message freedom reaches target distance 94
**2026-04-28**

## Summary

F109's exact-diff sweep showed that one-round W2 pins do not produce a
stable absorption effect. F110 widens the probe: fix one block-2 message,
then stochastically mutate the other block-2 message's 16 words to
minimize final chain-output distance to the all-zero collision target.

This is not a verifier and not a trail. It is a design-space probe for
whether raw block-2 message freedom can steer the chain diff downward.

## Tool

New script:

```
headline_hunt/bets/block2_wang/encoders/search_block2_absorption.py
```

It reconstructs the block-1 chain outputs from a trail bundle, fixes a
random side-1 block-2 message, and searches side-2 message words by
simulated annealing plus residual/chain-diff hint mutations.

The tool also supports `--init-json` to continue from the best result in
a previous search output.

Companion analysis script:

```
headline_hunt/bets/block2_wang/encoders/analyze_absorption_search.py
```

It summarizes saved JSON outputs by best score, message-word activity,
and recurring schedule-word activity.

## Main result on F106 bit3 HW55 fixture

Command:

```
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/search_block2_absorption.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit3_HW55_naive_blocktwo.json \
  --restarts 16 --iterations 20000 --seed 101 \
  --out-json /tmp/bit3_absorb_search_16x20k.json
```

Archived artifact:

```
results/search_artifacts/20260428_F110_bit3_absorb_search_16x20k.json
```

Result:

```
Block1 working residual HW: 55
Block2 chain-input diff HW: 68
Zero/zero baseline target distance: 119
Best target distance: 94
Best message diff HW: 154
Nonzero message words: 12
Nonzero W diffs: 60
```

The improvement from 119 to 94 is real but dense. It says unconstrained
message freedom can find lower residual regions, but the resulting shape
is not a clean Wang-style trail.

## Replayable best candidate

M1:

```
0x94c662cd 0xd8dcb35f 0x31db6e32 0xe88b7591
0xf71ab247 0x8a0ac984 0xec89b7a6 0x5bd21b6a
0x7796668d 0x0c6bdf0d 0xa9d93650 0x80e6b5d0
0x36eafa28 0x9a1f7aa5 0x38c115d6 0xeae3732d
```

M2:

```
0x4b5bdb73 0xd8dcb35f 0x647977c3 0xe88b7591
0x9b7d8978 0x3a4c4de6 0x273a53b5 0x56cc3b4a
0x7796668d 0x569b7dd2 0xa9d93450 0x00a6b5d2
0x366afa28 0xab61b50e 0x0d5bd63e 0xeae3732d
```

Final chain diff:

```
0x0206d091 0xc8035247 0xc3b84447 0xba083426
0x535b1380 0x485c03e5 0x20840163 0x714c3851
```

Target distance to all-zero: 94.

First 32 nonzero schedule diffs:

```
W00=0xdf9db9be W02=0x55a219f1 W04=0x6c673b3f W05=0xb0468462
W06=0xcbb3e413 W07=0x0d1e2020 W09=0x5af0a2df W10=0x00000200
W11=0x80400002 W12=0x00800000 W13=0x317ecfab W14=0x359ac3e8
W16=0x6e40c223 W17=0x2662efa5 W18=0x5960306b W19=0xa83ea3ca
W20=0x22934143 W21=0x4bed2760 W22=0xf9c37fb3 W23=0x1bf27243
W24=0x7de64449 W25=0x2245a489 W26=0xa7806a04 W27=0x83852d26
W28=0xa62b5215 W29=0xfefe318d W30=0x34b3eb3b W31=0xf419d1ef
W32=0xb15b66e0 W33=0x2d739c51 W34=0x5e807691 W35=0x032c6dfb
```

## Negative controls

Other search modes did not beat 94:

```
8 x 5k random/same:   best distance 95
4 x 2k + polish:      best distance 98
8 x 5k random/random: best distance 97
8 x 5k zero/same:     best distance 98
100k continuation from score-94 candidate: no improvement
```

## Sparse-biased result

The raw score-94 candidate is dense. A sparse-biased run used an
objective penalty of 0.05 per active message-diff bit and 1.0 per active
message word:

```
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/search_block2_absorption.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit3_HW55_naive_blocktwo.json \
  --restarts 12 --iterations 10000 --seed 141 \
  --hw-penalty 0.05 --word-penalty 1.0 \
  --out-json /tmp/bit3_absorb_search_sparse_12x10k.json
```

Archived artifact:

```
results/search_artifacts/20260428_F110_bit3_absorb_search_sparse_12x10k.json
```

Best sparse-biased candidate:

```
Target distance: 100
Objective: 104.75
Message diff HW: 15
Nonzero message words: 4
Nonzero W diffs: 52
```

M1:

```
0xded77f2b 0xc1e97f66 0xce5ae5b9 0x6c3a50e8
0xe9653766 0x85e18688 0x006e33f5 0x70fcf2ad
0x0643f5a4 0xa9f8218c 0x5221b3a5 0xbbbfe459
0xcb4ce6b1 0xa68d6e47 0xafc742f9 0xfd2e7550
```

M2:

```
0x93f7ea20 0xc1e95f66 0xce5ae5b9 0x6c3a50e8
0xe9653766 0x85e18688 0x006e33f5 0x70fcf2ad
0x0641f5a4 0xa9f8618c 0x5221b3a5 0xbbbfe459
0xcb4ce6b1 0xa68d6e47 0xafc742f9 0xfd2e7550
```

This candidate changes only message words 0, 1, 8, and 9. The resulting
first schedule diffs:

```
W00=0x4d20950b W01=0x00002000 W08=0x00020000 W09=0x00004000
W16=0x5560a975 W17=0x00002000 W18=0xc081782e W19=0x34000078
W20=0xf323880e W21=0x00621b80 W22=0x7d19b10f W23=0x9bb05f3c
```

## Interpretation

This is the first positive sign after the exact-diff negatives: direct
message search can push the final block-2 chain diff down substantially.
But the best candidate is highly dense:

- 12 of 16 message words differ
- 60 of 64 schedule words differ
- final distance is still 94, nowhere near collision

The sparse-biased result gives a more trail-like point: distance 100 with
only 4 active message words and low message-diff HW. That is probably a
better input for a late-schedule local solver than the absolute score-94
dense candidate.

## Active-word continuation

The sparse-biased run identified message words 0, 1, 8, and 9 as a compact
absorber subset. Continuing search while forcing all other message words
equal produced a better compact candidate:

```
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/search_block2_absorption.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit3_HW55_naive_blocktwo.json \
  --restarts 8 --iterations 30000 --seed 321 \
  --active-words 0,1,8,9 \
  --init-json /tmp/bit3_absorb_search_sparse_12x10k.json \
  --out-json /tmp/bit3_active_0189_continue_8x30k.json
```

Archived artifact:

```
results/search_artifacts/20260428_F110_bit3_active_0189_continue_8x30k.json
```

Result:

```
Target distance: 95
Message diff HW: 65
Nonzero message words: 4
Nonzero W diffs: 52
Active message words: 0, 1, 8, 9
```

M1:

```
0xbba8906f 0xe5068d13 0xb9bec94f 0x1c92a7b9
0x22efe02c 0x9f4d1a9e 0x4ed121b3 0x0d80b541
0x8b0d7e96 0xf64e3381 0xaa7499e9 0xd47d7d02
0xe5bfeb08 0x71b94ec2 0xf6ef2a18 0x50a60ef6
```

M2:

```
0xf57174a4 0xd671b2e9 0xb9bec94f 0x1c92a7b9
0x22efe02c 0x9f4d1a9e 0x4ed121b3 0x0d80b541
0x0acf7a90 0x9e159f67 0xaa7499e9 0xd47d7d02
0xe5bfeb08 0x71b94ec2 0xf6ef2a18 0x50a60ef6
```

First schedule diffs:

```
W00=0x4ed9e4cb W01=0x33773ffa W08=0x81c20406 W09=0x685bace6
W16=0x13455b46 W17=0x11eb5efe W18=0x01c91ebc W19=0x3b9cb01d
W20=0xac89719a W21=0x4a034c93 W22=0x8bf3e27f W23=0xe8885f8c
```

This is now the best trail-like absorber hint: it matches the earlier
distance-95 dense run while forcing the disturbance into four message
words.

So the next productive step is not "add more one-word exact_diff probes."
It is extracting structure from low-distance candidates and using it to
build a late-schedule local solver biased toward sparse/LM-cheap regions.
