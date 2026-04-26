# M5 cross-candidate 1B-trial sweep: HW5 D61 floor reproduces — 2026-04-26

After establishing the joint frontier at D61 HW5 / tail HW60 on idx=8
(`bit3_m33ec77ca_ff`, `off58=0x00010002`), the obvious question was
whether this is idiosyncratic to one candidate's sparse-off58 chamber
or a structural floor across cascade-eligible cands.

This memo records 1B-trial walks at HW8 starting points for **three
distinct candidates** with **three distinct sparse-off58 chambers**.

## Setup

Each cand was started at its known-best HW8 D61 base point (from
earlier 100M / 10M walks), at the candidate's specific sparse-off58
chamber. 10 OMP threads, max_passes=80, max_flips=32, 1,000,000,000
trials. ~14 min wall each on M5.

## Per-candidate 1B-trial floors

| candidate | W57 | base point | sparse off58 | D61 floor | tail floor |
|---|---:|---|---:|---:|---:|
| idx 8 (`bit3_m33ec77ca_ff`) | `0xaf07f044` | yale's HW10 → cascade walks | `0x00010002` | **HW 5** | **HW 60** |
| idx 0 (`msb_cert m17149975`) | `0x370fef5f` | `W58=0x7eded6a0, W59=0x127163c2` | `0x00000021` | **HW 5** | HW 64 |
| idx 3 (`bit20_m294e1ea8`) | `0xe28da599` | `W58=0xce86b0ed, W59=0xbab6d1d7` | `0x00000802` | HW 6 | HW 67 |

(D61 floor and tail floor were found at distinct points within each
walk; the table reports the best of each separately.)

## Key finding

**HW 5 D61 reproduces across two distinct candidates with two distinct
sparse-off58 chambers:**

- idx 8: `W58=0xdd73a9d7, W59=0x57046fad` (defect61=`0x04240880`, HW5)
- idx 0: `W58=0x4c4dc123, W59=0x9ad3f074` (defect61=`0x02081030`, HW5)

The two HW5 points share no W coordinate and live in different sparse
off58 chambers. They're at different candidates, different fills,
different kernel bits. Both verified via independent `tailpoint` runs.

This is evidence that **HW5 is a structural floor of the singular-
chamber descent under random-flip walks at 1B trials**, not a property
of one specific (m0, fill, bit) tuple.

idx 3 floors slightly higher at HW6, suggesting candidate-specific
variation but not far from the HW5 norm.

## d61 histograms (exact `defect60=0` only)

```text
idx 8 from HW7 base (cddef23):
  HW5: 5.9M  HW6: 4.8M  HW7: 42.4M  HW8: 45  HW9-17: ~26K

idx 0 from HW8 base (this run):
  HW5: 2.1M  HW6: 5.9M  HW7: 4.1M  HW8: 37.9M  HW9: 10.6K  HW10-28: scattered

idx 3 from HW8 base (this run):
  HW6: 1.7M  HW7: 2.9M  HW8: 40.5M  HW9: 575  HW10-25: scattered (HW5: 0)
```

Walker geometry differs per cand — idx 0 has a much wider HW6 basin
(5.9M / 1B) than idx 8 from its analogous HW8 starting point — but
the sub-HW8 reachability is qualitatively similar.

## Interpretation

The HW5 D61 floor is robust:
- Reachable from multiple candidates' sparse-off58 chambers.
- Reachable via the same `surface61greedywalk` operator with same
  parameters.
- Not idiosyncratic to idx 8's geometry.

The tail floor varies more by candidate:
- idx 8: HW60 (best)
- idx 0: HW64
- idx 3: HW67

This is consistent with cascade-2 propagating tail differences according
to candidate-specific carry chamber details, while D61 is gated by
synchronized-state geometry that's more universal across cands.

## What this does NOT show

- Whether HW4 / HW3 / lower D61 exist on any candidate (none found at 1B).
- Whether the HW5 floor is structural in the sense of a formal
  obstruction, or just a deep local minimum for the random-flip walker.
- Cross-fill behavior on the same kernel bit (untested).

## Joint frontier (yale + macbook campaign)

| value | source | comment |
|---|---|---|
| HW10 → HW8 → HW7 → **HW5** D61 | mixed | reproduced across 2 cands now |
| HW76 → 74 → 70 → 68 → 67 → **HW60** tail | M5 1B walks | idx 8 specific |
| D60-HW7/D61-HW2 cap-2 terrace (non-exact) | yale | repair gate |
| D60-HW4/D61-HW4 cap-4 terrace (non-exact) | yale | repair gate |

## Next directions (no-commit until substantive)

1. Walk from idx 0 HW5 base at 1B → does cross-cand HW4 or HW3 appear?
2. Try other yale-tested cands (idx 1, 2, 4, ..., 17) at 1B — how many
   reach HW5? Is this a floor across all 18 cands or just some?
3. Coordinate with yale on carry-aware repair from cap-4 terrace —
   if that path closes D60 while preserving D61=HW4, cross-cand HW4
   floor confirmed.
4. Consider non-flip perturbation: pair-bit flips, byte rotations, etc.

## Run inventory

- run7_HW7base_1B.json — found HW5 / HW68 (committed cddef23)
- run8_HW5base_1B.json — null on D61, tail → HW67 (committed ffc01c3)
- run9_HW67tail_1B.json — null on D61, **tail → HW60** (committed c28c1bb)
- run10_HW60tail_1B.json — null on both (not committed per user guidance)
- run11_cap4_1B.json — null on both (not committed)
- run12_idx3_HW8_1B.json — idx 3 floors at HW6 (this memo)
- run13_idx0_HW8_1B.json — idx 0 reaches HW5 / tail HW64 (this memo)

7 1B-trial walks total, ~7B trials processed, ~1.7 hours wall on M5.
