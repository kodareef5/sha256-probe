# F12b: msb_m189b13c7 HW=2 residual is STRUCTURALLY PINNED at de58=0x00000108
**2026-04-26 20:21 EDT**

Followup to F12 (commit b8a0a2e). Analyzed the structure of low-HW de58
values for the registry's structural champion (msb_m189b13c7, HW=2 reach).

## Result

Full 2^32 enumeration with per-HW distinct-value tracking:

| HW | total chambers | distinct de58 values |
|---:|---:|---:|
| **2** | **512** | **1** |
| 3 | 10,240 | 20 |
| 4 | 98,304 | 192 |

**At HW=2, every single one of the 512 chambers produces de58 =
0x00000108** (bits 3 and 8 set). Not just a single chamber as a fluke
— a structurally-fixed value with multi-W57 chamber multiplicity.

## HW=3 structure: all 20 values contain 0x108 as a core

The 20 HW=3 values are exactly: 0x108 OR (one extra bit). Examples:

```
0x20000108  0x01000108  0x00400108  0x00800108  0x00040108
0x00010108  0x00001108  0x00000908  0x00000308  0x00000188
0x00000128  0x00000148  0x00000118  0x00000508  0x00020108
0x00100108  0x00080108  0x00200108  0x40000108  0x80000108
```

20 values = 20 of the 30 possible "0x108 + one extra bit" combinations.
(2 bits are already set in 0x108, leaving 30 positions; only 20 produce
HW=3 chambers — the other 10 positions don't appear in the image.)

## What this means for yale's chart-preserving operator

The HW=2 residual is not a "random pair of bits" — it's a structural
fingerprint of the cascade-1 chamber's algebraic geometry for
msb_m189b13c7. Bit 3 and bit 8 are pinned.

For yale's "Sigma1/Ch/T2 chart-preserving operator" to close this
cand to sr=61, the operator must specifically MODULAR-ADD 0x00000108
to de58 while preserving cascade-1. That's a 2-bit modular correction
at fixed positions.

The operator's design space narrows dramatically:
- **NOT a generic perturbation**: must hit bits 3 and 8 specifically.
- **NOT XOR-based**: de58 is modular subtraction; the residual is
  arithmetic, not bit-wise.
- The closest cands by residual size:
  - msb_m189b13c7: residual 0x108 (HW=2, structurally unique)
  - bit13_m4e560940: residual 0x102040 (HW=3)
  - bit17_m427c281d: residual 0x080024 (HW=3)
  - bit18_m99bf552b: residual 0x2160000 (HW=4)

Each cand's residual is a different bit pattern. If the operator
exists, it likely doesn't transfer between cands — must be tuned
per-cand.

## Concrete next steps

1. **Send msb_m189b13c7 + residual structure to yale** as the priority
   chart-preserving operator target. Smallest residual + structurally
   simplest (single fixed value, single chamber-multiplicity).
2. **Cand-residue inverse map**: for each cand, build the {chamber W57}
   → {de58 value at that chamber} table at HW≤k, exposing structure.
3. **Cross-cand residual algebra**: do bits 3+8 (msb_m189b13c7's
   residual) appear in any other cand's residual? If yes, that's a
   shared structural feature — common operator might work across cands.

## C tool

`encoders/de58_lowhw_set.c` — full 2^32 enum with per-HW distinct
tracking. Compile: `gcc -O3 -march=native -o de58_lowhw_set de58_lowhw_set.c`.
Usage: `./de58_lowhw_set 0xMMM 0xFFF BIT MAX_HW` (~7s per cand).

EVIDENCE-level: VERIFIED. The HW=2 residual being structurally pinned
at 0x108 across 512 distinct W57 chambers is an exhaustive empirical
fact (full 2^32 enumeration).
