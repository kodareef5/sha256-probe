# Track B: New Angles And Human-Assisted Algebra

Purpose: build new representations of the problem. These tasks are worth doing
even if they do not immediately produce sr=61, because they can create lemmas,
candidate priors, or lower-dimensional search spaces.

## B1. Bitcondition calculus

Build a SHA-256 tail worksheet that treats each bitcondition like a first-class
object:

- signed differences,
- XOR differences,
- modular-add carry conditions,
- Ch/Maj equality gates,
- schedule compatibility gates.

Deliverable:

- `headline_hunt/bets/math_principles/results/bitcondition_calculus.md`
- A small library of reusable local conditions, each with:
  - condition,
  - rounds affected,
  - compatible carries,
  - CNF clauses,
  - reduced-N frequency.

Why it matters:

This is how human-assisted algebra can beat monolithic SAT: by turning repeated
local facts into reusable constraints.

## B2. Carry chamber atlas

Model the tail as a union of discrete carry chambers. A chamber is a fixed
pattern of relevant carries plus gate equalities such as Ch-invisible or
Maj-invisible coordinates.

Tasks:

- Define a chamber signature for rounds 57..63.
- Cluster sr=60 certificates, near-sr61 points, and low-residual surfaces by
  that signature.
- For each chamber, measure:
  - local rank of W60 defect,
  - D61 residual floor,
  - number of exact-D60 representatives,
  - transition graph to neighboring chambers.

Deliverable:

- `headline_hunt/bets/singular_chamber_rank/results/carry_chamber_atlas_v2.md`

Pass condition:

- At least one chamber has a statistically lower D61 floor or lower W60 defect
  rank than the baseline.

## B3. Defect-map algebra

Treat the sr=61 obstruction as the object:

```text
D(W57,W58,W59) = S(W58) - R(W57,W58,W59) mod 2^32
```

where `S` is the schedule-derived W60 differential and `R` is the cascade-
required W60 differential.

Tasks:

- Factor `S` by sigma1 finite-difference offsets.
- Histogram image sizes of `S` for sparse and dense offsets.
- Measure preimage bucket sizes for `R`.
- Search for alignments where a compressed `S` image overlaps a fat `R` bucket.

Deliverable:

- `headline_hunt/bets/singular_chamber_rank/results/defect_map_factorization.md`

Why it matters:

This is the most concrete "dimensionality" question: does the obstruction map
really have full effective dimension, or are there singular low-image chambers?

## B4. Constructive BDD / automaton route

The existing BDD findings are interesting but mostly post-hoc. The useful next
question is whether a compact object can be built without first knowing all
collisions.

Tasks:

- Try variable orders based on schedule dependency, not word order.
- Build BDDs over defect-map outputs first, then add final collision gates.
- Test if exact-D60 surfaces have smaller BDDs than full sr=60 collision sets.
- Compare construction cost against brute force at N=8,10,12.

Deliverable:

- `headline_hunt/bets/math_principles/results/constructive_bdd_pilot.md`

Kill condition:

- If every construction path has exponential intermediate blowup by N=12, keep
  BDDs as diagnostics only.

## B5. MITM residue operationalization

The MITM idea is only useful once the "24-bit hard residue" is concrete.

Tasks:

- Audit existing q4 MITM scripts and mark working/stub/broken.
- Define the exact residue key bits.
- Build N=8 and N=10 forward/backward tables.
- Measure whether table matching beats existing reduced-N solvers.

Deliverable:

- `headline_hunt/bets/mitm_residue/prototypes/audit_summary.md`
- `headline_hunt/bets/mitm_residue/results/n10_operational_mitm.md`

Pass condition:

- Clear speedup over brute force or SAT on reduced N.

## B6. Block-2 Wang residual absorption

Single-block sr=64 might be the wrong target shape. Block 2 gives a new IV and
new message-modification opportunities.

Tasks:

- Build a residual corpus from best block-1 near-collisions.
- Cluster residuals by signed difference and carry-entry profile.
- Search block-2 local-collision trails before SAT.
- Test reduced-round pilots at 20/24/28/32 rounds.

Deliverable:

- `headline_hunt/bets/block2_wang/residuals/corpus.jsonl`
- `headline_hunt/bets/block2_wang/trails/block2_trail_pilot.md`

Pass condition:

- Any tailored block-2 trail that beats naive block-2 SAT or generic reduced
  SHA-256 trail baselines.

## B7. Lemma mining from failures

Every hard UNSAT/timeout region should yield clauses or priors.

Tasks:

- Mine DRAT/solver logs for recurring conflict surfaces.
- Compare learned-clause touch rates across W57/W58/W59, actual registers,
  carries, and schedule variables.
- Promote stable patterns to explicit assumptions or programmatic propagator
  rules.

Deliverable:

- `headline_hunt/bets/programmatic_sat_propagator/results/algebraic_lemma_bank.md`

Pass condition:

- At least one mined lemma family transfers across candidates or reduced widths.
