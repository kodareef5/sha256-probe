# Defect Fiber Count Probe — 2026-04-26

## Question

The local rank probe showed full 32-bit rank for the sr=61 defect map:

```text
D(W57,W58,W59) =
    (W2_sched60 - W1_sched60) - cascade_required_offset60
```

Full local rank does not rule out nonlinear structure. This probe counts
exact fibers of `D=0` at reduced widths:

```text
for fixed W57: count {(W58,W59) : D(W57,W58,W59)=0}
```

If the map is uniformly random, expected hits per `W57` are `2^N`.

## Exact aggregate counts

| N | bit | fill | W57 checked | avg hits / W57 | enrichment | Fano | max hits | max enrichment | max W57 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 8  | 7 | `0xff`  | 256  | 257.633 | 1.006 | 2.203 | 339  | 1.324 | `0x27` |
| 8  | 6 | `0xff`  | 256  | 256.715 | 1.003 | 2.080 | 333  | 1.301 | `0xfb` |
| 10 | 9 | `0x3ff` | 1024 | 1020.631 | 0.997 | 23.324 | 1439 | 1.405 | `0x50` |
| 10 | 1 | `0x3ff` | 1024 | 1024.146 | 1.000 | 4.785 | 1301 | 1.271 | `0x119` |
| 12 | 11 | `0xfff` | 4096 | 4091.935 | 0.999 | 34.169 | 6985 | 1.705 | `0x666` |
| 14 | 1 | `0x3fff` | 64 | 16395.906 | 1.001 | 60.289 | 19300 | 1.178 | `0x30` |

The aggregate map is very close to uniform at every measured width. That
supports the existing `2^-N` cascade-break model at the mean level.

The nonuniformity is in the chamber distribution: Fano factors are far above
1, and the best `W57` chambers have 1.3x-1.7x the expected fiber count.

## Nested fibers

Inside the best `W57` chamber, count hits per `W58`:

| N | W57 | total hits | best W58 | hits over W59 | enrichment vs chamber mean |
|---:|---:|---:|---:|---:|---:|
| 8  | `0x27`  | 339  | `0x0c`  | 6  | 4.53 |
| 10 | `0x50`  | 1439 | `0x099` | 14 | 9.96 |
| 12 | `0x666` | 6985 | `0x393` | 21 | 12.31 |

The nested result is more interesting than the aggregate. Some
`(W57,W58)` pairs have many `W59` completions even though the global
`D=0` rate is random.

The N=12 hit list for the best chamber:

```text
W57=0x666, W58=0x393
W59 hits =
0x369,
0x8bb,0x8c3,0x8d3,0x8da,0x8e2,
0x9bb,0x9c3,0x9d3,0x9da,0x9e2,
0xcbb,0xcc3,0xcca,0xcda,0xce2,
0xdbb,0xdc3,0xdca,0xdda,0xde2
```

This is not random-looking. The suffixes repeat across high-bit bands.
The standout `W57=0x666` is also structured. This points at carry-chamber
geometry rather than independent uniform sampling.

Top `W58` values inside the same N=12 `W57=0x666` chamber:

```text
0x393:21, 0x3b3:17, 0x793:16, 0x7b3:14,
0x6b3:13, 0x493:13, 0x293:12, 0x392:12,
0x7f3:12, 0x7d3:11, 0x88d:11, 0xbbe:11,
0x8f3:10, 0xd89:10, 0x093:10, 0x773:10
```

Again the suffix pattern is visible: `0x?93`, `0x?b3`, `0x?f3`, `0x?d3`
families dominate the top list.

## Boolean-gate degeneracy check

For the nested fat fibers, simple Ch/Maj equality-sheet metrics did not
explain the enrichment.

Examples:

- N=12 `W57=0x666,W58=0x393`: hit and all-sample averages are identical
  for `Ch` and `Maj(a)` invisibility; `Maj(b/c)` is only mildly enriched.
- N=10 and N=8 show similarly weak/no enrichment.

So the current signal is probably not the simple `f=g` / `b=c` Boolean
degeneracy surface. It is more likely a modular-add carry chamber.

This is a useful correction to the first-principles guess: the singular
object appears to live in the carry language induced by modular additions,
not in the raw Boolean selector surfaces of `Ch`/`Maj`.

## Carry signature check

For the same nested fat fibers, the carry masks of the modular additions
inside `cascade_required_offset60` are strongly more invariant on hits than
on all `W59` values.

The three masks are from:

```text
c0: carry mask of dh + dSigma1
c1: carry mask of (dh + dSigma1) + dCh
c2: carry mask of previous + dT2
```

| N | chamber | all carry invariant bits | hit carry invariant bits |
|---:|---|---:|---:|
| 8 | `W57=0x27,W58=0x0c` | `[0,0,8]` | `[2,4,8]` |
| 10 | `W57=0x50,W58=0x099` | `[0,2,10]` | `[6,7,10]` |
| 12 | `W57=0x666,W58=0x393` | `[0,0,12]` | `[10,8,12]` |

For N=12, hit carries satisfy:

```text
hit_carry_and = [0x347, 0xc22, 0x000]
hit_carry_or  = [0x757, 0xe3e, 0x000]
```

That is the first concrete mechanism signal: the fat fibers are not explained
by Ch/Maj selector equality, but they do sit inside constrained carry masks
for the arithmetic that computes the round-60 cascade requirement.

## Interpretation

This does not yet give a severe reduction at full N. The mean remains exactly
where the structural proof predicts.

But it does show the defect map has exploitable-looking nonlinear fibers:

- local rank: full,
- aggregate fiber count: uniform,
- chamber variance: overdispersed,
- nested completions: patterned and many-to-one.

The next useful target is a carry-chamber classifier for the fat
`(W57,W58)` fibers, not another CDCL run.

## Full-N periodic lift check

I also tested a naive lift: repeat the N=12 fat chamber language periodically
into 32-bit words and evaluate the actual N=32 defect on the representative
candidate list.

Result: best lifted defects were HW 6-10 across 18 candidates, always full
rank. That is not better than the random 2048-point local-rank probe, which
already found defects in the HW 4-9 range depending on candidate.

So the N=12 carry language does not transfer to N=32 by simple periodic
repetition. If it transfers at all, the embedding has to respect the 32-bit
rotation/carry geometry rather than repeat the 12-bit suffix grammar.

## Next

1. For reduced N, extract carry signatures at round 59 for fat and thin
   `(W57,W58)` fibers.
2. Learn which carry bits/suffixes predict high `W59` multiplicity.
3. If the predictor is stable across N=8/10/12, test whether it can select
   full-N `W57,W58` regions with elevated `D` low-HW or partial-zero rates.
