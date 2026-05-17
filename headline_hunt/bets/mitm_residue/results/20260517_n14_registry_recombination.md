# N=14 Registry Recombination Round

This round extended the post-N=13 search from staged N=14 sampling into
registry-rich recombination mining. It covers the contiguous N=14 pilot, three
32-window strided N=14 passes, and a targeted cap64 registry rerun on the best
joint and near-`gh60` windows.

## Coverage

Unique N=14 scan coverage:

```text
windows          = 208
prefixes covered = 6,815,744 / 268,435,456 = 2.54%
scan triples     = 111,669,149,696
```

The targeted cap64 rerun added `12` selected windows and `6,442,450,944`
additional triples, but did not add new unique coverage because those windows
were already in the scan set.

Aggregate N=14 frontier histogram:

```text
best_tail: 16:3 17:5 18:9 19:13 20:37 21:66 22:54 23:16 24:4 25:1
best_r61 : 10:2 11:7 12:31 13:73 14:69 15:26
```

No N=14 window in this set reached `tail <= 13` or `r61 <= 8`.

## Current N=14 Frontier

Best tail rows:

```text
sample_start=54001664  tail=16 tail_r61=14 best_r61=11 W1=3a8c,0a1e,2c98 W2=3999,2bde,19ba
sample_start=458752    tail=16 tail_r61=17 best_r61=13 W1=11ca,1856,0ef7 W2=10d7,36a3,3a86
sample_start=16252928  tail=16 tail_r61=20 best_r61=13 W1=1a86,2843,298f W2=1993,14b3,3c39
```

Best true joint row is still `sample_start=54001664`: tail HW16 with the same
tail witness at r61 HW14. The best r61 rows remain non-joint:

```text
sample_start=2097152    r61=10 r61_tail=36 window_tail=22
sample_start=215482368  r61=10 r61_tail=29 window_tail=22
```

## Recombination Mining

After de-duplicating repeated targeted rerun witnesses, the N=14 registry pool
contains:

```text
unique registry entries = 3,897
tail entries            = 1,949
r61 entries             = 1,948
```

Best exact `gh60` tail/r61 pairs:

```text
score=30 gh60=fa045e6  tail=16 r61=14 sample_start=54001664
score=30 gh60=5684da6  tail=18 r61=12 sample_start=2392064
score=30 gh60=c609ce6  tail=19 r61=11 sample_start=1638400
score=33 gh60=4504566  tail=21 r61=12 sample_start=246939648
```

Best non-identical near-`gh60` pairs with Hamming distance <= 2:

```text
score=32 dist=2 tail=18 sample_start=3440640   r61=12 sample_start=2260992
score=32 dist=2 tail=18 sample_start=3440640   r61=12 sample_start=37224448
score=33 dist=2 tail=20 sample_start=230162432 r61=11 sample_start=1638400
score=33 dist=2 tail=19 sample_start=1835008   r61=12 sample_start=223870976
score=33 dist=2 tail=18 sample_start=263716864 r61=13 sample_start=2129920
score=33 dist=2 tail=17 sample_start=190316544 r61=14 sample_start=3178496
```

These are leads for an interface-repair build, not closures by themselves. The
current scanner can find close `gh60` neighborhoods, but it has no extra degree
of freedom to repair the remaining tail/r61 disagreement once the row is fixed.

## Structural Read

Aggregate N=14 structural correlations versus best tail:

```text
best_r61             +0.1400
tail_r61             +0.2585
d0                   +0.1142
d0_prefixes          +0.0063
max_fiber            +0.0330
largest_bucket_count -0.0534
```

This matches the N=13 read: raw D60 density, prefix count, max fiber, and bucket
mass are not strong selectors. The same-tail-witness r61 score is still the only
visible weak signal.

## Next Move

Keep N=14 strided sampling as a background breadth tool, but do not expect
plain coverage to jump from HW16 to SR64. The higher-leverage build is now:

```text
1. Turn exact gh60/near-gh60 registry pairs into a repairable interface.
2. Add one more controlled degree of freedom, likely D60 low-HW repair or W56/W60 widening.
3. Use cap64 only on windows that produce tail+r61+gh60 scores <= 33.
4. Continue strided N=14 coverage until either tail <= 13 or r61 <= 8 appears.
```
