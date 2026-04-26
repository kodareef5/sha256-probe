# bit=19 (mitm_residue priority target) floors at HW5, NOT HW4
**2026-04-26 14:18 EDT**

The B1 task — single 1B walk to test whether bit=19 (the de58_size=256
extreme-compression cand, mitm_residue's "priority MITM target") admits
sub-HW4 D61 — produced an unexpected negative result:

**bit=19 floors at HW5, HIGHER than the HW4 floor on idx=0/8/17.**

## Verified bit=19 D61 floor

```text
candidate: idx 1 (bit19_m51ca0b34_55, fill=0x55, de58_size=256)
W57 = 0x4f9409ff
W58 = 0x808b2c19
W59 = 0xf7f4de0b
off58 = 0x00000804  (HW 2)
defect60 = 0x00000000 (HW 0)
defect61 = 0x01488020  (HW 5)
tail HW = 83
```

Verified via tailpoint. **HW4 D61 NOT reached in 1B trials on bit=19.**

## d61 histogram

```text
HW  5:  2,016,222
HW  6:  6,598,643
HW  7: 11,875,698
HW  8:  5,239,099
HW  9:  1,494,484
HW 10:    992,873
HW 11-12:  1,159,856
HW 13: 33,137,619   ← dominant starting basin
HW 14-26:  ~2.5M scattered
```

HW5 hit 2M times in 1B (0.2%), HW6 hit 6.6M (0.66%). The walker
explores HW5-HW8 fluently. **HW4: zero hits**. Lowest reached: HW5.

## Cross-cand floor map (after this walk)

| candidate | de58_size | sparse off58 | D61 floor at 1B |
|---|---:|---:|---:|
| idx 0 (msb_cert m17149975) | 82826 | `0x00000021` (HW2) | **HW 4** |
| idx 1 (bit19 m51ca0b34) | **256** | `0x00000804` (HW2) | **HW 5** ← higher |
| idx 3 (bit20 m294e1ea8) | 8187 | `0x00000802` (HW2) | HW 6 |
| idx 8 (bit3 m33ec77ca) | ? | `0x00010002` (HW2) | **HW 4** |
| idx 17 (bit15 m28c09a5a) | 4096 | `0x00000001` (HW1) | **HW 4** |

Floor distribution: HW4 (×3 cands), HW5 (×1 cand), HW6 (×1 cand).
**No correlation between de58_size and D61 floor.** bit=19 with the
smallest de58 image has a HIGHER D61 floor.

## Implication for mitm_residue bet

The mitm_residue bet's BET.yaml current_progress declares bit=19
m=0x51ca0b34 as the "PRIORITY MITM TARGET" with these arguments:
- 17 empirical hard bits at round 60
- 3 bits below next-best
- de58_size=256 forward table built

The prediction was that bit=19's structural compression makes it
*easier* to find sr=61 SAT. **The B1 result shows bit=19 has HIGHER
D61 floor under singular_chamber descent — strictly harder than the
"average" cand for greedy-flip walks.**

This invalidates the framing that "extreme compression at de58 →
extreme advantage for SAT search." Yale's prior negative result on
GPU off58 chart scan showed off58 sparsity isn't the ranking function.
B1 confirms: de58 image compression isn't either. **Neither schedule-
side compression metric predicts D61 search difficulty.**

The rank-function for D61 difficulty is something other than de58
or off58 compression. Likely: a property of the carry chambers
themselves at the round 60-61 boundary, which yale is mapping via
exhaustive fiber enumeration (`2bc9e4d`).

## Implication for negatives.yaml

The `bdd_marginals_uniform` reopen criterion was: "BDD marginals at
N≥10 are uniform — provide no SAT branching heuristic signal." That
was tested on generic cands. The B1 result here shows bit=19's
structural distinguishment doesn't translate to D61 advantage — a
related-but-distinct claim. The BDD marginals test (D2 task) is still
worth running on bit=19, but the prior expectation that bit=19 would
show non-uniform marginals **is now weaker**, not stronger.

## What B1 settled

1. ✓ Does HW4 reproduce on the most-compressed cand? **NO** — bit=19
   floors at HW5, not HW4.
2. ✓ Is mitm_residue's "priority MITM target" structurally distinguished?
   **NO for D61 search** — bit=19 is harder, not easier.
3. ✗ negatives.yaml `bdd_marginals_uniform`: still untested; D2 task
   remains.

## What B1 opened

The HW4/HW5 split across cands is **per-cand**, not de58-predictable.
What does predict the floor? Likely: the dimension of the linear
kernel of the local two-wall map (rank_pair = 63 vs 64 distinguishes
some cands' geometry per yale's manifold61point output). Worth a
small follow-up analysis: rank_pair vs floor across the 5 tested cands.

## Run inventory addendum

run20: idx=1 bit=19, 1B trials → D61 HW5, tail HW65, exact60_hits=65.2M

14 1B-trial walks total. ~14B trials, ~3.3h M5 wall.

## Next per task list

- B1 ✓ complete (this commit)
- B2 not strictly needed (HW4 confirmed across enough cands; bit=19's
  HIGHER floor is the surprise, not HW3 found)
- D2 (BDD marginals on bit=19) still worth running — distinct test
- C1 (Mode B × HW4 near-misses) still worth running
- Coordinate with yale's `d60_fiber_exhaustion` work
