# F12c: All 4 close-cand residuals are highly structured grids
**2026-04-26 20:23 EDT**

Extends F12b (msb_m189b13c7 HW=2 single-value residual) with the
remaining 3 close-cand residual structures from full 2^32 enumeration.

## Per-cand minimum-HW de58 sets

### bit13_m4e560940 (fill=0xaaaaaaaa, bit=13) — HW=3 minimum

Only **2 distinct de58 values** at HW=3:
```
0x00102040  (bits 6, 13, 20)
0x00104040  (bits 6, 14, 20)
```
Difference: single-bit substitution at adjacent positions (13↔14).
**Pattern**: `0x001*2040 | one_of(13, 14)`

### bit17_m427c281d (fill=0x80000000, bit=17) — HW=3 minimum

**6 distinct de58 values**, 2×3 grid:
```
0x00080024 = bits {2, 5, 19}
0x00080021 = bits {0, 5, 19}
0x00080022 = bits {1, 5, 19}
0x00040024 = bits {2, 5, 18}
0x00040021 = bits {0, 5, 18}
0x00040022 = bits {1, 5, 18}
```
Structure: bit 5 always set; one of {bit 18, bit 19}; one of {bit 0, 1, 2}.
**Pattern**: `0x{0008|0004} | (1<<5) | (1<<bit_in_0_to_2)`

### bit18_m99bf552b (fill=0xffffffff, bit=18) — HW=4 minimum

**4 distinct de58 values**, 2×2 grid:
```
0x02160000 = bits {17, 18, 20, 25}
0x020e0000 = bits {17, 18, 19, 25}
0x04160000 = bits {17, 18, 20, 26}
0x040e0000 = bits {17, 18, 19, 26}
```
Structure: bits 17, 18 always; one of {bit 19, bit 20}; one of {bit 25, bit 26}.
**Pattern**: `(1<<17 | 1<<18) | one_of(1<<19, 1<<20) | one_of(1<<25, 1<<26)`

### msb_m189b13c7 (fill=0x80000000, bit=31) — HW=2 minimum (recap from F12b)

**1 distinct de58 value** at HW=2:
```
0x00000108  (bits 3, 8)
```

## Combined view

| cand | min HW | distinct values | grid structure |
|---|---:|---:|---|
| msb_m189b13c7 | 2 | 1 | (point) |
| bit13_m4e560940 | 3 | 2 | 1×2 (one bit varies) |
| bit17_m427c281d | 3 | 6 | 2×3 (two bits vary) |
| bit18_m99bf552b | 4 | 4 | 2×2 (two pairs vary) |

Each cand's residual structure is **algebraically determined** by the
cand's m0/fill/bit triple. Adjacent-bit substitutions and small
combinatorial grids — not random scatter.

## Implications

1. **The chart-preserving operator must hit specific bit positions.**
   Per F12b: the residual is modular (additive), not bitwise. An
   operator that correct ANY of the variants in a cand's grid suffices
   (since they're equivalent reachability paths to sr=61 collision).

2. **bit13's residual structure is the simplest** — only 2 values
   differing in one bit. If yale's chart-preserving operator works
   anywhere, this cand's "one-of-two" choice gives the most flexibility.

3. **msb_m189b13c7 still has the smallest HW (2)** but the residual is
   structurally rigid (1 value). Less flexibility than bit13's 2 options.
   Trade-off between residual size and option count.

4. **Cross-cand patterns**: Look for shared bit positions across cands.
   bit13's values use bits {6, 13, 14, 20}. bit17's use {0,1,2, 5, 18,
   19}. bit18's use {17, 18, 19, 20, 25, 26}. msb's use {3, 8}. No
   obvious overlap — each cand's residual is in a different bit region.

## What's next

- **F13 ETA: in flight**, will land all 67 cands' min HW (currently
  at 36/67).
- **F14 candidate**: For each fully-enumerated cand, output not just
  min HW but the FULL HW=k distinct-value table for k = min..min+2.
  Provides yale's operator design fully-specified residual targets.
- **Cross-cand shared-bit search**: are there any cand pairs whose
  HW=k residuals share a bit position? If yes, a single operator might
  close multiple cands.

EVIDENCE-level: VERIFIED (full 2^32 enumeration per cand).
