---
date: 2026-04-29
bet: cascade_aux_encoding × programmatic_sat_propagator
status: NEGATIVE — F344's 32 dW57 clauses do NOT uniquely determine dW57
---

# F345: F344's 32 dW57 clauses are necessary but not sufficient

## Setup

F344 mined 32 clauses on dW57 (1 unit + 31 adjacent-pair) for cand
m17149975/bit31. Hypothesis: those 32 clauses uniquely determine
dW57's value, so a propagator could pre-inject 32 unit clauses (one
per bit) at solver init, fully fixing dW57.

## Test

Loaded the 32 clauses in isolation (without the rest of the cascade
CNF), ran unit propagation + DPLL model counting on the 32 dW57 vars.

## Result

- After UP from F344's 32 clauses: **1 / 32 bits assigned** (only
  dW57[0] = 1, the single unit clause).
- DPLL model count: **> 1000 SAT models** in isolation (counter
  exceeded budget without finishing).

The 32 clauses are far from sufficient to determine dW57.

## What this means

The 32 clauses are **NECESSARY** structural constraints that any
cascade-1 valid assignment must satisfy. Cadical fast-derives them
from the full CNF.

But they are NOT SUFFICIENT to nail dW57 down. The actual unique value
of dW57 (if there is one for this cand) is determined by the
COUPLING of these 32 clauses with the rest of the CNF — the cascade
chain at rounds 0-56 + downstream rounds 58-63 + the kernel diff at
M[0]/M[9].

## Implication for Phase 2D propagator

The naive "pre-inject 32 dW57 unit clauses" approach REFUTED.

What the propagator CAN do (sound / value-add):
1. **Inject the 32 clauses as LEARNED CLAUSES** (not unit clauses).
   These save cadical's re-derivation cost (~0.05-0.15s × 32 =
   ~3-5s saved per solve) without forcing wrong values.
2. **Use the 32 clauses to PRUNE branches early in CDCL trajectory**.
   When CDCL assigns dW57[i] = a, the conditional implications fire
   immediately to constrain dW57[i+1]. Cadical does this anyway
   after deriving the clauses; pre-loading them moves the saving
   from "after first conflict" to "from the start".

What the propagator CANNOT do:
- Determine dW57 uniquely from these clauses alone.
- Skip the SHA-256 schedule recurrence + cascade subtraction
  arithmetic entirely.

## Refined value estimate for the propagator

Per-cand savings at solver init: ~3-5 seconds of conflict-derivation
work. For long-running solver runs (kissat 562s on F235 hard instance),
this is ~1% — negligible. For shorter solves (~50s mid-difficulty),
maybe 6-10% — modest.

The MAJOR win from the F344 mining isn't directly speedup but
STRUCTURAL UNDERSTANDING: we now have an explicit characterization of
the cascade-1 hardlock at the dW57 row level, which can inform other
mechanism design (e.g., direct encoding of the hardlock as a smaller
formula).

## Concrete next move (revised)

Drop the "naive pre-inject" approach. Instead:

1. **Test the propagator's value with REALISTIC injection**: inject
   the 32 clauses as learned clauses, run kissat/cadical with budget,
   measure speedup vs baseline. ~5 min experiment per cand.

2. **Sweep more rounds (W58/W59/W60)**: F344 only mined dW57. If
   later rounds have similar dense pair constraints, the cumulative
   clause library grows. ~10 min per round.

3. **Algebraic derivation of dW57**: compute dW57 directly from
   (M[0], fill, kernel-bit, sr) via 57-round forward schedule + cascade
   offset. This GIVES the unique dW57 value algebraically. The
   propagator would inject 32 actual unit clauses (not just the F344
   pair constraints) — full speedup.

(3) is the cleanest path. Fundamentally:

```
dW57 = W2[57] - W1[57] mod 2^32
W1[57] = sigma1(W1[55]) + W1[50] + sigma0(W1[42]) + W1[41]   (schedule)
W2[57] = same recurrence with W2[i] from M2 = M1 ^ kernel_diff
```

This is computable in microseconds for any cand. If the propagator
runs this preflight, it gets all 32 dW57 unit clauses directly without
any cadical at all.

## What's shipped

- F345 model-count test result.
- Honest negative on the "32 clauses → unique dW57" hypothesis.

## Discipline

- ~30s wall (UP + partial DPLL).
- 0 SAT compute beyond F344's already-shipped data.
- Self-verifying: this could have been done in F344 itself; F345 is
  the verification step.
- Honest reframe: from "naive pre-inject works" to "algebraic
  preflight works, mined clauses are conflict-clause hints".
