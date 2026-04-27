# bet: sigma1_aligned_kernel_sweep

**Status: open, owner: unassigned, priority: 7 (lowest)**

## The bet

The Σ1 function in SHA-256 is `Σ1(e) = ROR(e,6) ^ ROR(e,11) ^ ROR(e,25)`.
Bits 6, 11, 17 (= 6+11), 19 (= 11+8), and 25 are "Σ1-aligned" — they
appear at boundary positions in the rotated XOR. The hypothesis is that
candidates with kernel-difference bits at these positions might have
different (better?) cascade properties.

**Specific hypothesis**: bits 10, 17, 19 are sigma1-aligned and were
identified as productive for sr=61 but never fully swept with the best
fills. A complete fill sweep at these bits might find a candidate that
admits sr=61 SAT or faster sr=60 SAT.

## What's built

- `exotic_kernel_search.py` — search for non-(0,9) word-pair kernels
  (extending project's existing (0,9) baseline)
- `results/20260424_predict_audit.md` — closed-form (h60+f60) predicted
  hard bit count across 35 cands, comparing sigma1-aligned vs
  non-aligned

## What's known (against the bet)

1. **Pre-screen finds NO sigma1-alignment advantage**: mean predicted
   hard bits 7.6 (sigma1-aligned) vs 7.4 (non-aligned). Negligible.

2. **F-series per-conflict equivalence (F37, F39, F41)**: at 1M kissat
   conflicts, ALL distinguished cands cluster at 27s (sequential) or
   35s (parallel). Cand-level structural variations are SOLVER-INVISIBLE
   at moderate budgets. This eliminates the "easier solver behavior"
   pathway for sigma1-aligned advantage.

3. **F36 universal LM-compatibility**: ALL 67 cascade-1 trails are
   structurally LM-compatible. The "differential trail compatibility"
   pathway also doesn't differentiate cands.

4. **Hypothesis premise is unverified**: claim "never fully swept with
   the best fills" assumes there's a "best fill" to find. Pre-screen
   suggests no clear best fill exists at sigma1-aligned positions.

## What would change my mind (reopen criteria)

- **Empirical 1M-sample full sweep** confirms NO h+f+g advantage for
  sigma1-aligned cands → KILL.
- **Deep-budget (12h+) kissat** reveals a sigma1-aligned cand finds
  SAT before any non-aligned cand → REOPEN with high priority.
- **A NEW theoretical reason** (not currently in the literature) why
  Σ1's specific bit positions should give cascade advantage → REOPEN.

## Concrete next-actions if a worker picks this up

1. Validate the pre-screen with full empirical hard_residue analysis
   on a 35-cand 1M-sample sweep. If empirical h+f+g gap is also <1
   bit, KILL the bet and add to negatives.yaml.

2. If empirical gap exists (>3 bits): build full cascade_aux Mode A
   CNFs for top sigma1-aligned cands, run kissat 12h × multiple
   seeds, compare SAT/UNSAT outcomes to non-aligned cands of similar
   HW.

3. If still no advantage at deep budget: kill bet and write KILL_MEMO.

## Bet status

Per F36 and F37/F39/F41, this bet's pathway to a headline is narrow.
Recommend: leave open at priority 7, do NOT initiate compute. If a
worker has spare cycles and wants a clean negative result, the
1M-sample full sweep (~1 hour M5) will provide a definitive verdict.

The bet's hypothesis was reasonable in 2026-04 (pre-F-series); F-series
findings have substantially undermined the premise.
