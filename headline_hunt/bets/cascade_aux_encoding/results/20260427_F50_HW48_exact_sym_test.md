# F50: HW=48 exact-sym cands are SLOWER than plateau — symmetry alone ≠ fast
**2026-04-27 09:55 EDT — daily heartbeat substantive review**

Tests F49's open question: "is bit2's ~27s uniqueness from HW=45 alone,
exact symmetry alone, or HW=45+symmetry combo?"

Picked 2 untested HW=48 EXACT-sym cands (the lowest HW exact-sym cands
besides bit2 and bit13):
- bit00_md5508363_fill80000000 (HW=48, exact-sym a_61=e_61)
- bit17_mb36375a2_fill00000000 (HW=48, exact-sym a_61=e_61)

If symmetry is the discriminator, both should be ~27s. If HW=45 is the
discriminator, both should be on the plateau (~36s).

## Result

```
bit00_md5508363 (HW=48, EXACT-sym):  walls 57.40, 54.12, 48.51, 41.53, 53.42
                                     median 53.42s, mean 51.00s, range 15.87s

bit17_mb36375a2 (HW=48, EXACT-sym):  walls 58.05, 42.52, 38.39, 44.28, 38.00
                                     median 42.52s, mean 44.25s, range 20.05s
```

**Both HW=48 exact-sym cands are SLOWER than the plateau (35s).**
NEITHER fast like bit2 NOR consistent with the plateau. They're in
their own slow tier above 40s with high seed variance.

## Updated 8-cand picture

Sequential 1M-conflict kissat (clean conditions):

| cand | HW | sym | seq median | seq range | tier |
|---|---:|:---:|---:|---:|---|
| bit2_ma896ee41 | 45 | EXACT | **27.08s** | 2.6s | FAST |
| bit10_m9e157d24 | 47 | no | **28.04s** | 3.2s | FAST |
| msb_m9cfea9ce | 49 | no | 35.19s | 8.3s | plateau |
| msb_m17149975 | 49 | no | 35.81s | 8.07s | plateau |
| bit11_m45b0a5f6 | 50 | no | 37.79s | 6.6s | plateau-slow |
| bit28_md1acca79 | 49 | no | 39.25s | 21.8s | OUTLIER (high var) |
| bit17_mb36375a2 | 48 | **EXACT** | **42.52s** | **20.05s** | SLOW |
| bit00_md5508363 | 48 | **EXACT** | **53.42s** | 15.87s | VERY SLOW |

## What F50 reveals

**Symmetry alone doesn't predict speed**. Both new exact-sym cands
(bit00, bit17) are SLOWER than non-sym cands at similar HW.

**The "fast cluster" (bit2, bit10)** has 2 cands with NOTHING obvious
in common except low HW (45-47):
- bit2: HW=45, EXACT-sym, fill=ffffffff, breadth=68
- bit10: HW=47, NON-sym, fill=80000000, breadth=94

They DON'T share symmetry, fill, or breadth. The only shared property:
HW ≤ 47 AND particular distinguishing properties.

## Refined hypothesis (testable)

**H1**: HW=45 is uniquely fast; HW=46 also fast (untested); HW=47 is
mixed (bit10 fast, bit13 unknown sequential); HW≥48 is slow.

To test: run **bit13_m4e560940 SEQUENTIAL** (HW=47, exact-sym; only
parallel-5 measurement so far at 35.94s F39). If sequential is ~28s,
HW=47 is fast. If 35-37s, HW=47 is mixed.

Also: pick a HW=46 cand (e.g., bit25_m30f40618 or bit3_m33ec77ca) and
test sequentially. If ~27s, "HW≤47 fast" survives.

## What F50 does NOT confirm

The "fast cluster is uniquely (bit2, bit10)" is consistent with HW≤47
but ALSO consistent with cand-specific properties not yet captured.
8 data points across 7 HW values is sparse.

## High seed variance is a separate signal

bit00, bit17, bit28 all have seq RANGE > 15s (vs 3-8s for plateau
cands). High seed variance correlates with high median.

Tentative pattern: the SLOW cands (HW≥48 mostly) have BOTH higher
median AND higher seed variance. Suggests they have more "branchy"
CNFs (per F47's branchiness speculation) which kissat handles
unpredictably.

## Implication for paper Section 4

Revised claim from F49:
> "kissat at 1M conflicts on cascade_aux Mode A sr=60 has fast
> cands (HW≤47, ~27-28s seq) and slow cands (HW≥48, 35-53s seq with
> high seed variance). The HW threshold appears at HW=47-48 boundary.
> Within the slow tier, no further cand-level structure (symmetry,
> LM, breadth) gives further prediction. The mechanism for the HW
> threshold is unknown."

Narrower claim than F37/F38/F47/F48 ever made; better supported by
N=8 data.

## Discipline

- 10 kissat runs logged via append_run.py
- Both new CNFs CONFIRMED via audit
- Sequential measurement (clean conditions, no dispatcher contention
  attempted)

EVIDENCE-level: VERIFIED for symmetry-doesn't-explain. HYPOTHESIS for
HW=47 boundary; needs 2-3 more cands at HW=46/47 to test.

## Concrete next moves

1. **Test bit13_m4e560940 sequential** (HW=47, exact-sym). Decisive
   for HW=47 boundary.
2. **Test bit25_m30f40618 or bit3_m33ec77ca sequential** (both
   HW=46). If fast, HW boundary is at 46-47 area; if slow, the
   bit2/bit10 fast pair is sui generis.
3. **For block2_wang trail design**: bit2 + bit10 are dual primary
   targets on the solver-axis (regardless of which is more important
   on Wang-axis).
4. **For yale's operator design**: target the (bit2, bit10) fast
   cluster — solver-friendly anchors might also be operator-friendly.
