# M5 1B-trial deep descent — 2026-04-26

Companion to yale's `20260426_fulln_sparse_offset_probe.md`. While yale was
mapping local structure (radius-6 / radius-7 ridge enumeration, neighborhood
classification), the M5 ran a single 1,000,000,000-trial `surface61greedywalk`
from the M5-discovered HW7 round-61 base point. Wall: ~14 minutes on M5
with `-mcpu=apple-m4` + 10 OpenMP threads.

## Setup

Starting basin: M5 `idx=8 bit3_m33ec77ca_ff`, HW7 round-61 found at 100M
trials from yale's HW10 base.

```text
base point: W57=0xaf07f044, W58=0x55733d4f, W59=0x772319ec
  off58 = 0x00010002 (HW 2, sparse)
  off59 = 0x1a347b66
  defect60 = 0
  defect61 = 0x44045204 (HW 7)
  tail HW = 87
```

## Command

```bash
/tmp/singular_defect_rank surface61greedywalk \
  8 0xaf07f044 0x55733d4f 0x772319ec \
  1000000000 10 80 32
```

(1B trials, 10 threads, max_passes=80, max_flips=32. 14:14 wall.)

## Results

```text
trials                    : 1,000,000,000
exact60 hits              : 53,165,539  (5.3%)
changed exact60 hits      : 13,341,354
max exact distance        : 38

best_d61_hw               : 5  (was HW7 at base)
best_d61 point            : W58=0xdd73a9d7, W59=0x57046fad
best_d61 defect61         : 0x04240880

best_exact_tail_hw        : 68  (was 87 at base; yale's prior frontier was 70)
best_exact_tail point     : W58=0x464b2c4c, W59=0xef7b2fae
best_exact_tail defects   : 0,0,0,0,0xfa0735a3,0x15bfe278,0xc5ffbd08
```

## d61_hw histogram (exact `defect60=0` only)

```text
HW  5:  5,887,188   ← best D61 frontier (NEW)
HW  6:  4,822,245   ← previously not seen
HW  7: 42,421,551   ← original "floor" basin
HW  8:         45   ← previous M5 frontier (rare from this start)
HW  9:      2,992
HW 10:      5,172
HW 11..16: 26,123
HW 17:      2,696
HW 18..26: ~12,000
```

The histogram shows two distinct dense regions:
- **HW7 dense basin**: 42M hits (4.2% of trials), the local minimum we
  started from.
- **HW5/HW6 reachable region**: ~10.7M hits combined.

There's a sharp drop from HW7 to HW8 (only 45 hits) followed by spread
over HW9-HW17. The reach from HW7 down to HW5 went past the HW8 floor
yale and I established at 100M trials.

## Verified frontier

| objective | point | value | tail_hw |
|---|---|---:|---:|
| round-61 defect | `W57=0xaf07f044, W58=0xdd73a9d7, W59=0x57046fad` | **HW5** | 78 |
| checked tail | `W57=0xaf07f044, W58=0x464b2c4c, W59=0xef7b2fae` | tail_hw **HW68** | 68 |

Both verified via independent `tailpoint` runs.

The HW5 D61 point has `rank60=32`, `rank_pair=63`, `kernel_dim=32`,
`rank61_on_kernel=31` — same tangent signature as earlier frontier
points. Same sparse-off58 chamber (`off58=0x00010002`).

## Joint frontier across yale + M5

Combining yale's structural ridge work and M5's raw depth:

| value | source | comment |
|---|---|---|
| HW10 → HW8 → HW7 → **HW5** round-61 | mixed | M5 raw depth pushed past yale's HW7 ridge-repair |
| HW76 → HW74 → HW72 → HW70 → **HW68** tail | M5 1B run | new 8-bit tail improvement over yale's initial frontier |

Yale's complementary structural finding (radius-7 enumeration around HW7):
D60-HW7 ridge with D61=HW2. Cannot repair. M5's 1B walk reached D61=HW5
directly via the exact D60=0 surface, bypassing the ridge-repair pattern.

## What changed in the picture

- The "HW7 floor" yale and I both reached at smaller trial counts is **not
  structural**. Order-of-magnitude depth (1B vs 100M trials) reaches HW5.
- HW5 and HW6 are **dense** at 1B (millions of hits), not rare events.
  This means there's a multi-basin shelf around HW5 that the walker found.
- The sparse-off58 chamber `0x00010002` at `W57=0xaf07f044` (idx 8) supports
  D61 down to at least HW5. Whether HW4/HW3 exist is open.

## Next

- Walk from HW5 base at 1B trials → look for HW4.
- Walk from HW68 tail base at 1B trials → look for tail < 68.
- Possibly: pool walk over HW5, HW6, HW68 basins.
- Walk same parameters from `idx=0` and `idx=3` HW8 bases — see if those
  cands also descend to HW5.

## Reproduce

```bash
gcc -O3 -mcpu=apple-m4 -mtune=apple-m4 -Xclang -fopenmp \
    -I/opt/homebrew/opt/libomp/include -I. \
    -L/opt/homebrew/opt/libomp/lib -lomp \
    headline_hunt/bets/singular_chamber_rank/tools/singular_defect_rank.c \
    lib/sha256.c -lm \
    -o /tmp/singular_defect_rank

# 1B-trial deep walk (~14 min on M5, 10 threads):
/tmp/singular_defect_rank surface61greedywalk \
    8 0xaf07f044 0x55733d4f 0x772319ec \
    1000000000 10 80 32

# Verify HW5 frontier point:
/tmp/singular_defect_rank tailpoint 8 0xaf07f044 0xdd73a9d7 0x57046fad

# Verify HW68 tail frontier point:
/tmp/singular_defect_rank tailpoint 8 0xaf07f044 0x464b2c4c 0xef7b2fae
```
