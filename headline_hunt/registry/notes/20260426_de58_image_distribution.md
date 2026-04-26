# de58 image-size distribution across 55 N=32 candidates
**2026-04-26 04:10 EDT** — analysis of session-expanded registry.

## de58_size log-binned histogram (n=55)

| log2(de58_size) | range | candidates |
|---|---|---|
| 8 | 256-511 | 1 (bit=19 m=0x51ca0b34, fill=0x55) |
| 10 | 1024-2047 | 1 (bit=25 m=0xa2f498b1, fill=0xff) |
| 11 | 2048-4095 | 1 (bit=4  m=0x39a03c2d, fill=0xff) |
| 12 | 4096-8191 | 2 (bit=31 m=0x9cfea9ce + bit=25 m=0x09990bd2) |
| 13 | 8192-16383 | 11 |
| 14 | 16384-32767 | 8 |
| 15 | 32768-65535 | 11 |
| 16 | 65536-131071 | 20 |

The distribution is approximately log-uniform with mode at 2^16-2^17.
**bit=19 m=0x51ca0b34 has de58_size=256 — a 2^9 outlier** (~512x smaller
than median).

## Per-bit median de58_size

| bit | n  | min   | median | max    |
|----:|---:|------:|-------:|-------:|
|  0  | 4  | 32178 |  56709 | 115885 |
|  1  | 1  | 32175 |  32175 |  32175 |
|  2  | 3  |  8192 |   8192 |  56645 |
|  3  | 2  | 82835 |  82943 |  82943 |
|  4  | 2  |  2048 |  32152 |  32152 |
|  6  | 6  | 32197 |  82854 | 123067 |
| 10  | 7  | 16377 |  16381 |  82884 |
| 11  | 2  |  8192 |  16376 |  16376 |
| 13  | 7  |  8192 |  82762 | 123264 |
| 14  | 3  | 41496 |  61629 |  63510 |
| 17  | 3  | 82886 | 115967 | 115971 |
| 18  | 5  | 32171 | 102922 | 130086 |
| 19  | 1  |   256 |    256 |    256 |
| 25  | 3  |  1024 |   4096 |  16380 |
| 31  | 6  |  4096 |  56696 | 130049 |

Per-bit median ranges 256 (bit=19) to 115967 (bit=17). Bit-position
strongly correlates with image-size median, but no clean rotation-
alignment grouping (e.g., σ0-aligned bit=10 has median 16381, not
markedly smaller than non-aligned bit=14 at 61629).

## hardlock_bits distribution

Approximately Gaussian with mean ~8, tail to 16:
| hl_bits | count |
|---|---|
| 1 | 1 |
| 3 | 3 |
| 4 | 3 |
| 5 | 8 |
| 6 | 7 |
| 7 | 5 |
| 8 | 4 |
| 9 | 5 |
| 10 | 3 |
| 11 | 5 |
| 12 | 3 |
| 13 | 4 |
| 14 | 2 |
| 15 | 1 |
| 16 | 1 (bit=11 m=0x56076c68 fill=0x55) |

Median hardlock_bits = 8.

## Implication for SAT search (constrained by predictor closure)

The 20260425 validation matrix established that de58_size and
hard_bit_total_lb predictors are search-irrelevant (Spearman ρ ≤ 0
across all tested cells in both kissat and cadical, both budgets, both
seeds). So even the 256-image bit=19 candidate is **not** structurally
privileged for solver runtime.

This re-confirms what was found: the SAT solver does not benefit from
narrow image structure. If anything, the opposite: more constraints
may produce more conflict-driven backtracking.

## What this distribution does NOT predict

- Solver runtime (closed by validation matrix).
- SAT/UNSAT verdict (no candidate has produced SAT at sr=61).
- Which candidate is "right" for a backward-construction approach.

## What it MAY suggest (untested)

The 2^9-outlier bit=19 candidate's image size could mean some structural
phenomenon at boundary bit positions. **Untested**: whether this image-
size pattern persists at N>32 or is N=32-specific. **Not in scope** for
this note.

## Status: EVIDENCE-level analysis. Closes nothing; documents distribution.
