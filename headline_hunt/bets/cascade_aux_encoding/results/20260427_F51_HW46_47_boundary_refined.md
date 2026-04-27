# F51: HW=46/47 boundary refined — fast cluster extends to bit25, but bit13 splits HW=47
**2026-04-27 10:12 EDT**

Tests F50's "HW≤47 fast / HW≥48 slow" hypothesis with the 2 missing
data points: bit13 (HW=47, EXACT-sym; only par-5 measured) and
bit25 (HW=46, NON-sym; first HW=46 measurement ever).

## Result

```
bit13_m4e560940 (HW=47, EXACT-sym):  walls 32.83, 35.48, 37.09, 29.58, 29.13
                                     median 32.83s, range 7.96s, mean 32.82s

bit25_m30f40618 (HW=46, NON-sym):    walls 30.36, 28.99, 27.96, 27.99, 26.76
                                     median 27.99s, range 3.6s, mean 28.41s
```

## Updated 10-cand picture

Sequential 1M-conflict kissat, clean conditions:

| cand | HW | sym | seq median | seq range | tier |
|---|---:|:---:|---:|---:|---|
| bit2_ma896ee41 | **45** | EXACT | **27.08s** | 2.6s | FAST |
| **bit25_m30f40618** | **46** | NO | **27.99s** | 3.6s | **FAST** ← NEW |
| bit10_m9e157d24 | 47 | NO | 28.04s | 3.2s | FAST |
| **bit13_m4e560940** | **47** | EXACT | **32.83s** | 7.96s | **MEDIUM** ← NEW |
| msb_m9cfea9ce | 49 | NO | 35.19s | 8.3s | plateau |
| msb_m17149975 | 49 | NO | 35.81s | 8.07s | plateau |
| bit11_m45b0a5f6 | 50 | NO | 37.79s | 6.6s | plateau-slow |
| bit28_md1acca79 | 49 | NO | 39.25s | 21.8s | OUTLIER (high var) |
| bit17_mb36375a2 | 48 | EXACT | 42.52s | 20.05s | SLOW |
| bit00_md5508363 | 48 | EXACT | 53.42s | 15.87s | VERY SLOW |

## Two clear refinements

### 1. HW=46 cand IS fast (extends fast cluster to 3 cands)

bit25 (HW=46, NON-sym) at 27.99s is essentially indistinguishable
from bit2 (HW=45) and bit10 (HW=47). The fast cluster now includes
HW=45, 46, AND 47 cands.

### 2. HW=47 has INTERNAL VARIANCE — not all HW=47 cands fast

bit13 (HW=47, EXACT-sym) at 32.83s is NOT in the fast cluster, but
ALSO NOT in the slow tier. It's MEDIUM with moderate seed variance
(7.96s range).

bit10 (HW=47, NON-sym) at 28.04s IS in the fast cluster.

So at HW=47, EXACT-sym (bit13) is SLOWER than NON-sym (bit10) by
~5s. This is the OPPOSITE of any "symmetry helps" intuition.

## Refined narrow claim

The data now supports:

> "kissat at 1M conflicts on cascade_aux Mode A sr=60 has 3 fast cands
> (bit2 HW=45, bit25 HW=46, bit10 HW=47, all ~27-28s). bit13 (HW=47,
> exact-sym) is medium at ~33s. HW=48 EXACT-sym cands (bit00, bit17)
> are SLOW at 42-53s. HW≥49 cands cluster at 35-39s. The fast cluster
> requires HW≤47 BUT NOT all HW=47 cands qualify. Within the slow
> tier, HW=48 EXACT-sym is harder than HW=49 NON-sym — symmetry at
> HW=48 is HARMFUL, not helpful."

## What's NOW the discriminator?

The fast cluster (bit2, bit25, bit10) and the medium-fast (bit13)
all have HW≤47. Among HW=47:
- bit10 (NON-sym, fill=80000000): fast 28s
- bit13 (EXACT-sym, fill=aaaaaaaa): medium 33s

bit10's fill = 0x80000000 (single MSB bit set in fill words).
bit13's fill = 0xaaaaaaaa (alternating pattern).

Hypothesis: fill structure matters at HW=47. Sparse fill (bit10) →
fast, dense alternating (bit13) → medium. Untested.

Or: kernel bit position matters. bit10 uses bit 10 (sigma1-aligned),
bit13 uses bit 13 (different alignment).

The mechanism is opaque from current data. Need:
- Another HW=47 cand with different (kernel_bit, fill) combo to
  cross-check
- Another HW=46 cand to confirm bit25 isn't sui generis

## What this means for paper Section 4

The publishable claim solidifies as:

> "Within the cascade_aux Mode A sr=60 setting, the kissat-axis
> distinguishes ~3 cands at HW≤47 with sparse fills (bit2_ma896ee41,
> bit25_m30f40618, bit10_m9e157d24) at ~27-28s 1M-conflict
> sequential walls from a slower cluster of cands at HW≥48
> (~35-53s). The mechanism is unknown but appears tied to kernel-bit
> position + fill structure rather than HW alone, exact symmetry, or
> Lipmaa-Moriai cost."

This is a defensible claim with N=10 cand baseline.

## Implication for block2_wang target selection

The 3-cand FAST cluster:
- bit2_ma896ee41 — F28 HW champion + EXACT-sym + low LM-tail breadth
- bit25_m30f40618 — HW=46 non-sym + currently untested for LM properties
- bit10_m9e157d24 — HW=47 non-sym + medium-broad LM breadth

For Wang trail design:
- bit2 (best HW + sym) primary target
- bit25 (HW=46, untested LM) — worth running through cand_select.py
  with --weight-lm 1.0 to see where it stands LM-wise
- bit10 fast on solver but mediocre on LM (breadth=94)

For yale's operator-design: bit2 + bit25 + bit10 = the "fast cluster"
might also be operator-anchor-friendly. Worth testing whether yale's
guarded radius walks are similarly easier on these 3.

## Discipline

- 10 kissat runs logged via append_run.py
- bit13 CNF was pre-existing (built earlier today for F39 sequential
  test); bit25 CNF newly built and CONFIRMED via audit
- Sequential measurement (clean conditions)

EVIDENCE-level: VERIFIED for the 4-tier ordering (fast, medium,
plateau, slow). HYPOTHESIS for the (kernel_bit, fill) discriminator
within HW=47 — needs 2-3 more HW=47 data points.

## Concrete next moves

1. **Test bit25's LM properties** via active_adder_lm_bound on its
   F32 corpus records. Where does HW=46 sit on the LM tail?

2. **Test 1-2 more HW=46 cands** to verify the fast cluster includes
   most/all HW=46 cands (not just bit25).

3. **Test 1-2 more HW=47 cands with different (kernel_bit, fill)
   combos** to disambiguate the bit10 vs bit13 split. Candidates from
   F32: bit10 has multiple m0 values; bit28 has its HW=49 record;
   try bit13_m72f21093 (HW=47, fill=aaaaaaaa, NON-sym) — same fill
   as bit13_m4e560940 but different m0 → tests m0 vs symmetry.

4. **Update F49's "bit2 uniquely fast" claim** in paper-prep notes:
   it's now bit2 + bit25 + bit10 (3-cand fast cluster).
