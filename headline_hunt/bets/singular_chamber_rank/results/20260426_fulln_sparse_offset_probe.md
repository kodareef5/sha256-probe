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

## Exact sr=61 compatibility

Allowing W58 and W59 to move together while holding the sparse `W57` chamber
fixed found an exact `D=0` point.

```text
candidate idx 3: bit20_m294e1ea8_ff
W57 = 0xe28da599
W58 = 0xa3110717
W59 = 0x1afa1270

off57 = 0xa6a5a05c
off58 = 0x00000802
off59 = 0xf447ff7e
off60 = 0x737574d8

W1[60] = 0xb7d9b05f
W2[60] = 0x2b4f2537
W2[60] - W1[60] = 0x737574d8
defect60 = 0
```

The trace confirms:

```text
sched_offset60 = 0x737574d8
req_offset60   = 0x737574d8
```

This is the barrier event this bet was targeting: the schedule-derived round
60 word agrees with the cascade-required round 60 word.

## Tail check

This is not a full compression collision. Running rounds 57..63 from the
exact sr=61-compatible point gives final tail state difference HW 95.

The tail defects are:

```text
round 57: 0x00000000
round 58: 0x00000000
round 59: 0x00000000
round 60: 0x00000000
round 61: 0x47f8a46f
round 62: 0xd719bdfa
round 63: 0xdde9f221
```

So the current result breaks the sr=61 compatibility barrier but lands at the
next schedule/cascade wall. The next problem is extending the corridor beyond
round 60, not proving a final collision from this point.

## Additional exact chamber

The same fixed-W57 descent found another exact sr=61-compatible point in a
different sparse chamber:

```text
candidate idx 8: bit3_m33ec77ca_ff
W57 = 0xaf07f044
W58 = 0x9d3ceba8
W59 = 0xc3da20d1

off58 = 0x00010002
off60 = 0xee2b15a3
defect60 = 0
```

Tail defects:

```text
round 57: 0x00000000
round 58: 0x00000000
round 59: 0x00000000
round 60: 0x00000000
round 61: 0xc1bf6e60
round 62: 0x4d9baa10
round 63: 0x3a098d96
tail HW: 93
```

In the same 65,536-start pass:

```text
idx 3 exact hits: 1, best round-61 defect HW: 18
idx 8 exact hits: 2, best round-61 defect HW: 17
idx 0 exact hits: 0, best defect60: 0x00000001
```

This suggests exact sr61 compatibility is not a single lucky point. It is a
reachable class of sparse-offset chambers, while round 61 is the next real
barrier.

A larger 524,288-start selection pass found exact sr61 hits in all three
tested sparse chambers and improved the next-wall defect:

| idx | exact hits | best round-61 defect | HW | exact point |
|---:|---:|---:|---:|---|
| 0 | 4 | `0x754a07d8` | 15 | `W58=0x6a2c226f,W59=0xc08397e6` |
| 3 | 6 | `0x4aa48446` | 11 | `W58=0x5e06f0a7,W59=0x28859825` |
| 8 | 5 | `0x143f400e` | 12 | `W58=0x12df1f0f,W59=0x2734feeb` |

The best final tail HW among these checked points is currently the idx 8
point:

```text
idx 8, W57=0xaf07f044, W58=0x12df1f0f, W59=0x2734feeb
tail defects:
57..60 = 0
61 = 0x143f400e
62 = 0xdcd5f3ee
63 = 0x98bf2413
tail HW = 82
```

## Round-61 manifold probes

The next wall is not a fresh uniform 32-bit obstruction. At exact
`defect60=0` points, the local derivative of `(defect60, defect61)` with
respect to `(W58,W59)` is usually rank 63, and the restriction of `defect61`
to the `defect60` tangent kernel has rank 31.

Example at the best earlier idx 3 next-wall point:

```text
idx 3, W57=0xe28da599, W58=0x5e06f0a7, W59=0x28859825
defect60 = 0
defect61 = 0x4aa48446 (HW 11)
rank60 = 32
rank_pair(defect60,defect61) = 63
dim ker(d defect60) = 32
rank defect61 on that kernel = 31
```

So the exact `defect60=0` surface still has substantial tangent freedom, but
one Boolean obstruction bit remains visible at round 61 in these chambers.

The nonlinear exact surface is much thinner than the tangent space suggests.
Enumerating radius <= 6 combinations in the local `defect60` kernel around
the HW11 idx 3 point checked 1,149,017 tangent-kernel moves; only two
preserved exact `defect60=0`, and none improved `defect61`.

Natural bit neighborhoods are similarly sparse. Radius <= 5 in `(W58,W59)`
around the best exact points checks 8,303,633 points per center. It found one
additional idx 0 exact point improving that chamber's round-61 defect from
HW15 to HW11:

```text
idx 0, W57=0x370fef5f, W58=0x6a2c226f, W59=0xc08413e6
defect61 = 0xd0460515 (HW 11)
tail HW = 105
```

This improves the chamber's next-wall defect but not the final tail.

## Two-wall objective

A direct hill-climber scored candidates by:

```text
score = 64 * HW(defect60) + HW(defect61)
```

This can find exact `defect60=0` points, but it often parks at one-bit
`defect60` near misses instead of entering the exact corridor. A 524,288-start
pass found no point below HW11 for `defect61`, but did find another HW11 point
in idx 8:

```text
idx 8, W57=0xaf07f044, W58=0xe98d86d0, W59=0xc778e588
defect60 = 0
defect61 = 0x015aa22a (HW 11)
tail HW = 91
```

This is not better than the previous best tail, but it is a cleaner
low-valued round-61 miss and shows HW11 is reproducible across sparse
chambers and objectives.

## Sparse off59 check

The round-61 schedule side has the analogous finite-difference form:

```text
S61(W59) = C + sigma1(W59 + off59) - sigma1(W59)
```

Sparse `off59` chambers are reachable after fixing sparse `off58`:

| idx | W57 | W58 | off59 | HW |
|---:|---:|---:|---:|---:|
| 8 | `0xaf07f044` | `0xc62feb96` | `0x00000000` | 0 |
| 3 | `0xe28da599` | `0xa59469ce` | `0x20000000` | 1 |
| 0 | `0x370fef5f` | `0x0e4363c9` | `0x00000300` | 2 |

But sparse `off59` alone is not sufficient. Fixed-W58 descent found exact
`defect60=0` only for the idx 0 `off59=0x00000300` sheet:

```text
idx 0, W57=0x370fef5f, W58=0x0e4363c9, W59=0xfe337af3
off58 = 0x00000021
off59 = 0x00000300
defect60 = 0
defect61 = 0x3347fca2 (HW 17)
tail HW = 89
```

At this point the local pair rank is 64 and `defect61` has full rank on the
`defect60` kernel, so the linearized system can solve both walls. The full
Newton step still fails in the real arithmetic map because it jumps into a
different carry chamber and destroys `defect60`.

## Carry-chamber jump

Tracing the failed Newton step makes the carry transition concrete. At exact
`defect60=0` points, the state lanes synchronized by the cascade force the
round-61 required-offset parts:

```text
dSigma1(e) = 0
dT2(a,b,c) = 0
```

So the next required offset is reduced to:

```text
required61 = dh + dCh
```

The remaining difficulty is not an unconstrained four-term SHA-256 round. It
is a two-term arithmetic/carry problem after the cascade has synchronized
`a,b,c,e` at the round-61 boundary.

At the sparse-`off59` idx 0 point:

```text
idx 0, W57=0x370fef5f, W58=0x0e4363c9, W59=0xfe337af3
defect60 = 0
defect61 = 0x3347fca2
pair rank = 64
Newton delta HW = 29
linearized result = (0,0)
actual result     = (0x8049d05d, 0x277c5ddf)
```

The jump changes the carry chamber instead of solving the real arithmetic
system. At round 60, the `dSigma1` and `dCh` parts change by HW 13 and 14,
and the two active carry masks change by HW 14 and 18. At round 61, the
source had only the `dh+dCh` carry active, while the jump turns on all three
carry additions:

```text
round61 source parts:
dh=0xefef3e30, dSigma1=0, dCh=0x57388593, dT2=0

round61 jump parts:
dh=0xefef3e30, dSigma1=0x83a8bdd5, dCh=0x56ca3e8f, dT2=0x4b6a385a

round61 carry-mask XOR HW:
19, 15, 11
```

The same pattern appears at the earlier idx 3 HW11 point: the linearized
delta predicts `(0,0)`, but the actual move lands at
`(0xa69c6528, 0x7f97bd8f)` and turns on large round-61 `dSigma1`/`dT2`
parts.

This reframes the next problem: do not take high-Hamming Newton jumps across
carry chambers. Instead, search for moves that preserve the round-61 lane
equalities and tune the reduced `dh+dCh` equation.

## Fixed-W58 sparse-off59 test

A fixed-`W58` two-wall hill-climber was added to test whether sparse `off59`
sheets can directly produce better exact round-60 launch points.

On the three sparse `off59` sheets above, 65,536-start fixed-W58 passes found
no exact `defect60=0` point under the two-wall score. They did find low
near-misses:

| idx | W58 | off59 | best defect60 | HW60 | best defect61 | HW61 |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | `0x0e4363c9` | `0x00000300` | `0x00004000` | 1 | `0x1490709b` | 12 |
| 8 | `0xc62feb96` | `0x00000000` | `0x20000000` | 1 | `0x5600853b` | 12 |
| 3 | `0xa59469ce` | `0x20000000` | `0x00408000` | 2 | `0x4a9a0c84` | 11 |

So sparse `off59` is useful but insufficient by itself. The exact `defect60`
surface remains the gate; once crossed, round 61 is best viewed as a reduced
carry equation constrained by synchronized state lanes.

## Exact-surface projection walk

To avoid high-Hamming two-wall Newton jumps, a surface walk was added:

1. start from an exact `defect60=0` point,
2. perturb `(W58,W59)` by a bounded number of bit flips,
3. project back to `defect60=0` using the old one-wall Newton repair,
4. score only the repaired point's `defect61`.

This is a better question than random descent: can we walk the exact
round-60 surface while preserving the synchronized lane geometry?

The first answer is negative but informative. Around the HW11 idx 8 point,
32,768 trials with up to 12 perturbation flips produced 1,493 exact
`defect60=0` repairs, but every successful repair returned to the original
point:

```text
idx 8 base: W58=0xe98d86d0, W59=0xc778e588
defect61 = 0x015aa22a (HW 11)
exact60 repairs = 1,493 / 32,768
changed exact repairs = 0
max exact distance from base = 0
```

The same pattern held for the other HW11 centers in smaller and larger
passes: the one-wall Newton projection has strong local attractors. It is not
currently a surface-walk operator.

As a control, the sparse-`off59` idx 0 exact point at HW17 also projected
back to its own HW17 basin:

```text
idx 0 base: W58=0x0e4363c9, W59=0xfe337af3
defect61 = 0x3347fca2 (HW 17)
exact60 repairs = 2,991 / 65,536
d61 HW histogram: all 17
```

So the exact round-60 surface appears as separated Newton-attractor basins
under these local perturb/project moves. To move between basins, the next
operator likely has to preserve selected carry/lane invariants explicitly
rather than relying on unconstrained defect60 Newton repair.

Starting from arbitrary random `(W58,W59)` values in the same sparse `W57`
chambers and projecting with one-wall Boolean Newton was even harsher:

```text
surface61sample, 65,536 random starts per sparse W57 chamber:
idx 0 successes: 0
idx 3 successes: 0
idx 8 successes: 0
```

So Newton is not a global projector onto the exact surface. It is a local
attractor map around already-known exact points.

## Greedy Surface Walk

A more carry-safe projector was then tested:

1. perturb an exact point,
2. repair only `defect60` by greedy one-bit descent in the real arithmetic
   map,
3. score the repaired exact point's `defect61`.

This does cross exact-point basins, unlike Newton projection. Around the HW11
idx 3 point, 65,536 local greedy walks produced 190 changed exact points; the
best changed basin had HW12 at round 61:

```text
idx 3 changed exact:
W58 = 0x5e0770a7
W59 = 0x28c59a35
defect61 = 0x7c428416 (HW 12)
tail HW = 103
```

Around the HW11 idx 8 point, changed exact basins were rarer but one gave a
better checked tail despite a worse round-61 miss:

```text
idx 8 changed exact:
W58 = 0xe98d8ed0
W59 = 0xc77ced69
defect61 = 0xfb82a228 (HW 14)
tail HW = 88
```

The sparse-`off59` idx 0 control moved from HW17 to HW14:

```text
idx 0 changed exact:
W58 = 0x0e4363cd
W59 = 0x7a267a31
defect61 = 0xba0a9983 (HW 14)
tail HW = 100
```

Wider greedy walks with 262,144 trials and up to 24 perturbation flips around
the HW11 centers did not find HW10. Current evidence: greedy repair can cross
basins, but the known HW11 basins remain local minima for the round-61
defect.

Tracking the final 57..63 tail rather than only `defect61` found a better
tail basin. From the previous idx 8 tail-HW82 point:

```text
base: W58=0x12df1f0f, W59=0x2734feeb
tail HW = 82

changed exact:
W58 = 0x73db5f4f
W59 = 0xa7679a23
defect61 = 0xf2f94011 (HW 14)
tail defects = 0,0,0,0,0xf2f94011,0xeb952ff1,0xa1688000
tail HW = 76
```

That tail-HW76 basin then led to the first HW10 round-61 defect found in this
line:

```text
idx 8, W57=0xaf07f044, W58=0x73db5ecf, W59=0xb767da21
defect60 = 0
defect61 = 0x0259b011 (HW 10)
tail defects = 0,0,0,0,0x0259b011,0x75bd6dbf,0x97dae53f
tail HW = 91
```

The HW10 basin is stable under another 262,144-trial greedy walk; no HW9 was
found, and the best changed basin from it had HW13. This shows the previous
HW11 floor was not structural. Basin crossing can reduce round 61 further,
but the best round-61 basin and the best checked-tail basin are currently
different.

A larger 1,048,576-trial frontier pass with up to 32 perturbation flips tested
the linked HW10 and tail-HW76 basins directly. It found no HW9 and no checked
tail below 76. The two basins map into each other:

```text
HW10 basin -> best changed round61: HW11, best tail: HW76
HW76 basin -> best changed round61: HW10, best changed tail: HW79
```

So the current frontier is a two-basin pair:

| objective | point | value |
|---|---|---:|
| round-61 defect | `W58=0x73db5ecf,W59=0xb767da21` | HW10 |
| checked 57..63 tail | `W58=0x73db5f4f,W59=0xa7679a23` | HW76 |

The HW10 point still shows the same carry-jump failure mode. Boolean Newton
finds a rank-62 correction of HW28 that solves the linearized pair
`(defect60, defect61)`, but the true arithmetic lands at:

```text
actual after Newton delta:
defect60 = 0x84c306f9
defect61 = 0xaaed9cbd
```

So even after lowering the next wall to HW10, high-Hamming linear corrections
still leave the carry chamber.

## Deep frontier update

A follow-up deep greedy run from the HW10 idx 8 basin pushed the round-61
frontier again:

```text
idx 8, W57=0xaf07f044, W58=0x7fc3124f, W59=0xbf245aa1
defect60 = 0
defect61 = 0x42818308 (HW 8)
tail defects = 0,0,0,0,0x42818308,0x95989667,0x9a99ef91
tail HW = 92
off59 = 0x6474ce42 (HW 14)
```

The same search stream also improved the checked tail frontier:

```text
idx 8, W57=0xaf07f044, W58=0x1cbb355e, W59=0xad34d2a3
defect60 = 0
defect61 = 0xffd3e7fa (HW 25)
tail defects = 0,0,0,0,0xffd3e7fa,0x469fed24,0xf787dbea
tail HW = 74
off59 = 0xab66b434 (HW 16)
```

Using the low-D60 ridge states around that point as seeds, the side-objective
repair walk found a better representative of the same tail-HW74 frontier:

```text
idx 8, W57=0xaf07f044, W58=0x5cbb3d5e, W59=0x29a4dea3
defect60 = 0
defect61 = 0xc004d07e (HW 12)
tail defects = 0,0,0,0,0xc004d07e,0x8a9168f0,0x63fcc7ec
tail HW = 74
off59 = 0x2976ac72 (HW 16)
```

This does not lower the checked tail below 74, but it dominates the first
tail-HW74 representative on the round-61 objective.

The HW8 point has the same tangent signature as the earlier frontier:

```text
rank60 = 32
kernel_dim = 32
rank_pair = 63
rank61_on_kernel = 31
pair_solvable = 0
```

The tail-HW74 point also has `rank_pair=63`, but the linear correction is again
too disruptive: the rank-63 solve uses a HW31 delta and lands at
`defect60=0x2a5d0425`, `defect61=0x4e02bc31`.

Local exact-neighborhood enumeration shows the new points are sparse basins,
not broad sheets:

| base | radius | exact `defect60=0` points | best exact neighbor |
|---|---:|---:|---|
| HW8 | 5 | 2 | one-bit `W59=0xbf245ea1`, `defect61` HW17, tail HW88 |
| first tail HW74 | 5 | 1 | isolated |
| improved tail HW74 | 5 | 3 | base remains best, `defect61` HW12, tail HW74 |

Tracking non-exact low-D60 ridges inside those same radius-5 balls found a
consistent trade: as a few `defect60` bits are allowed to miss, `defect61`
can drop below the exact frontier. Around the HW8 point:

```text
best D60 HW5 ridge:
W58=0x7fe3124f, W59=0x9f255a21
defect60 = 0x84088004
defect61 = 0x4128c008 (HW 7)
```

Around the improved tail-HW74 point:

```text
best D60 HW5 ridge:
W58=0x5cbb3d5e, W59=0x29a51e23
defect60 = 0x2000c0a0
defect61 = 0x08430208 (HW 6)
```

However, one-wall Newton fails from both ridge states, and greedy
side-objective repair returns to the exact HW8 or tail-HW74 basins rather
than preserving the D61 gain.

Affine bridge checks sharpen that picture. The tail-HW74 to HW8 XOR bridge has
HW20. Enumerating every bridge subset plus every one-bit excursion outside the
bridge checked 47,185,920 points and found only three exact points: the two
endpoints and the one-bit HW8 neighbor. The best non-exact bridge point still
missed `defect60` by one bit:

```text
W58=0x1cbb355e, W59=0xad24d283
defect60 = 0x08000000 (HW 1)
defect61 HW = 15
```

The old HW10 to new HW8 bridge behaves similarly. Its bridge has HW14; checking
20,905,984 bridge-plus-two-extra points again found only the two endpoints plus
the HW8 one-bit neighbor. The best non-exact bridge point was:

```text
W58=0x73db5ecf, W59=0x3767da31
defect60 = 0x04000000 (HW 1)
defect61 HW = 13
```

A pooled six-seed frontier walk over the HW8, tail-HW74, HW8-neighbor, HW10,
tail-HW76, and HW11 basins did not improve either frontier in 262,144 trials.
It did find a dominated changed basin:

```text
W58=0x7fc3824f, W59=0xbf541be3
defect61 = 0x60714614 (HW 11)
tail HW = 85
```

Extending exact/ridge enumeration to radius 6 changed the picture again. The
HW8 point still had no better exact neighbor in 83,278,001 checked states, but
the low-D60 ridge improved:

```text
around HW8, best D60 HW6 ridge:
W58=0x6f831247, W59=0xbf047ab1
defect60 = 0xc2002024
defect61 = 0x18002801 (HW 5)
```

Greedy repair from that ridge found a new exact round-61 frontier:

```text
idx 8, W57=0xaf07f044, W58=0x478a938a, W59=0x1f833295
defect60 = 0
defect61 = 0x04200874 (HW 7)
tail defects = 0,0,0,0,0x04200874,0x5ee5771e,0xcc3500b6
tail HW = 85
off59 = 0x7ae6e91d (HW 19)
```

The HW7 point has `rank_pair=64`, but the full Newton correction is still a
carry jump: the linear solve uses a HW23 delta and lands at
`defect60=0xbabe756f`, `defect61=0xd19b157f`.

Radius-6 enumeration around the HW7 point found eight exact `defect60=0`
points, but no exact D61 below HW7. It did expose a lower non-exact ridge:

```text
around HW7, best D60 HW6 ridge:
W58=0x478a8182, W59=0x1f8b1215
defect60 = 0x10438040
defect61 = 0x21204000 (HW 4)
```

Repairing that ridge did not lower the round-61 defect, but it found a new
checked-tail frontier:

```text
idx 8, W57=0xaf07f044, W58=0x65aa818a, W59=0x31103285
defect60 = 0
defect61 = 0x05b0702c (HW 11)
tail defects = 0,0,0,0,0x05b0702c,0xb9d4141e,0x00111e04
tail HW = 70
off59 = 0xbb36e035 (HW 17)
```

The tail-HW70 point's radius-6 neighborhood found six exact points, no lower
tail, and a best non-exact ridge at D60 HW5 / D61 HW5. Repairing that ridge
returned to known exact basins.

The next shell around the HW7 point was also checked. Radius 7 enumerated
704,494,193 points:

```text
exact defect60 points: 16
exact defect61 points: 0
best exact defect61: HW7 (the base point)
best exact tail: HW79
```

The low-D60 ridge continued to improve in the non-exact layer:

```text
around HW7, best D60 HW7 ridge:
W58=0x569a93da, W59=0x1f813291
defect60 = 0x88400a30
defect61 = 0x00020040 (HW 2)
```

But this is still not a smooth path to an exact point. One-wall Newton from
that ridge diverges to a HW19 `defect60`, and greedy/side-objective repair
returns to the known HW7 basin or the one-bit HW8/tail81 neighbor. The radius-7
result makes the next obstruction sharper: there are very low-D61 shelves
nearby, but repairing seven D60 carry bits without losing the D61 gain remains
the wall.

## M5 deep descent and ridge repair

The companion M5 worker then ran a 1,000,000,000-trial greedy walk from an
independent HW7 point in the same idx 8 sparse-`off58` chamber. That depth
moved both frontiers:

```text
round-61 frontier:
W58 = 0xdd73a9d7
W59 = 0x57046fad
defect61 = 0x04240880 (HW 5)
tail HW = 78

checked-tail frontier:
W58 = 0x464b2c4c
W59 = 0xef7b2fae
tail defects = 0,0,0,0,0xfa0735a3,0x15bfe278,0xc5ffbd08
tail HW = 68
```

Both were verified locally with `tailpoint`. The HW5 point has the now-familiar
rank profile:

```text
rank60 = 32
kernel_dim = 32
rank_pair = 63
rank61_on_kernel = 31
```

Radius-6 enumeration around the HW5 point found only two exact `defect60=0`
points and no exact HW4, but it did expose another low-D61 shelf:

```text
W58=0xddf3a9d3, W59=0x76046f0d
defect60 = 0x64021108 (HW 7)
defect61 = 0x10200020 (HW 3)
```

A new weighted ridge walker was added to preserve low D61 while still reducing
D60. From the earlier radius-7 D60-HW7/D61-HW2 shelf it found an exact HW6
point:

```text
W58=0x561b939a, W59=0x4db054d5
defect60 = 0
defect61 = 0x01020486 (HW 6)
tail HW = 79
```

From the HW5-local D60-HW7/D61-HW3 shelf, the same ridge walker returned to
the exact HW5 point rather than finding HW4. So HW5 is now the verified exact
frontier, while D60-low shelves below HW5 remain visible nearby.

Current frontier:

| objective | point | value |
|---|---|---:|
| round-61 defect | `W58=0xdd73a9d7,W59=0x57046fad` | HW5 |
| checked 57..63 tail | `W58=0x464b2c4c,W59=0xef7b2fae` | HW68 |

The conclusion changed quantitatively, not qualitatively: neither the HW10,
HW8, nor HW7 floor was structural, but the exact `defect60=0` surface is still
fractured into thin carry-linked basins. The productive pattern is now a
two-track loop: deep greedy walking finds new exact basins, then ridge
enumeration and weighted ridge repair explain and locally extend the shelves
around them.

## Kernel-linear one-bit targets

The rank-31 kernel result suggests a tempting linear strategy: stay inside the
`defect60` tangent kernel and correct `defect61` down to a single remaining
bit. For a codimension-one image, one of those 32 one-bit residual targets
should be linearly reachable whenever full zero is not.

The linear algebra works, but the arithmetic move is still too disruptive.
At the HW11 idx 8 point:

```text
rank60 = 32
dim ker(d defect60) = 32
rank defect61 on kernel = 31
solvable one-bit residual targets = 16
best nonzero tangent delta HW = 27
linear residual target = 0x10000000
actual after move:
  defect60 = 0x2b938360
  defect61 = 0x6bb5b8d6
```

At the HW11 idx 3 point, the best nonzero kernel-linear correction similarly
uses a HW32 delta and lands at:

```text
defect60 = 0x50244c0e
defect61 = 0x398a090b
```

So even the gentler "leave one bit unsolved" tangent move crosses out of the
exact carry chamber. The missing object is not a linear correction; it is a
low-disruption representative of a correction, or a different coordinate
system where the carry chamber is part of the state.

## Interpretation

The full-N picture is now sharper:

1. The schedule side can be forced into a severe finite-difference collapse
   by steering `off58` sparse.
2. Sparse `off59` by itself does not collapse the round-required side.
3. The exact `defect60=0` surface has useful tangent freedom for round 61,
   usually losing only one Boolean dimension, but the exact nonlinear basin is
   thin.
4. The next obstruction is a nonlocal carry transition: Boolean Newton can
   predict a solving move, but the required high-Hamming delta crosses into a
   different arithmetic chamber.

This is not yet a collision. It is a reproducible full-N mechanism that first
gets the true sr=61 defect from 32 random-looking bits down to 1 bit, then to
zero when W58 and W59 are allowed to move together inside the sparse `off58`
chamber.

## Next

The next useful direction is not larger random sampling. It is to model the
final carry transition around the HW1 point:

- characterize the exact `D=0` basin, not just the near misses,
- write the analogous defect map for round 61,
- test whether sparse-offset steering can also reduce the round-61 defect,
- keep the proof boundary clear: sr=61 compatibility is solved here, final
  compression collision is not.
