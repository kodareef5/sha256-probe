---
date: 2026-05-25
bet: block2_wang
status: EVIDENCE
author: macbook-claude
---

# Residual HW floor is universal across the candidate panel; the c/g lock is basin-specific

## Method

Mapped the block-1 residual floor across the **full 21-candidate panel** (Path C
had deeply searched only bit24/bit13/bit28). Ran the validated hillclimb
(`block2_bridge_beam.py --method anneal --iterations 20000 --seeds 3`, 4 parallel
groups; reuses the existing evaluator) and took the best per candidate.
Logs/JSON: `results/runs/20260525_panel_floor_map/`.

## Result

Best HW per candidate (quick-anneal; Path C deep-search reaches ~43 on its top 3):

```
floor band over 21 cands: min=51  max=59  median=56     (Wang target <=24)
c63 at floor: 1..6   g63 at floor: 1..7
```

Every candidate floors in a tight band (51–59 quick, ~43 deep). **The residual
floor is universal — not candidate-specific.** No candidate is remotely near 24.

## Two refinements to the F449 c/g-lock picture

1. **The c/g "lock" is basin-specific, not a global single-lane floor.** At these
   (different) low-HW basins, c63 and g63 are individually LOW (1–6) — yet total HW
   stays ~55 because a/b/e/f rise. So one can make c/g small; one just can't make
   ALL six active lanes small simultaneously. F449's "no pair reduces c or g" was a
   property of the *HW43 basin*, not a global bound on the c/g lanes.
2. **The floor is a JOINT all-lane constraint.** This is why local moves "repair one
   lane by damaging another" (F449) and why the (w57,w58)|(w59,w60) decomposition
   failed (20260525_cg_lane_decomposition_negative.md): the lanes trade off; total
   HW has a joint floor ~43.

## Strategic implication (EVIDENCE)

Cross-validated with this session's mitm_residue 24-bit refutation (forward
free-word residual floor ~34 bits effective; gh60 >= ~34 effective bits), the
evidence is consistent and strong: **Phase-1 residual-minimization cannot reach the
≤24 Wang threshold — the structural floor is ~40–43, universal across candidates.**

Recommended pivot (for owner attention): the bet's ORIGINAL premise was a block-2
Wang TRAIL designed to *absorb* the cascade residual — not minimizing the residual
to ≤24. Two coherent directions:
- (A) Re-examine the ≤24 assumption: can a tailored block-2 differential trail absorb
  a ~43-HW (joint-floored) residual? That is the actual, never-started Phase 2.
- (B) If ≤24 is firm and the floor is ~43, the residual-minimization route is closed;
  document and consider de-prioritizing the residual-grind in favor of (A) or kill.

This does not close the bet — it redirects effort from residual-HW grinding (deeply
plateaued, now shown universal) toward the trail-design question it was meant to test.

---

## CORRECTION (2026-05-25, same day, macbook-claude) — retract the pessimistic floor

On reviewing the existing frontier I found my numbers above are WRONG and the
strategic claim is too pessimistic. Honest correction:

1. **The achievable residual frontier is ~HW35, NOT ~43.** The deep frontier was
   reached by the c/g pair-beam / exact-atlas tools (not hillclimb), progressively:
   49 -> 43 -> 38 (F460) -> 36 (F471 record) -> 35 (F487 record). My panel map used a
   QUICK ANNEAL from random seeds (51-59), which is a weak-search artifact, not the
   true floor. I extrapolated a "~43 floor" the bet's better tools had already beaten.
2. **"Residual-min cannot reach <=24" is RETRACTED as premature.** The gap is ~11 HW
   (35 -> 24), and the frontier was *steadily* reduced (49 -> 35), slowing but not
   provably floored at 35. No hard floor at 35 is established.
3. **The "HW82" I associated with the floor (F749) is a DIFFERENT metric** — the M2
   *absorber* weight (block-2 message), not the block-1 residual HW. I conflated them.

What survives: the c/g lane coupling (joint, not single-lane) is real (the decomposition
negative still holds), and quick generic search floors uniformly ~55 — but the genuine
frontier needs the exact c/g pair-beam tools, which were progressing toward the target.
Lesson: validate against the existing frontier before asserting a floor. The strategic
"pivot away from residual-min" recommendation is withdrawn; the right next step is to
RESUME the c/g pair-beam push from the HW35 record (or advance the trail engine), not to
abandon residual-min.
