---
date: 2026-04-29
bet: cascade_aux_encoding × programmatic_sat_propagator
status: NEGATIVE_REFRAME — algebraic preflight from M alone won't work; W57..W60 are free
---

# F346: algebraic dW57 preflight from M alone is structurally wrong

## Setup

F345 found F344's 32 dW57 clauses are necessary but not sufficient.
F346 attempted an algebraic preflight: compute dW57 directly from
(M[0], fill, kernel-bit) by running the schedule recurrence forward 57
rounds.

## What I did

For each of 6 cands, computed:
- M1 = [M[0]] + [fill] * 15
- M2 = M1 with kernel-bit XOR at words 0 and 9
- W1[16..57] via standard schedule recurrence
- W2[16..57] same recurrence
- dW57 = W1[57] XOR W2[57]

## What's wrong

Reading the cascade_aux_encoder source (`build_cascade_aux_cnf`):

```python
n_free_map = {59: 5, 60: 4, 61: 3}
n_free = n_free_map[sr]
first_sched = 57 + n_free    # first schedule-determined round
# --- Free schedule words ---
w1_free = [cnf.free_word(f"W1_{57 + i}") for i in range(n_free)]
w2_free = [cnf.free_word(f"W2_{57 + i}") for i in range(n_free)]
```

**For sr=60: rounds 57, 58, 59, 60 are FREE message words.** The
schedule recurrence only applies at rounds 61, 62, 63 (which are
schedule-determined from the free W57..W60).

For sr=61: rounds 57, 58, 59 are free; W60 is schedule-determined.

So my "compute W1[57] from schedule expansion of M" gives a DIFFERENT
value than what the encoder treats as W1[57]. In the encoder, W1[57]
is a free variable that the SAT solver chooses, constrained by:
- The cascade-1 hardlock at round 60: state1[0]_after_60 == state2[0]_after_60
- The schedule recurrence at rounds 61-63

## Empirical confirmation of the misframe

For bit0 cand (M[0]=0x8299b36f, fill=0x80000000):

```
Algebraic schedule-expand: W1[57] = 0x1d3f7373, W2[57] = 0xbaf2ed6a
                            dW57 XOR LSB = 1
```

But F342 cadical preflight reported `aux_W57[0] = 1 UNSAT` (so forced=0).

**Discrepancy**: my algebra says XOR LSB = 1, but cadical says it's 0.

Resolution: **W1[57] in the encoder is NOT 0x1d3f7373**. The encoder
treats W1[57] as free; the cascade-1 hardlock plus solver constraint
gives a different value where W1[57][0] = W2[57][0] (so XOR LSB = 0).

## Implication

The algebraic preflight from M alone is structurally wrong for sr=60.
A correct preflight must:

1. Compute s1, s2 (state after round 56) from M.
2. Set up the 4-round (sr=60) free-schedule problem with cascade-1
   hardlock at round 60.
3. Either (a) solve algebraically — likely intractable for arbitrary
   cand, OR (b) run a small cadical preflight to determine the unique
   W57..W60 values.

Path (b) IS what F343/F344 already does: cadical preflight on the
encoded CNF identifies the forced bits via CDCL fast-UNSAT. The
"algebraic" speedup over (b) doesn't exist because the underlying
problem is genuinely 4-round-coupled cascade-1 system.

## What stands

- F341, F342, F343, F344: empirical findings about CDCL-derived
  structural clauses are unchanged.
- F345 model-count finding stands: 32 isolated clauses are necessary
  but not sufficient.
- The cadical preflight (~20s per cand for the basic clauses, ~13 min
  for full dW57 row sweep) is the RIGHT approach.

## What's refuted

- "Algebraic dW57 preflight from M alone gives unique 32-bit value"
  hypothesis (F344 next-move (d), and what I attempted in F346).
- The "microseconds preflight" framing in F345's "what's next" — the
  preflight needs cadical, not just schedule arithmetic.

## Refined Phase 2D propagator design

The propagator workflow is:
1. **Init time**: Receive cand metadata (sr, M[0], fill, kernel-bit).
2. **Preflight**: Generate the cand's CNF + run cadical preflight
   probe (~20s for basic 2 clauses, ~13 min for full dW57 row).
3. **Inject**: Pre-load mined clauses as `cb_add_external_clause`.
4. **Solve**: Run cadical with propagator hooks active.

Net: cadical pays ~20s preflight + saves CDCL re-derivation cost.
For F235-class hard instances (562s baseline), 20s preflight is
~3.5% overhead — modest. Larger preflights (~13 min for full row)
only worth it if the propagator's clause library actually saves time.

## Discipline

- ~5 min wall (algebra + verification + refute).
- 0 cadical compute beyond F344's already-shipped data.
- Honest negative + structural reframe.
- Acknowledges F345's "what's next (d)" was wrong direction.

## What's shipped

- F346 algebra refutation in this memo.
- The schedule-expand-from-M approach is documented as STRUCTURALLY
  WRONG for sr=60.

## Cross-machine implication

For Phase 2D propagator: the preflight tool from F343 IS the right
architecture. No algebraic shortcut exists for sr=60 due to W57..W60
freedom. The propagator ships with cadical-based preflight, accepts
the ~20s startup cost, and uses the mined clauses to save CDCL
re-derivation during the main solve.
