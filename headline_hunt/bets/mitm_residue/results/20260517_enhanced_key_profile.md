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

## Engineering note

The enhanced exact N=11 run scanned `8,589,934,592` triples in 287.8 seconds.
The arithmetic scan is cheap enough; the bottleneck is signature-table memory
traffic. Future versions should keep top-k coarse buckets or shard prefix ranges
instead of storing exact high-cardinality signatures.
