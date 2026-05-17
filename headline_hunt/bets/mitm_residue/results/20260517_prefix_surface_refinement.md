# 2026-05-17: Prefix-Surface Refinement and N=12 Sample Sweep

Runner: mac-codex

## Question

Raw local mutation around low-tail witnesses did not improve the tail. Does a
more structured second stage help if it keeps work on the `D60=0` interface by
enumerating full `W59` fibers for nearby `(W57,W58)` prefixes?

## Implementation

Extended `free_word_mitm_reducedn.c` again:

```text
/private/tmp/free_word_mitm_reducedn N [prefix_limit] [refine_budget] [refine_seed_cap] [sample_start]
```

Changes:

- refinement now first enumerates full `W59` fibers for neighboring
  `(W57,W58)` prefixes around retained top witnesses,
- reports `prefix_enums` and separates prefix-fiber tests from single/double
  local bit tests,
- `sample_start` shifts the permuted-prefix sample window, enabling disjoint
  N=12 samples to run in parallel.

## Controls

### N=8 exact

```text
command: /private/tmp/free_word_mitm_reducedn 8 0 100000 64
scan best tail HW: 9
prefix_enums: 389
prefix-phase tests: 99,400
refinement D60=0: 372
best refined tail HW: 9
```

### N=10 exact

```text
command: /private/tmp/free_word_mitm_reducedn 10 0 1000000 128
scan best tail HW: 7
prefix_enums: 975
prefix-phase tests: 998,140
refinement D60=0: 983
best refined tail HW: 7
```

Both exact controls stayed at their known best tails.

## N=12 Sample Sweep

Each row scanned `262,144` permuted prefixes, i.e. `1,073,741,824` triples.

```text
sample_start  best tail HW  best r61 HW  best W1[57..59]      best W2[57..59]
0             15            16           a82,76b,cae          4b7,90f,189
262144        14            22           d07,e73,c6b          73c,b42,3ab
524288        11            14           e43,203,594          878,faf,d04
786432        14            16           509,939,ef4          f3e,989,5e1
1048576       14            17           e4b,e90,d70          880,c50,840
1310720       13            15           a6f,3d0,cee          4a4,747,bcd
1572864       13            15           720,eba,80e          155,9e9,c6f
1835008       15            18           66c,e66,89f          0a1,e98,19d
2097152       15            14           3a8,b16,1f3          ddd,065,bcf
```

The sample sweep covered `2,359,296` of `16,777,216` N=12 prefixes, about
14.1% of the prefix space. The best reduced-N lead improved from HW15 to HW11.

## Focused Prefix Refinement on the HW11 Window

```text
command: /private/tmp/free_word_mitm_reducedn 12 262144 500000000 1024 524288
scan best tail HW: 11
refinement tested: 500,000,000
prefix_enums: 122,005
prefix-phase tests: 499,730,270
refinement D60=0: 126,199
seed inserts: 324
collisions: 0
best refined tail HW: 11
```

The HW11 witness survived a much larger local prefix-fiber search, but the
neighborhood did not produce a lower tail.

## Interpretation

The evidence now splits the work:

- Broader disjoint prefix sampling is productive. It found HW11 quickly.
- Local prefix-fiber refinement around the best witness is valid and cheap, but
  still does not behave like a basin descent.
- The best witnesses look isolated even when the refinement enumerates full
  `W59` fibers for nearby `(W57,W58)` prefixes.

Next engineering move:

```text
build a lean scan-only / witness-registry mode
run disjoint N=12 and then N=13 sample windows in parallel
retain only low-tail witnesses and their compact prefix keys
```

That is a better CPU use than spending more cycles on local mutation around the
current HW11 witness.
