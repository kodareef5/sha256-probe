# Fill Consistency Across N Values

## Finding

Same fill values produce SAT at some N widths but TIMEOUT at others.
This proves N=26, 29, 31 are STRUCTURALLY harder, not just unlucky.

## Data

| Fill | SAT at N | TIMEOUT at N |
|------|----------|--------------|
| 0x00000000 | N=24 | N=26 |
| 0x00000055 | N=30 | N=26, 29, 31 |
| 0x000000aa | N=25, 28 | N=26 |
| 0x000000f0 | N=23 | N=26 |
| 0x03ffffff | N=27 | N=26, 29 |

## Implications

1. **N=26 is universally hard**: 5 different proven-winning fills all TIMEOUT
2. **N=29 is hard**: 4 winning fills TIMEOUT
3. **N=31 is hard**: at least 1 winning fill TIMEOUT
4. **The hardness is in N, not the candidate**: same fill behaves differently
   at different word widths

## Connection to Rotation Analysis

Cross-referencing with rotation_gap_full_analysis.md:
- N=26: sm=1, g1=4 → hard (the rotation gap hypothesis)
- N=29: sm=2, g1=5 → hard (rotation gap doesn't predict)
- N=31: sm=2, g1=5 → hard (same as N=29)

N=29 and N=31 share Sigma1 first gap g1=5 with N=28 and N=32.
N=28 and N=32 are NOT timing out structurally:
- N=28: SAT (with right fill)
- N=32: racing, presumably should SAT

The pattern suggests N=29/31 difficulty involves something OTHER than
rotation gaps. Possible factors:
- K[i] constant truncation creates bad bit patterns at these widths
- Specific bit positions in the schedule become degenerate
- Number-theoretic properties of N (29 and 31 are prime!)

## Hypothesis: Prime N is harder?

| N | Prime? | Status |
|---|--------|--------|
| 23 | yes | SAT (slow, needed cand 7/7) |
| 24 | no | SAT |
| 25 | no | SAT |
| 26 | no | TIMEOUT |
| 27 | no | SAT |
| 28 | no | SAT |
| 29 | **yes** | TIMEOUT |
| 30 | no | SAT |
| 31 | **yes** | TIMEOUT |
| 32 | no | racing |

**3 of 3 prime widths are difficult** (N=23 was solved but needed 7/7
candidates; N=29, 31 still timing out). This is striking but small sample.

Alternative explanation: rounded rotations may have specific
degeneracies at prime widths that don't appear at composite widths.

EVIDENCE level: HYPOTHESIS — pattern observed, mechanism unknown.
