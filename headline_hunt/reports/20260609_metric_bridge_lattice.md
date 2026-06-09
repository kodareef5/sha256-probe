---
date: 2026-06-09
status: T0.1 COMPLETE — the sr-metric and the standard step-reduced metric are ORTHOGONAL axes
author: macbook-claude (fable model test)
evidence_level: VERIFIED (definitional, from reference/paper.pdf + sr60 certificate; zero compute)
---

# The metric bridge: a rigorous lattice for "sr" vs the standard step-reduced world

This re-prices the entire project. It is a desk analysis (no compute) of how the repo's
Viragh "sr / schedule-compliance" metric relates to the metric every external result
(classical AND quantum) actually uses.

## The three orthogonal relaxation axes

A "collision-like" object on the SHA-256 compression function lives in a 3-axis relaxation
space. A *true* collision is the all-strict corner; every published result relaxes one axis:

| Axis | What it relaxes | What it keeps strict | Records here |
|---|---|---|---|
| **R — rounds** | run only R<64 rounds; collision required at round R | 100% schedule, standard/honest IV handling | 37 practical (Zhang 2026/232), 39 SFS (Li-Liu-Wang EC2024) |
| **IV — start freedom** | free-start (IV,IV' free) / semi-free-start (IV=IV' but attacker-chosen) | full schedule, full rounds | the standard "SFS" qualifier on the above |
| **S — schedule** | free `64−sr` of the 48 expansion equations W[i]=σ1(W[i-2])+W[i-7]+σ0(W[i-15])+W[i-16] | full 64 rounds, **standard IV** | **sr=59 (Viragh), sr=60 (this repo)** |

**The repo's sr=60 object relaxes ONLY axis S.** From the certificate + anatomy writeup:
full 64 rounds, **standard IV**, output difference = 0, with **4 free schedule words
W[57],W[58],W[59],W[60]** (W57 triggers cascade-1 da57=0; W60 triggers cascade-2 de60=0;
W58/W59 do schedule compatibility). It is *not* reduced-round and *not* free-IV.

## The metric's own definition is internally inconsistent (prefix vs count)

The paper defines sr two ways:
- **Prefix:** "the largest integer such that W[0..sr-1] satisfies the schedule expansion."
- **Count:** "sr = 16 + k, k = number of expansion equations that hold for i=16..63."

These coincide only if the satisfied set is a contiguous prefix. **Gap placement breaks
that.** For the sr=60 certificate the violations are at i=57,58,59,60 and the satisfied set
is the *non-contiguous* {16..56} ∪ {61..63} = 41+3 = 44 equations → 16+44 = **sr=60 by COUNT**,
whereas the PREFIX reading stops at the first violation (i=57) giving only **sr=57**. The
project (and the paper) use the COUNT. So "sr" is really "#expansion-equations-satisfied,
placeable non-contiguously via gap placement" — not a prefix depth. This matters whenever
sr is compared to a round count (which IS a prefix depth).

## The comparison table in the paper is a category error

The paper's §3.3 table maps standard results onto the sr column as "39 steps → sr 39/39",
"37 steps → sr 37/37". **This conflates axis R with axis S.** A 39-step collision is a
collision of the *39-round* compression function: rounds 40..63 do not exist in that attack.
Run that same colliding pair through all 64 rounds and you get **full schedule compliance
(all 48 equations hold, it's a real message) but a NON-ZERO output difference** — i.e. it is
*not* an sr-style 64-round collision at all. Conversely the sr=60 object has a zero 64-round
output difference but only 44/48 schedule equations. **Neither dominates the other; the axes
are incomparable.** "93.75% of SHA-256" (sr=60/64) is therefore NOT a step-count statement
and does not beat, tie, or compare to the 37/39-step records.

## What sr<64 means cryptographically (the deflationary truth)

Because W[57..60] deviate from the recurrence, the full schedule W[0..63] of the sr=60
object **does not expand from any single 16-word message**. So sr<64 is a collision in the
*relaxed/expanded* schedule space (4 expansion constraints dropped), with **no corresponding
real-message pair**. Only sr=64 would be a real collision. sr is a "distance-to-break"
heuristic on a progressively-relaxed system, not a partial break of real SHA-256. (Consistent
with the repo's own finding that the sr structural predictors are search-irrelevant, ρ≈0.)

## Consequence for the quantum angle (T3.1) — NO-GO, decided at zero compute

The Zhou et al. (Quantum Inf. Processing, Dec 2025) SFS→full conversion consumes a
**reduced-round, free-IV, differential semi-free-start collision** (axes R+IV relaxed, full
schedule) and absorbs its chaining-value difference with a second block. The repo's sr=60 is
**full-round, standard-IV, schedule-relaxed** (axis S only) with output difference already 0.
It is a different equivalence class of object: there is no free IV to vary and no reduced-round
differential trail to feed the conversion. **The quantum conversion cannot consume the
existing sr=60 result.** The quantum angle becomes relevant ONLY if the repo first produces a
genuine *standard differential SFS* on the R axis (see T0.2 / the standard-metric pivot) — at
which point quantum conversion is a citable destination, but it adds no step depth beyond
whatever classical differential SFS depth is achieved.

## Bottom line for project direction

1. sr=60 does **not** imply or beat any standard step record (orthogonal axes).
2. The only path to a result that the field (and the quantum framework) recognizes is to
   produce something on the **R axis** (a reduced-round differential collision/SFS) — which
   is exactly the block-2 / standard-metric pivot the four-agent review recommended.
3. The lattice + the prefix-vs-count + the table-category-error are a clean standalone
   clarification worth publishing as the "sr Rosetta" note regardless of what the experiments
   below find.
4. **Open question for T0.2:** is ANY of the repo's sr-regime structure (42% carry invariance;
   σ1-conflict barrier) a property of SHA-256's round function that shows up on the standard
   R-axis trails — or is it cascade-specific? That decides whether the sr program produced
   transferable science or only characterized one construction.
