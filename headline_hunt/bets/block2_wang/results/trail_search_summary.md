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

## kissat result (2026-05-26) — engine wall was weak search; an 18-round absorber EXISTS

A real CDCL solver (`absorber_cnf.py` → kissat, encoder validated: bit13 R=4 UNSAT / R=8 SAT
match the engine) blows straight through the naive-DFS R=15 wall on bit13_HW35:

```
  R=15: SAT  (0.1s)     R=16: SAT (0.1s)     R=18: SAT (5.2s)     R=20: TIMEOUT (300s)
```

The **R=18 absorber is oracle-confirmed** (`lib.sha256`): input difference = the residual,
zero state difference after 18 rounds, block-2 message-difference HW 240. So:
- The engine's "best-trail-round = 15" was a **weak-search artifact, not structural** — kissat
  reaches 18 in seconds. (The trail-engine value is its sound propagation / control validation,
  not its DFS.)
- An **18-round block-2 absorber exists** — this *matches* the naive-SAT frontier. The bet's
  gate is *>18*; R=20 is a 300s **timeout** (search-limited), so the >18 question is still open.
- A deeper sweep (R=19/20/22/24, 900s/call, oracle-verified) is running to settle >18.

(Note: this plain 2-message CNF *is* the "naive SAT" formulation; reaching 18 reproduces the
known frontier. Whether a tailored differential path pushes a solver past 18 is the open headline.)

**Deep sweep verdict (R=19):** kissat ran R=19 to UNKNOWN at 866s; a cadical cross-check on
the same instance also timed out (300s). So R=19 is **solver-limited (neither SAT nor UNSAT)**
for the naive CNF — a sharp hardness cliff right above the R=18 frontier. The >18 gate is thus
**search-limited, not proven-infeasible**; kill #1 stays unfired. Full verdict + the
pause-for-direction recommendation: `results/20260526_block2_absorber_VERDICT.md`.

## Propagation cannot decide it (2026-05-26) — kissat is required

Propagation-only (no search) was run on the schedule-compliant absorber at R=18, 20, 24 for
both a sparse (bit13 HW35) and dense (bit24 HW101) cluster: **no contradiction** at any R.
So a deep (>18-round) absorber is **NOT provably infeasible** by arc-consistency — kill #1
cannot be fired on a propagation argument. It is either satisfiable or search-hard. Given
block 2 has 512 bits of message freedom (W0..W15 ×2) and propagation finds no obstruction,
a >18-round absorber **may genuinely exist**; a real CDCL solver could return a *positive*
(headline) result, not only a kill. This makes the CNF + `lib.solver.run_kissat` build the
decisive next step (and potentially the bet's payoff, not just its closure).

## Decision — kill #1 NOT fired

Kill #1's trigger is "**1 week** of dedicated trail-engine development + search complete";
this is **~1 day** in. And the >18-round verdict is currently **search-limited**, not a
structural impossibility. Firing the kill now would mislabel an implementation limit as a
cryptographic barrier. Per CLAUDE.md ("don't say more than the evidence supports"), the bet
stays **open / in_flight**.

**Branching tried (2026-05-26):** added input-first ordering to `run_search`
(`input_first=True`: branch on state0 + message-word nodes before forward-determined
nodes). It gives only a constant-factor gain (R=15: 737 vs 997 nodes, ~26%) and does **not**
break the R≥16 wall — the wall is the exponential search, not node ordering. Confirms the
naive DFS is the wrong tool for the >18 verdict.

**What would decide it cleanly (next increments, in priority order):**
1. A **stronger search** to actually test R>18: encode the absorber as CNF and run
   `lib.solver.run_kissat` (the proper naive-SAT-vs-tailored comparison the bet is premised
   on) — a real CDCL solver vastly outpowers the Python DFS. (Sparse-difference branching is
   a weaker alternative.)
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
