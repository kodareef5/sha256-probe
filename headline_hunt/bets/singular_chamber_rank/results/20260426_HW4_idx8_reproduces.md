# HW4 D61 reproduces on idx=8 — cross-cand confirmation
**2026-04-26 12:58 EDT**

The 1B-trial walk from yale's HW59 tail base (idx=8) found a D61=HW4
exact-D60=0 point. Combined with the idx=0 HW4 finding (commit 37b721a),
**HW4 D61 now reproduces across both candidates** at distinct sparse
off58 chambers.

## idx=8 HW4 point (NEW)

```text
candidate: idx 8 (bit3_m33ec77ca_ff, sparse off58=0x00010002)
W57 = 0xaf07f044
W58 = 0x63f723cf
W59 = 0x10990224

tail defects:
  defect60 = 0x00000000  (HW 0)
  defect61 = 0x41200001  (HW 4)
  defect62 = 0x283ee703  (HW 15)
  defect63 = 0xe2155224  (HW 12)
tail HW = 79
```

Verified via `tailpoint`. 1,458,517 hits at HW4 in this walk's 1B trials
(0.146% of trials, 2.65% of exact-D60 hits). Note: the walk happened to
be from yale's HW59 tail base (W58=0xe537c1c7, W59=0x598feb25), not the
HW5 base — the walker descended both to HW14 dominant and to HW4 fringe.

## idx=0 HW4 point (committed 37b721a)

```text
candidate: idx 0 (msb_cert m17149975, sparse off58=0x00000021)
W57 = 0x370fef5f
W58 = 0x6ced4182
W59 = 0x9af03606
defect61 = 0x80110200  (HW 4)
tail HW = 77
```

## Cross-cand HW4 evidence

| candidate | W57 | W58 | W59 | sparse off58 | defect61 |
|---|---:|---:|---:|---:|---:|
| idx 0 | `0x370fef5f` | `0x6ced4182` | `0x9af03606` | `0x00000021` | `0x80110200` (HW4) |
| idx 8 | `0xaf07f044` | `0x63f723cf` | `0x10990224` | `0x00010002` | `0x41200001` (HW4) |

Different candidates, different sparse off58 chambers, different W
coordinates, **both reach exact D61=HW4 with defect60=0**.

This is structural evidence: HW4 D61 is reachable on multiple cands
under random-flip walks at 1B-trial budget. Not idiosyncratic.

## Histogram from yale's HW59-tail walk (idx=8)

```text
HW  4:  1,458,517   ← NEW idx=8 frontier
HW  5:  1,662,289
HW  6:  2,268,305
HW  7:  8,627,043
HW  8:  9,665,071
HW  9-13: ~1.85M
HW 14: 29,252,209  ← starting basin
HW 15-25: ~262K scattered
```

The HW59-tail base sits in a wide-spectrum region. Walker reaches HW4
through HW8 fluently (millions of hits each), with HW14 dominant from
the starting basin.

## Joint frontier (post this walk)

| value | source | comment |
|---|---|---|
| HW10 → HW8 → HW7 → HW5 → **HW4** D61 | mixed | reproduced on 2 cands |
| HW76 → 74 → 70 → 68 → 67 → 60 → **HW59** tail | yale 3335040 | unchanged this walk |

**6-bit total D61 improvement, 17-bit total tail improvement** from
yale's initial HW10 / HW76 frontier across the joint descent.

## What's still open

- HW3 D61: not seen in 1B-trial walk from HW4 base (idx=0) or in this
  walk. HW4 base on idx=0 was 99.3% trapping (committed earlier).
- Whether yale's structural cap-2 terrace (D60=HW7/D61=HW2) can be
  repaired onto exact D60=0 via carry-aware proposals.
- Cross-cand HW4 on idx=3 (which floored at HW6 in our 1B sweep).

## Run inventory (campaign so far)

9 1B-trial M5 walks, ~9B trials, ~2.1 hours wall total.

- run7 cddef23: idx=8 HW7 base → HW5 / HW68 (frontier)
- run8 ffc01c3: idx=8 HW5 base → null D61, tail HW67 (frontier)
- run9 c28c1bb: idx=8 HW67 tail base → null D61, tail HW60 (frontier)
- run10: idx=8 HW60 tail base → null both (no commit)
- run11: yale's cap-4 terrace → null both (no commit)
- run12: idx=3 HW8 base → D61 HW6, tail HW67 (in summary memo b69d5c4)
- run13: idx=0 HW8 base → D61 HW5, tail HW64 (in summary memo b69d5c4)
- run14 37b721a: idx=0 HW5 base → **D61 HW4 frontier**
- run15: idx=0 HW4 base → null both (HW4 trap, no commit)
- run16 (this memo): yale's HW59 tail base → cross-cand HW4 idx=8

7 substantive frontier moves, 5 commits. ~7B trials productive +
~2B null.
