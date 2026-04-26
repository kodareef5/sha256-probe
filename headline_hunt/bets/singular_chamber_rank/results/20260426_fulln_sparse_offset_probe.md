# Full-N Sparse Offset Probe - 2026-04-26

## Starting point

The reduced-N finite-difference probe isolated the schedule-side object:

```text
S(W58) = C + sigma1(W58 + off58) - sigma1(W58)
```

The next question was whether full 32-bit cascade states can steer `off58`
into sparse deltas where this finite difference has a compressed image.

## Sparse off58 is reachable

Exact Newton to a chosen target such as `off58=0x0000000c` failed on the
representative full-N candidates. The local tangent of `off58(W57)` is often
deficient near that exact target.

But simple one-bit local descent on `HW(off58)` works well. With 512 starts
per representative candidate, many candidates reached `off58` Hamming weight
2 or 3.

Examples:

| candidate index | candidate | W57 | off58 | HW |
|---:|---|---:|---:|---:|
| 0 | `msb_cert_m17149975_ff_bit31` | `0x370fef5f` | `0x00000021` | 2 |
| 3 | `bit20_m294e1ea8_ff` | `0xe28da599` | `0x00000802` | 2 |
| 8 | `bit3_m33ec77ca_ff` | `0xaf07f044` | `0x00010002` | 2 |

This is a material steering result: sparse schedule deltas are not merely
reduced-N artifacts.

## Full-N schedule collapse survives sampling

For one million random `W58` samples, sparse full-N `off58` values produce
far fewer schedule targets than random-looking deltas.

| delta | sampled unique arithmetic `sigma1` differences | top bucket count |
|---:|---:|---:|
| `0x00000021` | 9,185 / 1,000,000 | 22,147 |
| `0x00000070` | 8,317 / 1,000,000 | 33,247 |
| `0x00000802` | 54,017 / 1,000,000 | 10,074 |
| `0x00010002` | 55,401 / 1,000,000 | 18,675 |
| `0xdeadbeef` | 971,264 / 1,000,000 | 11 |

In real candidate context, `schedsample` shows the same compression:

| idx | W57 | off58 | unique `S(W58)` in 1M samples | top plateau |
|---:|---:|---:|---:|---:|
| 0 | `0x370fef5f` | `0x00000021` | 9,233 | 22,210 |
| 3 | `0xe28da599` | `0x00000802` | 53,973 | 10,163 |
| 8 | `0xaf07f044` | `0x00010002` | 55,583 | 18,744 |

The schedule side of the sr=61 defect is therefore severely nonuniform in
reachable full-N chambers.

## R side falsification

Taking top schedule plateaus and sampling `R(W59)` did not show matching
compression. For example:

```text
idx=0, W57=0x370fef5f, W58=0xf0f7e442
off58 = 0x00000021
off59 = 0x419de81e
S     = 0x6175cc4a
R unique in 1M W59 samples = 999,095
target hits = 0
max sampled R bucket = 2
```

Even after choosing W58 to make `off59` sparse, `R(W59)` remained essentially
uniform in one million samples:

| idx | W57 | W58 | off58 | off59 | R unique / 1M | target hits |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | `0x370fef5f` | `0xb115f94b` | `0x00000021` | `0x00000086` | 999,294 | 0 |
| 3 | `0xe28da599` | `0x233e4216` | `0x00000802` | `0x00000840` | 999,500 | 0 |
| 8 | `0xaf07f044` | `0xc72c7c36` | `0x00010002` | `0x08010000` | 999,522 | 0 |

So the reduced-N fat `R` buckets do not transfer as a simple "sparse off59"
rule. The R side depends on deeper post-round carry/state geometry.

## Local rank of the W59 side

For fixed `(W57,W58)`, the local derivative rank of `D` with respect to W59
is usually deficient but not catastrophically low.

Example for the top schedule plateau:

```text
idx=0, W57=0x370fef5f, W58=0xf0f7e442
rank histogram over 1024 W59 samples:
26:2, 27:6, 28:39, 29:159, 30:380, 31:367, 32:71
```

Sparse-off59 chambers look similar:

```text
idx=3, W57=0xe28da599, W58=0x233e4216
off59=0x00000840
rank histogram:
27:1, 28:17, 29:103, 30:364, 31:432, 32:107
```

That explains why W59-only Newton frequently stalls: the tangent is often
rank-deficient. But the rank loss is not enough to make `R` globally small.

## One-bit full-N sr61 defect

Greedy local descent on W59 defect Hamming weight produced full-N sr=61
near misses with only 1-2 defect bits.

Best current point:

```text
candidate idx 3: bit20_m294e1ea8_ff
W57 = 0xe28da599
W58 = 0x233e4216
W59 = 0xda9932f8
off58 = 0x00000802
off59 = 0x00000840
defect = 0x20000000
HW(defect) = 1
```

This came from a sparse-offset chamber:

```text
start W59 defect-hill best: 0x20001000 (HW2)
radius-4 neighborhood over W58/W59 found: 0x20000000 (HW1)
```

The one-bit point is not trivially adjacent to an exact sr=61 compatibility
point:

```text
neighborhood over W58/W59, radius <= 5: no exact hit
neighborhood over W57/W58/W59, radius <= 5: no exact hit
```

The all-word radius-5 check tested 64,593,561 points around the HW1 point.

## Interpretation

The full-N picture is now sharper:

1. The schedule side can be forced into a severe finite-difference collapse
   by steering `off58` sparse.
2. Sparse `off59` by itself does not collapse the round-required side.
3. The R side has local rank defects and can be descended to HW1, but the
   final bit sits behind a nonlocal carry transition.

This is not yet a collision and not yet a formal collision-difficulty
reduction. It is a reproducible full-N mechanism that gets the true sr=61
defect from 32 random-looking bits down to 1 bit in a structured chamber.

## Next

The next useful direction is not larger random sampling. It is to model the
final carry transition around the HW1 point:

- identify which carry bit produces `0x20000000`,
- trace that bit backward through the three additions in
  `cascade_required_offset60`,
- find a move that changes that carry without destroying the sparse
  `off58/off59` chamber,
- or deliberately choose S plateaus whose target differs from the reachable R
  image by that carry bit.
