# Headline Targets

*From GPT-5.5 meta-consultation (2026-04-24). See `consultations/20260424_secondwind/`.*

## The three headline classes we're hunting

Anything that doesn't fit one of these is not a headline. Stop pursuing it.

### 1. Break one more schedule-compliance round

> **A TRUE sr=61 semi-free-start collision at full N=32 SHA-256.**

Why headline-worthy: unambiguous, certificate-verifiable, directly extends
the public boundary, not dependent on mini-SHA extrapolation.

Why hard: previous "sr=61 racing" was on mislabeled sr=60 CNFs (CNF audit
2026-04-18). True sr=61 has had only ~1800 CPU-hours since.

**Bet:** `bets/sr61_n32/` — *budget-capped at 10k additional CPU-h*.

### 2. Turn compactness into construction

> **A SAT-free / compilation-based collision finder that beats the known
> search barrier on a nontrivial reduced-SHA target.**

Why headline-worthy: the BDD O(N^4.8) result says the collision manifold
is structurally polynomial. Constructive evidence would be a TCS+crypto
crossover result.

Why hard: all known compilation paths (BDD Apply, bottom-up SDD, d4,
derived encoding) hit blowup. The construction route is unproven.

**Bets:**
- `bets/cascade_aux_encoding/` — local-offset auxiliaries to escape the encoding/treewidth conflict.
- `bets/kc_xor_d4/` — d4 with XOR-preserving preprocessing on standard CNFs.
- `bets/programmatic_sat_propagator/` — propagator that exposes carry modes, cascade offsets, schedule-derived W[60].

### 3. Change mechanism class

> **A Wang/rebound/multi-block style attack that bypasses the single-block
> cascade boundary entirely.**

Why headline-worthy: Bridges beyond what schedule-compliance arguments cover.

Why hard: requires a real bitcondition/trail engine, not just SAT. Human-time
expensive. Naive multi-block was closed (HW=7 at N=8 too large); Wang with
tailored differential trails is structurally different and untried.

**Bets:**
- `bets/block2_wang/` — **highest EV/CPU-hour per GPT-5.5**.
- `bets/mitm_residue/` — MITM on the 24-bit hard residue (tools exist, not operational).
- `bets/chunk_mode_dp/` — chunk-mode DP with mode variables.

## Clean-stop criteria

If after a bounded, instrumented sprint:
- no SAT,
- no UNSAT proof,
- no solver-behavior improvement from new encodings,
- no structural predictor,

across **all five priority bets** under their stated kill criteria, then:

> Stop hunting. Publish the boundary/paradox paper. Or pause indefinitely.

The clean stop is real and acceptable. The point of the registry is to
make sure we *recognize* it instead of drifting back into seed farming.

## What is NOT a headline

- Another paper section on the existing sr=60 result.
- More seed farming on unchanged CNF encodings.
- Marginal speedup on already-closed approaches.
- Reduced-N results that don't extend or compose to N=32.

If the work doesn't pass one of those filters, log it in the relevant
mechanism entry but don't burn more CPU on it.

## Structural insights from the headline-hunt sprint (2026-04-24 / 2026-04-25)

Durable findings that should inform any future bet design.

### Cascade-DP residual is a 4-d.o.f. modular variety at r=63
- 6 active register diffs at r=63 are constrained by 2 modular relations (R63.1: dc=dg, R63.3: da-de=dT2). Net 4 independent moduli × 32 bits = 128-bit residual variety.
- Cascade-sr=61 SAT prob = 2^-32 per candidate matches the structural prediction of 2^(96 - 128).
- Empirical uniformity check (20k samples): 4 d.o.f. distribute uniformly, no hidden 5th constraint.
- Reference: `bets/mitm_residue/results/20260425_residual_structure_complete.md`

### CDCL search on cascade-DP CNF is DIFF-AUX-FOCUSED, not actual-value-focused
- CDCL navigates by deciding XOR-diff aux variables (dE[r], dA[r], etc.).
- Actual register values (a_61, a_60, etc.) are decided IMPLICITLY via unit propagation, rarely as primary decisions.
- Implication: propagation rules depending on actual register values fire heavily during preprocessing (when cascade-zero unit clauses cause massive propagation) and go SILENT during deep search.
- Reference: `bets/programmatic_sat_propagator/results/phase2c_continuous_trigger_2026-04-25/RESULT.md`

### Mode B preprocessing speedup is 2-3.4× but FRONT-LOADED
- 50k conflicts: Mode B is 2× faster than standard on kissat, 3.4× on cadical.
- 500k conflicts: speedup erodes to ~1×.
- The SPEC's "≥10× SAT speedup" claim was empirically refuted at all tested budgets.
- Reference: `bets/cascade_aux_encoding/comparisons/conflict_500k_2026-04-25/RESULT.md`

### Rule-4-style cascade propagator (this specific design) refuted on tested budgets
- Scope of this finding: ONE design — the actual-register-value-triggered Rule-4 propagator with continuous-decide variant. Does NOT generalize to "all programmatic SAT for SHA-256 is dead." A diff-aux-variable propagator, or a fundamentally different rule set, has not been tested.
- 750 LOC C++ propagator implementing Rules 1+2+3+5+4@r=61+4@r=62 ships and runs end-to-end.
- Rule 4@r=62 fires 209-249 times in first ~50k conflicts, ZERO times across 50k–500k under tested triggers.
- Decision count drops 17% with continuous trigger but wall time still 1.9× slower than vanilla at tested budgets.
- Reference: `bets/programmatic_sat_propagator/kill_criteria.md` (criterion #3 fired). Reopen criteria documented there.

### What this means for headline-hunting (claim-tightened 2026-04-25)

- **Cascade-DP at the tested encoding budgets did not go sub-2^32.** This is EVIDENCE that the structural ceiling on the current encoder family + CDCL approach is near 2^32, not a derived ceiling for all cascade-DP encodings. A new encoder or non-CDCL solver could in principle still help.
- **The Rule-4 propagator path doesn't beat Mode B at the budgets tested.** Future propagators must operate on diff-aux variables (which CDCL DOES decide) or actively shape CDCL decisions via cb_decide().
- **Headline path 1 (sr=61 SAT)** still requires multi-day-per-candidate compute. No structural shortcut found.
- **Headline path 2 (constructive collision via compilation)** unaltered by propagator findings — different mechanism class.
- **Headline path 3 (Wang-style block-2 trail)** unaltered, still highest EV per GPT-5.5 meta-consultation.

The 2026-04-25 sprint sharpened the bet portfolio. Future workers: design propagation rules that fit CDCL's natural diff-aux search trajectory, not against it.

### de58 family of structural findings (2026-04-25 evening)

Empirical sweeps across the 36 registered candidates produced a coherent picture of cascade-DP search-space structure at the cascade boundary:

- **At r=60, only de58 varies.** All other register diffs at r=60 are candidate-fixed constants (image=1). The cascade-DP residual at the cascade boundary is **1-dimensional in W57**.
- **Image sizes vary 24 bits across candidates**: bit-19_m51ca0b34 has image 2^8 (extreme); msb_m189b13c7 has image 2^17.98 (least compressed). 6 candidates have image = exact power of 2.
- **Theorem 4 verified at full N=32 across r=61**: `da_61 ≡ de_61 (mod 2^32)` for 1,048,576 random samples, 0 violations.
- **Full residual at r=63 is 1-D in W57 across all candidates**: joint image of 6-component diff saturates at sample size = injective. Cascade-DP r=63 residual is parameterized entirely by W57 (32 bits).
- **de58 images of the 36 candidates are 96.7% pairwise disjoint**. Total union covers ~0.030% of 32-bit de58 space. Choice of candidate = choice of de58 region. de58=0 is in NO candidate's image at 65k samples.
- **Low-HW de58 reachability differs across candidates**: 3 candidates achieve HW=3 (bit13_m4e560940, bit17_m427c281d, msb_m189b13c7); bit-19's image is HW=14+ throughout. Two competing structural extremes.
- **Per-de58-class W57 → da_63 is essentially injective**: bit-19's 24-bit compression at de58 does NOT propagate to r=63. Compression caps at de58 alone.
- **References**: `bets/sr61_n32/results/20260425_de58_*.md`, `20260425_residual_growth_r60_to_r63.md`, `20260425_residuals_only_de58_varies.md`.

**Implication for the bet portfolio**: candidate selection is non-redundant — different candidates explore disjoint regions of de58 space. But within a candidate, the W57 search hits a 32-bit ceiling. The "30s C brute force" speculation is wrong (encoder demands FULL slot-64 collision; observed 0 da_61=0 hits in 4M trials at bit-19). The 1800 CPU-h sr61_n32 baseline is real problem hardness.
