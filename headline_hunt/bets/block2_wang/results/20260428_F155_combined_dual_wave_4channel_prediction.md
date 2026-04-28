# F155: Combined dual-wave + 4-channel prediction — single highest-priority test

**2026-04-28**

## The synthesis

After 4 iterations of macbook ↔ yale structural-prediction loop:
- F150: raw density → F128: falsified
- F152: 4-channel composite → F131: also misses
- F154: dual-wave hypothesis (early {0,1,2} + mid {8,9} clusters)
- F129/F130: yale's concentration ranker also misses winner

Yale's F131 conclusion: "missing feature remains the word-8 to W24
phase". Yale identified the dual-wave structure independently.

F155 SYNTHESIZES both insights into a SINGLE high-priority candidate.

## The candidate

**(0, 1, 8, 9, 14)**

This subset has BOTH structural features:

### W[16] coverage: ALL 4 SHA expansion channels

| Active word | Channel | Reaches W[16] |
|---|---|---|
| W[0] | direct (i=16, offset 16) | yes |
| W[1] | σ_0 (i=16, offset 15) | yes |
| W[9] | direct_t7 (i=16, offset 7) | yes |
| W[14] | σ_1 (i=16, offset 2) | **yes (added)** |

vs yale's {0,1,2,8,9} which has only 3 of 4 (missing σ_1).

### W[24] dual-wave: same 2 channels as yale's winner

| Active word | Channel | Reaches W[24] |
|---|---|---|
| W[8] | direct (i=24, offset 16) | yes |
| W[9] | σ_0 (i=24, offset 15) | yes |

Same as yale's {0,1,2,8,9} second-wave structure.

## Why this is the sharpest prediction

(0,1,8,9,14) STRICTLY DOMINATES yale's winner on BOTH metrics:
- W[16] fan-in: 4 vs yale's 3 (with 4-channel coverage)
- W[24] fan-in: 2 (same dual-wave structure as yale's)

Yale's F131 tested (0,1,9,10,14), (0,1,9,14,15), etc. — these have
W[16] 4-channel coverage but DROP yale's W[24] dual-wave structure
(W[8] is replaced). They scored 96-102.

(0,1,8,9,14) PRESERVES yale's W[24] dual-wave (W[8]+W[9] both there)
AND adds the 4th W[16] channel via W[14].

Yale's stated next direction (F131): "search should bias toward masks
that preserve the W16/W17 structure of {0,1,2,8,9} while varying only
the W24 contributor" — F155 does the OPPOSITE (preserve W[24] structure,
augment W[16]). Both directions valuable.

## Predicted outcome

If F155 holds: (0,1,8,9,14) score < 86 (predicted 78-84).

If yes: composite metric (4-channel-W[16] + dual-wave-W[24]) is the
real structural feature. Validates the F152+F154 chain.

If no: yale's W[24] structure is sensitive to the OTHER words ({0,1,2}
specifically), and adding W[14] disrupts it somehow.

## Test command

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/active_subset_scan.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit3_HW55_naive_blocktwo.json \
  --pool 0,1,8,9,14 --sizes 5 --restarts 3 --iterations 4000 \
  --require-all-used \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F155_dualwave_4channel_0_1_8_9_14_3x4k.json
```

~5 minutes yale-side compute. If it shows score < 86, run a continuation
(--restarts 8 --iterations 50000) to refine.

## Other dual-wave + 4-channel candidates

The strict (W[16]≥3 AND W[24]≥3) intersection set is small. Beyond
(0,1,8,9,14), the next-best candidates with W[16] 4-channel coverage
+ dual-wave at W[24] are sparser. (0,1,8,9,14) is the cleanest.

For F155-PLUS (broader sweep), 32 subsets share yale's exact (3,2,3,2)
fan-in profile. Examples: {0,1,3,8,9}, {0,1,5,8,9}, {0,1,8,9,11},
{0,1,8,9,15}, etc. Yale has already implicitly explored some of these
in continuations (F121-F123), but the ENUMERATIVE map of all 33 is in
the probe output.

## Status

If F155's (0,1,8,9,14) test reveals score < 86, it's the FIRST
empirical break of yale's score-86 floor since F123. That alone is
headline-eligible structural progress on the bit3 absorber search.

The macbook ↔ yale loop is now at iteration 4. Yale tests fast (~5 min);
each iteration sharpens the structural metric. This is exactly the
multi-machine learning the project's mission directs.

## Discipline

- 0 SAT compute, 0 solver runs
- Pure-thought refinement on yale's F131 negative + F129/F130 ranker
- Probe at `/tmp/dual_wave_subsets.py` (one-shot, derivable)
