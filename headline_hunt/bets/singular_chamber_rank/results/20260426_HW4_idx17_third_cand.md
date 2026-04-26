# HW4 D61 reproduces on idx=17 — third candidate confirmation
**2026-04-26 13:50 EDT**

After the convergent-evidence checkpoint (`570bd4a` + `fb16afa` addendum)
indicated HW4 / HW59 is the structural floor of the current operator
family, the natural pivot was to test a structurally-distinct chamber.

idx=17 (bit15 m=0x28c09a5a fill=0xff) has off58=0x00000001 — the
**sparsest off58 in the registry** (HW=1, just one bit set).

## Verified HW4 point on idx=17

```text
candidate: idx 17 (bit15_m28c09a5a_ff)
W57 = 0xa418c4ae
W58 = 0x47d3203e
W59 = 0x6eb1fa38

off58 = 0x00000001  (HW 1, sparsest known)
defect60 = 0x00000000  (HW 0)
defect61 = 0x30201000  (HW 4)
defect62 = 0xe11ba83c
defect63 = 0xbee319f5
tail HW = 84
```

Verified via independent `tailpoint` run.
2,831,418 hits at HW4 in 1B trials (0.28%).

## HW4 across three structurally distinct chambers

| candidate | off58 | HW(off58) | HW4 D61 reachable? |
|---|---:|---:|---|
| idx 0 (msb_cert m17149975) | `0x00000021` | 2 | YES (commit 37b721a) |
| idx 8 (bit3 m33ec77ca) | `0x00010002` | 2 | YES (commit c14c587) |
| idx 17 (bit15 m28c09a5a) | `0x00000001` | 1 | YES (this memo) |

Three different candidates, three different sparse off58 chambers
with maximally distinct geometries (HW1 single-bit vs HW2 two-bit
patterns), all reach HW4 D61 at the exact `defect60=0` surface.

## What changed in the picture

The HW4 floor is **stronger than 'cross-cand reproduces'**:
even when off58 is reduced to HW=1 (the geometrically extreme
case where schedule finite-difference S(W58) collapses to the
smallest possible image), the D61 floor at exact D60=0 is still HW4.

This eliminates "off58 sparsity richer = lower D61 floor" as a
working hypothesis. Yale's GPU off58 chart scan (cf9cd74) pointed
the same direction; this is direct empirical confirmation at the
extreme HW1 chamber.

## Joint frontier (unchanged)

| objective | value |
|---|---:|
| round-61 defect | HW 4 |
| checked tail | HW 59 |

## Run inventory through this commit

| run | cand | base | result |
|---|---|---|---|
| 7 | idx 8 | HW7 | HW5 / HW68 |
| 8 | idx 8 | HW5 | tail HW67 |
| 9 | idx 8 | HW67 tail | tail HW60 |
| 10-11 | idx 8 | HW60 / cap-4 | null |
| 12-13 | idx 3,0 | HW8 | HW6/HW67, HW5/HW64 |
| 14 | idx 0 | HW5 | **HW4 frontier** |
| 15 | idx 0 | HW4 | trap (99.3%) |
| 16 | idx 8 | HW59 tail | idx=8 HW4 reproduces |
| 17 | idx 8 | HW4 | trap (99.94%) |
| 18 | idx 0 | HW4 radius=64 | trap (99.36%) |
| 19 | idx 17 | HW15 (this) | **idx=17 HW4 reproduces** |

13 1B-trial walks, ~13B trials, ~3 hours wall total on M5.

## Implications

The campaign now has 4 convergent attack vectors all bottoming at
HW4 / HW59:

1. M5 raw 1B greedy-flip (×11 walks across 3 cands)
2. M5 wider radius (radius=64)
3. Yale's GPU off58 chart scan + 100-250M walks on alt charts
4. Yale's kernel-rep enumeration in linear two-wall map
5. **(NEW) M5 walk in HW1 sparsest off58 chamber**

This memo strengthens the structural-floor hypothesis. To go below
HW4, the operator family must change — carry-aware proposals or
trail-search style construction.
