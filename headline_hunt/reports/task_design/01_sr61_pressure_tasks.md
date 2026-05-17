# Track A: sr=61 Pressure Tasks

Purpose: make the sr=60 to sr=61 jump with structured pressure, not by rerunning
the same hard instance. The target is either a true sr=61 certificate or a much
cleaner explanation of why this mechanism stops before sr=61.

## A1. sr=61 assumption ladder

Question: which exact bits of the W60 schedule equation are fatal?

Build a ladder of CNFs where W60 compliance is enforced in increasing strength:

| Level | Constraint |
|---|---|
| L0 | sr=60 baseline, W57..W60 free |
| L1 | 1 chosen W60 bit enforced |
| L2 | 2 to 4 W60 bits enforced, chosen by sigma1/carry relevance |
| L3 | one byte or one rotation-aligned slice enforced |
| L4 | full W60 equation enforced, true sr=61 |

Deliverable:

- `headline_hunt/bets/sr61_n32/results/sr61_assumption_ladder.md`
- `headline_hunt/bets/sr61_n32/results/sr61_assumption_ladder.jsonl`

Minimum useful output:

- A ranked list of W60 bit subsets by SAT rate, timeout depth, conflicts, and
  residual quality.
- At least one subset that is measurably easier than random bit enforcement,
  or a negative showing all natural slices collapse similarly.

Budget:

- 1 day to generate/audit CNFs.
- 200 to 500 CPU-hours for a first full matrix.
- Stop if all L1/L2 slices are equivalent and no solver metric separates them.

## A2. Defect-surface bridge mining

Question: can exact D60 compatibility be maintained while lowering the round-61
defect below the current HW4/HW5 frontier?

Use the existing `singular_chamber_rank` surface tools as the center. Focus on
actual bridges between carry chambers, not local random walks.

Tasks:

- Enumerate radius-6/radius-7/radius-8 neighborhoods around exact-D60, low-D61
  points.
- Record transitions by carry signature, not just Hamming score.
- Identify moves that preserve exact D60 but switch the D61-active term from
  Sigma/Ch/T2 mixed to a single-term failure.
- Export candidate surfaces as assumptions for A1.

Deliverable:

- `headline_hunt/bets/singular_chamber_rank/results/defect_surface_bridge_atlas.md`
- A machine-readable list of promising `(kernel, M0, W57, W58, W59, carry_signature)`.

Kill condition:

- If bridge moves repeatedly repair D60 only by destroying D61, treat this
  cascade surface as a hard local basin and move time to A4.

## A3. sr60 certificate inverse-lift

Question: can the known sr=60 certificate be pulled back toward real message
space instead of trying to solve sr=61 from scratch?

The sr=60 certificate gives ideal relaxed values for W57..W60. Real SHA-256
forces these to be schedule-derived from W0..W15. Search for message blocks
whose derived W57..W60 are close to the certificate while preserving the
cascade state gates.

Experiments:

- Linear no-carry lift from message bits to W57..W60.
- Carry-aware local repair of the lift.
- Multi-objective score:
  - schedule mismatch to certificate,
  - da56 gate,
  - de60/de61/de62/de63 cascade gates,
  - W60 defect bits.
- Track Pareto fronts, not a single scalar.

Deliverable:

- `headline_hunt/bets/math_principles/results/sr60_certificate_inverse_lift.md`
- Top 100 seeds for A1/A2, with mismatch decomposition by word and by bit.

Pass condition:

- Find seeds with better schedule proximity and no worse cascade score than
  current hand-picked candidates.

## A4. Non-cascade sr=61 trail search

Question: is the cascade mechanism itself the trap?

Search for sr=61 candidates that do not require the W60-free cascade trigger.
This means letting the differential trail move, not just modifying M0/fill
inside the MSB cascade family.

Tasks:

- Build a signed-difference trail model for the 7-round tail.
- Allow alternate zeroing order across registers.
- Penalize active carries and active schedule bits, but do not hardwire
  da56 -> db57 -> dc58 -> dd59.
- At reduced N, compare best non-cascade trails against the cascade baseline.

Deliverable:

- `headline_hunt/bets/sr61_n32/results/noncascade_trail_pilot.md`
- A reduced-N table: cascade best vs non-cascade best at N=8,10,12,16.

Pass condition:

- Any non-cascade family that beats cascade on W60 compatibility, even if its
  final residual is worse at first.

## A5. Minimal programmatic SAT propagator

Question: can domain lemmas cut the sr=61 search tree before CDCL learns them
the hard way?

Avoid building a full custom solver first. Start with a small set of trusted
propagation/lemma rules:

- W60 defect cannot be repaired under specific carry signatures.
- Certain D60 exact-surface transitions imply a lower bound on D61 HW.
- Known cascade gate combinations force W57/W58/W59 relations.

Deliverable:

- A lemma bank in DIMACS assumption/learned-clause form.
- `headline_hunt/bets/programmatic_sat_propagator/results/sr61_lemma_bank_eval.md`

Pass condition:

- More than 5x reduction in conflicts on N=8/N=10 sr=61 replicas, or a clear
  extrapolation reason to keep going.

## A6. sr=61 certificate criteria

A true sr=61 hit must include:

- Full 64-step compression collision under the relaxed model.
- Exactly 3 free schedule words, with W60 schedule-compliant.
- Independent native verifier.
- Stock SHA-256 non-collision check, to keep the model distinction explicit.
- A round-by-round trace showing how the collision closes without free W60.
