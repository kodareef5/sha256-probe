# F874 Combo Shape Calibration Correction

F868 extends `summarize_m2_combo_branches.py` so old combo artifacts are
annotated with M2 add/remove/net shape. It also now recomputes standalone pair
delta summaries from the selected pair atlas instead of trusting stale fields
stored in older combo records.

## Correction

The earlier read that F788 was "standalone-delta neutral" was wrong. The old
F788 artifact contained stale zero values for `standalone_net_delta_sum` and
`delta_lane_sum`.

After recomputation:

| branch | best HW | raw M2 shape | standalone net-delta sum |
| --- | --- | --- | --- |
| F788 successful detour | HW86 | add11/remove1/net+10 | 175 |
| F796 weak detour | HW87 | add11/remove1/net+10 | 161 |
| F799 later detour | HW87 | add11/remove1/net+10 | 160 |
| F852 bit18 transfer | HW90 | add12/remove0/net+12 | 140 |

So raw detour shape and standalone-delta sum do not explain why F788 repaired
to HW78 while F796/F799 did not.

## F870-F873 Delta-Neutral Selector Tests

I tested the mistaken delta-neutral hypothesis anyway:

- F870: F760 overlap selector with `max_standalone_net_delta_sum=0`
  - evaluated: 0 / 1,000,000 sampled
- F871: same, threshold 80
  - evaluated: 0 / 1,000,000 sampled
- F872: same, threshold 140
  - evaluated: 116,920
  - target improvements: 80
  - best HW: 94
- F873: meet-in-the-middle exact delta-neutral search
  - kept partials: 0
  - evaluated: 0

Verdict: delta-neutral composition is not the selector.

## Updated Interpretation

The F788 raw detour is add-heavy like several failed branches. The useful
property appears downstream: F788's repair transition to F789 has a mixed
add/remove cover, while weaker branches repair by pure add-add overfill or do
not repair.

The next selector should therefore not reject add-heavy raw detours outright.
It should score whether a detour is likely to have F788-like repair
coverability after the side basin is formed.
