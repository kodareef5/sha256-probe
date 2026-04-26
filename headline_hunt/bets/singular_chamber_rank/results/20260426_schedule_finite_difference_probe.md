# Schedule Finite-Difference Probe - 2026-04-26

## Reframe

The first fiber-count pass found fat reduced-N fibers for the sr=61 defect
map, but raw suffixes and simple `Ch`/`Maj` equality sheets did not explain
them globally.

The useful decomposition is:

```text
D(W57,W58,W59) = S(W57,W58) - R(W57,W58,W59)

S = W2_sched60 - W1_sched60
R = cascade_required_offset60 after round 59
```

For fixed `W57`, the cascade offset used at round 58 is fixed:

```text
off58 = cascade_offset(state after round 57)
```

Therefore the schedule side is just an additive finite difference of the
lower-case schedule function:

```text
S(W58) = C + sigma1(W58 + off58) - sigma1(W58)  mod 2^N
```

This is the first clean algebraic object found in this branch. The collapse
is not a solver artifact and not a suffix artifact.

## Raw suffix negative control

The local top chamber had strong-looking `W58` suffix families, but scanning
suffixes across all `W57` mostly destroys the signal.

| N | suffix bits | W57 scanned | best global suffix enrichment |
|---:|---:|---:|---:|
| 8  | 4 | 256  | 1.030 |
| 10 | 6 | 1024 | 1.034 |
| 12 | 8 | 4096 | 1.019 |

So `W58 mod 2^k` is not by itself a useful global predictor. The suffixes
are a coordinate shadow of a conditional chamber.

## Posterior carry filter

For a fixed fat `(W57,W58)` chamber, derive the carry bits that are invariant
over the observed `D=0` hits, then count all `W59` values satisfying those
same carry constraints.

| N | chamber | hits | carry-filter support | reduction | precision |
|---:|---|---:|---:|---:|---:|
| 8  | `W57=0x27,W58=0x0c`    | 6  | 31  | 8.26x  | 0.194 |
| 10 | `W57=0x50,W58=0x099`   | 14 | 80  | 12.80x | 0.175 |
| 12 | `W57=0x666,W58=0x393` | 21 | 130 | 31.51x | 0.162 |

This is posterior, so it is not an attack by itself. It is evidence that the
fat fibers are real carry chambers: the learned carry language keeps all
hits while cutting the `W59` space by 8x-31x in these reduced cases.

## Defect histogram: zero is not special

For fixed `W57=0x666` at N=12, counting all defects over `(W58,W59)` shows
the whole output distribution is overdispersed.

```text
mean bucket count = 4096
zero count        = 6985  (1.705x), rank 258
max bucket        = 8573  (2.093x), defect 0x9b9
Fano              = 639.687
```

So the chamber is not a magical zero-defect chamber. It is a biased arithmetic
field, and the collision condition asks whether the fixed target zero lands
in a fat bucket.

## Target alignment inside R(W59)

For fixed `(W57,W58)`, the `R(W59)` image itself is overdispersed. The best
known N=12 chamber aligns the schedule target with a maximum-preimage bucket:

```text
N=12, W57=0x666, W58=0x393
off58 = 0x00c
off59 = 0x671
S     = 0x1dd
R target count = 21
target rank    = 1
```

A nearby non-fat control in the same `W57` chamber does not align:

```text
N=12, W57=0x666, W58=0x000
S target count = 1
target rank    = 1089
```

Several top `W58` values in the fat chamber share the same schedule target
`S=0x1dd`:

```text
0x393 -> target count 21, rank 1
0x3b3 -> target count 17, rank 3
0x793 -> target count 16, rank 1
0x7b3 -> target count 14, rank 3
0x493 -> target count 13, rank 2
0x293 -> target count 12, rank 2
```

That is the current mechanism hypothesis:

```text
fat fiber = compressed S(W58) plateau + alignment with a fat R(W59) bucket
```

## Exact schedule-side collapse

`schedscan` measures the exact image of `S(W58)` for fixed `W57`. Because
`S` differs from `sigma1(W58+off58)-sigma1(W58)` only by an additive constant,
`sigmadiff` gives the same image statistics.

| N | chamber | off58 | occupied S values | image fraction | max bucket |
|---:|---|---:|---:|---:|---:|
| 10 | `bit=9,W57=0x50`   | `0x0e0`  | 74 / 1024     | 0.0723 | 32  |
| 12 | `bit=11,W57=0x666` | `0x00c`  | 152 / 4096    | 0.0371 | 256 |
| 14 | `bit=1,W57=0x30`   | `0x21ff` | 433 / 16384   | 0.0264 | 304 |

The N=12 top schedule offset `0x1dd` has 256 different `W58` preimages.
This explains why many `W58` values can share the same target.

## Isolated finite-difference geometry

Exact `sigmadiff` scans at N=16 show that the image size depends strongly on
the additive delta:

| N | delta | occupied values | image fraction | max bucket |
|---:|---:|---:|---:|---:|
| 16 | `0x000c` | 661 / 65536  | 0.0101  | 5120 |
| 16 | `0x00e0` | 1254 / 65536 | 0.0191  | 1152 |
| 16 | `0x21ff` | 4027 / 65536 | 0.0614  | 404  |
| 16 | `0x8000` | 8 / 65536    | 0.00012 | 8192 |

The MSB delta case is extreme: adding the high bit only flips a small rotated
and shifted footprint in `sigma1`, so the schedule finite difference has only
8 possible values at N=16.

## Can cascade steer off58 into singular deltas?

`off58scan` checks which round-58 cascade offsets are reachable by varying
`W57`.

| N | bit/fill | W57 values | occupied off58 | exact MSB off58 |
|---:|---|---:|---:|---:|
| 10 | `bit=9,fill=0x3ff`  | 1024  | 520  | 1 |
| 12 | `bit=11,fill=0xfff` | 4096  | 2441 | 3 |
| 14 | `bit=1,fill=0x3fff` | 16384 | 8620 | 0 |

At N=12 the exact-MSB `off58=0x800` chambers are:

```text
W57 = 0x599, 0xdc1, 0xe62
```

Their total `D=0` counts are not exceptional:

| N | W57 | off58 | total hits | enrichment | best W58 hits |
|---:|---:|---:|---:|---:|---:|
| 12 | `0x599` | `0x800` | 4150 | 1.013 | 13 |
| 12 | `0xdc1` | `0x800` | 4654 | 1.136 | 19 |
| 12 | `0xe62` | `0x800` | 4131 | 1.009 | 17 |

So extreme schedule collapse is not sufficient. It gives a small set of
targets, but the `R(W59)` side still has to place mass on those targets.

## Interpretation

The useful object is no longer "find low local rank" in the naive Jacobian
sense. The local rank stayed full. The nonlinear structure is a pair of
finite-difference/carry maps:

```text
W58 side: compressed target map S_delta(W58)
W59 side: overdispersed required-offset image R_delta(W59)
success:  S_delta(W58) lands in a fat R_delta(W59) bucket
```

This creates real reduced-N multiplicities of 12x-21x for selected
`(W57,W58)` fibers and posterior carry filters up to 31x. That is not a
full-N collision reduction yet. It is a sharper attack surface than raw
suffixes, Ch/Maj equality sheets, or local derivative rank.

## Next targets

1. Build a finite automaton for `sigma1(w+delta)-sigma1(w)` from carry-chain
   states, then score `off58` values without enumerating all `W58`.
2. Characterize reachable `off58` values from the cascade as a controllable
   map of `W57`.
3. For the `R(W59)` side, isolate the analogous fixed-`off59` finite
   difference components and learn which `off59` values create fat buckets.
4. Search for chambers where a singular `S` delta and a fat `R` target
   align before doing any larger brute force.
