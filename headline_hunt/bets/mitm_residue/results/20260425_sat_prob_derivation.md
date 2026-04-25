# Cascade-sr=61 SAT prob derived structurally: 2^-32 per candidate

The empirical observation that cascade-sr=61 SAT probability is ~2^-32 per candidate (BET.yaml current_progress; confirmed by ~1800 CPU-h null result and 1M-sample W[60] sweep) now has a structural derivation.

## The argument

Search input dimension (cascade-DP at sr=61): **96 bits**
- W[57], W[58], W[59] free; W[60] schedule-determined (per encoder line 86).

Residual modular dimension at r=63: **128 bits**
- 6 active registers at r=63: {a, b, c, e, f, g} → 6 × 32 = 192 raw bits.
- Two modular constraints (R63.1, R63.3 from `20260425_residual_structure_complete.md`) reduce 6 active registers to **4 independent modular d.o.f.** = 4 × 32 = 128 bits.

Collision constraint at r=63: **128 bits**
- For sr=61 collision, all 6 active register diffs must be zero, equivalent (via R63.1 and R63.3) to pinning 4 independent moduli to zero = 128 bits.

SAT probability = (input-dim) − (constraint-dim) = 2^(96 − 128) = **2^-32**.

## Why this matches empirically

Total W-search per candidate: 2^96.
Expected # of SAT W-tuples per candidate: 2^96 × 2^-128 = 2^-32 < 1.

So MOST candidates have zero solutions; ~1 in 2^32 candidates has at least one solution. When a candidate has solutions, expected count is ~1.

Empirical observations consistent with this:
- 1800 CPU-h Kissat null result on multiple sr=61 candidates (no SAT found).
- 1M-sample W[60] sweep on cascade-held triple: 0 hits at de61=0 (BET.yaml).
- 131k forward-table sweep on priority candidate: 0 collisions, best HW=65 (signature_distribution).

Each of these is consistent with 2^-32 SAT prob per candidate, which is the structural expectation.

## What this implies for the bet path

The 2^-32 hardness is **not** a property of solver implementation, candidate selection, or instance subtleties. It is a **structural consequence** of:
1. 96 bits of W-search freedom.
2. 128 bits of modular d.o.f. in the cascade-DP residual at r=63 (after the two constraints from Theorems 1-4 collapse 6 → 4 d.o.f.).

To beat 2^-32, one of the following must change:
- **(a)** Find a 5th independent modular constraint at r=63 (not just shift-register consequences of earlier constraints). This would reduce d.o.f. to 3 × 32 = 96 bits, matching the W-search space, giving a 1-SAT-per-candidate model.
- **(b)** Find a partition of the 96-bit W-search into independent halves such that meet-in-the-middle works. This is the original mitm_residue bet hypothesis; structurally dependent on the residual map's algebraic shape.
- **(c)** Give up cascade-DP and use a different mechanism (block2_wang second-block trail, kc_xor_d4 #SAT, etc.).

For path (a): ~no obvious 5th constraint exists from Theorems 1-4 + shift register alone. Searching the ANF / algebraic span of (da_63, db_63, dc_63, da_62, db_62, da_61, dT2_62, dT2_63) for hidden equalities is a research project (multi-day analytical work).

For path (b): the forward-table approach showed 0 collisions in 131k witnesses, suggesting the map is too "spread out" for naive MITM. Need a different splitting axis.

For path (c): the active bets cover this — block2_wang, kc_xor_d4, programmatic_sat_propagator each take a different non-cascade-DP angle.

## Status of the mitm_residue bet

The bet's CENTRAL QUESTION ("can MITM on the residue beat 2^32?") now has a STRUCTURAL ANSWER: under cascade-DP residual structure (4 modular d.o.f.), naive MITM can't beat 2^32. A non-naive MITM that uses the constraint structure (e.g., parametrize forward by `a_60, a_61, a_62`-determined moduli, parametrize backward by independent moduli) might break this — but no such partition has been found yet.

Recommendation: park the bet as **structurally complete** at p5. The path forward is path (c) — different mechanisms — not deeper MITM analysis. The structural picture serves as a clean ceiling that future bets (block2_wang, programmatic_sat_propagator) can use as a baseline ("anything below 2^-32 hardness is a structural breakthrough").
