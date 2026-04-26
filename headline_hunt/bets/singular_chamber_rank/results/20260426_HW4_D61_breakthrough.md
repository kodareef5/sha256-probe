# HW4 D61 breakthrough on idx=0 — 2026-04-26

After the cross-cand 1B sweep (commit b69d5c4) confirmed HW5 D61 floor
reproduces on both idx=8 and idx=0, walking 1B trials from idx=0's
HW5 base point (`W58=0x4c4dc123, W59=0x9ad3f074`) crossed the HW5
floor: **defect61 HW4 found at full N=32, exact defect60=0**.

This is the first sub-HW5 D61 in the joint yale + macbook descent.

## Verified frontier point

```text
candidate: idx 0 (msb_cert m17149975, kernel bit 31, fill ffffffff)
W57 = 0x370fef5f
W58 = 0x6ced4182
W59 = 0x9af03606

off58 = 0x00000021  (HW 2, sparse)
off59 = 0x0deeb412  (HW 15)

tail defects:
  defect57..60 = 0
  defect61 = 0x80110200  (HW 4)  ← NEW frontier
  defect62 = 0x82450a0c  (HW 9)
  defect63 = 0xc22bd337  (HW 17)
tail HW = 77
```

Verified via independent `tailpoint` and `manifold61point` runs.

## Walk that found it

```bash
/tmp/singular_defect_rank surface61greedywalk \
  0 0x370fef5f 0x4c4dc123 0x9ad3f074 \
  1000000000 10 80 32
```

(idx=0 HW5 base → 1B trials → HW4 reached.)

## Histogram from this walk

```text
HW  4:    659,651   ← NEW frontier (0.066% of trials)
HW  5: 46,334,304   ← starting basin (97% of exact-D60 hits)
HW  6:          1
HW  7-12:    ~9,750
HW 13:  1,477,012   ← next geometric distance
HW 14-25: ~52,000
```

Striking: HW4 appears 659,651 times in 1B trials, while HW5 absorbs
the vast majority. HW3 / HW2 / HW1 / HW0 not observed in 1B.

The histogram has a sharp gap between HW6 (1 hit) and HW13 (1.5M).
HW4 is a separate basin reachable from HW5 via a specific narrow
transition — not a smooth gradient.

## Joint frontier (yale + macbook campaign)

| value | source | comment |
|---|---|---|
| HW10 → HW8 → HW7 → HW5 → **HW4** D61 | mixed | crossed floor on idx=0 |
| HW76 → 74 → 70 → 68 → 67 → 60 → **HW59** tail | yale 3335040 / M5 c28c1bb | idx=8 specific |

**6-bit total improvement on D61 from yale's initial frontier.**

## Significance

Yale's structural analysis identified non-exact terraces at D61=HW4
(D60=HW4) and D61=HW2 (D60=HW7) but couldn't repair them onto the
exact D60=0 surface via standard Newton/greedy. Raw 1B-trial depth on
idx=0 found the exact D61=HW4 directly — confirming sub-HW5 D61 is
reachable on the exact surface, just not via local repair from
yale's near-miss terraces.

This **doesn't** prove HW3, HW2, HW1 are unreachable. It proves HW4
is reachable on idx=0. Three open questions:

1. Does idx=0 reach HW3 with continued 1B walks from HW4 base?
2. Does idx=8 (which floored at HW5) reach HW4 with a walk from a
   different idx=8 starting point, or is HW4 idx=0-specific?
3. What's the cross-cand pattern for HW4 — does it reproduce on idx=3
   and the other 15 yale cands?

## Reproduce

```bash
# Walk that found HW4 (idx=0 from HW5 base):
/tmp/singular_defect_rank surface61greedywalk \
  0 0x370fef5f 0x4c4dc123 0x9ad3f074 \
  1000000000 10 80 32

# Verify the HW4 point:
/tmp/singular_defect_rank tailpoint 0 0x370fef5f 0x6ced4182 0x9af03606
# Expected: defect61=0x80110200 (HW4), tail_hw=77

/tmp/singular_defect_rank manifold61point 0 0x370fef5f 0x6ced4182 0x9af03606
# Expected: defect60_hw=0, defect61_hw=4, off58=0x00000021 (HW2)
```

EVIDENCE-level: defect61 HW4 at exact defect60=0 verified at full N=32
on idx=0 (`msb_cert_m17149975_ff_bit31`).
