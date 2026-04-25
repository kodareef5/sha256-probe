# chunk_mode_dp baseline — q5/chunk_mode_dp.c results refute boundary-carry quotient

## What I found

While surveying q5_alternative_attacks/ for unexploited tooling that could feed active bets, found `chunk_mode_dp.c` (649 LOC) with a pre-built binary. Ran it at N=8 — completed in 100s on macbook.

This is GPT-5.4's prescribed boundary-carry-quotient measurement (per the file's docstring). It tests whether projecting collision states to "boundary carries at bit 4" yields effective deduplication.

## Results (verified 2026-04-25)

```
N=8, MSB kernel, M[0]=0x67, fill=0xff
Phase 1: 4294967296 configs, 260 collisions, 85.43s

--- Invariant analysis ---
Path 1: 5/49 invariant, 44 variable
Path 2: 5/49 invariant, 44 variable
Total variable carries: 88 of 98 (only 10 invariant)
Reduced state space: 2^88

--- Reduced boundary states for collisions ---
Unique reduced collision boundary states: 260 / 260
All unique? YES (perfect permutation at boundary)

--- Sample-based unique count estimate ---
Sample: 1048576 configs, 1048456 unique (~99.99%)
Duplicate rate: 0.0001
Almost all unique → dedup ratio ~1x at boundary
```

## Two findings

### 1. Boundary-carry quotient gives essentially NO compression

98 boundary-carry bits → 88 variable. Only 10 bits are invariant across all 260 collisions. The "natural" quotient state (carries at bit 4 boundary) has dimension only 10% lower than the full carry state.

### 2. ~1× deduplication ratio empirically

Out of 1M random configs, 99.99% have unique boundary states. The boundary state is effectively a UNIQUE FINGERPRINT of each (W57, W58, W59, W60) — not a quotient of any kind.

## What this kills

**The boundary-carry-quotient hypothesis from GPT-5.4's prescribed measurement is empirically refuted.** Per `negatives.yaml#raw_carry_state_dp_near_injective`:

> Trigger: A quotient state not based on raw carries gives >10x reduction at N=8.

The boundary-carry quotient gives ~1× reduction. **Trigger condition met for refutation; this specific quotient design dies.**

## What this DOESN'T kill

The chunk_mode_dp BET (priority 6) is broader than this specific quotient design. The design seed I shipped earlier (`bets/chunk_mode_dp/results/20260425_design_seed.md`) proposes a DIFFERENT quotient — based on cascade status + register diffs, not on raw boundary carries.

The cascade-status-based quotient might compress where the boundary-carry quotient doesn't. Both have to be tested separately.

## Implication for the bet's status

| Quotient design | Empirical status (2026-04-25) |
|---|---|
| Raw carry state | already closed in `negatives.yaml#raw_carry_state_dp_near_injective` |
| Boundary carries (this experiment) | EMPIRICALLY REFUTED at N=8 |
| Cascade-status + 4-d.o.f. modular (my design seed) | UNTESTED — might still work |
| Mode-variable quotient (BET.yaml original) | UNTESTED |

The bet stays alive ONLY if a smarter quotient (the modular-d.o.f.-based one or another untested design) compresses where boundary-carries don't.

Recommend: keep the bet status `open` but mark the boundary-carry quotient as closed in negatives.yaml.

## What this teaches

The N=8 collision boundary-carry STATE is essentially a UNIQUE fingerprint per collision. This is consistent with: "carry state DP is brute force" (the existing closed negative) but at a finer-grained level.

The chunk-mode hypothesis can only work if the quotient is FUNDAMENTALLY DIFFERENT from carry-based — operating in a higher-level structural space (mode + active-register subspace) rather than at the carry bit level.

## Compute spent

100s on macbook, single-threaded, run from existing pre-built binary in q5_alternative_attacks/. No new compute needed.

## Recommended actions

1. Add this finding to `negatives.yaml` as a new entry: `boundary_carry_quotient_no_compression`.
2. Keep chunk_mode_dp BET.yaml status open — the bet's mode-variable design is structurally different.
3. Future workers attempting chunk_mode_dp should use the cascade-status-based design (not boundary carries).

## Cross-bet impact

This finding sharpens the chunk_mode_dp design seed:
- The mode-variable approach must AVOID raw-carry components
- The 4-d.o.f. residual variety from mitm_residue is a candidate quotient that's structurally different from carry-state
- Specifically: mode-based quotient should encode CASCADE STATUS + MODULAR REGISTER DIFFS, not bit-level carries

Mitigation: my design seed already operates on register diffs, not carries. So it's NOT directly refuted by this experiment.
