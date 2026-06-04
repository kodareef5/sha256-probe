# Phase 0 — σ-map ranks + clean-lever feasibility (2026-05-30)

Bet: `linear_lever_gaps`. Owner: macbook-claude. Status: in_flight.

## Why this phase

Test whether the sr=61 wall (`writeups/sr61_impossibility_argument.md`,
`sr60_sr61_boundary_proof.md` Thm 5) is an artifact of the **one** enforcement lever
the paper/repo ever use — the `σ1` (t-2) term — by checking the structural premise
before building any CNF.

## 0a. GF(2) ranks of the σ maps (`q5_alternative_attacks/sigma1_algebra.py`)

| map | N=8 | N=10 | N=16 | **N=32** |
|-----|-----|------|------|----------|
| σ1  | rank 7/8 (nullity 1) | 9/10 (nullity 1) | 16/16 | **32/32 — invertible** |
| σ0  | — | — | — | **32/32 — invertible** |
| Σ0, Σ1 | (all-rotation) | | | full rank |

**Key correction to the thesis.** At **N=32 both σ0 and σ1 are full-rank bijections.**
Rank-deficiency exists only at small N (8, 10). Therefore the "linear lever reaches
values outside σ1's image" argument is **void at N=32** — σ1 is surjective, so enforcing
`W[t]=σ1(W[t-2])+const` can already hit any target by choosing `W[t-2]=σ1⁻¹(...)`.

This does **not** kill the bet. It relocates the mechanism from *image restriction* to
**decoupling** (see 0b). It also means small-N (N≤10) results would *overstate* the
linear-lever benefit (there the image restriction is real), so the N=32 test is the
honest one — small-N is a sanity check only.

## 0b. Clean-lever matching (`lever_feasibility.py`)

Single clean compliance formula: `sr = 16 + #{t∈16..63 : t is computed (not free)}`,
so `sr = 64 − |free|`. A boundary word is *independently controllable* iff it has a
**distinct free word in its direct dependency set** `{t-2, t-7, t-15, t-16}` (a System
of Distinct Representatives over the target set `{61,62,63}`).

### Head-to-head

```
LINEAR-LEVER (new):  free={54,55,56,57}  sr=60  3 linear levers  residual=W[57] (32b)
   61<-W[54](t-7), 62<-W[55](t-7), 63<-W[56](t-7)        [INDEP-CONTROLLABLE]

σ1-CASCADE (wall):   free={57,58,59,60}  sr=60  0 linear levers  residual=W[57],W[58]
   61<-W[59](σ1), 62<-W[60](σ1), 63<-NONE                [COUPLED/INFEASIBLE]
```

- **The new config is genuinely sr=60** (held = `{16..53}∪{58..63}` = 44 equations). The
  earlier adversarial "secretly sr=58" claim is **refuted**: W[58],W[59] are *computed*
  from the recurrence (using the free W[56],W[57] as inputs), hence schedule-compliant.
- **The wall, located exactly:** at the σ1-cascade sr=60, `W[63]` has **no free word in
  its dependency set** — its only non-precomputed input is `W[61]`, itself computed from
  `W[59]`. So `W[61]` and `W[63]` are both pinned by the single free word `W[59]`
  (over-determined). That is the sr=60 wall, and it is a property of the *lever choice*,
  not of σ1's rank.
- **The decoupling difference** (the real, N=32-valid mechanism): the new config gives
  each boundary word `{61,62,63}` its **own** free knob `{54,55,56}` (the `t-7` terms
  reach deep enough to be free), so all three are independently controllable while the
  boundary equations still *hold*. The σ1 cascade cannot do this at sr=60 without freeing
  `W[61]` — which costs an sr level.

### Enumeration (targets {61,62,63}; ranked indep→linear→residual→short-tail)

| sr | free words | #indep-controllable configs | best config | residual |
|----|-----------|------------------------------|-------------|----------|
| 60 | 4 | **428 / 2380** | `{54,55,56,57}` (3× t-7) | 32 bits (W[57]) |
| 61 | 3 | 41 / 680 | `{54,55,56}` (3× t-7) | **0 bits** |
| 62 | 2 | 0 / 136 | — | — (3 targets need ≥3 levers) |

- **sr=60** has ample decoupled configs (428) → lots of room for the decisive probe.
- **sr=61** is independently controllable (`{54,55,56}`) but has **zero tail collision
  freedom** — confirms the adversarial "starvation" point. Phase 3 must *restore* freedom
  (free a message word and/or layer `da[56]=0`), not just relocate levers.
- **sr=62** cannot decouple 3 boundary targets with 2 free words — a hard structural cap
  for this target set.

## Verdict for Phase 1/2

Proceed. The bet's honest mechanism at N=32 is **decoupling**, not image restriction. The
decisive test is: does the `free={54,55,56,57}` linear-lever sr=60 instance (3 independent
boundary knobs, 10-round tail) solve materially faster than the σ1-cascade sr=60 baseline
(paper: timeout; repo: 12h/seed=5)? Build the configurable encoder, validate it reproduces
the known sr=59/sr=60 CNFs, then solve.

Tools shipped: `lever_feasibility.py`. σ-rank run captured from existing
`q5_alternative_attacks/sigma1_algebra.py`.
