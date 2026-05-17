# Track D: Speculative Math Triage

Purpose: keep naive perspectives alive without letting them become fog. Riemann,
zeta, manifolds, dimension, and topology are only useful here if they become
measurable objects that rank candidates, shrink encodings, or suggest lemmas.

## First principle

The Riemann hypothesis itself is not a SHA-256 tool. It is about the zeta
function and prime distribution. SHA-256 is a finite bit/carry system.

The useful transfer is not "primes help SHA-256." The useful transfer is:

- zeta-like generating functions for counting solution strata,
- 2-adic lifting because SHA-256 uses arithmetic modulo `2^32`,
- singularity/rank ideas for defect maps,
- spectral/topological tools for basin graphs.

## D1. Solution-count zeta / partition function

Define an energy function such as:

```text
E(x) = final collision residual HW + lambda * schedule defect HW
```

Then compute:

```text
Z_N(beta) = sum_x exp(-beta * E(x))
```

or the discrete weight enumerator:

```text
A_N(k) = number of x with E(x) = k
```

Experiments:

- Exact enumerate N=4..8 where possible.
- Use collision-list / sampler estimates at N=10..12.
- Compare cascade, sr61, non-cascade, and block-2 residual families.
- Look for non-random heavy tails, phase transitions, or basin splits.

Deliverable:

- `headline_hunt/bets/math_principles/results/zeta_energy_atlas.md`

Useful if:

- The low-energy tail predicts which candidates become SAT or near-SAT.

Kill if:

- Curves are descriptive but do not rank candidates better than existing HW
  and defect metrics.

## D2. 2-adic lifting instead of real manifolds

SHA-256 additions live naturally in `Z / 2^N Z`. That suggests lifting from
small word widths to larger word widths:

```text
N -> N+1 -> ... -> 32
```

This is closer to the problem than smooth real manifolds.

Experiments:

- For each reduced-N sr=60 or near-sr61 point, count how many lifts survive
  to N+1.
- Identify obstruction bits that first appear at each lift.
- Test whether sr=61 failure is a stable obstruction cocycle or a local carry
  chamber accident.

Deliverable:

- `headline_hunt/bets/math_principles/results/adic_lift_obstruction_atlas.md`

Useful if:

- It predicts which N=32 chambers came from high-survival lift families.

## D3. Stratified carry manifold

Do not model this as a smooth manifold. A better object is a stratified finite
space:

- strata are carry/gate chambers,
- coordinates are free schedule/message bits,
- maps are defect and residual functions,
- singular strata are places where local rank drops or fibers grow.

Experiments:

- Build chamber adjacency graphs.
- Measure local rank and fiber size per chamber.
- Track whether low-D61 points live on singular strata.

Deliverable:

- `headline_hunt/bets/singular_chamber_rank/results/stratified_carry_space.md`

Useful if:

- It yields a chamber selector for sr=61 or non-cascade search.

## D4. Spectral graph view

If low-residual points form basins connected by rare carry jumps, build a graph:

- nodes: candidate states or chamber signatures,
- edges: one-bit/two-bit/radius-k moves,
- weights: residual change or carry transition cost.

Then measure:

- bottlenecks,
- connected components,
- low-energy cuts,
- Laplacian eigenvectors as coordinates.

Deliverable:

- `headline_hunt/bets/math_principles/results/residual_basin_spectral_map.md`

Useful if:

- Spectral coordinates suggest moves that local HW descent misses.

Kill if:

- It only makes nicer plots of known basins.

## D5. Error-correcting code perspective

Schedule compliance can be treated like a nonlinear code constraint:

```text
message bits -> W57..W63 -> syndrome
```

sr=64 is syndrome zero. sr=60 is syndrome with four erased words.

Experiments:

- Define schedule syndrome vectors for W57..W60 defects.
- Try decoding-style moves: bit flips that reduce syndrome while preserving
  round-state gates.
- Compare syndrome weight, syndrome rank, and final collision residual.

Deliverable:

- `headline_hunt/bets/math_principles/results/schedule_syndrome_decoder.md`

Useful if:

- Syndrome reduction correlates with cascade preservation better than raw
  schedule mismatch.

## Speculation budget rule

No speculative track gets more than 10% of total time unless it produces one
of:

- a better candidate ranking,
- a new exact reduced-N invariant,
- a clause/lemma family,
- a smaller search space,
- a new certificate.
