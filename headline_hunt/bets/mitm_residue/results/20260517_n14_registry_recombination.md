# N=14 Registry Recombination Round

This round extended the post-N=13 search from staged N=14 sampling into
registry-rich recombination mining and a first D60-repair probe. It covers the
contiguous N=14 pilot, eight unique 32-window strided N=14 passes, and a
targeted cap64 registry rerun on the best joint and near-`gh60` windows.

## Coverage

Extended checkpoint after phases 10-38, excluding the known duplicate
`phase5`, completes two interleaved 32-window grids (`0 mod 16` and `8 mod
16`) and starts the `4 mod 16` grid:

```text
windows          = 1184
prefixes covered = 38,797,312 / 268,435,456 = 14.45%
scan triples     = 635,655,159,808
```

Current exact frontier histogram at this checkpoint:

```text
best_tail: 13:1 14:2 15:3 16:11 17:23 18:49 19:95 20:188 21:319 22:306 23:158 24:29
best_r61 : 10:8 11:55 12:174 13:414 14:415 15:117 16:1
```

The first exact `tail <= 13` row arrived in phase18:

```text
sample_start=235143168 window=7176
tail=13 tail_r61=18 best_r61=12
gh60=0x7ba5ca6
W1=0x00f4,0x0ddd,0x285e
W2=0x0001,0x160c,0x3600
```

The next exact rows are `tail=14` at `sample_start=117702656` and
`sample_start=92405760`. Phases19-38 did not improve the exact frontier. There
are still no exact rows with `tail <= 12` or `r61 <= 9`.

Unique N=14 scan coverage:

```text
windows          = 365
prefixes covered = 11,960,320 / 268,435,456 = 4.46%
scan triples     = 195,957,882,880
```

The targeted cap64 rerun added `12` selected windows and `6,442,450,944`
additional triples, but did not add new unique coverage because those windows
were already in the scan set.

`20260517_n14_strided_registry_phase5` is excluded from the unique coverage
count because its start offset aliases the original strided pass. It is a
non-counting duplicate run.

Aggregate N=14 frontier histogram:

```text
best_tail: 16:5 17:8 18:12 19:23 20:61 21:106 22:100 23:41 24:8 25:1
best_r61 : 10:3 11:16 12:63 13:126 14:116 15:41
```

No N=14 window in this set reached `tail <= 13` or `r61 <= 8`.

## Current N=14 Frontier

Best tail rows:

```text
sample_start=54001664  tail=16 tail_r61=14 best_r61=11 W1=3a8c,0a1e,2c98 W2=3999,2bde,19ba
sample_start=458752    tail=16 tail_r61=17 best_r61=13 W1=11ca,1856,0ef7 W2=10d7,36a3,3a86
sample_start=16252928  tail=16 tail_r61=20 best_r61=13 W1=1a86,2843,298f W2=1993,14b3,3c39
sample_start=229113856 tail=16 tail_r61=13 best_r61=13 W1=2b7c,0929,195f W2=2a89,32ed,09d7
sample_start=57147392  tail=16 tail_r61=18 best_r61=15 W1=103d,2758,112e W2=0f4a,17ff,150e
```

Best same-witness joint row is now `sample_start=229113856`: tail HW16 with
the same witness at r61 HW13. The best r61 rows remain non-joint:

```text
sample_start=67633152   r61=10 r61_tail=25 window_tail=20
sample_start=2097152    r61=10 r61_tail=36 window_tail=22
sample_start=215482368  r61=10 r61_tail=29 window_tail=22
```

## Recombination Mining

After de-duplicating repeated targeted rerun witnesses, the N=14 registry pool
contains:

```text
unique registry entries = 9,011
tail entries            = 4,506
r61 entries             = 4,505
```

Best exact `gh60` tail/r61 pairs:

```text
score=29 gh60=ca847a6  tail=16 r61=13 sample_start=229113856
score=30 gh60=fa045e6  tail=16 r61=14 sample_start=54001664
score=30 gh60=5684da6  tail=18 r61=12 sample_start=2392064
score=30 gh60=c609ce6  tail=19 r61=11 sample_start=1638400
score=31 gh60=570856e  tail=17 r61=14 sample_start=51904512
```

Best non-identical near-`gh60` pairs with Hamming distance <= 2:

```text
score=30 dist=2 tail=17 sample_start=51904512  r61=11 sample_start=224919552
score=32 dist=2 tail=16 sample_start=57147392  r61=14 sample_start=229113856
score=32 dist=2 tail=17 sample_start=51904512  r61=13 sample_start=240648192
score=32 dist=2 tail=16 sample_start=54001664  r61=14 sample_start=245891072
score=32 dist=2 tail=19 sample_start=102236160 r61=11 sample_start=54001664
```

These are leads for an interface-repair build, not closures by themselves. The
current scanner can find close `gh60` neighborhoods, but it has no extra degree
of freedom to repair the remaining tail/r61 disagreement once the row is fixed.

## Structural Read

Aggregate N=14 structural correlations versus best tail:

```text
best_r61             +0.0897
tail_r61             +0.3016
d0                   +0.0783
d0_prefixes          +0.0496
max_fiber            +0.0540
largest_bucket_count +0.0246
```

This matches the N=13 read: raw D60 density, prefix count, max fiber, and bucket
mass are not strong selectors. The same-tail-witness r61 score remains the only
visible weak signal, and it strengthened slightly as coverage grew.

## D60 Repair Probe

The first repair build adds `mode=repair`, which also scores low-HW nonzero
`D60` rows as if `W60_2` could be patched to the required value. This is a
conditional probe, not a proof that the SHA-256 schedule can realize the patch.

Best N=14 conditional results so far:

```text
k=1 repair candidates = 2,742,976
best repaired tail    = HW15 at sample_start=2392064, d60=0x4
best repaired r61     = HW11 at sample_start=54001664, d60=0x800

k=2 repair candidates = 13,731,684
best repaired tail    = HW15 at sample_start=54001664, d60=0xa00
best repaired r61     = HW10 at sample_start=16252928, d60=0x18

k=3 repair candidates = 92,158,389
best repaired tail    = HW11 at sample_start=57147392, d60=0xc
best repaired r61     = HW10 at sample_start=57147392, d60=0x1108

k=4 repair candidates = 192,537,508
best repaired tail    = HW10 at sample_start=2392064, d60=0x88a
best repaired r61     = HW9 at sample_start=2392064, d60=0x2188

k=5 repair candidates = 454,933,980
best repaired tail    = HW10 at sample_start=16252928, d60=0xc0b
best repaired r61     = HW9 at sample_start=54001664, d60=0x2305
```

The control at N=8 is positive: exact best tail HW12 in the smoke sample, while
the k=1 repair probe exposes repaired tail HW8 and r61 HW6. The N=14 repair
surface has not closed anything, but the k=4/k=5 jump from exact HW16 to
conditional HW10 and repaired r61 HW9 is strong enough to make the next
algebraic target concrete:
build the actual schedule-realizable repair variable instead of continuing only
with exact `D60=0` breadth.

## Next Move

Keep N=14 strided sampling as a background breadth tool, but do not expect
plain coverage to jump from HW16 to SR64. The higher-leverage build is now:

```text
1. Turn the D60 low-HW conditional rows into a real schedule-repair map.
2. Keep strided N=14 coverage as a background breadth test.
3. Use cap64 only on windows that produce tail+r61+gh60 scores <= 32.
4. Promote repaired tail <= 10, repaired r61 <= 9, exact tail <= 13, or exact
   r61 <= 8 into focused local repair search.
```
