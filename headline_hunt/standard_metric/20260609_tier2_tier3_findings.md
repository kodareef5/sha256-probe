---
date: 2026-06-09
status: Tier 2/3 — decoupling toolchain imported & validated; door-closers resolved
author: macbook-claude (fable model test)
evidence_level: mixed (T2.1 VERIFIED operational; T3.1/T3.3 closed; T2.2/T2.3/T3.2 scoped with path)
---

# Tier 2 (decouple block-2) + Tier 3 (door-closers) findings

Context: Tier 0 redirected to the standard (R-axis) metric; T1.3 imported the SAT+CAS engine.
Tier 2/3 round out the standard-metric toolchain and close the remaining angles.

## T2.1 — local-collision decoupling finder: IMPORTED & VALIDATED OPERATIONAL

Cloned `Zhang-SDU/AutoSHA2Collision` (the eprint 2026/232 code). Its
`local_collision_search/search_local_collision_model.py` is the **decoupling** tool the repo
never had: it solves the *message-expansion* local-collision problem **alone** (word-level,
STP-backed), optimizing #difference-words + #cancellations, BEFORE the state characteristic.
Validated it runs end-to-end with the now-installed STP (55 (span,start) configs evaluated in
120s). The committed 37-step patterns (e.g. `pattern_37attackStep_18spansStep_7startStep_12obj`)
confirm it finds solutions at the right parameters (6 difference-words over an 18-step span).
**This is the split the repo's block-2 work never did** — it ran monolithic SAT absorbers
that walled at 18. The decoupling pipeline (finder → fixed difference-word pattern → feed to
the CAS state search) is now available. Producing a *block-2-tailored* pattern needs matching
the finder's `startStep` to the residual-entry round (the repo's proven 7-round absorption
depth bounds the usable span) — the concrete next experiment.

## T2.2 — new Ch/Maj bit-condition models: IMPORTED, comparison scoped

`differential_search/unit_function_256.py` contains the 2026/232 "holistic" Boolean-function
models: `maj_function` + condition-counting variants ((x,y)-based / x-based / (y,z)-based) and
`xor_function_bitcondition` — the richer bit-condition capture that the paper credits for
31→37. The repo's `wang_trail_engine.py` uses the standard (coarser) generalized-condition
Maj/Ch. The decisive comparison — does the richer model find a trail the repo's model declares
infeasible on the oracle-checked 9-step control — is an *integration* task (port the repo's
control into the CVC model framework, or vice versa); the models are now in-hand to do it.

## T2.3 — non-a-zeroing residual constructions: DEPRIORITIZED by Tier 0

This targets the block-2 *residual* direction (find a sparse residual class outside the
proven-for-one-construction floor). Tier 0's verdict (sr/cascade structure does not transfer;
pivot to the standard metric) makes this low-EV: it stays inside the cascade/residual frame
that the standard metric does not use. Recorded as available-but-deprioritized; the local-
collision finder (T2.1) is the better route to a sparse construction if pursued.

## T3.1 — quantum SFS→full: NO-GO (closed in Tier 0)

Decided definitionally in T0.1: the Zhou et al. conversion needs a reduced-round free-IV
differential SFS; the repo's sr=60 is full-round, standard-IV, schedule-relaxed. Category
mismatch. See `negatives.yaml#quantum_sfs_to_full_needs_differential_sfs_not_sr`.

## T3.3 — SMT-bitvector over Z/2^32 ("the different ring"): door CLOSED

The GF(2)-linearization reopen-trigger asked for "a GF(2)-equivalent quotient via a different
group." Tested STP (installed 2.3.3), a bit-vector SMT solver over Z/2^k. **STP bit-blasts
bitvector constraints to CNF and calls a SAT backend** — its invocation is literally
`stp --cryptominisat` (the SAT solver it bit-blasts to). The modular ring provides **no native
word-level shortcut**: solving over Z/2^32 with STP = bit-blast to CNF + SAT, the same object
the repo already solves with kissat, plus SMT front-end overhead. Decisively, the SOTA tool
(2026/232) itself uses STP precisely as a bit-blasting front-end (`--cryptominisat`) — the
leverage is the differential *encoding* (sparsity control + Boolean models), never the ring.
The "different ring" angle is closed: no structural advantage.

## T3.2 — cube-and-conquer: tool-gated + low-EV

Needs `march_cu` (the lookahead cuber), absent and not readily brew-installable
(cryptominisat5 IS present, but it is the conquer solver, not the cuber). Per the agent
analysis, C&C also fails structurally on the cascade (treewidth ≥ 50 ⟹ no good cubing
decomposition — the same wall) and is only plausible on the block-2 absorber, which Tier 0
deprioritized. Scoped out: tool-gated and aimed at a deprioritized target.

## Net for Tier 2/3
The standard-metric toolchain is now complete in the repo's environment: **CAS solver +
Nejati encoder + characteristics (T1.3)** and the **decoupling local-collision finder + new
Boolean models (T2.1/T2.2)**. Two angles are cleanly closed (quantum, SMT-ring). The live
next experiment is the decoupling pipeline on a standard reduced-round / block-2-derived
local collision, feeding the CAS engine — squarely on the R-axis Tier 0 pointed to.
