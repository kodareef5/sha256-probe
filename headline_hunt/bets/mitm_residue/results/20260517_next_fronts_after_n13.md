# Next Fronts After Full N=13 Sweep

The reduced-width N=13 surface is exhausted for the current three-free-word
`D60=0` interface. The tail frontier remains HW7, and no post-61% coverage
improved it. The next work should stop treating N=13 broad coverage as the main
source of new information and move to these fronts.

## Front 1: N=14 staged sampling

N=14 is operational at the same per-window cost by using `prefix_limit=32768`.
The first contiguous N=14 stage covered `112` windows:

```text
prefixes covered = 3,670,016 / 268,435,456 = 1.37%
triples covered  = 60,129,542,144
best tail HW     = 16 at sample_start 458752
best r61 HW      = 10 at sample_start 2097152
```

The r61-HW10 witness is not a joint lead; its actual `r61_tail` is HW36. The
best tail row is:

```text
sample_start = 458752
tail HW      = 16
tail r61 HW  = 17
best r61 HW  = 13
W1[57..59]   = 11ca,1856,0ef7
W2[57..59]   = 10d7,36a3,3a86
```

A strided N=14 registry pass sampled `32` windows across the whole N=14 surface
with `refine_seed_cap=16`:

```text
prefixes covered = 1,048,576 / 268,435,456 = 0.39%
triples covered  = 17,179,869,184
best tail HW     = 16 at sample_start 54001664
best r61 HW      = 11 at sample_start 54001664
registry entries = 512 tail + 512 r61
```

This repeats HW16 away from the low contiguous window band. It does not yet make
N=14 look better than N=13, but it is now a live staged sampling front rather
than a smoke test.

## Front 2: Rich witness registries

The old batch runner effectively used `registry_cap=1`, which is enough for
frontier tracking but bad for recombination. `run_scan_batch.py` now exposes:

```text
--refine-seed-cap
--stride
```

Use `--refine-seed-cap 16` or `64` for exploration batches. The logs then retain
multiple tail and r61 witnesses per window, which `analyze_scan_structure.py`
can mine globally.

Recommended next CPU block:

```text
N=14, prefix_limit=32768, stride=128 or 256, windows=64..256,
refine_seed_cap=16 initially, 64 for promising bands.
```

Promotion criteria:

```text
tail <= 13: run focused 500M prefix-surface validation.
tail <= 16 with r61 <= 12: rerun same window with refine_seed_cap=64.
r61 <= 9: rerun same window with refine_seed_cap=64 even if tail is weak.
```

## Front 3: Structure mining, not D60-density chasing

`analyze_scan_structure.py` parses scan logs and computes D60/fiber/bucket
signals plus real registry rows. On the logged N=13 rows:

```text
logged windows analyzed = 922
N=13 total with prior   = 1024 windows = 100%

correlation vs best_tail:
best_r61             -0.0232
tail_r61             +0.2541
d0                   -0.0245
d0_prefixes          -0.0120
max_fiber            -0.0433
largest_bucket_count +0.0394
```

Interpretation: raw D60 density, D60-prefix count, max fiber, and largest bucket
mass are not useful selectors for low-tail windows. The only visible signal is
that the r61 score of the same tail witness has a modest relationship to final
tail. That argues against choosing windows by D60 geometry alone.

## Front 4: Correct r61 accounting

The old summarizer printed the window's `best_tail` beside the best-r61 witness,
which made some r61-only rows look less bad than they were. It now reports
`r61_tail` separately when the log registry is available.

Corrected N=13 r61-HW7 interpretation:

```text
best true r61-HW7 tail = HW16 at sample_start 54853632
latest r61-HW7 repeat  = sample_start 65142784 with r61_tail HW27
```

So r61-HW7 alone is not a closure proxy. The useful joint row remains the HW7
tail witness at `sample_start=24641536` with `tail r61 HW=9`.

## Front 5: Change the interface if N=14 stays random

If another few hundred N=14 registry windows stay around tail HW16+ with no
r61<=9 joint structure, the next higher-leverage build is not a larger scan. It
is changing the interface:

```text
D60=0 exact       -> D60 low-HW repairable interface
W57..W59 free     -> wider W56..W60 or W57..W61 shaping
one-row minima    -> cross-window registry recombination by gh60/r61/carry keys
```

The full N=13 result says the current three-free-word exact-D60 surface is too
thin. The next algebraic work should try to expose one more repair degree of
freedom, then reuse the same scan/registry machinery.
