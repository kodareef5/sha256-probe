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
