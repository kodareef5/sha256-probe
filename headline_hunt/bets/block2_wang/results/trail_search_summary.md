---
date: 2026-05-26
bet: block2_wang
status: EVIDENCE — kill #1 NOT fired (search-limited verdict; trigger timeline not met)
author: macbook-claude
evidence_level: EVIDENCE (oracle-confirmed absorbers to R=15; deeper rounds search-budget-limited)
---

# Trail-search summary — block-2 absorber vs the >18-round kill gate

Kill_criteria #1 requires this document: per-cluster best-trail-round count, ≥5 clusters, and
a confirmed control case. All three are present. **The kill is NOT fired** — see "Decision".

## Control case (required) — CONFIRMED

The trail engine (`encoders/wang_trail_engine.py` + `encoders/wang_search.py`) independently
reproduces the known SHA-256 **9-step local collision**: a single-bit W0 disturbance is
provably uncancellable in ≤8 rounds and constructible at exactly 9 (corrections W0..W8),
oracle-confirmed. Memo: `results/20260526_local_collision_control.md`. (The kill template
suggested a SHA-1 Wang trail; the SHA-256 local collision is the on-target analog and
validates the engine end-to-end — soundness, find-ability, message modification.)

## Method

For each block-1 residual cluster: pin its round-63 state difference as the block-2 **input**
difference, require a **zero output difference at round R** (a 2-block-collision sub-problem),
allow message modification with the message schedule (t≥16), and run the guess-and-determine
search (node budget 250k). Deepest oracle-confirmed R = "best-trail-round count". Script:
`encoders/run_absorber_sweep.py` → `results/absorber_sweep.json`. Reuses `lib.sha256` as oracle.

## Results — 6 clusters

```
cluster        R=8  R=12 R=15 R=16 R=18 R=20   best-trail-round
bit13_HW35       A    A    A    ?    ?    ?     15
bit14_HW94       A    A    A    ?    ?    ?     15
bit6_HW93        A    A    A    ?    ?    ?     15
bit15_HW97       A    A    A    ?    ?    ?     15
bit24_HW101      A    A    A    ?    ?    ?     15
bit28_HW94       A    A    A    ?    ?    ?     15
A = oracle-confirmed absorber   . = infeasible by propagation   ? = search budget exceeded
```

- **All clusters: oracle-confirmed absorbers (full round-R state collision) up to R=15.** The
  search finds message differences in W0..W{R-1} that drive the residual to a zero state
  difference, re-checked by running both messages through `lib.sha256`.
- **Best-trail-round = 15 for every cluster**, then the naive DFS exceeds 250k nodes at R≥16.
- **Residual hamming weight barely matters**: the dense HW94–101 clusters absorb exactly as
  far (R=15) as the optimized HW35. This re-confirms the 2026-05-25 integration finding
  (HW35 vs HW59 identical) — message-modification freedom dominates the input-difference
  weight. Corollary: the hard-won residual-min work does not help the absorber.

## Critical caveats (why this is EVIDENCE, not a clean kill)

1. **Search-limited, not proven-infeasible.** The `?` at R≥16 is *budget exceeded*, not a
   propagation contradiction. The naive lowest-entropy DFS is weaker than a real CDCL SAT
   solver. R=16 has **no** schedule constraint yet (schedule starts at R=17), so the R=16
   wall is pure search cost of 16 free message words — an implementation limit, not structure.
2. **These are round-R state collisions, not hash collisions.** An R=15 absorber zeroes the
   state at round 15 using large W0..W14 differences; extending to a full 64-round 2-block
   collision is blocked by **schedule re-injection** — the W0..W14 differences reappear in
   W16,W17,… (`W_t = σ1(W_{t-2})+W_{t-7}+σ0(W_{t-15})+W_{t-16}`) and must be re-absorbed.
   The isolation test (`20260526_absorber_search_preliminary.md`) shows a free-message
   extension holds a collision to R=20 but the schedule-compliant version blows up — strong
   evidence the schedule coupling is the real deep barrier (same "dense schedule inverse" as
   `mitm_residue`'s W44↔init2 coupling, [[project_cascade_tail_suboptimal]]).
3. **Not apples-to-apples with the naive-SAT "18 rounds".** That frontier came from a
   different (CNF/SAT) formulation; comparing it to this engine's best-trail-round needs the
   naive-SAT metric re-derived under the same target. Pending.

## Decision — kill #1 NOT fired

Kill #1's trigger is "**1 week** of dedicated trail-engine development + search complete";
this is **~1 day** in. And the >18-round verdict is currently **search-limited**, not a
structural impossibility. Firing the kill now would mislabel an implementation limit as a
cryptographic barrier. Per CLAUDE.md ("don't say more than the evidence supports"), the bet
stays **open / in_flight**.

**What would decide it cleanly (next increments, in priority order):**
1. A **stronger search** to actually test R>18: encode the absorber as CNF and run
   `lib.solver.run_kissat` (the proper naive-SAT-vs-tailored comparison the bet is premised
   on), or add message-first / sparse-difference branching to the DFS.
2. If a stronger search still cannot reach a *full-hash* (re-injection-respecting) collision
   beyond 18 rounds across ≥5 clusters → fire kill #1 with the schedule-re-injection barrier
   as the documented reason (not a timeout).
3. If any cluster reaches an oracle-confirmed full collision past 18 rounds → **headline**;
   record loudly and update `mechanisms.yaml`.

## Honest bottom line

The engine is real, validated, and finds genuine absorbers — but with the current naive
search it reaches 15 rounds, **below** the naive-SAT 18-round frontier. Whether a *tailored
trail can beat naive SAT* (the bet's whole premise) is still **open**, now gated on search
strength and the schedule-re-injection obstacle, not on the engine's correctness.
