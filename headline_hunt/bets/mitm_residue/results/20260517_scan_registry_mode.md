# 2026-05-17: Scan-Only Witness Registry and N=13 Sweep

Runner: mac-codex

## Question

The prefix-surface refinement work showed broad disjoint sampling is more
productive than local mutation around one witness. Can we remove the heavy
profiling cost, retain only useful low-tail witnesses, and push the same
free-word MITM surface into N=13?

## Implementation

Extended `free_word_mitm_reducedn.c`:

```text
/private/tmp/free_word_mitm_reducedn N [prefix_limit] [refine_budget] [refine_seed_cap] [sample_start] [mode]
```

Changes:

- `mode=scan` disables dense/key profiling tables and keeps a compact witness
  registry of low-tail `D60=0` hits.
- The witness registry is also used as the seed pool when a second-stage
  refinement budget is provided.
- N=13 now has a deterministic random-fallback candidate search when the old
  fixed-fill `da56=0` seed does not exist.

## Controls

### N=8 exact smoke

```text
command: /private/tmp/free_word_mitm_reducedn 8 0 0 16 0 scan
D60=0 matches: 65,954
best tail HW: 9
registry: populated with tail 9/10 witnesses
```

This matches the known N=8 exact lead and confirms scan mode did not change the
scoring surface.

### N=13 seed

The fixed-fill seed does not produce `da56=0` at N=13. The deterministic
random-fallback seed does:

```text
N=13
candidate M0=0x974
mode=random-fallback
kernel=dM0=dM9=0x1000
```

## N=13 Scan Sweep

Each row scanned `65,536` permuted `(W57,W58)` prefixes and all `8,192` `W59`
values per prefix, i.e. `536,870,912` triples per row. Total coverage here is
`1,310,720 / 67,108,864` N=13 prefixes, about `1.95%`.

```text
sample_start  best tail  tail r61  best r61  best W1[57..59]     best W2[57..59]
0             17         14        11        10e6,00cd,103b      0a62,1639,0a92
65536         19         15        10        054e,18b4,1aa0      1eca,08fe,1b86
131072        16         15        11        1a35,0aa2,0960      13b1,0a3d,0c4d
196608        14         16        11        186f,17f9,1770      11eb,0b72,0ff5
262144        19         14        11        0c84,17db,0820      0600,1361,0bcf
327680        19         16        11        0750,0b38,0938      00cc,1f26,1278
393216        18         24        10        0d8d,1a7a,0911      0709,019e,0fb9
458752        20         18        10        094a,0b8d,0b0f      02c6,1a1b,052d
524288        19         21        9         09c7,0b7e,0f4b      0343,0d94,0e40
589824        16         12        11        161a,1c7e,1ca0      0f96,11dd,1758
655360        19         17        11        1b31,09db,0afb      14ad,1e73,106a
720896        19         23        11        17a4,1877,0525      1120,074d,0f8b
786432        18         18        9         076b,0553,0872      00e7,1f68,14ad
851968        20         17        9         06ef,01c8,0777      006b,1541,13f4
917504        19         12        11        1a88,125d,160e      1404,0cf9,1f84
983040        18         15        10        12fa,075a,0235      0c76,1c2a,1dd5
1048576       12         22        10        0092,0dbf,0ae1      1a0e,05d3,1eb2
1114112       18         18        11        1eb4,10f6,11fc      1830,0a1a,019a
1179648       16         23        9         0779,1770,0d2c      00f5,115a,0933
1245184       18         21        10        1562,1e5d,1a30      0ede,1770,153f
```

Best N=13 lead found in this sweep:

```text
sample_start = 1048576
tail HW      = 12
r61 HW       = 22
W1[57..59]   = 0092,0dbf,0ae1
W2[57..59]   = 1a0e,05d3,1eb2
```

Best N=13 r61 lead found in this sweep:

```text
r61 HW = 9
seen at sample_start 524288, 786432, 851968, and 1179648
```

`D60=0` stayed near random expectation across all windows. The useful signal is
still in broad witness sampling, not in raw `D60` enrichment.

## Focused Refinement on the N=13 HW12 Window

```text
command: /private/tmp/free_word_mitm_reducedn 13 65536 500000000 1024 1048576 scan
scan best tail HW: 12
refinement tested: 500,000,000
prefix_enums: 61,019
refinement D60=0: 63,497
collisions: 0
best refined tail HW: 12
best refined r61 HW: 10
```

The HW12 witness survived the focused surface pass, but the local neighborhood
did not improve. This is consistent with the earlier N=12 HW11 behavior:
low-tail witnesses appear isolated under nearby `(W57,W58)` prefix-fiber
refinement.

## Interpretation

Scan-only mode is the right current CPU primitive. It makes N=13 cheap enough
to sample in parallel and gives compact witness output without paying for
profiles that already looked weak.

Current reduced-N frontier from this branch:

```text
N=12 best tail HW: 11 at sample_start 524288
N=13 best tail HW: 12 at sample_start 1048576
```

Next useful work is more disjoint N=13/N=14 scan windows, plus a separate
attempt at a nonlocal combiner over retained witness registries. Local
prefix-fiber refinement remains useful as a validator, but not as the main
search engine.

## Continuation: r61 Registry and Wider N=13 Sweep

After the first 20-window sweep, scan mode was extended with a second retained
registry sorted by `r61_hw` first. The original witness registry is still
tail-first. The reason is empirical: some very low-r61 witnesses have mediocre
tail scores and were getting printed as the single best-r61 line but not
retained in the seed pool or compact registry.

Control:

```text
command: /private/tmp/free_word_mitm_reducedn 8 0 0 16 0 scan
best tail HW: 9
best r61 HW: 5
tail-first registry: populated with tail 9/10 witnesses
r61-first registry: populated with r61 5/6 witnesses
```

The extended N=13 sweep now covers `59` unique windows of `65,536` prefixes:

```text
unique prefixes covered: 3,866,624 / 67,108,864 = 5.76%
unique triples covered: 31,675,383,808
plus one targeted duplicate rerun of sample_start 2031616
```

The N=13 tail frontier did not improve beyond HW12. The r61 frontier improved:

```text
sample_start = 2031616
r61 HW       = 8
tail HW      = 28
gh60         = 0x500561
W1[57..59]   = 0486,020a,1fcf
W2[57..59]   = 1e02,169e,0967
```

The targeted rerun with the r61 registry confirmed why this needs a separate
retainer: the r61-HW8 witness is not competitive on tail score. It would not be
kept by a tail-first top-k registry.

Notable combined tail/r61 witnesses from the wider scan:

```text
sample_start  tail HW  r61 HW  W1[57..59]       W2[57..59]
1441792       16       9       0400,0c51,037a   1d7c,0e75,0007
2752512       18       9       06f0,108e,1ef9   006c,1018,1831
3538944       19       10      1d06,000c,080c   1682,1ca4,1593
3735552       19       10      0478,1884,02bd   1df4,0e7e,10aa
```

Interpretation update: tail minimization and r61 minimization are correlated
enough to produce occasional joint hits, but not enough that one registry can
serve both goals. Keep both registries for future nonlocal recombination.

## N=14 Pilot

Ran four N=14 scan windows after the r61-registry commit. Each row used
`32,768` prefixes and all `16,384` `W59` values per prefix, so the per-process
work stayed at `536,870,912` triples.

N=14 also required the deterministic random-fallback seed:

```text
candidate M0=0x3d36
mode=random-fallback
kernel=dM0=dM9=0x2000
```

Results:

```text
sample_start  best tail  tail r61  best r61  best W1[57..59]       best W2[57..59]
0             24         17        15        37f6,0479,08db        3703,36b9,30cc
32768         20         15        14        354d,1b36,1ba6        345a,1535,2ffc
65536         20         22        15        192e,2a33,0bb3        183b,3bb3,1625
98304         21         17        13        12bb,11a2,2fc8        11c8,35c7,0162
```

Best N=14 tail pilot lead:

```text
tail HW      = 20
sample_start = 32768
W1[57..59]   = 354d,1b36,1ba6
W2[57..59]   = 345a,1535,2ffc
r61 HW       = 15
```

Best N=14 r61 pilot lead:

```text
r61 HW       = 13
sample_start = 98304
tail HW      = 27
W1[57..59]   = 15bd,3fae,248c
W2[57..59]   = 14ca,3fb1,3397
```

N=14 scan rate stayed around `23M` triples/sec per worker in this mixed batch.
The first N=14 tail scores are not yet close to the N=13 frontier, but the
interface scales operationally.

The same mixed batch also added four more N=13 windows
(`sample_start=3866624..4063232`) with no frontier improvement. Total N=13
coverage for this artifact is now:

```text
unique windows: 63
unique prefixes covered: 4,128,768 / 67,108,864 = 6.15%
unique triples covered: 33,822,867,456
tail frontier: HW12 at sample_start 1048576
r61 frontier: HW8 at sample_start 2031616
```

## Continuation: Summary Lines and N=13 HW9 Lead

Added a single-line `SUMMARY` record to scan output so broad sweeps can be
parsed without retaining the full witness registry:

```text
SUMMARY N=13 sample_start=5570560 prefixes=65536 total=536870912 d0=66059 best_tail=9 tail_r61=17 best_r61=10 tail_W1=0x4cb,0xeaa,0x196e tail_W2=0x1e47,0x13bf,0x29e r61_W1=0x1346,0xfb0,0x1233 r61_W2=0xcc2,0x153c,0x15a9
```

Continued N=13 broad scan from `sample_start=4128768` through `6094848`.
This added 31 more unique windows after the previous 63-window checkpoint.
Total N=13 coverage for this artifact is now:

```text
unique windows: 94
unique prefixes covered: 6,160,384 / 67,108,864 = 9.18%
unique triples covered: 50,465,865,728
plus four targeted duplicate refinement/registry reruns over already-covered windows
```

New tail frontier:

```text
sample_start = 5570560
tail HW      = 9
r61 HW       = 17
gh60         = 0x1d065e3
W1[57..59]   = 04cb,0eaa,196e
W2[57..59]   = 1e47,13bf,029e
```

The first HW9 hit came from the scan-only pass. A focused second-stage local
refinement on the same window validated the witness but did not improve it:

```text
command: /private/tmp/free_word_mitm_reducedn 13 65536 500000000 1024 5570560 scan
scan best tail HW: 9
refinement tested: 500,000,000
prefix_enums: 61,019
refinement D60=0: 64,120
collisions: 0
best refined tail HW: 9
best refined r61 HW: 10
```

The r61 frontier remains HW8. The latest matching r61-HW8 witness was:

```text
sample_start = 5177344
r61 HW       = 8
tail HW      = 21
W1[57..59]   = 12ae,0b33,127c
W2[57..59]   = 0c2a,1bfd,1af2
```

Interpretation update: broad disjoint scan is still the main productive engine.
The HW9 witness is a large enough jump that subsequent work should bias toward
neighboring broad coverage and nonlocal recombination over retained witnesses,
while using local prefix-fiber refinement only as a validator.

## Continuation: Logged All-Day N=13 Sweep

Added lightweight batch tooling:

```text
headline_hunt/bets/mitm_residue/prototypes/run_scan_batch.py
headline_hunt/bets/mitm_residue/prototypes/summarize_scan_batch.py
headline_hunt/bets/mitm_residue/results/runs/20260517_n13_scan_batch/summaries.jsonl
```

The runner writes one log per window and appends parsed `SUMMARY` rows to JSONL.
The summarizer deduplicates by `sample_start` and reports coverage/frontiers.

Checkpoint after logged windows `102..885`, combined with the earlier manual
windows `0..101`:

```text
unique windows: 886
unique prefixes covered: 58,064,896 / 67,108,864 = 86.52%
unique triples covered: 475,667,628,032
tail frontier: HW7 at sample_start 24641536
r61 frontier: HW7 in seven logged windows
```

The logged sweep found a new joint tail/r61 lead:

```text
sample_start = 24641536
tail HW      = 7
r61 HW       = 9
gh60         = 0x121d21
W1[57..59]   = 0f36,07db,082b
W2[57..59]   = 08b2,1b15,1ef6
```

Focused validation on that window:

```text
command: /private/tmp/free_word_mitm_reducedn 13 65536 500000000 1024 24641536 scan
refinement tested: 500,000,000
prefix_enums: 61,019
refinement D60=0: 64,306
collisions: 0
best refined tail HW: 7
best refined r61 HW: 9
```

Best logged tail rows:

```text
sample_start  tail HW  tail r61  best r61  W1[57..59]       W2[57..59]
24641536      7        9         9         0f36,07db,082b   08b2,1b15,1ef6
38404096      10       12        11        1d6a,1a83,0914   16e6,1622,1287
36765696      11       15        10        08f3,1d31,083e   026f,11a8,1382
9961472       12       13        10        0c8d,0983,14dd   0609,02a2,127e
53477376      12       18        10        1c27,12e3,1e02   15a3,083e,18a4
41025536      12       14        11        0f80,0ed5,1d57   08fc,1141,0f5c
55377920      12       14        11        0856,0478,11b0   01d2,1192,0689
8126464       13       11        10        11f0,0e92,122e   0b6c,1f19,17a5
19988480      13       16        10        11ff,1bae,01e1   0b7b,15e8,0b0c
30736384      13       18        10        13d6,1ff1,10bc   0d52,0737,1e8c
```

The r61 side improved to HW7 and then repeated. Full-registry reruns were done
for the first three HW7 r61-only points; later scan-only repeats are retained
in the JSONL:

```text
sample_start = 26607616
r61 HW       = 7
tail HW      = 16
W1[57..59]   = 0368,1385,0157
W2[57..59]   = 1ce4,16cd,17cf

sample_start = 8257536
r61 HW       = 7
tail HW      = 27
W1[57..59]   = 1330,1b38,04f8
W2[57..59]   = 0cac,0be6,0d2e

sample_start = 14680064
r61 HW       = 7
tail HW      = 32
W1[57..59]   = 1e88,157b,0b71
W2[57..59]   = 1804,1397,0b67

sample_start = 22151168
r61 HW       = 7
tail HW      = 33
W1[57..59]   = 0288,15af,16e2
W2[57..59]   = 1c04,0847,08ea

sample_start = 28442624
r61 HW       = 7
tail HW      = 19
W1[57..59]   = 02b0,195e,15b0
W2[57..59]   = 1c2c,0a0c,1228

sample_start = 47054848
r61 HW       = 7
tail HW      = 20
W1[57..59]   = 1366,0abe,1713
W2[57..59]   = 0ce2,0e22,0dd9

sample_start = 54853632
r61 HW       = 7
tail HW      = 16
W1[57..59]   = 0f48,0b0a,0a7b
W2[57..59]   = 08c4,167e,1071
```

Crossing 86% of N=13 did not improve below tail HW7. The new tail-HW7 witness
is still the only strong joint tail/r61 hit, with `tail HW=7` and `r61 HW=9`
in the same witness. The added windows `630..885` are coverage-only so far;
their best new tails are HW12 at `sample_start=53477376` and
`sample_start=55377920`.
