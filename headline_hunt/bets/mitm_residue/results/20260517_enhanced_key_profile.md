# 2026-05-17: Enhanced Free-Word MITM Key Profile

Runner: mac-codex

## Question

After `D60=0`, which extra interface keys are useful for meet-in-the-middle
construction?

The enhanced prototype tracks, for every `D60=0` match:

- `(g60,h60)` XOR-difference key,
- exact r61 active-bit mask,
- tail carry chamber signature over rounds 60..63,
- r61 HW and final tail HW.

## Runs

### N=8 exact

```text
D60=0 matches: 65,954
tail collisions: 0
best r61 HW: 5
best tail HW: 9
gh60 buckets: 616 / 65,536 possible
gh60 max bucket: 1,092, best tail in that bucket 9
r61 active-mask buckets: 62,891, max bucket 6
tail carry-signature buckets: 65,954, max bucket 1
coarse gh60+r61_hw buckets: 7,343, max bucket 170, best tail in max bucket 13
```

### N=10 exact

```text
D60=0 matches: 1,045,126
tail collisions: 0
best r61 HW: 6
best tail HW: 7
gh60 buckets: 2,653 / 1,048,576 possible
gh60 max bucket: 4,964, best tail in that bucket 15
r61 active-mask buckets: 1,016,509, max bucket 13
tail carry-signature buckets: 1,045,126, max bucket 1
coarse gh60+r61_hw buckets: 42,678, max bucket 683, best tail in max bucket 20
```

### N=11 exact

```text
D60=0 matches: 4,195,321
tail collisions: 0
best r61 HW: 5
best tail HW: 9
gh60 buckets: 15,863 / 4,194,304 possible
gh60 max bucket: 8,716, best tail in that bucket 14
r61 active-mask buckets: 4,173,220, max bucket 6
tail carry-signature buckets: 4,195,321, max bucket 1
```

### N=12 sampled, 1,048,576 prefixes

```text
prefix sample: 1,048,576 / 16,777,216 prefixes
D60=0 matches: 1,047,131
tail collisions: 0
best r61 HW: 8
best tail HW: 11
gh60 buckets: 41,482 / 16,777,216 possible
gh60 max bucket: 896, best tail in that bucket 22
r61 active-mask buckets: 1,047,089, max bucket 2
tail carry-signature buckets: 1,047,131, max bucket 1
```

### N=12 sampled, 262,144 prefixes, after coarse-key instrumentation

```text
D60=0 matches: 260,993
tail collisions: 0
best r61 HW: 9
best tail HW: 15
gh60 buckets: 31,987 / 16,777,216 possible
gh60 max bucket: 247, best tail in that bucket 24
r61 active-mask buckets: 260,987, max bucket 2
tail carry-signature buckets: 260,993, max bucket 1
coarse gh60+r61_hw buckets: 151,189, max bucket 34, best tail in max bucket 27
```

## Interpretation

`D60=0` is not the construction bottleneck. It lands at random rate.

The enhanced keys split into three classes:

1. `(g60,h60)` is strongly compressed. This is a real MITM interface, but the
   fattest buckets do not automatically contain the best tail residual.
2. Exact r61 active masks are almost injective by N=10 and later. They are too
   fine as a meet key.
3. Tail carry signatures are fully injective in every run. Exact carry-chamber
   identity is not reusable as a table key.

So the next key should not be exact r61 mask or exact carry signature. It should
be a coarse projection, but not an occupancy-only projection:

```text
candidate key = gh60 + selected late-register active bits + learned tail score
```

The first coarse attempt, `gh60+r61_hw`, keeps multiplicity but does not rank
well. Its fattest buckets are actively mediocre:

- N=8: max coarse bucket best tail 13 while global best is 9.
- N=10: max coarse bucket best tail 20 while global best is 7.
- N=12 sample: max coarse bucket best tail 27 while global best is 15.

The target is not the fattest bucket. The target is a bucket whose conditional
tail distribution is shifted downward while retaining enough multiplicity for
MITM matching.

## Single-bit supervised feature check

The prototype also ranks r61 active bits by mean-tail improvement:

```text
gain(bit) = mean_tail(bit inactive) - mean_tail(bit active)
```

This is weak. The best gains are only around hundredths of a tail bit:

- N=8: best shown mean shift about 0.13 tail bits.
- N=10: best shown mean shift about 0.02 tail bits.
- N=12 sample: best shown mean shift about 0.05 tail bits.

So one-bit r61 filters are not a useful selector. They preserve too much of the
background distribution. The next selector should test interactions:

```text
gh60 + pairs/triples of late-register bits
gh60 + low-dimensional learned score
gh60 + projected carry features, not exact carry signatures
```

The immediate engineering shape is a top-k supervised bucket miner: stream
`D60=0` matches, score coarse feature buckets by best-tail or low-tail rate,
and keep only the promising buckets rather than exact masks/signatures.

## Late-register pair-state check

A follow-up scans all pair states over r61 registers 6 and 7. This is still
weak:

- N=8: best pair-state mean shift about 0.17 tail bits; best tail in top
  pair buckets still only matches the global best by luck.
- N=10: best pair-state mean shift about 0.06 tail bits; best tails in top
  pair buckets are mostly 8 to 13 while the global best is 7.
- N=12 sample: best pair-state mean shift about 0.18 tail bits in a tiny bucket,
  but best tail in top pair buckets is 15 to 28 while the global best is 15.

Pair states are slightly stronger than one-bit states but still not a usable
ranking function. This closes the simple manual feature path:

```text
r61_hw                  weak
single late r61 bit      weak
late r61 bit pair state  weak
exact r61 mask           too fine
tail carry signature     injective
```

The next tool should be a streaming top-k bucket miner over many projected
features, scoring by low-tail rate directly instead of by mean shift or bucket
size.

## Streaming projected-bucket miner

Implemented a streaming miner over ten projected key families:

```text
gh60
gh60+r61_hw
gh60+reg6hw+reg7hw
gh60+late_fold8
gh60+reg6_low8
gh60+reg7_low8
gh60+reg6_high8
gh60+reg7_high8
r61hw+reg_hw+fold8
reg_hw+late_fold8
```

The miner tracks count, mean tail HW, best tail HW, and low-tail counts at
thresholds 8/12/16/20/24/32. It reports top buckets by low-tail rate, by
rate-weighted score, and by best observed tail.

### N=8 exact

```text
D60=0 matches: 65,954
best tail HW: 9
miner unique buckets: 36,750 / 2,097,152
low threshold: <=16
```

Best low-rate buckets are real but shallow:

```text
r61hw+reg_hw+fold8 key=0x00000000f8850f cnt=32 low=6 rate=0.188 mean=20.84 best=16
gh60+r61_hw       key=0x000000000942a3 cnt=39 low=7 rate=0.179 mean=19.46 best=12
```

The best-tail list recovers the global HW9 witness through large `gh60` and
`reg_hw+late_fold8` buckets.

### N=10 exact

```text
D60=0 matches: 1,045,126
best tail HW: 7
miner unique buckets: 197,465 / 33,554,432
low threshold: <=12
```

The apparent best low-rate buckets are mostly 32-count one-hit artifacts:

```text
gh60+reg6_low8  key=0x00000004eda88e cnt=32 low=1 rate=0.031 mean=29.88 best=11
gh60+late_fold8 key=0x0000000a096b9a cnt=32 low=1 rate=0.031 mean=29.22 best=10
gh60+r61_hw     key=0x00000000b8609a cnt=32 low=1 rate=0.031 mean=22.66 best=12
```

The best-tail list does retrieve the global HW7 witness, but not as an enriched
bucket:

```text
reg_hw+late_fold8 key=0x000000000344a3 cnt=4555 low=1 rate=0.000 mean=30.11 best=7
gh60              key=0x00000000099886 cnt=2150 low=1 rate=0.000 mean=30.08 best=7
```

### N=12 sampled, 262,144 prefixes

```text
D60=0 matches: 260,993
best tail HW: 15
miner unique buckets: 859,469 / 8,388,608
low threshold: <=20
```

Top low-rate buckets are again small or duplicate the same coarse `gh60`
surface:

```text
gh60+reg7_high8 key=0x0000001010309f cnt=43 low=2 rate=0.047 mean=34.51 best=20
gh60            key=0x0000000010309f cnt=43 low=2 rate=0.047 mean=34.51 best=20
```

The best-tail list can still surface the best sampled HW15 witnesses:

```text
reg_hw+late_fold8 key=0x0000000000b906 cnt=104 low=1 rate=0.010 mean=35.14 best=15
gh60              key=0x000000000e3f91 cnt=24  low=1 rate=0.042 mean=37.17 best=15
gh60              key=0x000000007f1193 cnt=17  low=1 rate=0.059 mean=36.35 best=15
```

## Streaming-miner verdict

The projected-bucket miner changes the next move. It can recover buckets that
contain the global best reduced-N witnesses, but the useful event is isolated
inside those buckets. Bucket-level low-tail rate is not enriched enough to be a
standalone construction rule.

That means the next sr=61-useful tool should not merely pick buckets. It should
store witnesses from the top best-tail buckets, then run a second-stage local
refinement inside those buckets:

```text
coarse bucket -> keep best witnesses -> local mutate W57/W58/W59 or nearby
projection bits -> re-test D60=0 and tail HW
```

The current evidence says `D60=0 + projected bucket` is a good address system,
not yet a closing constraint.

## Engineering note

The enhanced exact N=11 run scanned `8,589,934,592` triples in 287.8 seconds.
The arithmetic scan is cheap enough; the bottleneck is signature-table memory
traffic. Future versions should keep top-k coarse buckets or shard prefix ranges
instead of storing exact high-cardinality signatures.
