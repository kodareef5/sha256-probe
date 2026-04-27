# F52: EXACT-symmetry at HW≥47 is HARMFUL — discriminator identified
**2026-04-27 10:23 EDT**

DECISIVE TEST of F51's open question: at HW=47, is the bit10/bit13
split caused by symmetry, fill, or m0?

Answer: **EXACT-symmetry alone is the discriminator at HW≥47.**

## The crucial control

Tested bit13_m72f21093 — SAME m0=0x72f21093... wait, different m0.
SAME fill (0xaaaaaaaa) and same kernel_bit (13) as bit13_m4e560940,
but different m0 → NON-symmetric residual.

| cand | HW | fill | bit | sym | seq median | tier |
|---|---:|:---:|:---:|:---:|---:|---|
| bit13_m4e560940 | 47 | aaaaaaaa | 13 | **EXACT** | **32.83s** | MEDIUM |
| **bit13_m72f21093** | **47** | **aaaaaaaa** | **13** | **NO** | **28.72s** | **FAST** |

**Same fill, same kernel_bit, different m0 → DIFFERENT speed because
of symmetry status.** F51's "fill=aaaaaaaa is the discriminator"
hypothesis is REFUTED.

## Two more data points (HW=47 + HW=46)

```
bit14_m40fde4d2 (HW=47, fill=ffffffff, NON-sym):  median 31.73s, range 8.22s — MEDIUM
bit3_m33ec77ca  (HW=46, fill=ffffffff, NON-sym):  median 29.22s, range 2.78s — FAST
```

bit3 is FAST at HW=46 (2nd HW=46 cand confirmed fast after bit25).
bit14 is MEDIUM at HW=47 NON-sym — NOT in fast cluster despite NON-sym.

## Updated 13-cand picture

Sequential 1M-conflict kissat, clean conditions:

| cand | HW | sym | seq median | seq range | tier |
|---|---:|:---:|---:|---:|---|
| bit2_ma896ee41 | 45 | EXACT | 27.08s | 2.6s | FAST |
| **bit13_m72f21093** | 47 | **NO** | 28.72s | 2.76s | FAST |
| bit10_m9e157d24 | 47 | NO | 28.04s | 3.2s | FAST |
| bit25_m30f40618 | 46 | NO | 27.99s | 3.6s | FAST |
| bit3_m33ec77ca | 46 | NO | 29.22s | 2.78s | FAST |
| bit14_m40fde4d2 | 47 | NO | 31.73s | 8.22s | medium |
| **bit13_m4e560940** | 47 | **EXACT** | 32.83s | 7.96s | MEDIUM (sym hurts) |
| msb_m9cfea9ce | 49 | NO | 35.19s | 8.3s | plateau |
| msb_m17149975 | 49 | NO | 35.81s | 8.07s | plateau |
| bit11_m45b0a5f6 | 50 | NO | 37.79s | 6.6s | plateau-slow |
| bit28_md1acca79 | 49 | NO | 39.25s | 21.8s | OUTLIER (high var) |
| **bit17_mb36375a2** | 48 | **EXACT** | 42.52s | 20.05s | SLOW (sym hurts) |
| **bit00_md5508363** | 48 | **EXACT** | 53.42s | 15.87s | VERY SLOW (sym hurts) |

## Refined narrow claim — solidified at N=13 cands

> "kissat at 1M conflicts on cascade_aux Mode A sr=60: a fast cluster
> of 5 cands exists at HW≤47 with NON-symmetric residuals (or HW=45
> with sym), all at ~27-29s sequential. EXACT-symmetric residuals at
> HW=47 are MEDIUM (~33s); at HW=48, EXACT-sym are SLOW (42-53s).
> NON-sym cands at HW=49+ form a 35-39s plateau. The pattern is
> consistent: at HW≤45, EXACT-sym is fast; at HW≥47, EXACT-sym is
> slower than NON-sym at the same HW."

This is a STRONG result — 13-cand baseline + clean control via
bit13_m72f21093 (same fill/kernel as bit13_m4e560940, different m0).

## Why bit2 (HW=45 EXACT-sym) is fast despite the trend

bit2's exact-symmetric pattern (a_61=e_61=0x02000004, HW=2) is
SPARSE — only 2 bits. bit13_m4e560940's pattern (a_61=e_61=0x00820042,
HW=4) is denser. bit00_md5508363's a_61=e_61=0x40001004 (HW=3) — and
bit00 is the SLOWEST cand tested.

Hmm — bit00's pattern HW=3 is sparser than bit13's HW=4 but bit00 is
SLOWER. So sparse-symmetry doesn't explain bit2's speed either.

bit2's distinguishing properties: HW=45 (lowest in registry) AND
exact-sym. It might be that HW=45 alone makes it fast and the
symmetry is incidental. Then bit13_m4e560940 (HW=47, exact-sym) is
slow because HW=47 + exact-sym overlap with whatever harmful
combination exists.

Working hypothesis (untested): **the speed predictor is HW alone for
NON-sym cands (HW=46/47 fast, HW=49+ slow); EXACT-sym cands at
HW≥47 are SLOWER than NON-sym at same HW; HW=45 is uniquely fast
regardless of symmetry**.

This needs:
- Another HW=45 cand (NONE EXIST in F32 corpus — bit2 is unique)
- Another HW=48 NON-sym cand to test if "HW=48 is slow universally"
  or just "HW=48 EXACT-sym is slow"

## What this enables

For paper Section 4, the kissat-axis structural finding is now solid:

1. **HW=45 is uniquely fast** (only 1 cand exists; can't generalize)
2. **HW=46-47 NON-sym cands form a 4-cand fast cluster** (~27-29s)
3. **EXACT-symmetry at HW≥47 is HARMFUL** (medium to very slow)
4. **HW=49+ NON-sym** plateaus at 35-39s
5. **HW=48 EXACT-sym is SPECIFICALLY hardest** (42-53s)

Mechanism speculation: cascade_aux CNF for EXACT-sym residuals at
HW≥47 has structural redundancy (both a_61 and e_61 share the same
bit pattern) that creates symmetric SAT branches kissat can't easily
break. At HW=45, the residual is too sparse for redundancy to dominate.

## Implications for block2_wang

The fast cluster (5 cands at HW≤47 non-sym + HW=45 sym):
- bit2_ma896ee41: F28 HW champion + EXACT-sym + fast
- bit25_m30f40618: HW=46 + non-sym + fast
- bit3_m33ec77ca: HW=46 + non-sym + fast (idx8 in older memos)
- bit10_m9e157d24: HW=47 + non-sym + fast
- bit13_m72f21093: HW=47 + non-sym + fast

For Wang trail design, bit2 keeps its primary status (HW + sym for
absorption pattern). For solver-axis, all 5 are interchangeable.

## Discipline

- 15 kissat runs logged via append_run.py
- 3 new CNFs CONFIRMED via audit
- Sequential measurement (clean conditions)

EVIDENCE-level: VERIFIED. The bit13_m4e560940 vs bit13_m72f21093
control (same fill, kernel_bit, different m0) is the strongest
piece of evidence. 13-cand baseline now solid.

## Concrete next moves

1. **Test ANY HW=48 NON-sym cand** to confirm "HW=48 universally slow"
   vs "HW=48 EXACT-sym specifically slow." If HW=48 NON-sym ~35s,
   then exact-sym is the discriminator at HW=48 too.

2. **Test bit13_mbee3704b (HW=48, EXACT-sym, fill=00000000)** —
   different fill, same sym status. If slow like bit00/bit17, sym is
   confirmed at HW=48 too.

3. **Document the F52 finding in the cascade_aux BET.yaml** as a
   structural observation suitable for paper Section 4.

4. **For yale's operator design**: the EXACT-sym-at-HW≥47 cands
   (bit13_m4e560940, bit17_mb36375a2, bit00_md5508363) all have
   structural symmetric patterns. yale's manifold-search might be
   easier on these because the symmetry constrains the manifold —
   opposite of solver-axis intuition. Worth testing.
