# KILL MEMO — linear_lever_gaps (closed 2026-05-30)

**Kill criterion #2 fired:** linear-lever sr=60 shows no SAT and no advantage over the
σ1 baseline within the fail-fast window. Owner: macbook-claude. Lifetime: 2026-05-30
(one-day fail-fast probe, as designed).

## The bet (recap)

The sr=61 wall (`writeups/sr61_impossibility_argument.md`, `sr60_sr61_boundary_proof.md`
Thm 5) was blamed on the σ1 (t-2) enforcement lever. The schedule recurrence
`W[t]=σ1(W[t-2])+W[t-7]+σ0(W[t-15])+W[t-16]` has two full-rank LINEAR feedback terms
(t-7, t-16) never used as levers (`04_alternative_gaps.py` posed then dropped the idea).
Claim: enforce the boundary words {61,62,63} via independent linear levers (decoupling)
→ the linear-lever sr=60 instance the σ1 cascade *cannot build* solves faster, opening
a path to sr=61.

## Why it was killed (3 independent confirmations, full data in
`bets/linear_lever_gaps/results/20260530_phase2_verdict.md`)

1. **Controlled sr=59 comparison (the clincher).** Same candidate m17149975:
   σ1 top-block sr=59 → **SAT 208s/252s** (oracle-verified; also reproduces the paper's
   "92% broken" result). Linear-lever sr=59 (more freedom, deeper tail) → **TIMEOUT 900s**.
   The deep tail the linear lever *requires* (≥8 rounds to reach a free t-7 lever word,
   vs 7) makes the SAT instance strictly harder; decoupling does not compensate.
2. **sr=60 probe:** 6 seeds × 2 solvers × 1h → all TIMEOUT. Holding the a-path trigger
   W[57] → **UNSAT in 8s**.
3. **Trigger-counting wall (the real, lever-independent reason).** The cascade collision
   requires both triggers **W[57]** (a-path) and **W[60]** (e-path) free. So any config
   spends free words on 2 triggers + ≥2 boundary levers = **≥4 free = sr≤60**. The lever
   *kind* does not change this count. sr=61 (3 free words) cannot fit it.

Phase 0 also found σ0/σ1 are **full-rank bijections at N=32**, so there was never an
image-restriction for the linear lever to escape — only the adverse tail-depth cost.

## What would change my mind (reopen criteria)

- A collision mechanism needing only ONE cascade trigger free (then sr=61 = 1 trigger +
  boundary levers might fit 3 free words). The two-cascade structure appears inherent to
  SHA-256 collisions, so low conviction.
- A lever family that enforces a boundary word without deepening the tail (none exists:
  t-7→tail≥8, t-16→tail≥17).

## Salvage (preserved in `bets/linear_lever_gaps/`, NOT deleted)

- `encoders/lever_gap_encoder.py` — configurable gap-placement CNF encoder (arbitrary
  free positions, any tail_start, per-equation lever choice). 6/6 validation gate.
  **Reusable for the block2_wang pivot and any future free-position experiment.**
- `verify_lever_collision.py` + `verify_from_model.py` — independent general collision
  verifier (reproduced the cert + paper sr=59).
- `lever_feasibility.py` — clean-lever matching / sr-accounting analyzer.
- **Structural finding worth folding into the boundary writeup:** "W[57]/W[60]
  trigger-freedom is a hard counting constraint capping cascade gap-placement at sr=60,
  regardless of enforcement lever" — a sharper statement than the σ1-conflict argument.

## Disposition

Pivot (user-directed 2026-05-30): **block2_wang two-block connection** — jointly design
block-1 to produce an absorbable residual with CV pinned. The trigger-counting result
reinforces that single-block cascade gap-placement is genuinely capped at sr=60, so the
frontier is multi-block.
