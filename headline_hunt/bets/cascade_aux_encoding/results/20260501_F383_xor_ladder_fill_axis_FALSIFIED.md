---
date: 2026-05-01
bet: cascade_aux_encoding
status: F382 HYPOTHESIS FALSIFIED — actual axis is fill=0xffffffff, NOT fill-bit-31
parent: F382 (3-cand small-sample claim)
type: deliverable_5_progress + falsification
compute: 3 additional cadical 30s LRAT runs (bit13, bit10, bit17); reuse F381+F382
---

# F383: 6-cand cross-cand XOR ladder analysis — F382's "fill-bit-31 axis" was undertested

## What changed

F382 claimed (based on n=3 cands) that the structural Tseitin XOR ladder
in cadical's CDCL proof is **fill-bit-31-dependent**. F383 extended to
n=6 cands by running cadical 30s + LRAT proof on bit13_m4d9f691c,
bit10_m3304caa0, bit17_m427c281d (~90s additional compute) and analyzing
with a refined "longest contiguous ladder-shape run" classifier.

## Result — refined classifier on 6 cands

```
cand                fill          b31   kbit   tot_xor   ladder_run   start_triple
bit31_m17149975     0xffffffff      1     31       877          31    (11886, 12622, 12624)
bit2_ma896ee41      0xffffffff      1      2       884          31    (11890, 12626, 12628)
bit11_m45b0a5f6     0x00000000      0     11       854           1    (14, 1349, 1351)
bit13_m4d9f691c     0x55555555      0     13       857           1    (6, 1348, 1350)
bit10_m3304caa0     0x80000000      1     10       837           1    (5, 1335, 1337)   ← FALSIFIES F382
bit17_m427c281d     0x80000000      1     17       823           1    (8, 1321, 1323)   ← FALSIFIES F382
```

`ladder_run` = longest contiguous run of triples matching
`(aux_i, dw_a, dw_a+2) → (aux_i+1, dw_a+5, dw_a+5+2)` with same EVEN
polarity.

## F382 falsified

F382 hypothesized: fill bit-31 SET → 31-step ladder; fill bit-31 CLEAR
→ no ladder. F383's bit10 and bit17 are both fill=0x80000000 (bit-31=1)
but show **no ladder** (run length = 1). That falsifies the
fill-bit-31 axis directly.

The actual axis is much more specific:

  **fill = 0xffffffff (all 32 bits set)** → 31-step ladder
  fill = anything else (00000000, 55555555, 80000000) → no ladder

bit31_m17149975 and bit2_ma896ee41 are the only cands in this 6-cand
panel with fill=0xffffffff. Both produce the 31-step ladder identically.
The 4 cands with non-all-set fills (00000000, 55555555, 80000000)
all produce ladder_run=1 (no ladder).

## Why fill=0xffffffff specifically?

The cascade-aux encoder's W2 derivation is:
  W2 = W1 XOR diff_pattern

For fill=0xffffffff (all-1), W1[1..15] are all 0xffffffff. After XOR
with diff at slot 0 and 9, W2[1..15] also all 0xffffffff except at
slots 0 and 9. The resulting cascade-1 trajectory has highly
symmetric W1, W2 patterns at most rounds.

Conjecture: the ladder is the encoder's Tseitin output for the
**M[1..15] = constant 0xffffffff** symmetry. Slots 1, 2, ..., 15 all
contribute identical sub-formulas; CDCL discovers the per-slot
equivalences as the 31-step ladder (one rung per slot from 1 to ~30).

For non-all-set fills, M[1..15] aren't all the same constant (they're
all the same fill value, but with bits CLEAR), and the same Tseitin
symmetry doesn't apply — the ladder doesn't materialize.

If correct, this is **fill-density-dependent**, not fill-bit-31:
fill=0xffffffff is the maximum-density fill; everything else has lower
density and lacks the ladder.

## Findings

### Finding 1 — F382 hypothesis falsified honestly

The fill-bit-31 axis I claimed in F382 was based on too small a sample
(n=3). F383's 2 counter-examples (bit10, bit17 with fill=0x80000000)
falsify it cleanly. The true axis appears to be **fill = 0xffffffff
specifically** — a much narrower condition.

This is the project's 7th retraction (after F340 → F377, F365 → F366,
F368 → F369, F358 → F360, F315 → F322, F125 → ...). Pattern continues:
small-sample structural hypotheses get falsified by larger-sample tests
within hours of being proposed. Discipline holds.

### Finding 2 — Real generalization is narrower than F382 claimed

The structural Tseitin XOR ladder is a **cand-class property**, but
the class is narrower than F382 thought:

  - Class A: fill = 0xffffffff (only 2 cands in this 6-cand panel)
  - Class B (everything else): fill ∈ {0x00000000, 0x55555555,
    0x80000000, 0xaaaaaaaa, ...}

For the registry of 67 cands, Class A is small. Looking at typical
fills: ~30 cands have fill=0xffffffff per the candidates.yaml count.
So Class A is roughly half the registry, not a generic property.

### Finding 3 — Phase 2D + F343 design implications

The propagator's pre-injection should be:
  - Class A (fill=0xffffffff): inject the 31-rung ladder
    (Tseitin XOR triples + size-2 equivalences). Per-cand var-mapped.
  - Class B (other fills): inject only F343's 2-clause preflight.
    No ladder available.

This is structurally cleaner than F382's misclaim — instead of two
broad classes by fill bit-31, we have one narrow class (fill=ffffffff)
that gets a substantial ladder injection plus everything else getting
the existing F343 baseline.

### Finding 4 — Mode-dependence of cadical proof structure

Within Class A (fill=0xffffffff cands bit31 + bit2), the ladder shape
is identical (aux step 1, dW step 5, EVEN polarity, length 31). The
var IDs differ per cand (bit31 starts at aux 11886 / dW 12622; bit2
starts at aux 11890 / dW 12626) but the structure is invariant.

For Phase 2D pre-injection: the ladder template is universal across
Class A; just plug in the per-cand var-base offsets.

## Compute discipline

- 3 cadical 30s runs (bit13, bit10, bit17), all UNKNOWN at 30s, logged
  via append_run.py
- Total wall: ~90s
- Real audit fail rate stays 0%

## What's shipped

- This memo with falsification of F382's fill-bit-31 hypothesis
- 6-cand cross-cand fingerprint table
- Refined hypothesis: fill=0xffffffff is the actual axis
- Concrete propagator pre-injection design implication
- 3 runs.jsonl entries

## Open question for next session

Confirm with 1-2 more fill=0xffffffff cands. The registry has
~30 such cands; F347-F369 already used several. If all fill=0xffffffff
cands show 31-rung ladder and all other fills don't, the hypothesis
firms up. ~5 min compute.

## Honest summary of the F381 → F382 → F383 chain

  F381: discovered Tseitin XOR clauses in cadical proof on bit31. Tool
        unblock.
  F382: claimed fill-bit-31 axis based on n=3. **Wrong axis.**
  F383: 6 cands → fill=0xffffffff is the actual axis. **Narrower class
        than claimed.** Falsifies F382, refines mechanism.

The "structural class" finding is real. The exact class boundary needed
3 more compute-runs to nail down. Pattern of small-sample hypotheses
getting refined or falsified continues — exactly what the project's
discipline is for.
